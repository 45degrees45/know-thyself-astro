"""
GPT Astro Vedic Astrology — Browser Automation + Telegram Delivery

Two modes:
  --report   One-time full birth chart report (saved once, never regenerated)
  --monthly  Monthly prediction update for current month (the main feature)

Setup:
  1. pip install -r requirements.txt
  2. playwright install chromium
  3. python gpt_astro_automation.py --login       (log into ChatGPT once)
  4. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  5. python gpt_astro_automation.py --monthly     (generate this month's updates)

Schedule monthly via cron (1st of every month at 9 AM):
  0 9 1 * * cd /path/to/know-thyself-astro && python gpt_astro_automation.py --monthly
"""

import argparse
import base64
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import gspread
import requests
from token_tracker import TokenTracker
from session_tracker import SessionTracker
from fpdf import FPDF
from google.oauth2.service_account import Credentials
from pdf_premium import generate_pdf_premium
from playwright.sync_api import sync_playwright
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    From,
    Mail,
    ReplyTo,
)

# Load .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

GPT_ASTRO_URL = "https://chatgpt.com/g/g-NxOF679wx-gpt-astro-vedic-astrology"
PROFILE_DIR = os.path.expanduser("~/.chatgpt-profile")
REPORTS_DIR = "reports"
MONTHLY_DIR = "monthly"
DELAY_BETWEEN_REQUESTS = 60  # seconds between ChatGPT requests
DEFAULT_RECIPIENT_EMAIL = os.getenv("DEFAULT_RECIPIENT_EMAIL", "45degreesolutions@gmail.com")


# ── WhatsApp (Twilio) ────────────────────────────────────────────────────────

def _upload_pdf_to_litterbox(pdf_path):
    """Upload a PDF to litterbox.catbox.moe (72h) and return the public URL, or None."""
    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                data={"reqtype": "fileupload", "time": "72h"},
                files={"fileToUpload": (os.path.basename(pdf_path), f, "application/pdf")},
                timeout=30,
            )
        if resp.ok and resp.text.startswith("https://"):
            return resp.text.strip()
    except Exception as e:
        print(f"  PDF upload error: {e}")
    return None


def send_whatsapp(notification, to_number, account_sid, auth_token, from_number, pdf_path=None):
    """Send a WhatsApp notification via Twilio, with optional PDF attachment."""
    from twilio.rest import Client
    client = Client(account_sid, auth_token)
    try:
        kwargs = dict(
            body=notification,
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_number}",
        )
        if pdf_path and os.path.exists(pdf_path):
            pdf_url = _upload_pdf_to_litterbox(pdf_path)
            if pdf_url:
                kwargs["media_url"] = [pdf_url]
                print(f"  PDF uploaded: {pdf_url}")
            else:
                print(f"  PDF upload failed — sending notification only")
        client.messages.create(**kwargs)
        return True
    except Exception as e:
        print(f"  WhatsApp error: {e}")
        return False


# ── WhatsApp (Direct — Meta Cloud API) ──────────────────────────────────────

def _upload_pdf_to_meta(pdf_path, api_token, app_id):
    """Upload a PDF to Meta's servers for use in WhatsApp templates. Returns handle or None."""
    file_size = os.path.getsize(pdf_path)
    try:
        # Initiate upload session
        resp = requests.post(
            f"https://graph.facebook.com/v22.0/{app_id}/uploads",
            params={
                "file_name": os.path.basename(pdf_path),
                "file_length": file_size,
                "file_type": "application/pdf",
                "access_token": api_token,
            },
            timeout=15,
        )
        if not resp.ok:
            print(f"  Meta upload init error: {resp.text}")
            return None
        session_id = resp.json()["id"]

        # Upload file bytes
        with open(pdf_path, "rb") as f:
            resp2 = requests.post(
                f"https://graph.facebook.com/v22.0/{session_id}",
                headers={"Authorization": f"OAuth {api_token}", "file_offset": "0"},
                data=f,
                timeout=60,
            )
        if resp2.ok:
            return resp2.json().get("h")
        print(f"  Meta upload error: {resp2.text}")
    except Exception as e:
        print(f"  Meta upload error: {e}")
    return None


def send_whatsapp_direct(notification, to_number, api_token, phone_number_id,
                         pdf_path=None, name=None, report_type=None, period=None):
    """Send a WhatsApp message directly via Meta's WhatsApp Business Cloud API.

    When pdf_path + name/report_type are provided, uses the approved
    'astrowise_report' template. Otherwise sends free-form text.
    """
    import re
    to_clean = re.sub(r"[^\d]", "", to_number)

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"

    try:
        use_template = pdf_path and os.path.exists(pdf_path) and name and report_type

        if use_template:
            app_id = os.getenv("WA_APP_ID", "1281688460492103")
            handle = _upload_pdf_to_meta(pdf_path, api_token, app_id)
            if not handle:
                # Fallback: upload to litterbox and send as free-form document
                print(f"  Meta upload failed — trying litterbox fallback")
                pdf_url = _upload_pdf_to_litterbox(pdf_path)
                if pdf_url:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": to_clean,
                        "type": "document",
                        "document": {
                            "link": pdf_url,
                            "filename": os.path.basename(pdf_path),
                            "caption": notification,
                        },
                    }
                else:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": to_clean,
                        "type": "text",
                        "text": {"body": notification},
                    }
            else:
                period_text = f" for {period}" if period else ""
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to_clean,
                    "type": "template",
                    "template": {
                        "name": "astrowise_report",
                        "language": {"code": "en_US"},
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "document",
                                        "document": {
                                            "id": handle,
                                            "filename": os.path.basename(pdf_path),
                                        },
                                    }
                                ],
                            },
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": name},
                                    {"type": "text", "text": report_type.title()},
                                    {"type": "text", "text": period_text},
                                ],
                            },
                        ],
                    },
                }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_clean,
                "type": "text",
                "text": {"body": notification},
            }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.ok:
            return True
        print(f"  WhatsApp Direct error: {resp.status_code} {resp.text}")
        return False
    except Exception as e:
        print(f"  WhatsApp Direct error: {e}")
        return False


# ── Telegram ────────────────────────────────────────────────────────────────

