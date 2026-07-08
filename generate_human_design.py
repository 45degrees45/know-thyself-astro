#!/usr/bin/env python3
"""Generate Human Design group analysis HTML for all 32 profiles."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, date
from collections import Counter
from astro_engine.human_design import calculate

# ── Profile data (name, dob, tob, lat, lon, tz, animal, gender) ─────────────
PROFILES = [
    ("Joseph TC",     "1984-08-05","15:30", 10.10, 76.36,"Asia/Kolkata",  "🦅","M"),
    ("Goldy",         "1985-03-07","07:15",  9.60, 76.45,"Asia/Kolkata",  "🐬","M"),
    ("Prakashji",     "1973-11-04","01:22", 10.77, 76.65,"Asia/Kolkata",  "🦁","M"),
    ("Gewin",         "1984-12-11","11:55", 23.61, 58.59,"Asia/Muscat",   "🦅","M"),
    ("Mirjam",        "1975-05-27","23:00", 52.63,  4.75,"Europe/Amsterdam","🦢","F"),
    ("Ruhi CH",       "2002-03-03","02:00",  9.49, 76.33,"Asia/Kolkata",  "🦌","F"),
    ("Athens CH",     "2000-06-07","20:08",  9.55, 76.78,"Asia/Kolkata",  "🦅","M"),
    ("Zerin",         "2000-11-09","09:25", 10.87, 76.33,"Asia/Kolkata",  "🦌","F"),
    ("Spirilla Guy",  "1996-12-12","10:15", 13.08, 80.27,"Asia/Kolkata",  "🐬","M"),
    ("Gracious George","1985-07-24","07:30",  9.75, 77.08,"Asia/Kolkata", "🐘","M"),
    ("Yaqza",         "2003-09-19","12:00", 11.25, 75.77,"Asia/Kolkata",  "🦅","M"),
    ("Isolda",        "1985-07-24","14:04",  9.93, 76.26,"Asia/Kolkata",  "🦚","F"),
    ("Jinx",          "2001-07-01","23:30",  8.52, 76.94,"Asia/Kolkata",  "🐅","F"),
    ("Sai",           "1991-02-24","04:40",  8.52, 76.94,"Asia/Kolkata",  "🦅","M"),
    ("Vi CH",         "1998-08-23","11:55",  8.52, 76.94,"Asia/Kolkata",  "🦅","F"),
    ("Pi CH",         "1989-10-01","20:43", 10.52, 76.21,"Asia/Kolkata",  "🐅","F"),
    ("Lalu",          "1958-05-18","19:30", 10.10, 76.36,"Asia/Kolkata",  "🐍","F"),
    ("Reddit Girl",   "2002-11-16","11:25", 26.91, 75.79,"Asia/Kolkata",  "🦢","F"),
    ("Tintu",         "1990-12-26","09:30", 10.10, 76.36,"Asia/Kolkata",  "🐘","M"),
    ("Cini",          "1985-10-29","11:30", 23.61, 58.59,"Asia/Muscat",   "🐘","F"),
    ("Khayel CH",     "2001-01-01","00:02", 25.20, 55.27,"Asia/Dubai",    "🦁","F"),
    ("Soniya",        "1984-06-13","16:15", 10.77, 76.65,"Asia/Kolkata",  "🦚","F"),
    ("Vasudevan",     "1999-06-23","10:30", 10.02, 76.31,"Asia/Kolkata",  "🦁","M"),
    ("Remya",         "1987-06-18","06:30", 10.10, 76.36,"Asia/Kolkata",  "🐬","F"),
    ("Ammu CH",       "1990-09-05","05:30",  8.52, 76.94,"Asia/Kolkata",  "🦁","F"),
    ("Biju Jacob",    "1983-11-10","05:30", 23.61, 58.59,"Asia/Muscat",   "🦋","M"),
    ("Kiran",         "1983-11-02","12:58", 10.77, 76.00,"Asia/Kolkata",  "🦁","M"),
    ("Ann CH",        "1994-08-09","13:30",  9.94, 76.35,"Asia/Kolkata",  "🦋","F"),
    ("Always CH",     "1991-09-21","08:45", 28.70, 77.10,"Asia/Kolkata",  "🦋","M"),
    ("Bodhi CH",      "1991-09-05","21:50",  9.73, 76.33,"Asia/Kolkata",  "🐘","M"),
    ("Kunal",         "1993-09-10","18:50", 27.56, 76.61,"Asia/Kolkata",  "🐅","M"),
    ("Hari CH",       "1968-09-16","07:15",  8.52, 76.94,"Asia/Kolkata",  "🦊","M"),
    ("George Varghese","1961-12-15","22:30",10.11, 76.36,"Asia/Kolkata",  "🦁","M"),
]

ANON = {
    "Joseph TC":      "The Wise Eagle",
    "Goldy":          "Me",
    "Prakashji":      "The Royal Lion",
    "Gewin":          "The Mystic Eagle",
    "Mirjam":         "The White Swan",
    "Zerin":          "The Golden Deer",
    "Spirilla Guy":   "The Deep Dolphin",
    "Gracious George":"The Steady Elephant",
    "Yaqza":          "The Storm Eagle",
    "Isolda":         "The Dark Peacock",
    "Jinx":           "The Midnight Tiger",
    "Sai":            "The Mountain Eagle",
    "Lalu":           "The Ancient Cobra",
    "Reddit Girl":    "The Moonlit Swan",
    "Tintu":          "The Gentle Elephant",
    "Cini":           "The Desert Elephant",
    "Soniya":         "The Celestial Peacock",
    "Vasudevan":      "The Golden Lion",
    "Remya":          "The Swift Dolphin",
    "Biju Jacob":     "The Wandering Butterfly",
    "Kiran":          "The Stone Lion",
    "Ann CH":         "Ann CH",
    "Athens CH":      "Athens CH",
    "Ruhi CH":        "Ruhi CH",
    "Vi CH":          "Vi CH",
    "Pi CH":          "Pi CH",
    "Bodhi CH":       "Bodhi CH",
    "Ammu CH":        "Ammu CH",
    "Always CH":      "Always CH",
    "Khayel CH":      "Khayel CH",
    "Kunal":          "The Indigo Tiger",
    "Hari CH":        "The Watchful Fox",
    "George Varghese":"The Ancient Lion",
}

TYPE_META = {
    "Generator": {
        "color": "#5a8f72", "bg": "rgba(90,143,114,0.09)", "border": "rgba(90,143,114,0.28)",
        "stripe": "rgba(90,143,114,0.5)", "icon": "⚡",
        "founder_role": "The Builder",
        "founder_note": "Sustainably deep work energy. The engine of any startup — happiest doing and mastering. Best co-founder: Projector (strategy) or Manifestor (spark).",
    },
    "Manifesting Generator": {
        "color": "#c49e40", "bg": "rgba(196,158,64,0.09)", "border": "rgba(196,158,64,0.28)",
        "stripe": "rgba(196,158,64,0.5)", "icon": "🔥",
        "founder_role": "The Catalyst",
        "founder_note": "Multi-passionate, moves fast, can pivot. High output founder who needs freedom to skip steps. Best asset: turning ideas into motion instantly. Risk: burning out the team.",
    },
    "Manifestor": {
        "color": "#c4607a", "bg": "rgba(196,96,122,0.09)", "border": "rgba(196,96,122,0.28)",
        "stripe": "rgba(196,96,122,0.5)", "icon": "🚀",
        "founder_role": "The Pioneer",
        "founder_note": "Initiates independently, needs to inform (not ask permission). Classic solo founder archetype. Must communicate before acting or creates resistance. Rare — ~8% of population.",
    },
    "Projector": {
        "color": "#5b8fd4", "bg": "rgba(91,143,212,0.09)", "border": "rgba(91,143,212,0.28)",
        "stripe": "rgba(91,143,212,0.5)", "icon": "🎯",
        "founder_role": "The Strategist",
        "founder_note": "Sees the system nobody else sees. The CEO-type who works through others. Must wait for invitation — unsolicited advice creates friction. Thrives as co-founder or advisor.",
    },
    "Reflector": {
        "color": "#7c5cbf", "bg": "rgba(124,92,191,0.09)", "border": "rgba(124,92,191,0.28)",
        "stripe": "rgba(124,92,191,0.5)", "icon": "🔮",
        "founder_role": "The Mirror",
        "founder_note": "Rare (1%). Reflects the health of the team like a living barometer. Exceptional board member or strategic advisor. Needs 28 days before any major decision.",
    },
}

AUTHORITY_SHORT = {
    "Emotional": "Wait through emotional wave before deciding",
    "Sacral": "Trust gut yes/no in the moment",
    "Splenic": "One-time instinct — don't second-guess",
    "Ego-Manifested": "Commit only if you truly will it",
    "Self-Projected": "Speak it out — hear your own voice",
    "Mental": "Sample multiple trusted perspectives",
    "No Inner Authority": "Follow the environment",
}

# ── Compute all HD data ───────────────────────────────────────────────────────
print("Computing Human Design charts...", flush=True)
all_data = []
for row in PROFILES:
    name, dob, tob, lat, lon, tz, animal, gender = row
    age = (date.today() - datetime.strptime(dob, "%Y-%m-%d").date()).days // 365
    anon = ANON.get(name, name)
    gender_sym = "♂" if gender == "M" else "♀"
    is_me = (name == "Goldy")

    try:
        hd = calculate(dob, tob, lat, lon, tz)
    except Exception as e:
        print(f"  ERROR {name}: {e}", flush=True)
        hd = {"type": "Generator", "strategy": "Wait to respond",
              "authority": "Sacral — trust your gut response",
              "profile": "?/?", "cross_gates": (0,0,0,0),
              "defined_centers": [], "activated_gates": []}

    tm = TYPE_META[hd['type']]
    auth_text = hd['authority'].split(' — ')[0]

    all_data.append({
        "name": name, "anon": anon, "animal": animal,
        "age": age, "gender_sym": gender_sym, "is_me": is_me,
        "type": hd['type'],
        "strategy": hd['strategy'],
        "authority": hd['authority'],
        "authority_short": auth_text,
        "profile": hd['profile'],
        "cross_gates": hd['cross_gates'],
        "defined_centers": hd['defined_centers'],
        "tm": tm,
    })
    print(f"  ✓ {name}: {hd['type']} {hd['profile']}  [{auth_text}]", flush=True)

type_counts = Counter(d['type'] for d in all_data)
today_str = datetime.now().strftime("%d %B %Y")

# ── HTML generation ───────────────────────────────────────────────────────────
TYPE_ORDER = ["All", "Generator", "Manifesting Generator", "Manifestor", "Projector", "Reflector"]

def centers_html(centers, stripe_color):
    all_c = ['HEAD','AJNA','THROAT','G','HEART','SP','SACRAL','SPLEEN','ROOT']
    labels = {'HEAD':'Head','AJNA':'Ajna','THROAT':'Throat','G':'Identity',
              'HEART':'Ego','SP':'Solar Plexus','SACRAL':'Sacral',
              'SPLEEN':'Spleen','ROOT':'Root'}
    parts = []
    for c in all_c:
        if c in centers:
            parts.append(f'<span style="background:{stripe_color};color:#0b0b18;border-radius:4px;padding:2px 7px;font-size:0.7rem;font-weight:600;margin:2px 2px 2px 0;display:inline-block">{labels[c]}</span>')
        else:
            parts.append(f'<span style="background:rgba(255,255,255,0.05);color:rgba(240,232,216,0.3);border-radius:4px;padding:2px 7px;font-size:0.7rem;margin:2px 2px 2px 0;display:inline-block">{labels[c]}</span>')
    return "".join(parts)

def card_html(d):
    tm = d['tm']
    me_badge = ' <span style="background:rgba(196,158,64,0.2);border:1px solid rgba(196,158,64,0.4);color:#e8c96a;font-size:0.65rem;padding:2px 8px;border-radius:999px;vertical-align:middle;">You</span>' if d['is_me'] else ""
    cg = d['cross_gates']
    cross_str = f"{cg[0]}·{cg[1]} / {cg[2]}·{cg[3]}" if cg[0] else "—"
    ctrs = centers_html(d['defined_centers'], tm['color'])
    return f"""
