#!/usr/bin/env python3
"""
Generate all-profiles skill + startup-fitness dashboard HTML.
Computes 5 skill scores + startup fitness tier per person from chart dignities.
"""

import sys
from datetime import datetime, date
sys.path.insert(0, "/home/jo/claude_projects/P046_202604_KnowThyselfAstro")

from astro_engine.calc import calculate_chart, SIGNS
from astro_engine.yoga import SIGN_LORD, EXALT_SIGN, DEBIL_SIGN, OWN_SIGNS
from astro_engine.match import _sign_dignity, _planet_relation

# ---------------------------------------------------------------------------
# All profiles — (name, dob, time, lat, lon, tz, lagna_label, dasha, animal, gender)
# ---------------------------------------------------------------------------
PROFILES = [
    ("Joseph TC",    "1984-08-05", "15:30", 10.10, 76.36, "Asia/Kolkata",   "Sagittarius", "Venus/Venus/Mercury",    "🦅", "M"),
    ("Goldy",        "1985-03-07", "07:15",  9.60, 76.45, "Asia/Kolkata",   "Pisces",      "Rahu/Venus/Venus",       "🐬", "M"),
    ("Prakashji",    "1973-11-04", "01:22", 10.77, 76.65, "Asia/Kolkata",   "Leo",         "Saturn/Moon/Mercury",    "🦁", "M"),
    ("Gewin",        "1984-12-11", "11:55", 23.61, 58.59, "Asia/Muscat",    "Aquarius",    "Ketu/Moon/Saturn",       "🦅", "M"),
    ("Mirjam",       "1975-05-27", "23:00", 52.63,  4.75, "Europe/Amsterdam","Sagittarius","Rahu/Ketu/Rahu",         "🦢", "F"),
    ("Ruhi CH",      "2002-03-03", "02:00",  9.49, 76.33, "Asia/Kolkata",   "Sagittarius", "Jupiter/Mercury/Saturn", "🦌", "F"),
    ("Athens CH",    "2000-06-07", "20:08",  9.55, 76.78, "Asia/Kolkata",   "Sagittarius", "Sun/Mars/Jupiter",       "🦅", "M"),
    ("Zerin",        "2000-11-09", "09:25", 10.87, 76.33, "Asia/Kolkata",   "Sagittarius", "Venus/Sun/Mercury",      "🦌", "F"),
    ("Spirilla Guy", "1996-12-12", "10:15", 13.08, 80.27, "Asia/Kolkata",   "Capricorn",   "Moon/Venus/Jupiter",     "🐬", "M"),
    ("Gracious George","1985-07-24","07:30", 9.75, 77.08, "Asia/Kolkata",   "Cancer",      "Saturn/Saturn/Ketu",     "🐘", "M"),
    ("Yaqza",        "2003-09-19", "12:00", 11.25, 75.77, "Asia/Kolkata",   "Scorpio",     "Jupiter/Mercury/Sun",    "🦅", "M"),
    ("Isolda",       "1985-07-24", "14:04",  9.93, 76.26, "Asia/Kolkata",   "Scorpio",     "Saturn/Mercury/Mercury", "🦚", "F"),
    ("Jinx",         "2001-07-01", "23:30",  8.52, 76.94, "Asia/Kolkata",   "Pisces",      "Mercury/Ketu/Mercury",   "🐅", "F"),
    ("Sai",          "1991-02-24", "04:40",  8.52, 76.94, "Asia/Kolkata",   "Capricorn",   "Saturn/Saturn/Rahu",     "🦅", "M"),
    ("Vi CH",        "1998-08-23", "11:55",  8.52, 76.94, "Asia/Kolkata",   "Scorpio",     "Mars/Rahu/Venus",        "🦅", "F"),
    ("Pi CH",        "1989-10-01", "20:43", 10.52, 76.21, "Asia/Kolkata",   "Aries",       "Saturn/Saturn/Ketu",     "🐅", "F"),
    ("Lalu",         "1958-05-18", "19:30", 10.10, 76.36, "Asia/Kolkata",   "Scorpio",     "Saturn/Mars/Ketu",       "🐍", "F"),
    ("Reddit Girl",  "2002-11-16", "11:25", 26.91, 75.79, "Asia/Kolkata",   "Capricorn",   "Venus/Venus/Rahu",       "🦢", "F"),
    ("Tintu",        "1990-12-26", "09:30", 10.10, 76.36, "Asia/Kolkata",   "Capricorn",   "Venus/Ketu/Mercury",     "🐘", "M"),
    ("Cini",         "1985-10-29", "11:30", 23.61, 58.59, "Asia/Muscat",    "Sagittarius", "Rahu/Saturn/Saturn",     "🐘", "F"),
    ("Khayel CH",    "2001-01-01", "00:02", 25.20, 55.27, "Asia/Dubai",     "Virgo",       "Saturn/Mars/Jupiter",    "🦁", "F"),
    ("Soniya",       "1984-06-13", "16:15", 10.77, 76.65, "Asia/Kolkata",   "Libra",       "Moon/Saturn/Venus",      "🦚", "F"),
    ("Vasudevan",    "1999-06-23", "10:30", 10.02, 76.31, "Asia/Kolkata",   "Leo",         "Jupiter/Venus/Venus",    "🦁", "M"),
    ("Remya",        "1987-06-18", "06:30", 10.10, 76.36, "Asia/Kolkata",   "Gemini",      "Mercury/Jupiter/Mercury","🐬", "F"),
    ("Ammu CH",      "1990-09-05", "05:30",  8.52, 76.94, "Asia/Kolkata",   "Leo",         "Saturn/Jupiter/Jupiter", "🦁", "F"),
    ("Biju Jacob",   "1983-11-10", "05:30", 23.61, 58.59, "Asia/Muscat",    "Libra",       "Rahu/Moon/Sun",          "🦋", "M"),
    ("Kiran",        "1983-11-02", "12:58", 10.77, 76.00, "Asia/Kolkata",   "Capricorn",   "Jupiter/Venus/Sun",      "🦁", "M"),
    ("Ann CH",       "1994-08-09", "13:30",  9.94, 76.35, "Asia/Kolkata",   "Scorpio",     "Mars/Saturn/Ketu",       "🦋", "F"),
    ("Always CH",    "1991-09-21", "08:45", 28.70, 77.10, "Asia/Kolkata",   "Libra",       "Jupiter/Mercury/Sun",    "🦋", "M"),
    ("Bodhi CH",     "1991-09-05", "21:50",  9.73, 76.33, "Asia/Kolkata",   "Taurus",      "Jupiter/Mercury/Jupiter","🐘", "M"),
    ("Kunal",        "1993-09-10", "18:50", 27.56, 76.61, "Asia/Kolkata",   "Pisces",      "Saturn/Saturn/Rahu",     "🐅", "M"),
    ("Hari CH",      "1968-09-16", "07:15",  8.52, 76.94, "Asia/Kolkata",   "Virgo",       "Mercury/Jupiter/Sun",    "🦊", "M"),
]

