# Trusted Friends Tier + Full Profile Reading — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a full natal reading HTML to every chart (free), and give selected trusted friends permanent free chat access (own chart only, compatibility allowed).

**Architecture:** Extend the existing `AccessCode` table with `type` + `note` columns to support permanent trusted codes. Add `profile_html` column to `Chart` — generated async after chart creation via a Python HTML template (no external LLM). The frontend profile page gains a "View Full Reading" button and skips the payment wall for trusted charts.

**Tech Stack:** FastAPI, SQLAlchemy (async), Alembic, PostgreSQL, Next.js 16, pytest

---

## File Map

### Backend — P046 repo (`/home/jo/claude_projects/P046_202604_KnowThyselfAstro`)

| File | Change |
|---|---|
| `api/models.py` | Add `profile_html` to Chart; add `type`, `note` to AccessCode; add `TrustedEmailWhitelist` model |
| `api/migrations/versions/<hash>_trusted_tier.py` | New Alembic migration (4 schema changes) |
| `api/config.py` | Add `admin_secret` setting |
| `api/schemas.py` | Add `profile_html_ready`, `trusted` to `ChartSummary`; new admin request/response schemas |
| `api/services/astro_service.py` | Add `generate_profile_html(chart_json, name) -> str` |
| `api/routers/charts.py` | POST: whitelist check + async HTML gen; GET: return `trusted`/`profile_html_ready`; new GET `/{id}/reading` |
| `api/routers/demo.py` | Extend `redeem` to handle trusted codes (no expiry) |
| `api/routers/admin.py` | Add 3 endpoints: generate trusted codes, add to whitelist, list trusted users |
| `api/routers/chat.py` | Check trusted code access; inject compatibility system prompt |
| `api/tests/test_trusted_tier.py` | New test file: 8 tests covering all new behaviour |

### Frontend — P081 repo (`/home/jo/claude_projects/P081_202605_AstrowiseSite`)

| File | Change |
|---|---|
| `lib/types.ts` | Add `trusted: boolean`, `profile_html_ready: boolean` to `ChartSummary` |
| `lib/api.ts` | Add `getReadingUrl(chartId)` helper |
| `app/profile/[chartId]/page.tsx` | "View Full Reading" button; skip payment if `trusted` |

---

## Task 1: DB Models + Migration

**Files:**
- Modify: `api/models.py`
- Create: `api/migrations/versions/<new>_trusted_tier.py`

- [ ] **Step 1: Update models.py**

Replace the `Chart` and `AccessCode` classes and add `TrustedEmailWhitelist`:

```python
# In api/models.py — Chart class, add after anon_slug:
profile_html: Mapped[str | None] = mapped_column(Text, nullable=True)

# In api/models.py — AccessCode class, add after created_at:
type: Mapped[str] = mapped_column(String, default="demo")
note: Mapped[str | None] = mapped_column(String, nullable=True)

# New model at the bottom of api/models.py:
class TrustedEmailWhitelist(Base):
    __tablename__ = "trusted_email_whitelist"
    email: Mapped[str] = mapped_column(String, primary_key=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 2: Generate the migration**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/alembic revision --autogenerate -m "trusted_tier"
```

Expected: creates `api/migrations/versions/<hash>_trusted_tier.py`

- [ ] **Step 3: Verify and fix migration if needed**

Open the generated file. Confirm it contains:
- `op.add_column('charts', sa.Column('profile_html', sa.Text(), nullable=True))`
- `op.add_column('access_codes', sa.Column('type', sa.String(), nullable=False, server_default='demo'))`
- `op.add_column('access_codes', sa.Column('note', sa.String(), nullable=True))`
- `op.create_table('trusted_email_whitelist', ...)`

If autogenerate missed any, add them manually.

- [ ] **Step 4: Run migration against test DB**

```bash
DATABASE_URL=sqlite+aiosqlite:///test_migrate.db .venv/bin/alembic upgrade head
```

Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add api/models.py api/migrations/versions/
git commit -m "feat: add profile_html, trusted code columns, whitelist table"
```

---

## Task 2: Config + Schemas

**Files:**
- Modify: `api/config.py`
- Modify: `api/schemas.py`

- [ ] **Step 1: Add admin_secret to config**

```python
# In api/config.py — add to Settings class:
admin_secret: str = "admin-dev-secret"  # override in prod via ADMIN_SECRET env var
```

- [ ] **Step 2: Update ChartSummary and add admin schemas**

```python
# In api/schemas.py — update ChartSummary:
class ChartSummary(BaseModel):
    chart_id: str
    lagna: str
    lagna_deg: float
    current_dasha: str
    yogas: list[str]
    animal: str
    animal_emoji: str
    paid: bool = False
    trusted: bool = False
    profile_html_ready: bool = False

