#!/usr/bin/env python3
"""
Generate all-profiles skill dashboard HTML.
Computes 5 skill scores per person from chart dignities.
"""

import sys, json
from datetime import datetime, date
sys.path.insert(0, "/home/jo/claude_projects/P046_202604_KnowThyselfAstro")

from astro_engine.calc import calculate_chart
from astro_engine.yoga import SIGN_LORD, EXALT_SIGN, DEBIL_SIGN, OWN_SIGNS
from astro_engine.match import _sign_dignity, _planet_relation

# ---------------------------------------------------------------------------
# All profiles — (name, dob, time, lat, lon, tz, lagna_label, dasha, animal, gender)
# ---------------------------------------------------------------------------
PROFILES = [
    # (name, dob, time, lat, lon, timezone, lagna, current_dasha, animal_emoji, gender)
    ("Joseph TC",    "1984-08-05", "15:30", 10.10, 76.36, "Asia/Kolkata",  "Sagittarius", "Venus/Venus/Mercury",    "🦅", "M"),
    ("Goldy",        "1985-03-07", "07:15",  9.60, 76.45, "Asia/Kolkata",  "Pisces",      "Rahu/Venus/Venus",       "🐬", "M"),
    ("Prakashji",    "1973-11-04", "01:22", 10.77, 76.65, "Asia/Kolkata",  "Leo",         "Saturn/Moon/Mercury",    "🦁", "M"),
    ("Gewin",        "1984-12-11", "11:55", 23.61, 58.59, "Asia/Muscat",   "Aquarius",    "Ketu/Moon/Saturn",       "🦅", "M"),
    ("Mirjam",       "1975-05-27", "23:00", 52.63,  4.75, "Europe/Amsterdam","Sagittarius","Rahu/Ketu/Rahu",        "🦢", "F"),
    ("Ruhi CH",      "2002-03-03", "02:00",  9.49, 76.33, "Asia/Kolkata",  "Sagittarius", "Jupiter/Mercury/Saturn", "🦌", "F"),
    ("Athens CH",    "2000-06-07", "20:08",  9.55, 76.78, "Asia/Kolkata",  "Sagittarius", "Sun/Mars/Jupiter",       "🦅", "M"),
    ("Zerin",        "2000-11-09", "09:25", 10.87, 76.33, "Asia/Kolkata",  "Sagittarius", "Venus/Sun/Mercury",      "🦌", "F"),
    ("Spirilla Guy", "1996-12-12", "10:15", 13.08, 80.27, "Asia/Kolkata",  "Capricorn",   "Moon/Venus/Jupiter",     "🐬", "M"),
    ("Gracious George","1985-07-24","07:30", 9.75, 77.08, "Asia/Kolkata",  "Cancer",      "Saturn/Saturn/Ketu",     "🐘", "M"),
    ("Yaqza",        "2003-09-19", "12:00", 11.25, 75.77, "Asia/Kolkata",  "Scorpio",     "Jupiter/Mercury/Sun",    "🦅", "M"),
    ("Isolda",       "1985-07-24", "14:04",  9.93, 76.26, "Asia/Kolkata",  "Scorpio",     "Saturn/Mercury/Mercury", "🦚", "F"),
    ("Jinx",         "2001-07-01", "23:30",  8.52, 76.94, "Asia/Kolkata",  "Pisces",      "Mercury/Ketu/Mercury",   "🐅", "F"),
    ("Sai",          "1991-02-24", "04:40",  8.52, 76.94, "Asia/Kolkata",  "Capricorn",   "Saturn/Saturn/Rahu",     "🦅", "M"),
    ("Vi CH",        "1998-08-23", "11:55",  8.52, 76.94, "Asia/Kolkata",  "Scorpio",     "Mars/Rahu/Venus",        "🦅", "F"),
    ("Pi CH",        "1989-10-01", "20:43", 10.52, 76.21, "Asia/Kolkata",  "Aries",       "Saturn/Saturn/Ketu",     "🐅", "F"),
    ("Lalu",         "1958-05-18", "19:30", 10.10, 76.36, "Asia/Kolkata",  "Scorpio",     "Saturn/Mars/Ketu",       "🐍", "F"),
    ("Reddit Girl",  "2002-11-16", "11:25", 26.91, 75.79, "Asia/Kolkata",  "Capricorn",   "Venus/Venus/Rahu",       "🦢", "F"),
    ("Tintu",        "1990-12-26", "09:30", 10.10, 76.36, "Asia/Kolkata",  "Capricorn",   "Venus/Ketu/Mercury",     "🐘", "M"),
    ("Cini",         "1985-10-29", "11:30", 23.61, 58.59, "Asia/Muscat",   "Sagittarius", "Rahu/Saturn/Saturn",     "🐘", "F"),
    ("Khayel CH",    "2001-01-01", "00:02", 25.20, 55.27, "Asia/Dubai",    "Virgo",       "Saturn/Mars/Jupiter",    "🦁", "F"),
    ("Soniya",       "1984-06-13", "16:15", 10.77, 76.65, "Asia/Kolkata",  "Libra",       "Moon/Saturn/Venus",      "🦚", "F"),
    ("Vasudevan",    "1999-06-23", "10:30", 10.02, 76.31, "Asia/Kolkata",  "Leo",         "Jupiter/Venus/Venus",    "🦁", "M"),
    ("Remya",        "1987-06-18", "06:30", 10.10, 76.36, "Asia/Kolkata",  "Gemini",      "Mercury/Jupiter/Mercury","🐬", "F"),
    ("Ammu CH",      "1990-09-05", "05:30",  8.52, 76.94, "Asia/Kolkata",  "Leo",         "Saturn/Jupiter/Jupiter", "🦁", "F"),
    ("Biju Jacob",   "1983-11-10", "05:30", 23.61, 58.59, "Asia/Muscat",   "Libra",       "Rahu/Moon/Sun",          "🦋", "M"),
    ("Kiran",        "1983-11-02", "12:58", 10.77, 76.00, "Asia/Kolkata",  "Capricorn",   "Jupiter/Venus/Sun",      "🦁", "M"),
    ("Ann CH",       "1994-08-09", "13:30",  9.94, 76.35, "Asia/Kolkata",  "Scorpio",     "Mars/Saturn/Ketu",       "🦋", "F"),
    ("Always CH",    "1991-09-21", "08:45", 28.70, 77.10, "Asia/Kolkata",  "Libra",       "Jupiter/Mercury/Sun",    "🦋", "M"),
    ("Bodhi CH",     "1991-09-05", "21:50",  9.73, 76.33, "Asia/Kolkata",  "Taurus",      "Jupiter/Mercury/Jupiter","🐘", "M"),
    ("Kunal",        "1993-09-10", "18:50", 27.56, 76.61, "Asia/Kolkata",  "Pisces",      "Saturn/Saturn/Rahu",     "🐅", "M"),
]

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

