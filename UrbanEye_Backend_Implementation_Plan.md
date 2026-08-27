# UrbanEye Backend — Member B Final Implementation Plan

## Repository State (confirmed by inspection)

| Path | Status |
|------|--------|
| `/backend` | Does NOT exist — will be created from scratch |
| `/edge` | Exists — READ-ONLY reference only |
| `API_Contract.md` | Exists — READ-ONLY, must not be changed |
| `BUILD_PLAN.md` | Does NOT exist in repo |
| `docker-compose.yml` | Does NOT exist at root |
| `.gitignore` | Exists — READ-ONLY |

Everything created below is **inside `/backend` only**.

---

## User Review Required

> [!IMPORTANT]
> **Type weights are not in the API contract.** Initial proposed values are labeled assumptions and kept in a single config file. Team must confirm before final release.

> [!IMPORTANT]
> **Severity normalization uses a configurable `SEVERITY_SCALE` env var** instead of an assumed fleet size. See Phase 5 for full explanation.

> [!IMPORTANT]
> **No root-level `docker-compose.yml` exists.** A standalone `/backend/docker-compose.yml` is created for local development only. The team must decide later whether to merge this into a root-level file.

> [!WARNING]
> **Transitive merging** (Event A ↔ B ↔ C but A not close to C) is addressed using centroid-based matching. Full reasoning is in the Corroboration section.

---

## Open Questions

| # | Question | Impact |
|---|----------|--------|
| OQ-1 | Are the proposed type weights (pothole=8, road_damage=7, obstruction=6, congestion=5) acceptable? | Severity values will differ if changed |
| OQ-2 | Is `SEVERITY_SCALE=10.0` (meaning raw ≤ scale maps to ≤ 10) acceptable, or does the team want explicit examples first? | Severity normalization |
| OQ-3 | Should an event from the same bus still update `last_seen` and contribute to `mean_confidence`? (Proposed: yes) | Incident freshness |
| OQ-4 | Is `ln` (natural log) the correct log function? (Proposed: yes) | Severity values change ~2× if log₁₀ |
| OQ-5 | Should `GET /incidents` return all incidents ever, or only those updated within a rolling window? (Proposed: all) | Frontend UX |

---

## 1. Final `/backend` Directory Tree

```
/backend/
├── Dockerfile
├── docker-compose.yml          # Postgres+PostGIS for local dev only
├── .env.example                # Template of required env vars (no secrets)
├── requirements.txt            # Python dependencies
├── README.md                   # Setup, run, and test instructions
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan, CORS, router mounts
│   ├── config.py               # Settings loaded from .env (pydantic-settings)
│   ├── database.py             # SQLAlchemy async engine, session, table creation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py            # ORM model: events table
│   │   └── incident.py         # ORM model: incidents table
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── event.py            # Pydantic: EventCreate, EventResponse
│   │   └── incident.py         # Pydantic: IncidentResponse (exact contract fields)
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── events.py           # POST /events
│   │   └── incidents.py        # GET /incidents
│   │
│   └── services/
│       ├── __init__.py
│       ├── corroboration.py    # find-or-create incident, merge logic, bus tracking
│       └── severity.py         # type weights, severity formula, 0-10 mapping
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # pytest fixtures: test DB, async client, cleanup
    └── test_backend.py         # All 16 required test cases
```

### Files to CREATE (none pre-exist)

| Action | Path | Purpose |
|--------|------|---------|
| CREATE | `/backend/Dockerfile` | Containerise the FastAPI app |
| CREATE | `/backend/docker-compose.yml` | Run Postgres+PostGIS locally |
| CREATE | `/backend/.env.example` | Env var template |
| CREATE | `/backend/requirements.txt` | Python dependencies |
| CREATE | `/backend/README.md` | Setup and run guide |
| CREATE | `/backend/app/__init__.py` | Package marker |
| CREATE | `/backend/app/main.py` | FastAPI app entry point |
| CREATE | `/backend/app/config.py` | Pydantic Settings class |
| CREATE | `/backend/app/database.py` | Async engine + session |
| CREATE | `/backend/app/models/__init__.py` | Package marker |
| CREATE | `/backend/app/models/event.py` | `events` ORM model |
| CREATE | `/backend/app/models/incident.py` | `incidents` ORM model |
| CREATE | `/backend/app/schemas/__init__.py` | Package marker |
| CREATE | `/backend/app/schemas/event.py` | Event Pydantic schemas |
| CREATE | `/backend/app/schemas/incident.py` | Incident Pydantic schemas |
| CREATE | `/backend/app/routers/__init__.py` | Package marker |
| CREATE | `/backend/app/routers/events.py` | POST /events endpoint |
| CREATE | `/backend/app/routers/incidents.py` | GET /incidents endpoint |
| CREATE | `/backend/app/services/__init__.py` | Package marker |
| CREATE | `/backend/app/services/corroboration.py` | Core corroboration service |
| CREATE | `/backend/app/services/severity.py` | Severity config + formula |
| CREATE | `/backend/tests/__init__.py` | Package marker |
| CREATE | `/backend/tests/conftest.py` | Test fixtures |
| CREATE | `/backend/tests/test_backend.py` | 16 test cases |

