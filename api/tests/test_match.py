"""Unit tests for astro_engine/match.py — scoring engine."""
from datetime import datetime
import pytest

from astro_engine.match import (
    score_working_style,
    score_drive,
    score_vision,
    score_timing_sync,
    suggest_roles,
    match_cofounders,
    _accuracy_warning,
    _score_label,
)


# ---------------------------------------------------------------------------
# Helpers — build minimal chart dicts
# ---------------------------------------------------------------------------

SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _chart(
    moon_nak: str,
    moon_sign: str,
    mars_sign: str,
    merc_sign: str,
    jup_sign: str,
    sun_sign: str,
    sat_sign: str,
    asc_sign: str,
    moon_lon: float = 0.0,
) -> dict:
    """Minimal chart dict sufficient for all match.py functions."""
    asc_idx = SIGNS_LIST.index(asc_sign)
    return {
        "ascendant": {"sign": asc_sign, "sign_index": asc_idx, "degrees": 5.0},
        "planets": {
            "Moon":    {"sign": moon_sign,  "longitude": moon_lon, "nakshatra": moon_nak},
            "Mars":    {"sign": mars_sign,  "longitude": 0.0},
            "Mercury": {"sign": merc_sign,  "longitude": 0.0},
            "Jupiter": {"sign": jup_sign,   "longitude": 0.0},
            "Sun":     {"sign": sun_sign,   "longitude": 0.0},
            "Saturn":  {"sign": sat_sign,   "longitude": 0.0},
        },
        "birth_utc": "1985-03-07T01:45:00",
    }


# ---------------------------------------------------------------------------
# score_working_style
# ---------------------------------------------------------------------------

def test_working_style_mixed_taras_returns_60():
    # Ashwini (idx 0) ↔ Rohini (idx 3)
    # Tara A→B: (3-0)%27%9+1 = 4 (favorable → 90)
    # Tara B→A: (0-3)%27%9+1 = 24%9+1 = 7 (challenging → 30)
    # Score = (90+30)/2 = 60
    a = _chart("Ashwini", "Aries",  "Leo", "Gemini", "Cancer",     "Leo",    "Capricorn", "Pisces")
    b = _chart("Rohini",  "Taurus", "Leo", "Gemini", "Sagittarius","Scorpio","Capricorn", "Virgo")
    result = score_working_style(a, b)
    assert result["score"] == 60
    assert result["label"] == "Good"
    assert "Ashwini" in result["detail"]
    assert "Rohini" in result["detail"]


def test_working_style_both_favorable_returns_90():
    # Ashwini (idx 0) ↔ Mrigashira (idx 4)
    # Tara A→B: (4-0)%27%9+1 = 4+1 = 5 — wait, 4%9+1=5 (challenging)
    # Let me pick Ashwini↔Bharani: B=idx1
    # Tara A→B: (1-0)%27%9+1=1+1=2 (favorable→90)
    # Tara B→A: (0-1)%27%9+1=26%9+1=8+1=9 (favorable→90)
    # Score=(90+90)/2=90
    a = _chart("Ashwini", "Aries",  "Leo", "Gemini", "Cancer", "Leo", "Capricorn", "Pisces")
    b = _chart("Bharani", "Aries",  "Leo", "Gemini", "Cancer", "Leo", "Capricorn", "Pisces")
    result = score_working_style(a, b)
    assert result["score"] == 90
    assert result["label"] == "Exceptional"


# ---------------------------------------------------------------------------
# score_drive
# ---------------------------------------------------------------------------

