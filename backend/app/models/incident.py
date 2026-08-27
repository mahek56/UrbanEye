"""
app/models/incident.py – ORM model for the `incidents` table.

Defined BEFORE event.py because Event has a FK → Incident.
"""
from __future__ import annotations

import sys
import os
# Add the backend directory to sys.path to enable running this file directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
     ARRAY,
     DateTime,
     Float,
     Integer,
     String,
     Text,
     func,
 )
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Incident(Base):
    """Represents a corroborated urban incident.

    Each incident is the aggregation of one or more raw events that are:
      - the same type
      - within 15 m of each other (centroid-based)
      - reported within a 10-minute rolling window
    """

    __tablename__ = "incidents"

    # ── Primary key ──────────────────────────────────────────────────────
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # ── Classification ───────────────────────────────────────────────────
    type: Mapped[str] = mapped_column(String(32), nullable=False)

    # ── Centroid (stored as plain floats for fast JSON serialisation) ─────
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Geography column (used for PostGIS spatial queries) ───────────────
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # ── Severity (pre-computed, updated on every merge) ──────────────────
    severity: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Corroboration tracking ───────────────────────────────────────────
    corroboration_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    contributing_buses: Mapped[list] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    mean_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Running counter of all linked events (used for running mean of
    # centroid and mean_confidence without an extra COUNT query).
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ── Temporal bounds ──────────────────────────────────────────────────
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