# Known yogas and risk flags from deep readings (from memory/natal files)
# Format: {name: {"yogas": [...], "risks": [...], "strength": "note"}}
KNOWN_CONTEXT = {
    "Joseph TC":     {"yogas": ["Hamsa", "Chandra-Mangala", "Viparita Raja", "Exalted Saturn H11"], "risks": ["Mars H12 (private drive, not public)", "Moon H12 (introvert)"]},
    "Goldy":         {"yogas": ["Rahu in H2 (wealth disruption)"], "risks": ["Rahu/Venus dasha (obsessive phase)", "Scattered energy"]},
    "Prakashji":     {"yogas": ["Leo Lagna (natural authority)"], "risks": ["Saturn/Moon/Mercury (slow, karmic phase)", "Age — 52"]},
    "Gewin":         {"yogas": ["Saturn exalted H9", "Strong Aquarius Lagna"], "risks": ["Ketu mahadasha (withdrawal, detachment)", "Abstract thinker, execution gaps"]},
    "Mirjam":        {"yogas": ["Jupiter in own sign", "Hamsa Yoga"], "risks": ["Rahu/Ketu bhukti (chaos within Rahu period)", "Far from home base"]},
    "Ruhi CH":       {"yogas": ["Mars exalted H5 (strong initiative)"], "risks": ["Kemadruma Yoga (emotional instability)", "Vosi Yoga (isolation tendency)", "Too young (24)"]},
    "Athens CH":     {"yogas": ["4-planet H6 stellium (service power)", "Bhadra Yoga", "2 Raja Yogas"], "risks": ["Kemadruma Yoga", "H6 overload — better as operator than founder"]},
    "Zerin":         {"yogas": ["Jupiter in H1 (dharmic orientation)"], "risks": ["Kemadruma Yoga", "Vosi Yoga", "NBRY — needs Neecha Bhanga to fire", "Very young (25)"]},
    "Spirilla Guy":  {"yogas": ["Malavya Yoga (Venus exalted)", "Yoga Karaka Venus", "8 yogas"], "risks": ["Moon/Venus dasha (comfort-seeking phase)", "H12 stellium (solitary worker)"]},
    "Gracious George":{"yogas": ["Sasa Yoga", "Yoga Karaka Mars exalted", "Sun+Mars H1"], "risks": ["Saturn/Saturn/Ketu (Ketu antara = confusion)", "Cancer Lagna = very home/security oriented"]},
    "Yaqza":         {"yogas": ["2 Raja Yogas H10", "Jupiter+Mercury H10 stellium"], "risks": ["Venus debilitated H11 (weak monetization)", "Only 22 — needs team"]},
    "Isolda":        {"yogas": ["Malavya Yoga (Venus exalted H7)", "NBRY", "Vesi Yoga"], "risks": ["Saturn/Mercury long dasha (technical, not entrepreneurial)", "Scorpio Lagna = deep but slow to act"]},
    "Jinx":          {"yogas": ["Adhi Yoga", "NBRY"], "risks": ["Guru-Chandala Yoga (rebel energy, hard to sustain)", "Ketu bhukti (withdrawal)", "Mercury/Ketu is unstable dasha combo"]},
    "Sai":           {"yogas": ["Sasa Yoga", "Hamsa Yoga (Jupiter exalted)", "Budha-Aditya", "Yoga Karaka Venus"], "risks": ["Saturn/Saturn — slow but builds for 20 years", "Rahu antara (volatility)"]},
    "Vi CH":         {"yogas": ["Raja Yoga", "Dharma Karma Adhipati", "Neecha Bhanga"], "risks": ["Mars (Lagna lord) in H12 — Ops score 7 confirms", "Drive inward, not public-facing"]},
    "Pi CH":         {"yogas": ["Malavya Yoga", "Budha-Aditya", "2x Viparita Raja", "Vesi"], "risks": ["Ketu antara now (confusion, endings)", "Aries = lone wolf, struggles with partnership"]},
    "Lalu":          {"yogas": ["Raja Yoga", "DKA Yoga", "Viparita Raja"], "risks": ["Age 68 — legacy stage not startup", "Ketu antara (withdrawal)", "Saturn/Mars intense karma"]},
    "Reddit Girl":   {"yogas": ["Hamsa+Malavya+Yoga Karaka Venus", "8 yogas total"], "risks": ["Very young (23)", "Venus/Venus bhukti = social/comfort seeking now", "Needs mentorship first"]},
    "Tintu":         {"yogas": ["Hamsa Yoga", "Sasa Yoga", "10 yogas", "Jupiter exalted H7"], "risks": ["Ketu bhukti (endings, confusion)", "H12 stellium (private energy)"]},
    "Cini":          {"yogas": ["Parivartana Raja", "Gajakesari", "Amala"], "risks": ["All skill scores very low (yogas don't fire well)", "Rahu/Saturn double heavy dasha", "Planets weakly placed despite yogas"]},
    "Khayel CH":     {"yogas": ["Budha-Aditya", "Raja Yoga (Jup+Sat)", "Gajakesari"], "risks": ["Kemadruma (emotional instability)", "Saturn/Mars bhukti (obstacle-heavy)", "Best in structured org"]},
    "Soniya":        {"yogas": ["Sasa+Adhi+7 strong yogas", "H8 stellium (Viparita Rajas)"], "risks": ["Moon mahadasha (emotional, reactive)", "H8 stellium = wealth through others/crisis, not clean startup"]},
    "Vasudevan":     {"yogas": ["Gajakesari", "Yoga Karaka Mars"], "risks": ["Kemadruma Yoga (big drag)", "All scores below 35 — weakest chart overall", "Jupiter/Venus bhukti = idealism over execution"]},
    "Remya":         {"yogas": ["Bhadra Yoga (Mercury exalted H1)", "Budha-Aditya", "2x Viparita Raja", "4-planet H1 stellium"], "risks": ["Kemadruma Yoga (flanking issue)", "Mercury/Jupiter = sharp mind but needs grounding"]},
    "Ammu CH":       {"yogas": ["Budha-Aditya", "Yoga Karaka Mars", "Viparita Raja (Jup exalted H12)"], "risks": ["Kemadruma", "Saturn/Jupiter long dasha (slow, karmic build)"]},
    "Biju Jacob":    {"yogas": ["Sasa Yoga", "Raja Yoga (Sat+Mer H1)", "Budha-Aditya", "Viparita Raja"], "risks": ["Venus H12 (Lagna lord in loss house)", "Rahu/Moon/Sun dasha = emotional turbulence now"]},
    "Kiran":         {"yogas": ["Sasa Yoga", "Budha-Aditya", "Raja Yoga (Sun H10)", "Yoga Karaka"], "risks": ["Jupiter/Venus/Sun — good dasha but can over-expand", "Conservative Capricorn Lagna"]},
    "Ann CH":        {"yogas": ["Scorpio intensity", "Mars in own house"], "risks": ["Mars/Saturn/Ketu = brutal dasha combo", "Low scores across all domains", "Very early career (31)"]},
    "Always CH":     {"yogas": ["Jupiter/Mercury dasha (expansive intellect)", "Budha-Aditya"], "risks": ["All scores moderate (40-53)", "Libra Lagna = needs harmony, startup = chaos"]},
    "Bodhi CH":      {"yogas": ["Jupiter/Mercury dasha (knowledge focus)", "Stable Taurus Lagna"], "risks": ["All scores exactly 53 (balanced but not exceptional)", "Taurus = prefers stability over risk"]},
    "Kunal":         {"yogas": ["Saturn/Saturn (discipline building phase)", "Pisces Lagna = visionary"], "risks": ["Saturn/Rahu = heavy karma, delayed rewards", "Ops-dominant but vision scattered"]},
    "Hari CH":       {"yogas": ["Bhadra Yoga (Mercury exalted H1)", "Viparita Raja (Sun+Mars+Jupiter H12)", "Ketu H1 (past-life intelligence)"], "risks": ["Venus debilitated H1 (weak partnerships/aesthetics)", "Saturn debilitated H8 (hidden structural cracks)", "Finance score lowest (two debilitations drag it)"]},
}

