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
from datetime import datetime, timedelta, timezone as _tz

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
    cutoff = today + timedelta(days=1827)

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