def send_telegram(text, bot_token, chat_id):
    """Send a message via Telegram Bot API. Splits long messages into chunks."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    max_len = 4096

    chunks = [text[i : i + max_len] for i in range(0, len(text), max_len)]
    for chunk in chunks:
        resp = requests.post(url, json={"chat_id": chat_id, "text": chunk})
        if not resp.ok:
            print(f"  Telegram error: {resp.status_code} {resp.text}")
        time.sleep(0.5)


# ── Browser Automation ──────────────────────────────────────────────────────

def launch_browser(playwright, headless=False):
    """Launch Chromium with a persistent profile so ChatGPT login persists."""
    return playwright.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=headless,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )


def click_allow_buttons(page):
    """Click any 'Allow' or 'Always Allow' buttons (plugin permission dialogs)."""
    allow_selectors = [
        'button:has-text("Always Allow")',
        'button:has-text("Allow")',
    ]
    clicked = False
    for sel in allow_selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                print(f"    Clicked permission button: {sel}")
                clicked = True
                time.sleep(3)
                break
        except Exception:
            continue
    return clicked


def wait_for_response(page, timeout_ms=180000):
    """Wait for ChatGPT to finish generating its response.

    Handles plugin permission dialogs that appear mid-stream.
    """
    stop_selectors = [
        'button[aria-label="Stop streaming"]',
        'button[aria-label="Stop generating"]',
        'button[data-testid="stop-button"]',
    ]

    deadline = time.time() + timeout_ms / 1000
    print("    Waiting for response...")

    while time.time() < deadline:
        # Check for and click any Allow dialogs (plugin permissions)
        click_allow_buttons(page)

        # Check if still streaming
        still_streaming = False
        for sel in stop_selectors:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                still_streaming = True
                break

        if not still_streaming:
            # Check if a response has appeared
            messages = page.query_selector_all('[data-message-author-role="assistant"]')
            if messages:
                last_text = messages[-1].inner_text()
                if last_text and len(last_text.strip()) > 20:
                    print("    Response complete.")
                    time.sleep(2)
                    return

        time.sleep(2)

    print("    Timed out waiting for response.")


def extract_last_response(page):
    """Extract the text of the last assistant message on the page."""
    # Try multiple selectors — ChatGPT changes these
    selector_strategies = [
        '[data-message-author-role="assistant"]',
        '.agent-turn .markdown',
        '.markdown.prose',
        '[class*="markdown"]',
    ]

    for sel in selector_strategies:
        messages = page.query_selector_all(sel)
        if messages:
            text = messages[-1].inner_text()
            if text and len(text.strip()) > 20:
                print(f"    Extracted response ({len(text)} chars) via: {sel}")
                return text.strip()

    # Last resort: grab all text from the conversation area
    try:
        main = page.query_selector("main")
        if main:
            text = main.inner_text()
            print(f"    Fallback: grabbed main content ({len(text)} chars)")
            return text.strip()
    except Exception:
        pass

    return None


def send_prompt_to_gpt(page, prompt_text):
    """Type a prompt into ChatGPT and wait for the response."""
    # Try multiple selectors for the text input
    input_selectors = [
        "#prompt-textarea",
        '[data-testid="prompt-textarea"]',
        'div[contenteditable="true"]',
        "textarea",
    ]

    textarea = None
    for sel in input_selectors:
        try:
            textarea = page.wait_for_selector(sel, timeout=5000)
            if textarea:
                print(f"    Found input via: {sel}")
                break
        except Exception:
            continue

    if not textarea:
        print("    ERROR: Could not find text input!")
        page.screenshot(path="debug_no_input.png")
        return None

    textarea.click()
    time.sleep(0.5)

    # Use keyboard to type — more reliable than fill() for contenteditable divs
    textarea.fill(prompt_text)
    time.sleep(0.5)

    # Try multiple selectors for send button
    send_selectors = [
        'button[data-testid="send-button"]',
        'button[aria-label="Send prompt"]',
        'button[aria-label="Send"]',
    ]

    sent = False
    for sel in send_selectors:
        try:
            btn = page.wait_for_selector(sel, timeout=3000)
            if btn and btn.is_enabled():
                btn.click()
                sent = True
                print(f"    Clicked send via: {sel}")
                break
        except Exception:
            continue

    if not sent:
        # Fallback: press Enter
        print("    No send button found — pressing Enter")
        textarea.press("Enter")

    wait_for_response(page)
    return extract_last_response(page)


def ask_gpt_astro(context, prompt_text):
    """Open a fresh GPT Astro page, send prompt, return response."""
    page = context.new_page()
    try:
        print("    Loading GPT Astro page...")
        page.goto(GPT_ASTRO_URL, wait_until="networkidle", timeout=60000)

        # Wait for page to be ready
        time.sleep(3)

        # Take a screenshot so we can debug if things go wrong
        page.screenshot(path="debug_before_prompt.png")

        result = send_prompt_to_gpt(page, prompt_text)

        if not result:
            page.screenshot(path="debug_no_response.png")
            print("    ERROR: No response extracted. Screenshot saved to debug_no_response.png")

        page.close()
        return result
    except Exception as e:
        print(f"    ERROR: {e}")
        try:
            page.screenshot(path="debug_error.png")
            print("    Screenshot saved to debug_error.png")
        except Exception:
            pass
        page.close()
        return None


# ── Response Cleanup / Proofreading ────────────────────────────────────────

# Patterns that indicate ChatGPT conversational tail (not report content).
# We scan from the bottom up and strip everything from the first trigger line.
_TAIL_TRIGGERS = re.compile(
    r'^\s*('
    r'If you would like|If you\'d like|Would you like|Shall I|'
    r'Let me know|Tell me what|Tell me which|Tell me'
    r'|Want me to|Want to go deeper|'
    r'I can now|I can also|'
    r'Feel free|Happy to help|'
    r'Which area would you|'
    r'Do you want me|'
    r'Now, before|Before I proceed|'
    r'Did the|Did you|'
    r'Please reflect|Your feedback will help|'
    r'Over the last|Have you experienced|'
    r'If this prediction matches|Based on your feedback|'
    r'Error in message stream|Retry'
    r')',
    re.IGNORECASE,
)

# Lines that are clearly ChatGPT option-list items (not astrological content)
_OPTION_LINE = re.compile(
    r'^\s*[-–•*]?\s*(Analyze|Predict|Examine|Break down|Go deeper|Explore|'
    r'Or go deeper|Or examine|Or analyze|Or predict)\b',
    re.IGNORECASE,
)


def clean_gpt_response(text):
    """Remove ChatGPT conversational tail and other non-report artifacts.

    Scans from the bottom and strips everything from the first trigger line
    that matches conversational patterns (e.g. "If you would like, I can now:").
    Also removes trailing option-list lines and empty lines.
    """
    if not text:
        return text

    lines = text.split('\n')

    # Only scan the last half of lines (tail content won't be in the first half)
    scan_start = max(0, len(lines) // 2)

    # Find the EARLIEST trigger line in the tail portion
    cut_idx = len(lines)
    for i in range(scan_start, len(lines)):
        stripped = lines[i].strip()
        if _TAIL_TRIGGERS.match(stripped) or _OPTION_LINE.match(stripped):
            cut_idx = i
            break

    # Strip trailing blank lines before the cut
    while cut_idx > 0 and not lines[cut_idx - 1].strip():
        cut_idx -= 1

    lines = lines[:cut_idx]

    # Strip trailing blank lines
    while lines and not lines[-1].strip():
        lines.pop()

    result = '\n'.join(lines)
    if len(result) < len(text):
        removed = len(text) - len(result)
        print(f"  Cleaned response: removed {removed} chars of conversational tail")
    return result


# ── Guidance Topics ─────────────────────────────────────────────────────────

ALL_GUIDANCE_TOPICS = [
    "Career & Wealth",
    "Love & Relationships",
    "Health & Wellness",
    "Spirituality & Purpose",
    "Family & Children",
    "Education & Learning",
]

TOPIC_PROMPTS_REPORT = {
    "Career & Wealth": (
        "CAREER & WEALTH (In-Depth)\n"
        "  - 10th house analysis: planets, sign, aspects, and lord placement\n"
        "  - Dhana yogas and wealth-producing combinations\n"
        "  - Best career fields based on planetary strengths\n"
        "  - Financial patterns: earning, saving, and investment tendencies\n"
        "  - Dasha periods most favorable for career breakthroughs"
    ),
    "Love & Relationships": (
        "LOVE & RELATIONSHIPS (In-Depth)\n"
        "  - 7th house analysis: planets, sign, aspects, and lord placement\n"
        "  - Venus and Mars strength for romantic compatibility\n"
        "  - Marriage timing indicators and Navamsa insights\n"
        "  - Relationship patterns, strengths, and challenges\n"
        "  - Dasha periods most favorable for love and marriage"
    ),
    "Health & Wellness": (
        "HEALTH & WELLNESS (In-Depth)\n"
        "  - 6th house and Ascendant analysis for constitution\n"
        "  - Vulnerable body areas based on planetary afflictions\n"
        "  - Mental health indicators from Moon and Mercury\n"
        "  - Ayurvedic dosha tendency from chart elements\n"
        "  - Periods requiring extra health vigilance"
    ),
    "Spirituality & Purpose": (
        "SPIRITUALITY & PURPOSE (In-Depth)\n"
        "  - 9th and 12th house analysis for spiritual inclination\n"
        "  - Ketu and Jupiter placement for moksha potential\n"
        "  - Dharma and life purpose from Sun and 10th lord\n"
        "  - Past-life karmic indicators from Rahu-Ketu axis\n"
        "  - Recommended spiritual practices based on chart"
    ),
    "Family & Children": (
        "FAMILY & CHILDREN (In-Depth)\n"
        "  - 4th house (mother, home) and 5th house (children) analysis\n"
        "  - Jupiter's role in progeny and family harmony\n"
        "  - Timing of children and family milestones\n"
        "  - Parent-child relationship dynamics from chart\n"
        "  - Property and ancestral wealth indicators"
    ),
    "Education & Learning": (
        "EDUCATION & LEARNING (In-Depth)\n"
        "  - 4th and 5th house for academic ability\n"
        "  - Mercury and Jupiter strength for intellectual growth\n"
        "  - Best fields of study aligned with planetary strengths\n"
        "  - Higher education and foreign study indicators\n"
        "  - Periods most favorable for exams and learning"
    ),
}

TOPIC_PROMPTS_MONTHLY = {
    "Career & Wealth": (
        "CAREER & WEALTH\n"
        "   - Key planetary transits affecting career and finances this month\n"
        "   - Current dasha/antardasha impact on professional growth\n"
        "   - Income, investments, and financial decisions outlook\n"
        "   - Auspicious dates for career and money matters"
    ),
    "Love & Relationships": (
        "LOVE & RELATIONSHIPS\n"
        "   - Romantic and marital life predictions\n"
        "   - Emotional climate and communication patterns\n"
        "   - Auspicious dates for relationship matters"
    ),
    "Health & Wellness": (
        "HEALTH & WELLNESS\n"
        "   - Physical and mental health considerations\n"
        "   - Vulnerable areas to watch\n"
        "   - Diet and lifestyle recommendations"
    ),
    "Spirituality & Purpose": (
        "SPIRITUALITY & PURPOSE\n"
        "   - Spiritual growth opportunities this month\n"
        "   - Meditation and practice recommendations\n"
        "   - Auspicious dates for spiritual activities"
    ),
    "Family & Children": (
        "FAMILY & CHILDREN\n"
        "   - Family dynamics and harmony this month\n"
        "   - Children-related developments\n"
        "   - Auspicious dates for family matters"
    ),
    "Education & Learning": (
        "EDUCATION & LEARNING\n"
        "   - Academic and intellectual outlook\n"
        "   - Best periods for study, exams, or skill development\n"
        "   - Learning opportunities and challenges"
    ),
}


def _parse_guidance_topics(guidance_str):
    """Parse comma-separated guidance topics from form, matching against known topics."""
    if not guidance_str:
        return []
    raw = [t.strip() for t in guidance_str.split(",")]
    matched = []
    for topic in ALL_GUIDANCE_TOPICS:
        for raw_t in raw:
            if raw_t.lower() in topic.lower() or topic.lower() in raw_t.lower():
                matched.append(topic)
                break
    return matched


def _build_focus_section(topics):
    """Build the focus areas section for a birth chart report prompt."""
    parts = []
    for i, topic in enumerate(topics, 1):
        parts.append(f"{i}. {TOPIC_PROMPTS_REPORT[topic]}")
    return "\n\n".join(parts)


def _build_monthly_focus_section(topics, month, year):
    """Build the focus areas section for a monthly prompt."""
    parts = []
    for i, topic in enumerate(topics, 1):
        section = TOPIC_PROMPTS_MONTHLY[topic]
        parts.append(f"{i}. {section}")
    return "\n\n".join(parts)


def _build_other_section(topics, all_topics, prompts_dict, label="Also briefly cover"):
    """Build a brief section for non-selected topics."""
    others = [t for t in all_topics if t not in topics]
    if not others:
        return ""
    names = ", ".join(others)
    return f"\n\n{label} (brief overview only): {names}"


# ── Prompts ─────────────────────────────────────────────────────────────────

_REASONING_INSTRUCTION = (
    "CRITICAL: For every prediction, state the specific astrological reason — "
    "name the exact planet, transit, dasha/antardasha period, house placement, "
    "or yoga that causes it. Never make a claim without citing the chart factor "
    "behind it. The reader should understand WHY each prediction applies to them "
    "specifically, not feel like they are reading a generic horoscope."
)


def build_report_prompt(name, birth_date, birth_time, birth_place,
                        gender="", guidance=""):
    """One-time full birth chart report prompt."""
    topics = _parse_guidance_topics(guidance)
    gender_line = f"Gender: {gender}\n" if gender else ""

    if topics:
        focus = _build_focus_section(topics)
        others = _build_other_section(topics, ALL_GUIDANCE_TOPICS,
                                      TOPIC_PROMPTS_REPORT)
        return (
            f"Generate a detailed Vedic astrology birth chart report for:\n"
            f"Name: {name}\n"
            f"{gender_line}"
            f"Birth Date: {birth_date}\n"
            f"Birth Time: {birth_time}\n"
            f"Birth Place: {birth_place}\n\n"
            f"Include: complete birth chart (Rasi & Navamsa), planetary positions with "
            f"degrees, Vimshottari dasha timeline, and major yogas.\n\n"
            f"Then provide IN-DEPTH analysis for the following areas "
            f"(these are the person's primary interests):\n\n"
            f"{focus}{others}\n\n"
            f"{_REASONING_INSTRUCTION}\n\n"
            f"Important: Give the complete report directly. "
            f"Do not ask follow-up questions or offer additional readings."
        )

    # No specific topics — full coverage (original behavior)
    return (
        f"Generate a detailed Vedic astrology birth chart report for:\n"
        f"Name: {name}\n"
        f"{gender_line}"
        f"Birth Date: {birth_date}\n"
        f"Birth Time: {birth_time}\n"
        f"Birth Place: {birth_place}\n\n"
        f"Include: complete birth chart (Rasi & Navamsa), planetary positions with "
        f"degrees, Vimshottari dasha timeline, major yogas, and general life predictions "
        f"for career, relationships, health, and spirituality.\n\n"
        f"{_REASONING_INSTRUCTION}\n\n"
        f"Important: Deliver the complete report directly. "
        f"Do not ask follow-up questions, request feedback, or invite the person to reflect."
    )


def build_monthly_prompt(name, birth_date, birth_time, birth_place, month, year,
                         gender="", guidance=""):
    """Monthly prediction update prompt."""
    topics = _parse_guidance_topics(guidance)
    gender_line = f"Gender: {gender}\n" if gender else ""

    if topics:
        focus = _build_monthly_focus_section(topics, month, year)
        others = _build_other_section(topics, ALL_GUIDANCE_TOPICS,
                                      TOPIC_PROMPTS_MONTHLY,
                                      label="Also briefly cover")
        return (
            f"Give a detailed Vedic astrology monthly prediction for {month} {year}.\n\n"
            f"Person details:\n"
            f"Name: {name}\n"
            f"{gender_line}"
            f"Birth Date: {birth_date}\n"
            f"Birth Time: {birth_time}\n"
            f"Birth Place: {birth_place}\n\n"
            f"Focus on these areas with detailed analysis:\n\n"
            f"{focus}{others}\n\n"
            f"End with:\n"
            f"REMEDIES & SUMMARY\n"
            f"   - Recommended mantras, gemstones, fasting days\n"
            f"   - Overall month rating (1-10) with summary\n\n"
            f"{_REASONING_INSTRUCTION}\n\n"
            f"Important: Give the complete report directly. "
            f"Do not ask follow-up questions or offer additional readings."
        )

    # No specific topics — full coverage (original behavior)
    return (
        f"Give a detailed Vedic astrology monthly prediction for {month} {year}.\n\n"
        f"Person details:\n"
        f"Name: {name}\n"
        f"{gender_line}"
        f"Birth Date: {birth_date}\n"
        f"Birth Time: {birth_time}\n"
        f"Birth Place: {birth_place}\n\n"
        f"Focus on these areas with detailed analysis:\n\n"
        f"1. CAREER & WEALTH\n"
        f"   - Key planetary transits affecting career and finances in {month} {year}\n"
        f"   - Current dasha/antardasha impact on professional growth\n"
        f"   - Income, investments, and financial decisions outlook\n"
        f"   - Auspicious dates for career and money matters\n\n"
        f"2. RELATIONSHIPS\n"
        f"   - Romantic and marital life predictions\n"
        f"   - Family dynamics and social connections\n"
        f"   - Auspicious dates for relationship matters\n\n"
        f"3. HEALTH\n"
        f"   - Physical and mental health considerations\n"
        f"   - Vulnerable areas to watch\n"
        f"   - Diet and lifestyle recommendations\n\n"
        f"4. REMEDIES & SUMMARY\n"
        f"   - Recommended mantras, gemstones, fasting days\n"
        f"   - Overall month rating (1-10) with summary\n\n"
        f"{_REASONING_INSTRUCTION}\n\n"
        f"Important: Give the complete report directly. "
        f"Do not ask follow-up questions or offer additional readings."
    )


# ── Google Sheet ────────────────────────────────────────────────────────────

# Map possible column headers from Google Forms to our standard keys
COLUMN_ALIASES = {
    "Name": ["Name", "name", "Full Name", "Full name"],
    "Birth Date": ["Birth Date", "Birth date", "Date of Birth", "Date of birth",
                    "DOB", "Date"],
    "Birth Time": ["Birth Time", "Birth time", "Time of Birth", "Time of birth",
                    "Time"],
    "Birth Place": ["Birth Place", "Birth place", "Place of Birth", "Place of birth",
                     "Place", "City"],
    "Gender": ["Gender", "gender"],
    "Guidance": ["Guidance", "guidance", "Guidance Topics", "Areas of Guidance",
                 "What areas of guidance are you most interested in?",
                 "What would you like guidance on?"],
    "Email": ["Email", "email", "Email Address", "Email address"],
    "Phone": ["Phone", "phone", "Phone Number", "Phone number", "Mobile"],
    "Telegram": ["Telegram", "telegram", "Telegram Username",
                  "Telegram username", "Telegram ID",
                  "Telegram Username or Number (Optional)"],
    "Consent": ["Consent", "consent", "Consent Checkbox",
                 "Do you consent to receiving your Vedic astrology report?"],
}

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Astrowise (Responses)")
TRACKING_SHEET_NAME = "Sent Reports"
TRACKING_HEADERS = ["Name", "Report Type", "Period", "Sent Date", "Email Sent", "Telegram Sent"]

# Shared token tracker — lazy-connects on first use
_tracker = TokenTracker(
    credentials_file="credentials.json",
    spreadsheet_name=os.getenv("GOOGLE_SHEET_NAME", "Astrowise (Responses)"),
)


def _strip_prefix(header):
    """Strip leading emoji, numbering, and whitespace from a column header."""
    import re
    # Remove leading emoji (keycap sequences, misc symbols), digits, punctuation, whitespace
    cleaned = re.sub(
        r'^[\s\d️⃣🔟]*[\.\)\-–—:]*\s*',
        '', header
    )
    # Also strip any remaining leading/trailing whitespace
    return cleaned.strip()


_DATE_FORMATS = [
    # ISO / numeric
    "%Y-%m-%d",          # 1990-11-12
    "%d-%m-%Y",          # 12-11-1990
    "%m/%d/%Y",          # 11/12/1990  (US)
    "%d/%m/%Y",          # 12/11/1990  (UK/IN)
    "%d.%m.%Y",          # 12.11.1990
    "%Y/%m/%d",          # 1990/11/12
    # With month name
    "%d-%b-%Y",          # 12-Nov-1990
    "%d-%B-%Y",          # 12-November-1990
    "%d %b %Y",          # 12 Nov 1990
    "%d %B %Y",          # 12 November 1990
    "%b %d, %Y",         # Nov 12, 1990
    "%B %d, %Y",         # November 12, 1990
    "%d/%b/%Y",          # 12/Nov/1990
    # Two-digit year (less reliable — appended last)
    "%d-%m-%y",          # 12-11-90
    "%m/%d/%y",          # 11/12/90
    "%d/%m/%y",          # 12/11/90
]


def _normalize_date(raw: str) -> str:
    """Parse any common date string and return it as DD-MON-YYYY (e.g. 12-NOV-1990).

    Falls back to returning the original string unchanged if parsing fails.
    """
    if not raw:
        return raw
    raw = raw.strip()

    # Already in target format?
    if re.match(r'^\d{1,2}-[A-Za-z]{3}-\d{4}$', raw):
        return raw.upper()

    for fmt in _DATE_FORMATS:
        try:
            from datetime import datetime as _dt
            dt = _dt.strptime(raw, fmt)
            # Reject obviously wrong two-digit-year parses (e.g. year < 1900)
            if dt.year < 1900:
                continue
            return dt.strftime("%d-%b-%Y").upper()   # e.g. 12-NOV-1990
        except ValueError:
            continue

    # Could not parse — return as-is so nothing is lost
    print(f"  Warning: could not parse date {raw!r} — using as-is")
    return raw


def _normalize_time(raw: str) -> str:
    """Convert any AM/PM time string to 24-hour HH:MM format.

    Examples: '10:30 AM' -> '10:30', '2:15 PM' -> '14:15', '14:30' -> '14:30'.
    Falls back to returning the original string unchanged if parsing fails.
    """
    if not raw:
        return raw
    raw = raw.strip()

    # Already in 24-hour format (HH:MM or H:MM with no AM/PM)?
    if re.match(r'^\d{1,2}:\d{2}$', raw):
        return raw

    # Try parsing with AM/PM variants (uppercase input so strptime matches AM/PM)
    for fmt in ("%I:%M %p", "%I:%M%p", "%I:%M:%S %p", "%I:%M:%S%p", "%H:%M:%S"):
        try:
            from datetime import datetime as _dt
            dt = _dt.strptime(raw.upper(), fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            continue

    print(f"  Warning: could not parse time {raw!r} — using as-is")
    return raw


def normalize_record(record):
    """Map varying column names from Google Forms to standard keys.

    Matches aliases against both original and cleaned (emoji-stripped) headers.
    Uses startswith matching so 'Time of Birth' matches
    'Time of Birth (If not accurate, need analysis)'.
    """
    # Build a cleaned-header lookup: cleaned_header -> original_header
    cleaned_map = {}
    for original_key in record:
        cleaned = _strip_prefix(original_key)
        cleaned_map[cleaned] = original_key

    def _find_value(alias):
        """Try exact match then startswith match against original and cleaned headers."""
        # Exact match on original
        if alias in record:
            return str(record[alias]).strip()
        # Exact match on cleaned
        if alias in cleaned_map:
            return str(record[cleaned_map[alias]]).strip()
        # Startswith match on cleaned headers
        for cleaned, original in cleaned_map.items():
            if cleaned.startswith(alias):
                return str(record[original]).strip()
        return None

    normalized = {}
    for standard_key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            val = _find_value(alias)
            if val is not None:
                normalized[standard_key] = val
                break
        if standard_key not in normalized:
            normalized[standard_key] = ""

    # Normalize birth date to unambiguous DD-MON-YYYY format
    if normalized.get("Birth Date"):
        normalized["Birth Date"] = _normalize_date(normalized["Birth Date"])

    # Normalize birth time to 24-hour HH:MM format
    if normalized.get("Birth Time"):
        normalized["Birth Time"] = _normalize_time(normalized["Birth Time"])

    return normalized


def _get_gspread_client():
    """Return an authorized gspread client with read+write access."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    return gspread.authorize(creds)