**ZERO files created or modified outside `/backend`.**

---

## 2. FastAPI Architecture

- **Framework:** FastAPI (async)
- **ASGI server:** Uvicorn with `--reload` during development
- **ORM:** SQLAlchemy 2.x async (`asyncpg` driver)
- **Settings:** `pydantic-settings` reads `.env` file at startup
- **Lifespan:** `@asynccontextmanager` on the FastAPI app — runs `create_tables()` on startup, so the schema is always in sync without a migration tool
- **CORS:** `CORSMiddleware` with `allow_origins=["*"]` during development (unblocks Member C / Frontend)
- **Routing:** One `APIRouter` per domain (`events`, `incidents`)

### `app/main.py` responsibilities
- Instantiate `FastAPI(lifespan=lifespan)`
- Add `CORSMiddleware`
- Include `events_router` (prefix `/`)
- Include `incidents_router` (prefix `/`)

### `app/config.py` responsibilities
- `class Settings(BaseSettings)` reads all env vars
- Exposes `get_settings()` via `@lru_cache` so it is a singleton per process
- Contains: `DATABASE_URL`, `CORS_ORIGINS`, `TYPE_WEIGHTS` (JSON string), `SEVERITY_SCALE`

### `app/database.py` responsibilities
- Build `create_async_engine(settings.DATABASE_URL)`
- `AsyncSessionLocal` factory (`async_sessionmaker`)
- `get_db()` — FastAPI `Depends()` yielding a session per request
- `create_tables()` — called at startup, issues `CREATE TABLE IF NOT EXISTS` via SQLAlchemy metadata

---

## 3. Database Schema

### Technology: PostgreSQL 15 + PostGIS 3

PostGIS is used for:
- Storing points as `GEOGRAPHY(POINT, 4326)` — sphere-aware
- `ST_DWithin(a.location, b.location, 15)` — accurate metre-based proximity check without manual Haversine

### `events` Table

```sql
CREATE TABLE events (
    event_id    SERIAL          PRIMARY KEY,
    bus_id      VARCHAR(64)     NOT NULL,
    lat         DOUBLE PRECISION NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    location    GEOGRAPHY(POINT, 4326) NOT NULL,
    type        VARCHAR(32)     NOT NULL,
    confidence  FLOAT           NOT NULL,  -- 0.0 to 1.0
    timestamp   TIMESTAMPTZ     NOT NULL,
    incident_id UUID            REFERENCES incidents(incident_id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_incident ON events(incident_id);
CREATE INDEX idx_events_type     ON events(type);
CREATE INDEX idx_events_ts       ON events(timestamp);
```

**Notes:**
- `location` = `ST_SetSRID(ST_MakePoint(lon, lat), 4326)::GEOGRAPHY` — populated on INSERT from `lat`/`lon`
- `incident_id` is a FK back to `incidents` — set when the event is linked to an incident

### `incidents` Table

```sql
CREATE TABLE incidents (
    incident_id     UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    type            VARCHAR(32)     NOT NULL,
    lat             DOUBLE PRECISION NOT NULL,    -- centroid lat (updated on merge)
    lon             DOUBLE PRECISION NOT NULL,    -- centroid lon (updated on merge)
    location        GEOGRAPHY(POINT, 4326) NOT NULL,  -- centroid geography
    severity        FLOAT           NOT NULL,
    corroboration_count INT         NOT NULL DEFAULT 1,
    contributing_buses  TEXT[]      NOT NULL,     -- array of unique bus_ids
    mean_confidence FLOAT           NOT NULL,
    first_seen      TIMESTAMPTZ     NOT NULL,
    last_seen       TIMESTAMPTZ     NOT NULL,
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_incidents_location ON incidents USING GIST(location);
CREATE INDEX idx_incidents_type     ON incidents(type);
CREATE INDEX idx_incidents_severity ON incidents(severity DESC);
```

