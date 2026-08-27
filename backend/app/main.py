"""
app/main.py – FastAPI application entry point.

Responsibilities:
  - Instantiate the FastAPI app with a lifespan context manager.
  - Add CORSMiddleware (open during development).
  - Mount the events and incidents routers.
  - Run create_tables() at startup so the schema is always in sync.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables
from app.routers.events import router as events_router
from app.routers.incidents import router as incidents_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup logic before the app serves requests."""
    await create_tables()
    yield
    # (cleanup on shutdown can go here if needed)


app = FastAPI(
    title="UrbanEye Backend",
    description=(
        "Corroboration and severity-scoring API for urban events "
        "detected by bus-mounted AI cameras."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(events_router)
app.include_router(incidents_router)


@app.get("/health", tags=["health"], summary="Health check")
async def health() -> dict:
    """Simple liveness check — returns OK when the server is running."""
    return {"status": "ok"}