# Add new schemas at the bottom of api/schemas.py:
class TrustedCodeGenerateRequest(BaseModel):
    secret: str
    count: int = Field(default=1, ge=1, le=20)
    note: str | None = None

class WhitelistAddRequest(BaseModel):
    secret: str
    email: EmailStr
    note: str | None = None
```

- [ ] **Step 3: Commit**

```bash
git add api/config.py api/schemas.py
git commit -m "feat: add admin_secret config and trusted/profile_html_ready schema fields"
```

---

## Task 3: Profile HTML Generator

**Files:**
- Modify: `api/services/astro_service.py`
- Test: `api/tests/test_trusted_tier.py` (partial — generator tests)

- [ ] **Step 1: Write the failing test**

Create `api/tests/test_trusted_tier.py`:

```python
"""Tests for trusted tier and profile HTML generation."""
import pytest
from api.services.astro_service import AstroService

SAMPLE_CHART_JSON = {
    "lagna": "Pisces",
    "lagna_deg": 2.4,
    "planets": {
        "Sun":     {"sign": "Gemini",      "degrees": 15.2, "house": 4, "nakshatra": "Ardra",          "pada": 2, "retrograde": False},
        "Moon":    {"sign": "Capricorn",   "degrees": 8.7,  "house": 11,"nakshatra": "Shravana",        "pada": 1, "retrograde": False},
        "Mars":    {"sign": "Scorpio",     "degrees": 22.1, "house": 9, "nakshatra": "Jyeshtha",        "pada": 3, "retrograde": False},
        "Mercury": {"sign": "Gemini",      "degrees": 5.3,  "house": 4, "nakshatra": "Mrigashira",      "pada": 4, "retrograde": True},
        "Jupiter": {"sign": "Libra",       "degrees": 11.0, "house": 8, "nakshatra": "Swati",           "pada": 2, "retrograde": False},
        "Venus":   {"sign": "Taurus",      "degrees": 29.8, "house": 3, "nakshatra": "Krittika",        "pada": 1, "retrograde": False},
        "Saturn":  {"sign": "Capricorn",   "degrees": 3.5,  "house": 11,"nakshatra": "Uttara Ashadha",  "pada": 2, "retrograde": False},
        "Rahu":    {"sign": "Virgo",       "degrees": 14.2, "house": 7, "nakshatra": "Hasta",           "pada": 3, "retrograde": True},
        "Ketu":    {"sign": "Pisces",      "degrees": 14.2, "house": 1, "nakshatra": "Uttara Bhadrapada","pada": 4,"retrograde": True},
    },
    "moon_nakshatra": "Shravana",
    "yogas": ["Adhi Yoga", "NBRY", "Guru-Chandala"],
    "yoga_details": [
        {"name": "Adhi Yoga", "description": "Mercury, Venus, Jupiter in 6th/7th/8th from Moon"},
        {"name": "NBRY",      "description": "No benefics in kendras"},
        {"name": "Guru-Chandala", "description": "Jupiter-Rahu conjunction"},
    ],
    "current_dasha": "Mercury/Ketu/Mercury",
    "animal": "Monkey",
    "animal_emoji": "🐒",
    "lat": 8.5241,
    "lon": 76.9366,
    "tz": "Asia/Kolkata",
}


def test_generate_profile_html_returns_string():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert isinstance(html, str)
    assert len(html) > 1000


def test_generate_profile_html_contains_lagna():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Pisces" in html


def test_generate_profile_html_contains_name():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Jinx" in html


def test_generate_profile_html_contains_dasha():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Mercury" in html


