# Cofounder Matching & Startup Timing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a stateless cofounder compatibility tool that scores two Vedic birth charts across 4 dimensions and shows startup timing windows.

**Architecture:** Three new files — `astro_engine/match.py` (pure scoring engine), `api/routers/match.py` (thin FastAPI router), `docs/cofounder/index.html` (self-contained HTML/JS frontend). The router calls `calculate_chart` and `geocode` from existing modules, then delegates all scoring to `match.py`. No database writes.

**Tech Stack:** Python 3.12, FastAPI, pyswisseph (Swiss Ephemeris already installed), vanilla JS + Astrowise design system CSS.

## Global Constraints

- Always use `.venv/bin/python3` — bare `python` is not in PATH
- Run pytest from project root: `.venv/bin/python3 -m pytest api/tests/ -v`
- All astro_engine imports use `from astro_engine.X import Y` (project root on sys.path)
- Whole Sign house system throughout — house N sign = `SIGNS[(asc_sign_idx + N - 1) % 12]`
- Sidereal (Lahiri ayanamsha) longitudes — `chart["planets"]["Moon"]["longitude"]` is already sidereal
- `birth_utc` in chart dict is an ISO datetime string (UTC, no tzinfo suffix): `"1985-03-07T01:45:00"`
- Frontend API_BASE must be set to the deployed Railway URL before pushing to production

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `astro_engine/match.py` | Create | All scoring logic — pure functions, no I/O |
| `api/routers/match.py` | Create | FastAPI endpoint — orchestrates geocode + calc + match |
| `api/main.py` | Modify | Register new router |
| `api/tests/test_match.py` | Create | Unit tests for scoring engine |
| `api/tests/test_match_router.py` | Create | Integration test for endpoint |
| `docs/cofounder/index.html` | Create | Self-contained frontend |

---

### Task 1: Scoring Engine (`astro_engine/match.py`)

**Files:**
- Create: `astro_engine/match.py`
- Create: `api/tests/test_match.py`

**Interfaces:**
- Consumes: `astro_engine.calc.SIGNS`, `astro_engine.calc.NAKSHATRAS`, `astro_engine.yoga.SIGN_LORD`, `astro_engine.yoga.EXALT_SIGN`, `astro_engine.yoga.DEBIL_SIGN`, `astro_engine.yoga.OWN_SIGNS`, `astro_engine.dasha.calculate_dashas`, `astro_engine.dasha.calculate_bhuktis`
- Produces: `match_cofounders(chart_a, chart_b, name_a, name_b, birth_dt_a, birth_dt_b, time_accuracy_a, time_accuracy_b) -> dict` and `get_startup_timing(moon_lon, birth_dt) -> list[dict]`

- [ ] **Step 1: Write the failing tests**

Create `api/tests/test_match.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/python3 -m pytest api/tests/test_match.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'astro_engine.match'`

- [ ] **Step 3: Create `astro_engine/match.py`**

