import pytest
from api.services.astro_service import AstroService

def test_calculate_chart_returns_lagna():
    svc = AstroService()
    result = svc.calculate(
        birth_date="1985-03-07",
        birth_time="07:15",
        birth_place="Kangazha, Kerala",
    )
    assert result["lagna"] == "Pisces"
    assert 0 < result["lagna_deg"] < 30
    assert "yogas" in result
    assert isinstance(result["yogas"], list)

def test_chart_summary_has_animal():
    svc = AstroService()
    chart_json = svc.calculate("1985-03-07", "07:15", "Kangazha, Kerala")
    summary = svc.build_summary(chart_json)
    assert "animal" in summary
    assert summary["lagna"] == "Pisces"
    assert "current_dasha" in summary

def test_build_summary_extracts_fields():
    svc = AstroService()
    chart_json = {
        "lagna": "Aries", "lagna_deg": 5.0,
        "current_dasha": "Jupiter/Venus/Sun",
        "yogas": ["Hamsa", "Gajakesari", "Raja Yoga", "Bhadra"],
        "animal": "Eagle", "animal_emoji": "🦅",
        "planets": {}, "moon_nakshatra": "Ashwini",
        "yoga_details": [], "raw_chart": {},
    }
    summary = svc.build_summary(chart_json)
    assert summary["lagna"] == "Aries"
    assert summary["animal_emoji"] == "🦅"
    assert len(summary["yogas"]) == 3  # only first 3
    assert "lagna_deg" in summary
    assert "current_dasha" in summary
    assert len(summary) == 6  # exactly 6 keys
