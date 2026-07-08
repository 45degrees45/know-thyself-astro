# Astrowise — Claude Instructions

## Workflow (ALWAYS FOLLOW)

### Primary Path — astro_engine/ (use this for ALL report generation)
- Swiss Ephemeris + Lahiri ayanamsha — mathematically precise
- Run with: `.venv/bin/python3 astro_engine/main.py --sheet` (all users) or `--name "X" ...`
- Or for natal reading: `.venv/bin/python3 astro_engine/natal_reading.py --name "X" ...`
- **This is the GROUND TRUTH for all chart data** (lagna, planet positions, dasha, yogas)
- Delivery: generate PDF + send via email using `send_html_report.py --all` or inline script

### ChatGPT Playwright (gpt_astro_automation.py) — verification + HTML only
- **Do NOT use as primary generation path**
- Use only to verify interpretations against astro_engine output
- When it sends email, it sends **HTML inline** (not PDF attachment) — `send_html=True`
- Cannot run on EC2 (ChatGPT blocks those IPs)

### Delivery Commands
```bash
# Send HTML email for all (primary delivery after astro_engine generates reports)
.venv/bin/python3 send_html_report.py --all

# Send HTML email for one person
.venv/bin/python3 send_html_report.py --name "X"
```

### Ground Truth Check
- If a stale output file exists in `astro_engine/output/` with wrong data, DELETE it and re-run
- Always verify Lagna matches expectation before sending

**Never trust an existing output file without checking the lagna matches expectations.**

## Key Commands
```bash
# Always use venv python — 'python' command not found
../.venv/bin/python3 astro_engine/main.py --sheet          # all users, monthly
../.venv/bin/python3 astro_engine/main.py --name "X" ...   # single person, monthly
../.venv/bin/python3 astro_engine/natal_reading.py ...      # natal deep reading

# Re-authenticate Gmail (if token expired)
../.venv/bin/python3 gpt_astro_automation.py --gmail-auth

# Re-login to ChatGPT (session expires ~30 days)
../.venv/bin/python3 gpt_astro_automation.py --login
```

## Ground Truth: Kunal Agarwal
- Birth: 10-Sep-1993, 18:50, Alwar, Rajasthan
- Correct Lagna: **Pisces 0.9°** (NOT Scorpio — old engine had a bug)
- Current Dasha (Apr 2026): Saturn / Saturn / Rahu
- 8 yogas including Bhadra, Gajakesari, 3 Raja Yogas

## Known Issues
- Old engine (Playwright) cannot run on EC2 — ChatGPT blocks those IPs
- astro_engine output files skip re-generation if file exists — delete stale files first
- Gmail token (gmail_token.json) expires; re-run `--gmail-auth` if email fails
- Twilio WhatsApp credentials were expired as of Apr 2026 — verify before use

---

## Group Analysis Dashboards ("Startup Umbrella")

Four group generators live in the project root. Run them whenever a new profile is added.

### Generators & Output Files

| Generator | Output | URL |
|---|---|---|
| `generate_profiles_dashboard.py` | `docs/profiles_skills_dashboard.html` | `/profiles_skills_dashboard.html` |
| `generate_spiritual_paths.py` | `docs/spiritual_paths.html` | `/spiritual_paths.html` |
| `generate_spiritual_paths_ml.py` | `docs/spiritual_paths_ml.html` | `/spiritual_paths_ml.html` |
| `generate_human_design.py` | `docs/human_design.html` | `/human_design.html` |

Base GitHub Pages URL: `https://45degrees45.github.io/know-thyself-astro/`

### Regeneration Commands
```bash
.venv/bin/python3 generate_profiles_dashboard.py
.venv/bin/python3 generate_spiritual_paths.py
.venv/bin/python3 generate_human_design.py
# ML only when needed:
.venv/bin/python3 generate_spiritual_paths_ml.py
```

### Adding a New Profile — Touch These 4 Things
Every generator has **two** places to update:
1. **`PROFILES` list** — tuple with (name, dob, tob, lat, lon, tz, lagna, dasha, animal, gender) — or (name, dob, tob, lat, lon, tz, animal, gender) for HD
2. **`ANON` dict** — `"Name": ("The Codename", "🦁")` in spiritual paths; `"Name": "The Codename"` in HD
3. **`SPIRITUAL` dict** — full spiritual path entry (spiritual paths generator only)
4. **`KNOWN_CONTEXT` dict** — yogas + risks (profiles dashboard only)