# ---------------------------------------------------------------------------
# Startup fitness scoring
# ---------------------------------------------------------------------------

DASHA_QUALITY = {
    "Jupiter": 85, "Venus": 80, "Mercury": 75, "Sun": 70,
    "Moon": 55, "Mars": 55,
    "Saturn": 40, "Rahu": 35, "Ketu": 20,
}

DIGNITY_SCORE = {3: 100, 2: 85, 1: 65, 0: 45, -1: 25, -2: 0}

HOUSE_QUALITY = {
    1: 90, 4: 80, 7: 80, 10: 80,   # kendra
    5: 85, 9: 85,                    # trikona
    2: 60, 11: 65,                   # artha
    3: 55, 6: 45,                    # upachaya/dusthana
    8: 35, 12: 30,                   # dusthana
}


def startup_score(chart, dasha_str, skills):
    lagna_sign = chart["ascendant"]["sign"]
    lagna_idx = SIGNS.index(lagna_sign)

    # Lagna lord
    ll = SIGN_LORD[lagna_sign]
    ll_sign = chart["planets"][ll]["sign"]
    ll_house = chart["planets"][ll]["house"]
    ll_dignity = _sign_dignity(ll, ll_sign)
    ll_score = (DIGNITY_SCORE[ll_dignity] * 0.6 + HOUSE_QUALITY.get(ll_house, 45) * 0.4)

    # 10th lord
    tenth_sign = SIGNS[(lagna_idx + 9) % 12]
    tl = SIGN_LORD[tenth_sign]
    tl_sign = chart["planets"][tl]["sign"]
    tl_house = chart["planets"][tl]["house"]
    tl_dignity = _sign_dignity(tl, tl_sign)
    tl_score = (DIGNITY_SCORE[tl_dignity] * 0.6 + HOUSE_QUALITY.get(tl_house, 45) * 0.4)

    # Mars (drive/initiation)
    mars_sign = chart["planets"]["Mars"]["sign"]
    mars_house = chart["planets"]["Mars"]["house"]
    mars_dignity = _sign_dignity("Mars", mars_sign)
    mars_score = (DIGNITY_SCORE[mars_dignity] * 0.5 + HOUSE_QUALITY.get(mars_house, 45) * 0.5)

    # Sun (authority/leadership)
    sun_sign = chart["planets"]["Sun"]["sign"]
    sun_dignity = _sign_dignity("Sun", sun_sign)
    sun_score = DIGNITY_SCORE[sun_dignity]

    # Dasha timing
    parts = dasha_str.split("/")
    maha = parts[0].strip() if parts else "Saturn"
    bhukti = parts[1].strip() if len(parts) > 1 else maha
    maha_q = DASHA_QUALITY.get(maha, 45)
    bhuk_q = DASHA_QUALITY.get(bhukti, 45)
    dasha_q = maha_q * 0.65 + bhuk_q * 0.35

    # Skill floor penalty
    min_skill = min(skills.values())
    if min_skill < 15:
        floor_penalty = -25
    elif min_skill < 25:
        floor_penalty = -10
    else:
        floor_penalty = 0

    # Overall skill average as proxy for chart strength
    avg_skill = sum(skills.values()) / len(skills)

    # Weighted total
    raw = (
        ll_score    * 0.25 +
        tl_score    * 0.20 +
        mars_score  * 0.15 +
        sun_score   * 0.10 +
        dasha_q     * 0.20 +
        avg_skill   * 0.10
    ) + floor_penalty

    return round(min(100, max(0, raw)))


