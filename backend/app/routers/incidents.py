"""
app/routers/incidents.py – GET /incidents endpoint.

Returns all incidents ordered by severity descending.
No filters, no pagination (not in the API contract).
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentResponse

router = APIRouter(tags=["incidents"])


@router.get(
    "/incidents",
    response_model=List[IncidentResponse],
    status_code=200,
    summary="Retrieve all verified incidents",
)
async def get_incidents(
    db: AsyncSession = Depends(get_db),
) -> List[IncidentResponse]:
    """Return all incidents sorted by severity descending.

    Each row in the `incidents` table is already deduplicated and
    pre-scored — no recomputation is needed at read time.
    """
    result = await db.execute(
        select(Incident).order_by(Incident.severity.desc())
    )
    incidents = result.scalars().all()

    return [
        IncidentResponse(
            incident_id=str(inc.incident_id),
            lat=inc.lat,
            lon=inc.lon,
            type=inc.type,
            severity=inc.severity,
            corroboration_count=inc.corroboration_count,
            first_seen=inc.first_seen,
            last_seen=inc.last_seen,
        )
        for inc in incidents
    ]
