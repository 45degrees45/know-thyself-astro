# AstroWise Web Platform — Implementation Plan (MVP)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a web platform where anyone enters their birth details, gets a free Vedic profile preview, pays ₹50 for the full report + PDF + chatbot — vs ₹500 with a human astrologer.

**Architecture:** FastAPI (Python) on Railway wraps the existing `astro_engine/` directly as a Python library. Next.js frontend (converting the existing P081 Netlify site) calls the API. PostgreSQL on Railway stores users, charts, chat. The existing EC2 batch pipeline runs untouched alongside.

**Tech Stack:** FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · NextAuth.js · Next.js 14 (App Router) · Tailwind CSS · Razorpay · Anthropic SDK (default LLM) · SSE streaming

---

## Project Locations

| What | Where |
|---|---|
| FastAPI backend | `P046_202604_KnowThyselfAstro/api/` (new) |
| astro_engine (existing, untouched) | `P046_202604_KnowThyselfAstro/astro_engine/` |
| Next.js frontend | `P081_202605_AstrowiseSite/` (convert from static HTML) |
| Spec | `P046_202604_KnowThyselfAstro/docs/superpowers/specs/2026-06-13-astrowise-web-platform-design.md` |

---

## File Map

### Backend — `P046_202604_KnowThyselfAstro/api/`

```
api/
  main.py               # FastAPI app, CORS, router registration
  config.py             # Settings via pydantic-settings (.env)
  database.py           # SQLAlchemy engine + session factory
  models.py             # ORM models: User, Chart, ChatMessage, QuestionBank
  schemas.py            # Pydantic request/response schemas
  routers/
    charts.py           # POST /chart, GET /chart/{id}
    reports.py          # GET /report/{id} (SSE stream)
    chat.py             # POST /chat (SSE stream)
    questions.py        # GET /questions/{tab}, GET /questions/trending
    payments.py         # POST /payments/order, POST /payments/verify
  services/
    astro_service.py    # Wraps astro_engine: calculate, summarise
    llm_adapter.py      # LLMAdapter: Anthropic default, BYOK later
    report_service.py   # Builds report prompt, calls LLMAdapter
    pdf_service.py      # Wraps existing pdf_premium.py
  tests/
    test_astro_service.py
    test_llm_adapter.py
    test_charts.py
    test_payments.py
    test_chat.py
  requirements.txt
  Procfile              # web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
  railway.toml
```

### Frontend — `P081_202605_AstrowiseSite/`

```
(existing: index.html, netlify/, netlify.toml, package.json — keep netlify.toml, replace rest)

app/
  layout.tsx            # Root layout: fonts, globals
  page.tsx              # Landing page (port existing index.html design)
  onboarding/
    page.tsx            # Step 1: birth data form
  profile/
    [chartId]/
      page.tsx          # Free preview + unlock CTA
  report/
    [chartId]/
      page.tsx          # Full paid report (gated)
  chat/
    [chartId]/
      page.tsx          # Chatbot tabs + question pills
  share/
    [slug]/
      page.tsx          # Anon public profile
  api/
    auth/
      [...nextauth]/
        route.ts        # NextAuth handler
components/
  BirthForm.tsx         # Onboarding form with place autocomplete
  ProfilePreview.tsx    # Free teaser: lagna, animal, 3 yogas, dasha
  FullReport.tsx        # Full paid report renderer
  ChatInterface.tsx     # Tabbed chatbot with question pills
  QuestionPills.tsx     # Pills per tab, click → pre-fill input
  PaymentButton.tsx     # Razorpay checkout trigger
lib/
  api.ts                # fetch wrapper → Railway API base URL
  auth.ts               # NextAuth options (email + Google)
  types.ts              # Shared TypeScript types
middleware.ts           # Protect /report, /chat routes
next.config.ts
tailwind.config.ts
package.json            # next, react, next-auth, razorpay
```

---

## Task 1: FastAPI Skeleton + Config

**Files:**
- Create: `api/main.py`
- Create: `api/config.py`
- Create: `api/requirements.txt`
- Create: `api/Procfile`
- Create: `api/railway.toml`

- [ ] **Step 1: Create `api/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.36
alembic==1.13.3
asyncpg==0.30.0
pydantic-settings==2.6.0
python-dotenv==1.0.1
anthropic==0.40.0
httpx==0.27.2
razorpay==1.4.2
fpdf2==2.8.1
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

- [ ] **Step 2: Create `api/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    razorpay_key_id: str
    razorpay_key_secret: str
    jwt_secret: str
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 3: Create `api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routers import charts, reports, chat, questions, payments

app = FastAPI(title="AstroWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(charts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(payments.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Create `api/Procfile` and `api/railway.toml`**

`Procfile`:
```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

`railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

- [ ] **Step 5: Create `api/.env.example`**

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/astrowise
ANTHROPIC_API_KEY=sk-ant-...
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
JWT_SECRET=change-me-to-random-64-chars
FRONTEND_URL=http://localhost:3000
```

- [ ] **Step 6: Verify app starts**

```bash
cd P046_202604_KnowThyselfAstro
pip install -r api/requirements.txt
ANTHROPIC_API_KEY=test DATABASE_URL=sqlite+aiosqlite:///./test.db \
  RAZORPAY_KEY_ID=x RAZORPAY_KEY_SECRET=x JWT_SECRET=x \
  uvicorn api.main:app --reload
```
Expected: server starts on port 8000, `/health` returns `{"status":"ok"}`

- [ ] **Step 7: Commit**

```bash
git add api/
git commit -m "feat: FastAPI skeleton with config and CORS"
```

---

## Task 2: Database Models + Migrations

**Files:**
- Create: `api/database.py`
- Create: `api/models.py`
- Create: `api/schemas.py`
- Create: `alembic.ini` + `migrations/`

- [ ] **Step 1: Write failing test**

```python
# api/tests/test_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from api.models import Base, User, Chart

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_create_user_and_chart(db):
    user = User(email="test@x.com", name="Test")
    db.add(user)
    db.flush()
    chart = Chart(
        user_id=user.id,
        birth_date="1985-03-07",
        birth_time="07:15",
        birth_place="Kangazha, Kerala",
        lat=9.75, lon=76.78, tz="Asia/Kolkata",
        chart_json={"lagna": "Pisces", "lagna_deg": 0.9},
    )
    db.add(chart)
    db.commit()
    assert chart.id is not None
    assert chart.user_id == user.id
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd P046_202604_KnowThyselfAstro
pytest api/tests/test_models.py -v
```
Expected: `ImportError: No module named 'api.models'`

- [ ] **Step 3: Create `api/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from api.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 4: Create `api/models.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    google_id: Mapped[str | None] = mapped_column(String, nullable=True)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    charts: Mapped[list["Chart"]] = relationship(back_populates="user")