def startup_tier(score):
    if score >= 68:
        return ("🚀", "Startup-Ready",   "#5a8f72",  "Built for it — strong enough to go alone or lead a team")
    if score >= 55:
        return ("🌱", "Founder-Track",   "#c49e40",  "Can found with the right co-founder covering gaps")
    if score >= 42:
        return ("🔄", "Conditional",     "#5b8fd4",  "Strong in one domain; better as early employee / co-founder #3")
    return ("🏢", "Specialist",         "#c4607a",  "Thrives in structured role; startup pressure is misaligned")


# ---------------------------------------------------------------------------
# Skill scoring
# ---------------------------------------------------------------------------

SKILL_PLANETS = {
    "Product":    ["Jupiter", "Venus", "Mercury"],
    "Operations": ["Saturn", "Mars", "Mercury"],
    "Sales":      ["Venus", "Mercury", "Moon"],
    "Marketing":  ["Venus", "Mercury", "Sun"],
    "Finance":    ["Jupiter", "Saturn", "Venus"],
}
SKILL_MIN, SKILL_MAX = -6, 9

def compute_skills(chart):
    skills = {}
    for skill, planets in SKILL_PLANETS.items():
        raw = sum(_sign_dignity(p, chart["planets"][p]["sign"]) for p in planets)
        skills[skill] = round((raw - SKILL_MIN) / (SKILL_MAX - SKILL_MIN) * 100)
    return skills

def best_domain(skills):
    return max(skills, key=skills.get)


# ---------------------------------------------------------------------------
# Compute all charts
# ---------------------------------------------------------------------------

print("Computing charts for all profiles...", flush=True)
results = []
for (name, dob, t, lat, lon, tz, lagna, dasha, animal, gender) in PROFILES:
    try:
        chart = calculate_chart(dob, t, lat, lon, tz)
        skills = compute_skills(chart)
        best = best_domain(skills)
        ss = startup_score(chart, dasha, skills)
        tier_icon, tier_name, tier_color, tier_desc = startup_tier(ss)
        age = (date.today() - datetime.strptime(dob, "%Y-%m-%d").date()).days // 365
        ctx = KNOWN_CONTEXT.get(name, {"yogas": [], "risks": []})
        results.append({
            "name": name, "lagna": lagna, "dasha": dasha,
            "animal": animal, "gender": gender, "age": age,
            "skills": skills, "best": best,
            "startup_score": ss,
            "tier_icon": tier_icon, "tier_name": tier_name,
            "tier_color": tier_color, "tier_desc": tier_desc,
            "yogas": ctx["yogas"], "risks": ctx["risks"],
            "chart": chart,
        })
        print(f"  ✓ {name:18s} | {lagna:12s} | Startup:{ss:3d} ({tier_name})")
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        import traceback; traceback.print_exc()

