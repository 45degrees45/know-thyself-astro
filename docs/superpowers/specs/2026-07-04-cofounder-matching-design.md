# Cofounder Matching & Startup Timing — Design Spec
Date: 2026-07-04

## Overview

A standalone, stateless tool (no login) where two people enter their birth details and receive a Vedic astrological cofounder compatibility score plus startup timing windows. Delivered as an on-screen HTML page using the existing Astrowise design system.

---

## Architecture

```
[docs/cofounder/index.html]         [FastAPI backend]           [astro_engine]
  Person A birth details    ──►  POST /api/cofounder-match  ──►  calc.py × 2
  Person B birth details            (new endpoint)               dasha.py × 2
  Time accuracy flags                    │                        yoga.py × 2
                                         ▼
                                  astro_engine/match.py
                                  (scoring engine)
                                         │
                                         ▼
                                  JSON response
                                         │
                                         ▼
                            [Results rendered in same page]
```

**New files:**
- `astro_engine/match.py` — scoring logic (isolated, no side effects)
- `api/routers/match.py` — FastAPI router with `POST /api/cofounder-match`
- `docs/cofounder/index.html` — frontend, self-contained HTML/JS

**No new database tables.** Results are stateless — not persisted.

---

## API Contract

### `POST /api/cofounder-match`

**Request:**
```json
{
  "person_a": {
    "name": "Alice",
    "date": "1990-03-15",
    "time": "14:30",
    "time_accuracy": "exact",
    "place": "Mumbai, India"
  },
  "person_b": {
    "name": "Bob",
    "date": "1988-11-22",
    "time": "09:00",
    "time_accuracy": "approximate",
    "place": "Bangalore, India"
  }
}
```

`time_accuracy` values: `"exact"` | `"approximate"` (±2h) | `"unknown"` (no time given — defaults to noon)

**Response:**
```json
{
  "overall_score": 74,
  "score_label": "Strong",
  "accuracy_warning": null,
  "dimensions": {
    "working_style":  { "score": 82, "label": "Strong",   "detail": "..." },
    "drive":          { "score": 68, "label": "Good",     "detail": "..." },
    "vision":         { "score": 71, "label": "Good",     "detail": "..." },
    "timing_sync":    { "score": 75, "label": "Strong",   "detail": "..." }
  },
  "role_suggestion": {
    "person_a": "Visionary / Strategy",
    "person_b": "Execution / Operations"
  },
  "startup_timing": {
    "person_a": [
      { "start": "2026-08-01", "end": "2027-02-15", "dasha": "Jupiter/Venus", "quality": "favorable" },
      ...
    ],
    "person_b": [...],
    "overlap_zones": [
      { "start": "2026-08-01", "end": "2027-02-15", "label": "★ Best window" }
    ]
  }
}
```

`accuracy_warning`: `null` | `"person_a_approximate"` | `"person_b_approximate"` | `"person_a_unknown"` | `"person_b_unknown"` | `"both_approximate"` | `"both_unknown"`

---

## Scoring Algorithm (`astro_engine/match.py`)

Overall score = average of 4 dimensions, each 0–100.

### Dimension 1 — Working Style (Moon Nakshatra Tara) 25%

1. Get Moon nakshatra index for each person (0–26)
2. Compute Tara A→B: `(b_nak - a_nak) % 27 % 9 + 1`
3. Compute Tara B→A: `(a_nak - b_nak) % 27 % 9 + 1`
4. Favorable Taras: 2, 4, 6, 8, 9 → score 90
5. Challenging Taras: 1, 3, 5, 7 → score 30
6. Mixed (one each) → score 60
7. Final = average of both directions

### Dimension 2 — Drive & Execution (Mars + Mercury) 25%

Planetary natural friendship table (Vedic):
- Mars friends: Sun, Moon, Jupiter
- Mars enemies: Mercury, Ketu
- Mercury friends: Sun, Venus
- Mercury enemies: Moon, Mars

1. Get Mars sign and Mercury sign for each person
2. Check sign lord friendships: if Person A's Mars sign lord is friend of Person B's Mars sign lord → `+1`; enemy → `-1`; neutral → `0`
3. Do the same for Mercury signs
4. Also check: if Person A's Mars sign == Person B's 10th house sign → `+15 pts bonus`; and vice versa
5. Score map: sum +2 → 90, sum +1 → 75, sum 0 → 60, sum -1 → 45, sum -2 → 30

**Time accuracy note:** If birth time is unknown, skip the H10 Mars bonus (house position unreliable).

### Dimension 3 — Vision & Growth (Jupiter) 25%