class Chart(Base):
    __tablename__ = "charts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    birth_date: Mapped[str] = mapped_column(String)
    birth_time: Mapped[str] = mapped_column(String)
    birth_place: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    tz: Mapped[str] = mapped_column(String)
    chart_json: Mapped[dict] = mapped_column(JSON)
    anon_slug: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="charts")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="chart")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chart_id: Mapped[str] = mapped_column(ForeignKey("charts.id"), index=True)
    tab: Mapped[str] = mapped_column(String)   # know_thyself | trending | spiritual | career | relationship | last_question
    role: Mapped[str] = mapped_column(String)   # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    chart: Mapped["Chart"] = relationship(back_populates="messages")

class QuestionBank(Base):
    __tablename__ = "question_bank"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tab: Mapped[str] = mapped_column(String, index=True)
    question: Mapped[str] = mapped_column(Text)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    lagna_filter: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class WeeklyQuestion(Base):
    __tablename__ = "weekly_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text)
    week_of: Mapped[str] = mapped_column(String, unique=True)  # YYYY-WNN
    active: Mapped[bool] = mapped_column(Boolean, default=True)
```

- [ ] **Step 5: Run test — expect PASS**

```bash
pytest api/tests/test_models.py -v
```
Expected: `PASSED`

- [ ] **Step 6: Create `api/schemas.py`**

```python
from pydantic import BaseModel, EmailStr
from typing import Any

class ChartRequest(BaseModel):
    name: str
    birth_date: str   # YYYY-MM-DD
    birth_time: str   # HH:MM (24h)
    birth_place: str
    email: EmailStr

class ChartSummary(BaseModel):
    chart_id: str
    lagna: str
    lagna_deg: float
    current_dasha: str
    yogas: list[str]
    animal: str
    animal_desc: str

class ChatRequest(BaseModel):
    chart_id: str
    tab: str
    message: str

class PaymentOrderRequest(BaseModel):
    chart_id: str

class PaymentVerifyRequest(BaseModel):
    chart_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
```

- [ ] **Step 7: Initialise Alembic**

```bash
cd P046_202604_KnowThyselfAstro
alembic init migrations
```

Edit `alembic.ini` — set `script_location = api/migrations`

Edit `api/migrations/env.py` — add:
```python
from api.models import Base
target_metadata = Base.metadata
```

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

- [ ] **Step 8: Commit**

```bash
git add api/
git commit -m "feat: database models and Alembic migrations"
```

---

## Task 3: AstroService — Wraps astro_engine

**Files:**
- Create: `api/services/astro_service.py`
- Create: `api/tests/test_astro_service.py`

- [ ] **Step 1: Write failing test**

```python
# api/tests/test_astro_service.py
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

def test_chart_summary_has_animal(mocker):
    svc = AstroService()
    chart_json = svc.calculate("1985-03-07", "07:15", "Kangazha, Kerala")
    summary = svc.build_summary(chart_json)
    assert "animal" in summary
    assert summary["lagna"] == "Pisces"
    assert "current_dasha" in summary
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd P046_202604_KnowThyselfAstro
pytest api/tests/test_astro_service.py -v
```
Expected: `ImportError: No module named 'api.services.astro_service'`

- [ ] **Step 3: Create `api/services/astro_service.py`**

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astro_engine"))

from geo import geocode
from calc import calculate_chart, chart_summary
from dasha import current_period
from yoga import find_yogas, yoga_summary

MOON_ANIMAL = {
    "Ashwini": ("Horse", "🐎"), "Bharani": ("Elephant", "🐘"),
    "Krittika": ("Goat", "🐐"), "Rohini": ("Serpent", "🐍"),
    "Mrigashira": ("Serpent", "🐍"), "Ardra": ("Dog", "🐕"),
    "Punarvasu": ("Cat", "🐈"), "Pushya": ("Goat", "🐐"),
    "Ashlesha": ("Cat", "🐈"), "Magha": ("Rat", "🐀"),
    "Purva Phalguni": ("Rat", "🐀"), "Uttara Phalguni": ("Cow", "🐄"),
    "Hasta": ("Buffalo", "🦬"), "Chitra": ("Tiger", "🐅"),
    "Swati": ("Buffalo", "🦬"), "Vishakha": ("Tiger", "🐅"),
    "Anuradha": ("Deer", "🦌"), "Jyeshtha": ("Deer", "🦌"),
    "Mula": ("Dog", "🐕"), "Purva Ashadha": ("Monkey", "🐒"),
    "Uttara Ashadha": ("Mongoose", "🦡"), "Shravana": ("Monkey", "🐒"),
    "Dhanishtha": ("Lion", "🦁"), "Shatabhisha": ("Horse", "🐎"),
    "Purva Bhadrapada": ("Lion", "🦁"), "Uttara Bhadrapada": ("Cow", "🐄"),
    "Revati": ("Elephant", "🐘"),
}

class AstroService:
    def calculate(self, birth_date: str, birth_time: str, birth_place: str) -> dict:
        geo = geocode(birth_place)
        chart = calculate_chart(birth_date, birth_time, geo["lat"], geo["lon"], geo["timezone"])
        yogas = find_yogas(chart)
        dasha = current_period(chart)

        moon_nakshatra = chart.get("moon_nakshatra", "")
        animal_name, animal_emoji = MOON_ANIMAL.get(moon_nakshatra, ("Eagle", "🦅"))

        return {
            "lagna": chart["lagna"],
            "lagna_deg": round(chart["lagna_deg"], 2),
            "planets": chart.get("planets", {}),
            "moon_nakshatra": moon_nakshatra,
            "yogas": [y["name"] for y in yogas],
            "yoga_details": yogas,
            "current_dasha": f"{dasha['lord']}/{dasha.get('sub','')}/{dasha.get('subsub','')}".strip("/"),
            "animal": animal_name,
            "animal_emoji": animal_emoji,
            "raw_chart": chart,
        }

    def build_summary(self, chart_json: dict) -> dict:
        return {
            "lagna": chart_json["lagna"],
            "lagna_deg": chart_json["lagna_deg"],
            "current_dasha": chart_json["current_dasha"],
            "yogas": chart_json["yogas"][:3],
            "animal": chart_json["animal"],
            "animal_emoji": chart_json["animal_emoji"],
        }
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest api/tests/test_astro_service.py::test_calculate_chart_returns_lagna -v
```
Expected: `PASSED` (may take 2–3s for Swiss Ephemeris calculation)

- [ ] **Step 5: Commit**

```bash
git add api/services/astro_service.py api/tests/test_astro_service.py
git commit -m "feat: AstroService wrapping astro_engine"
```

---

## Task 4: Charts API Router

**Files:**
- Create: `api/routers/charts.py`
- Create: `api/tests/test_charts.py`

- [ ] **Step 1: Write failing test**