**Key rule: `ANON` keys are the real name; values are the display name + emoji. Changing one dict entry anonymizes that person everywhere in that generator.**

### Startup Fitness Tiers (profiles_dashboard)
- 🚀 **Startup-Ready** (≥68): strong enough to found alone
- 🌱 **Founder-Track** (55–67): needs right co-founder
- 🔄 **Conditional** (42–54): better as early employee or co-founder #3
- 🏢 **Specialist** (<42): thrives in structured role

Scoring weights: Lagna lord (25%) + 10th lord (20%) + Mars (15%) + Sun (10%) + Dasha quality (20%) + avg skill (10%)

### Skill Domains
- **Product**: Jupiter + Venus + Mercury dignity scores
- **Operations**: Saturn + Mars + Mercury dignity scores
- **Sales**: Venus + Mercury + Moon dignity scores
- **Marketing**: Venus + Mercury + Sun dignity scores
- **Finance**: Jupiter + Saturn + Venus dignity scores

---

## Spiritual Paths Classification

Five path types. Every new profile must be classified into exactly one.

| Path | Color | Key Indicators |
|---|---|---|
| **Dharmic** | Gold `#c49e40` | Leo/Sagittarius/Aries Lagna, Sun in H9/H5, DKA Yoga, Jupiter as Lagna lord |
| **Jnana** | Blue `#5b8fd4` | Mercury strong, Gemini/Virgo/Aquarius Lagna, Ketu in H1, Bhadra Yoga |
| **Bhakti** | Rose `#c4607a` | Venus strong, Pisces/Cancer/Taurus Lagna, Moon in H4/H8, Jupiter in Lagna |
| **Karma** | Sage `#5a8f72` | Saturn Yoga Karaka, H6 emphasis, service yogas, exalted Saturn |
| **Mystic** | Plum `#7c5cbf` | H8/H12 emphasis, Scorpio Lagna, Ketu strong, Uttara Bhadrapada Moon |

### Spiritual Entry Structure
```python
"Name": {
    "path": "Dharmic",             # one of the 5 keys above
    "archetype": "The ...",        # poetic title linking chart to essence
    "indicators": ["H7 lord...", "..."],  # 3-4 specific placements
    "description": "...",          # 3-4 sentences, evidence-first
    "strengths": ["...", "..."],   # 3 items
    "shadow": "...",               # 1 sentence, honest
    "practices": ["...", "..."],   # 3 concrete practices
},
```

---

## Human Design (HD) Bodygraph

**CRITICAL**: HD uses **tropical zodiac** (NOT sidereal Lahiri). Different system from Jyotish.

### Engine Location
- Calculation: `astro_engine/human_design.py`
- Generator: `generate_human_design.py` → `docs/human_design.html`
- Uses existing Swiss Ephemeris (tropical mode) — no separate library needed

### HD Types & Startup Founder Roles
| Type | % Pop | Icon | Founder Role | Strategy |
|---|---|---|---|---|
| **Generator** | ~37% | ⚡ | The Builder | Wait to respond |
| **Manifesting Generator** | ~32% | 🔥 | The Catalyst | Respond then inform |
| **Manifestor** | ~9% | 🚀 | The Pioneer | Inform before acting |
| **Projector** | ~20% | 🎯 | The Strategist | Wait for invitation |
| **Reflector** | ~1% | 🔮 | The Mirror | Wait 28-day lunar cycle |

### Authority Hierarchy (determined by which centers are defined)
Emotional → Sacral → Splenic → Ego-Manifested → Self-Projected → Mental → No Inner Authority

### Profile Notation
`Personality Sun line / Design Sun line` — e.g., 4/5 = line 4 (Opportunist) over line 5 (Heretic)

### Design Date Calculation
~88.736° of Sun travel BEFORE birth (binary search). This is ~3 months prior to birth. The engine computes it with 30 iterations of precision.

### Adding a New Person to HD Dashboard
Only 2 things needed:
```python
# In PROFILES list:
("Name", "YYYY-MM-DD", "HH:MM", lat, lon, "Timezone/Zone", "🦁", "M/F"),

# In ANON dict:
"Name": "The Codename",
```

---