def test_generate_profile_html_contains_animal():
    svc = AstroService()
    html = svc.generate_profile_html(SAMPLE_CHART_JSON, "Jinx")
    assert "Monkey" in html or "🐒" in html
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
.venv/bin/pytest api/tests/test_trusted_tier.py::test_generate_profile_html_returns_string -v
```

Expected: `AttributeError: 'AstroService' object has no attribute 'generate_profile_html'`

- [ ] **Step 3: Implement generate_profile_html in astro_service.py**

Add this method to the `AstroService` class (after `build_summary`):

```python
def generate_profile_html(self, chart_json: dict, name: str) -> str:
    """Generate a full natal profile HTML from chart data (no external LLM)."""
    lagna = chart_json.get("lagna", "Unknown")
    lagna_deg = chart_json.get("lagna_deg", 0.0)
    dasha = chart_json.get("current_dasha", "")
    yogas = chart_json.get("yogas") or []
    yoga_details = chart_json.get("yoga_details") or []
    animal = chart_json.get("animal", "Eagle")
    animal_emoji = chart_json.get("animal_emoji", "🦅")
    moon_nak = chart_json.get("moon_nakshatra", "")
    planets = chart_json.get("planets") or {}

    SIGN_SYMBOLS = {
        "Aries":"♈","Taurus":"♉","Gemini":"♊","Cancer":"♋","Leo":"♌","Virgo":"♍",
        "Libra":"♎","Scorpio":"♏","Sagittarius":"♐","Capricorn":"♑","Aquarius":"♒","Pisces":"♓",
    }
    lagna_sym = SIGN_SYMBOLS.get(lagna, "✦")

    # Planet rows
    planet_rows = ""
    for pname, pdata in planets.items():
        retro = " ℞" if pdata.get("retrograde") else ""
        sym = SIGN_SYMBOLS.get(pdata.get("sign", ""), "")
        planet_rows += f"""
        <tr>
          <td style="color:#e8c96a;font-weight:600">{pname}</td>
          <td>{sym} {pdata.get('sign','')}{retro}</td>
          <td style="color:rgba(240,232,216,0.6)">{pdata.get('degrees',0):.1f}°</td>
          <td>H{pdata.get('house','')}</td>
          <td style="color:rgba(240,232,216,0.6)">{pdata.get('nakshatra','')} p{pdata.get('pada','')}</td>
        </tr>"""

    # Yoga rows
    yoga_rows = ""
    for y in yoga_details:
        yoga_rows += f"""
        <div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
          <div style="color:#e8c96a;font-weight:600;font-size:.85rem">{y.get('name','')}</div>
          <div style="color:rgba(240,232,216,0.7);font-size:.82rem;margin-top:4px;line-height:1.5">{y.get('description','')}</div>
        </div>"""
    if not yoga_rows and yogas:
        for y in yogas:
            yoga_rows += f'<div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);color:rgba(240,232,216,0.85);font-size:.85rem">{y}</div>'

    from datetime import date
    today = date.today().strftime("%B %d, %Y")

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
:root{{
  --bg:#0b0b18;--surface:rgba(255,255,255,0.035);--border:rgba(196,158,64,0.18);
  --gold:#c49e40;--gold2:#e8c96a;--cream:#f0e8d8;--muted:rgba(240,232,216,0.55);
  --plum:#7c5cbf;--rose:#c4607a;--sage:#5a8f72;--shadow:0 20px 60px rgba(0,0,0,0.45);--r:22px;
}}
body{{font-family:'DM Sans',system-ui,sans-serif;background-color:var(--bg);
  background-image:radial-gradient(ellipse 80% 50% at 20% -10%,rgba(124,92,191,0.18),transparent),
  radial-gradient(ellipse 60% 40% at 80% 110%,rgba(196,158,64,0.12),transparent);
  background-attachment:fixed;color:var(--cream);min-height:100vh;padding:40px 20px 80px}}