for r in results:
    r["overall"] = round(sum(r["skills"].values()) / 5)

ranked_all     = sorted(results, key=lambda x: -x["startup_score"])
ranked_skills  = sorted(results, key=lambda x: -x["overall"])


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

DOMAIN_COLORS = {
    "Product":    "#7c5cbf",
    "Operations": "#c4607a",
    "Sales":      "#5b8fd4",
    "Marketing":  "#c49e40",
    "Finance":    "#5a8f72",
}
DOMAIN_ICONS = {
    "Product": "🔮", "Operations": "⚙️",
    "Sales": "🤝", "Marketing": "📣", "Finance": "💰",
}
LAGNA_ICONS = {
    "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋","Leo":"♌","Virgo":"♍",
    "Libra":"♎","Scorpio":"♏","Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓",
}

def bar(val, color, h="8px"):
    return (f'<div style="background:rgba(255,255,255,0.07);border-radius:99px;height:{h};overflow:hidden;margin-top:4px">'
            f'<div style="width:{val}%;height:100%;background:{color};border-radius:99px"></div></div>')

def skill_pill(name, val):
    color = DOMAIN_COLORS[name]
    return (f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">'
            f'<span style="font-size:.65rem;color:rgba(240,232,216,0.5);width:58px;flex-shrink:0">{name[:4].upper()}</span>'
            f'{bar(val, color, "5px")}'
            f'<span style="font-size:.72rem;color:{color};font-weight:600;min-width:26px;text-align:right">{val}</span></div>')


# ---------------------------------------------------------------------------
# Startup tiers section
# ---------------------------------------------------------------------------

tier_order = ["🚀 Startup-Ready", "🌱 Founder-Track", "🔄 Conditional", "🏢 Specialist"]
tier_groups = {"🚀 Startup-Ready": [], "🌱 Founder-Track": [], "🔄 Conditional": [], "🏢 Specialist": []}
for r in ranked_all:
    key = f"{r['tier_icon']} {r['tier_name']}"
    tier_groups[key].append(r)

