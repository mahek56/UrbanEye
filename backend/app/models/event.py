"""
app/models/event.py – ORM model for the `events` table.
"""
from __future__ import annotations

import sys
import os
# Add the backend directory to sys.path to enable running this file directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import uuid
from datetime import datetime

from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.incident import Incident



class Event(Base):
    """Represents a single raw detection event from a bus.

    After insertion, an event is linked to an incident via the
    corroboration service (find_or_create_incident).
    """

    __tablename__ = "events"

    # ── Primary key ──────────────────────────────────────────────────────
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Source ───────────────────────────────────────────────────────────
    bus_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # ── Location ─────────────────────────────────────────────────────────
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # ── Classification ───────────────────────────────────────────────────
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Timing ───────────────────────────────────────────────────────────
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Incident FK (set after corroboration) ─────────────────────────────
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.incident_id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # ORM relationship (lazy-loaded, read-only reference)
    incident: Mapped["Incident | None"] = relationship(
        "Incident", foreign_keys=[incident_id], lazy="select"
    )