.wrap{{max-width:860px;margin:0 auto;display:flex;flex-direction:column;gap:24px}}
/* Hero */
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
/* Panel */
.panel{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:28px;box-shadow:var(--shadow)}}
.panel-header{{display:flex;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid rgba(196,158,64,.12);margin-bottom:20px}}
.panel-icon{{width:36px;height:36px;border-radius:50%;background:rgba(196,158,64,.1);display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:var(--gold)}}
.panel h2{{font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:400;color:var(--cream)}}
/* Dasha panel */
.dasha-panel{{background:rgba(124,92,191,.06);border-color:rgba(124,92,191,.22)}}
.dasha-panel .panel-icon{{background:rgba(124,92,191,.14);color:#b49edf}}
.dasha-panel .panel h2{{color:#d0c4f0}}
/* Animal panel */
.animal-panel{{background:linear-gradient(135deg,rgba(28,18,56,.98),rgba(60,30,80,.96));border-color:rgba(196,158,64,.22);text-align:center;padding:48px 40px}}
/* Table */
.planet-table{{width:100%;border-collapse:collapse;font-size:.86rem}}
.planet-table th{{text-align:left;padding:10px 14px;background:rgba(196,158,64,.1);color:var(--gold);
  font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;border-bottom:1px solid rgba(196,158,64,.2)}}
.planet-table td{{padding:10px 14px;color:rgba(240,232,216,.85);border-bottom:1px solid rgba(255,255,255,.05);vertical-align:middle}}
.planet-table tr:last-child td{{border-bottom:none}}
.planet-table tr:hover td{{background:rgba(255,255,255,.02)}}
/* Footer */
.footer{{text-align:center;padding:20px 0;font-size:.72rem;color:rgba(240,232,216,.3);letter-spacing:.08em;border-top:1px solid var(--border);margin-top:16px}}
@media(max-width:768px){{.stat-grid{{grid-template-columns:1fr 1fr}}.hero{{padding:32px 24px 28px}}}}
</style>
</head>
<body>
<div class="wrap">

<!-- Hero -->
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

<!-- Planets -->
<div class="panel">
  <div class="panel-header">
    <div class="panel-icon">☿</div>
    <h2>Planetary Positions</h2>
  </div>
  <table class="planet-table">
    <thead>
      <tr><th>Planet</th><th>Sign</th><th>Degree</th><th>House</th><th>Nakshatra</th></tr>
    </thead>
    <tbody>{planet_rows}</tbody>
  </table>
</div>

<!-- Yogas -->
<div class="panel">
  <div class="panel-header">
    <div class="panel-icon">✦</div>
    <h2>Yogas ({len(yogas)} found)</h2>
  </div>
  {yoga_rows or '<div style="color:var(--muted);font-size:.9rem">No yogas detected</div>'}
</div>

<!-- Dasha -->
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

<!-- Spirit Animal -->
<div class="panel animal-panel">
  <div style="font-size:96px;margin-bottom:16px">{animal_emoji}</div>
  <div class="eyebrow" style="justify-content:center;display:block">Spirit Animal · Moon in {moon_nak}</div>
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
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py -k "generate_profile_html" -v
```

Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add api/services/astro_service.py api/tests/test_trusted_tier.py
git commit -m "feat: add generate_profile_html to AstroService (data template, no LLM)"
```

---

## Task 4: Charts Router — POST, GET, and /reading

**Files:**
- Modify: `api/routers/charts.py`
- Test: `api/tests/test_trusted_tier.py` (add tests)

- [ ] **Step 1: Write failing tests**

Append to `api/tests/test_trusted_tier.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app
from api.database import Base, AsyncSessionLocal, engine


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_get_chart_includes_trusted_false():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/chart", json={
            "name": "Test", "birth_date": "1990-01-01", "birth_time": "12:00",
            "birth_place": "Mumbai, India", "email": "test@example.com"
        })
        chart_id = r.json()["chart_id"]
        r2 = await client.get(f"/api/chart/{chart_id}")
        assert r2.status_code == 200
        assert r2.json()["trusted"] == False


@pytest.mark.asyncio
async def test_reading_endpoint_returns_404_before_html_ready():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/chart", json={
            "name": "Test", "birth_date": "1990-01-01", "birth_time": "12:00",
            "birth_place": "Mumbai, India", "email": "test2@example.com"
        })
        chart_id = r.json()["chart_id"]
        r2 = await client.get(f"/api/chart/{chart_id}/reading")
        # profile_html is None immediately after creation (generated async)
        assert r2.status_code == 404
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py -k "test_get_chart_includes_trusted" -v
```

Expected: FAIL (`KeyError: 'trusted'` or similar)

- [ ] **Step 3: Rewrite charts.py**

Replace `api/routers/charts.py` entirely:

```python
"""
Charts router — POST /api/chart, GET /api/chart/{id}, GET /api/chart/{id}/reading.
"""
import asyncio
import logging

import secrets as _secrets

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload

from api.database import get_db, AsyncSessionLocal
from api.models import User, Chart, AccessCode, TrustedEmailWhitelist
from api.schemas import ChartRequest, ChartSummary
from api.services.astro_service import AstroService

router = APIRouter(tags=["charts"])
_astro = AstroService()


async def _save_profile_html(chart_id: str, chart_json: dict, name: str) -> None:
    """Background task: generate profile HTML and persist it."""
    try:
        html = await asyncio.to_thread(_astro.generate_profile_html, chart_json, name)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Chart).where(Chart.id == chart_id))
            chart = result.scalar_one_or_none()
            if chart:
                chart.profile_html = html
                await db.commit()
    except Exception:
        logging.exception("Profile HTML generation failed for chart_id=%s", chart_id)


@router.post("/chart", response_model=ChartSummary, status_code=201)
async def create_chart(
    req: ChartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Upsert user by email
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=req.email, name=req.name)
        db.add(user)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(User).where(User.email == req.email))
            user = result.scalar_one()
    else:
        user.name = req.name

    # Calculate chart
    try:
        chart_json = await asyncio.to_thread(
            _astro.calculate, req.birth_date, req.birth_time, req.birth_place
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    chart = Chart(
        user_id=user.id,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        birth_place=req.birth_place,
        lat=chart_json["lat"],
        lon=chart_json["lon"],
        tz=chart_json["tz"],
        chart_json=chart_json,
    )
    db.add(chart)

    # Auto-grant trusted if email is whitelisted
    wl_result = await db.execute(
        select(TrustedEmailWhitelist).where(TrustedEmailWhitelist.email == req.email)
    )
    trusted = False
    if wl_result.scalar_one_or_none():
        trusted = True

    await db.commit()
    await db.refresh(chart)

    # Auto-create trusted AccessCode for whitelisted users
    if trusted:
        code = "TRUST-" + _secrets.token_urlsafe(6).upper()
        db.add(AccessCode(code=code, chart_id=chart.id, type="trusted", expires_at=None))
        await db.commit()

    # Generate profile HTML in background
    background_tasks.add_task(_save_profile_html, chart.id, chart_json, req.name)

    summary = _astro.build_summary(chart_json)
    return {
        "chart_id": chart.id,
        **summary,
        "paid": user.paid,
        "trusted": trusted,
        "profile_html_ready": False,
    }


@router.get("/chart/{chart_id}/reading", response_class=HTMLResponse)
async def get_reading(chart_id: str, db: AsyncSession = Depends(get_db)):
    """Return the generated full natal profile HTML."""
    result = await db.execute(select(Chart).where(Chart.id == chart_id))
    chart = result.scalar_one_or_none()
    if not chart or not chart.profile_html:
        raise HTTPException(status_code=404, detail="Reading not ready yet")
    return HTMLResponse(content=chart.profile_html)


@router.get("/chart/{chart_id}", response_model=ChartSummary)
async def get_chart(chart_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chart)
        .where(Chart.id == chart_id)
        .options(selectinload(Chart.user))
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    # Check if a trusted code exists for this chart
    trusted_result = await db.execute(
        select(AccessCode).where(
            AccessCode.chart_id == chart_id,
            AccessCode.type == "trusted",
            AccessCode.expires_at.is_(None),
        )
    )
    trusted = trusted_result.scalar_one_or_none() is not None

    summary = _astro.build_summary(chart.chart_json)
    return {
        "chart_id": chart.id,
        **summary,
        "paid": chart.user.paid,
        "trusted": trusted,
        "profile_html_ready": chart.profile_html is not None,
    }
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py -k "test_get_chart or test_reading" -v
```

Expected: 2 tests PASS

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
.venv/bin/pytest api/tests/ -v --tb=short
```

Expected: all previously passing tests still pass

- [ ] **Step 6: Commit**

```bash
git add api/routers/charts.py
git commit -m "feat: charts router — trusted field, profile HTML generation, /reading endpoint"
```

---

## Task 5: Demo Router + Admin Router

**Files:**
- Modify: `api/routers/demo.py`
- Modify: `api/routers/admin.py`
- Test: `api/tests/test_trusted_tier.py` (add tests)

- [ ] **Step 1: Write failing tests**

Append to `api/tests/test_trusted_tier.py`:

```python
@pytest.mark.asyncio
async def test_admin_generate_trusted_codes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "admin-dev-secret", "count": 2, "note": "for Ruhi"
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["codes"]) == 2
        assert all(c["code"].startswith("TRUST-") for c in data["codes"])


@pytest.mark.asyncio
async def test_admin_generate_trusted_codes_wrong_secret():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "wrong", "count": 1
        })
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_redeem_trusted_code_grants_permanent_access():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate a trusted code
        gen = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "admin-dev-secret", "count": 1
        })
        code = gen.json()["codes"][0]["code"]

        # Create a chart
        chart_r = await client.post("/api/chart", json={
            "name": "Ruhi", "birth_date": "2002-03-03", "birth_time": "02:00",
            "birth_place": "Alleppey, Kerala", "email": "ruhi@test.com"
        })
        chart_id = chart_r.json()["chart_id"]

        # Redeem the trusted code
        redeem = await client.post("/api/demo/redeem", json={"code": code, "chart_id": chart_id})
        assert redeem.status_code == 200
        assert redeem.json()["trusted"] == True
        assert redeem.json().get("expires_at") is None

        # GET chart should now return trusted=True
        get_r = await client.get(f"/api/chart/{chart_id}")
        assert get_r.json()["trusted"] == True
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py -k "admin" -v
```

Expected: 404 or FAIL

- [ ] **Step 3: Update demo.py to handle trusted codes**

In `api/routers/demo.py`, replace the `redeem_code` function:

```python
@router.post("/demo/redeem")
async def redeem_code(req: DemoRedeemRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessCode).where(AccessCode.code == req.code))
    access = result.scalar_one_or_none()

    if not access:
        raise HTTPException(status_code=404, detail="Code not found")
    if access.chart_id and access.chart_id != req.chart_id:
        raise HTTPException(status_code=409, detail="Code already used for a different chart")

    chart_result = await db.execute(select(Chart).where(Chart.id == req.chart_id))
    if not chart_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chart not found")

    now = datetime.now(timezone.utc)
    access.chart_id = req.chart_id

    if access.type == "trusted":
        # Permanent — no expiry
        access.expires_at = None
        await db.commit()
        return {"ok": True, "trusted": True, "expires_at": None}
    else:
        # Demo — extend 10-minute window
        access.expires_at = now + timedelta(minutes=WINDOW_MINUTES)
        await db.commit()
        return {
            "ok": True,
            "trusted": False,
            "expires_at": access.expires_at.isoformat(),
            "window_minutes": WINDOW_MINUTES,
        }