## New Profile Workflow (AUTO-GENERATE — do not wait to be asked)

On every new birth profile (name + DOB + time + place), immediately generate ALL of:

1. **Core Nature** — personality, dominant planets, lagna traits, emotional style
2. **Career** — best domains, strengths, supporting yogas
3. **Relationships** — 7th house, Venus, partner profile, relationship style
4. **Fun Facts** — 3–5 surprising chart details (unusual placements, rare yogas, standout nakshatras)
5. **Career Window** — specific dasha/transit periods for breakthroughs
6. **Marriage Window** — dasha/transit windows for committed relationships
7. **Negative Traits** — shadow side, challenging yogas (honest but constructive)
8. **Animal Connection** — identify spirit animal from Moon nakshatra + Lagna sign + dominant yoga:
   - Pick ONE primary animal (+ one secondary if strongly relevant)
   - Write 2–3 sentences linking the animal to specific placements and their nature
   - Weave the animal as a metaphor through Core Nature, Career, Relationships descriptions
9. **Meta AI Image Prompt** — ready-to-copy prompt for meta.ai spirit animal portrait:
   - Mystical dark cosmic background, animal glowing with astrological symbolism
   - Include Lagna symbol, Moon sign, key planet glyphs as glowing elements
   - Style: painterly surreal digital art, ultra detailed, --ar 3:4
   - Present in a code block (copy-paste ready)
10. **Beautiful HTML profile** — run `astro_engine/profile_html.py --gender`:
    - Saved to `astro_engine/output/{Name}/{Name}_profile.html`
    - HTML must include animal section with large emoji icon (🦢 🐘 🦁 🐎 🦅 🐅 🦌 🐬)
    - Share local network URL: `http://192.168.1.102:8765/`

11. **Profile folder** — create `docs/{Name}/` for every person; all their files live here:
    - `docs/{Name}/{Name}_profile.html` — full named profile
    - `docs/{Name}/{Name}_anon.html` — anonymous version
    - Portraits, session notes, remedies HTML added here over time

12. **GitHub Pages upload** — publish after HTML is generated:
    ```bash
    mkdir -p docs/{Name}
    cp astro_engine/output/{Name}/{Name}_profile.html docs/{Name}/{Name}_profile.html
    # generate anon version, then:
    git add docs/{Name}/
    git commit -m "Add {Name} profile to GitHub Pages"
    git push
    ```
    - Named link: `https://45degrees45.github.io/know-thyself-astro/{Name}/{Name}_profile.html`
    - Anonymous link: `https://45degrees45.github.io/know-thyself-astro/{Name}/{Name}_anon.html`
    - All docs/ files have `noindex, nofollow` — not indexed by Google

13. **Anonymous version** — second HTML with identifying info removed:
    - Remove: full name → "Chart Reading", birth date, birth time, birth place
    - Keep everything substantive: interpretations, yogas, dasha, animal, remedies
    - Replace name in body text with "this chart" / "the native"
    - Use: person shares publicly without revealing birth details

14. **Notion entry** — add a page under `🔮 Mysticism` (Notion page ID: `367764ca-b288-81fe-84f4-def874d878d7`):
    - Page title: `{Name} — Jyotish Profile`
    - Icon: the person's spirit animal emoji
    - Content: Lagna, current dasha, spirit animal, key yogas, and **both GitHub Pages links** (named + anon)
    - This makes all profiles accessible from Notion from any device
    - Use the `mcp__claude_ai_Notion__notion-create-pages` tool with `parent.page_id = "367764cab28881fe84f4def874d878d7"`

---

## Deep Readings Workflow

When a user asks questions about specific chart topics (relationship, intuition, husband, divorce, mother-in-law, career, health, etc.), follow this methodology:

### Reading Approach — Always Evidence-First
Every statement must trace to a specific placement. Format: **[Placement]** → what it means → applied to this person. Never interpretation without named house/planet/nakshatra.

### Topic Lookup Table — What to Examine

