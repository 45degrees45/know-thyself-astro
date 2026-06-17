"""Tests for trusted tier and profile HTML generation."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import app
from api.models import Base
from api.database import get_db
from api.services.astro_service import AstroService

# ── Test database ────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestAsyncSession() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_geocode(monkeypatch):
    monkeypatch.setattr(
        "api.services.astro_service.geocode",
        lambda place: {"lat": 9.58, "lon": 76.54, "timezone": "Asia/Kolkata", "display_name": place},
    )


# ── Sample chart data ────────────────────────────────────────────────────────

SAMPLE_CHART_JSON = {
    "lagna": "Pisces",
    "lagna_deg": 2.4,
    "planets": {
        "Sun":     {"sign": "Gemini",      "degrees": 15.2, "house": 4, "nakshatra": "Ardra",            "pada": 2, "retrograde": False},
        "Moon":    {"sign": "Capricorn",   "degrees": 8.7,  "house": 11,"nakshatra": "Shravana",          "pada": 1, "retrograde": False},
        "Mars":    {"sign": "Scorpio",     "degrees": 22.1, "house": 9, "nakshatra": "Jyeshtha",          "pada": 3, "retrograde": False},
        "Mercury": {"sign": "Gemini",      "degrees": 5.3,  "house": 4, "nakshatra": "Mrigashira",        "pada": 4, "retrograde": True},
        "Jupiter": {"sign": "Libra",       "degrees": 11.0, "house": 8, "nakshatra": "Swati",             "pada": 2, "retrograde": False},
        "Venus":   {"sign": "Taurus",      "degrees": 29.8, "house": 3, "nakshatra": "Krittika",          "pada": 1, "retrograde": False},
        "Saturn":  {"sign": "Capricorn",   "degrees": 3.5,  "house": 11,"nakshatra": "Uttara Ashadha",    "pada": 2, "retrograde": False},
        "Rahu":    {"sign": "Virgo",       "degrees": 14.2, "house": 7, "nakshatra": "Hasta",             "pada": 3, "retrograde": True},
        "Ketu":    {"sign": "Pisces",      "degrees": 14.2, "house": 1, "nakshatra": "Uttara Bhadrapada", "pada": 4, "retrograde": True},
    },
    "moon_nakshatra": "Shravana",
    "yogas": ["Adhi Yoga", "NBRY", "Guru-Chandala"],
    "yoga_details": [
        {"name": "Adhi Yoga",     "description": "Mercury, Venus, Jupiter in 6th/7th/8th from Moon"},
        {"name": "NBRY",          "description": "No benefics in kendras"},
        {"name": "Guru-Chandala", "description": "Jupiter-Rahu conjunction"},
    ],
    "current_dasha": "Mercury/Ketu/Mercury",
    "animal": "Monkey",
    "animal_emoji": "🐒",
    "lat": 8.5241,
    "lon": 76.9366,
    "tz": "Asia/Kolkata",
}


# ── Profile HTML generator tests ─────────────────────────────────────────────

def test_generate_profile_html_returns_string():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert isinstance(html, str)
    assert len(html) > 1000


def test_generate_profile_html_contains_lagna():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Pisces" in html


def test_generate_profile_html_contains_name():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Jinx" in html


def test_generate_profile_html_contains_dasha():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Mercury" in html


def test_generate_profile_html_contains_animal():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Monkey" in html or "🐒" in html


# ── Integration tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_chart_includes_trusted_false():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/chart", json={
            "name": "Test", "birth_date": "1990-01-01", "birth_time": "12:00",
            "birth_place": "Mumbai, India", "email": "test@example.com"
        })
        assert r.status_code == 201
        chart_id = r.json()["chart_id"]
        r2 = await client.get(f"/api/chart/{chart_id}")
        assert r2.status_code == 200
        assert r2.json()["trusted"] == False


@pytest.mark.asyncio
async def test_reading_endpoint_returns_404_before_html_ready():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/chart", json={
            "name": "Test", "birth_date": "1990-01-01", "birth_time": "12:00",
            "birth_place": "Mumbai, India", "email": "test2@example.com"
        })
        chart_id = r.json()["chart_id"]
        r2 = await client.get(f"/api/chart/{chart_id}/reading")
        assert r2.status_code == 404


@pytest.mark.asyncio
async def test_admin_generate_trusted_codes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "admin-dev-secret", "count": 2, "note": "for Ruhi"
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["codes"]) == 2
        assert all(c["code"].startswith("TRUST-") for c in data["codes"])


@pytest.mark.asyncio
async def test_admin_generate_trusted_codes_wrong_secret():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "wrong", "count": 1
        })
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_redeem_trusted_code_grants_permanent_access():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        gen = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "admin-dev-secret", "count": 1
        })
        code = gen.json()["codes"][0]["code"]

        chart_r = await client.post("/api/chart", json={
            "name": "Ruhi", "birth_date": "2002-03-03", "birth_time": "02:00",
            "birth_place": "Alleppey, Kerala", "email": "ruhi@test.com"
        })
        chart_id = chart_r.json()["chart_id"]

        redeem = await client.post("/api/demo/redeem", json={"code": code, "chart_id": chart_id})
        assert redeem.status_code == 200
        assert redeem.json()["trusted"] == True
        assert redeem.json().get("expires_at") is None

        get_r = await client.get(f"/api/chart/{chart_id}")
        assert get_r.json()["trusted"] == True


@pytest.mark.asyncio
async def test_whitelist_auto_grants_trusted_on_chart_create():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/admin/whitelist/add", json={
            "secret": "admin-dev-secret", "email": "wl@test.com", "note": "test"
        })

        chart_r = await client.post("/api/chart", json={
            "name": "Whitelisted", "birth_date": "1985-05-15", "birth_time": "10:00",
            "birth_place": "Chennai, India", "email": "wl@test.com"
        })
        assert chart_r.status_code == 201
        assert chart_r.json()["trusted"] == True