def get_friends_from_sheet():
    """Read entries from the Google Sheet and normalize column names."""
    gs_client = _get_gspread_client()
    sheet = gs_client.open(GOOGLE_SHEET_NAME).sheet1
    raw = sheet.get_all_records()
    friends = [normalize_record(r) for r in raw]
    # Filter out empty rows
    return [f for f in friends if f["Name"]]


def _get_or_create_tracking_sheet(gs_client):
    """Return the 'Sent Reports' worksheet, creating it with headers if needed."""
    try:
        workbook = gs_client.open(GOOGLE_SHEET_NAME)
    except Exception as e:
        print(f"  Could not open workbook '{GOOGLE_SHEET_NAME}': {e}")
        return None

    try:
        ws = workbook.worksheet(TRACKING_SHEET_NAME)
        return ws
    except gspread.exceptions.WorksheetNotFound:
        pass

    try:
        ws = workbook.add_worksheet(title=TRACKING_SHEET_NAME, rows=2000, cols=10)
        ws.append_row(TRACKING_HEADERS)
        print(f"  Created tracking sheet: '{TRACKING_SHEET_NAME}'")
        return ws
    except Exception as e:
        print(f"  Could not create tracking sheet: {e}")
        return None


def log_report_sent(name, report_type, period, email_sent, telegram_sent):
    """Append one row to the 'Sent Reports' tracking sheet.

    Args:
        name: Person's name
        report_type: "Birth Chart", "Monthly", "Daily", or "Weekly"
        period: e.g. "February 2026" for monthly, or date string for others
        email_sent: bool
        telegram_sent: bool
    """
    try:
        gs_client = _get_gspread_client()
        ws = _get_or_create_tracking_sheet(gs_client)
        if not ws:
            return
        row = [
            name,
            report_type,
            period,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "\u2713" if email_sent else "\u2717",   # ✓ / ✗
            "\u2713" if telegram_sent else "\u2717",
        ]
        ws.append_row(row)
        print(f"  Logged to '{TRACKING_SHEET_NAME}': {name} / {report_type} / {period}")
    except Exception as e:
        print(f"  Warning: could not log to tracking sheet: {e}")