```python
"""
Vedic cofounder compatibility scoring engine.

Scoring dimensions (25% each):
  1. Working Style  — Moon nakshatra Tara compatibility
  2. Drive          — Mars + Mercury sign lord friendship
  3. Vision         — Jupiter aspect harmony
  4. Timing Sync    — Dasha overlap (next 5 years)

Entry point:
    result = match_cofounders(chart_a, chart_b, name_a, name_b,
                              birth_dt_a, birth_dt_b,
                              time_accuracy_a, time_accuracy_b)
"""
from datetime import datetime, timezone as _tz

from astro_engine.calc import SIGNS, NAKSHATRAS
from astro_engine.yoga import SIGN_LORD, EXALT_SIGN, DEBIL_SIGN, OWN_SIGNS
from astro_engine.dasha import calculate_dashas, calculate_bhuktis

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLANET_FRIENDS: dict[str, dict[str, list[str]]] = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"],      "enemies": ["Venus", "Saturn"]},
    "Moon":    {"friends": ["Sun", "Mercury"],               "enemies": []},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"],       "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"],                 "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"],          "enemies": ["Mercury", "Venus"]},
    "Venus":   {"friends": ["Mercury", "Saturn"],            "enemies": ["Sun", "Moon"]},
    "Saturn":  {"friends": ["Mercury", "Venus"],             "enemies": ["Sun", "Moon", "Mars"]},
}

FAVORABLE_DASHA = {"Jupiter", "Venus", "Mercury", "Sun"}
CHALLENGING_DASHA = {"Rahu", "Ketu"}

_FAVORABLE_TARAS = {2, 4, 6, 8, 9}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _score_label(score: float) -> str:
    if score >= 85:
        return "Exceptional"
    if score >= 70:
        return "Strong"
    if score >= 55:
        return "Good"
    if score >= 40:
        return "Workable"
    return "Challenging"


def _planet_relation(p1: str, p2: str) -> int:
    """Return +1 (friend), 0 (neutral), -1 (enemy) from p1's perspective of p2."""
    info = PLANET_FRIENDS.get(p1, {})
    if p2 in info.get("friends", []):
        return 1
    if p2 in info.get("enemies", []):
        return -1
    return 0


def _house_sign(chart: dict, house_num: int) -> str:
    """Return the sign ruling house N in Whole Sign system."""
    asc_idx = chart["ascendant"]["sign_index"]
    return SIGNS[(asc_idx + house_num - 1) % 12]


def _sign_dignity(planet: str, sign: str) -> int:
    """Dignity score: exalted=3, own=2, friendly=1, neutral=0, enemy=-1, debilitated=-2."""
    if EXALT_SIGN.get(planet) == sign:
        return 3
    if sign in OWN_SIGNS.get(planet, []):
        return 2
    if DEBIL_SIGN.get(planet) == sign:
        return -2
    lord = SIGN_LORD.get(sign, "")
    return _planet_relation(planet, lord)


def _dasha_quality(planet: str) -> str:
    if planet in FAVORABLE_DASHA:
        return "favorable"
    if planet in CHALLENGING_DASHA:
        return "challenging"
    return "neutral"


def _accuracy_warning(acc_a: str, acc_b: str) -> str | None:
    a_issue = acc_a in ("approximate", "unknown")
    b_issue = acc_b in ("approximate", "unknown")
    if not a_issue and not b_issue:
        return None
    if a_issue and b_issue:
        if acc_a == "unknown" or acc_b == "unknown":
            return "both_unknown"
        return "both_approximate"
    if a_issue:
        return f"person_a_{acc_a}"
    return f"person_b_{acc_b}"


# ---------------------------------------------------------------------------
# Scoring dimensions
# ---------------------------------------------------------------------------

def score_working_style(chart_a: dict, chart_b: dict) -> dict:
    """Moon nakshatra Tara compatibility (25% of total)."""
    nak_a = NAKSHATRAS.index(chart_a["planets"]["Moon"]["nakshatra"])
    nak_b = NAKSHATRAS.index(chart_b["planets"]["Moon"]["nakshatra"])

    t_ab = (nak_b - nak_a) % 27 % 9 + 1
    t_ba = (nak_a - nak_b) % 27 % 9 + 1
    score_ab = 90 if t_ab in _FAVORABLE_TARAS else 30
    score_ba = 90 if t_ba in _FAVORABLE_TARAS else 30
    score = (score_ab + score_ba) / 2

    nak_a_name = chart_a["planets"]["Moon"]["nakshatra"]
    nak_b_name = chart_b["planets"]["Moon"]["nakshatra"]
    return {
        "score": round(score),
        "label": _score_label(score),
        "detail": (
            f"Moon A: {nak_a_name} | Moon B: {nak_b_name} | "
            f"Tara A→B: {t_ab} ({'favorable' if t_ab in _FAVORABLE_TARAS else 'challenging'}), "
            f"Tara B→A: {t_ba} ({'favorable' if t_ba in _FAVORABLE_TARAS else 'challenging'})"
        ),
    }


def score_drive(
    chart_a: dict,
    chart_b: dict,
    use_houses_a: bool = True,
    use_houses_b: bool = True,
) -> dict:
    """Mars + Mercury sign lord friendship (25% of total)."""
    mars_a = chart_a["planets"]["Mars"]["sign"]
    mars_b = chart_b["planets"]["Mars"]["sign"]
    merc_a = chart_a["planets"]["Mercury"]["sign"]
    merc_b = chart_b["planets"]["Mercury"]["sign"]

    lord_mars_a = SIGN_LORD[mars_a]
    lord_mars_b = SIGN_LORD[mars_b]
    lord_merc_a = SIGN_LORD[merc_a]
    lord_merc_b = SIGN_LORD[merc_b]

    mars_rel = (
        _planet_relation(lord_mars_a, lord_mars_b)
        + _planet_relation(lord_mars_b, lord_mars_a)
    ) / 2
    merc_rel = (
        _planet_relation(lord_merc_a, lord_merc_b)
        + _planet_relation(lord_merc_b, lord_merc_a)
    ) / 2
    total = mars_rel + merc_rel

    bonus = 0
    if use_houses_b and mars_a == _house_sign(chart_b, 10):
        bonus += 15
    if use_houses_a and mars_b == _house_sign(chart_a, 10):
        bonus += 15

    score_map = {2: 90, 1: 75, 0: 60, -1: 45, -2: 30}
    rounded_total = max(-2, min(2, round(total)))
    base = score_map[rounded_total]
    score = min(100, base + bonus)

    bonus_str = f" | H10 bonus: +{bonus}pts" if bonus else ""
    return {
        "score": round(score),
        "label": _score_label(score),
        "detail": f"Mars: {mars_a} ↔ {mars_b} | Mercury: {merc_a} ↔ {merc_b}{bonus_str}",
    }


def score_vision(chart_a: dict, chart_b: dict) -> dict:
    """Jupiter aspect harmony (25% of total)."""
    jup_sign_a = chart_a["planets"]["Jupiter"]["sign"]
    jup_sign_b = chart_b["planets"]["Jupiter"]["sign"]
    jup_idx_a = SIGNS.index(jup_sign_a)
    jup_idx_b = SIGNS.index(jup_sign_b)

    # Jupiter aspects 5th (offset 4), 7th (offset 6), 9th (offset 8) signs
    _OFFSETS = {4, 6, 8}

    def aspect_signs(idx: int) -> set[str]:
        return {SIGNS[(idx + o) % 12] for o in _OFFSETS}

    aspects_a = aspect_signs(jup_idx_a)
    aspects_b = aspect_signs(jup_idx_b)

    pts = 0
    for planet in ("Sun", "Moon", "Jupiter"):
        if chart_b["planets"][planet]["sign"] in aspects_a:
            pts += 1
    for planet in ("Sun", "Moon", "Jupiter"):
        if chart_a["planets"][planet]["sign"] in aspects_b:
            pts += 1

    lord_jup_a = SIGN_LORD[jup_sign_a]
    lord_jup_b = SIGN_LORD[jup_sign_b]
    jup_rel = (
        _planet_relation(lord_jup_a, lord_jup_b)
        + _planet_relation(lord_jup_b, lord_jup_a)
    ) / 2
    if jup_rel > 0:
        pts += 1
    elif jup_rel < 0:
        pts -= 1

    score_map = {4: 90, 3: 78, 2: 65, 1: 50}
    pts_clamped = max(0, min(4, pts))
    score = score_map.get(pts_clamped, 35)

    return {
        "score": score,
        "label": _score_label(score),
        "detail": (
            f"Jupiter A: {jup_sign_a} (aspects {', '.join(sorted(aspects_a))}) | "
            f"Jupiter B: {jup_sign_b} (aspects {', '.join(sorted(aspects_b))}) | "
            f"Pts: {pts}"
        ),
    }


def get_startup_timing(moon_lon: float, birth_dt: datetime) -> list[dict]:
    """Return dasha/bhukti windows for the next 5 years from today."""
    today = datetime.now(_tz.utc).replace(tzinfo=None)
    cutoff = today.replace(year=today.year + 5)

    dashas = calculate_dashas(moon_lon, birth_dt, periods=4)
    windows: list[dict] = []

    for dasha in dashas:
        bhuktis = calculate_bhuktis(dasha)
        for bhukti in bhuktis:
            if bhukti["end"] < today:
                continue
            if bhukti["start"] > cutoff:
                break
            start = max(bhukti["start"], today)
            end = min(bhukti["end"], cutoff)
            windows.append({
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "dasha": f"{dasha['planet']}/{bhukti['planet']}",
                "quality": _dasha_quality(bhukti["planet"]),
            })

    return windows


def score_timing_sync(windows_a: list[dict], windows_b: list[dict]) -> dict:
    """Score timing sync and collect overlapping favorable windows."""

    def favorable_ranges(windows: list[dict]) -> list[tuple[datetime, datetime]]:
        return [
            (
                datetime.strptime(w["start"], "%Y-%m-%d"),
                datetime.strptime(w["end"], "%Y-%m-%d"),
            )
            for w in windows if w["quality"] == "favorable"
        ]

    ranges_a = favorable_ranges(windows_a)
    ranges_b = favorable_ranges(windows_b)

    overlap_months = 0.0
    overlap_zones: list[dict] = []

    for s_a, e_a in ranges_a:
        for s_b, e_b in ranges_b:
            s = max(s_a, s_b)
            e = min(e_a, e_b)
            if s < e:
                overlap_months += (e - s).days / 30.44
                overlap_zones.append({
                    "start": s.strftime("%Y-%m-%d"),
                    "end": e.strftime("%Y-%m-%d"),
                    "label": "★ Best window",
                })

    if overlap_months >= 12:
        score = 95
    elif overlap_months >= 6:
        score = 80
    elif overlap_months >= 1:
        score = 65
    elif ranges_a and ranges_b:
        score = 50
    else:
        score = 35

    return {
        "score": score,
        "label": _score_label(score),
        "overlap_zones": overlap_zones,
        "detail": f"{overlap_months:.0f} months of overlapping favorable dasha windows",
    }


def suggest_roles(chart_a: dict, chart_b: dict) -> dict:
    """Suggest founder roles based on planetary dignities."""

    def vision_score(chart: dict) -> int:
        return (
            _sign_dignity("Jupiter", chart["planets"]["Jupiter"]["sign"])
            + _sign_dignity("Sun", chart["planets"]["Sun"]["sign"])
        )

    def execution_score(chart: dict) -> int:
        return (
            _sign_dignity("Mars", chart["planets"]["Mars"]["sign"])
            + _sign_dignity("Saturn", chart["planets"]["Saturn"]["sign"])
        )

    vis_a, vis_b = vision_score(chart_a), vision_score(chart_b)
    exe_a, exe_b = execution_score(chart_a), execution_score(chart_b)

    if abs(vis_a - vis_b) <= 2 and abs(exe_a - exe_b) <= 2:
        return {
            "person_a": "Co-leads — define roles explicitly",
            "person_b": "Co-leads — define roles explicitly",
        }

    if vis_a >= vis_b:
        return {"person_a": "Visionary / Strategy", "person_b": "Execution / Operations"}
    return {"person_a": "Execution / Operations", "person_b": "Visionary / Strategy"}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def match_cofounders(
    chart_a: dict,
    chart_b: dict,
    name_a: str,
    name_b: str,
    birth_dt_a: datetime,
    birth_dt_b: datetime,
    time_accuracy_a: str = "exact",
    time_accuracy_b: str = "exact",
) -> dict:
    """Compute full cofounder compatibility. Returns API response dict."""
    use_houses_a = time_accuracy_a != "unknown"
    use_houses_b = time_accuracy_b != "unknown"

    moon_lon_a = chart_a["planets"]["Moon"]["longitude"]
    moon_lon_b = chart_b["planets"]["Moon"]["longitude"]

    ws = score_working_style(chart_a, chart_b)
    dr = score_drive(chart_a, chart_b, use_houses_a, use_houses_b)
    vi = score_vision(chart_a, chart_b)

    timing_a = get_startup_timing(moon_lon_a, birth_dt_a)
    timing_b = get_startup_timing(moon_lon_b, birth_dt_b)
    ts = score_timing_sync(timing_a, timing_b)

    overall = round((ws["score"] + dr["score"] + vi["score"] + ts["score"]) / 4)

    return {
        "overall_score": overall,
        "score_label": _score_label(overall),
        "accuracy_warning": _accuracy_warning(time_accuracy_a, time_accuracy_b),
        "dimensions": {
            "working_style": ws,
            "drive": dr,
            "vision": vi,
            "timing_sync": {
                "score": ts["score"],
                "label": ts["label"],
                "detail": ts["detail"],
            },
        },
        "role_suggestion": suggest_roles(chart_a, chart_b),
        "startup_timing": {
            "person_a": timing_a,
            "person_b": timing_b,
            "overlap_zones": ts["overlap_zones"],
        },
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/python3 -m pytest api/tests/test_match.py -v
```

