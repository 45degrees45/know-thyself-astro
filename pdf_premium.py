"""
Premium PDF report generator for Astrowise.

Parses raw GPT astrology report text into structured sections,
then renders a visually rich PDF with cover page, colored section
headers, auspicious-date tables, rating bar, and branded footer.

Uses fpdf2 with built-in Helvetica only (latin-1).
"""

import re
from fpdf import FPDF

# ── Emoji / Unicode sanitisation (mirrors gpt_astro_automation._sanitize_text) ─

_EMOJI_MAP = {
    "\U0001F539": "* ",     # 🔹
    "\U0001F538": "* ",     # 🔸
    "\U0001F537": "* ",     # 🔷
    "\U0001F53A": "* ",     # 🔺
    "\U0001F53B": "* ",     # 🔻
    "\u2B50": "* ",         # ⭐
    "\U0001F31F": "* ",     # 🌟
    "\u2728": "* ",         # ✨
    "\U0001F52E": "* ",     # 🔮
    "\U0001F5D3": "* ",     # 🗓
    "\U0001F495": "",       # 💕
    "\U0001F549": "",       # 🕉
    "\U0001F4DA": "",       # 📚
    "\u2192": "-> ",        # →
    "\u2013": "-",          # –
    "\u2014": "-",          # —
    # Sanskrit / Devanagari transliteration (used in Vedic section headers)
    "\u0100": "A",          # Ā
    "\u0101": "a",          # ā
    "\u012A": "I",          # Ī
    "\u012B": "i",          # ī
    "\u0102": "A",          # Ă
    "\u015A": "S",          # Ś
    "\u015B": "s",          # ś
    "\u1E62": "S",          # Ṣ
    "\u1E63": "s",          # ṣ
    "\u1E42": "M",          # Ṃ
    "\u1E43": "m",          # ṃ
    "\u1E24": "H",          # Ḥ
    "\u1E25": "h",          # ḥ
    "\u201C": '"',          # "
    "\u201D": '"',          # "
    "\u201E": '"',          # „
    "\u2018": "'",          # '
    "\u2019": "'",          # '
    "\u2022": "* ",         # •
    "\u25CF": "* ",         # ●
    "\u25CB": "o ",         # ○
    "\u2714": "[x]",        # ✔
    "\u2716": "[!]",        # ✖
    "\u26A0": "[!]",        # ⚠
    "\uFE0F": "",           # variation selector
    "\u20E3": "",           # combining enclosing keycap
    # Number emojis (1️⃣ 2️⃣ etc.)
    "\u0031\u20E3": "1.",   # 1️⃣
    "\u0032\u20E3": "2.",   # 2️⃣
    "\u0033\u20E3": "3.",   # 3️⃣
    "\u0034\u20E3": "4.",   # 4️⃣
    "\u0035\u20E3": "5.",   # 5️⃣
    "\u0036\u20E3": "6.",   # 6️⃣
    "\u0037\u20E3": "7.",   # 7️⃣
    "\u0038\u20E3": "8.",   # 8️⃣
    "\u0039\u20E3": "9.",   # 9️⃣
    "\u0030\u20E3": "0.",   # 0️⃣
    # Common ChatGPT emojis
    "\u2705": "[x]",        # ✅
    "\u274C": "[!]",        # ❌
    "\U0001F4B0": "$",      # 💰
    "\U0001F4B5": "$",      # 💵
    "\U0001F4B8": "$",      # 💸
    "\U0001F9D8": "",       # 🧘
    "\U0001F514": "",       # 🔔
    "\U0001F515": "",       # 🔕
    "\u2764": "*",          # ❤
    "\U0001F496": "*",      # 💖
    "\U0001F497": "*",      # 💗
    "\U0001F499": "*",      # 💙
    "\U0001F49B": "*",      # 💛
    "\U0001F49A": "*",      # 💚
    "\U0001F3E5": "+",      # 🏥
    "\U0001F468": "",       # 👨 (and family combos)
    "\U0001F469": "",       # 👩
    "\U0001F467": "",       # 👧
    "\U0001F466": "",       # 👦
    "\U0001F46A": "",       # 👪
    "\u200D": "",           # zero-width joiner (used in family emoji combos)
    "\U0001F4A1": "* ",     # 💡
    "\U0001F4AA": "",       # 💪
    "\U0001F3AF": "",       # 🎯
    "\U0001F525": "",       # 🔥
    "\U0001F4C8": "",       # 📈
    "\U0001F4C9": "",       # 📉
    "\U0001F4CC": "",       # 📌
    "\U0001F4CD": "",       # 📍
    "\U0001F4D6": "",       # 📖
    "\U0001F4D7": "",       # 📗
    "\U0001F4DD": "",       # 📝
    "\U0001F4E2": "",       # 📢
    "\U0001F4F1": "",       # 📱
    "\U0001F30D": "",       # 🌍
    "\U0001F30E": "",       # 🌎
    "\U0001F30F": "",       # 🌏
    "\U0001F305": "",       # 🌅
    "\U0001F319": "",       # 🌙
    "\U0001F31E": "",       # 🌞
    "\U0001F320": "* ",     # 🌠
    "\U0001F331": "",       # 🌱
    "\U0001F33F": "",       # 🌿
    "\U0001F33B": "",       # 🌻
    "\U0001F48E": "",       # 💎
    "\U0001F3C6": "",       # 🏆
    "\U0001F389": "",       # 🎉
    "\U0001F64F": "",       # 🙏
    "\U0001F6E1": "",       # 🛡
    "\u2615": "",           # ☕
    "\u2696": "",           # ⚖
    "\u26A1": "!",          # ⚡
    "\u2611": "[x]",        # ☑
    "\u2610": "[ ]",        # ☐
    "\u2606": "* ",         # ☆
    "\u2605": "* ",         # ★
    "\u270E": "",           # ✎
    "\u270F": "",           # ✏
    "\u2660": "",           # ♠
    "\u2663": "",           # ♣
    "\u2665": "*",          # ♥
    "\u2666": "",           # ♦
    # Additional ChatGPT favorites
    "\U0001F449": "->",     # 👉
    "\U0001F448": "<-",     # 👈
    "\U0001F446": "",       # 👆
    "\U0001F447": "",       # 👇
    "\U0001F49E": "*",      # 💞
    "\U0001FA7A": "+",      # 🩺
    "\U0001FA78": "",       # 🩸
    "\U0001F9E0": "",       # 🧠
    "\U0001F9D9": "",       # 🧙
    "\U0001F3B5": "",       # 🎵
    "\U0001F4AB": "* ",     # 💫
    "\U0001F4A0": "* ",     # 💠
    "\U0001F518": "* ",     # 🔘
    "\U0001F536": "* ",     # 🔶 (large orange diamond)
    # Clock emojis
    "\U0001F550": "",       # 🕐
    "\U0001F551": "",       # 🕑
    "\U0001F552": "",       # 🕒
    "\U0001F553": "",       # 🕓
    "\U0001F554": "",       # 🕔
    "\U0001F555": "",       # 🕕
    "\U0001F556": "",       # 🕖
    "\U0001F557": "",       # 🕗
    "\U0001F558": "",       # 🕘
    "\U0001F559": "",       # 🕙
    "\U0001F55A": "",       # 🕚
    "\U0001F55B": "",       # 🕛
    "\U0001F55C": "",       # 🕜
    "\U0001F55D": "",       # 🕝
    "\U0001F55E": "",       # 🕞
    "\U0001F55F": "",       # 🕟
    "\U0001F560": "",       # 🕠
    "\U0001F561": "",       # 🕡
    "\U0001F562": "",       # 🕢
    "\U0001F563": "",       # 🕣
    "\U0001F564": "",       # 🕤
    "\U0001F565": "",       # 🕥
    "\U0001F566": "",       # 🕦
    "\U0001F567": "",       # 🕧
}