```

- [ ] **Step 4: Add trusted endpoints to admin.py**

Add these imports at the top of `api/routers/admin.py`:

```python
import secrets as _secrets
from api.models import TrustedEmailWhitelist
from api.schemas import TrustedCodeGenerateRequest, WhitelistAddRequest
```

Add these endpoints at the bottom of `api/routers/admin.py`:

```python
@router.post("/admin/trusted-codes/generate")
async def generate_trusted_codes(req: TrustedCodeGenerateRequest, db: AsyncSession = Depends(get_db)):
    if req.secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    codes = []
    for _ in range(req.count):
        code = "TRUST-" + _secrets.token_urlsafe(6).upper()
        db.add(AccessCode(code=code, type="trusted", note=req.note))
        codes.append({"code": code})
    await db.commit()
    return {"codes": codes}


@router.post("/admin/whitelist/add")
async def add_to_whitelist(req: WhitelistAddRequest, db: AsyncSession = Depends(get_db)):
    if req.secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    existing = await db.execute(
        select(TrustedEmailWhitelist).where(TrustedEmailWhitelist.email == req.email)
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "message": "Already whitelisted"}
    db.add(TrustedEmailWhitelist(email=req.email, note=req.note))
    await db.commit()
    return {"ok": True}


@router.get("/admin/trusted-users")
async def list_trusted_users(secret: str, db: AsyncSession = Depends(get_db)):
    if secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(
        select(AccessCode, Chart, User)
        .join(Chart, AccessCode.chart_id == Chart.id, isouter=True)
        .join(User, Chart.user_id == User.id, isouter=True)
        .where(AccessCode.type == "trusted")
        .order_by(AccessCode.created_at.desc())
    )
    rows = []
    for code, chart, user in result.all():
        rows.append({
            "code": code.code,
            "note": code.note,
            "email": user.email if user else None,
            "name": user.name if user else None,
            "chart_id": code.chart_id,
            "redeemed": code.chart_id is not None,
            "created_at": code.created_at.isoformat(),
        })
    return rows