Expected: All tests pass (PASSED ×N).

- [ ] **Step 5: Commit**

```bash
git add astro_engine/match.py api/tests/test_match.py
git commit -m "feat: add Vedic cofounder scoring engine (match.py)"
```

---

### Task 2: FastAPI Router + Register

**Files:**
- Create: `api/routers/match.py`
- Create: `api/tests/test_match_router.py`
- Modify: `api/main.py` (add two lines)

**Interfaces:**
- Consumes: `astro_engine.geo.geocode`, `astro_engine.calc.calculate_chart`, `astro_engine.match.match_cofounders`
- Produces: `POST /api/cofounder-match` → JSON (structure from Task 1 `match_cofounders`)

- [ ] **Step 1: Write the failing router test**

Create `api/tests/test_match_router.py`:

```python
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
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/python3 -m pytest api/tests/test_match_router.py -v 2>&1 | head -20
```

Expected: `404 Not Found` (route not registered yet).

- [ ] **Step 3: Create `api/routers/match.py`**

```python
"""Cofounder matching router — POST /api/cofounder-match."""
import asyncio
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from astro_engine.geo import geocode
from astro_engine.calc import calculate_chart
from astro_engine.match import match_cofounders

router = APIRouter(tags=["match"])


class PersonInput(BaseModel):
    name: str
    date: str                    # YYYY-MM-DD or DD-MM-YYYY
    time: str = "12:00"          # HH:MM; ignored when time_accuracy=="unknown"
    time_accuracy: Literal["exact", "approximate", "unknown"] = "exact"
    place: str


class MatchRequest(BaseModel):
    person_a: PersonInput
    person_b: PersonInput


@router.post("/cofounder-match")
async def cofounder_match(req: MatchRequest):
    time_a = "12:00" if req.person_a.time_accuracy == "unknown" else req.person_a.time
    time_b = "12:00" if req.person_b.time_accuracy == "unknown" else req.person_b.time

    try:
        geo_a, geo_b = await asyncio.gather(
            asyncio.to_thread(geocode, req.person_a.place),
            asyncio.to_thread(geocode, req.person_b.place),
        )
        chart_a, chart_b = await asyncio.gather(
            asyncio.to_thread(
                calculate_chart,
                req.person_a.date, time_a,
                geo_a["lat"], geo_a["lon"], geo_a["timezone"],
            ),
            asyncio.to_thread(
                calculate_chart,
                req.person_b.date, time_b,
                geo_b["lat"], geo_b["lon"], geo_b["timezone"],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    birth_dt_a = datetime.fromisoformat(chart_a["birth_utc"])
    birth_dt_b = datetime.fromisoformat(chart_b["birth_utc"])

    return await asyncio.to_thread(
        match_cofounders,
        chart_a, chart_b,
        req.person_a.name, req.person_b.name,
        birth_dt_a, birth_dt_b,
        req.person_a.time_accuracy, req.person_b.time_accuracy,
    )
```