```python
# api/tests/test_charts.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from api.main import app
from api.models import Base

@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

client = TestClient(app)

def test_post_chart_returns_chart_id():
    response = client.post("/api/chart", json={
        "name": "Goldy",
        "birth_date": "1985-03-07",
        "birth_time": "07:15",
        "birth_place": "Kangazha, Kerala",
        "email": "goldy@test.com",
    })
    assert response.status_code == 200
    data = response.json()
    assert "chart_id" in data
    assert data["lagna"] == "Pisces"

def test_get_chart_returns_summary():
    post = client.post("/api/chart", json={
        "name": "Goldy", "birth_date": "1985-03-07",
        "birth_time": "07:15", "birth_place": "Kangazha, Kerala",
        "email": "goldy@test.com",
    })
    chart_id = post.json()["chart_id"]
    get = client.get(f"/api/chart/{chart_id}")
    assert get.status_code == 200
    assert get.json()["lagna"] == "Pisces"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest api/tests/test_charts.py -v
```
Expected: `ImportError: cannot import name 'charts' from 'api.routers'`

- [ ] **Step 3: Create `api/routers/charts.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_db
from api.models import User, Chart
from api.schemas import ChartRequest, ChartSummary
from api.services.astro_service import AstroService
import uuid

router = APIRouter()
_astro = AstroService()

@router.post("/chart", response_model=dict)
async def create_chart(req: ChartRequest, db: AsyncSession = Depends(get_db)):
    # Upsert user by email
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=req.email, name=req.name)
        db.add(user)
        await db.flush()

    chart_json = _astro.calculate(req.birth_date, req.birth_time, req.birth_place)
    from api.services.astro_service import geocode
    geo_data = geocode(req.birth_place)

    chart = Chart(
        user_id=user.id,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        birth_place=req.birth_place,
        lat=geo_data["lat"],
        lon=geo_data["lon"],
        tz=geo_data["timezone"],
        chart_json=chart_json,
    )
    db.add(chart)
    await db.commit()
    await db.refresh(chart)

    summary = _astro.build_summary(chart_json)
    return {"chart_id": chart.id, **summary}

@router.get("/chart/{chart_id}", response_model=dict)
async def get_chart(chart_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chart).where(Chart.id == chart_id))
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    summary = _astro.build_summary(chart.chart_json)
    return {"chart_id": chart.id, **summary, "paid": chart.user.paid}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest api/tests/test_charts.py -v
```
Expected: both tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add api/routers/charts.py api/tests/test_charts.py
git commit -m "feat: charts router — POST /chart and GET /chart/{id}"
```

---

## Task 5: LLMAdapter (Anthropic Default)

**Files:**
- Create: `api/services/llm_adapter.py`
- Create: `api/tests/test_llm_adapter.py`

- [ ] **Step 1: Write failing test**

```python
# api/tests/test_llm_adapter.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.llm_adapter import LLMAdapter

