"""
app/services/corroboration.py – Core incremental corroboration service.

Algorithm per POST /events:
  1. Search `incidents` for a matching row:
       same type  AND  ≤ 15 m away (PostGIS ST_DWithin)
       AND  last_seen >= event.timestamp - 10 minutes
     Use SELECT FOR UPDATE to guard against concurrent duplicate creation.
  2. If found  → merge event into existing incident (update centroid,
                  contributing_buses, mean_confidence, severity).
  3. If not found → create a new incident from this event.
  4. Link event.incident_id to the incident.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_DWithin
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.incident import Incident
from app.services.severity import compute_severity

# Corroboration radius in metres
RADIUS_METRES: float = 15.0

# Maximum age of an incident's last_seen relative to the incoming event's
# timestamp for it to be a candidate.
TIME_WINDOW: timedelta = timedelta(minutes=10)


def _make_wkt(lon: float, lat: float) -> WKTElement:
    """Return a GeoAlchemy2 WKTElement for a geography point."""
    return WKTElement(f"POINT({lon} {lat})", srid=4326, extended=False)


async def find_or_create_incident(
    db: AsyncSession,
    event: Event,
) -> Incident:
    """Find an existing matching incident or create a new one.

    Uses table-level SHARE ROW EXCLUSIVE lock (which allows concurrent SELECTs
    such as GET /incidents, but serializes concurrent incident insertions/merges)
    and SELECT FOR UPDATE to prevent duplicate-incident race conditions when
    multiple workers process events concurrently.

    Args:
        db:    Async SQLAlchemy session (transaction must be managed by caller).
        event: The newly-inserted Event ORM object.

    Returns:
        The matched or newly-created Incident.
    """
    await db.execute(text("LOCK TABLE incidents IN SHARE ROW EXCLUSIVE MODE"))

    event_wkt = _make_wkt(event.lon, event.lat)
    earliest_last_seen = event.timestamp - TIME_WINDOW


    # ── Step 1: Find candidate incident (with row lock) ──────────────────
    stmt = (
        select(Incident)
        .where(
            Incident.type == event.type,
            ST_DWithin(
                Incident.location,
                event_wkt,
                RADIUS_METRES,
            ),
            Incident.last_seen >= earliest_last_seen,
        )
        .limit(1)
        .with_for_update()
    )

    result = await db.execute(stmt)
    incident: Incident | None = result.scalar_one_or_none()

    if incident is not None:
        # ── Step 2: Merge event into existing incident ───────────────────
        _merge_event(incident, event)
    else:
        # ── Step 3: Create new incident ──────────────────────────────────
        incident = _create_incident(event)
        db.add(incident)
        await db.flush()  # Populate incident_id from DB default

    # ── Step 4: Link event to incident ───────────────────────────────────
    event.incident_id = incident.incident_id

    return incident


# ── Internal helpers ──────────────────────────────────────────────────────────

def _create_incident(event: Event) -> Incident:
    """Build a new Incident from a single Event."""
    return Incident(
        incident_id=uuid.uuid4(),
        type=event.type,
        lat=event.lat,
        lon=event.lon,
        location=f"SRID=4326;POINT({event.lon} {event.lat})",
        severity=compute_severity(event.type, event.confidence, 1),
        corroboration_count=1,
        contributing_buses=[event.bus_id],
        mean_confidence=event.confidence,
        event_count=1,
        first_seen=event.timestamp,
        last_seen=event.timestamp,
    )


def _merge_event(incident: Incident, event: Event) -> None:
    """Merge an event into an existing incident (in-place mutation).

    Updates:
      - contributing_buses / corroboration_count
      - first_seen / last_seen
      - centroid (running mean)
      - mean_confidence (running mean over all events)
      - severity (recomputed)
    """
    n = incident.event_count  # number of events already in incident

    # 1. Bus tracking (unique buses only)
    if event.bus_id not in incident.contributing_buses:
        incident.contributing_buses = incident.contributing_buses + [event.bus_id]
        incident.corroboration_count = len(incident.contributing_buses)

    # 2. Temporal bounds
    if event.timestamp < incident.first_seen:
        incident.first_seen = event.timestamp
    if event.timestamp > incident.last_seen:
        incident.last_seen = event.timestamp

    # 3. Centroid update (running mean)
    new_lat = (incident.lat * n + event.lat) / (n + 1)
    new_lon = (incident.lon * n + event.lon) / (n + 1)
    incident.lat = new_lat
    incident.lon = new_lon
    incident.location = f"SRID=4326;POINT({new_lon} {new_lat})"

    # 4. Mean confidence update (running mean over all events)
    incident.mean_confidence = (incident.mean_confidence * n + event.confidence) / (n + 1)

    # 5. Event count
    incident.event_count = n + 1

    # 6. Recompute severity
    incident.severity = compute_severity(
        incident.type,
        incident.mean_confidence,
        incident.corroboration_count,
    )