- [ ] **Step 4: Register router in `api/main.py`**

Add to `api/main.py` (two lines — one import, one include):

Find this block:
```python
from api.routers import charts, reports, chat, questions, payments, demo, admin, named
```

Replace with:
```python
from api.routers import charts, reports, chat, questions, payments, demo, admin, named, match
```

Find:
```python
app.include_router(admin.router, prefix="/api")
app.include_router(named.router)
```

Replace with:
```python
app.include_router(admin.router, prefix="/api")
app.include_router(match.router, prefix="/api")
app.include_router(named.router)
```

- [ ] **Step 5: Run router tests to confirm they pass**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/python3 -m pytest api/tests/test_match_router.py -v
```

Expected: All 4 tests PASSED.

- [ ] **Step 6: Run full test suite to confirm no regressions**

```bash
.venv/bin/python3 -m pytest api/tests/ -v 2>&1 | tail -20
```

Expected: All pre-existing tests still pass.

- [ ] **Step 7: Commit**

```bash
git add api/routers/match.py api/tests/test_match_router.py api/main.py
git commit -m "feat: add POST /api/cofounder-match endpoint"
```

---

### Task 3: Frontend (`docs/cofounder/index.html`)

**Files:**
- Create: `docs/cofounder/index.html`

**Interfaces:**
- Consumes: `POST /api/cofounder-match` (from Task 2)
- Produces: Self-contained HTML page browsable at `http://192.168.1.102:8765/docs/cofounder/index.html`

