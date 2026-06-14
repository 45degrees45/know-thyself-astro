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