| Topic | Primary Houses | Key Planets | Notes |
|---|---|---|---|
| **Relationship themes** | H7, H2, H5, H8 | Venus, Moon, Mars (7th lord), 5th lord | Also check Lagna lord's placement |
| **Intuition / psychic** | H8, H12, H4 | Moon (nakshatra), Ketu, 12th lord, 4th lord | Moon nakshatra = intuition type |
| **Husband** | H7, H10 (from H7 = H4 perspective) | Jupiter (karaka for female), 7th lord, Darakaraka | Darakaraka = lowest-degree planet (excl. nodes) |
| **Wife** | H7 | Venus (karaka for male), 7th lord, Darakaraka | — |
| **Marriage yogas** | H7, H1, H5, H8 | Venus, 7th lord, Jupiter aspect on H7, Rahu-Ketu axis | Check Viparita Raja if Venus/Mercury in H8 |
| **Divorce / separation** | H7, H2, H12 | Malefics on H7, 7th lord in dusthana, Venus affliction | Jupiter's aspect on H7 = strongest protection |
| **Mother-in-law** | H10 (4th from H7), H8 | H10 lord, Ketu with H10 lord, Saturn aspect on H10 | H8 = in-law environment generally |
| **Father-in-law** | H4 from H7 = H10... check H9 from H7 = H3 | H3 lord | — |
| **Career** | H10, H6, H2 | 10th lord, Saturn, Sun | Yogas in H10 or aspecting it |
| **Finance** | H2, H11, H8 | 2nd lord, 11th lord, Jupiter | H8 = hidden wealth / inheritance |
| **Health** | H1, H6, H8 | Lagna lord, 6th lord, Mars | Nakshatras of Lagna / Moon for body type |
| **Spirituality** | H9, H12, H4 | Jupiter, Ketu, 9th lord | 12th lord in H8 = subconscious access |
| **Children** | H5 | Jupiter, 5th lord | Ketu in H5 = past-life connection to children |
| **Mother** | H4 | Moon, 4th lord | Moon nakshatra = mother's nature |
| **Father** | H9 | Sun, 9th lord | Sun nakshatra = father's nature |
| **Siblings** | H3 | Mars (brothers), Mercury (sisters), 3rd lord | — |

### Nakshatra Reading Depth
Always name the nakshatra when it adds meaning. For key planets (Moon, Lagna lord, 7th lord, Darakaraka) always include:
- Nakshatra name + ruling planet
- Shakti (power/quality) of the nakshatra
- Deity and its relevance
- Pada (1-4) if it adds precision

### Darakaraka Calculation
Exclude Rahu and Ketu. Among Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn — the planet with the **lowest degree** (0°–30° within its sign) is the Darakaraka. It is the soul-level significator of the spouse.

### After a Deep Reading Session — Generate Session HTML
When a meaningful set of deep readings has been done in a session (3+ topics), generate a session readings HTML:

**File:** `docs/{Name}/{Name}_session_readings.html`

**Layout:** Sticky sidebar + scrollable main (CSS Grid, `260px 1fr`)
- Sidebar: spirit animal emoji, chart stats, chapter nav links with icons
- Main: hero intro + chapters with `scroll-margin-top`

**Chapter Structure:**
```
chapter-header (icon box + h2 with eyebrow small label)
  → section cards (each placement as its own card)
  → reading-table (summary of all factors)
  → callout box (honest bottom-line assessment)
```

**Color system (consistent across all reading HTMLs):**
- Gold `#c49e40` — general/neutral
- Plum `#7c5cbf` — intuition, mystery, spiritual
- Rose `#c4607a` — risk, challenge, divorce
- Sage `#5a8f72` — positive, protective, husband
- Blue `#5b8fd4` — neuroscience, analysis

**Callout types:**
- `.callout-gold` — core signature / summary
- `.callout-plum` — spiritual / intuitive insight
- `.callout-rose` — warning / risk / honest assessment
- `.callout-sage` — protective factor / positive outcome

**Badge types:**
- `.badge-risk` — rose — separation risk / challenge
- `.badge-protect` — sage — protective factor
- `.badge-mixed` — gold — mixed/complex

**After creating:**
1. Add `<meta name="robots" content="noindex, nofollow">` in head
2. `git add docs/{Name}/{Name}_session_readings.html`
3. `git commit -m "Add {Name} session readings HTML"`
4. `git push`
5. Share: `https://45degrees45.github.io/know-thyself-astro/{Name}/{Name}_session_readings.html`

---

## Design System — All Astrowise HTMLs

Every HTML file (profile, session readings, remedies, anonymous) uses this unified design system. Never deviate without a specific reason.