<div class="card" data-type="{d['type']}">
  <div class="card-stripe" style="background:{tm['stripe']}"></div>
  <div class="card-body">
    <div class="card-top">
      <div>
        <div class="card-name">{d['anon']} {d['animal']}{me_badge}</div>
        <div class="card-sub">{d['age']}y {d['gender_sym']}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div class="type-badge" style="background:{tm['bg']};border:1px solid {tm['border']};color:{tm['color']}">{tm['icon']} {d['type']}</div>
        <div class="role-label" style="color:{tm['color']}">{tm['founder_role']}</div>
      </div>
    </div>

    <div class="meta-row">
      <div class="meta-item">
        <div class="meta-label">Strategy</div>
        <div class="meta-val" style="color:{tm['color']}">{d['strategy']}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Authority</div>
        <div class="meta-val">{d['authority_short']}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Profile</div>
        <div class="meta-val" style="color:{tm['color']};font-size:1.15rem;font-family:'Cormorant Garamond',serif">{d['profile']}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Cross</div>
        <div class="meta-val" style="font-size:0.78rem">{cross_str}</div>
      </div>
    </div>

    <div class="founder-box" style="background:{tm['bg']};border:1px solid {tm['border']}">
      <div class="meta-label" style="color:{tm['color']};margin-bottom:6px">As a Founder</div>
      <p style="font-size:0.84rem;line-height:1.65;color:rgba(240,232,216,0.82)">{tm['founder_note']}</p>
    </div>

    <div style="margin-top:12px">
      <div class="meta-label" style="margin-bottom:6px">Defined Centers</div>
      <div>{ctrs}</div>
    </div>
  </div>