# Range: min=-6 (all debilitated), max=9 (all exalted)
SKILL_MIN, SKILL_MAX = -6, 9

def skill_raw(chart, planets_list):
    raw = 0
    for p in planets_list:
        sign = chart["planets"][p]["sign"]
        raw += _sign_dignity(p, sign)
    return raw

def skill_norm(raw):
    return round((raw - SKILL_MIN) / (SKILL_MAX - SKILL_MIN) * 100)

def best_domain(skills):
    return max(skills, key=skills.get)

def compute_skills(chart):
    skills = {}
    for skill, planets in SKILL_PLANETS.items():
        raw = skill_raw(chart, planets)
        skills[skill] = skill_norm(raw)
    return skills

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
        age = (date.today() - datetime.strptime(dob, "%Y-%m-%d").date()).days // 365
        results.append({
            "name": name, "lagna": lagna, "dasha": dasha,
            "animal": animal, "gender": gender, "age": age,
            "skills": skills, "best": best,
            "chart": chart,
        })
        print(f"  ✓ {name:18s} | {lagna:12s} | Prod:{skills['Product']:3d} Ops:{skills['Operations']:3d} Sales:{skills['Sales']:3d} Mktg:{skills['Marketing']:3d} Fin:{skills['Finance']:3d} → BEST: {best}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

DOMAIN_COLORS = {
    "Product":    "#7c5cbf",  # plum
    "Operations": "#c4607a",  # rose
    "Sales":      "#5b8fd4",  # blue
    "Marketing":  "#c49e40",  # gold
    "Finance":    "#5a8f72",  # sage
}

DOMAIN_ICONS = {
    "Product":    "🔮",
    "Operations": "⚙️",
    "Sales":      "🤝",
    "Marketing":  "📣",
    "Finance":    "💰",
}

LAGNA_ICONS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}

def bar(val, color, small=False):
    h = "6px" if small else "8px"
    return f'<div style="background:rgba(255,255,255,0.07);border-radius:99px;height:{h};overflow:hidden;margin-top:4px"><div style="width:{val}%;height:100%;background:{color};border-radius:99px;transition:width .4s"></div></div>'

