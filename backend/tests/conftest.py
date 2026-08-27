"""
tests/conftest.py – Pytest fixtures for the UrbanEye backend test suite.

Setup:
  - Connects to a real PostgreSQL + PostGIS TEST database (urbaneye_test).
    PostGIS geographic operations cannot be meaningfully mocked, so a
    real DB is required.
  - Creates all tables once per session.
  - Truncates `events` and `incidents` after EACH test for isolation.
  - Provides an `async_client` fixture backed by httpx.AsyncClient.

Environment:
  - TEST_DATABASE_URL env var (optional) overrides the default.
  - Default: postgresql+asyncpg://urbaneye:urbaneye@localhost:5432/urbaneye_test
"""
from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

# ── Test database URL ─────────────────────────────────────────────────────────
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://urbaneye:urbaneye@localhost:5432/urbaneye_test",
)

# ── Engine and session factory ────────────────────────────────────────────────
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Session-scoped: create tables once ───────────────────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all ORM tables in the test database once per test session."""
    import app.models.event     # noqa: F401 – register metadata
    import app.models.incident  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Tear-down: drop all tables after the session (optional – keeps DB clean)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Function-scoped: truncate tables before each test ────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate events and incidents before each test for isolation."""
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE events, incidents RESTART IDENTITY CASCADE"))
    yield


# ── Override the app's get_db dependency ─────────────────────────────────────
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


# ── Async HTTP client fixture ─────────────────────────────────────────────────
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an httpx AsyncClient pointed at the FastAPI test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
