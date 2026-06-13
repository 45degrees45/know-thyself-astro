# AstroWise Web Platform — Design Spec
**Date:** 2026-06-13  
**Status:** Approved  
**Scope:** Know Thyself MVP — v1

---

## 1. Problem & Positioning

A traditional Vedic astrologer costs ₹500 for a 30-minute consultation. AstroWise delivers the same depth of insight — instantly, in writing, with chat follow-up — for ₹50.

**Tagline:** *"The clarity of an astrologer. The cost of a chai."*

The existing `astro_engine/` (Swiss Ephemeris + Lahiri ayanamsha) is the calculation ground truth. This project wraps it in a web platform accessible to anyone, not just people who email Goldy.

---

## 2. Existing Infrastructure (Build On, Don't Rebuild)

| Asset | Location | Status |
|---|---|---|
| Landing page | `P081_202605_AstrowiseSite` — Netlify | Live, dark gold brand, Cormorant Garamond |
| Netlify Function | `P081/netlify/functions/submit.js` | Wired, form submit handler |
| EC2 backend | `i-00ba016421926b357`, ap-south-1 Mumbai | Running `astro_engine` via systemd |
| Batch pipeline | Google Sheets → Apps Script → Lambda → EC2 → astro_engine | Phase 1 complete |
| astro_engine | `P046_202604_KnowThyselfAstro/astro_engine/` | Ground truth calc library |

**Build strategy:** FastAPI is added to the existing Mumbai EC2. The Next.js frontend replaces / extends the existing Netlify landing page. PostgreSQL is added to the EC2 (or Railway). The existing batch pipeline continues to run alongside.

---

## 3. Architecture Overview

```
Browser (Next.js → Netlify or Vercel)
    ↓ HTTPS
FastAPI (Python) on existing EC2 ap-south-1 Mumbai
    ↓  imports directly
astro_engine/ (Swiss Ephemeris, already on EC2)
    ↓
PostgreSQL (users, charts, chat history, question banks)
    ↓
LLMAdapter (routes to NIM / Anthropic / user's BYOK key)
```

**Key principle:** `astro_engine/` is not rewritten. FastAPI imports and calls it directly as a Python library. The web layer is purely additive.

**Dating-ready from day 1:** user accounts store charts as structured JSON in DB; a `/api/compatibility` endpoint wraps `astro_engine/compare.py` even though the dating UI is out of scope for v1.

---

## 3. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js 14 (App Router) | SSR for SEO on landing page; React for chat/profile UI |
| Styling | Tailwind CSS | Matches brand speed requirements |
| Backend | FastAPI (Python 3.11+) | Same language as astro_engine; async, fast, typed |
| Database | PostgreSQL | Handles JSON chart data; scales to matching queries later |
| Payments | Razorpay | INR-native, easy React integration |
| Inference | NIM (llama-3.1-70b) default; BYOK fallback | Zero per-token cost for platform |
| Deployment | Netlify (frontend, existing) + existing EC2 Mumbai (API + DB) | Reuse existing infra |
| Auth | NextAuth.js (email + Google OAuth) | No friction onboarding |

---

## 4. User Journey

```
Landing → Onboarding (birth data) → Chart calc → Free Profile Preview
→ [Unlock for ₹50] → Full Report + PDF → Chat (5 free/day, unlimited paid)
→ Share anon link
```

**Later (v2):** Dating vertical plugs in here — "Find your match" CTA after profile.  
**Later (v3):** Astro counselling (human sessions) as a premium upsell.

---

## 5. Features — MVP Scope

### 5.1 Birth Data Onboarding
- Fields: Name, Date of Birth, Time of Birth, Place of Birth
- Place autocomplete via geocoding (existing `astro_engine/geo.py`)
- Validation: time required (lagna sensitive to minutes)
- On submit: chart calculated, stored in DB as JSON, user account created

### 5.2 Free Profile Preview
Shown to all users before payment:
- Lagna sign + degree
- Spirit animal + 2-line description
- 3 yogas (teaser)
- Current dasha period (main only, no sub-periods)
- One-line career hint, one-line relationship hint

### 5.3 Full Report — ₹50 (one-time)
After Razorpay payment:
- Full natal reading (all sections from existing `profile_html.py`)
- Career deep-dive: best domains, timing windows, leadership style
- Relationship style: how you love, partner profile, compatibility type
- Spiritual pointers: soul lesson, karma, dharma, best practice
- Remedies: Tier 1 (Universal) + Tier 3 (Neuroscience/CBT) always shown; Tier 2 (Vedic) optional
- Weekly practice calendar (Mon–Sun grid)
- PDF download
- Shareable anonymous link (anon nickname: "The [Adjective] [Animal], [age]")

### 5.4 Chart Chatbot
Interface: tabbed question pills + free-form input. Tabs:

