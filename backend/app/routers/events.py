"""
app/routers/events.py – POST /events endpoint.

Flow:
  1. Pydantic validates the request body (EventCreate).
  2. Insert the raw event row into `events`.
  3. Call corroboration.find_or_create_incident() to link it to an incident.
  4. Commit the transaction.
  5. Return EventResponse { event_id, message }.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse
from app.services.corroboration import find_or_create_incident

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a detected urban event",
)
async def post_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Accept a raw detection event from the edge AI or bus simulator.

    - Validates the payload (422 on failure).
    - Stores the event in the database.
    - Runs incremental corroboration to find or create a matching incident.
    - Returns the assigned event_id.
    """
    try:
        async with db.begin():
            # Build the Event ORM object.
            # The `location` geography column is populated via WKT string
            # so SQLAlchemy/GeoAlchemy2 can parse it without a round-trip.
            event = Event(
                bus_id=payload.bus_id,
                lat=payload.lat,
                lon=payload.lon,
                location=f"SRID=4326;POINT({payload.lon} {payload.lat})",
                type=payload.type,
                confidence=payload.confidence,
                timestamp=payload.timestamp,
            )
            db.add(event)
            await db.flush()  # Populate event.event_id from the SERIAL PK

            # Corroboration: find or create an incident, link the event.
            await find_or_create_incident(db, event)

    except Exception as exc:
        # Log and surface as 500 — FastAPI will also produce 422 for
        # validation errors before this handler is reached.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process event: {exc}",
        ) from exc

    return EventResponse(
        event_id=event.event_id,
        message="Event received and processed.",
    )
