"""
app/schemas/event.py – Pydantic schemas for event request/response.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    """Validates the body of POST /events.

    Matches the API contract exactly:
      bus_id, lat, lon, timestamp, type, confidence
    """

    bus_id: str
    lat: float
    lon: float
    timestamp: datetime
    type: Literal["pothole", "road_damage", "congestion", "obstruction"]
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("timestamp", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        """Ensure the timestamp is timezone-aware and normalized to UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)



class EventResponse(BaseModel):
    """Response returned by POST /events on success."""

    event_id: int
    message: str