# ── PDF Generation ─────────────────────────────────────────────────────────

def _is_heading(line):
    """Heuristic: detect section headings in report text."""
    stripped = line.strip()
    if not stripped:
        return False
    # Lines that are ALL CAPS (with allowed punctuation/digits), at least 4 chars
    alpha = "".join(c for c in stripped if c.isalpha())
    if len(alpha) >= 4 and alpha.isupper():
        return True
    # Lines starting with a number followed by period/parenthesis and mostly caps
    if len(stripped) > 3 and stripped[0].isdigit() and stripped[1] in ".)" :
        rest = stripped[2:].strip()
        rest_alpha = "".join(c for c in rest if c.isalpha())
        if rest_alpha and rest_alpha.isupper():
            return True
    return False


_EMOJI_MAP = {
    "\U0001F539": "* ",     # 🔹 small blue diamond → bullet
    "\U0001F538": "* ",     # 🔸 small orange diamond → bullet
    "\U0001F53A": "* ",     # 🔺 red triangle → bullet
    "\U0001F53B": "* ",     # 🔻 down triangle → bullet
    "\u2B50": "* ",         # ⭐ star
    "\U0001F31F": "* ",     # 🌟 glowing star
    "\u2728": "* ",         # ✨ sparkles
    "\U0001F52E": "* ",     # 🔮 crystal ball
    "\U0001F5D3": "* ",     # 🗓 calendar
    "\u2192": "->",         # → arrow
    "\u2013": "-",          # – en dash
    "\u2014": "--",         # — em dash
    "\u201C": '"',          # " left double quote
    "\u201D": '"',          # " right double quote
    "\u201E": '"',          # „ double low quote
    "\u2018": "'",          # ' left single quote
    "\u2019": "'",          # ' right single quote
    "\u2022": "* ",         # • bullet
    "\u25CF": "* ",         # ● black circle
    "\u25CB": "o ",         # ○ white circle
    "\u2714": "[x]",        # ✔ check mark
    "\u2716": "[!]",        # ✖ heavy multiplication
    "\u2660": "(Spade)",    # ♠
    "\u2665": "(Heart)",    # ♥
    "\u2666": "(Diamond)",  # ♦
    "\u2663": "(Club)",     # ♣
    "\uFE0F": "",           # variation selector (invisible, just strip)
    "\u20E3": "",           # combining enclosing keycap (strip)
}