```

- [ ] **Step 5: Run tests**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Run full suite**

```bash
.venv/bin/pytest api/tests/ -v --tb=short
```

Expected: all previously passing tests still pass

- [ ] **Step 7: Commit**

```bash
git add api/routers/demo.py api/routers/admin.py
git commit -m "feat: trusted code generation, whitelist admin, extended demo redeem"
```

---

## Task 6: Chat Router — Trusted Access + Compatibility Prompt

**Files:**
- Modify: `api/routers/chat.py`
- Test: `api/tests/test_trusted_tier.py` (add test)

- [ ] **Step 1: Write failing test**

Append to `api/tests/test_trusted_tier.py`:

```python
@pytest.mark.asyncio
async def test_chat_allowed_for_trusted_chart(monkeypatch):
    """Trusted chart should bypass the daily free limit."""
    from unittest.mock import AsyncMock, patch

    async def fake_stream(msg, system):
        yield "test response"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create chart
        chart_r = await client.post("/api/chart", json={
            "name": "Trusted", "birth_date": "1990-06-15", "birth_time": "08:00",
            "birth_place": "Chennai, India", "email": "trusted_chat@test.com"
        })
        chart_id = chart_r.json()["chart_id"]

        # Generate + redeem a trusted code
        gen = await client.post("/api/admin/trusted-codes/generate", json={
            "secret": "admin-dev-secret", "count": 1
        })
        code = gen.json()["codes"][0]["code"]
        await client.post("/api/demo/redeem", json={"code": code, "chart_id": chart_id})

        # Chat should succeed (patch LLM to avoid real API call)
        with patch("api.routers.chat.LLMAdapter") as MockAdapter:
            instance = MockAdapter.return_value
            instance.stream = fake_stream
            r = await client.post("/api/chat", json={
                "chart_id": chart_id,
                "tab": "know_thyself",
                "message": "What is my purpose?"
            })
            # Should not get 403
            assert r.status_code != 403
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py::test_chat_allowed_for_trusted_chart -v
```

Expected: FAIL (403 because daily limit hit with no access code recognised)

- [ ] **Step 3: Update chat.py — trusted access check and compatibility prompt**

In `api/routers/chat.py`, replace the access-check block and add the compatibility prompt.

After the `if not chart.user.paid:` block (replace the entire block):

```python
    if not chart.user.paid:
        now = datetime.now(timezone.utc)
        code_result = await db.execute(
            select(AccessCode).where(
                AccessCode.chart_id == req.chart_id,
                or_(
                    and_(AccessCode.type == "demo", AccessCode.expires_at > now),
                    and_(AccessCode.type == "trusted", AccessCode.expires_at.is_(None)),
                ),
            )
        )
        access = code_result.scalar_one_or_none()
        is_trusted = access is not None and access.type == "trusted"
        has_access = access is not None

        if not has_access:
            since = now - timedelta(days=1)
            count_result = await db.execute(
                select(func.count()).where(
                    ChatMessage.chart_id == req.chart_id,
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= since,
                )
            )
            if count_result.scalar() >= FREE_DAILY_LIMIT:
                raise HTTPException(
                    status_code=403,
                    detail="Daily free limit reached. Unlock full access for ₹50.",
                )
    else:
        is_trusted = False