| Tab | Description |
|---|---|
| 🪞 Know Thyself | Core personality, shadow, patterns, ego |
| 🔥 Trending | Most-clicked questions this week, personalised by lagna |
| 🕊 Spiritual Pointers | Soul lesson, karma, dharma, past-life indicators |
| 💼 Career | Domains, timing, leadership vs support, money blocks |
| 💞 Relationship Style | Attachment, partner profile, triggers, windows |
| ⭐ Last Question | One editorial question per week — philosophical, universal |

**System prompt:** User's full chart summary (lagna, all planets, dashas, yogas) injected as structured context. Model "knows" their chart without user re-explaining.

**Free tier:** 5 messages/day across all tabs.  
**Paid tier:** Unlimited. Unlocked with ₹50 report purchase.  
**Streaming:** SSE (Server-Sent Events) for real-time feel.  
**History:** Last 30 days stored per user.

### 5.5 BYOK — Bring Your Own Model Key
- Settings → "AI Engine" section
- Supported providers: Google Gemini, OpenAI GPT-4o, Claude API, Mistral, any OpenAI-compatible endpoint
- Keys stored AES-256 encrypted in DB, never logged
- "Your key, your privacy" badge shown in chat when BYOK active
- Platform default: NVIDIA NIM (llama-3.1-70b-instruct) → fallback: Anthropic

**LLMAdapter interface:**
```python
class LLMAdapter:
    def chat(self, messages, system, stream=True) -> AsyncIterator[str]: ...
    def complete(self, prompt, system) -> str: ...
```
All report generation and chatbot calls go through `LLMAdapter`. Provider is resolved at request time from user config.

### 5.6 User Accounts
- Email + Google OAuth (NextAuth.js)
- Stored: birth data, chart JSON, payment status, BYOK config, chat history
- One account = one chart (v1); multiple charts in v2
- Privacy: profile default = private; user can set to anon-shareable

### 5.7 Anonymous Share Link
- Format: `astrowise.app/s/[slug]`
- Removes: real name, birth date, birth time, birth place
- Anon identity: "The [Adjective] [Animal], [Age]" (e.g. "The Velvet Lioness, 25")
- Keeps: all interpretations, yogas, dasha, animal, remedies
- Anyone can view without account

### 5.8 Pricing

| Tier | Price | Includes |
|---|---|---|
| Free | ₹0 | Profile preview, 5 chat msgs/day, Know Thyself Qs only |
| Full Report | ₹50 | Full PDF, all question banks, unlimited chat, BYOK, share link |
| Subscription | ₹149/mo | Monthly report, transit alerts, priority chat, everything in Full |

**Positioning always shown:** "vs ₹500 with an astrologer"

---

## 6. Data Model (PostgreSQL)

```sql
users (id, email, name, google_id, created_at, payment_status)
charts (id, user_id, birth_date, birth_time, birth_place, lat, lon, tz, 
        chart_json, created_at)
chat_messages (id, user_id, tab, role, content, created_at)
question_bank (id, tab, question_text, click_count, lagna_filter, active)
weekly_question (id, question_text, week_of, created_by)
byok_keys (id, user_id, provider, encrypted_key, created_at)
```

`chart_json` stores the full output of `calculate_chart()` — lagna, planets, dashas, yogas — so chart recalculation is never needed after onboarding.

---

## 7. API Endpoints (FastAPI)

```
POST /api/chart          — calculate + store chart (onboarding)
GET  /api/chart/{id}     — fetch chart for profile page
POST /api/report/unlock  — verify Razorpay payment, unlock full report
GET  /api/report/{id}    — generate + stream full report (LLMAdapter)
GET  /api/report/{id}/pdf — generate PDF (existing pdf_premium.py)
POST /api/chat           — chat message (streamed via SSE, LLMAdapter)
GET  /api/questions/{tab} — fetch question bank for tab
GET  /api/questions/trending — top questions this week by lagna
GET  /api/share/{slug}   — fetch anon profile
POST /api/byok           — save/update BYOK key
GET  /api/compatibility/{id1}/{id2} — compatibility score (dating-ready, no UI yet)
```

---

## 8. Out of Scope — v1

- Dating / matching UI
- Co-founder matching
- Friendship matching  
- Mobile app
- Astro counselling / human sessions (v3)
- Transits / daily readings
- Multiple charts per account
- Admin dashboard for question bank management (manual DB edits for now)

---

## 9. Phased Delivery

| Phase | Deliverable |
|---|---|
| P1 | FastAPI skeleton + astro_engine integration + DB schema |
| P2 | Next.js frontend: onboarding form + free profile page |
| P3 | Razorpay payment + full report generation + PDF |
| P4 | Chatbot (tabs, question pills, SSE streaming) |
| P5 | BYOK settings + LLMAdapter multi-provider |
| P6 | Anonymous share links |
| P7 | Trending questions engine + Last Question editorial tab |
| P8 | Subscription tier + monthly reports |
