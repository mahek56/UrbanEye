"""
tests/test_backend.py – All 16 required test cases for the UrbanEye backend.

Each test uses a real PostgreSQL + PostGIS test database (see conftest.py).
Tests assert on field values, not just HTTP status codes.

Test index:
  1.  test_valid_event_accepted
  2.  test_invalid_event_type_rejected
  3.  test_invalid_confidence_rejected
  4.  test_invalid_coordinates_rejected
  5.  test_event_stored_in_db
  6.  test_two_buses_same_location_one_incident
  7.  test_three_buses_corroboration_count_3
  8.  test_same_bus_no_extra_corroboration
  9.  test_far_apart_events_not_merged
  10. test_outside_time_window_not_merged
  11. test_different_types_not_merged
  12. test_severity_increases_with_corroboration
  13. test_severity_in_0_10_range
  14. test_incidents_deduplicated
  15. test_incidents_ranked_by_severity
  16. test_concurrent_events_no_duplicate_incident
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select, text

from app.models.event import Event
from app.models.incident import Incident
from tests.conftest import TestSessionLocal

pytestmark = pytest.mark.asyncio

# ── Shared event payloads ─────────────────────────────────────────────────────

BASE_LAT = 17.4239
BASE_LON = 78.4738
BASE_TS  = "2026-08-26T10:15:00Z"

def _event(
    bus_id: str = "BUS_01",
    lat: float = BASE_LAT,
    lon: float = BASE_LON,
    timestamp: str = BASE_TS,
    type_: str = "pothole",
    confidence: float = 0.87,
) -> Dict[str, Any]:
    return {
        "bus_id": bus_id,
        "lat": lat,
        "lon": lon,
        "timestamp": timestamp,
        "type": type_,
        "confidence": confidence,
    }


async def _post(client: AsyncClient, **kwargs) -> Any:
    """Helper: POST /events and return the response."""
    return await client.post("/events", json=_event(**kwargs))


async def _incidents(client: AsyncClient) -> list:
    """Helper: GET /incidents and return the JSON list."""
    resp = await client.get("/incidents")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Test 1 ────────────────────────────────────────────────────────────────────

async def test_valid_event_accepted(async_client: AsyncClient):
    """POST a valid event → HTTP 200 with event_id in response."""
    resp = await _post(async_client)
    print("T1 response:", resp.json())
    assert resp.status_code == 200
    body = resp.json()
    assert "event_id" in body
    assert isinstance(body["event_id"], int)
    assert body["event_id"] >= 1


# ── Test 2 ────────────────────────────────────────────────────────────────────

async def test_invalid_event_type_rejected(async_client: AsyncClient):
    """POST event with type='earthquake' → HTTP 422."""
    resp = await _post(async_client, type_="earthquake")
    print("T2 response:", resp.json())
    assert resp.status_code == 422


# ── Test 3 ────────────────────────────────────────────────────────────────────

async def test_invalid_confidence_rejected(async_client: AsyncClient):
    """POST event with confidence=1.5 (out of range) → HTTP 422."""
    resp = await _post(async_client, confidence=1.5)
    print("T3 response:", resp.json())
    assert resp.status_code == 422


# ── Test 4 ────────────────────────────────────────────────────────────────────

async def test_invalid_coordinates_rejected(async_client: AsyncClient):
    """POST event with lat='abc' (wrong type) → HTTP 422."""
    payload = _event()
    payload["lat"] = "abc"
    resp = await async_client.post("/events", json=payload)
    print("T4 response:", resp.json())
    assert resp.status_code == 422


# ── Test 5 ────────────────────────────────────────────────────────────────────

async def test_event_stored_in_db(async_client: AsyncClient):
    """POST event → query events table → row exists with correct fields."""
    resp = await _post(async_client, bus_id="BUS_STORE")
    assert resp.status_code == 200
    event_id = resp.json()["event_id"]

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(Event).where(Event.event_id == event_id)
        )
        row = result.scalar_one_or_none()

    print("T5 DB row:", row)
    assert row is not None
    assert row.bus_id == "BUS_STORE"
    assert row.type == "pothole"
    assert abs(row.lat - BASE_LAT) < 1e-6
    assert row.confidence == pytest.approx(0.87)
    assert row.incident_id is not None


# ── Test 6 ────────────────────────────────────────────────────────────────────

async def test_two_buses_same_location_one_incident(async_client: AsyncClient):
    """2 buses, ≤15m apart, ≤10min apart → 1 incident, corroboration_count=2."""
    await _post(async_client, bus_id="BUS_01", timestamp="2026-08-26T10:15:00Z")
    await _post(async_client, bus_id="BUS_02",
                lat=BASE_LAT + 0.00005,   # ~5.5m north
                lon=BASE_LON + 0.00005,
                timestamp="2026-08-26T10:18:00Z")

    incidents = await _incidents(async_client)
    print("T6 incidents:", incidents)
    assert len(incidents) == 1
    assert incidents[0]["corroboration_count"] == 2


# ── Test 7 ────────────────────────────────────────────────────────────────────

async def test_three_buses_corroboration_count_3(async_client: AsyncClient):
    """3 buses, same location → corroboration_count=3."""
    for bus in ("BUS_A", "BUS_B", "BUS_C"):
        await _post(async_client, bus_id=bus)

    incidents = await _incidents(async_client)
    print("T7 incidents:", incidents)
    assert len(incidents) == 1
    assert incidents[0]["corroboration_count"] == 3


# ── Test 8 ────────────────────────────────────────────────────────────────────

async def test_same_bus_no_extra_corroboration(async_client: AsyncClient):
    """BUS_01 × 3 same location → corroboration_count stays 1."""
    for _ in range(3):
        await _post(async_client, bus_id="BUS_01")

    incidents = await _incidents(async_client)
    print("T8 incidents:", incidents)
    assert len(incidents) == 1
    assert incidents[0]["corroboration_count"] == 1


# ── Test 9 ────────────────────────────────────────────────────────────────────

async def test_far_apart_events_not_merged(async_client: AsyncClient):
    """2 events >50m apart → 2 separate incidents."""
    await _post(async_client, bus_id="BUS_01", lat=BASE_LAT, lon=BASE_LON)
    # ~55m east: 0.0005° lon ≈ 55m at this latitude
    await _post(async_client, bus_id="BUS_02",
                lat=BASE_LAT, lon=BASE_LON + 0.0005)

    incidents = await _incidents(async_client)
    print("T9 incidents:", incidents)
    assert len(incidents) == 2


# ── Test 10 ───────────────────────────────────────────────────────────────────

async def test_outside_time_window_not_merged(async_client: AsyncClient):
    """2 events, same location, 15 min apart → 2 separate incidents."""
    await _post(async_client, bus_id="BUS_01", timestamp="2026-08-26T10:00:00Z")
    await _post(async_client, bus_id="BUS_02", timestamp="2026-08-26T10:15:00Z")

    incidents = await _incidents(async_client)
    print("T10 incidents:", incidents)
    assert len(incidents) == 2


# ── Test 11 ───────────────────────────────────────────────────────────────────

async def test_different_types_not_merged(async_client: AsyncClient):
    """pothole + congestion, same location and time → 2 separate incidents."""
    await _post(async_client, bus_id="BUS_01", type_="pothole")
    await _post(async_client, bus_id="BUS_02", type_="congestion")

    incidents = await _incidents(async_client)
    print("T11 incidents:", incidents)
    assert len(incidents) == 2


# ── Test 12 ───────────────────────────────────────────────────────────────────

async def test_severity_increases_with_corroboration(async_client: AsyncClient):
    """severity after 3-bus corroboration > severity after 1-bus detection."""
    # First bus — 1 corroboration
    await _post(async_client, bus_id="BUS_01", confidence=0.9)
    incidents_1 = await _incidents(async_client)
    sev_1 = incidents_1[0]["severity"]
    print("T12 severity after 1 bus:", sev_1)

    # Second and third buses
    await _post(async_client, bus_id="BUS_02", confidence=0.9)
    await _post(async_client, bus_id="BUS_03", confidence=0.9)
    incidents_3 = await _incidents(async_client)
    sev_3 = incidents_3[0]["severity"]
    print("T12 severity after 3 buses:", sev_3)

    assert sev_3 > sev_1


# ── Test 13 ───────────────────────────────────────────────────────────────────

async def test_severity_in_0_10_range(async_client: AsyncClient):
    """All returned incidents must have severity in [0.0, 10.0]."""
    # Create incidents of different types / confidences
    combos = [
        ("BUS_01", "pothole",     0.99),
        ("BUS_02", "road_damage", 0.50),
        ("BUS_03", "congestion",  0.01),
        ("BUS_04", "obstruction", 0.75),
    ]
    for bus_id, type_, conf in combos:
        await _post(async_client, bus_id=bus_id, type_=type_, confidence=conf)

    # Corroborate the pothole with 5 more buses to push raw severity high
    for i in range(5, 11):
        await _post(async_client, bus_id=f"BUS_{i:02d}", type_="pothole",
                    confidence=1.0)

    incidents = await _incidents(async_client)
    print("T13 incidents:", incidents)
    for inc in incidents:
        assert 0.0 <= inc["severity"] <= 10.0, (
            f"severity {inc['severity']} out of range for incident {inc['incident_id']}"
        )


# ── Test 14 ───────────────────────────────────────────────────────────────────

async def test_incidents_deduplicated(async_client: AsyncClient):
    """5 events at the same location → GET /incidents returns exactly 1 incident."""
    for i in range(5):
        await _post(async_client, bus_id=f"BUS_{i:02d}")

    incidents = await _incidents(async_client)
    print("T14 incidents:", incidents)
    assert len(incidents) == 1


# ── Test 15 ───────────────────────────────────────────────────────────────────

async def test_incidents_ranked_by_severity(async_client: AsyncClient):
    """Multiple incidents → returned in descending severity order."""
    # High-severity: pothole, 3 buses
    for bus in ("BUS_A1", "BUS_A2", "BUS_A3"):
        await _post(async_client, bus_id=bus, type_="pothole",
                    lat=BASE_LAT, lon=BASE_LON, confidence=0.95)

    # Low-severity: congestion, 1 bus, far away
    await _post(async_client, bus_id="BUS_B1", type_="congestion",
                lat=BASE_LAT + 0.01,   # ~1.1km away, definitely separate
                lon=BASE_LON + 0.01,
                confidence=0.20)

    incidents = await _incidents(async_client)
    print("T15 incidents:", incidents)
    assert len(incidents) == 2
    assert incidents[0]["severity"] >= incidents[1]["severity"]
    assert incidents[0]["type"] == "pothole"


# ── Test 16 ───────────────────────────────────────────────────────────────────

async def test_concurrent_events_no_duplicate_incident(async_client: AsyncClient):
    """Two events posted concurrently at the same location → only 1 incident."""
    tasks = [
        _post(async_client, bus_id="BUS_C1"),
        _post(async_client, bus_id="BUS_C2"),
    ]
    responses = await asyncio.gather(*tasks)
    print("T16 responses:", [r.json() for r in responses])
    for resp in responses:
        assert resp.status_code == 200

    incidents = await _incidents(async_client)
    print("T16 incidents:", incidents)
    assert len(incidents) == 1
    assert incidents[0]["corroboration_count"] == 2