def test_drive_friendly_mars_signs_no_h10():
    # Mars A: Leo (lord=Sun), Mars B: Sagittarius (lord=Jupiter)
    # Sun↔Jupiter: both mutual friends → mars_rel=1.0
    # Merc A: Gemini (lord=Mercury), Merc B: Virgo (lord=Mercury)
    # Mercury↔Mercury: not in friends/enemies → rel=0 → merc_rel=0
    # total=1.0 → score_map[1]=75
    a = _chart("Ashwini","Aries","Leo",        "Gemini","Cancer","Leo","Capricorn","Aries")
    b = _chart("Rohini", "Taurus","Sagittarius","Virgo", "Cancer","Leo","Capricorn","Aries")
    result = score_drive(a, b, use_houses_a=False, use_houses_b=False)
    assert result["score"] == 75
    assert "Leo" in result["detail"]
    assert "Sagittarius" in result["detail"]


def test_drive_h10_bonus_applied():
    # Mars A: Scorpio. Chart B has Aquarius ascendant → H10 = Scorpio.
    # So Mars A sign == B's H10 sign → +15 bonus
    # mars_rel neutral (Mars↔Mars=0), merc_rel=0 → base score=60 → 60+15=75
    a = _chart("Ashwini","Aries","Scorpio","Gemini","Cancer","Leo","Capricorn","Aries")
    b = _chart("Rohini","Taurus","Aries","Gemini","Cancer","Leo","Capricorn","Aquarius")
    # Aquarius asc (idx 10) → H10 = SIGNS[(10+9)%12] = SIGNS[7] = Scorpio ✓
    result = score_drive(a, b, use_houses_a=True, use_houses_b=True)
    assert result["score"] >= 75
    assert "H10 bonus" in result["detail"]


def test_drive_h10_bonus_skipped_when_house_unknown():
    a = _chart("Ashwini","Aries","Scorpio","Gemini","Cancer","Leo","Capricorn","Aries")
    b = _chart("Rohini","Taurus","Aries","Gemini","Cancer","Leo","Capricorn","Aquarius")
    result_with = score_drive(a, b, use_houses_a=True, use_houses_b=True)
    result_without = score_drive(a, b, use_houses_a=False, use_houses_b=False)
    assert result_with["score"] > result_without["score"]


# ---------------------------------------------------------------------------
# score_vision
# ---------------------------------------------------------------------------

def test_vision_mutual_aspects_score():
    # Jupiter A: Cancer (idx 3) → aspects Scorpio(7), Capricorn(9), Pisces(11)
    # Jupiter B: Sagittarius (idx 8) → aspects Aries(0), Gemini(2), Leo(4)
    # B's Sun=Scorpio → in A's aspects → +1
    # A's Sun=Leo → in B's aspects → +1
    # Jupiter lord: Cancer→Moon, Sagittarius→Jupiter
    # Moon↔Jupiter: Moon not in Jupiter's enemies, Jupiter not in Moon's friends (Sun,Mercury only)
    # _planet_relation("Moon","Jupiter")=0, _planet_relation("Jupiter","Moon")=+1 → jup_rel=0.5>0 → pts+=1
    # Total pts=3 → score=78
    a = _chart("Ashwini","Cancer","Leo","Gemini","Cancer","Leo","Capricorn","Pisces")
    b = _chart("Rohini","Aries","Leo","Gemini","Sagittarius","Scorpio","Capricorn","Virgo")
    result = score_vision(a, b)
    assert result["score"] == 78
    assert "Cancer" in result["detail"]
    assert "Sagittarius" in result["detail"]


# ---------------------------------------------------------------------------
# score_timing_sync
# ---------------------------------------------------------------------------

def test_timing_sync_full_overlap_scores_95():
    windows_a = [{"start": "2026-01-01", "end": "2027-06-01", "dasha": "Jupiter/Venus", "quality": "favorable"}]
    windows_b = [{"start": "2026-01-01", "end": "2027-06-01", "dasha": "Venus/Jupiter", "quality": "favorable"}]
    result = score_timing_sync(windows_a, windows_b)
    assert result["score"] == 95
    assert len(result["overlap_zones"]) >= 1
    assert "★ Best window" in result["overlap_zones"][0]["label"]