```

Then add the compatibility system prompt addition. Replace the `system = CHAT_SYSTEM.format(...)` line with:

```python
    system = CHAT_SYSTEM.format(chart_context=chart_context, book_passages=book_passages)
    if is_trusted:
        system += (
            "\n\nThis user has access to their own natal chart only. "
            "If they reference another person's birth details (date, time, place) "
            "in the context of compatibility or relationship matching, you may provide "
            "a brief synastry analysis only. Do not provide a full standalone natal "
            "reading for any other person."
        )
```

- [ ] **Step 4: Add `or_`, `and_` imports to chat.py**

At the top of `api/routers/chat.py`, update the sqlalchemy import:

```python
from sqlalchemy import select, func, or_, and_
```

- [ ] **Step 5: Run tests**

```bash
.venv/bin/pytest api/tests/test_trusted_tier.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Run full suite**

```bash
.venv/bin/pytest api/tests/ -v --tb=short
```

Expected: all previously passing tests pass

- [ ] **Step 7: Commit**

```bash
git add api/routers/chat.py
git commit -m "feat: chat allows trusted access, injects compatibility system prompt"
```

---

## Task 7: DB Migration + Railway Env Var

- [ ] **Step 1: Set ADMIN_SECRET on Railway**

```bash
cd /home/jo/claude_projects/P046_202604_KnowThyselfAstro
railway variables set ADMIN_SECRET=astrowise-admin-2026
```

Expected: variable set confirmation

- [ ] **Step 2: Deploy backend to Railway**

```bash
railway up --detach
```