def skill_pill(name, val):
    color = DOMAIN_COLORS[name]
    return f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px"><span style="font-size:.65rem;color:rgba(240,232,216,0.55);width:60px;flex-shrink:0">{name[:4].upper()}</span>{bar(val, color, True)}<span style="font-size:.72rem;color:{color};font-weight:600;min-width:26px;text-align:right">{val}</span></div>'

# Sort by best skill score descending within each domain cluster
results_sorted = sorted(results, key=lambda x: (-x["skills"][x["best"]], x["name"]))

# Group by best domain
from collections import defaultdict
by_domain = defaultdict(list)
for r in results:
    by_domain[r["best"]].append(r)

# Also rank all by overall (mean of 5 skills)
for r in results:
    r["overall"] = round(sum(r["skills"].values()) / 5)
ranked_all = sorted(results, key=lambda x: -x["overall"])

# Build HTML
today = datetime.today().strftime("%B %d, %Y")

cards_html = ""
for r in ranked_all:
    skills = r["skills"]
    best = r["best"]
    bcolor = DOMAIN_COLORS[best]
    bicon = DOMAIN_ICONS[best]
    lsym = LAGNA_ICONS.get(r["lagna"], "✦")

    skill_bars = "".join(skill_pill(s, skills[s]) for s in ["Product", "Operations", "Sales", "Marketing", "Finance"])

    cards_html += f"""
    <div class="pcard" style="border-top:3px solid {bcolor}">
      <div class="pcard-head">
        <div class="pcard-animal">{r["animal"]}</div>
        <div>
          <div class="pcard-name">{r["name"]}</div>
          <div class="pcard-sub">{lsym} {r["lagna"]} · {r["age"]}y</div>
        </div>
        <div class="pcard-best" style="background:{bcolor}22;border:1px solid {bcolor}44;color:{bcolor}">
          {bicon} {best}
        </div>
      </div>
      <div class="pcard-dasha">⏱ {r["dasha"]}</div>
      <div class="pcard-skills">{skill_bars}</div>
      <div class="pcard-overall">Overall: <strong style="color:{bcolor}">{r["overall"]}</strong>/100</div>
    </div>"""