**Before starting:** Find your Railway API URL by running:
```bash
cat /home/jo/claude_projects/P046_202604_KnowThyselfAstro/.env | grep -i railway
# or check Railway dashboard — looks like https://something.up.railway.app
```
Replace `YOUR_RAILWAY_URL` in the JS constant below with the actual URL.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p /home/jo/claude_projects/P046_202604_KnowThyselfAstro/docs/cofounder
```

- [ ] **Step 2: Create `docs/cofounder/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="robots" content="noindex, nofollow">
<title>Cofounder Compatibility — Astrowise</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:      #0b0b18;
  --surface: rgba(255,255,255,0.035);
  --border:  rgba(196,158,64,0.18);
  --gold:    #c49e40;
  --gold2:   #e8c96a;
  --cream:   #f0e8d8;
  --muted:   rgba(240,232,216,0.55);
  --plum:    #7c5cbf;
  --rose:    #c4607a;
  --sage:    #5a8f72;
  --blue:    #5b8fd4;
  --shadow:  0 20px 60px rgba(0,0,0,0.45);
  --r:       22px;
}
*{box-sizing:border-box;margin:0;padding:0}
body {
  background-color: var(--bg);
  background-image:
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(124,92,191,0.18), transparent),
    radial-gradient(ellipse 60% 40% at 80% 110%, rgba(196,158,64,0.12), transparent);
  background-attachment: fixed;
  font-family: 'DM Sans', system-ui, sans-serif;
  color: var(--cream);
  min-height: 100vh;
}
.page { max-width: 820px; margin: 0 auto; padding: 48px 24px 80px; }

/* ── Form ── */
.hero-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(2.2rem, 5vw, 3.8rem);
  font-weight: 300;
  color: #fff8f0;
  text-align: center;
  margin-bottom: 10px;
}
.hero-sub {
  font-size: 0.88rem;
  color: var(--muted);
  text-align: center;
  letter-spacing: 0.06em;
  margin-bottom: 36px;
}
.persons-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-bottom: 24px;
}
.person-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 24px 20px;
}
.person-label {
  font-size: 0.65rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 16px;
  display: block;
}
.field { margin-bottom: 14px; }
.field label {
  display: block;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}
.field input {
  width: 100%;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(196,158,64,0.22);
  border-radius: 10px;
  padding: 9px 12px;
  color: var(--cream);
  font-size: 0.9rem;
  font-family: 'DM Sans', sans-serif;
  outline: none;
  transition: border-color 0.2s;
}
.field input:focus { border-color: rgba(196,158,64,0.55); }
.check-row { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: var(--muted); margin-top: 6px; cursor: pointer; }
.check-row input[type=checkbox] { accent-color: var(--gold); width: 14px; height: 14px; cursor: pointer; }
.cta-btn {
  display: block;
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
  padding: 14px 0;
  background: linear-gradient(135deg, rgba(196,158,64,0.22), rgba(196,158,64,0.12));
  border: 1px solid rgba(196,158,64,0.4);
  border-radius: 14px;
  color: var(--gold2);
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
  transition: background 0.2s, transform 0.1s;
}
.cta-btn:hover { background: linear-gradient(135deg, rgba(196,158,64,0.32), rgba(196,158,64,0.18)); }
.cta-btn:active { transform: scale(0.98); }
.cta-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Loading ── */
#loading { display: none; text-align: center; padding: 60px 0; }
.star-pulse { font-size: 2.5rem; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:0.3;transform:scale(0.9)} 50%{opacity:1;transform:scale(1.1)} }
#loading p { margin-top: 16px; color: var(--muted); font-size: 0.9rem; letter-spacing: 0.1em; }

/* ── Results ── */
#results { display: none; }

/* Score hero */
.score-hero {
  background: linear-gradient(140deg, rgba(28,18,56,0.98) 0%, rgba(44,24,72,0.96) 45%, rgba(80,38,58,0.92) 100%);
  border: 1px solid rgba(196,158,64,0.22);
  border-radius: 28px;
  padding: 40px 36px 32px;
  box-shadow: var(--shadow);
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.score-names {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.5rem, 4vw, 2.4rem);
  font-weight: 300;
  color: #fff8f0;
  text-align: center;
  margin-bottom: 28px;
}
.score-dial-wrap { display: flex; flex-direction: column; align-items: center; margin-bottom: 28px; }
.score-dial { width: 140px; height: 140px; position: relative; }
.score-dial svg { transform: rotate(-90deg); }
.dial-bg { fill: none; stroke: rgba(255,255,255,0.06); stroke-width: 10; }
.dial-fill { fill: none; stroke: var(--gold); stroke-width: 10; stroke-linecap: round;
  stroke-dasharray: 339.29; stroke-dashoffset: 339.29; transition: stroke-dashoffset 1.2s ease; }