### Design Tokens (CSS Variables)
```css
:root {
  --bg:      #0b0b18;                     /* page background */
  --surface: rgba(255,255,255,0.035);     /* panel fill */
  --border:  rgba(196,158,64,0.18);       /* default gold border */
  --gold:    #c49e40;                     /* primary accent */
  --gold2:   #e8c96a;                     /* bright gold (highlights) */
  --cream:   #f0e8d8;                     /* body text */
  --muted:   rgba(240,232,216,0.55);      /* secondary text */
  --plum:    #7c5cbf;                     /* spiritual / dasha */
  --rose:    #c4607a;                     /* shadow / challenge / risk */
  --sage:    #5a8f72;                     /* positive / protective */
  --blue:    #5b8fd4;                     /* neuroscience / analytical */
  --shadow:  0 20px 60px rgba(0,0,0,0.45);
  --r:       22px;                        /* default panel border-radius */
}
```

### Semantic Color Usage
| Color | Use For |
|---|---|
| **Gold** `#c49e40` | Accent, borders, labels, neutral sections, eyebrows |
| **Gold2** `#e8c96a` | Bright highlights, period windows, star elements |
| **Plum** `#7c5cbf` | Dasha, spiritual, intuition, mystery chapters |
| **Rose** `#c4607a` | Shadow side, challenges, divorce risk, warnings |
| **Sage** `#5a8f72` | Positive outcomes, protective yogas, antidotes |
| **Blue** `#5b8fd4` | Neuroscience / CBT / NLP / biohacking tier |
| **Cream** `#f0e8d8` | Primary body text, headings |
| **Muted** `rgba(240,232,216,0.55)` | Secondary text, captions, notes |

### Typography
```css
/* Headings, hero, serifs */
font-family: 'Cormorant Garamond', serif;
weights: 300 (hero/display), 400 (panel h2), 600 (emphasis)

/* Body, labels, UI */
font-family: 'DM Sans', system-ui, sans-serif;
weights: 300, 400, 500, 600

/* Google Fonts import (always both) */
https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500;600&display=swap
```

### Background System
```css
/* Always fixed, always two radial gradients: plum top-left + gold bottom-right */
background-color: #0b0b18;
background-image:
  radial-gradient(ellipse 80% 50% at 20% -10%, rgba(124,92,191,0.18), transparent),
  radial-gradient(ellipse 60% 40% at 80% 110%, rgba(196,158,64,0.12), transparent);
background-attachment: fixed;
```

### Hero Block (profile HTML only)
```css
.hero {
  border-radius: 28px;
  padding: 48px 44px 38px;
  background: linear-gradient(140deg,
    rgba(28,18,56,0.98) 0%,
    rgba(44,24,72,0.96) 45%,
    rgba(80,38,58,0.92) 100%);
  border: 1px solid rgba(196,158,64,0.22);
  box-shadow: var(--shadow);
}
/* Watermark symbol (Lagna glyph) */
.hero-symbol { position:absolute; right:36px; top:24px; font-size:180px; color:rgba(196,158,64,0.07); }
/* Glow orb */
.hero-glow { position:absolute; right:-60px; bottom:-80px; width:340px; height:340px; border-radius:50%;
  background: radial-gradient(circle, rgba(196,158,64,0.15), transparent 65%); }
/* Name */
.hero h1 { font-family: Cormorant Garamond; font-size: clamp(3rem,6vw,5.5rem); font-weight:300; color:#fff8f0; }
/* Lagna line */
.lagna-line { font-family: Cormorant Garamond; font-size:1.3rem; font-style:italic; color:rgba(196,158,64,0.85); }
/* Eyebrow */
.eyebrow { font-size:0.7rem; letter-spacing:0.3em; text-transform:uppercase; color:var(--gold); }
```

### Stat Grid (4 columns in hero)
```css
.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
.stat { background:rgba(255,255,255,0.06); border:1px solid rgba(196,158,64,0.14); border-radius:16px; padding:16px 18px; }
.stat-label { font-size:0.65rem; letter-spacing:0.22em; text-transform:uppercase; color:var(--gold); }
.stat-value { font-size:1rem; color:#fff8f0; }
```