def _sanitize(text):
    """Replace emoji/special Unicode with latin-1 safe equivalents.

    Applies in three passes so compound sequences win over their parts:
      1. Regex for number keycaps (1️⃣…9️⃣) — digit + optional FE0F + U+20E3
      2. Multi-char map entries (e.g. arrow pairs)
      3. Single-char map entries (strips individual emoji/unicode chars)
    """
    # Pass 0: number keycap emoji  (0️⃣–9️⃣)
    text = re.sub(r'([0-9])\uFE0F?\u20E3', lambda m: m.group(1) + '.', text)
    # Pass 1: multi-char sequences
    for char, repl in _EMOJI_MAP.items():
        if len(char) > 1:
            text = text.replace(char, repl)
    # Pass 2: single-char replacements
    for char, repl in _EMOJI_MAP.items():
        if len(char) == 1:
            text = text.replace(char, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")


# ── Design constants ──────────────────────────────────────────────────────────

# Colors (R, G, B)
COL_COVER_BG    = (27, 20, 100)
COL_GOLD        = (201, 168, 76)
COL_BODY        = (50, 50, 50)
COL_MUTED       = (120, 120, 120)
COL_TABLE_ALT   = (245, 245, 248)
COL_LIGHT_BG    = (240, 240, 243)
COL_WHITE       = (255, 255, 255)

# Section title -> color mapping (keyword-based)
_SECTION_COLORS = {
    "career":       (44, 95, 138),
    "wealth":       (44, 95, 138),
    "finance":      (44, 95, 138),
    "relationship": (138, 44, 78),
    "love":         (138, 44, 78),
    "marriage":     (138, 44, 78),
    "health":       (44, 138, 95),
    "wellness":     (44, 138, 95),
    "family":       (138, 95, 44),
    "children":     (138, 95, 44),
    "remed":        (95, 44, 138),
    "summary":      (95, 44, 138),
    "spiritual":    (78, 44, 138),
    "purpose":      (78, 44, 138),
    "education":    (44, 78, 138),
    "learning":     (44, 78, 138),
    "rasi":         (44, 95, 138),
    "chart":        (44, 95, 138),
    "navamsa":      (44, 95, 138),
    "dasha":        (95, 138, 44),
    "yoga":         (138, 95, 44),
    "vimshottari":  (95, 138, 44),
    "overview":     (95, 44, 138),
    "life theme":   (95, 44, 138),
    "brief":        (95, 44, 138),
    "analysis":     (60, 80, 120),
}
_DEFAULT_SECTION_COLOR = (60, 60, 100)

# Layout
MARGIN = 15          # mm
PAGE_W = 210         # A4
PAGE_H = 297
CONTENT_W = PAGE_W - 2 * MARGIN


def _color_for_title(title):
    """Pick a section color based on keywords in the title."""
    lower = title.lower()
    for keyword, color in _SECTION_COLORS.items():
        if keyword in lower:
            return color
    return _DEFAULT_SECTION_COLOR


# ── Content parser ────────────────────────────────────────────────────────────

# Regex for main section markers: "1️⃣ CAREER & WEALTH" or "🔮 REMEDIES" or "🔷 CAREER"
_RE_MAIN_SECTION = re.compile(
    r'^(?:'
    r'[1-9]\uFE0F?\u20E3\s*'       # 1️⃣ keycap digit
    r'|[🔮🌟]\s*'                    # 🔮 or 🌟 prefix
    r'|[🔷]\s*'                      # 🔷 prefix (birth chart sections)
    r')'
    r'(.+)',
    re.UNICODE,
)

# Subsection markers: 🔹/🔸/🔷 prefix
_RE_SUB_MARKER = re.compile(r'^[🔹🔸🔷]\s*(.+)', re.UNICODE)

# Brief-overview section headers with emoji prefix (💕, 🕉, 📚, etc.)
_RE_BRIEF_HEADER = re.compile(
    r'^[\U0001F300-\U0001FAFF\u2600-\u27BF]\s*(.+)', re.UNICODE
)

# Date patterns in auspicious-dates lines
_RE_DATE_LINE = re.compile(
    r'^(?:Feb(?:ruary)?\s+)?\d{1,2}(?:st|nd|rd|th)?'
    r'(?:\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?)?'
    r'(?:\s*Feb(?:ruary)?)?'
    r'\s*[-–→>]\s*(.+)',
    re.IGNORECASE,
)

# Rating pattern
_RE_RATING = re.compile(r'(\d+\.?\d*)\s*/\s*10')

# Dasha / current period
_RE_DASHA = re.compile(
    r'(?:Current\s+(?:Major\s+)?Period\s+(?:Influence)?|Current\s+Period)\s*:\s*(.+)',
    re.IGNORECASE,
)

# ALL CAPS section headings used in birth chart reports (e.g. "BASIC BIRTH CHART STRUCTURE")
_RE_ALLCAPS_SECTION = re.compile(r'^([A-Z][A-Z\d\s&/()\'\-]{4,})$')

# Any line starting with one or more emoji chars — used as section headers in birth chart reports
# Captures everything after the leading emoji(s) and whitespace as the section title
_RE_BIRTH_SECTION = re.compile(
    r'^(?:[\U0001F300-\U0001FAFF\u2600-\u27BF][\uFE0F\u20E3]?\s*)+(\S.{2,})',
    re.UNICODE,
)

# Title lines to skip even when emoji-prefixed (decorative, not real sections)
_BIRTH_SECTION_SKIP = re.compile(r'vedic birth chart report', re.IGNORECASE)

# Reasoning block triggers
_REASONING_PREFIXES = ('because:', 'why?', 'reason:', 'result:')

# Labeled list triggers
_LABEL_PREFIXES = (
    'good for:', 'avoid:', 'recommendations:', 'best suited for:',
    'be cautious about:', 'balance through:', 'indicates:',
)


def _is_brief_overview_header(line):
    """Detect 'Brief Overview' lines or emoji-prefixed short headers."""
    stripped = line.strip()
    if 'brief overview' in stripped.lower():
        return True
    return False


def _looks_like_subsection_title(line):
    """Heuristic: short, title-case-ish line that serves as a subsection heading."""
    s = line.strip()
    if not s or len(s) > 60:
        return False
    # Tab-separated lines are table rows, never headings
    if '\t' in s:
        return False
    # Must not end with common sentence punctuation
    if s.endswith(('.', ',', ':', '?', '!')):
        return False
    # Exclude lines with equations
    if '=' in s:
        return False
    # Parenthetical: allow short qualifiers, reject explanatory content
    if '(' in s and ')' in s:
        paren_content = s[s.index('(') + 1:s.rindex(')')]
        # Reject if parens contain commas (e.g. "Mars (strategy, authority)")
        if ',' in paren_content:
            return False
        # Reject if parenthetical is long (> 3 words = explanation, not qualifier)
        if len(paren_content.split()) > 3:
            return False
    elif '(' in s:
        return False
    # Should have some alpha
    alpha = ''.join(c for c in s if c.isalpha())
    if len(alpha) < 3:
        return False
    # ALL CAPS is a heading (even single word)
    if alpha.isupper() and len(alpha) >= 4:
        return True
    # Title Case: require 2-7 words, most starting with uppercase
    words = s.split()
    if 2 <= len(words) <= 7:
        caps = sum(1 for w in words if w[0].isupper() or not w[0].isalpha())
        if caps >= len(words) * 0.6:
            return True
    return False


def _classify_block_lines(lines, section_title=""):
    """Given a list of content lines, classify them into typed blocks."""
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        lower = line.lower()

        # Check for reasoning block
        if any(lower.startswith(p) for p in _REASONING_PREFIXES):
            reason_lines = [line]
            i += 1
            # Skip blank lines after trigger
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Collect contiguous non-blank lines (stop at first blank)
            while i < len(lines) and lines[i].strip():
                reason_lines.append(lines[i].strip())
                i += 1
            blocks.append({"type": "reasoning", "text": "\n".join(reason_lines)})
            continue

        # Check for labeled list
        if any(lower.startswith(p) for p in _LABEL_PREFIXES):
            label = line
            items = []
            i += 1
            # Skip blank lines after label
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Collect items (across single blank gaps)
            consecutive_blanks = 0
            while i < len(lines):
                stripped_l = lines[i].strip()
                if not stripped_l:
                    consecutive_blanks += 1
                    if consecutive_blanks >= 2:
                        break
                    i += 1
                    continue
                ll = stripped_l.lower()
                if (any(ll.startswith(p) for p in _REASONING_PREFIXES) or
                        any(ll.startswith(p) for p in _LABEL_PREFIXES) or
                        _looks_like_subsection_title(stripped_l) or
                        _RE_DATE_LINE.match(stripped_l) or
                        ll.endswith(':')):
                    break
                consecutive_blanks = 0
                items.append(stripped_l)
                i += 1
            if items:
                blocks.append({"type": "labeled_list", "label": label, "items": items})
            else:
                blocks.append({"type": "paragraph", "text": label})
            continue

        # Check for date lines (auspicious dates)
        if _RE_DATE_LINE.match(line):
            dates = []
            consecutive_blanks = 0
            while i < len(lines):
                stripped_d = lines[i].strip()
                if not stripped_d:
                    consecutive_blanks += 1
                    if consecutive_blanks >= 2:
                        break
                    i += 1
                    continue
                m = _RE_DATE_LINE.match(stripped_d)
                if m:
                    consecutive_blanks = 0
                    parts = stripped_d.split("->", 1)
                    if len(parts) < 2:
                        parts = re.split(r'\s*[-–→>]\s*', stripped_d, maxsplit=1)
                    if len(parts) == 2:
                        dates.append({"range": parts[0].strip(), "desc": parts[1].strip()})
                    else:
                        dates.append({"range": stripped_d, "desc": ""})
                    i += 1
                else:
                    # Non-date line following dates
                    break
            if dates:
                blocks.append({"type": "dates", "items": dates})
            continue

        # Check for tab-separated table rows
        if '\t' in line:
            table_rows = []
            while i < len(lines):
                s = lines[i].strip()
                if not s:
                    break
                if '\t' in s:
                    table_rows.append([c.strip() for c in s.split('\t')])
                    i += 1
                else:
                    break
            if table_rows:
                blocks.append({"type": "table", "rows": table_rows})
            continue

        # Check for bullet-like lines (starting with ->, -, *, [x], [!])
        bullet_markers = ('->', '-', '*', '[x]', '[!]')
        if any(lower.startswith(m) for m in bullet_markers):
            items = []
            while i < len(lines) and lines[i].strip():
                s = lines[i].strip()
                sl = s.lower()
                if any(sl.startswith(m) for m in bullet_markers):
                    # Strip marker
                    for m in bullet_markers:
                        if sl.startswith(m):
                            s = s[len(m):].strip()
                            break
                    items.append(s)
                    i += 1
                else:
                    break
            if items:
                blocks.append({"type": "bullets", "items": items})
            continue

        # Default: paragraph (collect contiguous non-empty lines)
        para_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                break
            nl = next_line.lower()
            # Stop if we hit something that should be its own block
            if (any(nl.startswith(p) for p in _REASONING_PREFIXES) or
                    any(nl.startswith(p) for p in _LABEL_PREFIXES) or
                    _RE_DATE_LINE.match(next_line) or
                    any(nl.startswith(m) for m in bullet_markers) or
                    _looks_like_subsection_title(next_line)):
                break
            para_lines.append(next_line)
            i += 1
        blocks.append({"type": "paragraph", "text": "\n".join(para_lines)})

    return blocks


def parse_report(body, report_type="monthly"):
    """Parse raw report text into structured data for rendering.

    Returns:
        dict with keys: intro, dasha_info, rating, summary, sections
    """
    lines = body.split("\n")
    parsed = {
        "intro": "",
        "dasha_info": "",
        "rating": None,
        "summary": "",
        "sections": [],
    }

    # ── Pass 1: extract rating and dasha ──
    for line in lines:
        if not parsed["dasha_info"]:
            m = _RE_DASHA.search(line)
            if m:
                parsed["dasha_info"] = m.group(1).strip()
        if parsed["rating"] is None:
            m = _RE_RATING.search(line)
            if m:
                parsed["rating"] = float(m.group(1))

    # ── Pass 2: split into main sections ──
    # Find indices of main section headers
    section_starts = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if _RE_RATING.search(stripped):
            continue
        m = _RE_MAIN_SECTION.match(stripped)
        if m:
            section_starts.append((idx, m.group(1).strip()))
        elif report_type == "report":
            # Birth chart: ALL CAPS headers
            m2 = _RE_ALLCAPS_SECTION.match(stripped)
            if m2:
                section_starts.append((idx, m2.group(1).strip()))
            else:
                # Birth chart: emoji-prefixed headers (🪐 RASI CHART, 🏆 CAREER, etc.)
                m3 = _RE_BIRTH_SECTION.match(stripped)
                if m3:
                    title_text = m3.group(1).strip()
                    if not _BIRTH_SECTION_SKIP.search(title_text):
                        section_starts.append((idx, title_text))

    # Everything before first section is intro (strip header/metadata lines)
    first_section_idx = section_starts[0][0] if section_starts else len(lines)
    intro_lines = []
    _header_patterns = (
        re.compile(r'^GPT\s*ASTRO', re.IGNORECASE),
        re.compile(r'^Name\s*:', re.IGNORECASE),
        re.compile(r'^Birth\s*(Date|Time|Place|Details)\s*:', re.IGNORECASE),
        re.compile(r'^=+$'),
        re.compile(r'^-+$'),
        re.compile(r'^Monthly Vedic Astrology Prediction', re.IGNORECASE),
        re.compile(r'^Vedic Birth Chart', re.IGNORECASE),
        re.compile(r'^Below is your detailed', re.IGNORECASE),
        re.compile(r'^(Date|Time|Place)\s*:', re.IGNORECASE),
        re.compile(r'^Ascendant\s*:', re.IGNORECASE),
        # Birth chart decorative title (may have emoji prefix like 🌺)
        re.compile(r'^.*vedic birth chart report', re.IGNORECASE),
        # Birth date/time/place summary line: "29 October 1985 | 11:30 AM | Muscat"
        re.compile(r'^\d{1,2}\s+\w+\s+\d{4}\s*\|'),
    )
    for line in lines[:first_section_idx]:
        stripped = line.strip()
        # Skip metadata lines already captured
        if _RE_DASHA.match(stripped):
            continue
        if not stripped:
            continue
        if any(p.match(stripped) for p in _header_patterns):
            continue
        intro_lines.append(stripped)
    parsed["intro"] = "\n".join(intro_lines)

    # Everything after rating line is summary
    for idx, line in enumerate(lines):
        if _RE_RATING.search(line):
            # Summary = lines after rating, starting from "Summary" line if present
            summary_lines = []
            for sline in lines[idx + 1:]:
                s = sline.strip()
                if s.lower() == 'summary' and not summary_lines:
                    continue  # skip bare "Summary" heading
                summary_lines.append(s)
            parsed["summary"] = "\n".join(summary_lines).strip()
            break

    # ── Pass 3: parse each section ──
    for si, (start_idx, sec_title) in enumerate(section_starts):
        end_idx = section_starts[si + 1][0] if si + 1 < len(section_starts) else len(lines)

        # Check if the rating line is inside this section; if so, stop before it
        for ri in range(start_idx, end_idx):
            if _RE_RATING.search(lines[ri]):
                end_idx = ri
                break

        section_lines = lines[start_idx + 1: end_idx]
        color = _color_for_title(sec_title)

        section = {
            "title": _sanitize(sec_title),
            "color": color,
            "subsections": [],
        }

        # Find subsections within this section
        sub_starts = []
        in_brief_overview = False

        for li, line in enumerate(section_lines):
            stripped = line.strip()

            # Check for brief overview header
            if _is_brief_overview_header(stripped):
                in_brief_overview = True
                continue

            # Emoji-prefixed subsection markers
            m = _RE_SUB_MARKER.match(stripped)
            if m:
                sub_starts.append((li, m.group(1).strip(), False))
                continue

            # Brief overview: emoji-prefixed headers (💕 Love, 🕉 Spirituality, etc.)
            if in_brief_overview and _RE_BRIEF_HEADER.match(stripped):
                title_text = _RE_BRIEF_HEADER.match(stripped).group(1).strip()
                sub_starts.append((li, title_text, False))
                continue

            # Plain-text subsection titles (heuristic)
            if (stripped and _looks_like_subsection_title(stripped) and
                    li > 0 and not section_lines[li - 1].strip()):
                # Previous line is blank -> likely a heading
                sub_starts.append((li, stripped, False))
                continue

        if not sub_starts:
            # No subsections found; treat all content as one block
            blocks = _classify_block_lines(section_lines, sec_title)
            if blocks:
                section["subsections"].append({
                    "title": "",
                    "blocks": blocks,
                })
        else:
            # Content before first subsection
            pre_lines = section_lines[:sub_starts[0][0]]
            pre_blocks = _classify_block_lines(pre_lines, sec_title)
            if pre_blocks:
                section["subsections"].append({
                    "title": "",
                    "blocks": pre_blocks,
                })

            for ssi, (sub_idx, sub_title, is_dates) in enumerate(sub_starts):
                sub_end = sub_starts[ssi + 1][0] if ssi + 1 < len(sub_starts) else len(section_lines)
                content_lines = section_lines[sub_idx + 1: sub_end]

                # Check if this is an auspicious dates subsection
                title_lower = sub_title.lower()
                is_date_section = ('auspicious' in title_lower or 'date' in title_lower)

                blocks = _classify_block_lines(content_lines, sec_title)
                section["subsections"].append({
                    "title": _sanitize(sub_title),
                    "blocks": blocks,
                })

        parsed["sections"].append(section)

    return parsed


# ── PDF renderer ──────────────────────────────────────────────────────────────

class PremiumPDF(FPDF):
    """FPDF subclass with branded footer and helper methods."""

    def __init__(self, report_type="monthly"):
        super().__init__()
        self.report_type = report_type
        self._current_section_color = _DEFAULT_SECTION_COLOR
        self.set_auto_page_break(auto=True, margin=25)

    def footer(self):
        """Branded footer on every page except the cover (page 1)."""
        if self.page_no() == 1:
            return
        display_page = self.page_no() - 1
        self.set_y(-20)
        self.set_draw_color(*COL_MUTED)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COL_MUTED)
        self.cell(CONTENT_W / 2, 5, f"Page {display_page}", align="L")
        self.cell(CONTENT_W / 2, 5, "Astrowise", align="R")

    # ── Helper drawing methods ──

    def _set_color(self, rgb):
        self.set_text_color(*rgb)

    def _draw_cover(self, title, person_name, subtitle, rating, person_details):
        """Render the full-page cover."""
        self.set_auto_page_break(auto=False)
        self.add_page()
        # Background
        self.set_fill_color(*COL_COVER_BG)
        self.rect(0, 0, PAGE_W, PAGE_H, "F")

        # Gold border inset
        self.set_draw_color(*COL_GOLD)
        self.set_line_width(0.6)
        inset = 12
        self.rect(inset, inset, PAGE_W - 2 * inset, PAGE_H - 2 * inset)

        # Decorative gold lines
        line_y1 = PAGE_H * 0.32
        line_y2 = PAGE_H * 0.68
        self.set_line_width(0.3)
        self.line(inset + 10, line_y1, PAGE_W - inset - 10, line_y1)
        self.line(inset + 10, line_y2, PAGE_W - inset - 10, line_y2)

        # Title
        self.set_y(line_y1 + 12)
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*COL_WHITE)
        self.cell(0, 12, _sanitize(title), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

        # Person name
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*COL_GOLD)
        self.cell(0, 10, _sanitize(person_name), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        # Subtitle (month or "Lifetime Analysis")
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*COL_WHITE)
        self.cell(0, 8, _sanitize(subtitle), align="C", new_x="LMARGIN", new_y="NEXT")

        # Rating badge (monthly only)
        if rating is not None:
            self.ln(12)
            badge_w, badge_h = 50, 18
            badge_x = (PAGE_W - badge_w) / 2
            badge_y = self.get_y()
            self.set_fill_color(*COL_GOLD)
            self.set_draw_color(*COL_GOLD)
            self.rect(badge_x, badge_y, badge_w, badge_h, "DF")
            self.set_xy(badge_x, badge_y + 2)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*COL_COVER_BG)
            self.cell(badge_w, badge_h - 4, f"{rating}/10", align="C")

        # Birth details (small, below center)
        self.set_y(line_y2 + 8)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 180, 200)
        details_parts = []
        for key in ["Birth Date", "Birth Time", "Birth Place"]:
            val = person_details.get(key, "")
            if val:
                details_parts.append(f"{key}: {val}")
        if details_parts:
            self.cell(0, 5, _sanitize(" | ".join(details_parts)),
                      align="C", new_x="LMARGIN", new_y="NEXT")

        # Brand at bottom
        self.set_y(PAGE_H - inset - 12)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COL_WHITE)
        self.cell(0, 5, "Astrowise", align="C")
        self.set_auto_page_break(auto=True, margin=25)

    def _draw_person_box(self, person_details, dasha_info):
        """Draw person details box at the top of page 2."""
        self.add_page()
        box_x = MARGIN
        box_y = self.get_y()
        box_h = 30 if not dasha_info else 36

        # Background
        self.set_fill_color(*COL_LIGHT_BG)
        self.rect(box_x, box_y, CONTENT_W, box_h, "F")

        self.set_xy(box_x + 5, box_y + 4)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COL_BODY)

        for key in ["Name", "Gender", "Birth Date", "Birth Time", "Birth Place"]:
            val = person_details.get(key, "")
            if val:
                self.set_font("Helvetica", "B", 10)
                self.cell(28, 5, _sanitize(f"{key}:"), new_x="END")
                self.set_font("Helvetica", "", 10)
                self.cell(60, 5, _sanitize(val), new_x="LMARGIN", new_y="NEXT")
                self.set_x(box_x + 5)

        if dasha_info:
            # Gold accent bar
            bar_y = self.get_y() + 1
            self.set_fill_color(*COL_GOLD)
            self.rect(box_x + 4, bar_y, 2, 5, "F")
            self.set_xy(box_x + 10, bar_y)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*COL_GOLD)
            self.cell(0, 5, _sanitize(f"Current Period: {dasha_info}"),
                      new_x="LMARGIN", new_y="NEXT")

        self.set_y(box_y + box_h + 6)

    def _draw_intro(self, intro_text):
        """Draw the intro paragraph."""
        if not intro_text:
            return
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COL_BODY)
        self.multi_cell(CONTENT_W, 5, _sanitize(intro_text),
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def _ensure_space(self, needed_mm):
        """Add a page break if less than needed_mm remains."""
        if self.get_y() + needed_mm > PAGE_H - 25:
            self.add_page()

    def _draw_section_header(self, title, color):
        """Full-width colored bar with white text."""
        self._ensure_space(45)
        self._current_section_color = color

        y = self.get_y()
        self.set_fill_color(*color)
        self.rect(MARGIN, y, CONTENT_W, 10, "F")
        self.set_xy(MARGIN + 5, y + 1)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*COL_WHITE)
        self.cell(CONTENT_W - 10, 8, _sanitize(title), align="L")
        self.set_y(y + 13)

    def _draw_subsection_title(self, title, color):
        """Subsection heading with colored text and underline."""
        if not title:
            return
        self._ensure_space(15)
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*color)
        self.cell(CONTENT_W, 6, _sanitize(title),
                  new_x="LMARGIN", new_y="NEXT")
        # Thin colored underline (half width)
        y = self.get_y()
        self.set_draw_color(*color)
        self.set_line_width(0.4)
        self.line(MARGIN, y, MARGIN + CONTENT_W * 0.4, y)
        self.ln(3)

    def _draw_paragraph(self, text):
        """Render a text paragraph."""
        self._ensure_space(12)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COL_BODY)
        self.multi_cell(CONTENT_W, 5, _sanitize(text),
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def _draw_bullets(self, items, color):
        """Render a bullet list."""
        self._ensure_space(8)
        indent = 8
        self.set_font("Helvetica", "", 10)
        for item in items:
            self._ensure_space(7)
            self.set_x(MARGIN + indent)
            self.set_text_color(*color)
            self.cell(5, 5, "*", new_x="END")
            self.set_text_color(*COL_BODY)
            self.multi_cell(CONTENT_W - indent - 5, 5, _sanitize(item),
                            new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def _draw_reasoning(self, text, color):
        """Render a reasoning/explanation block with background and left bar."""
        self._ensure_space(15)
        # Calculate height needed
        self.set_font("Helvetica", "I", 10)
        # Approximate: use a temporary multi_cell to get height
        start_y = self.get_y()

        # Draw left bar + background
        block_x = MARGIN + 3
        text_x = MARGIN + 8
        text_w = CONTENT_W - 11

        # We need to render to know the height, so let's estimate
        lines_est = len(_sanitize(text)) / (text_w * 0.45) + text.count('\n')
        block_h = max(lines_est * 5 + 4, 10)

        # Background
        self.set_fill_color(*COL_LIGHT_BG)
        self.rect(block_x, start_y, CONTENT_W - 6, block_h, "F")
        # Left bar
        self.set_fill_color(*color)
        self.rect(block_x, start_y, 2, block_h, "F")

        self.set_xy(text_x, start_y + 2)
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*COL_BODY)
        self.multi_cell(text_w, 5, _sanitize(text),
                        new_x="LMARGIN", new_y="NEXT")
        actual_end = self.get_y()

        # If text was longer than estimated, we can't redraw background easily,
        # but the text will still render correctly. Adjust for next element.
        self.set_y(max(start_y + block_h, actual_end) + 3)

    def _draw_labeled_list(self, label, items, color):
        """Render a labeled list (e.g., 'Good For:' followed by items)."""
        self._ensure_space(12)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*color)
        self.cell(CONTENT_W, 5, _sanitize(label),
                  new_x="LMARGIN", new_y="NEXT")
        self._draw_bullets(items, color)

    def _draw_dates_table(self, items, color):
        """Render an auspicious dates table."""
        self._ensure_space(15)
        col_date_w = CONTENT_W * 0.35
        col_desc_w = CONTENT_W * 0.65

        # Header row
        y = self.get_y()
        self.set_fill_color(*color)
        self.rect(MARGIN, y, CONTENT_W, 7, "F")
        self.set_xy(MARGIN + 2, y + 1)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*COL_WHITE)
        self.cell(col_date_w - 2, 5, "Date Range", new_x="END")
        self.cell(col_desc_w, 5, "Focus", new_x="LMARGIN", new_y="NEXT")
        self.set_y(y + 7)

        # Data rows
        for i, date_item in enumerate(items):
            self._ensure_space(8)
            row_y = self.get_y()
            if i % 2 == 1:
                self.set_fill_color(*COL_TABLE_ALT)
                self.rect(MARGIN, row_y, CONTENT_W, 6, "F")
            self.set_xy(MARGIN + 2, row_y)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*COL_BODY)
            self.cell(col_date_w - 2, 6, _sanitize(date_item["range"]),
                      new_x="END")
            self.set_font("Helvetica", "", 9)
            self.cell(col_desc_w, 6, _sanitize(date_item["desc"]),
                      new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def _draw_table(self, rows, color):
        """Render a tab-separated data table with a styled header row."""
        if not rows:
            return
        self._ensure_space(15)
        num_cols = max(len(r) for r in rows)
        if num_cols < 2:
            return
        col_w = CONTENT_W / num_cols
        header = rows[0]
        data = rows[1:]

        # Header row
        y = self.get_y()
        self.set_fill_color(*color)
        self.rect(MARGIN, y, CONTENT_W, 7, "F")
        self.set_xy(MARGIN + 2, y + 1)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*COL_WHITE)
        for ci, cell in enumerate(header):
            self.cell(col_w - 2, 5, _sanitize(cell), border=0, new_x="END")
        self.set_y(y + 7)

        # Data rows
        for ri, row in enumerate(data):
            self._ensure_space(7)
            row_y = self.get_y()
            if ri % 2 == 1:
                self.set_fill_color(*COL_TABLE_ALT)
                self.rect(MARGIN, row_y, CONTENT_W, 6, "F")
            self.set_xy(MARGIN + 2, row_y)
            for ci, cell_text in enumerate(row):
                self.set_font("Helvetica", "B" if ci == 0 else "", 9)
                self.set_text_color(*COL_BODY)
                self.cell(col_w - 2, 6, _sanitize(cell_text), border=0, new_x="END")
            self.set_y(row_y + 6)
        self.ln(4)

    def _draw_rating_bar(self, rating):
        """Draw the overall rating bar."""
        if rating is None:
            return
        self._ensure_space(25)
        self.ln(6)

        # Label
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COL_GOLD)
        self.cell(CONTENT_W, 6, "Overall Rating",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        bar_x = MARGIN
        bar_y = self.get_y()
        bar_w = CONTENT_W - 30
        bar_h = 8
        filled_w = bar_w * (rating / 10.0)

        # Empty bar background
        self.set_fill_color(*COL_LIGHT_BG)
        self.rect(bar_x, bar_y, bar_w, bar_h, "F")
        # Filled portion
        if filled_w > 6:
            self.set_fill_color(*COL_GOLD)
            self.rect(bar_x, bar_y, filled_w, bar_h, "F")
        elif filled_w > 0:
            self.set_fill_color(*COL_GOLD)
            self.rect(bar_x, bar_y, filled_w, bar_h, "F")

        # Rating number
        self.set_xy(bar_x + bar_w + 4, bar_y - 1)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*COL_GOLD)
        self.cell(25, 10, f"{rating}/10")
        self.set_y(bar_y + bar_h + 6)

    def _draw_summary(self, summary):
        """Render the summary section."""
        if not summary:
            return
        self._ensure_space(20)
        self.ln(4)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*COL_BODY)
        self.multi_cell(CONTENT_W, 5.5, _sanitize(summary),
                        new_x="LMARGIN", new_y="NEXT")

    def _render_blocks(self, blocks, color):
        """Render a list of typed content blocks."""
        for block in blocks:
            btype = block["type"]
            if btype == "paragraph":
                self._draw_paragraph(block["text"])
            elif btype == "bullets":
                self._draw_bullets(block["items"], color)
            elif btype == "reasoning":
                self._draw_reasoning(block["text"], color)
            elif btype == "labeled_list":
                self._draw_labeled_list(block["label"], block["items"], color)
            elif btype == "dates":
                self._draw_dates_table(block["items"], color)
            elif btype == "table":
                self._draw_table(block["rows"], color)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf_premium(title, person_details, body, output_path,
                         report_type="monthly"):
    """Generate a premium styled PDF report.

    Args:
        title: Report title (used as PDF metadata, not directly displayed)
        person_details: dict with Name, Gender, Birth Date, Birth Time, Birth Place
        body: Raw report text body
        output_path: Where to save the PDF
        report_type: "monthly" or "report" (birth chart)
    Returns:
        output_path
    """
    parsed = parse_report(body, report_type)
    person_name = person_details.get("Name", "")

    pdf = PremiumPDF(report_type=report_type)

    # ── Cover page ──
    if report_type == "report":
        cover_title = "VEDIC BIRTH CHART ANALYSIS"
        cover_subtitle = "Lifetime Analysis"
        cover_rating = None
    elif report_type == "daily":
        cover_title = "DAILY VEDIC INSIGHT"
        # Extract date like "February 17, 2026" from body
        date_match = re.search(
            r'((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
            r'[,\s]+)?'
            r'((?:January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+\d{1,2}[,\s]+\d{4})',
            body, re.IGNORECASE
        )
        cover_subtitle = date_match.group(0).strip() if date_match else ""
        cover_rating = parsed["rating"]
    elif report_type == "weekly":
        cover_title = "WEEKLY VEDIC INSIGHT"
        # Extract week range like "February 17 – February 23, 2026"
        week_match = re.search(
            r'(?:Week\s+(?:of\s+)?)?'
            r'((?:January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+\d{1,2})'
            r'\s*[-\u2013\u2014]+\s*'
            r'((?:January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+\d{1,2}[,\s]+\d{4})',
            body, re.IGNORECASE
        )
        if week_match:
            cover_subtitle = f"{week_match.group(1)} - {week_match.group(2)}"
        else:
            cover_subtitle = ""
        cover_rating = parsed["rating"]
    else:
        cover_title = "MONTHLY VEDIC INSIGHT"
        # Extract month/year from body or title
        month_match = re.search(
            r'((?:January|February|March|April|May|June|July|August|September|'
            r'October|November|December)\s+\d{4})',
            body, re.IGNORECASE
        )
        cover_subtitle = month_match.group(1) if month_match else ""
        cover_rating = parsed["rating"]

    pdf._draw_cover(cover_title, person_name, cover_subtitle,
                    cover_rating, person_details)

    # ── Person details + intro ──
    pdf._draw_person_box(person_details, parsed["dasha_info"])
    pdf._draw_intro(parsed["intro"])

    # ── Sections ──
    for section in parsed["sections"]:
        color = section["color"]
        pdf._draw_section_header(section["title"], color)

        for subsection in section["subsections"]:
            pdf._draw_subsection_title(subsection["title"], color)
            pdf._render_blocks(subsection["blocks"], color)

    # ── Rating bar + summary ──
    pdf._draw_rating_bar(parsed["rating"])
    pdf._draw_summary(parsed["summary"])

    pdf.output(output_path)
    print(f"  PDF saved: {output_path}")
    return output_path