.dial-number {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  font-family: 'Cormorant Garamond', serif; font-size: 2.6rem; font-weight: 300; color: var(--gold2);
}
.dial-label {
  font-size: 0.72rem; letter-spacing: 0.2em; text-transform: uppercase; color: var(--gold);
  margin-top: 8px;
}
.dim-bars { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; margin-bottom: 20px; }
.dim-bar { }
.dim-bar-name { font-size: 0.68rem; letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
.dim-bar-track { height: 5px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 999px; transition: width 1s ease; }
.dim-bar-score { font-size: 0.78rem; color: var(--cream); margin-top: 3px; }
.accuracy-badge {
  display: inline-block; padding: 5px 14px; border-radius: 999px; font-size: 0.72rem;
  font-weight: 500; letter-spacing: 0.06em; margin-top: 8px; text-align: center;
}
.badge-amber { background: rgba(196,158,64,0.15); color: #e8c96a; border: 1px solid rgba(196,158,64,0.3); }
.badge-rose  { background: rgba(196,96,122,0.15); color: #e8909f; border: 1px solid rgba(196,96,122,0.3); }

/* Panels */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 0;
  box-shadow: var(--shadow);
  margin-bottom: 16px;
  overflow: hidden;
}
.panel-header {
  display: flex; align-items: center; gap: 12px; padding: 18px 24px;
  cursor: pointer; user-select: none;
}
.panel-header:hover { background: rgba(255,255,255,0.02); }
.panel-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content:center; font-size: 1rem; flex-shrink: 0; }
.icon-plum { background: rgba(124,92,191,0.14); color: #b49edf; }
.icon-gold  { background: rgba(196,158,64,0.1);  color: var(--gold); }
.icon-sage  { background: rgba(90,143,114,0.12); color: #80c4a0; }
.icon-blue  { background: rgba(91,143,212,0.12); color: #8ab4e8; }
.panel-title { font-family: 'Cormorant Garamond', serif; font-size: 1.3rem; font-weight: 400; color: var(--cream); flex: 1; }
.panel-score-badge {
  font-size: 0.78rem; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  background: rgba(196,158,64,0.1); color: var(--gold2); border: 1px solid rgba(196,158,64,0.2);
}
.panel-chevron { color: var(--muted); transition: transform 0.25s; font-size: 0.8rem; }
.panel.open .panel-chevron { transform: rotate(180deg); }
.panel-body { display: none; padding: 0 24px 20px; border-top: 1px solid rgba(196,158,64,0.08); }
.panel.open .panel-body { display: block; }
.panel-detail { font-size: 0.85rem; color: var(--muted); line-height: 1.7; padding-top: 16px; }
.panel-detail strong { color: var(--cream); font-weight: 500; }

/* Timeline */
.timeline-section { margin-bottom: 28px; }
.tl-heading {
  font-family: 'Cormorant Garamond', serif; font-size: 1.5rem; font-weight: 300;
  color: var(--cream); margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border);
}
.tl-row { margin-bottom: 16px; }
.tl-name { font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); margin-bottom: 6px; }
.tl-track { height: 28px; border-radius: 8px; overflow: hidden; display: flex; position: relative; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); }
.tl-seg { height: 100%; display: flex; align-items: center; justify-content: center; font-size: 0.62rem; letter-spacing: 0.05em; overflow: hidden; white-space: nowrap; transition: opacity 0.2s; }
.tl-seg:hover { opacity: 0.8; }
.tl-seg.favorable { background: rgba(90,143,114,0.4); color: #a0d4b8; border-right: 1px solid rgba(90,143,114,0.2); }
.tl-seg.neutral   { background: rgba(196,158,64,0.15); color: rgba(196,158,64,0.7); border-right: 1px solid rgba(196,158,64,0.1); }
.tl-seg.challenging { background: rgba(196,96,122,0.25); color: rgba(196,96,122,0.8); border-right: 1px solid rgba(196,96,122,0.15); }
.tl-legend { display: flex; gap: 16px; margin-top: 8px; font-size: 0.7rem; color: var(--muted); }
.tl-legend span { display: flex; align-items: center; gap: 5px; }
.tl-legend-dot { width: 8px; height: 8px; border-radius: 2px; }
.overlap-callout {
  background: rgba(196,158,64,0.09); border: 1px solid rgba(196,158,64,0.28);
  border-radius: 14px; padding: 14px 18px; margin-top: 14px; font-size: 0.88rem; line-height: 1.7;
}
.overlap-callout strong { color: var(--gold2); }

/* Roles */
.roles-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 28px; }
.role-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 18px;
  padding: 22px 20px; text-align: center;
}
.role-name { font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; font-weight: 300; color: var(--cream); margin-bottom: 10px; }
.role-badge {
  display: inline-block; padding: 5px 14px; border-radius: 999px; font-size: 0.75rem;
  font-weight: 600; letter-spacing: 0.08em;
  background: rgba(196,158,64,0.1); color: var(--gold2); border: 1px solid rgba(196,158,64,0.25);
}
.footer { text-align: center; padding: 20px 0; font-size: 0.72rem; color: rgba(240,232,216,0.3); letter-spacing: 0.08em; border-top: 1px solid var(--border); margin-top: 40px; }
@media (max-width: 640px) {
  .persons-grid, .dim-bars, .roles-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<div class="page">

  <!-- ── Form ── -->
  <section id="form-section">
    <h1 class="hero-title">Find Your Founding Partner</h1>
    <p class="hero-sub">Vedic astrological compatibility for cofounders &amp; startup timing</p>

    <div class="persons-grid">
      <!-- Person A -->
      <div class="person-card">
        <span class="person-label">Person A</span>
        <div class="field"><label>Name</label><input id="a-name" type="text" placeholder="Alice"></div>
        <div class="field"><label>Date of Birth</label><input id="a-date" type="text" placeholder="YYYY-MM-DD"></div>
        <div class="field">
          <label>Birth Time</label>
          <input id="a-time" type="text" placeholder="HH:MM">
          <label class="check-row"><input type="checkbox" id="a-approx"> Approximate (±2h)</label>
          <label class="check-row"><input type="checkbox" id="a-unknown"> I don't know the birth time</label>
        </div>
        <div class="field"><label>Birth Place</label><input id="a-place" type="text" placeholder="Mumbai, India"></div>
      </div>
      <!-- Person B -->
      <div class="person-card">
        <span class="person-label">Person B</span>
        <div class="field"><label>Name</label><input id="b-name" type="text" placeholder="Bob"></div>
        <div class="field"><label>Date of Birth</label><input id="b-date" type="text" placeholder="YYYY-MM-DD"></div>
        <div class="field">
          <label>Birth Time</label>
          <input id="b-time" type="text" placeholder="HH:MM">
          <label class="check-row"><input type="checkbox" id="b-approx"> Approximate (±2h)</label>
          <label class="check-row"><input type="checkbox" id="b-unknown"> I don't know the birth time</label>
        </div>
        <div class="field"><label>Birth Place</label><input id="b-place" type="text" placeholder="Bangalore, India"></div>
      </div>
    </div>

    <button class="cta-btn" id="submit-btn" onclick="submitMatch()">★ Calculate Compatibility</button>
  </section>

  <!-- ── Loading ── -->
  <div id="loading">
    <div class="star-pulse">✦</div>
    <p>Reading the stars…</p>
  </div>

  <!-- ── Results ── -->
  <div id="results"></div>

</div>

<script>
// ─── Config ───────────────────────────────────────────────────────────────
const API_BASE = (() => {
  const h = window.location.hostname;
  if (h === 'localhost' || h.startsWith('192.168') || h.startsWith('100.')) {
    return 'http://localhost:8000';
  }
  return 'https://YOUR_RAILWAY_URL.up.railway.app'; // TODO: replace with actual URL
})();

// ─── Toggle unknown time ───────────────────────────────────────────────────
['a','b'].forEach(p => {
  document.getElementById(`${p}-unknown`).addEventListener('change', e => {
    document.getElementById(`${p}-time`).disabled = e.target.checked;
    document.getElementById(`${p}-approx`).disabled = e.target.checked;
    if (e.target.checked) document.getElementById(`${p}-approx`).checked = false;
  });
});

// ─── Submit ────────────────────────────────────────────────────────────────
async function submitMatch() {
  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  document.getElementById('form-section').style.display = 'none';
  document.getElementById('loading').style.display = 'block';
  document.getElementById('results').style.display = 'none';
  document.getElementById('results').innerHTML = '';

  const get = id => document.getElementById(id).value.trim();
  const checked = id => document.getElementById(id).checked;

  const person = (p) => ({
    name: get(`${p}-name`),
    date: get(`${p}-date`),
    time: checked(`${p}-unknown`) ? '12:00' : (get(`${p}-time`) || '12:00'),
    time_accuracy: checked(`${p}-unknown`) ? 'unknown' : (checked(`${p}-approx`) ? 'approximate' : 'exact'),
    place: get(`${p}-place`),
  });

  try {
    const resp = await fetch(`${API_BASE}/api/cofounder-match`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ person_a: person('a'), person_b: person('b') }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';
    renderResults(data, person('a').name, person('b').name);
  } catch (err) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('form-section').style.display = 'block';
    btn.disabled = false;
    alert('Error: ' + err.message);
  }
}

