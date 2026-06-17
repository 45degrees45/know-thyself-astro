"""
AstroService — wraps astro_engine/ calculation modules.

Provides calculate() and build_summary() for chart generation and summarisation.
"""
from datetime import datetime, timezone

from astro_engine.geo import geocode
from astro_engine.calc import calculate_chart
from astro_engine.dasha import current_period
from astro_engine.yoga import find_yogas

# Jyotish nakshatra → spirit animal mapping
MOON_ANIMAL = {
    "Ashwini":            ("Horse",     "🐎"),
    "Bharani":            ("Elephant",  "🐘"),
    "Krittika":           ("Goat",      "🐐"),
    "Rohini":             ("Serpent",   "🐍"),
    "Mrigashira":         ("Serpent",   "🐍"),
    "Ardra":              ("Dog",       "🐕"),
    "Punarvasu":          ("Cat",       "🐈"),
    "Pushya":             ("Goat",      "🐐"),
    "Ashlesha":           ("Cat",       "🐈"),
    "Magha":              ("Rat",       "🐀"),
    "Purva Phalguni":     ("Rat",       "🐀"),
    "Uttara Phalguni":    ("Cow",       "🐄"),
    "Hasta":              ("Buffalo",   "🦬"),
    "Chitra":             ("Tiger",     "🐅"),
    "Swati":              ("Buffalo",   "🦬"),
    "Vishakha":           ("Tiger",     "🐅"),
    "Anuradha":           ("Deer",      "🦌"),
    "Jyeshtha":           ("Deer",      "🦌"),
    "Mula":               ("Dog",       "🐕"),
    "Purva Ashadha":      ("Monkey",    "🐒"),
    "Uttara Ashadha":     ("Mongoose",  "🦡"),
    "Shravana":           ("Monkey",    "🐒"),
    "Dhanishtha":         ("Lion",      "🦁"),
    "Shatabhisha":        ("Horse",     "🐎"),
    "Purva Bhadrapada":   ("Lion",      "🦁"),
    "Uttara Bhadrapada":  ("Cow",       "🐄"),
    "Revati":             ("Elephant",  "🐘"),
}


