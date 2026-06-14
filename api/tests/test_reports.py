"""
TDD tests for GET /api/report/{chart_id} — SSE streaming report.

Tests:
1. 403 for unpaid users
2. 404 for nonexistent chart_id
3. SSE stream returned for paid users (LLMAdapter mocked)
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import app
from api.models import Base, User, Chart
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


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Helper: create a user + chart in the test DB
# ---------------------------------------------------------------------------
SAMPLE_CHART_JSON = {
    "lagna": "Pisces",
    "lagna_deg": 7.5,
    "current_dasha": "Rahu/Venus/Venus",
    "yogas": ["Gajakesari", "Hamsa"],
    "animal": "Elephant",
    "animal_emoji": "🐘",
    "moon_nakshatra": "Revati",
    "planets": {
        "Sun": {"sign": "Pisces", "house": 1},
        "Moon": {"sign": "Cancer", "house": 5},
    },
}


async def create_test_user_and_chart(paid: bool = False) -> tuple[str, str]:
    """Insert a User + Chart into the test DB and return (user_id, chart_id)."""
    async with TestAsyncSession() as session:
        user = User(
            id=str(uuid.uuid4()),
            email=f"test-{uuid.uuid4()}@example.com",
            name="Test User",
            paid=paid,
        )
        session.add(user)
        await session.flush()

        chart = Chart(
            id=str(uuid.uuid4()),
            user_id=user.id,
            birth_date="1985-03-07",
            birth_time="07:15",
            birth_place="Kangazha, Kerala",
            lat=9.58,
            lon=76.54,
            tz="Asia/Kolkata",
            chart_json=SAMPLE_CHART_JSON,
        )
        session.add(chart)
        await session.commit()
        return user.id, chart.id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_report_404_for_nonexistent_chart(client):
    """GET /api/report/<random-id> should return 404."""
    response = await client.get(f"/api/report/{uuid.uuid4()}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_report_403_for_unpaid_user(client):
    """GET /api/report/<chart_id> should return 403 when user.paid is False."""
    _, chart_id = await create_test_user_and_chart(paid=False)
    response = await client.get(f"/api/report/{chart_id}")
    assert response.status_code == 403
    assert "payment" in response.json()["detail"].lower()


async def test_report_streams_sse_for_paid_user(client):
    """GET /api/report/<chart_id> streams SSE data: lines for paid users."""
    _, chart_id = await create_test_user_and_chart(paid=True)

    # Fake async generator that yields two chunks
    async def fake_stream_report(chart_json, name):
        yield "Hello "
        yield "world"

    with patch("api.routers.reports._report_svc.stream_report", side_effect=fake_stream_report):
        response = await client.get(f"/api/report/{chart_id}")

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    lines = [line for line in body.split("\n") if line.startswith("data:")]

    # Should have 2 chunk lines + 1 [DONE] line
    assert len(lines) == 3

    # Check chunk lines contain JSON with 'text' key
    import json
    chunk_lines = lines[:2]
    for line in chunk_lines:
        payload = json.loads(line[len("data: "):].strip())
        assert "text" in payload

    # Last line should be [DONE] sentinel
    assert lines[-1] == "data: [DONE]"