// ─── Render ────────────────────────────────────────────────────────────────
function scoreColor(s) {
  if (s >= 85) return '#e8c96a';
  if (s >= 70) return '#80c4a0';
  if (s >= 55) return '#8ab4e8';
  if (s >= 40) return '#c49e40';
  return '#e8909f';
}

function renderResults(d, nameA, nameB) {
  const el = document.getElementById('results');
  el.innerHTML = buildHTML(d, nameA, nameB);
  // Animate score dial
  requestAnimationFrame(() => {
    const fill = document.querySelector('.dial-fill');
    if (fill) {
      const circumference = 339.29;
      fill.style.strokeDashoffset = circumference - (circumference * d.overall_score / 100);
    }
    // Animate dimension bars
    document.querySelectorAll('.dim-bar-fill[data-w]').forEach(bar => {
      bar.style.width = bar.dataset.w + '%';
    });
  });
  // Expandable panels
  document.querySelectorAll('.panel-header').forEach(h => {
    h.addEventListener('click', () => h.closest('.panel').classList.toggle('open'));
  });
}

function buildHTML(d, nameA, nameB) {
  const dims = d.dimensions;
  const dimList = [
    { key:'working_style', label:'Working Style',   icon:'🌙', iconClass:'icon-plum' },
    { key:'drive',         label:'Drive & Execution',icon:'⚡', iconClass:'icon-gold' },
    { key:'vision',        label:'Vision & Growth', icon:'🌿', iconClass:'icon-sage' },
    { key:'timing_sync',   label:'Timing Sync',     icon:'📅', iconClass:'icon-blue' },
  ];
  const dimBarColor = { working_style:'#b49edf', drive:scoreColor(dims.drive?.score), vision:'#80c4a0', timing_sync:'#8ab4e8' };

  // Accuracy badge
  let accBadge = '';
  if (d.accuracy_warning) {
    const unknown = d.accuracy_warning.includes('unknown');
    const msg = unknown
      ? '~70% accuracy — Lagna not used (birth time unknown)'
      : '~85% accuracy — birth time approximate (±2h)';
    accBadge = `<div style="text-align:center;margin-top:10px"><span class="accuracy-badge ${unknown?'badge-rose':'badge-amber'}">${msg}</span></div>`;
  }

  // Dimension bars HTML
  const dimBarsHTML = dimList.map(di => {
    const s = dims[di.key]?.score ?? 0;
    return `<div class="dim-bar">
      <div class="dim-bar-name">${di.label}</div>
      <div class="dim-bar-track"><div class="dim-bar-fill" data-w="${s}" style="width:0%;background:${dimBarColor[di.key]}"></div></div>
      <div class="dim-bar-score">${s} — ${dims[di.key]?.label ?? ''}</div>
    </div>`;
  }).join('');

  // Expandable panels
  const panelsHTML = dimList.map(di => {
    const s = dims[di.key]?.score ?? 0;
    const detail = dims[di.key]?.detail ?? '';
    return `<div class="panel">
      <div class="panel-header">
        <div class="panel-icon ${di.iconClass}">${di.icon}</div>
        <div class="panel-title">${di.label}</div>
        <div class="panel-score-badge">${s}</div>
        <div class="panel-chevron">▼</div>
      </div>
      <div class="panel-body">
        <div class="panel-detail"><strong>Analysis:</strong> ${detail}</div>
      </div>
    </div>`;
  }).join('');

  // Timeline
  const timing = d.startup_timing;
  const tl = buildTimeline(timing.person_a, timing.person_b, timing.overlap_zones, nameA, nameB);

  // Roles
  const roles = d.role_suggestion;
  const rolesHTML = `
    <div class="roles-grid">
      <div class="role-card">
        <div class="role-name">${nameA}</div>
        <div class="role-badge">${roles.person_a}</div>
      </div>
      <div class="role-card">
        <div class="role-name">${nameB}</div>
        <div class="role-badge">${roles.person_b}</div>
      </div>
    </div>`;

  return `
    <div class="score-hero">
      <div class="score-names">${nameA} ✦ ${nameB}</div>
      <div class="score-dial-wrap">
        <div class="score-dial">
          <svg viewBox="0 0 120 120" width="140" height="140">
            <circle class="dial-bg" cx="60" cy="60" r="54"/>
            <circle class="dial-fill" cx="60" cy="60" r="54"/>
          </svg>
          <div class="dial-number">${d.overall_score}</div>
        </div>
        <div class="dial-label">${d.score_label} Founding Match</div>
      </div>
      <div class="dim-bars">${dimBarsHTML}</div>
      ${accBadge}
    </div>

    ${panelsHTML}

    <div class="timeline-section">
      <div class="tl-heading">Startup Launch Windows</div>
      ${tl}
    </div>

    ${rolesHTML}

    <div class="footer">Generated ${new Date().toLocaleDateString('en-GB',{year:'numeric',month:'long',day:'numeric'})} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris</div>
  `;
}