startup_section_html = ""
for tier_key in tier_order:
    members = tier_groups[tier_key]
    if not members:
        continue
    tc = members[0]["tier_color"]
    ti = members[0]["tier_icon"]
    td = members[0]["tier_desc"]

    rows = ""
    for r in members:
        yogas_html = " ".join(f'<span class="badge-yoga">{y}</span>' for y in r["yogas"][:3]) or "—"
        risks_html = " ".join(f'<span class="badge-risk-sm">{rk}</span>' for rk in r["risks"][:2]) or "—"
        rows += f"""
        <tr>
          <td>{r["animal"]} <strong>{r["name"]}</strong><br>
            <span style="font-size:.7rem;color:var(--muted)">{LAGNA_ICONS.get(r["lagna"],"✦")} {r["lagna"]} · {r["age"]}y</span></td>
          <td>
            <div style="display:flex;align-items:center;gap:8px">
              <div style="width:80px;background:rgba(255,255,255,0.07);border-radius:99px;height:8px">
                <div style="width:{r["startup_score"]}%;height:8px;background:{tc};border-radius:99px"></div>
              </div>
              <strong style="color:{tc}">{r["startup_score"]}</strong>
            </div>
          </td>
          <td style="font-size:.72rem;color:rgba(196,158,64,0.7)">⏱ {r["dasha"]}</td>
          <td style="font-size:.72rem">
            <span style="color:{DOMAIN_COLORS[r['best']]};font-weight:600">{DOMAIN_ICONS[r['best']]} {r['best']}</span>
            <span style="color:var(--muted)"> · avg {r["overall"]}</span>
          </td>
          <td style="font-size:.72rem;line-height:1.7">{yogas_html}</td>
          <td style="font-size:.72rem;line-height:1.7">{risks_html}</td>
        </tr>"""

    startup_section_html += f"""
    <div class="tier-block" style="border-left:4px solid {tc}">
      <div class="tier-head">
        <span class="tier-icon">{ti}</span>
        <div>
          <div class="tier-name" style="color:{tc}">{tier_key}</div>
          <div class="tier-desc">{td}</div>
        </div>
        <div class="tier-count" style="background:{tc}22;color:{tc};border:1px solid {tc}44">{len(members)} profiles</div>
      </div>
      <table class="startup-table">
        <thead><tr>
          <th>Name</th><th>Fit Score</th><th>Current Dasha</th>
          <th>Best Domain</th><th>Key Strengths</th><th>Watch Out</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


# ---------------------------------------------------------------------------
# Full comparison table (skills)
# ---------------------------------------------------------------------------

from collections import defaultdict
by_domain = defaultdict(list)
for r in results:
    by_domain[r["best"]].append(r)

top_html = ""
for rank, r in enumerate(ranked_skills, 1):
    skills = r["skills"]
    best = r["best"]
    bc = DOMAIN_COLORS[best]
    tc = r["tier_color"]
    cells = "".join(
        f'<td><span style="color:{DOMAIN_COLORS[s]};font-weight:{"700" if s==best else "400"}">{skills[s]}</span></td>'
        for s in ["Product", "Operations", "Sales", "Marketing", "Finance"]
    )
    top_html += f"""
    <tr>
      <td><span class="rank">#{rank}</span></td>
      <td>{r["animal"]} <strong>{r["name"]}</strong></td>
      <td><span style="font-size:.75rem">{LAGNA_ICONS.get(r["lagna"],"✦")} {r["lagna"]}</span></td>
      {cells}
      <td><span class="badge-best" style="background:{bc}22;color:{bc};border:1px solid {bc}44">{DOMAIN_ICONS[best]} {best}</span></td>
      <td><strong style="color:{bc}">{r["overall"]}</strong></td>
      <td><span class="badge-tier" style="background:{tc}22;color:{tc};border:1px solid {tc}44">{r["tier_icon"]} {r["tier_name"]}</span></td>
    </tr>"""


# ---------------------------------------------------------------------------
# Profile cards (sorted by startup score)
# ---------------------------------------------------------------------------

cards_html = ""
for r in ranked_all:
    skills = r["skills"]
    best = r["best"]
    bc = DOMAIN_COLORS[best]
    tc = r["tier_color"]
    lsym = LAGNA_ICONS.get(r["lagna"], "✦")
    skill_bars = "".join(skill_pill(s, skills[s]) for s in ["Product", "Operations", "Sales", "Marketing", "Finance"])

    cards_html += f"""
    <div class="pcard" style="border-top:3px solid {tc}">
      <div class="pcard-head">
        <div class="pcard-animal">{r["animal"]}</div>
        <div style="flex:1;min-width:0">
          <div class="pcard-name">{r["name"]}</div>
          <div class="pcard-sub">{lsym} {r["lagna"]} · {r["age"]}y</div>
        </div>
        <div class="pcard-tier" style="background:{tc}22;border:1px solid {tc}44;color:{tc}">{r["tier_icon"]}</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div style="flex:1;background:rgba(255,255,255,0.07);border-radius:99px;height:6px">
          <div style="width:{r["startup_score"]}%;height:6px;background:{tc};border-radius:99px"></div>
        </div>
        <span style="font-size:.72rem;color:{tc};font-weight:700;min-width:30px">{r["startup_score"]}</span>
        <span style="font-size:.65rem;color:{tc}">{r["tier_name"]}</span>
      </div>
      <div class="pcard-dasha">⏱ {r["dasha"]}</div>
      <div class="pcard-skills">{skill_bars}</div>
      <div class="pcard-overall">Best: <strong style="color:{bc}">{DOMAIN_ICONS[best]} {best}</strong> · Avg: <strong>{r["overall"]}</strong></div>
    </div>"""


# ---------------------------------------------------------------------------
# Domain tabs (by best skill domain)
# ---------------------------------------------------------------------------

domain_tabs_html = ""
domain_panels_html = ""
for domain, color in DOMAIN_COLORS.items():
    icon = DOMAIN_ICONS[domain]
    members = sorted(by_domain[domain], key=lambda x: -x["skills"][domain])
    domain_tabs_html += (
        f'<button class="dtab" data-domain="{domain}" onclick="showDomain(this)" '
        f'style="border-bottom-color:{color}">{icon} {domain} '
        f'<span class="dtab-count">{len(members)}</span></button>'
    )
    rows = ""
    for rank, r in enumerate(members, 1):
        sc = r["skills"][domain]
        tc = r["tier_color"]
        rows += f"""
        <tr>
          <td><span class="rank">#{rank}</span></td>
          <td><span style="font-size:1rem">{r["animal"]}</span> <strong>{r["name"]}</strong></td>
          <td><span style="font-size:.75rem;color:var(--muted)">{LAGNA_ICONS.get(r["lagna"],"✦")} {r["lagna"]}</span></td>
          <td style="font-size:.75rem;color:rgba(240,232,216,0.55)">{r["dasha"]}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px">
              <div style="flex:1;background:rgba(255,255,255,0.07);border-radius:99px;height:8px;min-width:80px">
                <div style="width:{sc}%;height:8px;background:{color};border-radius:99px"></div>
              </div>
              <strong style="color:{color};font-size:.85rem">{sc}</strong>
            </div>
          </td>
          <td><span class="badge-tier" style="background:{tc}22;color:{tc};border:1px solid {tc}44">{r["tier_icon"]} {r["tier_name"]}</span></td>
          <td style="font-size:.72rem;color:var(--muted)">{r["overall"]}</td>
        </tr>"""

    domain_panels_html += f"""
    <div class="dpanel" id="dp-{domain}" style="display:none">
      <p style="font-size:.82rem;color:var(--muted);margin-bottom:16px">
        {len(members)} profiles strongest in <strong style="color:{color}">{icon} {domain}</strong>
        — planets: {", ".join(SKILL_PLANETS[domain])}
      </p>
      <table class="dtable">
        <thead><tr><th>#</th><th>Name</th><th>Lagna</th><th>Dasha</th>
          <th style="min-width:160px">{domain} Score</th><th>Startup Fit</th><th>Avg</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


# ---------------------------------------------------------------------------
# Render full HTML
# ---------------------------------------------------------------------------

