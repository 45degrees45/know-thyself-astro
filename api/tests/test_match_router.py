"""Integration test for POST /api/cofounder-match."""
import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app


@pytest.fixture
def mock_geocode(monkeypatch):
    monkeypatch.setattr(
        "api.routers.match.geocode",
        lambda place: {"lat": 9.58, "lon": 76.54, "timezone": "Asia/Kolkata", "display": place},
    )


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


PAYLOAD = {
    "person_a": {
        "name": "Alice",
        "date": "1985-03-07",
        "time": "07:15",
        "time_accuracy": "exact",
        "place": "Kangazha, Kerala",
    },
    "person_b": {
        "name": "Bob",
        "date": "1988-11-22",
        "time": "09:00",
        "time_accuracy": "exact",
        "place": "Mumbai, India",
    },
}


async def test_cofounder_match_returns_200_with_score(client, mock_geocode):
    response = await client.post("/api/cofounder-match", json=PAYLOAD)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 100
    assert data["score_label"] in ("Exceptional", "Strong", "Good", "Workable", "Challenging")
    assert "dimensions" in data
    assert "startup_timing" in data
    assert "role_suggestion" in data
    assert data["accuracy_warning"] is None


async def test_unknown_time_sets_warning(client, mock_geocode):
    payload = {
        **PAYLOAD,
        "person_a": {**PAYLOAD["person_a"], "time_accuracy": "unknown"},
    }
    response = await client.post("/api/cofounder-match", json=payload)
    assert response.status_code == 200
    assert response.json()["accuracy_warning"] == "person_a_unknown"


async def test_approximate_time_sets_warning(client, mock_geocode):
    payload = {
        **PAYLOAD,
        "person_b": {**PAYLOAD["person_b"], "time_accuracy": "approximate"},
    }
    response = await client.post("/api/cofounder-match", json=payload)
    assert response.status_code == 200
    assert response.json()["accuracy_warning"] == "person_b_approximate"


async def test_missing_required_field_returns_422(client, mock_geocode):
    bad = {"person_a": {"name": "Alice"}}  # missing person_b and required fields
    response = await client.post("/api/cofounder-match", json=bad)
    assert response.status_code == 422