**Key design decisions:**

| Field | Rationale |
|-------|-----------|
| `UUID` PK | Stable, unguessable IDs — suitable for Frontend map markers |
| `contributing_buses TEXT[]` | PostgreSQL array of unique bus_id strings. Simple, no join table needed at hackathon scale. `ARRAY_LENGTH` gives corroboration_count; membership check prevents double-counting. |
| `lat`/`lon` floats | Stored alongside `location` for direct JSON serialisation without PostGIS decoding |
| `mean_confidence` | Running average, updated on each merge. Used in severity calculation. |
| `corroboration_count` | Derived from `ARRAY_LENGTH(contributing_buses)` but stored explicitly for fast reads |

**Relationship summary:**
- `events.incident_id → incidents.incident_id` (many-to-one)
- One incident owns many events
- An event has at most one incident

---

## 4. PostGIS Geographic Approach

**Column type:** `GEOGRAPHY(POINT, 4326)`

- Uses WGS84 ellipsoid coordinates (same as GPS)
- `ST_DWithin` on GEOGRAPHY columns measures distance in **metres** on the sphere
- No projection, no coordinate conversion needed

**The 15-metre query:**
```sql
SELECT i.*
FROM incidents i
WHERE i.type = :event_type
  AND ST_DWithin(i.location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::GEOGRAPHY, 15)
  AND i.last_seen >= :timestamp - INTERVAL '10 minutes'
ORDER BY ST_Distance(i.location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::GEOGRAPHY) ASC
LIMIT 1;
```

The GIST index on `incidents.location` makes this fast even with many incidents.

---

## 5. POST /events Flow

```
POST /events
    │
    ▼
Pydantic validation (EventCreate)
    │  ── rejects wrong type, confidence out of 0-1, missing fields
    │
    ▼
INSERT into events (all fields + location geography) → returns event_id
    │
    ▼
corroboration.find_or_create_incident(db, event)
    │
    ▼
  ┌─ ST_DWithin query: any matching incident?
  │   (same type, ≤15m, last_seen within 10 min of this event's timestamp)
  │
  ├── YES → merge event into existing incident
  │          update: centroid, last_seen, contributing_buses, mean_confidence, severity
  │          link: events.incident_id = incident.incident_id
  │
  └── NO → create new incident from this event
            link: events.incident_id = new incident's id
    │
    ▼
Return EventResponse { event_id, message }
```

**HTTP responses:**
- `200 OK` — event stored and processed
- `422 Unprocessable Entity` — validation failure (FastAPI default)
- `500 Internal Server Error` — unexpected DB error

---

## 6. Corroboration Algorithm (Incremental Per-Event)

### Why incremental (not batch DBSCAN)?

The updated specification explicitly requires incremental processing: store → find matching incident → merge or create. This avoids:
- Re-clustering the entire `events` table on every GET request
- Stale incident data between POSTs
- The `sklearn` dependency

Incremental corroboration with PostGIS `ST_DWithin` is simpler, faster, and directly maps to the event-driven nature of the problem.

### The Transitive Merging Problem — Explicit Analysis

> Concern: Event A ↔ B (within 15m), Event B ↔ C (within 15m), but A and C may be >15m apart.

**In batch DBSCAN,** this would merge A, B, and C into one cluster via transitivity — which could be inappropriate for events spread across a 30m arc.

**In the incremental approach proposed here,** each new event is matched against the **current centroid of an existing incident**, not against individual events. This behaves differently:

- When A arrives first → creates Incident₁, centroid = A.location
- When B arrives → centroid of Incident₁ is A. If B is within 15m of A → merged. Centroid updates to mean(A, B).
- When C arrives → centroid of Incident₁ is now mean(A, B). C is checked against this centroid.

**Analysis of the limitation:** If A and C are 20m apart but both within 15m of B, the centroid mean(A,B) might be roughly ~7-10m from C, so C **might** merge in. This is a soft boundary artefact inherent to centroid-based matching.