today = datetime.today().strftime("%B %d, %Y")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="robots" content="noindex, nofollow">
  <title>Astrowise — Profiles Skills & Startup Fitness</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root{{--bg:#0b0b18;--surface:rgba(255,255,255,0.035);--border:rgba(196,158,64,0.18);
      --gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.55);
      --plum:#7c5cbf;--rose:#c4607a;--sage:#5a8f72;--blue:#5b8fd4;
      --shadow:0 20px 60px rgba(0,0,0,0.45);--r:22px}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'DM Sans',system-ui,sans-serif;background-color:var(--bg);
      background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(124,92,191,0.18),transparent),
        radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.12),transparent);
      background-attachment:fixed;color:var(--cream);min-height:100vh;padding:48px 24px 80px}}
    .container{{max-width:1400px;margin:0 auto}}

    .hero{{text-align:center;margin-bottom:52px}}
    .hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(2.5rem,6vw,4.5rem);font-weight:300;color:#fff8f0}}
    .hero-sub{{font-size:.85rem;color:var(--muted);margin-top:10px;letter-spacing:.06em}}
    .eyebrow{{font-size:.7rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}}

    .stats-bar{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-bottom:44px}}
    .stat-pill{{background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:9px 20px;font-size:.8rem}}
    .stat-pill strong{{color:var(--gold2)}}

    .panel{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:28px;box-shadow:var(--shadow);margin-bottom:36px}}

    .section-head{{margin-bottom:24px}}
    .section-title{{font-family:'Cormorant Garamond',serif;font-size:1.9rem;font-weight:300;color:var(--cream)}}
    .section-eyebrow{{font-size:.68rem;letter-spacing:.25em;text-transform:uppercase;color:var(--gold);margin-bottom:8px}}

    /* STARTUP TIERS */
    .tier-block{{background:rgba(255,255,255,0.025);border-radius:18px;padding:20px 24px;margin-bottom:20px}}
    .tier-head{{display:flex;align-items:center;gap:14px;margin-bottom:16px}}
    .tier-icon{{font-size:1.8rem;flex-shrink:0}}
    .tier-name{{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:400}}
    .tier-desc{{font-size:.78rem;color:var(--muted);margin-top:3px}}
    .tier-count{{margin-left:auto;flex-shrink:0;padding:5px 14px;border-radius:999px;font-size:.75rem;font-weight:600}}
    .startup-table{{width:100%;border-collapse:collapse;font-size:.84rem}}
    .startup-table th{{text-align:left;padding:8px 12px;background:rgba(196,158,64,0.08);color:var(--gold);
      font-size:.65rem;letter-spacing:.15em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,0.15)}}
    .startup-table td{{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.04);vertical-align:top;line-height:1.5}}
    .startup-table tr:last-child td{{border-bottom:none}}
    .startup-table tr:hover td{{background:rgba(255,255,255,0.02)}}
    .badge-yoga{{background:rgba(90,143,114,0.12);border:1px solid rgba(90,143,114,0.25);color:#80c4a0;
      padding:2px 8px;border-radius:999px;font-size:.65rem;display:inline-block;margin:1px}}
    .badge-risk-sm{{background:rgba(196,96,122,0.1);border:1px solid rgba(196,96,122,0.2);color:#e8909f;
      padding:2px 8px;border-radius:999px;font-size:.65rem;display:inline-block;margin:1px}}

    /* FULL TABLE */
    .full-table{{width:100%;border-collapse:collapse;font-size:.86rem}}
    .full-table th{{text-align:left;padding:10px 14px;background:rgba(196,158,64,0.1);color:var(--gold);
      font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,0.2)}}
    .full-table td{{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.05);vertical-align:middle}}
    .full-table tr:hover td{{background:rgba(255,255,255,0.02)}}
    .full-table tr:last-child td{{border-bottom:none}}
    .rank{{font-size:.7rem;color:var(--muted);font-weight:600}}
    .badge-best{{padding:3px 10px;border-radius:999px;font-size:.7rem;font-weight:600;white-space:nowrap}}
    .badge-tier{{padding:3px 10px;border-radius:999px;font-size:.68rem;font-weight:600;white-space:nowrap}}

    /* DOMAIN TABS */
    .dtabs{{display:flex;border-bottom:1px solid var(--border);margin-bottom:24px;flex-wrap:wrap}}
    .dtab{{background:none;border:none;border-bottom:2px solid transparent;padding:12px 18px;
      font-family:'DM Sans',sans-serif;font-size:.82rem;color:var(--muted);cursor:pointer;margin-bottom:-1px;transition:.2s}}
    .dtab:hover,.dtab.active{{color:var(--cream)}}
    .dtab.active{{border-bottom-width:2px;border-bottom-style:solid}}
    .dtab-count{{background:rgba(255,255,255,0.1);border-radius:999px;padding:2px 7px;font-size:.65rem;margin-left:5px}}
    .dtable{{width:100%;border-collapse:collapse;font-size:.85rem}}
    .dtable th{{text-align:left;padding:8px 14px;background:rgba(196,158,64,0.08);color:var(--gold);
      font-size:.65rem;letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,0.15)}}
    .dtable td{{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.05);vertical-align:middle}}
    .dtable tr:last-child td{{border-bottom:none}}
    .dtable tr:hover td{{background:rgba(255,255,255,0.02)}}

    /* CARDS */
    .cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px;margin-bottom:40px}}
    .pcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:18px;box-shadow:var(--shadow);transition:.2s}}
    .pcard:hover{{transform:translateY(-3px);box-shadow:0 30px 80px rgba(0,0,0,0.5)}}
    .pcard-head{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
    .pcard-animal{{font-size:1.9rem;flex-shrink:0;width:40px;text-align:center}}
    .pcard-name{{font-family:'Cormorant Garamond',serif;font-size:1.15rem;font-weight:400;color:#fff8f0}}
    .pcard-sub{{font-size:.7rem;color:var(--muted);margin-top:1px}}
    .pcard-tier{{flex-shrink:0;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1rem}}
    .pcard-dasha{{font-size:.7rem;color:rgba(196,158,64,0.6);margin-bottom:10px}}
    .pcard-skills{{margin-bottom:8px}}
    .pcard-overall{{font-size:.7rem;color:var(--muted);text-align:right}}

    /* DIVIDER */
    .divider{{display:flex;align-items:center;gap:16px;margin:44px 0 28px;font-size:.65rem;letter-spacing:.3em;text-transform:uppercase;color:rgba(240,232,216,0.3)}}
    .divider::before,.divider::after{{content:'';flex:1;height:1px;background:var(--border)}}

    /* LEGEND */
    .domain-legend{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:26px}}
    .dl-item{{display:flex;align-items:center;gap:7px;font-size:.76rem;color:var(--muted)}}
    .dl-dot{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}

    .footer{{text-align:center;padding:24px 0;font-size:.72rem;color:rgba(240,232,216,0.3);
      letter-spacing:.08em;border-top:1px solid var(--border);margin-top:40px}}

    @media(max-width:768px){{
      .cards-grid{{grid-template-columns:1fr}}
      .startup-table,.full-table,.dtable{{font-size:.76rem}}
      .tier-head{{flex-wrap:wrap}}
    }}
  </style>
</head>
<body>
<div class="container">

  <div class="hero">
    <div class="eyebrow">Vedic Jyotish · Lahiri Ayanamsha · Swiss Ephemeris</div>
    <h1>Profiles — Skills & Startup Fitness</h1>
    <div class="hero-sub">{len(results)} charts · 5 domains · Startup fitness score = Lagna lord + 10th lord + Mars drive + dasha timing · Generated {today}</div>
  </div>

  <div class="stats-bar">
    <div class="stat-pill">📊 <strong>{len(results)}</strong> Total Profiles</div>
    <div class="stat-pill">🚀 Startup-Ready: <strong>{sum(1 for r in results if r["tier_name"]=="Startup-Ready")}</strong></div>
    <div class="stat-pill">🌱 Founder-Track: <strong>{sum(1 for r in results if r["tier_name"]=="Founder-Track")}</strong></div>
    <div class="stat-pill">🔄 Conditional: <strong>{sum(1 for r in results if r["tier_name"]=="Conditional")}</strong></div>
    <div class="stat-pill">🏢 Specialist: <strong>{sum(1 for r in results if r["tier_name"]=="Specialist")}</strong></div>
  </div>

  <!-- STARTUP FITNESS TIERS -->
  <div class="divider">Startup Fitness — Who's Built For It</div>
  <div class="panel">
    <div class="section-head">
      <div class="section-eyebrow">Scored on: Lagna lord strength · 10th lord dignity · Mars drive · Current dasha quality · Skill floor</div>
      <div class="section-title">Startup Fitness by Tier</div>
    </div>
    {startup_section_html}
  </div>

  <!-- FULL SKILLS TABLE -->
  <div class="divider">All Profiles — Skills Comparison</div>
  <div class="domain-legend">
    {"".join(f'<div class="dl-item"><div class="dl-dot" style="background:{c}"></div><span>{DOMAIN_ICONS[d]} <strong style="color:{c}">{d}</strong> — {", ".join(SKILL_PLANETS[d])}</span></div>' for d, c in DOMAIN_COLORS.items())}
  </div>
  <div class="panel">
    <table class="full-table">
      <thead><tr>
        <th>#</th><th>Name</th><th>Lagna</th>
        <th>🔮 Prod</th><th>⚙️ Ops</th><th>🤝 Sales</th><th>📣 Mktg</th><th>💰 Fin</th>
        <th>Best Domain</th><th>Avg</th><th>Startup Fit</th>
      </tr></thead>
      <tbody>{top_html}</tbody>
    </table>
  </div>

  <!-- BY DOMAIN TABS -->
  <div class="divider">Ranked by Best Domain</div>
  <div class="panel">
    <div class="dtabs" id="dtabs">{domain_tabs_html}</div>
    {domain_panels_html}
  </div>

  <!-- PROFILE CARDS (sorted by startup score) -->
  <div class="divider">Profile Cards — Sorted by Startup Fitness</div>
  <div class="cards-grid">{cards_html}</div>

  <div class="footer">Generated {today} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris · {len(results)} profiles · Startup score = Lagna lord (25%) + 10th lord (20%) + Mars (15%) + Sun (10%) + Dasha timing (20%) + Skill avg (10%)</div>
</div>

<script>
  function showDomain(btn) {{
    document.querySelectorAll('.dtab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.dpanel').forEach(p => p.style.display = 'none');
    btn.classList.add('active');
    document.getElementById('dp-' + btn.dataset.domain).style.display = 'block';
  }}
  const firstTab = document.querySelector('.dtab');
  if (firstTab) showDomain(firstTab);
</script>
</body>
</html>"""

out_path = "docs/profiles_skills_dashboard.html"
with open(out_path, "w") as f:
    f.write(html)

print(f"\n✅ Dashboard written → {out_path}")
print(f"\nStartup Fitness Summary:")
for tier_key in tier_order:
    members = tier_groups[tier_key]
    if members:
        names = [r["name"] for r in members]
        print(f"  {tier_key} ({len(members)}): {', '.join(names)}")