Expected: deploy triggered (watch logs at https://railway.app)

- [ ] **Step 3: Run migration against production DB**

```bash
DATABASE_URL=$(railway variables get DATABASE_URL) .venv/bin/alembic upgrade head
```

Or via Railway shell if DATABASE_URL not accessible locally. Confirm migration ran:

```bash
curl -s https://astrowise-api-production.up.railway.app/health
```

Expected: `{"status": "ok"}`

---

## Task 8: Frontend Updates

**Repo:** `/home/jo/claude_projects/P081_202605_AstrowiseSite`

**Files:**
- Modify: `lib/types.ts`
- Modify: `lib/api.ts`
- Modify: `app/profile/[chartId]/page.tsx`

- [ ] **Step 1: Update ChartSummary type**

In `lib/types.ts`, update `ChartSummary`:

```typescript
export interface ChartSummary {
  chart_id: string
  lagna: string
  lagna_deg: number
  current_dasha: string
  yogas: string[]
  animal: string
  animal_emoji: string
  paid: boolean
  trusted: boolean
  profile_html_ready: boolean
}
```

- [ ] **Step 2: Add reading URL helper to api.ts**

Append to `lib/api.ts`:

```typescript
export function getReadingUrl(chartId: string): string {
  const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
  return `${BASE}/api/chart/${chartId}/reading`
}
```

- [ ] **Step 3: Update profile page**

Replace `app/profile/[chartId]/page.tsx`:

```typescript
import { redirect } from 'next/navigation'
import { getChart, getReadingUrl } from '@/lib/api'
import ProfilePreview from '@/components/ProfilePreview'
import PaymentButton from '@/components/PaymentButton'
import DemoCodeInput from '@/components/DemoCodeInput'
import type { ChartSummary } from '@/lib/types'

export default async function ProfilePage({
  params,
  searchParams,
}: {
  params: Promise<{ chartId: string }>
  searchParams: Promise<{ demo?: string }>
}) {
  const { chartId } = await params
  const { demo } = await searchParams
  let chart: ChartSummary
  try {
    chart = await getChart(chartId)
  } catch {
    redirect('/onboarding')
  }

  if (chart!.paid) redirect(`/report/${chartId}`)
  if (chart!.trusted) redirect(`/chat/${chartId}`)

  const readingUrl = getReadingUrl(chartId)

  return (
    <main className="min-h-screen py-20 px-6">
      <div className="text-center mb-12">
        <p className="text-gold text-xs tracking-widest uppercase mb-2">Your Chart</p>
        <h1 className="text-4xl text-cream">A glimpse into who you are</h1>
      </div>
      <ProfilePreview chart={chart!} />

      {/* Full Reading button */}
      <div className="text-center mt-8 mb-4">
        <a
          href={readingUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-block border border-gold text-gold px-8 py-3 rounded-full text-sm
                      hover:bg-gold hover:text-ink transition-colors
                      ${!chart!.profile_html_ready ? 'opacity-40 pointer-events-none' : ''}`}
        >
          {chart!.profile_html_ready ? 'View Full Reading ↗' : 'Preparing your reading…'}
        </a>
        {!chart!.profile_html_ready && (
          <p className="text-cream-muted text-xs mt-2">Usually ready within 10 seconds</p>
        )}
      </div>

      <PaymentButton chartId={chartId} />
      <DemoCodeInput chartId={chartId} initialCode={demo} />
    </main>
  )
}
```

- [ ] **Step 4: Build frontend locally to check for TypeScript errors**

```bash
cd /home/jo/claude_projects/P081_202605_AstrowiseSite
npm run build
```

Expected: no TypeScript errors, build succeeds

- [ ] **Step 5: Commit frontend**

```bash
git add lib/types.ts lib/api.ts app/profile/
git commit -m "feat: profile page — full reading button, trusted redirect to chat"
```

- [ ] **Step 6: Deploy frontend**

```bash
netlify deploy --build --prod
```

Expected: deploy to https://astrowyze.netlify.app

---

## Task 9: Smoke Test End-to-End

- [ ] **Step 1: Generate a trusted invite code**

```bash
curl -s -X POST https://astrowise-api-production.up.railway.app/api/admin/trusted-codes/generate \
  -H "Content-Type: application/json" \
  -d '{"secret": "astrowise-admin-2026", "count": 1, "note": "smoke test"}'
```

Expected: `{"codes": [{"code": "TRUST-XXXXXX"}]}`

- [ ] **Step 2: Test whitelist**

```bash
curl -s -X POST https://astrowise-api-production.up.railway.app/api/admin/whitelist/add \
  -H "Content-Type: application/json" \
  -d '{"secret": "astrowise-admin-2026", "email": "45degreesolutions@gmail.com", "note": "Jo - admin"}'
```

Expected: `{"ok": true}`

- [ ] **Step 3: Check trusted-users list**

```bash
curl -s "https://astrowise-api-production.up.railway.app/api/admin/trusted-users?secret=astrowise-admin-2026"
```

Expected: JSON array with generated codes

- [ ] **Step 4: Visit https://astrowyze.netlify.app and create a test chart**

Open in browser, fill in birth details, submit. Profile page should show:
- "View Full Reading ↗" button (may show "Preparing…" for first 10 seconds, then become active)
- Payment button below
- Demo code input below that

- [ ] **Step 5: Test the /reading endpoint directly**

```bash
curl -s -o /dev/null -w "%{http_code}" \
  https://astrowise-api-production.up.railway.app/api/chart/<chart_id>/reading
```

Wait ~15 seconds after chart creation, then check. Expected: 200 with HTML body.

- [ ] **Step 6: Onboard Ruhi using invite code**

Send Ruhi the invite code + link:  
`https://astrowyze.netlify.app/onboarding?invite=TRUST-XXXXXX`  
(No URL param needed — she just uses the DemoCodeInput on the profile page)

---

## Generating Trusted Codes for Existing Clients

For Ruhi, Prakashji, and other past clients who already have chart IDs:

```bash
# Generate codes
curl -s -X POST https://astrowise-api-production.up.railway.app/api/admin/trusted-codes/generate \
  -H "Content-Type: application/json" \
  -d '{"secret": "astrowise-admin-2026", "count": 5, "note": "existing clients June 2026"}'

# Or use whitelist if you know their email:
curl -s -X POST https://astrowise-api-production.up.railway.app/api/admin/whitelist/add \
  -H "Content-Type: application/json" \
  -d '{"secret": "astrowise-admin-2026", "email": "ruhi@example.com", "note": "Ruhi - past client"}'
```