**Why this is acceptable for the hackathon:**
1. The spec says "approximately 15m" — not a hard legal boundary.
2. The alternative (per-event membership checking) requires O(n) queries per POST as the incident grows.
3. In urban bus GPS data, events that cluster within 15m of each other's centroid are almost certainly the same physical pothole.
4. If the centroid drifts due to many events, the cluster is self-correcting: events far from the centroid simply create new incidents.

**Stated limitation in the README:** Centroid-based matching can allow incidents to "drift" spatially as events merge. For higher precision, a maximum-diameter constraint can be added later.

### The 10-Minute Temporal Condition

The query filters: `i.last_seen >= :event_timestamp - INTERVAL '10 minutes'`

This means: an incident is a candidate only if it has seen activity within the 10-minute window relative to the incoming event's timestamp. Using `last_seen` (not `first_seen`) means an incident stays "active" as long as recent detections keep arriving.

**Edge case:** If event timestamps are not monotonically increasing (e.g., a delayed POST from a bus that went offline), this comparison still works correctly because it uses `event.timestamp` (the detection time), not `NOW()`.

### Unique-Bus Corroboration

```python
# On merge: only add bus_id if not already in contributing_buses
if event.bus_id not in incident.contributing_buses:
    incident.contributing_buses = incident.contributing_buses + [event.bus_id]
    incident.corroboration_count = len(incident.contributing_buses)
```

`contributing_buses` is a PostgreSQL `TEXT[]` array. Membership check before append enforces uniqueness. A bus reporting the same location 10 times still only appears once.

A repeated event from the same bus:
- **Does NOT** increase `corroboration_count`
- **Does** update `last_seen` if its timestamp is later
- **Does** contribute its confidence to `mean_confidence` (running average over all events)

This last point is an assumption (OQ-3). The alternative is to average only one confidence value per bus. Averaging all events smooths out variation from a noisy sensor.

### Centroid Update

When merging event E into an incident with N existing events:

```python
new_lat = (incident.lat * N + event.lat) / (N + 1)
new_lon = (incident.lon * N + event.lon) / (N + 1)
```

`N` is tracked implicitly as the count of linked events (queried by `COUNT(*) FROM events WHERE incident_id = ...`), or stored as a running counter. For hackathon simplicity: store a running `event_count` integer on the incident, avoiding a COUNT query on every merge.

---

## 7. Incident Creation / Merging

### Create new incident (no match found)

```python
new_incident = Incident(
    incident_id = uuid4(),  # generated by DB default
    type        = event.type,
    lat         = event.lat,
    lon         = event.lon,
    location    = ST_MakePoint(event.lon, event.lat),
    severity    = compute_severity(event.type, event.confidence, 1),
    corroboration_count = 1,
    contributing_buses  = [event.bus_id],
    mean_confidence     = event.confidence,
    first_seen  = event.timestamp,
    last_seen   = event.timestamp,
)
event.incident_id = new_incident.incident_id
```

### Merge into existing incident

```python
# 1. Update bus tracking
if event.bus_id not in incident.contributing_buses:
    incident.contributing_buses = incident.contributing_buses + [event.bus_id]
    incident.corroboration_count = len(incident.contributing_buses)

# 2. Update temporal bounds
if event.timestamp < incident.first_seen:
    incident.first_seen = event.timestamp
if event.timestamp > incident.last_seen:
    incident.last_seen = event.timestamp

# 3. Update centroid (running mean)
n = incident.event_count  # running counter
incident.lat = (incident.lat * n + event.lat) / (n + 1)
incident.lon = (incident.lon * n + event.lon) / (n + 1)
incident.location = ST_MakePoint(incident.lon, incident.lat)

# 4. Update mean confidence (running mean over all events)
incident.mean_confidence = (incident.mean_confidence * n + event.confidence) / (n + 1)
incident.event_count += 1

# 5. Recompute severity
incident.severity = compute_severity(
    incident.type,
    incident.mean_confidence,
    incident.corroboration_count
)

# 6. Link event
event.incident_id = incident.incident_id
```

---

## 8. Internal Confidence Calculation

`incident.mean_confidence` = running arithmetic mean of ALL contributing event confidences (regardless of bus).