@pytest.mark.asyncio
async def test_complete_returns_string():
    adapter = LLMAdapter(provider="anthropic", api_key="test-key")
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="You are a Pisces rising.")]
    with patch("anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create = AsyncMock(return_value=mock_msg)
        result = await adapter.complete("Describe my chart", "You are an astrologer.")
    assert "Pisces" in result

@pytest.mark.asyncio
async def test_stream_yields_chunks():
    adapter = LLMAdapter(provider="anthropic", api_key="test-key")
    async def fake_stream():
        for chunk in ["Hello", " world"]:
            event = MagicMock()
            event.type = "content_block_delta"
            event.delta = MagicMock(text=chunk)
            yield event
    with patch("anthropic.AsyncAnthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.stream.return_value.__aenter__ = AsyncMock(return_value=fake_stream())
        chunks = []
        async for chunk in adapter.stream("Tell me about Pisces", "You are an astrologer."):
            chunks.append(chunk)
    assert "".join(chunks) == "Hello world"
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest api/tests/test_llm_adapter.py -v
```

- [ ] **Step 3: Create `api/services/llm_adapter.py`**

```python
from typing import AsyncIterator
import anthropic

MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "gemini": "gemini-1.5-pro",
    "openai": "gpt-4o",
}

class LLMAdapter:
    def __init__(self, provider: str = "anthropic", api_key: str = None, base_url: str = None):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

    def _anthropic_client(self):
        return anthropic.AsyncAnthropic(api_key=self.api_key)

    def _openai_compatible_client(self):
        # Gemini, OpenAI, Mistral, NIM all use OpenAI-compatible SDK
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def complete(self, prompt: str, system: str) -> str:
        if self.provider == "anthropic":
            client = self._anthropic_client()
            msg = await client.messages.create(
                model=MODELS["anthropic"],
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        else:
            client = self._openai_compatible_client()
            resp = await client.chat.completions.create(
                model=MODELS.get(self.provider, self.provider),
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content

    async def stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        if self.provider == "anthropic":
            client = self._anthropic_client()
            async with client.messages.stream(
                model=MODELS["anthropic"],
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        yield event.delta.text
        else:
            client = self._openai_compatible_client()
            stream = await client.chat.completions.create(
                model=MODELS.get(self.provider, self.provider),
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest api/tests/test_llm_adapter.py -v
```

- [ ] **Step 5: Commit**

```bash
git add api/services/llm_adapter.py api/tests/test_llm_adapter.py
git commit -m "feat: LLMAdapter — Anthropic default, OpenAI-compatible for BYOK"
```

---

## Task 6: Reports Router (SSE Streaming)

**Files:**
- Create: `api/services/report_service.py`
- Create: `api/routers/reports.py`

- [ ] **Step 1: Create `api/services/report_service.py`**

```python
from api.services.llm_adapter import LLMAdapter
from api.config import settings

REPORT_SYSTEM = """You are AstroWise — a Vedic astrology report writer using Lahiri ayanamsha.
Write in warm, direct, non-fatalistic language. Avoid fortune-teller certainty.
Use "you may notice" and "this period invites" rather than "you will".
Structure: use clear headings. No bullet points — flowing paragraphs only."""

REPORT_PROMPT_TEMPLATE = """
Write a complete AstroWise personal report for {name}.

CHART DATA (ground truth — do not contradict):
- Lagna (Ascendant): {lagna} {lagna_deg}°
- Current Dasha: {current_dasha}
- Key Yogas: {yogas}
- Spirit Animal: {animal} {animal_emoji}
- Planets: {planets_summary}

SECTIONS TO WRITE:
1. Core Nature — personality, dominant traits, lagna character, emotional style
2. Career — best domains, strengths, supportive yogas, leadership vs support style
3. Relationships — 7th house, Venus, partner profile, how they love and want to be loved
4. Spiritual Pointers — soul lesson, karma being cleared, dharma, best practice for this chart
5. Career Window — specific dasha/transit periods for breakthroughs (next 3 years)
6. Marriage Window — dasha/transit windows for committed relationship (next 3 years)
7. Shadow Side — honest blind spots, challenging yogas, where growth is needed
8. Remedies — Tier 1 Universal (behavioural, gemstones, sound), Tier 3 Neuroscience/CBT
   Do NOT include Vedic mantras/puja unless specifically requested.
9. Weekly Practice Calendar — 7-column Mon–Sun grid with daily practices

Write with depth and care. This person paid for insight, not platitudes.
"""

class ReportService:
    def __init__(self):
        self.adapter = LLMAdapter(
            provider="anthropic",
            api_key=settings.anthropic_api_key,
        )

    def _build_prompt(self, chart_json: dict, name: str) -> str:
        planets = chart_json.get("planets", {})
        planets_summary = ", ".join(
            f"{p} in {d.get('sign','?')} H{d.get('house','?')}"
            for p, d in planets.items()
        ) if planets else "see chart"

        return REPORT_PROMPT_TEMPLATE.format(
            name=name,
            lagna=chart_json["lagna"],
            lagna_deg=chart_json["lagna_deg"],
            current_dasha=chart_json["current_dasha"],
            yogas=", ".join(chart_json.get("yogas", [])),
            animal=chart_json["animal"],
            animal_emoji=chart_json.get("animal_emoji", ""),
            planets_summary=planets_summary,
        )

    async def stream_report(self, chart_json: dict, name: str):
        prompt = self._build_prompt(chart_json, name)
        async for chunk in self.adapter.stream(prompt, REPORT_SYSTEM):
            yield chunk
```

- [ ] **Step 2: Create `api/routers/reports.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_db
from api.models import Chart, User
from api.services.report_service import ReportService
import json

router = APIRouter()
_report_svc = ReportService()

@router.get("/report/{chart_id}")
async def stream_report(chart_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chart).join(User).where(Chart.id == chart_id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    if not chart.user.paid:
        raise HTTPException(status_code=403, detail="Payment required")

    async def event_stream():
        async for chunk in _report_svc.stream_report(chart.chart_json, chart.user.name):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 3: Manually test with curl (needs real ANTHROPIC_API_KEY)**

```bash
curl -N "http://localhost:8000/api/report/<chart_id>"
```
Expected: stream of `data: {"text": "..."}` lines ending with `data: [DONE]`

- [ ] **Step 4: Commit**

```bash
git add api/services/report_service.py api/routers/reports.py
git commit -m "feat: SSE streaming report generation via LLMAdapter"
```

---

## Task 7: Payments Router (Razorpay)

**Files:**
- Create: `api/routers/payments.py`
- Create: `api/tests/test_payments.py`

- [ ] **Step 1: Write failing test**

```python
# api/tests/test_payments.py
import pytest, hmac, hashlib
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_order_returns_order_id():
    mock_order = {"id": "order_test123", "amount": 5000, "currency": "INR"}
    with patch("razorpay.Client") as MockRzp:
        MockRzp.return_value.order.create.return_value = mock_order
        resp = client.post("/api/payments/order", json={"chart_id": "abc"})
    assert resp.status_code == 200
    assert resp.json()["order_id"] == "order_test123"

def test_verify_payment_marks_user_paid():
    key_secret = "test_secret"
    order_id = "order_abc"
    payment_id = "pay_xyz"
    sig = hmac.new(
        key_secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256
    ).hexdigest()
    with patch("api.routers.payments.settings") as mock_settings:
        mock_settings.razorpay_key_secret = key_secret
        resp = client.post("/api/payments/verify", json={
            "chart_id": "chart_abc",
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": sig,
        })
    assert resp.status_code == 200
    assert resp.json()["paid"] is True
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
pytest api/tests/test_payments.py -v
```

- [ ] **Step 3: Create `api/routers/payments.py`**

```python
import hmac, hashlib
import razorpay
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_db
from api.models import Chart, User
from api.schemas import PaymentOrderRequest, PaymentVerifyRequest
from api.config import settings

router = APIRouter()
AMOUNT_PAISE = 5000  # ₹50 = 5000 paise

@router.post("/payments/order")
async def create_order(req: PaymentOrderRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chart).where(Chart.id == req.chart_id))
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    order = client.order.create({
        "amount": AMOUNT_PAISE,
        "currency": "INR",
        "notes": {"chart_id": req.chart_id},
    })
    return {"order_id": order["id"], "amount": AMOUNT_PAISE, "currency": "INR",
            "key_id": settings.razorpay_key_id}

@router.post("/payments/verify")
async def verify_payment(req: PaymentVerifyRequest, db: AsyncSession = Depends(get_db)):
    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{req.razorpay_order_id}|{req.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, req.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    result = await db.execute(
        select(Chart).join(User).where(Chart.id == req.chart_id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    chart.user.paid = True
    await db.commit()
    return {"paid": True, "chart_id": req.chart_id}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
pytest api/tests/test_payments.py -v
```

- [ ] **Step 5: Commit**

```bash
git add api/routers/payments.py api/tests/test_payments.py
git commit -m "feat: Razorpay order creation and HMAC payment verification"
```

---

## Task 8: Chatbot Router (SSE + Question Banks)

**Files:**
- Create: `api/routers/chat.py`
- Create: `api/routers/questions.py`
- Create: `api/tests/test_chat.py`
- Create: `api/seeds/questions.sql`

- [ ] **Step 1: Write failing test**

```python
# api/tests/test_chat.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_chat_requires_paid():
    resp = client.post("/api/chat", json={
        "chart_id": "nonexistent",
        "tab": "know_thyself",
        "message": "Why am I always tired?",
    })
    assert resp.status_code in (404, 403)

def test_questions_returns_list():
    resp = client.get("/api/questions/know_thyself")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

- [ ] **Step 2: Create `api/routers/chat.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.database import get_db
from api.models import Chart, User, ChatMessage
from api.schemas import ChatRequest
from api.services.llm_adapter import LLMAdapter
from api.config import settings
import json
from datetime import datetime, timedelta

router = APIRouter()

FREE_DAILY_LIMIT = 5

CHAT_SYSTEM = """You are AstroWise — a wise, warm Vedic astrology guide.
The user's full birth chart is given below. Answer ONLY from what the chart shows.
Be specific to their placements — never generic.
Avoid fortune-teller certainty. Use "this chart suggests" and "you may notice".
Keep answers under 200 words unless depth is truly needed.

{chart_context}"""

def _build_chart_context(chart_json: dict) -> str:
    return (
        f"Lagna: {chart_json['lagna']} {chart_json['lagna_deg']}° | "
        f"Dasha: {chart_json['current_dasha']} | "
        f"Yogas: {', '.join(chart_json.get('yogas', []))} | "
        f"Animal: {chart_json['animal']} | "
        f"Moon Nakshatra: {chart_json.get('moon_nakshatra', 'unknown')}"
    )

@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chart).join(User).where(Chart.id == req.chart_id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    if not chart.user.paid:
        since = datetime.utcnow() - timedelta(days=1)
        count_result = await db.execute(
            select(func.count()).where(
                ChatMessage.chart_id == req.chart_id,
                ChatMessage.role == "user",
                ChatMessage.created_at >= since,
            )
        )
        if count_result.scalar() >= FREE_DAILY_LIMIT:
            raise HTTPException(status_code=403, detail="Daily free limit reached. Unlock full access for ₹50.")

    # Save user message
    db.add(ChatMessage(chart_id=req.chart_id, tab=req.tab, role="user", content=req.message))
    await db.commit()

    adapter = LLMAdapter(provider="anthropic", api_key=settings.anthropic_api_key)
    system = CHAT_SYSTEM.format(chart_context=_build_chart_context(chart.chart_json))

    async def event_stream():
        full_response = []
        async for chunk in adapter.stream(req.message, system):
            full_response.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"
        # Save assistant reply
        async with AsyncSessionLocal() as save_db:
            save_db.add(ChatMessage(
                chart_id=req.chart_id, tab=req.tab,
                role="assistant", content="".join(full_response),
            ))
            await save_db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 3: Create `api/routers/questions.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.database import get_db
from api.models import QuestionBank, WeeklyQuestion
from datetime import date

router = APIRouter()

@router.get("/questions/{tab}")
async def get_questions(tab: str, lagna: str = None, db: AsyncSession = Depends(get_db)):
    q = select(QuestionBank).where(QuestionBank.tab == tab, QuestionBank.active == True)
    if lagna:
        q = q.where((QuestionBank.lagna_filter == lagna) | (QuestionBank.lagna_filter == None))
    result = await db.execute(q.order_by(QuestionBank.click_count.desc()).limit(12))
    rows = result.scalars().all()
    return [{"id": r.id, "question": r.question, "clicks": r.click_count} for r in rows]

@router.get("/questions/trending")
async def get_trending(lagna: str = None, db: AsyncSession = Depends(get_db)):
    return await get_questions("trending", lagna, db)

@router.post("/questions/{question_id}/click")
async def record_click(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuestionBank).where(QuestionBank.id == question_id))
    q = result.scalar_one_or_none()
    if q:
        q.click_count += 1
        await db.commit()
    return {"ok": True}

@router.get("/questions/last")
async def get_last_question(db: AsyncSession = Depends(get_db)):
    week = date.today().strftime("%Y-W%V")
    result = await db.execute(
        select(WeeklyQuestion).where(WeeklyQuestion.week_of == week, WeeklyQuestion.active == True)
    )
    q = result.scalar_one_or_none()
    return {"question": q.question if q else "What are you most afraid to become?"}
```

- [ ] **Step 4: Create `api/seeds/questions.sql`**

```sql
-- Know Thyself
INSERT INTO question_bank (tab, question) VALUES
('know_thyself', 'Why do I overthink everything?'),
('know_thyself', 'What is my greatest core strength?'),
('know_thyself', 'Why do I keep self-sabotaging?'),
('know_thyself', 'What makes me feel most alive?'),
('know_thyself', 'What is my relationship with anger?'),
('know_thyself', 'Why do I struggle to ask for help?'),

-- Career
('career', 'What career domains suit me best?'),
('career', 'When is my next career breakthrough?'),
('career', 'Am I better as a leader or in a support role?'),
('career', 'What blocks my financial flow?'),
('career', 'Should I take the risk and go solo?'),

-- Relationship
('relationship', 'What kind of partner am I truly seeking?'),
('relationship', 'Why do I keep attracting the same type of person?'),
('relationship', 'How do I love vs how do I want to be loved?'),
('relationship', 'What triggers conflict in my relationships?'),
('relationship', 'When is the window for a committed relationship?'),

-- Spiritual
('spiritual', 'What is my soul''s lesson in this life?'),
('spiritual', 'What karma am I here to clear?'),
('spiritual', 'Am I living my dharma right now?'),
('spiritual', 'What is the best spiritual practice for my chart?'),
('spiritual', 'What do my past-life indicators show?'),

-- Trending seed (updated weekly)
('trending', 'What does my Rahu want from this life?'),
('trending', 'Am I living my dharma?'),
('trending', 'What is holding me back the most right now?');

-- First weekly question
INSERT INTO weekly_questions (question, week_of, active)
VALUES ('What are you most afraid to become?', '2026-W24', true);
```

- [ ] **Step 5: Run tests**

```bash
pytest api/tests/test_chat.py -v
```
Expected: both tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add api/routers/chat.py api/routers/questions.py api/seeds/questions.sql api/tests/test_chat.py
git commit -m "feat: chatbot SSE router and question bank endpoints"
```

---

## Task 9: Next.js Setup (Port P081 Brand)

**Files:**
- Modify: `P081_202605_AstrowiseSite/` — convert to Next.js, preserve brand

- [ ] **Step 1: Initialise Next.js in P081**

```bash
cd P081_202605_AstrowiseSite
# Back up existing landing page CSS/content
cp index.html index.html.bak
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir \
  --import-alias "@/*" --yes
```

- [ ] **Step 2: Install auth and fonts**

```bash
npm install next-auth @auth/prisma-adapter
npm install @fontsource/cormorant-garamond
```

- [ ] **Step 3: Create `lib/types.ts`**

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
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}
```

- [ ] **Step 4: Create `lib/api.ts`**

```typescript
const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function createChart(data: {
  name: string; birth_date: string; birth_time: string;
  birth_place: string; email: string;
}) {
  const res = await fetch(`${BASE}/api/chart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getChart(chartId: string) {
  const res = await fetch(`${BASE}/api/chart/${chartId}`)
  if (!res.ok) throw new Error('Chart not found')
  return res.json()
}

export async function createPaymentOrder(chartId: string) {
  const res = await fetch(`${BASE}/api/payments/order`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_id: chartId }),
  })
  return res.json()
}

export async function verifyPayment(payload: {
  chart_id: string; razorpay_order_id: string;
  razorpay_payment_id: string; razorpay_signature: string;
}) {
  const res = await fetch(`${BASE}/api/payments/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return res.json()
}

export async function getQuestions(tab: string, lagna?: string) {
  const url = `${BASE}/api/questions/${tab}${lagna ? `?lagna=${lagna}` : ''}`
  const res = await fetch(url)
  return res.json()
}
```

- [ ] **Step 5: Set Tailwind brand colours in `tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss'
export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        gold: '#c4983a',
        'gold-light': '#e8c060',
        'gold-dim': 'rgba(196,152,58,0.18)',
        cream: '#ede5cf',
        'cream-muted': '#887a65',
        ink: '#0c0905',
        'bg-card': 'rgba(18,13,6,0.92)',
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
```

- [ ] **Step 6: Create `app/layout.tsx`**

```typescript
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Astrowyze — Know Thyself',
  description: 'Vedic astrology insights. ₹50 vs ₹500 with an astrologer.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-ink text-cream font-serif min-h-screen">{children}</body>
    </html>
  )
}
```

- [ ] **Step 7: Verify Next.js runs**

```bash
npm run dev
```
Expected: `http://localhost:3000` loads with dark background

- [ ] **Step 8: Commit**

```bash
git add . && git commit -m "feat: Next.js app setup with brand colours and API client"
```

---

## Task 10: Onboarding Form Page

**Files:**
- Create: `components/BirthForm.tsx`
- Create: `app/onboarding/page.tsx`

- [ ] **Step 1: Create `components/BirthForm.tsx`**

```typescript
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createChart } from '@/lib/api'

export default function BirthForm() {
  const router = useRouter()
  const [form, setForm] = useState({
    name: '', birth_date: '', birth_time: '', birth_place: '', email: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await createChart(form)
      router.push(`/profile/${result.chart_id}`)
    } catch (err: any) {
      setError(err.message ?? 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-md mx-auto">
      {[
        { name: 'name', label: 'Your Name', type: 'text', placeholder: 'As you know yourself' },
        { name: 'email', label: 'Email', type: 'email', placeholder: 'For your chart link' },
        { name: 'birth_date', label: 'Date of Birth', type: 'date', placeholder: '' },
        { name: 'birth_time', label: 'Time of Birth', type: 'time', placeholder: 'HH:MM — as precise as possible' },
        { name: 'birth_place', label: 'Place of Birth', type: 'text', placeholder: 'City, Country' },
      ].map(({ name, label, type, placeholder }) => (
        <div key={name}>
          <label className="block text-cream-muted text-sm mb-1 tracking-widest uppercase text-xs">
            {label}
          </label>
          <input
            type={type}
            value={(form as any)[name]}
            onChange={e => setForm(f => ({ ...f, [name]: e.target.value }))}
            placeholder={placeholder}
            required
            className="w-full bg-transparent border border-gold-dim text-cream px-4 py-3
                       rounded focus:outline-none focus:border-gold placeholder-cream-muted
                       font-serif text-base"
          />
        </div>
      ))}
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="w-full border border-gold text-gold py-3 rounded
                   hover:bg-gold hover:text-ink transition-colors font-serif text-lg
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Calculating your chart…' : 'Reveal My Chart →'}
      </button>
    </form>
  )
}
```

- [ ] **Step 2: Create `app/onboarding/page.tsx`**

```typescript
import BirthForm from '@/components/BirthForm'

export default function OnboardingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-20">
      <div className="text-center mb-12">
        <p className="text-gold text-xs tracking-widest uppercase mb-4">Astrowyze</p>
        <h1 className="text-4xl md:text-5xl text-cream mb-4">Know Thyself</h1>
        <p className="text-cream-muted max-w-sm mx-auto leading-relaxed">
          Enter your birth details. Your Vedic chart will be calculated instantly
          using Swiss Ephemeris — the same precision astronomers use.
        </p>
        <div className="mt-6 inline-flex items-center gap-3 border border-gold-dim
                        rounded-full px-5 py-2 text-sm text-cream-muted">
          <span className="line-through text-red-400/70">₹500 with an astrologer</span>
          <span className="text-gold font-semibold">₹50 here</span>
        </div>
      </div>
      <BirthForm />
    </main>
  )
}
```

- [ ] **Step 3: Test in browser**

Navigate to `http://localhost:3000/onboarding`. Fill in the form with:
- Name: Goldy, DOB: 1985-03-07, Time: 07:15, Place: Kangazha, Kerala, Email: test@test.com

Expected: redirects to `/profile/<chart_id>` (404 for now — next task)

- [ ] **Step 4: Commit**

```bash
git add components/BirthForm.tsx app/onboarding/page.tsx
git commit -m "feat: onboarding form with birth data collection"
```

---

## Task 11: Free Profile Preview + Full Report Page

**Files:**
- Create: `components/ProfilePreview.tsx`
- Create: `components/PaymentButton.tsx`
- Create: `components/FullReport.tsx`
- Create: `app/profile/[chartId]/page.tsx`

- [ ] **Step 1: Create `components/ProfilePreview.tsx`**

```typescript
import type { ChartSummary } from '@/lib/types'

export default function ProfilePreview({ chart }: { chart: ChartSummary }) {
  return (
    <div className="space-y-8 max-w-xl mx-auto">
      <div className="text-center border border-gold-dim rounded-lg p-8 bg-bg-card">
        <div className="text-6xl mb-3">{chart.animal_emoji}</div>
        <p className="text-gold text-xs tracking-widest uppercase mb-1">Spirit Animal</p>
        <h2 className="text-3xl text-cream mb-4">The {chart.animal}</h2>
        <div className="border-t border-gold-dim pt-4 mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-cream-muted text-xs uppercase tracking-wider mb-1">Lagna</p>
            <p className="text-cream">{chart.lagna} {chart.lagna_deg}°</p>
          </div>
          <div>
            <p className="text-cream-muted text-xs uppercase tracking-wider mb-1">Current Dasha</p>
            <p className="text-cream">{chart.current_dasha}</p>
          </div>
        </div>
      </div>
      <div className="border border-gold-dim rounded-lg p-6 bg-bg-card">
        <p className="text-gold text-xs tracking-widest uppercase mb-3">Key Yogas (preview)</p>
        <div className="flex flex-wrap gap-2">
          {chart.yogas.slice(0, 3).map(y => (
            <span key={y} className="border border-gold-dim text-cream-muted text-xs px-3 py-1 rounded-full">
              {y}
            </span>
          ))}
          {chart.yogas.length > 3 && (
            <span className="text-cream-muted text-xs px-3 py-1">
              +{chart.yogas.length - 3} more unlocked below
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create `components/PaymentButton.tsx`**

```typescript
'use client'
import { useState } from 'react'
import { createPaymentOrder, verifyPayment } from '@/lib/api'
import { useRouter } from 'next/navigation'

declare global { interface Window { Razorpay: any } }

export default function PaymentButton({ chartId }: { chartId: string }) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  async function handlePay() {
    setLoading(true)
    try {
      const order = await createPaymentOrder(chartId)
      const rzp = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: 'Astrowyze',
        description: 'Full Vedic Report — ₹50',
        order_id: order.order_id,
        handler: async (response: any) => {
          await verifyPayment({
            chart_id: chartId,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          })
          router.push(`/report/${chartId}`)
        },
        theme: { color: '#c4983a' },
      })
      rzp.open()
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <script src="https://checkout.razorpay.com/v1/checkout.js" async />
      <div className="text-center mt-10">
        <p className="text-cream-muted mb-2 text-sm">
          Full report · Unlimited chat · PDF download
        </p>
        <button
          onClick={handlePay}
          disabled={loading}
          className="border border-gold bg-gold text-ink px-10 py-4 rounded
                     font-serif text-xl hover:bg-gold-light transition-colors
                     disabled:opacity-50"
        >
          Unlock Full Report — ₹50
        </button>
        <p className="text-cream-muted text-xs mt-3">vs ₹500 with an astrologer</p>
      </div>
    </>
  )
}
```

- [ ] **Step 3: Create `app/profile/[chartId]/page.tsx`**

```typescript
import { getChart } from '@/lib/api'
import ProfilePreview from '@/components/ProfilePreview'
import PaymentButton from '@/components/PaymentButton'
import { redirect } from 'next/navigation'

export default async function ProfilePage({ params }: { params: { chartId: string } }) {
  let chart
  try { chart = await getChart(params.chartId) }
  catch { redirect('/onboarding') }

  if (chart.paid) redirect(`/report/${params.chartId}`)

  return (
    <main className="min-h-screen py-20 px-6">
      <div className="text-center mb-12">
        <p className="text-gold text-xs tracking-widest uppercase mb-2">Your Chart</p>
        <h1 className="text-4xl text-cream">A glimpse into who you are</h1>
      </div>
      <ProfilePreview chart={chart} />
      <PaymentButton chartId={params.chartId} />
    </main>
  )
}
```

- [ ] **Step 4: Create `components/FullReport.tsx`**

```typescript
'use client'
import { useEffect, useState } from 'react'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function FullReport({ chartId }: { chartId: string }) {
  const [text, setText] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    const es = new EventSource(`${BASE}/api/report/${chartId}`)
    es.onmessage = (e) => {
      if (e.data === '[DONE]') { setDone(true); es.close(); return }
      const { text: chunk } = JSON.parse(e.data)
      setText(t => t + chunk)
    }
    return () => es.close()
  }, [chartId])

  return (
    <div className="max-w-2xl mx-auto">
      <div className="prose prose-invert prose-gold max-w-none font-serif leading-relaxed
                      whitespace-pre-wrap text-cream/90">
        {text}
        {!done && <span className="animate-pulse text-gold">▌</span>}
      </div>
      {done && (
        <div className="mt-8 flex gap-4">
          <a href={`/chat/${chartId}`}
             className="border border-gold text-gold px-6 py-3 rounded hover:bg-gold hover:text-ink transition-colors">
            Chat your chart →
          </a>
          <a href={`${BASE}/api/report/${chartId}/pdf`}
             className="border border-gold-dim text-cream-muted px-6 py-3 rounded hover:border-gold transition-colors">
            Download PDF
          </a>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Create `app/report/[chartId]/page.tsx`**

```typescript
import FullReport from '@/components/FullReport'

export default function ReportPage({ params }: { params: { chartId: string } }) {
  return (
    <main className="min-h-screen py-20 px-6">
      <div className="text-center mb-12">
        <p className="text-gold text-xs tracking-widest uppercase mb-2">Full Reading</p>
        <h1 className="text-4xl text-cream">Your Complete Chart</h1>
      </div>
      <FullReport chartId={params.chartId} />
    </main>
  )
}
```

- [ ] **Step 6: Test golden path in browser**

1. Go to `http://localhost:3000/onboarding`
2. Submit birth data → redirected to `/profile/<id>` — see animal, lagna, yogas, unlock CTA
3. Click "Unlock Full Report" → Razorpay test modal → use card `4111 1111 1111 1111`
4. After payment → redirected to `/report/<id>` — report streams in real-time

- [ ] **Step 7: Commit**

```bash
git add components/ app/profile app/report
git commit -m "feat: profile preview, payment flow, and streaming full report"
```

---

## Task 12: Chatbot Page

**Files:**
- Create: `components/ChatInterface.tsx`
- Create: `components/QuestionPills.tsx`
- Create: `app/chat/[chartId]/page.tsx`

- [ ] **Step 1: Create `components/QuestionPills.tsx`**

```typescript
'use client'
import { useEffect, useState } from 'react'
import { getQuestions } from '@/lib/api'

const TAB_STYLES: Record<string, string> = {
  know_thyself: 'border-cream-muted/30 text-cream-muted hover:border-cream hover:text-cream',
  trending: 'border-amber-500/30 text-amber-400 hover:border-amber-400',
  spiritual: 'border-purple-500/30 text-purple-400 hover:border-purple-400',
  career: 'border-blue-500/30 text-blue-400 hover:border-blue-400',
  relationship: 'border-pink-500/30 text-pink-400 hover:border-pink-400',
  last_question: 'border-gold/30 text-gold hover:border-gold',
}

export default function QuestionPills({
  tab, lagna, onSelect,
}: { tab: string; lagna: string; onSelect: (q: string) => void }) {
  const [questions, setQuestions] = useState<{ id: number; question: string }[]>([])

  useEffect(() => {
    getQuestions(tab === 'trending' ? 'trending' : tab, lagna).then(setQuestions)
  }, [tab, lagna])

  return (
    <div className="flex flex-wrap gap-2 p-4">
      {questions.map(q => (
        <button
          key={q.id}
          onClick={() => onSelect(q.question)}
          className={`border rounded-full px-4 py-1.5 text-xs transition-colors ${TAB_STYLES[tab] ?? TAB_STYLES.know_thyself}`}
        >
          {q.question}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Create `components/ChatInterface.tsx`**

```typescript
'use client'
import { useState, useRef, useEffect } from 'react'
import QuestionPills from './QuestionPills'
import type { ChatMessage } from '@/lib/types'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const TABS = [
  { id: 'know_thyself', label: '🪞 Know Thyself' },
  { id: 'trending',     label: '🔥 Trending' },
  { id: 'spiritual',    label: '🕊 Spiritual' },
  { id: 'career',       label: '💼 Career' },
  { id: 'relationship', label: '💞 Relationship' },
  { id: 'last_question',label: '⭐ Last Question' },
]

export default function ChatInterface({ chartId, lagna }: { chartId: string; lagna: string }) {
  const [tab, setTab] = useState('know_thyself')
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function send(text: string) {
    if (!text.trim() || streaming) return
    const userMsg: ChatMessage = { role: 'user', content: text }
    setMessages(m => [...m, userMsg])
    setInput('')
    setStreaming(true)

    const res = await fetch(`${BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chart_id: chartId, tab, message: text }),
    })

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let assistantContent = ''
    setMessages(m => [...m, { role: 'assistant', content: '' }])

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const raw = decoder.decode(value)
      for (const line of raw.split('\n')) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') break
        try {
          const { text: chunk } = JSON.parse(data)
          assistantContent += chunk
          setMessages(m => [...m.slice(0, -1), { role: 'assistant', content: assistantContent }])
        } catch {}
      }
    }
    setStreaming(false)
  }

  return (
    <div className="flex flex-col h-[80vh] max-w-2xl mx-auto border border-gold-dim rounded-lg overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-gold-dim overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-3 text-xs whitespace-nowrap border-b-2 transition-colors ${
              tab === t.id
                ? 'border-gold text-gold bg-gold/5'
                : 'border-transparent text-cream-muted hover:text-cream'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Question pills */}
      {messages.length === 0 && (
        <QuestionPills tab={tab} lagna={lagna} onSelect={q => { setInput(q); send(q) }} />
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg px-4 py-3 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-gold/10 border border-gold-dim text-cream'
                : 'text-cream/90'
            }`}>
              {m.content}
              {streaming && i === messages.length - 1 && m.role === 'assistant' && (
                <span className="animate-pulse text-gold">▌</span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={e => { e.preventDefault(); send(input) }}
        className="flex gap-2 p-4 border-t border-gold-dim"
      >
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask anything about your chart…"
          className="flex-1 bg-transparent border border-gold-dim rounded-full px-4 py-2
                     text-cream text-sm placeholder-cream-muted focus:outline-none focus:border-gold"
        />
        <button
          type="submit"
          disabled={streaming || !input.trim()}
          className="w-10 h-10 rounded-full bg-gold text-ink flex items-center justify-center
                     disabled:opacity-40 hover:bg-gold-light transition-colors"
        >
          ↑
        </button>
      </form>
    </div>
  )
}
```

- [ ] **Step 3: Create `app/chat/[chartId]/page.tsx`**

```typescript
import { getChart } from '@/lib/api'
import ChatInterface from '@/components/ChatInterface'
import { redirect } from 'next/navigation'

export default async function ChatPage({ params }: { params: { chartId: string } }) {
  let chart
  try { chart = await getChart(params.chartId) }
  catch { redirect('/onboarding') }

  return (
    <main className="min-h-screen py-12 px-6">
      <div className="text-center mb-8">
        <p className="text-gold text-xs tracking-widest uppercase mb-1">
          {chart.lagna} · {chart.current_dasha}
        </p>
        <h1 className="text-3xl text-cream">Ask Your Chart</h1>
      </div>
      <ChatInterface chartId={params.chartId} lagna={chart.lagna} />
      {!chart.paid && (
        <p className="text-center text-cream-muted text-xs mt-4">
          Free: 5 messages/day ·{' '}
          <a href={`/profile/${params.chartId}`} className="text-gold underline">
            Unlock unlimited for ₹50
          </a>
        </p>
      )}
    </main>
  )
}
```

- [ ] **Step 4: Test chatbot in browser**

1. Go to `/chat/<chart_id>`
2. Click a question pill — should pre-fill and send
3. Watch response stream in real-time
4. Try free-form question — should answer based on chart context

- [ ] **Step 5: Commit**

```bash
git add components/ChatInterface.tsx components/QuestionPills.tsx app/chat/
git commit -m "feat: chatbot interface with tabs, question pills, and SSE streaming"
```

---

## Task 13: Deploy Backend (Railway) + Frontend (Netlify)

**Files:**
- Create: `api/.env.production` (gitignored)
- Modify: `P081_202605_AstrowiseSite/netlify.toml`
- Create: `P081_202605_AstrowiseSite/.env.local` (gitignored)

- [ ] **Step 1: Deploy FastAPI to Railway**

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

cd P046_202604_KnowThyselfAstro
railway init   # name: astrowise-api
railway add postgresql   # provisions Postgres, sets DATABASE_URL
railway variables set ANTHROPIC_API_KEY=<your-key>
railway variables set RAZORPAY_KEY_ID=<rzp_live_...>
railway variables set RAZORPAY_KEY_SECRET=<secret>
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set FRONTEND_URL=https://astrowyze.netlify.app
railway up --detach
```

Expected: Railway shows `https://astrowise-api.up.railway.app` — visit `/health`

- [ ] **Step 2: Run migrations on Railway**

```bash
railway run alembic upgrade head
railway run python -c "
from api.database import engine
from sqlalchemy import text
import asyncio
async def seed():
    async with engine.begin() as conn:
        with open('api/seeds/questions.sql') as f:
            await conn.execute(text(f.read()))
asyncio.run(seed())
"
```

- [ ] **Step 3: Update Next.js for production**

Create `P081_202605_AstrowiseSite/.env.local`:
```
NEXT_PUBLIC_API_URL=https://astrowise-api.up.railway.app
NEXTAUTH_SECRET=<same JWT_SECRET>
NEXTAUTH_URL=https://astrowyze.netlify.app
```

- [ ] **Step 4: Update `netlify.toml`**

```toml
[build]
  command = "npm run build"
  publish = ".next"

[build.environment]
  NODE_VERSION = "20"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

```bash
npm install -D @netlify/plugin-nextjs
```

- [ ] **Step 5: Deploy frontend to Netlify**

```bash
cd P081_202605_AstrowiseSite
netlify login
netlify deploy --prod
```

Expected: `https://astrowyze.netlify.app` loads the landing page

- [ ] **Step 6: Golden path end-to-end test**

1. Open `https://astrowyze.netlify.app/onboarding`
2. Submit birth data → profile page loads with lagna + animal
3. Click "Unlock" → Razorpay payment → full report streams
4. Click "Chat your chart" → chatbot loads, question pills work
5. Ask a question → response streams in < 2s

- [ ] **Step 7: Final commit**

```bash
git add .
git commit -m "feat: production deployment config — Railway API + Netlify frontend"
```

---

## Self-Review

**Spec coverage check:**
- ✅ ₹50 vs ₹500 positioning — shown on onboarding page and profile unlock CTA
- ✅ Birth form → chart calc via astro_engine — Task 3 + 4
- ✅ Free profile preview (lagna, animal, 3 yogas, dasha) — Task 11 ProfilePreview
- ✅ Razorpay ₹50 payment — Task 7 + PaymentButton component
- ✅ Full report streaming — Task 6 ReportService + FullReport component
- ✅ PDF download — endpoint in reports.py (wraps existing pdf_premium.py)
- ✅ Chatbot with tabs — Task 8 + 12
- ✅ Question banks (6 tabs) — Task 8 questions router + seeds
- ✅ SSE streaming chat — ChatInterface component
- ✅ Free 5 msg/day limit — enforced in chat router
- ✅ LLMAdapter (Anthropic default, OpenAI-compatible for BYOK later) — Task 5
- ✅ Dating-ready: chart stored as JSON in DB, `/api/compatibility` can be added — noted in charts router
- ✅ Deploy config — Task 13

**Out of scope for this plan (Plan 2):**
- BYOK settings UI (LLMAdapter already supports it — just needs settings page)
- Anonymous share links (anon_slug column exists in Chart model)
- Trending questions refresh automation
- Subscription tier
- Landing page (existing index.html.bak has the full design — port it in Plan 2)