### Panel (standard card)
```css
.panel {
  background: var(--surface);         /* rgba(255,255,255,0.035) */
  border: 1px solid var(--border);    /* rgba(196,158,64,0.18) */
  border-radius: var(--r);            /* 22px */
  padding: 28px;
  box-shadow: var(--shadow);
}
.panel-header { display:flex; align-items:center; gap:10px; padding-bottom:14px; border-bottom:1px solid rgba(196,158,64,0.12); }
.panel-icon { width:36px; height:36px; border-radius:50%; background:rgba(196,158,64,0.1); display:flex; align-items:center; justify-content:center; font-size:1.1rem; color:var(--gold); }
.panel h2 { font-family:Cormorant Garamond; font-size:1.5rem; font-weight:400; color:var(--cream); }
```

### Panel Variants
```css
/* Dasha panel — plum */
.dasha-panel { background:rgba(124,92,191,0.06); border-color:rgba(124,92,191,0.22); }
.dasha-panel .panel-icon { background:rgba(124,92,191,0.14); color:#b49edf; }
.dasha-panel .panel h2 { color:#d0c4f0; }

/* Shadow panel — rose */
.shadow-panel { background:rgba(140,40,70,0.06); border-color:rgba(196,96,122,0.2); }
.shadow-panel .panel-icon { background:rgba(196,96,122,0.12); color:#e8909f; }
.shadow-panel .panel h2 { color:#f0c8d0; }

/* Ref panel — neutral with scroll */
.ref-panel { overflow-y:auto; max-height:460px; }
```

### Planet Chip
```css
.pchip {
  display:inline-flex; align-items:center; gap:6px;
  background:rgba(255,255,255,0.05); border:1px solid rgba(196,158,64,0.12);
  border-radius:999px; padding:5px 12px 5px 8px; font-size:0.78rem;
}
.pchip-name { color:var(--gold); font-weight:500; font-size:0.72rem; }
.pchip-val  { color:rgba(240,232,216,0.75); }
```

### Trait Chips
```css
.chip     { background:rgba(196,158,64,0.09); border:1px solid rgba(196,158,64,0.2); border-radius:999px; padding:6px 14px; font-size:0.82rem; color:var(--gold2); }
.chip-neg { background:rgba(196,96,122,0.09); border-color:rgba(196,96,122,0.22); color:#e8909f; }
.chip-green { background:rgba(90,143,114,0.1); border-color:rgba(90,143,114,0.22); color:#80c4a0; }
```

### Badges
```css
.badge { display:inline-block; padding:3px 10px; border-radius:999px; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; }
.badge-hard  / .badge-risk   { background:rgba(196,96,122,0.18); color:#e8909f; }
.badge-mixed                 { background:rgba(196,158,64,0.15); color:#e8c96a; }
.badge-good  / .badge-protect { background:rgba(90,143,114,0.18); color:#80c4a0; }
```

### Callout Boxes
```css
/* All share: border-radius:14px; padding:14px 18px; font-size:0.9rem; line-height:1.65; */
.golden-box   { background:rgba(196,158,64,0.08); border:1px solid rgba(196,158,64,0.25); color:#e8d89a; }
.golden-box::before { content:"★ Golden Window — "; font-weight:600; color:var(--gold); }

.antidote-box { background:rgba(90,143,114,0.08); border:1px solid rgba(90,143,114,0.2); color:#a0d4b8; }
.antidote-box::before { content:"Antidote — "; font-weight:600; color:#80c4a0; }

/* Session readings callout variants */
.callout { border-radius:14px; padding:18px 22px; font-size:0.9rem; line-height:1.8; }
.callout-gold { background:rgba(196,158,64,0.09); border:1px solid rgba(196,158,64,0.28); }
.callout-plum { background:rgba(124,92,191,0.09); border:1px solid rgba(124,92,191,0.28); }
.callout-rose { background:rgba(196,96,122,0.09); border:1px solid rgba(196,96,122,0.28); }
.callout-sage { background:rgba(90,143,114,0.09); border:1px solid rgba(90,143,114,0.3); }
.callout-label { font-size:0.65rem; letter-spacing:0.25em; text-transform:uppercase; font-weight:600; margin-bottom:8px; }
```

### Fun Facts List
```css
.fun-list { list-style:none; padding:0; display:flex; flex-direction:column; gap:10px; }
.fun-list li { padding:12px 16px; background:rgba(255,255,255,0.04); border-left:3px solid var(--gold); border-radius:0 12px 12px 0; font-size:0.9rem; line-height:1.6; color:rgba(240,232,216,0.82); }
```