**Why average over all events (not one per bus)?**

- Simple and transparent.
- Naturally up-weights high-corroboration incidents (more detections → more samples → more stable mean).
- Not exposed in the API contract, so the exact formula is an internal concern.

Alternative considered: average only the most recent confidence per bus. Rejected as more complex with no clear advantage at hackathon scale.

---

## 9. Type Weights, Severity Formula, and 0-10 Normalization

### Type Weights

> [!IMPORTANT]
> The following weights are **not specified by the API contract or build plan**. They are initial implementation assumptions. They must be kept in a single place (`app/services/severity.py` + `.env.example`) and are configurable via the `TYPE_WEIGHTS` environment variable.

| Type | Proposed Weight | Rationale |
|------|----------------|-----------|
| `pothole` | 8.0 | Immediate vehicle/safety damage |
| `road_damage` | 7.0 | Structural risk, slightly broader category |
| `obstruction` | 6.0 | Situational hazard, depends on severity |
| `congestion` | 5.0 | Traffic flow impact only, no physical danger |

### Severity Formula

```
raw_severity = type_weight × mean_confidence × ln(corroboration_count + 1)
```

Using natural log (`math.log`, base e) as specified.

### 0-10 Normalization — Proposed Strategy

**Problem:** The raw value is unbounded above. We must not assume a fleet size.

**Solution: Configurable linear scaling with a hard clamp.**

```python
severity = min(10.0, raw_severity * (10.0 / SEVERITY_SCALE))
```

Where `SEVERITY_SCALE` is an env var with a default of `8.0`.

**Rationale for default `SEVERITY_SCALE = 8.0`:**

The theoretical maximum raw value for `corroboration_count = 1` (single bus detection, max weight, perfect confidence) is:

```
8.0 (pothole) × 1.0 (confidence) × ln(1+1) ≈ 8.0 × 0.693 ≈ 5.55
```

For `corroboration_count = 3`:
```
8.0 × 1.0 × ln(4) ≈ 8.0 × 1.386 ≈ 11.09  → clamped to 10.0
```

So with `SEVERITY_SCALE = 8.0`, a pothole confirmed by 3 buses with perfect confidence scores ~10, which feels semantically correct.

With `SEVERITY_SCALE = 10.0`, the same case scores `~11.09 → clamped to 10`. Slightly less granular.

**The clamp (`min(10.0, ...)`) is always applied.** It is the safety net.

**Concrete examples:**

| Scenario | type_weight | mean_confidence | corroboration_count | raw | severity (scale=8) |
|----------|-------------|-----------------|---------------------|-----|---------------------|
| 1 bus, pothole, 0.87 | 8.0 | 0.87 | 1 | 8.0×0.87×ln(2) ≈ 4.83 | 4.83×(10/8) = **6.04** |
| 2 buses, pothole, 0.90 | 8.0 | 0.90 | 2 | 8.0×0.90×ln(3) ≈ 7.91 | 7.91×(10/8) = **9.89** |
| 3 buses, pothole, 0.95 | 8.0 | 0.95 | 3 | 8.0×0.95×ln(4) ≈ 10.53 | min(10, 13.16) = **10.00** |
| 1 bus, congestion, 0.70 | 5.0 | 0.70 | 1 | 5.0×0.70×ln(2) ≈ 2.43 | 2.43×(10/8) = **3.04** |

These values feel reasonable. `SEVERITY_SCALE` can be tuned without touching code.

---

## 10. Concurrency Strategy

**Scenario:** BUS_01 and BUS_02 POST the same pothole at almost exactly the same time. Two parallel FastAPI workers both query for a matching incident → both find none → both create a new incident → duplicate.

**Proposed solution: Advisory lock via PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` on `incidents`.**

More specifically:

```python
async with db.begin():
    # Step 1: Find candidate incident with a row-level lock
    result = await db.execute(
        select(Incident)
        .where(type_filter, spatial_filter, temporal_filter)
        .with_for_update()          # Lock the row
        .limit(1)
    )
    incident = result.scalar_one_or_none()

    if incident:
        # Step 2: Safe to merge — we hold the lock
        merge_event_into_incident(incident, event)
    else:
        # Step 3: Create new incident
        incident = create_incident_from_event(event)
        db.add(incident)
