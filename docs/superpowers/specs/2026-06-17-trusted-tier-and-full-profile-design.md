# AstroWise — Trusted Friends Tier + Full Profile Reading

**Date:** 2026-06-17  
**Status:** Approved for implementation

---

## Overview

Two features shipped together:

1. **Full Profile Reading** — every user (free) gets the complete natal reading HTML. Chat is the paid feature.
2. **Trusted Friends Tier** — selected users (past clients, close friends) get free permanent chat access with own-chart restrictions.

---

## Product Structure (post-ship)

| Tier | Profile Reading | Chat |
|---|---|---|
| Free (everyone) | Full natal reading (HTML) | ✗ |
| Paid | Full natal reading | ✓ |
| Trusted | Full natal reading | ✓ own chart only + compatibility |

---

## Architecture Note

The app is stateless — no JWT, no session login. The `chart_id` IS the session identifier. All access control is chart-id-based. The existing `AccessCode` table handles tiered access; we extend it rather than adding a separate auth layer.

---

## Feature 1 — Full Profile Reading

### What changes

Profile page gains a **"View Full Reading"** button → opens complete natal HTML in new tab.  
HTML is generated from `chart_json` (no external LLM call — pure Python template) at chart creation and stored in DB.

### Backend

**Model change — `Chart`:**
```python
profile_html: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**Schema change — `ChartSummary`:**
```python
profile_html_ready: bool = False
trusted: bool = False
```

**New endpoint:**
```
GET /api/chart/{id}/reading
```
- No auth required (chart_id is the access token)
- Returns `Content-Type: text/html` from `chart.profile_html`
- Returns 404 if `profile_html` is None

**Profile HTML generation:**
- `AstroService.generate_profile_html(chart_json, name) -> str`
- Called async (background thread) after `POST /api/chart` commits
- Saves result to `chart.profile_html` in a separate DB session
- Uses design system: Cormorant Garamond + DM Sans, dark cosmic theme, gold/plum/rose/sage tokens
- Sections: Planet Table · Yogas · Dasha · Spirit Animal · Houses summary
- No Gemini/Groq needed — all data comes from chart_json

**Updated `POST /api/chart`:**
- After commit: `asyncio.create_task(generate_and_save_profile_html(chart.id, chart_json, user.name))`
- Returns `profile_html_ready: False` immediately (generated async)

**Updated `GET /api/chart/{id}`:**
- Returns `profile_html_ready: chart.profile_html is not None`
- Returns `trusted: <bool>` (see Feature 2)

### Frontend (`/profile/[chartId]`)

- Add "View Full Reading" button → `/api/chart/{chartId}/reading` in `target="_blank"`
- Button shown always; if not ready yet (first few seconds), show as disabled with "Preparing…"
- Poll `GET /api/chart/{id}` until `profile_html_ready: true` (max 30s, 2s interval)

---

## Feature 2 — Trusted Friends Tier

### Approach: Extend AccessCode

Extend the existing `AccessCode` table rather than adding a `User.trusted` field:

```python
# New columns on AccessCode:
type: Mapped[str] = mapped_column(String, default="demo")   # 'demo' | 'trusted'
note: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Ruhi - past client"
```

- **Demo codes:** `type='demo'`, `expires_at = now + 10min`, single-use per chart
- **Trusted codes:** `type='trusted'`, `expires_at = NULL` (permanent), single-use per chart

### New Table — `TrustedEmailWhitelist`

```python
class TrustedEmailWhitelist(Base):
    __tablename__ = "trusted_email_whitelist"
    email: Mapped[str] = mapped_column(String, primary_key=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
```

### Access Grant Flows

**Invite code path:**
1. Admin calls `POST /api/admin/trusted-codes/generate` → returns N codes with `type='trusted'`, no chart_id yet
2. Jo sends code to friend (WhatsApp/email)
3. Friend creates chart → gets chart_id
4. Friend enters code at onboarding → `POST /api/demo/redeem` (extended) → links code to chart_id, no expiry set (NULL)
5. Code becomes single-use after redemption

**Email whitelist path:**
1. Admin calls `POST /api/admin/whitelist/add` with email
2. When `POST /api/chart` creates chart and the email matches whitelist → auto-creates trusted AccessCode for that chart_id
3. No action needed from the user — they just arrive and have access

### Updated Chat Access Logic

```python
# In chat router — after checking user.paid:
if not chart.user.paid:
    now = datetime.now(timezone.utc)
    code_result = await db.execute(
        select(AccessCode).where(
            AccessCode.chart_id == req.chart_id,
            or_(
                and_(AccessCode.type == 'demo', AccessCode.expires_at > now),
                and_(AccessCode.type == 'trusted', AccessCode.expires_at == None),
            )
        )
    )
    access = code_result.scalar_one_or_none()
    is_trusted = access is not None and access.type == 'trusted'
    has_access = access is not None
    if not has_access:
        # check free daily limit as before
        ...
```

**Chart restriction for trusted users:** Enforced by design — the trusted code is linked to ONE specific chart_id. They can only chat on the chart they redeemed the code against.

**Compatibility system prompt — appended for trusted users:**
```
This user has access to their own natal chart only. If they reference another person's 
birth details (date, time, place) in the context of compatibility or relationship 
matching, you may provide a brief synastry analysis. Do not provide a full standalone 
natal reading for any other person.
```

### Admin Endpoints

All protected by `ADMIN_SECRET` env var.

```
POST /api/admin/trusted-codes/generate
  Body: { "count": int, "note": str? }
  Returns: [{ "code": str }]

POST /api/admin/whitelist/add
  Body: { "email": str, "note": str? }
  Returns: { "ok": true }

GET /api/admin/trusted-users
  Returns: [{ "email", "chart_id", "note", "created_at" }]
```

### Updated `ChartSummary.trusted`

- `POST /api/chart`: check if newly created trusted code was auto-applied → return `trusted: True`
- `GET /api/chart/{id}`: query AccessCode for this chart_id with `type='trusted'` → return `trusted: True/False`

### Frontend Changes

**Onboarding page:**
- Add "Have an invite code?" collapsible input (below existing demo code input)
- Uses same `POST /api/demo/redeem` endpoint — trusted codes work through the same flow

**Profile page (`/profile/[chartId]`):**
- If `trusted: true` in ChartSummary → show "Chat with your chart" button directly (no payment CTA)
- If `paid: true` → same as now
- Both states can coexist; trusted takes visual precedence

---

## Migration Plan

1. `ALTER TABLE charts ADD COLUMN profile_html TEXT`
2. `ALTER TABLE access_codes ADD COLUMN type VARCHAR DEFAULT 'demo'`
3. `ALTER TABLE access_codes ADD COLUMN note VARCHAR`
4. `CREATE TABLE trusted_email_whitelist (...)`
5. `railway variables set ADMIN_SECRET=<secret>` in Railway

---

## Out of Scope

- Compatibility tab UI (future)
- Trusted user message quotas (future)
- Trusted code expiry dates (future)
- Razorpay payment integration (not touched)
