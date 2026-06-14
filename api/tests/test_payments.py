"""
TDD tests for POST /api/payments/order and POST /api/payments/verify.

Uses an in-memory async SQLite DB via dependency override so no real DB is needed.
Note: razorpay is stubbed in conftest.py (pkg_resources is absent in this venv).
"""
import hmac
import hashlib
import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
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
# Helper: seed a user + chart directly into the test DB
# ---------------------------------------------------------------------------
async def create_user_and_chart() -> tuple[str, str]:
    async with TestAsyncSession() as session:
        user = User(
            id=str(uuid.uuid4()),
            email=f"pay-{uuid.uuid4()}@test.com",
            name="Payer",
        )
        session.add(user)
        await session.flush()
        chart = Chart(
            id=str(uuid.uuid4()),
            user_id=user.id,
            birth_date="1985-03-07",
            birth_time="07:15",
            birth_place="Kangazha",
            lat=9.58,
            lon=76.54,
            tz="Asia/Kolkata",
            chart_json={
                "lagna": "Pisces",
                "lagna_deg": 7.5,
                "current_dasha": "Rahu/Venus",
                "yogas": [],
                "animal": "Elephant",
                "animal_emoji": "🐘",
                "moon_nakshatra": "Revati",
                "planets": {},
            },
        )
        session.add(chart)
        await session.commit()
        return user.id, chart.id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_create_order_returns_order_id(client):
    _, chart_id = await create_user_and_chart()
    mock_order = {"id": "order_test123", "amount": 5000, "currency": "INR"}
    with patch("api.routers.payments.razorpay.Client") as MockRzp:
        MockRzp.return_value.order.create.return_value = mock_order
        resp = await client.post("/api/payments/order", json={"chart_id": chart_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_id"] == "order_test123"
    assert data["amount"] == 5000
    assert "key_id" in data


async def test_create_order_404_for_missing_chart(client):
    resp = await client.post("/api/payments/order", json={"chart_id": "nonexistent"})
    assert resp.status_code == 404


async def test_verify_payment_marks_user_paid(client):
    _, chart_id = await create_user_and_chart()
    # conftest.py sets RAZORPAY_KEY_SECRET=test-rzp-secret
    key_secret = "test-rzp-secret"
    order_id = "order_abc"
    payment_id = "pay_xyz"
    sig = hmac.new(
        key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    resp = await client.post("/api/payments/verify", json={
        "chart_id": chart_id,
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": sig,
    })
    assert resp.status_code == 200
    assert resp.json()["paid"] is True


async def test_verify_payment_rejects_invalid_signature(client):
    _, chart_id = await create_user_and_chart()
    resp = await client.post("/api/payments/verify", json={
        "chart_id": chart_id,
        "razorpay_order_id": "order_abc",
        "razorpay_payment_id": "pay_xyz",
        "razorpay_signature": "invalid_sig",
    })
    assert resp.status_code == 400
