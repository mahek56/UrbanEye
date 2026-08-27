"""
app/schemas/incident.py – Pydantic schema for the GET /incidents response.

Field names match the API contract EXACTLY.  No aliasing.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentResponse(BaseModel):
    """Serialises one row from the `incidents` table for the API response.

    incident_id is stored as UUID in the DB but serialised as a plain
    string — the contract example uses "abc123" which is illustrative;
    a UUID4 string fully satisfies the `string` type requirement.
    """

    model_config = ConfigDict(from_attributes=True)

    incident_id: str          # UUID serialised as string
    lat: float
    lon: float
    type: str
    severity: float           # 0.0 – 10.0
    corroboration_count: int
    first_seen: datetime
    last_seen: datetime