```

**Why this is appropriate for a hackathon:**

- FastAPI with a single Uvicorn worker is single-process (no concurrency concern at all)
- With multiple workers (default `--workers 1`), `SELECT FOR UPDATE` prevents the double-create race condition at the DB layer
- No Redis, no Celery, no distributed locks needed
- SQLAlchemy async supports `with_for_update()`

**Limitation stated:** Under very high concurrency (many workers), `FOR UPDATE` on the search query could become a bottleneck. Acceptable at hackathon scale.

---

## 11. GET /incidents Flow

```
GET /incidents
    │
    ▼
SELECT * FROM incidents
ORDER BY severity DESC
    │
    ▼
Serialize each row as IncidentResponse
    │  Fields: incident_id, lat, lon, type, severity,
    │           corroboration_count, first_seen, last_seen
    │
    ▼
Return JSON array
```

- No filters, no pagination (not in contract)
- Already deduplicated — each row in `incidents` IS one incident
- Severity already stored — no recomputation at read time
- `first_seen` and `last_seen` returned as ISO-8601 UTC strings

**`incident_id`** is a UUID stored in the DB. The API contract shows `"abc123"` as an example but specifies it as a `string`. UUID strings (`"3f2504e0-..."`) fully satisfy this.

---

## 12. Pydantic Schemas

### `schemas/event.py`

```python
class EventCreate(BaseModel):
    bus_id:     str
    lat:        float
    lon:        float
    timestamp:  datetime
    type:       Literal["pothole", "road_damage", "congestion", "obstruction"]
    confidence: float = Field(..., ge=0.0, le=1.0)

class EventResponse(BaseModel):
    event_id: int
    message:  str
```

### `schemas/incident.py`

```python
class IncidentResponse(BaseModel):
    incident_id:         str       # UUID as string
    lat:                 float
    lon:                 float
    type:                str
    severity:            float     # 0.0 – 10.0
    corroboration_count: int
    first_seen:          datetime
    last_seen:           datetime

    model_config = ConfigDict(from_attributes=True)
```

Field names match the API contract **exactly**. No renaming.

---

## 13. Dependencies

### `requirements.txt`

```
fastapi>=0.111.0          # Web framework
uvicorn[standard]>=0.30.0 # ASGI server
pydantic>=2.7.0           # Data validation
pydantic-settings>=2.3.0  # Settings from .env
sqlalchemy>=2.0.30        # Async ORM
asyncpg>=0.29.0           # Async PostgreSQL driver (required by SQLAlchemy async)
geoalchemy2>=0.15.0       # PostGIS column type + ST_* function wrappers
psycopg2-binary>=2.9.9    # Sync driver (used by GeoAlchemy2 DDL helpers at startup)
pytest>=8.2.0             # Test runner
pytest-asyncio>=0.23.0    # Async test support
httpx>=0.27.0             # Async HTTP client for FastAPI TestClient
```

**Why each dependency:**

| Package | Why |
|---------|-----|
| `fastapi` | The API framework |
| `uvicorn[standard]` | ASGI server with WebSocket support |
| `pydantic` | Request/response validation; FastAPI requires it |
| `pydantic-settings` | Load `.env` into typed Settings class |
| `sqlalchemy` | ORM; async engine for PostgreSQL |
| `asyncpg` | Async PostgreSQL driver; SQLAlchemy async requires it |
| `geoalchemy2` | Adds `GEOGRAPHY` column type + `ST_DWithin`, `ST_MakePoint` etc. to SQLAlchemy |
| `psycopg2-binary` | GeoAlchemy2 uses sync introspection during table creation; needed at startup |
| `pytest` | Test runner |
| `pytest-asyncio` | `async def test_*` support |
| `httpx` | `AsyncClient` for hitting FastAPI endpoints in tests |

**NOT included:** `scikit-learn`, `numpy`, `redis`, `celery` — none are needed for the incremental approach.

---

## 14. Environment Variables

### `.env.example`

```bash
# ── Database ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://urbaneye:urbaneye@localhost:5432/urbaneye_db

# ── App ───────────────────────────────────────────────────
APP_ENV=development
BACKEND_PORT=8000

# ── CORS ─────────────────────────────────────────────────
# Comma-separated allowed origins. Use * for development.
CORS_ORIGINS=*

