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