function buildTimeline(windowsA, windowsB, overlaps, nameA, nameB) {
  if (!windowsA.length && !windowsB.length) return '<p style="color:var(--muted);font-size:0.88rem">No timing data available.</p>';

  const allDates = [...windowsA, ...windowsB].flatMap(w => [new Date(w.start), new Date(w.end)]);
  const minDate = new Date(Math.min(...allDates));
  const maxDate = new Date(Math.max(...allDates));
  const totalMs = maxDate - minDate || 1;

  function trackHTML(windows) {
    return windows.map(w => {
      const s = new Date(w.start), e = new Date(w.end);
      const left = ((s - minDate) / totalMs * 100).toFixed(1);
      const width = ((e - s) / totalMs * 100).toFixed(1);
      const label = w.dasha.length < 18 ? w.dasha : w.dasha.slice(0,16)+'…';
      return `<div class="tl-seg ${w.quality}" style="width:${width}%;margin-left:${left}%;position:absolute;left:0" title="${w.dasha}: ${w.start} → ${w.end}">${label}</div>`;
    }).join('');
  }

  let overlapHTML = '';
  if (overlaps.length) {
    const zones = overlaps.map(z => `<strong>${z.start.slice(0,7)} → ${z.end.slice(0,7)}</strong>`).join(', ');
    overlapHTML = `<div class="overlap-callout">★ Best launch windows (both favorable): ${zones}</div>`;
  }

  return `
    <div class="tl-row">
      <div class="tl-name">${nameA}</div>
      <div class="tl-track" style="position:relative">${trackHTML(windowsA)}</div>
    </div>
    <div class="tl-row">
      <div class="tl-name">${nameB}</div>
      <div class="tl-track" style="position:relative">${trackHTML(windowsB)}</div>
    </div>
    <div class="tl-legend">
      <span><span class="tl-legend-dot" style="background:rgba(90,143,114,0.5)"></span>Favorable</span>
      <span><span class="tl-legend-dot" style="background:rgba(196,158,64,0.3)"></span>Neutral</span>
      <span><span class="tl-legend-dot" style="background:rgba(196,96,122,0.4)"></span>Challenging</span>
    </div>
    ${overlapHTML}`;
}
</script>
</body>
</html>
```

- [ ] **Step 3: Set the Railway API URL**

Open `docs/cofounder/index.html`, find:
```javascript
return 'https://YOUR_RAILWAY_URL.up.railway.app';
```
Replace `YOUR_RAILWAY_URL` with the actual Railway hostname. To find it:
```bash
# Check Railway dashboard, or look for it in existing env files:
grep -r "railway\|RAILWAY" /home/jo/claude_projects/P046_202604_KnowThyselfAstro/.env 2>/dev/null
```

- [ ] **Step 4: Test locally in browser**

Open in browser: `http://192.168.1.102:8765/docs/cofounder/index.html`

Test the golden path:
- Person A: Name=Alice, Date=1985-03-07, Time=07:15, Place=Kangazha, Kerala
- Person B: Name=Bob, Date=1988-11-22, Time=09:00, Place=Mumbai, India
- Click "Calculate Compatibility"
- Confirm: score dial animates, 4 dimension bars fill, timeline shows, roles display

Test edge cases:
- Check "I don't know the birth time" for Person A → amber/rose accuracy badge appears
- Check "Approximate" for Person B → amber badge appears
- Both unknown → "both_unknown" badge appears

Make sure the local API is running:
```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/python3 -m uvicorn api.main:app --reload --port 8000 &
```

- [ ] **Step 5: Commit and push to GitHub Pages**

```bash
git add docs/cofounder/index.html
git commit -m "feat: add cofounder matching frontend page"
git push
```

Live URL: `https://45degrees45.github.io/know-thyself-astro/cofounder/`

---

## Execution Order

1. Task 1 — scoring engine + tests (no server needed, pure Python)
2. Task 2 — router + register + integration test
3. Task 3 — frontend HTML (requires local API running)