class AstroService:
    def calculate(self, birth_date: str, birth_time: str, birth_place: str) -> dict:
        """
        Calculate a full Vedic birth chart.

        Returns a dict with lagna, planets, yogas, dasha, and spirit animal.
        """
        try:
            geo = geocode(birth_place)
        except ValueError as exc:
            raise ValueError(f"Unknown birth place: {birth_place!r}") from exc
        except Exception as exc:
            raise RuntimeError(f"Geocoding service unavailable: {exc}") from exc
        chart = calculate_chart(
            birth_date, birth_time,
            geo["lat"], geo["lon"], geo["timezone"],
        )

        yogas = find_yogas(chart)

        # current_period needs (moon_lon: float, birth_dt: naive-UTC datetime)
        moon_lon = chart["planets"]["Moon"]["longitude"]
        birth_dt = datetime.fromisoformat(chart["birth_utc"]).replace(tzinfo=None)
        dasha = current_period(moon_lon, birth_dt)

        # dasha keys: {"mahadasha": {"planet": ...}, "bhukti": {"planet": ...}, "antara": {"planet": ...}}
        maha = dasha.get("mahadasha", {}).get("planet", "")
        bhuk = dasha.get("bhukti", {}).get("planet", "")
        anta = dasha.get("antara", {}).get("planet", "")
        dasha_str = "/".join(p for p in [maha, bhuk, anta] if p)

        moon_nakshatra = chart["planets"]["Moon"]["nakshatra"]
        animal_name, animal_emoji = MOON_ANIMAL.get(moon_nakshatra, ("Eagle", "🦅"))

        return {
            "lagna":          chart["ascendant"]["sign"],
            "lagna_deg":      round(chart["ascendant"]["degrees"], 2),
            "planets":        chart["planets"],
            "moon_nakshatra": moon_nakshatra,
            "yogas":          [y["name"] for y in yogas],
            "yoga_details":   yogas,
            "current_dasha":  dasha_str,
            "animal":         animal_name,
            "animal_emoji":   animal_emoji,
            "raw_chart":      chart,
            "lat":            geo["lat"],
            "lon":            geo["lon"],
            "tz":             geo["timezone"],
        }

    def build_summary(self, chart_json: dict) -> dict:
        """
        Distil a full calculate() result into a lightweight summary dict.
        """
        return {
            "lagna":        chart_json["lagna"],
            "lagna_deg":    chart_json["lagna_deg"],
            "current_dasha": chart_json["current_dasha"],
            "yogas":        chart_json["yogas"][:3],
            "animal":       chart_json["animal"],
            "animal_emoji": chart_json["animal_emoji"],
        }

    def generate_profile_html(self, chart_json: dict, name: str) -> str:
        """Generate a full natal profile HTML from chart data (no external LLM)."""
        from datetime import date as _date
        lagna      = chart_json.get("lagna", "Unknown")
        lagna_deg  = chart_json.get("lagna_deg", 0.0)
        dasha      = chart_json.get("current_dasha", "")
        yogas      = chart_json.get("yogas") or []
        yoga_det   = chart_json.get("yoga_details") or []
        animal     = chart_json.get("animal", "Eagle")
        animal_em  = chart_json.get("animal_emoji", "🦅")
        moon_nak   = chart_json.get("moon_nakshatra", "")
        planets    = chart_json.get("planets") or {}

        SIGN_SYM = {
            "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋","Leo":"♌","Virgo":"♍",
            "Libra":"♎","Scorpio":"♏","Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓",
        }
        lagna_sym = SIGN_SYM.get(lagna, "✦")

        planet_rows = ""
        for pname, p in planets.items():
            retro = " ℞" if p.get("retrograde") else ""
            sym   = SIGN_SYM.get(p.get("sign", ""), "")
            planet_rows += (
                f"<tr>"
                f"<td style='color:#e8c96a;font-weight:600'>{pname}</td>"
                f"<td>{sym} {p.get('sign','')}{retro}</td>"
                f"<td style='color:rgba(240,232,216,0.6)'>{p.get('degrees',0):.1f}°</td>"
                f"<td>H{p.get('house','')}</td>"
                f"<td style='color:rgba(240,232,216,0.6)'>{p.get('nakshatra','')} p{p.get('pada','')}</td>"
                f"</tr>"
            )

        yoga_rows = ""
        for y in yoga_det:
            yoga_rows += (
                f"<div style='padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05)'>"
                f"<div style='color:#e8c96a;font-weight:600;font-size:.85rem'>{y.get('name','')}</div>"
                f"<div style='color:rgba(240,232,216,0.7);font-size:.82rem;margin-top:4px;line-height:1.5'>"
                f"{y.get('description','')}</div></div>"
            )
        if not yoga_rows:
            for y in yogas:
                yoga_rows += f"<div style='padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);color:rgba(240,232,216,0.85);font-size:.85rem'>{y}</div>"

        today = _date.today().strftime("%B %d, %Y")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="robots" content="noindex,nofollow">
