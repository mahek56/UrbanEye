# UrbanEye Backend

FastAPI backend for the UrbanEye urban-event corroboration system.

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (async) |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2.x async |
| Database | PostgreSQL 15 + PostGIS 3 |
| Settings | pydantic-settings |
| Testing | pytest + pytest-asyncio + httpx |

---

## Prerequisites

- Python 3.11+
- Docker + Docker Compose (for PostgreSQL + PostGIS)

---

## Local Setup

```bash
# Step 1: Enter the backend directory
cd /path/to/UrbanEye/backend

# Step 2: Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows PowerShell

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Configure environment
cp .env.example .env
# Edit .env if needed – the defaults work for local dev

# Step 5: Start PostgreSQL + PostGIS
docker compose up -d db
# Wait ~5 seconds for Postgres to be ready

# Step 6: Start FastAPI
uvicorn app.main:app --reload --port 8000

# Step 7: Verify API docs
open http://localhost:8000/docs
```

---

## Running the Full Stack (Docker)

```bash
docker compose up --build
```

This starts both the `db` (PostGIS) and `backend` (FastAPI) services.

---

## API Reference

### `POST /events`

Submit a detected urban event from the edge AI or bus simulator.

**Request body:**

```json
{
  "bus_id": "BUS_01",
  "lat": 17.4239,
  "lon": 78.4738,
  "timestamp": "2026-08-26T10:15:00Z",
  "type": "pothole",
  "confidence": 0.87
}
```

Allowed `type` values: `pothole`, `road_damage`, `congestion`, `obstruction`

**Response (200):**

```json
{ "event_id": 1, "message": "Event received and processed." }
```

**Error responses:** `422` for validation failures, `500` for unexpected DB errors.

---

### `GET /incidents`

Retrieve all verified incidents, sorted by severity descending.

**Response:**

```json
[
  {
    "incident_id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    "lat": 17.4239,
    "lon": 78.4738,
    "type": "pothole",
    "severity": 8.2,
    "corroboration_count": 2,
    "first_seen": "2026-08-26T10:15:00Z",
    "last_seen": "2026-08-26T10:25:00Z"
  }
]
```

---

## Manual curl Test Sequence

```bash
# Test 1 – valid event
curl -s -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "bus_id": "BUS_01",
    "lat": 17.4239,
    "lon": 78.4738,
    "timestamp": "2026-08-26T10:15:00Z",
    "type": "pothole",
    "confidence": 0.87
  }' | python3 -m json.tool

# Test 2 – second bus, same location, within 10 min → should merge
curl -s -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "bus_id": "BUS_02",
    "lat": 17.42391,
    "lon": 78.47381,
    "timestamp": "2026-08-26T10:18:00Z",
    "type": "pothole",
    "confidence": 0.92
  }' | python3 -m json.tool

# Test 3 – GET /incidents → 1 incident, corroboration_count=2
curl -s http://localhost:8000/incidents | python3 -m json.tool

# Test 4 – invalid event type → 422
curl -s -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"bus_id":"BUS_01","lat":17.4239,"lon":78.4738,"timestamp":"2026-08-26T10:15:00Z","type":"earthquake","confidence":0.9}' \
  | python3 -m json.tool

# Test 5 – invalid confidence → 422
curl -s -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"bus_id":"BUS_01","lat":17.4239,"lon":78.4738,"timestamp":"2026-08-26T10:15:00Z","type":"pothole","confidence":1.5}' \
  | python3 -m json.tool
```

---

## Running Tests

Tests require a running PostgreSQL + PostGIS instance with a **separate** test database (`urbaneye_test`).

```bash
# Start the DB (if not already running)
docker compose up -d db

# Create the test database (first time only)
docker exec -it $(docker compose ps -q db) \
  psql -U urbaneye -c "CREATE DATABASE urbaneye_test;"

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_backend.py::test_two_buses_same_location_one_incident -v
```

---

## Severity Formula

```
raw_severity = type_weight × mean_confidence × ln(corroboration_count + 1)
severity     = min(10.0, raw_severity × (10.0 / SEVERITY_SCALE))
```

Default type weights:

| Type | Weight |
|------|--------|
| pothole | 8.0 |
| road_damage | 7.0 |
| obstruction | 6.0 |
| congestion | 5.0 |

These are configurable via `TYPE_WEIGHTS` and `SEVERITY_SCALE` in `.env`.

---

## Architecture Notes

### Corroboration (Incremental, not batch)

Each `POST /events`:
1. Stores the event in the `events` table.
2. Searches `incidents` for a matching row: **same type**, **≤ 15 m** away (PostGIS `ST_DWithin`), **last seen within 10 minutes** of this event's timestamp.
3. If found → merges: updates centroid, `contributing_buses`, `mean_confidence`, `severity`.
4. If not found → creates a new incident.

### Concurrency Guard

A `SELECT … FOR UPDATE` lock is acquired before the merge/create decision, preventing duplicate incidents under concurrent POSTs.

### Known Limitation

Centroid-based matching allows incidents to drift spatially as events merge. A maximum-diameter constraint can be added post-hackathon for higher precision.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://urbaneye:urbaneye@localhost:5432/urbaneye_db` | Async DB URL |
| `APP_ENV` | `development` | Environment tag |
| `BACKEND_PORT` | `8000` | Port for uvicorn |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `SEVERITY_SCALE` | `8.0` | Normalization divisor for severity |
| `TYPE_WEIGHTS` | `{"pothole":8.0,...}` | JSON map of event-type weights |
