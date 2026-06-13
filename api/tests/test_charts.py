"""
TDD tests for POST /api/chart and GET /api/chart/{id}.

Uses an in-memory async SQLite DB via dependency override so no real DB is needed.
TestClient runs the ASGI app synchronously; async fixtures handle DB lifecycle.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import app
from api.models import Base
from api.database import get_db

# ---------------------------------------------------------------------------
# Test database — in-memory async SQLite
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestAsyncSession() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper: async HTTP client using ASGI transport (no real server needed)
# ---------------------------------------------------------------------------
@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
GOLDY_PAYLOAD = {
    "name": "Goldy",
    "birth_date": "1985-03-07",
    "birth_time": "07:15",
    "birth_place": "Kangazha, Kerala",
    "email": "goldy@test.com",
}


async def test_post_chart_returns_chart_id(client):
    response = await client.post("/api/chart", json=GOLDY_PAYLOAD)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "chart_id" in data
    assert data["lagna"] == "Pisces"
    assert isinstance(data["lagna_deg"], float)
    assert isinstance(data["yogas"], list)
    assert "current_dasha" in data
    assert "animal" in data
    assert "animal_emoji" in data


async def test_get_chart_returns_summary(client):
    post = await client.post("/api/chart", json=GOLDY_PAYLOAD)
    assert post.status_code == 200, post.text
    chart_id = post.json()["chart_id"]

    get = await client.get(f"/api/chart/{chart_id}")
    assert get.status_code == 200, get.text
    data = get.json()
    assert data["lagna"] == "Pisces"
    assert data["chart_id"] == chart_id
    assert "paid" in data
    assert data["paid"] is False  # new user is unpaid


async def test_get_chart_not_found(client):
    get = await client.get("/api/chart/nonexistent-id")
    assert get.status_code == 404


async def test_post_chart_upserts_user_on_duplicate_email(client):
    """Posting the same email twice should not create duplicate users."""
    r1 = await client.post("/api/chart", json=GOLDY_PAYLOAD)
    assert r1.status_code == 200
    r2 = await client.post("/api/chart", json=GOLDY_PAYLOAD)
    assert r2.status_code == 200
    # Both charts exist, but same user
    assert r1.json()["chart_id"] != r2.json()["chart_id"]


async def test_post_chart_invalid_place(client):
    bad = {**GOLDY_PAYLOAD, "birth_place": "ZZZNOTAPLACE999"}
    response = await client.post("/api/chart", json=bad)
    assert response.status_code == 422