# Domain cluster tabs
domain_tabs_html = ""
domain_panels_html = ""
for domain, color in DOMAIN_COLORS.items():
    icon = DOMAIN_ICONS[domain]
    members = sorted(by_domain[domain], key=lambda x: -x["skills"][domain])
    domain_tabs_html += f'<button class="dtab" data-domain="{domain}" onclick="showDomain(this)" style="border-bottom-color:{color}">{icon} {domain} <span class="dtab-count">{len(members)}</span></button>'

    rows = ""
    for rank, r in enumerate(members, 1):
        sc = r["skills"][domain]
        rows += f"""
        <tr>
          <td><span class="rank">#{rank}</span></td>
          <td><span class="animal-sm">{r["animal"]}</span> <strong>{r["name"]}</strong></td>
          <td><span style="font-size:.75rem;color:rgba(240,232,216,0.5)">{LAGNA_ICONS.get(r["lagna"],"✦")} {r["lagna"]}</span></td>
          <td style="font-size:.75rem;color:rgba(240,232,216,0.55)">{r["dasha"]}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px">
              <div style="flex:1;background:rgba(255,255,255,0.07);border-radius:99px;height:8px;min-width:80px">
                <div style="width:{sc}%;height:8px;background:{color};border-radius:99px"></div>
              </div>
              <strong style="color:{color};font-size:.85rem">{sc}</strong>
            </div>
          </td>
          <td style="font-size:.72rem;color:rgba(240,232,216,0.55)">{r["overall"]}</td>
        </tr>"""

    domain_panels_html += f"""
    <div class="dpanel" id="dp-{domain}" style="display:none">
      <p style="font-size:.82rem;color:rgba(240,232,216,0.55);margin-bottom:16px">
        {len(members)} profiles whose strongest domain is <strong style="color:{color}">{icon} {domain}</strong>
      </p>
      <table class="dtable">
        <thead><tr>
          <th>#</th><th>Name</th><th>Lagna</th><th>Current Dasha</th>
          <th style="min-width:160px">{domain} Score</th><th>Avg</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""

# Top performers table (all skills)
top_html = ""
for rank, r in enumerate(ranked_all, 1):
    skills = r["skills"]
    best = r["best"]
    bc = DOMAIN_COLORS[best]

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
    </tr>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="robots" content="noindex, nofollow">
  <title>Astrowise — All Profiles Skills Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg:#0b0b18; --surface:rgba(255,255,255,0.035); --border:rgba(196,158,64,0.18);
      --gold:#c49e40; --gold2:#e8c96a; --cream:#f0e8d8; --muted:rgba(240,232,216,0.55);
      --plum:#7c5cbf; --rose:#c4607a; --sage:#5a8f72; --blue:#5b8fd4;
      --shadow:0 20px 60px rgba(0,0,0,0.45); --r:22px;
    }}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'DM Sans',system-ui,sans-serif;background-color:var(--bg);
      background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(124,92,191,0.18),transparent),
        radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.12),transparent);
      background-attachment:fixed;color:var(--cream);min-height:100vh;padding:48px 24px 80px}}
    .container{{max-width:1400px;margin:0 auto}}

    /* HERO */
    .hero{{text-align:center;margin-bottom:56px}}
    .hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(2.5rem,6vw,4.5rem);font-weight:300;color:#fff8f0;letter-spacing:-.01em}}
    .hero-sub{{font-size:.85rem;color:var(--muted);margin-top:10px;letter-spacing:.08em}}
    .eyebrow{{font-size:.7rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}}

    /* STATS BAR */
    .stats-bar{{display:flex;gap:20px;justify-content:center;flex-wrap:wrap;margin-bottom:48px}}
    .stat-pill{{background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:10px 24px;font-size:.82rem}}
    .stat-pill strong{{color:var(--gold2)}}

    /* SECTION TITLES */
    .section-title{{font-family:'Cormorant Garamond',serif;font-size:1.8rem;font-weight:300;margin-bottom:6px}}
    .section-eyebrow{{font-size:.68rem;letter-spacing:.25em;text-transform:uppercase;color:var(--gold);margin-bottom:20px}}

    /* FULL TABLE */
    .panel{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:28px;box-shadow:var(--shadow);margin-bottom:40px}}
    .full-table{{width:100%;border-collapse:collapse;font-size:.86rem}}
    .full-table th{{text-align:left;padding:10px 14px;background:rgba(196,158,64,0.1);color:var(--gold);
      font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,0.2)}}
    .full-table td{{padding:11px 14px;border-bottom:1px solid rgba(255,255,255,0.05);vertical-align:middle}}
    .full-table tr:hover td{{background:rgba(255,255,255,0.025)}}
    .full-table tr:last-child td{{border-bottom:none}}
    .rank{{font-size:.7rem;color:var(--muted);font-weight:600}}
    .badge-best{{padding:3px 10px;border-radius:999px;font-size:.7rem;font-weight:600;white-space:nowrap}}
    .animal-sm{{font-size:1.1rem}}

    /* DOMAIN TABS */
    .dtabs{{display:flex;gap:0;border-bottom:1px solid var(--border);margin-bottom:24px;flex-wrap:wrap}}
    .dtab{{background:none;border:none;border-bottom:2px solid transparent;padding:12px 20px;
      font-family:'DM Sans',sans-serif;font-size:.82rem;color:var(--muted);cursor:pointer;transition:.2s;margin-bottom:-1px}}
    .dtab:hover,.dtab.active{{color:var(--cream)}}
    .dtab.active{{border-bottom-width:2px;border-bottom-style:solid}}
    .dtab-count{{background:rgba(255,255,255,0.1);border-radius:999px;padding:2px 8px;font-size:.65rem;margin-left:6px}}
    .dtable{{width:100%;border-collapse:collapse;font-size:.86rem}}
    .dtable th{{text-align:left;padding:8px 14px;background:rgba(196,158,64,0.08);color:var(--gold);
      font-size:.65rem;letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,0.15)}}
    .dtable td{{padding:11px 14px;border-bottom:1px solid rgba(255,255,255,0.05);vertical-align:middle}}
    .dtable tr:last-child td{{border-bottom:none}}
    .dtable tr:hover td{{background:rgba(255,255,255,0.02)}}

    /* PROFILE CARDS */
    .cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px;margin-bottom:40px}}
    .pcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
      padding:20px;box-shadow:var(--shadow);transition:.2s}}
    .pcard:hover{{transform:translateY(-3px);box-shadow:0 30px 80px rgba(0,0,0,0.5)}}
    .pcard-head{{display:flex;align-items:center;gap:12px;margin-bottom:12px}}
    .pcard-animal{{font-size:2rem;flex-shrink:0;width:44px;text-align:center}}
    .pcard-name{{font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-weight:400;color:#fff8f0}}
    .pcard-sub{{font-size:.72rem;color:var(--muted);margin-top:2px}}
    .pcard-best{{margin-left:auto;flex-shrink:0;padding:4px 10px;border-radius:999px;font-size:.68rem;font-weight:600;white-space:nowrap}}
    .pcard-dasha{{font-size:.72rem;color:rgba(196,158,64,0.6);margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid rgba(255,255,255,0.06)}}
    .pcard-skills{{margin-bottom:10px}}
    .pcard-overall{{font-size:.72rem;color:var(--muted);text-align:right}}

    /* DOMAIN LEGEND */
    .domain-legend{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}}
    .dl-item{{display:flex;align-items:center;gap:8px;font-size:.78rem;color:var(--muted)}}
    .dl-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}

    /* DIVIDER */
    .divider{{display:flex;align-items:center;gap:16px;margin:40px 0;font-size:.65rem;letter-spacing:.3em;text-transform:uppercase;color:rgba(240,232,216,0.3)}}
    .divider::before,.divider::after{{content:'';flex:1;height:1px;background:var(--border)}}

    /* FOOTER */
    .footer{{text-align:center;padding:24px 0;font-size:.72rem;color:rgba(240,232,216,0.3);letter-spacing:.08em;border-top:1px solid var(--border);margin-top:40px}}

    @media(max-width:768px){{
      .cards-grid{{grid-template-columns:1fr}}
      .stats-bar{{gap:10px}}
      .dtabs{{gap:0}}
      .dtab{{padding:10px 14px;font-size:.75rem}}
      .full-table,.dtable{{font-size:.78rem}}
    }}
  </style>
</head>
<body>
<div class="container">

  <!-- HERO -->
  <div class="hero">
    <div class="eyebrow">Vedic Jyotish · Lahiri Ayanamsha</div>
    <h1>Profiles Skills Map</h1>
    <div class="hero-sub">{len(results)} charts · 5 startup domains · Swiss Ephemeris ground truth · Generated {today}</div>
  </div>

  <!-- STATS BAR -->
  <div class="stats-bar">
    <div class="stat-pill">📊 <strong>{len(results)}</strong> Profiles</div>
    <div class="stat-pill">🔮 Best in Product: <strong>{sum(1 for r in results if r["best"]=="Product")}</strong></div>
    <div class="stat-pill">⚙️ Best in Ops: <strong>{sum(1 for r in results if r["best"]=="Operations")}</strong></div>
    <div class="stat-pill">🤝 Best in Sales: <strong>{sum(1 for r in results if r["best"]=="Sales")}</strong></div>
    <div class="stat-pill">📣 Best in Marketing: <strong>{sum(1 for r in results if r["best"]=="Marketing")}</strong></div>
    <div class="stat-pill">💰 Best in Finance: <strong>{sum(1 for r in results if r["best"]=="Finance")}</strong></div>
  </div>

  <!-- DOMAIN LEGEND -->
  <div class="domain-legend">
    {"".join(f'<div class="dl-item"><div class="dl-dot" style="background:{c}"></div><span>{DOMAIN_ICONS[d]} <strong style="color:{c}">{d}</strong> — {", ".join(SKILL_PLANETS[d])}</span></div>' for d, c in DOMAIN_COLORS.items())}
  </div>

  <!-- FULL COMPARISON TABLE -->
  <div class="divider">All Profiles — Full Comparison</div>
  <div class="panel">
    <table class="full-table">
      <thead><tr>
        <th>#</th><th>Name</th><th>Lagna</th>
        <th>🔮 Prod</th><th>⚙️ Ops</th><th>🤝 Sales</th><th>📣 Mktg</th><th>💰 Fin</th>
        <th>Best Domain</th><th>Avg</th>
      </tr></thead>
      <tbody>{top_html}</tbody>
    </table>
  </div>

  <!-- BY DOMAIN TABS -->
  <div class="divider">By Best Domain</div>
  <div class="panel">
    <div class="dtabs" id="dtabs">{domain_tabs_html}</div>
    {domain_panels_html}
  </div>

  <!-- PROFILE CARDS -->
  <div class="divider">Profile Cards</div>
  <div class="cards-grid">{cards_html}</div>

  <div class="footer">Generated {today} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris · {len(results)} profiles</div>
</div>

<script>
  // Initialize first domain tab
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

print(f"\n✅ Dashboard written to {out_path}")
print(f"   {len(results)} profiles computed")
print(f"\nDomain distribution:")
for d in ["Product", "Operations", "Sales", "Marketing", "Finance"]:
    count = sum(1 for r in results if r["best"] == d)
    names = [r["name"] for r in results if r["best"] == d]
    print(f"  {DOMAIN_ICONS[d]} {d:12s}: {count} — {', '.join(names)}")