def _sanitize_text(text):
    """Replace emoji and special Unicode chars with readable latin-1 equivalents."""
    for char, replacement in _EMOJI_MAP.items():
        text = text.replace(char, replacement)
    # Catch anything else outside latin-1
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(title, person_details, body, output_path):
    """Generate a PDF report using fpdf2.

    Args:
        title: Report title (e.g. "Vedic Birth Chart Report")
        person_details: dict with Name, Birth Date, etc.
        body: The report text body
        output_path: Where to save the PDF
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _sanitize_text(title), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Person details
    pdf.set_font("Helvetica", "", 10)
    for key in ["Name", "Gender", "Birth Date", "Birth Time", "Birth Place"]:
        val = person_details.get(key, "")
        if val:
            pdf.cell(0, 6, _sanitize_text(f"{key}: {val}"),
                     new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    y = pdf.get_y()
    pdf.line(10, y, 200, y)
    pdf.set_xy(pdf.l_margin, y)
    pdf.ln(6)

    # Body
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            pdf.ln(4)
            continue
        if _is_heading(stripped):
            pdf.set_font("Helvetica", "B", 12)
            pdf.ln(3)
            pdf.multi_cell(0, 6, _sanitize_text(stripped),
                           new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, _sanitize_text(stripped),
                           new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
    print(f"  PDF saved: {output_path}")
    return output_path


# ── Email Delivery ─────────────────────────────────────────────────────────

def _build_html_email(body_text):
    """Wrap plain text email body in a clean HTML template for better deliverability."""
    # Escape HTML entities and convert newlines to <br>
    import html as _html
    escaped = _html.escape(body_text).replace("\n", "<br>\n")
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head><meta charset="utf-8"></head>\n'
        '<body style="font-family: Georgia, serif; font-size: 15px; '
        'color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; '
        'padding: 20px;">\n'
        f'{escaped}\n'
        '<br>\n'
        '<hr style="border: none; border-top: 1px solid #ccc; margin: 20px 0;">\n'
        '<p style="font-size: 11px; color: #999;">'
        'You are receiving this because you subscribed to Astrowise '
        'Vedic astrology updates. '
        'To unsubscribe, reply with "unsubscribe".</p>\n'
        '</body>\n'
        '</html>'
    )


def send_email_with_pdf(to_email, subject, body_text, pdf_path, from_email=None,
                        api_key=None):
    """Send an email with a PDF attachment via SendGrid.

    Includes HTML version, sender name, and reply-to for better deliverability.
    """
    api_key = api_key or os.getenv("SENDGRID_API_KEY")
    from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL")

    if not api_key or not from_email:
        print("  Email skipped: SENDGRID_API_KEY or SENDGRID_FROM_EMAIL not set")
        return False

    sender = From(from_email, "Astrowise")

    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body_text,
        html_content=_build_html_email(body_text),
    )
    message.reply_to = ReplyTo(from_email, "Astrowise")

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    attachment = Attachment(
        FileContent(base64.b64encode(pdf_data).decode()),
        FileName(os.path.basename(pdf_path)),
        FileType("application/pdf"),
        Disposition("attachment"),
    )
    message.attachment = attachment

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"  Email sent to {to_email} (status {response.status_code})")
        return True
    except Exception as e:
        print(f"  Email error: {e}")
        return False


# ── File helpers ────────────────────────────────────────────────────────────

def safe_name(name):
    return name.strip().replace(" ", "_")


def report_path(name):
    return os.path.join(REPORTS_DIR, f"{safe_name(name)}_birth_chart.txt")


def monthly_path(name, year, month_num):
    person_dir = os.path.join(MONTHLY_DIR, safe_name(name))
    os.makedirs(person_dir, exist_ok=True)
    return os.path.join(person_dir, f"{year}_{month_num:02d}.txt")


# ── Modes ───────────────────────────────────────────────────────────────────

def login_mode():
    """Open browser so user can log into ChatGPT manually."""
    print("Opening browser for ChatGPT login...")
    print("Log in, then close the browser window when done.")
    print(f"Profile saved to: {PROFILE_DIR}")

    with sync_playwright() as p:
        context = launch_browser(p, headless=False)
        page = context.new_page()
        page.goto("https://chatgpt.com/", wait_until="networkidle", timeout=60000)
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        context.close()

    print("Login session saved.")


def _resolve_telegram_chat_id(friend, default_chat_id):
    """Return per-person Telegram chat ID/username, or fall back to global default."""
    tg = friend.get("Telegram", "").strip()
    if tg:
        # Accept @username or numeric chat_id
        return tg
    return default_chat_id


def save_and_send(filepath, header_lines, body, bot_token, chat_id,
                  telegram_header, friend=None, report_type="report",
                  log_tracking=True):
    """Save text+PDF and deliver via email/Telegram.

    Delivery matrix:
      report  (birth chart): PDF via email; Telegram text only if no email
      monthly               : PDF via email AND text on Telegram
    """
    friend = friend or {}

    # 1. Save .txt (existing behavior)
    with open(filepath, "w") as f:
        for line in header_lines:
            f.write(line + "\n")
        f.write(f"{'=' * 60}\n\n")
        f.write(body)
    print(f"  Saved: {filepath}")

    # 2. Generate PDF alongside .txt
    pdf_path = filepath.rsplit(".", 1)[0] + ".pdf"
    person_details = {
        "Name": friend.get("Name", ""),
        "Gender": friend.get("Gender", ""),
        "Birth Date": friend.get("Birth Date", ""),
        "Birth Time": friend.get("Birth Time", ""),
        "Birth Place": friend.get("Birth Place", ""),
    }
    if report_type == "report":
        pdf_title = "Vedic Astrology — Birth Chart Report"
    elif report_type == "daily":
        pdf_title = header_lines[0] if header_lines else "Vedic Astrology — Daily Prediction"
    elif report_type == "weekly":
        pdf_title = header_lines[0] if header_lines else "Vedic Astrology — Weekly Prediction"
    else:
        pdf_title = header_lines[0] if header_lines else "Vedic Astrology — Monthly Update"
    generate_pdf_premium(pdf_title, person_details, body, pdf_path,
                         report_type=report_type)

    # 3. Email delivery (PDF attachment)
    email = friend.get("Email", "").strip() or DEFAULT_RECIPIENT_EMAIL
    email_sent = False
    if email:
        name = friend.get("Name", "Friend")
        if report_type == "report":
            subject = f"Your Vedic Birth Chart Report — {name}"
            email_body = (
                f"Namaste {name},\n\n"
                f"Please find your personalised Vedic astrology birth chart report "
                f"attached as a PDF.\n\n"
                f"May the stars guide you well.\n"
                f"— Astrowise"
            )
        elif report_type == "daily":
            subject = f"Daily Vedic Prediction — {name}"
            email_body = (
                f"Namaste {name},\n\n"
                f"Your daily Vedic astrology prediction is attached as a PDF.\n\n"
                f"May the stars guide your day.\n"
                f"— Astrowise"
            )
        elif report_type == "weekly":
            subject = f"Weekly Vedic Prediction — {name}"
            email_body = (
                f"Namaste {name},\n\n"
                f"Your weekly Vedic astrology prediction is attached as a PDF.\n\n"
                f"May this week bring you clarity and growth.\n"
                f"— Astrowise"
            )
        else:
            subject = f"Monthly Vedic Update — {name}"
            email_body = (
                f"Namaste {name},\n\n"
                f"Your monthly Vedic astrology update is attached as a PDF.\n\n"
                f"May this month bring you clarity and growth.\n"
                f"— Astrowise"
            )
        email_sent = send_email_with_pdf(email, subject, email_body, pdf_path)

    # 4. Telegram delivery
    resolved_chat_id = _resolve_telegram_chat_id(friend, chat_id)
    telegram_sent = False
    if bot_token and resolved_chat_id:
        if report_type == "report":
            # Birth chart: Telegram only if no email was sent
            if not email_sent:
                send_telegram(telegram_header + body, bot_token, resolved_chat_id)
                telegram_sent = True
                print(f"  Sent to Telegram (no email available)")
        else:
            # Monthly/daily/weekly: always send text to Telegram
            send_telegram(telegram_header + body, bot_token, resolved_chat_id)
            telegram_sent = True
            print(f"  Sent to Telegram")

    # 5. WhatsApp delivery (direct Meta API, or Twilio as fallback)
    phone = friend.get("Phone", "").strip()
    if phone:
        name = friend.get("Name", "Friend")
        period = header_lines[0].split(":")[-1].strip().title() if header_lines and ":" in header_lines[0] else ""
        wa_notification = f"Namaste {name}, your Astrowise {report_type.title()} report{' for ' + period if period else ''} is ready. Please find your PDF attached. 🌟"

        # Try direct Meta Cloud API first
        wa_api_token = os.getenv("WA_API_TOKEN")
        wa_phone_number_id = os.getenv("WA_PHONE_NUMBER_ID")
        wa_sent = False
        if wa_api_token and wa_phone_number_id:
            print(f"  Trying WhatsApp Direct (Meta API)…")
            wa_sent = send_whatsapp_direct(
                wa_notification, phone, wa_api_token, wa_phone_number_id,
                pdf_path=pdf_path, name=name, report_type=report_type, period=period,
            )
            if wa_sent:
                print(f"  Sent to WhatsApp (Direct): {phone}")

        # Fall back to Twilio if direct failed or not configured
        if not wa_sent:
            twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_from = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")
            if twilio_sid and twilio_token:
                print(f"  Trying WhatsApp via Twilio…")
                wa_sent = send_whatsapp(wa_notification, phone, twilio_sid, twilio_token, twilio_from, pdf_path=pdf_path)
                if wa_sent:
                    print(f"  Sent to WhatsApp (Twilio): {phone}")
                else:
                    print(f"  WhatsApp delivery failed for {phone}")

    # 6. Log delivery to tracking sheet
    if log_tracking:
        name = friend.get("Name", "Unknown")
        type_labels = {
            "report": "Birth Chart",
            "monthly": "Monthly",
            "daily": "Daily",
            "weekly": "Weekly",
        }
        rtype_label = type_labels.get(report_type, report_type.title())
        # Build period string from header or current date
        if report_type == "monthly" and len(header_lines) > 0:
            # e.g. "GPT ASTRO — MONTHLY UPDATE: FEBRUARY 2026"
            period = header_lines[0].split(":")[-1].strip().title() if ":" in header_lines[0] else datetime.now().strftime("%B %Y")
        else:
            period = datetime.now().strftime("%Y-%m-%d")
        log_report_sent(name, rtype_label, period, email_sent, telegram_sent)


def run_reports(friends, bot_token, chat_id, log_tracking=True, log_tokens=True,
                session: SessionTracker = None):
    """Generate one-time birth chart reports for all friends."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    total = len(friends)

    with sync_playwright() as p:
        context = launch_browser(p, headless=False)

        for i, friend in enumerate(friends):
            name = friend["Name"]
            path = report_path(name)

            if os.path.exists(path):
                print(f"[{i+1}/{total}] Skipping {name} (birth chart exists)")
                if session:
                    session.log(f"Skipped birth chart for {name}", status="skipped",
                                detail="file already exists")
                continue

            print(f"[{i+1}/{total}] Generating birth chart for {name}...")
            prompt = build_report_prompt(
                name, friend["Birth Date"], friend["Birth Time"],
                friend["Birth Place"],
                gender=friend.get("Gender", ""),
                guidance=friend.get("Guidance", ""),
            )
            result = ask_gpt_astro(context, prompt)

            if not result:
                print(f"  Failed for {name}")
                if session:
                    session.log(f"Birth chart failed for {name}", status="failed",
                                detail="no response from GPT")
                continue

            result = clean_gpt_response(result)

            if log_tokens:
                _tracker.log(
                    label=name, report_type="Birth Chart",
                    period=datetime.now().strftime("%Y-%m-%d"),
                    prompt_text=prompt, completion_text=result,
                    model="gpt-4o",
                )

            email = friend.get("Email", "").strip()
            save_and_send(
                path,
                [
                    "GPT ASTRO — VEDIC BIRTH CHART REPORT",
                    f"Name: {name}",
                    f"Birth Date: {friend['Birth Date']}",
                    f"Birth Time: {friend['Birth Time']}",
                    f"Birth Place: {friend['Birth Place']}",
                ],
                result,
                bot_token,
                chat_id,
                f"🔮 Birth Chart Report: {name}\n{'─' * 30}\n\n",
                friend=friend,
                report_type="report",
                log_tracking=log_tracking,
            )

            if session:
                session.log(f"Birth chart generated for {name}",
                            detail=f"emailed to {email}" if email else "no email")

            if i < total - 1:
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

        context.close()


