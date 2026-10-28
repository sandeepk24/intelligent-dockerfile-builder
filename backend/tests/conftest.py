"""Shared test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.memory_store import MemoryStore
from app.db.store import store
from app.main import app


@pytest.fixture(autouse=True)
def reset_store():
    store.configure(MemoryStore(), "memory")
    yield
    store.clear()


@pytest.fixture
async def client():
    """Async test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