# ── Severity ─────────────────────────────────────────────
# Raw severity is mapped to 0-10 as: min(10, raw * (10 / SEVERITY_SCALE))
# Default 8.0 means a pothole with 3 corroborating buses ≈ 10.0
SEVERITY_SCALE=8.0

# ── Type Weights (JSON) ──────────────────────────────────
# ASSUMPTION: These values are not in the API contract.
# Adjust to change how each event type contributes to severity.
TYPE_WEIGHTS={"pothole": 8.0, "road_damage": 7.0, "obstruction": 6.0, "congestion": 5.0}
```

No passwords hardcoded anywhere. `.env` is in `.gitignore` (already is).

---

## 15. Docker / PostgreSQL Setup

> [!IMPORTANT]
> No root-level `docker-compose.yml` exists. I will create `/backend/docker-compose.yml` only. The team must later decide whether to merge this into a root-level compose file. I will document the service specification clearly in the README so the integration is straightforward.

### `/backend/docker-compose.yml`

```yaml
services:
  db:
    image: postgis/postgis:15-3.4
    restart: unless-stopped
    environment:
      POSTGRES_USER: urbaneye
      POSTGRES_PASSWORD: urbaneye
      POSTGRES_DB: urbaneye_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U urbaneye -d urbaneye_db"]
      interval: 5s
      retries: 10

  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```

The `postgis/postgis:15-3.4` image auto-enables the PostGIS extension on first start.

### `/backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 16. Local Setup and Run Instructions

```bash
# ── Step 1: Go to backend directory ──────────────────────
cd /path/to/UrbanEye/backend

# ── Step 2: Create and activate virtual environment ───────
python3.11 -m venv .venv
source .venv/bin/activate

# ── Step 3: Install dependencies ─────────────────────────
pip install -r requirements.txt

# ── Step 4: Configure environment ────────────────────────
cp .env.example .env
# Edit .env if needed (default values work for local dev)

# ── Step 5: Start PostgreSQL + PostGIS ───────────────────
docker compose up -d db
# Wait ~5 seconds for postgres to be ready

# ── Step 6: Start FastAPI ─────────────────────────────────
uvicorn app.main:app --reload --port 8000

# ── Step 7: Verify API docs ───────────────────────────────
open http://localhost:8000/docs
```

### Manual curl test sequence

```bash
# Test POST /events — valid event
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

# Test second bus, same location, within 10 min
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

# Test GET /incidents — should show 1 incident, corroboration_count=2
curl -s http://localhost:8000/incidents | python3 -m json.tool

# Test invalid event type — should get 422
curl -s -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"bus_id":"BUS_01","lat":17.4239,"lon":78.4738,"timestamp":"2026-08-26T10:15:00Z","type":"earthquake","confidence":0.9}' \
  | python3 -m json.tool

# Test invalid confidence — should get 422
curl -s -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"bus_id":"BUS_01","lat":17.4239,"lon":78.4738,"timestamp":"2026-08-26T10:15:00Z","type":"pothole","confidence":1.5}' \
  | python3 -m json.tool
```

---

## 17. Testing Strategy

All tests in `/backend/tests/`. Use `pytest-asyncio` + `httpx.AsyncClient`.

### Test Database

Tests use a **real PostgreSQL + PostGIS test database** (same Docker container, different DB name: `urbaneye_test`). This is critical because PostGIS `ST_DWithin` and geography operations cannot be meaningfully mocked.

`conftest.py`:
1. Connects to `TEST_DATABASE_URL` (default: same host, db `urbaneye_test`)
2. Creates all tables once per session
3. Truncates `events` and `incidents` after each test for isolation
4. Provides `async_client` fixture (FastAPI `AsyncClient`)

### Test Cases (16 required)