def run_monthly(friends, bot_token, chat_id, year=None, month_num=None,
                log_tracking=True, log_tokens=True, session: SessionTracker = None):
    """Generate monthly prediction updates for all friends."""
    now = datetime.now()
    if year is None:
        year = now.year
    if month_num is None:
        month_num = now.month
    month_name = datetime(year, month_num, 1).strftime("%B")

    print(f"Generating monthly updates for {month_name} {year}")
    print(f"{'─' * 40}\n")

    total = len(friends)

    with sync_playwright() as p:
        context = launch_browser(p, headless=False)

        for i, friend in enumerate(friends):
            name = friend["Name"]
            path = monthly_path(name, year, month_num)

            if os.path.exists(path):
                print(f"[{i+1}/{total}] Skipping {name} ({month_name} {year} already done)")
                continue

            print(f"[{i+1}/{total}] {name} — {month_name} {year} update...")
            prompt = build_monthly_prompt(
                name,
                friend["Birth Date"],
                friend["Birth Time"],
                friend["Birth Place"],
                month_name,
                year,
                gender=friend.get("Gender", ""),
                guidance=friend.get("Guidance", ""),
            )
            result = ask_gpt_astro(context, prompt)

            if not result:
                print(f"  Failed for {name}")
                if session:
                    session.log(f"Monthly update failed for {name}",
                                status="failed", detail="no response from GPT")
                continue

            result = clean_gpt_response(result)

            if log_tokens:
                _tracker.log(
                    label=name, report_type="Monthly",
                    period=f"{month_name} {year}",
                    prompt_text=prompt, completion_text=result,
                    model="gpt-4o",
                )

            email = friend.get("Email", "").strip()
            save_and_send(
                path,
                [
                    f"GPT ASTRO — MONTHLY UPDATE: {month_name.upper()} {year}",
                    f"Name: {name}",
                    f"Birth Date: {friend['Birth Date']}",
                    f"Birth Time: {friend['Birth Time']}",
                    f"Birth Place: {friend['Birth Place']}",
                ],
                result,
                bot_token,
                chat_id,
                f"🗓 {month_name} {year} — Vedic Update for {name}\n{'─' * 30}\n\n",
                friend=friend,
                report_type="monthly",
                log_tracking=log_tracking,
            )

            if session:
                session.log(f"Monthly update sent for {name} — {month_name} {year}",
                            detail=f"emailed to {email}" if email else "no email")

            if i < total - 1:
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

        context.close()

    print(f"\nAll {month_name} {year} updates done!")