### Shadow Cards (2-col grid)
```css
.shadow-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:16px; }
.shadow-card { background:rgba(196,96,122,0.06); border:1px solid rgba(196,96,122,0.15); border-radius:14px; padding:14px 16px; }
.shadow-card strong { display:block; font-size:0.82rem; letter-spacing:0.08em; text-transform:uppercase; color:#e8909f; margin-bottom:6px; }
.shadow-card p { font-size:0.88rem; color:rgba(240,232,216,0.7); line-height:1.6; }
```

### Dasha Issue Rows
```css
.dasha-issues { display:flex; flex-direction:column; gap:10px; margin-top:14px; }
.dasha-issue { display:grid; grid-template-columns:130px 80px 1fr; gap:10px; align-items:center;
  padding:10px 14px; border-radius:12px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); }
.dasha-issue-period { font-weight:600; color:#b49edf; font-size:0.8rem; }
.dasha-issue-note { color:rgba(240,232,216,0.72); line-height:1.5; font-size:0.86rem; }
```

### Period / Window Rows
```css
.period-row { display:grid; grid-template-columns:90px 140px 1fr; gap:10px; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.88rem; }
.period-window { font-weight:600; color:var(--gold2); font-size:0.82rem; }
.period-dasha  { color:rgba(196,158,64,0.65); font-size:0.8rem; }
.period-theme  { color:rgba(240,232,216,0.75); line-height:1.55; }
```

### Classical Reference Cards
```css
.ref-card { padding:16px 0; border-bottom:1px solid rgba(255,255,255,0.06); }
.ref-meta { display:flex; justify-content:space-between; margin-bottom:6px; }
.ref-source { font-size:0.72rem; color:var(--gold); letter-spacing:0.1em; text-transform:uppercase; }
.ref-placement { font-size:0.72rem; color:rgba(240,232,216,0.45); }
.ref-quote { font-family:Cormorant Garamond; font-size:1.05rem; font-style:italic; color:var(--cream); margin-bottom:6px; }
.ref-application { font-size:0.85rem; color:rgba(240,232,216,0.72); line-height:1.6; padding-left:12px; border-left:2px solid rgba(196,158,64,0.3); }
```

### Warning List
```css
.warning-list { list-style:none; padding:0; display:flex; flex-direction:column; gap:6px; margin-top:12px; }
.warning-list li { padding:8px 14px; background:rgba(196,96,122,0.06); border-left:3px solid rgba(196,96,122,0.4); border-radius:0 10px 10px 0; font-size:0.87rem; color:rgba(240,232,216,0.75); }
```

### Sub-label
```css
.sub-label { font-size:0.68rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--gold); margin-bottom:8px; margin-top:18px; }
```

### Section Divider
```css
.divider { display:flex; align-items:center; gap:16px; margin:32px 0; font-size:0.65rem; letter-spacing:0.3em; text-transform:uppercase; color:rgba(240,232,216,0.3); }
.divider::before, .divider::after { content:''; flex:1; height:1px; background:var(--border); }
/* Usage: <div class="divider">Career &amp; Growth</div> or <div class="divider">✦</div> */
```

### Symmetric Grid (2-col panels)
```css
.sym-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
/* Mobile: grid-template-columns:1fr */
```

### Reading Table (session readings)
```css
.reading-table { width:100%; border-collapse:collapse; font-size:0.86rem; }
.reading-table th { text-align:left; padding:10px 14px; background:rgba(196,158,64,0.1); color:var(--gold);
  font-size:0.68rem; letter-spacing:0.18em; text-transform:uppercase; border-bottom:1px solid rgba(196,158,64,0.2); }
.reading-table td { padding:10px 14px; color:rgba(240,232,216,0.82); border-bottom:1px solid rgba(255,255,255,0.05); vertical-align:top; line-height:1.6; }
.reading-table tr:last-child td { border-bottom:none; }
.reading-table tr:hover td { background:rgba(255,255,255,0.02); }
```