| # | Test Name | What It Validates |
|---|-----------|-------------------|
| 1 | `test_valid_event_accepted` | POST valid event → HTTP 200, response has `event_id` |
| 2 | `test_invalid_event_type_rejected` | POST `type="earthquake"` → HTTP 422 |
| 3 | `test_invalid_confidence_rejected` | POST `confidence=1.5` → HTTP 422 |
| 4 | `test_invalid_coordinates_rejected` | POST `lat="abc"` → HTTP 422 |
| 5 | `test_event_stored_in_db` | POST event → query `events` table → row exists with correct fields |
| 6 | `test_two_buses_same_location_one_incident` | POST 2 events (diff buses, ≤15m, ≤10min) → GET /incidents → 1 incident, `corroboration_count=2` |
| 7 | `test_three_buses_corroboration_count_3` | 3 buses, same location → `corroboration_count=3` |
| 8 | `test_same_bus_no_extra_corroboration` | BUS_01 × 3 same location → `corroboration_count=1` |
| 9 | `test_far_apart_events_not_merged` | 2 events >50m apart → GET /incidents → 2 separate incidents |
| 10 | `test_outside_time_window_not_merged` | 2 events same location but 15 min apart → 2 separate incidents |
| 11 | `test_different_types_not_merged` | `pothole` + `congestion` same location/time → 2 separate incidents |
| 12 | `test_severity_increases_with_corroboration` | severity(3 buses) > severity(1 bus) for same type/location |
| 13 | `test_severity_in_0_10_range` | All incidents → `0.0 <= severity <= 10.0` |
| 14 | `test_incidents_deduplicated` | 5 events same location → GET /incidents returns exactly 1 incident |
| 15 | `test_incidents_ranked_by_severity` | Multiple incidents → returned in descending severity order |
| 16 | `test_concurrent_events_no_duplicate_incident` | Two events posted ~simultaneously (same location/type) → only 1 incident created |

Each test prints the actual JSON response. Tests assert on field values, not just status codes.

---

## 18. Integration Concerns

### Member A (Edge AI)
- Must send all 6 required fields in POST /events: `bus_id`, `lat`, `lon`, `timestamp`, `type`, `confidence`
- `type` must be one of `pothole`, `road_damage`, `congestion`, `obstruction`. Member A's `data.yaml` only defines `pothole` — the team must clarify which types the model can actually detect before the full system test
- `confidence` must be in `[0.0, 1.0]`. The backend will return HTTP 422 if it is outside this range
- `timestamp` must be a valid ISO-8601 datetime string. UTC is recommended
- Backend endpoint: `POST http://localhost:8000/events`

### Member C (Frontend)
- `GET http://localhost:8000/incidents` returns the full incident list sorted by severity descending
- CORS is open (`*`) during development — no proxy configuration needed
- `incident_id` is a UUID string — stable across multiple calls, safe to use as a map marker key
- `severity` is a `float` (0–10), not an integer — frontend should render as a decimal
- `first_seen` and `last_seen` are ISO-8601 UTC strings

### Member D (Simulator)
- The simulator sends `POST /events` with the same schema as Member A
- The backend is fully testable without the simulator (see manual curl sequence above)
- Simulator should use the exact `type` vocabulary defined in the contract
- For load testing: the backend handles concurrent POSTs safely via `SELECT FOR UPDATE`

---

## 19. Assumptions

1. Python 3.11+ is used for development.
2. Docker is available locally for PostgreSQL+PostGIS.
3. `postgis/postgis:15-3.4` Docker image auto-enables PostGIS extension on first start (confirmed behaviour of that image).
4. `ln` (natural log, `math.log`) is the intended log function in the severity formula.
5. An event from the same bus updates `last_seen` and contributes to `mean_confidence` but not `corroboration_count`.
6. Two events of different types at the same location are **not** merged (type must match for corroboration).
7. Events are not expired from incidents over time — all incidents remain active unless a team decision is made to add expiry.
8. `GET /incidents` returns all incidents sorted by severity descending, no pagination.
9. The `incident_id` in the contract example `"abc123"` is illustrative; a UUID4 string is used as the actual implementation.
10. Single Uvicorn worker is used for development; `SELECT FOR UPDATE` is the concurrency guard.
11. `lat`/`lon` are valid geographic coordinates (FastAPI validates they are floats, but not that they are within [-90,90]/[-180,180] — PostGIS will error on invalid values, which is acceptable).

---

## 20. What Requires Team Action (Not My Responsibility)

| Item | Who | What |
|------|-----|------|
| Root `docker-compose.yml` | Team | If a unified compose file is needed, the `db` service from `/backend/docker-compose.yml` must be merged in |
| Member A event types | Member A | Confirm which of `pothole/road_damage/congestion/obstruction` the edge model can detect |
| Type weight approval | Team | Confirm or revise the proposed weights before release |
| `SEVERITY_SCALE` tuning | Team | Can be adjusted post-integration via `.env` without code change |