def test_timing_sync_no_overlap_both_favorable_scores_50():
    windows_a = [{"start": "2026-01-01", "end": "2026-03-01", "dasha": "Jupiter/Venus", "quality": "favorable"}]
    windows_b = [{"start": "2027-01-01", "end": "2027-06-01", "dasha": "Venus/Jupiter", "quality": "favorable"}]
    result = score_timing_sync(windows_a, windows_b)
    assert result["score"] == 50
    assert result["overlap_zones"] == []


def test_timing_sync_no_favorable_at_all_scores_35():
    windows_a = [{"start": "2026-01-01", "end": "2026-06-01", "dasha": "Saturn/Rahu", "quality": "challenging"}]
    windows_b = [{"start": "2026-01-01", "end": "2026-06-01", "dasha": "Rahu/Saturn", "quality": "challenging"}]
    result = score_timing_sync(windows_a, windows_b)
    assert result["score"] == 35


# ---------------------------------------------------------------------------
# suggest_roles
# ---------------------------------------------------------------------------

def test_suggest_roles_visionary_vs_executor():
    # Jupiter exalted in Cancer → dignity=3 for person_a
    # Saturn own sign Capricorn → dignity=2 for person_b
    a = _chart("Ashwini","Cancer","Leo","Gemini","Cancer","Leo","Aries","Pisces")   # Jupiter exalted
    b = _chart("Rohini","Taurus","Scorpio","Gemini","Leo","Leo","Capricorn","Virgo") # Saturn own sign
    result = suggest_roles(a, b)
    assert result["person_a"] == "Visionary / Strategy"
    assert result["person_b"] == "Execution / Operations"


# ---------------------------------------------------------------------------
# _accuracy_warning
# ---------------------------------------------------------------------------

def test_accuracy_warning_none_for_exact():
    assert _accuracy_warning("exact", "exact") is None

def test_accuracy_warning_person_a_approximate():
    assert _accuracy_warning("approximate", "exact") == "person_a_approximate"

def test_accuracy_warning_person_b_unknown():
    assert _accuracy_warning("exact", "unknown") == "person_b_unknown"

def test_accuracy_warning_both_approximate():
    assert _accuracy_warning("approximate", "approximate") == "both_approximate"

def test_accuracy_warning_both_unknown_when_one_unknown():
    assert _accuracy_warning("unknown", "approximate") == "both_unknown"


# ---------------------------------------------------------------------------
# _score_label
# ---------------------------------------------------------------------------

def test_score_labels():
    assert _score_label(90) == "Exceptional"
    assert _score_label(74) == "Strong"
    assert _score_label(60) == "Good"
    assert _score_label(45) == "Workable"
    assert _score_label(30) == "Challenging"


# ---------------------------------------------------------------------------
# match_cofounders integration
# ---------------------------------------------------------------------------

def test_match_cofounders_returns_full_structure():
    a = _chart("Ashwini","Aries","Leo","Gemini","Cancer","Leo","Capricorn","Pisces", moon_lon=0.0)
    b = _chart("Bharani","Aries","Leo","Gemini","Cancer","Leo","Capricorn","Virgo",  moon_lon=13.5)
    birth_a = datetime(1985, 3, 7, 1, 45)
    birth_b = datetime(1988, 11, 22, 3, 30)
    result = match_cofounders(a, b, "Alice", "Bob", birth_a, birth_b)
    assert "overall_score" in result
    assert 0 <= result["overall_score"] <= 100
    assert result["score_label"] in ("Exceptional", "Strong", "Good", "Workable", "Challenging")
    assert result["accuracy_warning"] is None
    dims = result["dimensions"]
    assert all(k in dims for k in ("working_style", "drive", "vision", "timing_sync"))
    assert all(0 <= dims[k]["score"] <= 100 for k in dims)
    assert "person_a" in result["role_suggestion"]
    assert "person_b" in result["role_suggestion"]
    timing = result["startup_timing"]
    assert "person_a" in timing and "person_b" in timing and "overlap_zones" in timing