<title>{name} — Vedic Natal Profile</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0b0b18;--surface:rgba(255,255,255,0.035);--border:rgba(196,158,64,0.18);
--gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.55);
--plum:#7c5cbf;--rose:#c4607a;--sage:#5a8f72;--shadow:0 20px 60px rgba(0,0,0,0.45);--r:22px}}
body{{font-family:'DM Sans',system-ui,sans-serif;background-color:var(--bg);
background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(124,92,191,0.18),transparent),
radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.12),transparent);
background-attachment:fixed;color:var(--cream);min-height:100vh;padding:40px 20px 80px}}
.wrap{{max-width:860px;margin:0 auto;display:flex;flex-direction:column;gap:24px}}
.hero{{border-radius:28px;padding:48px 44px 38px;position:relative;overflow:hidden;
background:linear-gradient(140deg,rgba(28,18,56,0.98) 0%,rgba(44,24,72,0.96) 45%,rgba(80,38,58,0.92) 100%);
border:1px solid rgba(196,158,64,0.22);box-shadow:var(--shadow)}}
.hero-symbol{{position:absolute;right:36px;top:24px;font-size:180px;color:rgba(196,158,64,0.07);line-height:1;pointer-events:none}}
.eyebrow{{font-size:.7rem;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin-bottom:12px}}
.hero h1{{font-family:'Cormorant Garamond',serif;font-size:clamp(2.5rem,6vw,5rem);font-weight:300;color:#fff8f0;margin-bottom:6px}}
.lagna-line{{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-style:italic;color:rgba(196,158,64,.85);margin-bottom:24px}}
.stat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:20px}}
.stat{{background:rgba(255,255,255,.06);border:1px solid rgba(196,158,64,.14);border-radius:16px;padding:16px 18px}}
.stat-label{{font-size:.65rem;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);margin-bottom:4px}}
.stat-value{{font-size:.95rem;color:#fff8f0}}
.panel{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:28px;box-shadow:var(--shadow)}}
.panel-header{{display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(196,158,64,.12);margin-bottom:20px}}
.panel-icon{{width:36px;height:36px;border-radius:50%;background:rgba(196,158,64,.1);display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:var(--gold)}}
.panel h2{{font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:400;color:var(--cream)}}
.dasha-panel{{background:rgba(124,92,191,.06);border-color:rgba(124,92,191,.22)}}
.dasha-panel .panel-icon{{background:rgba(124,92,191,.14);color:#b49edf}}
.dasha-panel .panel h2{{color:#d0c4f0}}
.animal-panel{{background:linear-gradient(135deg,rgba(28,18,56,.98),rgba(60,30,80,.96));border-color:rgba(196,158,64,.22);text-align:center;padding:48px 40px}}
.planet-table{{width:100%;border-collapse:collapse;font-size:.86rem}}
.planet-table th{{text-align:left;padding:10px 14px;background:rgba(196,158,64,.1);color:var(--gold);
font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,.2)}}
.planet-table td{{padding:10px 14px;color:rgba(240,232,216,.85);border-bottom:1px solid rgba(255,255,255,.05);vertical-align:middle}}
.planet-table tr:last-child td{{border-bottom:none}}
.planet-table tr:hover td{{background:rgba(255,255,255,.02)}}
.footer{{text-align:center;padding:20px 0;font-size:.72rem;color:rgba(240,232,216,.3);letter-spacing:.08em;border-top:1px solid var(--border);margin-top:16px}}
@media(max-width:768px){{.stat-grid{{grid-template-columns:1fr 1fr}}.hero{{padding:32px 24px 28px}}}}
</style>
</head>
<body>
<div class="wrap">
<div class="hero">
  <div class="hero-symbol">{lagna_sym}</div>
  <div class="eyebrow">Vedic Natal Profile · Lahiri Ayanamsha</div>
  <h1>{name}</h1>
  <div class="lagna-line">{lagna} Lagna {lagna_deg:.1f}°</div>
  <div class="stat-grid">
    <div class="stat"><div class="stat-label">Lagna</div><div class="stat-value">{lagna}</div></div>
    <div class="stat"><div class="stat-label">Current Dasha</div><div class="stat-value">{dasha}</div></div>
    <div class="stat"><div class="stat-label">Moon Nakshatra</div><div class="stat-value">{moon_nak}</div></div>
    <div class="stat"><div class="stat-label">Yogas</div><div class="stat-value">{len(yogas)} found</div></div>
  </div>
</div>
<div class="panel">
  <div class="panel-header">
    <div class="panel-icon">☿</div>
    <h2>Planetary Positions</h2>
  </div>
  <table class="planet-table">
    <thead><tr><th>Planet</th><th>Sign</th><th>Degree</th><th>House</th><th>Nakshatra</th></tr></thead>
    <tbody>{planet_rows}</tbody>
  </table>
</div>
<div class="panel">
  <div class="panel-header">
    <div class="panel-icon">✦</div>
    <h2>Yogas ({len(yogas)} found)</h2>
  </div>
  {yoga_rows or "<div style='color:var(--muted);font-size:.9rem'>No yogas detected</div>"}
</div>
<div class="panel dasha-panel">
  <div class="panel-header">
    <div class="panel-icon">◉</div>
    <h2>Current Dasha Period</h2>
  </div>
  <div style="font-family:Cormorant Garamond,serif;font-size:2rem;font-weight:300;color:#d0c4f0;margin-bottom:8px">{dasha}</div>
  <div style="font-size:.85rem;color:rgba(240,232,216,.65);line-height:1.6">
    The Vimshottari Dasha system maps planetary periods onto your life timeline based on Moon's nakshatra at birth.
    Each period activates that planet's significations in your chart.
  </div>
</div>
<div class="panel animal-panel">
  <div style="font-size:96px;margin-bottom:16px">{animal_em}</div>
  <div class="eyebrow" style="display:block">Spirit Animal · Moon in {moon_nak}</div>
  <div style="font-family:Cormorant Garamond,serif;font-size:2.2rem;font-weight:300;color:#fff8f0;margin:12px 0 8px">The {animal}</div>
  <div style="font-size:.85rem;color:rgba(240,232,216,.65);max-width:500px;margin:0 auto;line-height:1.7">
    In Jyotish, the Moon nakshatra carries the soul's instinctive nature. The {animal} reflects the
    energy of {moon_nak} nakshatra — your emotional intelligence, intuitive style, and how you navigate the world.
  </div>
</div>
<div class="footer">Generated {today} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris</div>
</div>
</body>
</html>"""