### Session Readings Layout (sidebar + main)
```css
.layout { display:grid; grid-template-columns:260px 1fr; min-height:100vh; max-width:1300px; margin:0 auto; }
.sidebar { position:sticky; top:0; height:100vh; overflow-y:auto; padding:36px 20px 36px 24px;
  border-right:1px solid var(--border); background:rgba(11,11,24,0.92); backdrop-filter:blur(12px); }
.main { padding:48px 52px 80px; max-width:860px; }
/* Mobile: grid-template-columns:1fr; sidebar position:relative; height:auto */
```

### Chapter Structure (session readings)
```css
.chapter { margin-bottom:56px; scroll-margin-top:32px; }
.chapter-header { display:flex; align-items:center; gap:14px; margin-bottom:24px; padding-bottom:14px; border-bottom:1px solid var(--border); }
.chapter-icon { width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.3rem; flex-shrink:0; }
/* Variants: .chapter-icon.gold/plum/rose/sage/blue */
.chapter h2 { font-family:Cormorant Garamond; font-size:1.9rem; font-weight:300; color:var(--cream); }
.chapter h2 small { display:block; font-size:0.68rem; letter-spacing:0.22em; text-transform:uppercase; color:var(--gold); font-family:'DM Sans',sans-serif; margin-bottom:4px; }
```

### Section Card (within chapters)
```css
.section { background:var(--surface); border:1px solid var(--border); border-radius:var(--r); padding:24px 28px; margin-bottom:16px; }
.section-title { font-family:Cormorant Garamond; font-size:1.2rem; font-weight:400; color:var(--cream); margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
/* .dot-gold / .dot-plum / .dot-rose / .dot-sage / .dot-blue */
```

### Footer
```css
.footer { text-align:center; padding:20px 0; font-size:0.72rem; color:rgba(240,232,216,0.3); letter-spacing:0.08em; border-top:1px solid var(--border); margin-top:40px; }
/* Content: "Generated {date} · Vedic / Lahiri Ayanamsha · Swiss Ephemeris" */
```

### Required Meta Tags (all files)
```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="robots" content="noindex, nofollow">   <!-- ALWAYS on docs/ files -->
```

### Mobile Breakpoint
```css
@media (max-width: 768px) {
  .sym-grid, .stat-grid, .shadow-grid { grid-template-columns: 1fr; }
  .hero { padding: 32px 24px 28px; }
  /* Session readings: sidebar becomes horizontal strip, main padding 32px 20px */
}
```

### Spirit Animal Section (profile HTML — before footer)
```html
<!-- Full-width panel, text-align:center, padding 48px 40px -->
<!-- Background: linear-gradient(135deg, rgba(28,18,56,0.98), rgba(60,30,80,0.96)) -->
<!-- Animal emoji: font-size 96px -->
<!-- Title: Cormorant Garamond, 2.2rem, weight 300 -->
<!-- Subtitle: 0.7rem eyebrow in gold with placement labels -->
<!-- 3 paragraphs, max-width 680px, centered -->
```

### Remedy HTML Layout
```
Weekly Calendar (full-width table, gold headers, 2-row: practice + planet label)
  ↓
[Tier 1 Universal (sage green)] [Tier 2 Vedic Tradition (gold)] — side by side, 1fr 1fr
  ↓
Tier 3 Neuroscience (blue) — full width, 3-column inner grid (CBT | NLP | Biohacking)
```

---

## Remedy Tier System (ALWAYS classify remedies into 3 tiers)

**Always show a Weekly Practice Calendar FIRST** (before any remedy tiers):
- 7-column Mon–Sun grid with planet emoji headers: 🌙 🔴 🟢 🟡 🟠 🪐 🌞
- Assign remedies to their planetary day (Saturn → Saturday, Venus → Friday, etc.)
- Universal behavioral/neuroscience practices fill weekdays
- This calendar is the first thing in any remedy section

**Tier 1 — ● Universal (green #5AC48A)** — behavioral, gemstones, dana as charity, sound/music therapy, wellness. For everyone.

**Tier 2 — ◆ Vedic Tradition (gold #C9A84C)** — Sanskrit mantras, deity worship, puja, yantra. Only for believers. Never default to this for non-believers.

**Tier 3 — ◈ Neuroscience (blue #5B8FD4)** — CBT | NLP | Biohacking. Full-width row, 3 sub-columns. Always present.

**HTML Layout:** Weekly Calendar (full-width) → Tier 1 + 2 side-by-side → Tier 3 full-width below.
**Never mix tiers in a single list** — always visually separate them.