Jupiter's Vedic aspects: 5th, 7th, 9th from its position.

1. Get Jupiter sign index for each person
2. Check if Person A's Jupiter aspects (5th/7th/9th sign from A's Jupiter) land on Person B's Sun, Moon, or Jupiter sign → each hit = `+1 pt`
3. Do the same B→A
4. Also check: are their Jupiter signs in mutual natural friendship? → `+1`; enmity → `-1`
5. Score: 4+ pts → 90, 3 pts → 78, 2 pts → 65, 1 pt → 50, 0 pts → 35

### Dimension 4 — Timing Sync (Dasha Overlap) 25%

Favorable dasha periods (Mahadasha or Antardasha lord):
- **Tier 1 Favorable:** Jupiter, Venus
- **Tier 2 Favorable:** Mercury, Sun (if Sun is well-placed in natal — skip this refinement for v1, use universally)
- **Neutral:** Moon, Mars, Saturn
- **Challenging:** Rahu, Ketu

1. Scan next 5 years of dasha periods for each person (from `dasha.py`)
2. Tag each sub-period: `favorable` | `neutral` | `challenging`
3. Find windows where BOTH are in favorable periods simultaneously → `overlap_zones`
4. Score:
   - Overlap ≥ 12 months → 95
   - Overlap 6–11 months → 80
   - Overlap 1–5 months → 65
   - No overlap but both have upcoming favorable periods → 50
   - One or both in challenging period only → 35

### Score Labels
| Range | Label |
|---|---|
| 85–100 | Exceptional |
| 70–84 | Strong |
| 55–69 | Good |
| 40–54 | Workable |
| 0–39 | Challenging |

### Role Suggestion Logic
- Compute a simple "vision score" per person: Jupiter sign dignity (exalted=3, own=2, friendly=1, neutral=0, enemy=-1, debilitated=-2) + Sun sign dignity (same scale)
- Compute "execution score": Mars sign dignity + Saturn sign dignity (same scale)
- Person with higher vision score → "Visionary / Strategy"
- Person with higher execution score → "Execution / Operations"
- If vision and execution scores are within 2 pts of each other → "Co-leads — define roles explicitly"

---

## Time Accuracy Handling

| Scenario | Lagna used? | Accuracy badge |
|---|---|---|
| Exact time | Yes | None |
| Approximate ±2h | Yes, with caveat | "~85% accuracy" in amber |
| No time (unknown) | No | "~70% accuracy — Lagna not used" in rose |

- Unknown time → birth time set to 12:00 noon internally for planet positions
- H10-based bonuses skipped if time is unknown
- Badge shown in hero score card, not blocking — matching always proceeds

---

## Frontend Design (`docs/cofounder/index.html`)

### Form State
- Centered, max-width 680px
- Two cards side by side (Person A / Person B), each with: Name, Date, Time, Place
- Time field has: `☐ Approximate (±2h)` checkbox and `☐ I don't know the birth time` checkbox
- "Calculate Compatibility" CTA button (gold)
- Loading state: animated star pulse with "Reading the stars…"

### Results State

**Hero score card** (full-width, dark gradient):
- Large circular score dial (0–100)
- Score label ("Strong Founding Pair")
- Four dimension bars with scores
- Accuracy badge (if applicable)
- Names + "+"

**Expandable sections** (one per dimension):
- Working Style → plum color
- Drive & Execution → gold color
- Vision & Growth → sage color
- Timing Sync → blue color
- Each expands to show: what was analyzed, the specific placements, what it means in plain language

**Startup Launch Windows** (full-width):
- Two horizontal timelines (Person A, Person B) for next 5 years
- Color-coded segments: green (favorable), amber (neutral), rose (challenging)
- Overlap zones highlighted with gold border + "★ Best window: [dates]" label

**Role Suggestion** (2-col panel):
- Left: Person A name + role badge
- Right: Person B name + role badge

### Design tokens
Inherits the existing Astrowise design system exactly (CSS variables, fonts, panel styles, color semantics).

---

## Out of Scope (v1)
- Email delivery (planned for v2)
- Saving/bookmarking results
- More than 2 people (group cofounder matching)
- Muhurta (electional astrology) for picking a specific launch date
- Mobile-specific timeline layout refinements

---

## Files to Create / Modify

| File | Action |
|---|---|
| `astro_engine/match.py` | Create — scoring engine |
| `api/routers/match.py` | Create — FastAPI router |
| `api/main.py` | Modify — add `from api.routers import match` and `app.include_router(match.router, prefix="/api")` |
| `docs/cofounder/index.html` | Create — frontend |