</div>"""


tab_html = ""
for t in TYPE_ORDER:
    if t == "All":
        cnt = len(all_data)
        col = "#e8c96a"
        bg = "rgba(196,158,64,0.12)"
        ico = "✦"
        label = "All Types"
    else:
        tm = TYPE_META[t]
        cnt = type_counts.get(t, 0)
        col = tm['color']
        bg = tm['bg']
        ico = tm['icon']
        label = t
    active = ' tab-active' if t == "All" else ""
    tab_html += f'<button class="tab{active}" onclick="filterType(\'{t}\')" style="--tc:{col}">{ico} {label} <span class="tab-count">{cnt}</span></button>\n'

all_cards = "\n".join(card_html(d) for d in all_data)

# Stat pills
stat_pills = ""
for t in ["Generator","Manifesting Generator","Manifestor","Projector","Reflector"]:
    tm = TYPE_META[t]
    cnt = type_counts.get(t, 0)
    stat_pills += f'<div class="stat-pill"><span style="color:{tm["color"]}">{tm["icon"]}</span><span class="stat-pill-num" style="color:{tm["color"]}">{cnt}</span><span>{t}</span></div>\n'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow">
<title>Human Design — Group Reading</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0b0b18;--surface:rgba(255,255,255,0.035);--border:rgba(196,158,64,0.18);
  --gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.55);
  --shadow:0 20px 60px rgba(0,0,0,0.45);--r:20px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  font-family:'DM Sans',system-ui,sans-serif;font-size:15px;color:var(--cream);
  background-color:var(--bg);
  background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(196,158,64,0.14),transparent),
    radial-gradient(ellipse 60% 40% at 80% 110%,rgba(91,143,212,0.10),transparent);
  background-attachment:fixed;min-height:100vh;
}}
.hero{{max-width:1100px;margin:0 auto;padding:48px 24px 0;text-align:center}}
.hero-eyebrow{{font-size:0.68rem;letter-spacing:0.32em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}}
.hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(2.4rem,5vw,4rem);font-weight:300;color:#fff8f0;line-height:1.15;margin-bottom:10px}}
.hero-sub{{font-size:0.9rem;color:var(--muted);max-width:620px;margin:0 auto 10px;line-height:1.7}}
.hero-note{{font-size:0.78rem;color:rgba(240,232,216,0.35);margin-bottom:32px}}

.stat-row{{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-bottom:32px}}
.stat-pill{{background:var(--surface);border:1px solid var(--border);border-radius:999px;
  padding:8px 18px;font-size:0.82rem;display:flex;align-items:center;gap:8px}}
.stat-pill-num{{font-size:1.1rem;font-weight:600;font-family:'Cormorant Garamond',serif}}

.tabs{{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;max-width:1100px;margin:0 auto 28px;padding:0 24px}}
.tab{{background:var(--surface);border:1px solid rgba(255,255,255,0.08);border-radius:999px;
  padding:9px 18px;font-size:0.82rem;color:var(--muted);cursor:pointer;transition:all .2s;font-family:'DM Sans',sans-serif}}
.tab:hover{{border-color:var(--tc);color:var(--tc)}}
.tab-active{{background:rgba(255,255,255,0.06);border-color:var(--tc)!important;color:var(--tc)!important;font-weight:600}}
.tab-count{{background:rgba(255,255,255,0.08);border-radius:999px;padding:1px 7px;font-size:0.72rem;margin-left:4px}}

.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(460px,1fr));gap:20px;
  max-width:1100px;margin:0 auto;padding:0 24px 80px}}

.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);
  display:flex;overflow:hidden;box-shadow:var(--shadow);transition:transform .2s}}
.card:hover{{transform:translateY(-2px)}}
.card-stripe{{width:4px;flex-shrink:0}}
.card-body{{padding:20px 22px;flex:1;min-width:0}}
.card-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:14px}}
.card-name{{font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-weight:400;color:#fff8f0;margin-bottom:2px}}
.card-sub{{font-size:0.74rem;color:var(--muted)}}
.type-badge{{border-radius:999px;padding:5px 12px;font-size:0.72rem;font-weight:600;white-space:nowrap}}
.role-label{{font-size:0.68rem;color:var(--muted);text-align:right;margin-top:4px;font-style:italic}}

.meta-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}}
.meta-item{{background:rgba(255,255,255,0.03);border-radius:10px;padding:10px 12px}}
.meta-label{{font-size:0.62rem;letter-spacing:0.18em;text-transform:uppercase;color:var(--gold);margin-bottom:4px}}
.meta-val{{font-size:0.82rem;color:rgba(240,232,216,0.88);line-height:1.4}}

.founder-box{{border-radius:12px;padding:12px 14px;margin-bottom:12px}}

.card.hidden{{display:none}}
.footer{{text-align:center;padding:20px 0;font-size:0.72rem;color:rgba(240,232,216,0.3);
  letter-spacing:0.08em;border-top:1px solid var(--border);margin-top:0}}

@media(max-width:600px){{
  .grid{{grid-template-columns:1fr;padding:0 16px 60px}}
  .meta-row{{grid-template-columns:1fr 1fr}}
  .card-top{{flex-direction:column;align-items:flex-start}}
  .hero{{padding:36px 16px 0}}
}}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-eyebrow">Human Design · Group Reading · {len(all_data)} Charts</div>
  <h1>Human Design<br>Bodygraph Analysis</h1>
  <p class="hero-sub">Energy type, decision-making strategy and authority for every chart in the pool — calculated from birth data via Swiss Ephemeris (I Ching wheel, tropical).</p>
  <p class="hero-note">Created 1987 by Ra Uru Hu · Blends I Ching, Kabbalah, Hindu Chakra System &amp; Quantum Physics</p>
  <div class="stat-row">
{stat_pills}  </div>
</div>

<div class="tabs">
{tab_html}</div>

<div class="grid" id="grid">
{all_cards}
</div>

<div class="footer">Generated {today_str} · Swiss Ephemeris · Tropical · Human Design I Ching Wheel</div>

<script>
function filterType(t) {{
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('tab-active'));
  event.target.closest('.tab').classList.add('tab-active');
  document.querySelectorAll('.card').forEach(c => {{
    if (t === 'All' || c.dataset.type === t) c.classList.remove('hidden');
    else c.classList.add('hidden');
  }});
}}
</script>
</body>
</html>"""

os.makedirs("docs", exist_ok=True)
with open("docs/human_design.html", "w") as f:
    f.write(html)

print(f"\n✓ docs/human_design.html written ({len(html):,} bytes)")
print(f"  Type distribution: {dict(type_counts)}")
