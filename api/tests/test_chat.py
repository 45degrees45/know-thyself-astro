"""
TDD tests for POST /api/chat (SSE) and question bank endpoints.

Tests:
1. test_chat_404_for_nonexistent_chart
2. test_chat_403_when_free_limit_exceeded
3. test_chat_streams_sse_for_paid_user
4. test_questions_returns_list
5. test_questions_click_increments_count
"""
import json
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import app
from api.models import Base, User, Chart, ChatMessage, QuestionBank
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
# Helpers
# ---------------------------------------------------------------------------
SAMPLE_CHART_JSON = {
    "lagna": "Pisces",
    "lagna_deg": 7.5,
    "current_dasha": "Rahu/Venus/Venus",
    "yogas": ["Gajakesari", "Hamsa"],
    "animal": "Elephant",
    "animal_emoji": "🐘",
    "moon_nakshatra": "Revati",
    "planets": {},
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
# Chat tests
# ---------------------------------------------------------------------------

async def test_chat_404_for_nonexistent_chart(client):
    """POST /api/chat with unknown chart_id should return 404."""
    resp = await client.post("/api/chat", json={
        "chart_id": str(uuid.uuid4()),
        "tab": "know_thyself",
        "message": "What is my lagna?",
    })
    assert resp.status_code == 404


async def test_chat_403_when_free_limit_exceeded(client):
    """Unpaid user with 5+ messages in the last 24h should get 403."""
    _, chart_id = await create_test_user_and_chart(paid=False)

    # Insert 5 user messages within the last 24 hours directly into the test DB
    async with TestAsyncSession() as session:
        for i in range(5):
            session.add(ChatMessage(
                chart_id=chart_id,
                tab="know_thyself",
                role="user",
                content=f"Message {i}",
                created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            ))
        await session.commit()

    resp = await client.post("/api/chat", json={
        "chart_id": chart_id,
        "tab": "know_thyself",
        "message": "One more question",
    })
    assert resp.status_code == 403
    assert "free" in resp.json()["detail"].lower() or "limit" in resp.json()["detail"].lower()


async def test_chat_streams_sse_for_paid_user(client):
    """Paid user should receive SSE stream from the chat endpoint."""
    _, chart_id = await create_test_user_and_chart(paid=True)

    # Mock LLMAdapter.stream to yield two chunks
    async def fake_stream(message, system):
        yield "Hello "
        yield "world"

    mock_adapter = MagicMock()
    mock_adapter.stream = fake_stream

    with patch("api.services.report_service._make_adapter", return_value=mock_adapter):
        # Also patch AsyncSessionLocal to avoid production DB writes
        with patch("api.routers.chat.AsyncSessionLocal") as mock_session_local:
            # Make the context manager work as a no-op
            mock_save_session = AsyncMock()
            mock_save_session.__aenter__ = AsyncMock(return_value=mock_save_session)
            mock_save_session.__aexit__ = AsyncMock(return_value=False)
            mock_save_session.add = MagicMock()
            mock_save_session.commit = AsyncMock()
            mock_session_local.return_value = mock_save_session

            resp = await client.post("/api/chat", json={
                "chart_id": chart_id,
                "tab": "know_thyself",
                "message": "Tell me about my lagna",
            })

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    body = resp.text
    lines = [line for line in body.split("\n") if line.startswith("data:")]

    # Should have 2 chunk lines + 1 [DONE] line
    assert len(lines) == 3

    # Check chunk content
    chunk_lines = lines[:2]
    for line in chunk_lines:
        payload = json.loads(line[len("data: "):].strip())
        assert "text" in payload

    # Last line should be [DONE]
    assert lines[-1] == "data: [DONE]"


# ---------------------------------------------------------------------------
# Question bank tests
# ---------------------------------------------------------------------------

async def test_questions_returns_list(client):
    """GET /api/questions/know_thyself should return a list of questions."""
    # Seed some questions into the test DB
    async with TestAsyncSession() as session:
        for i in range(3):
            session.add(QuestionBank(
                tab="know_thyself",
                question=f"Question {i}?",
                click_count=i,
                active=True,
            ))
        # Also add a question for a different tab — should not appear
        session.add(QuestionBank(
            tab="career",
            question="Career question?",
            click_count=0,
            active=True,
        ))
        await session.commit()

    resp = await client.get("/api/questions/know_thyself")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 3
    # All should be know_thyself questions
    for item in data:
        assert "id" in item
        assert "question" in item
        assert "clicks" in item


async def test_questions_click_increments_count(client):
    """POST /api/questions/{id}/click should increment click_count by 1."""
    # Seed a question
    async with TestAsyncSession() as session:
        q = QuestionBank(
            tab="know_thyself",
            question="Who am I?",
            click_count=5,
            active=True,
        )
        session.add(q)
        await session.commit()
        question_id = q.id

    resp = await client.post(f"/api/questions/{question_id}/click")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # Verify the count was incremented
    async with TestAsyncSession() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(QuestionBank).where(QuestionBank.id == question_id)
        )
        updated = result.scalar_one()
        assert updated.click_count == 6