# ── Weekly Summary Report ────────────────────────────────────────────────────

def weekly_report_mode(bot_token, chat_id):
    """Read the tracking sheet and send a summary of the last 7 days.

    Sends to Telegram (and optionally email) as a plain-text digest.
    """
    from datetime import timedelta

    print("Generating weekly summary report...")

    try:
        gs_client = _get_gspread_client()
        ws = _get_or_create_tracking_sheet(gs_client)
        if not ws:
            print("Could not access tracking sheet — aborting.")
            return

        all_rows = ws.get_all_records()
    except Exception as e:
        print(f"Error reading tracking sheet: {e}")
        return

    cutoff = datetime.now() - timedelta(days=7)
    recent = []
    for row in all_rows:
        try:
            sent_dt = datetime.strptime(row["Sent Date"], "%Y-%m-%d %H:%M")
            if sent_dt >= cutoff:
                recent.append(row)
        except (ValueError, KeyError):
            continue

    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime("%b %d")
    week_end = today.strftime("%b %d, %Y")

    lines = [
        "WEEKLY REPORT SUMMARY",
        f"Week of {week_start} - {week_end}",
        "=" * 44,
        f"Total reports sent: {len(recent)}",
        "",
    ]

    def _rows_of_type(rtype):
        return [r for r in recent if r.get("Report Type") == rtype]

    sections = [
        ("Birth Chart", "BIRTH CHART REPORTS"),
        ("Monthly",     "MONTHLY UPDATES"),
        ("Weekly",      "WEEKLY UPDATES"),
        ("Daily",       "DAILY UPDATES"),
    ]

    for rtype, heading in sections:
        rows = _rows_of_type(rtype)
        if not rows:
            continue
        lines.append(f"{heading}:")
        for r in rows:
            sent_d = r.get("Sent Date", "")[:10]
            period = r.get("Period", "")
            period_part = f" [{period}]" if period else ""
            em = r.get("Email Sent", "?")
            tg = r.get("Telegram Sent", "?")
            lines.append(
                f"  {r.get('Name', '?')}{period_part} — {sent_d}"
                f"  Email:{em}  Telegram:{tg}"
            )
        lines.append("")

    if not recent:
        lines.append("No reports sent in the past 7 days.")

    summary = "\n".join(lines)
    print("\n" + summary + "\n")

    if bot_token and chat_id:
        send_telegram(summary, bot_token, chat_id)
        print("Weekly summary sent to Telegram.")
    else:
        print("No Telegram credentials — summary printed above only.")


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GPT Astro — Vedic Astrology Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --login                  Log into ChatGPT (one time)\n"
            "  %(prog)s --monthly                This month's updates for everyone\n"
            "  %(prog)s --monthly --year 2026 --month 3   March 2026 updates\n"
            "  %(prog)s --report                 One-time birth chart reports\n"
        ),
    )
    parser.add_argument("--login", action="store_true", help="Open browser to log into ChatGPT")
    parser.add_argument("--init-tracking", action="store_true",
                        help="Create the 'Sent Reports' tracking sheet now (safe to run anytime)")
    parser.add_argument("--report", action="store_true", help="Generate one-time birth chart reports")
    parser.add_argument("--monthly", action="store_true", help="Generate monthly prediction updates")
    parser.add_argument("--weekly-report", action="store_true",
                        help="Send a weekly summary of all reports sent in the last 7 days")
    parser.add_argument("--year", type=int, help="Year for monthly update (default: current)")
    parser.add_argument("--month", type=int, help="Month number for monthly update (default: current)")
    # Single-person test mode (skips Google Sheet)
    parser.add_argument("--name", help="Person's name (test mode, skips Sheet)")
    parser.add_argument("--date", help="Birth date, e.g. 1990-01-15")
    parser.add_argument("--time", help="Birth time, e.g. 14:30")
    parser.add_argument("--place", help="Birth place, e.g. Mumbai")
    parser.add_argument("--gender", help="Gender (test mode)")
    parser.add_argument("--guidance", help='Guidance topics, e.g. "Career & Wealth, Health"')
    parser.add_argument("--email", help="Email for PDF delivery (test mode)")
    parser.add_argument("--filter", help="Only process people whose name contains this string (case-insensitive)")
    args = parser.parse_args()

    if args.login:
        login_mode()
        return

    if args.init_tracking:
        print(f"Creating '{TRACKING_SHEET_NAME}' sheet in '{GOOGLE_SHEET_NAME}'...")
        gs_client = _get_gspread_client()
        ws = _get_or_create_tracking_sheet(gs_client)
        if ws:
            print(f"Done! Open your Google Sheet and look for the '{TRACKING_SHEET_NAME}' tab.")
        return

    if args.weekly_report:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        weekly_report_mode(bot_token, chat_id)
        return

    if not args.report and not args.monthly:
        parser.print_help()
        print("\nSpecify --report, --monthly, or --weekly-report")
        sys.exit(1)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — no Telegram delivery.\n")

    # Single-person test mode
    test_mode = bool(args.name)
    if test_mode:
        if not all([args.date, args.time, args.place]):
            print("Error: --name requires --date, --time, and --place")
            sys.exit(1)
        friends = [{
            "Name": args.name,
            "Birth Date": args.date,
            "Birth Time": args.time,
            "Birth Place": args.place,
            "Gender": args.gender or "",
            "Guidance": args.guidance or "",
            "Email": args.email or "",
        }]
        print(f"Test mode: single person — {args.name} (tracking sheet logging disabled)\n")
    else:
        friends = get_friends_from_sheet()
        print(f"Loaded {len(friends)} people from Google Sheet")
        if args.filter:
            friends = [f for f in friends if args.filter.lower() in f["Name"].lower()]
            print(f"Filtered to {len(friends)} people matching '{args.filter}'\n")
        else:
            print()

    mode = "report" if args.report else "monthly"
    session = SessionTracker(project="Astrowise", tool="Claude Code / GPT Astro")
    session.log(f"Loaded {len(friends)} people from Google Sheet",
                status="info" if not test_mode else "skipped",
                detail="test mode — sheet skipped" if test_mode else "")

    if args.report:
        run_reports(friends, bot_token, chat_id, log_tracking=not test_mode,
                    session=session)

    if args.monthly:
        run_monthly(friends, bot_token, chat_id, year=args.year, month_num=args.month,
                    log_tracking=not test_mode, session=session)

    session.end()
    print("\n── SESSION CONTEXT (copy this into your next Claude session) ──")
    SessionTracker.print_context(project="Astrowise", last_n=3)


if __name__ == "__main__":
    main()
