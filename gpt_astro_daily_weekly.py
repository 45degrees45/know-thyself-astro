"""
GPT Astro — Daily & Weekly Vedic Astrology Predictions

Two modes:
  --daily   Short daily prediction for today (or specific date)
  --weekly  Week-ahead prediction for the current week (or specific week)

Uses the same infrastructure as gpt_astro_automation.py:
  - Google Sheet for person data
  - ChatGPT browser automation (GPT Astro custom GPT)
  - PDF generation + email/Telegram delivery

Setup: same as gpt_astro_automation.py (see that file for details)

Examples:
  python gpt_astro_daily_weekly.py --daily
  python gpt_astro_daily_weekly.py --daily --date 2026-02-18
  python gpt_astro_daily_weekly.py --daily --filter "Joseph T C"
  python gpt_astro_daily_weekly.py --weekly
  python gpt_astro_daily_weekly.py --weekly --filter "Joseph"

Schedule via cron:
  Daily at 6 AM:   0 6 * * * cd /path/to/know-thyself-astro && python gpt_astro_daily_weekly.py --daily
  Weekly on Monday: 0 6 * * 1 cd /path/to/know-thyself-astro && python gpt_astro_daily_weekly.py --weekly
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta

import os

from gpt_astro_automation import (
    DELAY_BETWEEN_REQUESTS,
    _tracker,
    ask_gpt_astro,
    clean_gpt_response,
    get_friends_from_sheet,
    launch_browser,
    report_path,
    run_reports,
    safe_name,
    save_and_send,
    send_telegram,
)
from session_tracker import SessionTracker
from playwright.sync_api import sync_playwright

# ── Directories ────────────────────────────────────────────────────────────

DAILY_DIR = "daily"
WEEKLY_DIR = "weekly"

# ── Path helpers ───────────────────────────────────────────────────────────


def daily_path(name, date):
    """Return path like daily/<Name>/2026_02_17.txt"""
    person_dir = os.path.join(DAILY_DIR, safe_name(name))
    os.makedirs(person_dir, exist_ok=True)
    return os.path.join(person_dir, f"{date.strftime('%Y_%m_%d')}.txt")


def weekly_path(name, week_start):
    """Return path like weekly/<Name>/2026_W08.txt (ISO week number)."""
    person_dir = os.path.join(WEEKLY_DIR, safe_name(name))
    os.makedirs(person_dir, exist_ok=True)
    iso_year, iso_week, _ = week_start.isocalendar()
    return os.path.join(person_dir, f"{iso_year}_W{iso_week:02d}.txt")


# ── Reasoning instruction ─────────────────────────────────────────────────

_REASONING_INSTRUCTION = (
    "CRITICAL: For every prediction, state the specific astrological reason — "
    "name the exact planet, transit, dasha/antardasha period, house placement, "
    "or yoga that causes it. Never make a claim without citing the chart factor "
    "behind it. The reader should understand WHY each prediction applies to them "
    "specifically, not feel like they are reading a generic horoscope."
)

# ── Daily prompt topics ────────────────────────────────────────────────────

TOPIC_PROMPTS_DAILY = {
    "Career & Wealth": (
        "CAREER & WEALTH\n"
        "   - Today's planetary transits affecting work and finances\n"
        "   - Best hours for important decisions or meetings\n"
        "   - Money matters: spending, earning, or investment cues"
    ),
    "Love & Relationships": (
        "LOVE & RELATIONSHIPS\n"
        "   - Emotional tone of the day\n"
        "   - Communication tips for partner/family\n"
        "   - Social interactions outlook"
    ),
    "Health & Wellness": (
        "HEALTH & WELLNESS\n"
        "   - Energy level forecast\n"
        "   - Body areas to care for today\n"
        "   - Recommended activities (exercise, rest, diet tips)"
    ),
    "Spirituality & Purpose": (
        "SPIRITUALITY & PURPOSE\n"
        "   - Spiritual practice recommendation for today\n"
        "   - Meditation or mantra suggestion\n"
        "   - Karmic themes active today"
    ),
    "Family & Children": (
        "FAMILY & CHILDREN\n"
        "   - Family dynamics today\n"
        "   - Parenting or domestic focus areas"
    ),
    "Education & Learning": (
        "EDUCATION & LEARNING\n"
        "   - Mental clarity and focus forecast\n"
        "   - Best times for study or creative work"
    ),
}

# ── Weekly prompt topics ───────────────────────────────────────────────────

TOPIC_PROMPTS_WEEKLY = {
    "Career & Wealth": (
        "CAREER & WEALTH\n"
        "   - Key planetary transits affecting career and finances this week\n"
        "   - Best days for important professional moves\n"
        "   - Financial outlook: earning, spending, investments\n"
        "   - Auspicious days for career and money matters"
    ),
    "Love & Relationships": (
        "LOVE & RELATIONSHIPS\n"
        "   - Relationship energy and emotional climate this week\n"
        "   - Communication patterns to watch\n"
        "   - Best days for relationship matters"
    ),
    "Health & Wellness": (
        "HEALTH & WELLNESS\n"
        "   - Physical and mental health considerations\n"
        "   - Vulnerable areas to watch this week\n"
        "   - Energy peaks and low points\n"
        "   - Diet and lifestyle recommendations"
    ),
    "Spirituality & Purpose": (
        "SPIRITUALITY & PURPOSE\n"
        "   - Spiritual growth opportunities this week\n"
        "   - Recommended practices and mantras\n"
        "   - Karmic themes and lessons active"
    ),
    "Family & Children": (
        "FAMILY & CHILDREN\n"
        "   - Family dynamics and harmony this week\n"
        "   - Children-related developments\n"
        "   - Auspicious days for family activities"
    ),
    "Education & Learning": (
        "EDUCATION & LEARNING\n"
        "   - Intellectual outlook and focus periods\n"
        "   - Best days for exams, study, or skill development\n"
        "   - Learning challenges and opportunities"
    ),
}

ALL_GUIDANCE_TOPICS = [
    "Career & Wealth",
    "Love & Relationships",
    "Health & Wellness",
    "Spirituality & Purpose",
    "Family & Children",
    "Education & Learning",
]


# ── Prompt helpers ─────────────────────────────────────────────────────────

def _parse_guidance_topics(guidance_str):
    """Parse comma-separated guidance topics from form."""
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


def _build_focus_section(topics, prompts_dict):
    parts = []
    for i, topic in enumerate(topics, 1):
        parts.append(f"{i}. {prompts_dict[topic]}")
    return "\n\n".join(parts)


def _build_other_section(topics):
    others = [t for t in ALL_GUIDANCE_TOPICS if t not in topics]
    if not others:
        return ""
    return f"\n\nAlso briefly cover (1-2 lines each): {', '.join(others)}"


# ── Prompt builders ────────────────────────────────────────────────────────

def build_daily_prompt(name, birth_date, birth_time, birth_place, target_date,
                       gender="", guidance=""):
    """Build a concise daily prediction prompt."""
    topics = _parse_guidance_topics(guidance)
    gender_line = f"Gender: {gender}\n" if gender else ""
    date_str = target_date.strftime("%A, %B %d, %Y")  # e.g. "Tuesday, February 17, 2026"

    if topics:
        focus = _build_focus_section(topics, TOPIC_PROMPTS_DAILY)
        others = _build_other_section(topics)
        return (
            f"Give a concise Vedic astrology DAILY prediction for {date_str}.\n\n"
            f"Person details:\n"
            f"Name: {name}\n"
            f"{gender_line}"
            f"Birth Date: {birth_date}\n"
            f"Birth Time: {birth_time}\n"
            f"Birth Place: {birth_place}\n\n"
            f"Analyze today's planetary transits, Moon nakshatra/sign, and current "
            f"dasha/antardasha to provide specific guidance.\n\n"
            f"Focus on:\n\n"
            f"{focus}{others}\n\n"
            f"End with:\n"
            f"TODAY'S REMEDY\n"
            f"   - One specific mantra or remedy for today\n"
            f"   - Lucky color, number, and direction\n"
            f"   - Overall day rating (1-10)\n\n"
            f"{_REASONING_INSTRUCTION}\n\n"
            f"Keep the report focused and actionable — this is a daily guide, not a "
            f"monthly report. Aim for concise, practical advice.\n\n"
            f"Important: Give the complete report directly. "
            f"Do not ask follow-up questions or offer additional readings."
        )

    # No specific topics — default coverage
    return (
        f"Give a concise Vedic astrology DAILY prediction for {date_str}.\n\n"
        f"Person details:\n"
        f"Name: {name}\n"
        f"{gender_line}"
        f"Birth Date: {birth_date}\n"
        f"Birth Time: {birth_time}\n"
        f"Birth Place: {birth_place}\n\n"
        f"Analyze today's planetary transits, Moon nakshatra/sign, and current "
        f"dasha/antardasha to provide specific guidance.\n\n"
        f"Cover these areas:\n\n"
        f"1. CAREER & WEALTH\n"
        f"   - Today's transits affecting work and finances\n"
        f"   - Best hours for important decisions\n\n"
        f"2. RELATIONSHIPS\n"
        f"   - Emotional tone and social outlook\n"
        f"   - Communication tips\n\n"
        f"3. HEALTH & ENERGY\n"
        f"   - Energy level and body areas to watch\n"
        f"   - Recommended activities\n\n"
        f"4. TODAY'S REMEDY\n"
        f"   - One specific mantra or remedy for today\n"
        f"   - Lucky color, number, and direction\n"
        f"   - Overall day rating (1-10)\n\n"
        f"{_REASONING_INSTRUCTION}\n\n"
        f"Keep the report focused and actionable — this is a daily guide, not a "
        f"monthly report. Aim for concise, practical advice.\n\n"
        f"Important: Give the complete report directly. "
        f"Do not ask follow-up questions or offer additional readings."
    )


def build_weekly_prompt(name, birth_date, birth_time, birth_place,
                        week_start, week_end, gender="", guidance=""):
    """Build a weekly prediction prompt."""
    topics = _parse_guidance_topics(guidance)
    gender_line = f"Gender: {gender}\n" if gender else ""
    start_str = week_start.strftime("%B %d")
    end_str = week_end.strftime("%B %d, %Y")
    week_range = f"{start_str} – {end_str}"

    if topics:
        focus = _build_focus_section(topics, TOPIC_PROMPTS_WEEKLY)
        others = _build_other_section(topics)
        return (
            f"Give a detailed Vedic astrology WEEKLY prediction for the week of "
            f"{week_range}.\n\n"
            f"Person details:\n"
            f"Name: {name}\n"
            f"{gender_line}"
            f"Birth Date: {birth_date}\n"
            f"Birth Time: {birth_time}\n"
            f"Birth Place: {birth_place}\n\n"
            f"Analyze planetary transits through the week, Moon sign changes, and "
            f"current dasha/antardasha to give day-by-day highlights where relevant.\n\n"
            f"Focus on:\n\n"
            f"{focus}{others}\n\n"
            f"End with:\n"
            f"WEEKLY REMEDIES & SUMMARY\n"
            f"   - Recommended mantras and spiritual practices\n"
            f"   - Best and most challenging days of the week\n"
            f"   - Overall week rating (1-10) with summary\n\n"
            f"{_REASONING_INSTRUCTION}\n\n"
            f"Important: Give the complete report directly. "
            f"Do not ask follow-up questions or offer additional readings."
        )

    # No specific topics — default coverage
    return (
        f"Give a detailed Vedic astrology WEEKLY prediction for the week of "
        f"{week_range}.\n\n"
        f"Person details:\n"
        f"Name: {name}\n"
        f"{gender_line}"
        f"Birth Date: {birth_date}\n"
        f"Birth Time: {birth_time}\n"
        f"Birth Place: {birth_place}\n\n"
        f"Analyze planetary transits through the week, Moon sign changes, and "
        f"current dasha/antardasha to give day-by-day highlights where relevant.\n\n"
        f"Cover these areas:\n\n"
        f"1. CAREER & WEALTH\n"
        f"   - Key transits affecting career and finances this week\n"
        f"   - Best days for professional moves and financial decisions\n\n"
        f"2. RELATIONSHIPS\n"
        f"   - Relationship energy and communication patterns\n"
        f"   - Best days for social and romantic matters\n\n"
        f"3. HEALTH & WELLNESS\n"
        f"   - Energy peaks and low points through the week\n"
        f"   - Body areas to watch, diet and lifestyle tips\n\n"
        f"4. WEEKLY REMEDIES & SUMMARY\n"
        f"   - Recommended mantras and spiritual practices\n"
        f"   - Best and most challenging days of the week\n"
        f"   - Overall week rating (1-10) with summary\n\n"
        f"{_REASONING_INSTRUCTION}\n\n"
        f"Important: Give the complete report directly. "
        f"Do not ask follow-up questions or offer additional readings."
    )


# ── Run modes ──────────────────────────────────────────────────────────────

def run_daily(friends, bot_token, chat_id, target_date=None, session=None):
    """Generate daily predictions for all (or filtered) friends."""
    if target_date is None:
        target_date = datetime.now().date()

    date_str = target_date.strftime("%A, %B %d, %Y")
    print(f"Generating daily predictions for {date_str}")
    print(f"{'─' * 40}\n")

    total = len(friends)

    with sync_playwright() as p:
        context = launch_browser(p, headless=False)

        for i, friend in enumerate(friends):
            name = friend["Name"]
            path = daily_path(name, target_date)

            if os.path.exists(path):
                print(f"[{i+1}/{total}] Skipping {name} (daily already done for {target_date})")
                continue

            print(f"[{i+1}/{total}] {name} — daily prediction for {date_str}...")
            prompt = build_daily_prompt(
                name,
                friend["Birth Date"],
                friend["Birth Time"],
                friend["Birth Place"],
                target_date,
                gender=friend.get("Gender", ""),
                guidance=friend.get("Guidance", ""),
            )
            result = ask_gpt_astro(context, prompt)

            if not result:
                print(f"  Failed for {name}")
                continue

            result = clean_gpt_response(result)

            _tracker.log(
                label=name, report_type="Daily",
                period=str(target_date),
                prompt_text=prompt, completion_text=result,
                model="gpt-4o",
            )
            if session:
                email = friend.get("Email", "").strip()
                session.log(f"Daily prediction sent for {name} — {target_date}",
                            detail=f"emailed to {email}" if email else "no email")

            save_and_send(
                path,
                [
                    f"GPT ASTRO — DAILY PREDICTION: {target_date.strftime('%B %d, %Y').upper()}",
                    f"Name: {name}",
                    f"Birth Date: {friend['Birth Date']}",
                    f"Birth Time: {friend['Birth Time']}",
                    f"Birth Place: {friend['Birth Place']}",
                ],
                result,
                bot_token,
                chat_id,
                f"🌅 Daily Vedic Prediction — {date_str}\n"
                f"For: {name}\n{'─' * 30}\n\n",
                friend=friend,
                report_type="daily",
            )

            if i < total - 1:
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

        context.close()


def _get_week_range(ref_date=None):
    """Return (monday, sunday) for the week containing ref_date."""
    if ref_date is None:
        ref_date = datetime.now().date()
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def run_weekly(friends, bot_token, chat_id, ref_date=None, session=None):
    """Generate weekly predictions for all (or filtered) friends."""
    week_start, week_end = _get_week_range(ref_date)

    iso_year, iso_week, _ = week_start.isocalendar()
    print(f"Generating weekly predictions for Week {iso_week} "
          f"({week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')})")
    print(f"{'─' * 40}\n")

    total = len(friends)

    with sync_playwright() as p:
        context = launch_browser(p, headless=False)

        for i, friend in enumerate(friends):
            name = friend["Name"]
            path = weekly_path(name, week_start)

            if os.path.exists(path):
                print(f"[{i+1}/{total}] Skipping {name} (week {iso_week} already done)")
                continue

            print(f"[{i+1}/{total}] {name} — week {iso_week} prediction...")
            prompt = build_weekly_prompt(
                name,
                friend["Birth Date"],
                friend["Birth Time"],
                friend["Birth Place"],
                week_start,
                week_end,
                gender=friend.get("Gender", ""),
                guidance=friend.get("Guidance", ""),
            )
            result = ask_gpt_astro(context, prompt)

            if not result:
                print(f"  Failed for {name}")
                continue

            result = clean_gpt_response(result)

            _tracker.log(
                label=name, report_type="Weekly",
                period=f"Week {iso_week}, {iso_year}",
                prompt_text=prompt, completion_text=result,
                model="gpt-4o",
            )
            if session:
                email = friend.get("Email", "").strip()
                session.log(f"Weekly prediction sent for {name} — Week {iso_week}",
                            detail=f"emailed to {email}" if email else "no email")

            save_and_send(
                path,
                [
                    f"GPT ASTRO — WEEKLY PREDICTION: WEEK {iso_week}, {iso_year}",
                    f"({week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')})",
                    f"Name: {name}",
                    f"Birth Date: {friend['Birth Date']}",
                    f"Birth Time: {friend['Birth Time']}",
                    f"Birth Place: {friend['Birth Place']}",
                ],
                result,
                bot_token,
                chat_id,
                f"📅 Weekly Vedic Prediction — Week {iso_week}\n"
                f"({week_start.strftime('%b %d')} – {week_end.strftime('%b %d')})\n"
                f"For: {name}\n{'─' * 30}\n\n",
                friend=friend,
                report_type="weekly",
            )

            if i < total - 1:
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

        context.close()


# ── New-entry onboarding ───────────────────────────────────────────────────

def run_new_entries(friends, bot_token, chat_id, session=None):
    """Onboard new sign-ups: generate birth chart report + current week's prediction.

    A "new entry" is anyone in the Google Sheet who does not yet have a
    birth chart report file on disk.
    """
    new_friends = [f for f in friends if not os.path.exists(report_path(f["Name"]))]

    if not new_friends:
        print("No new entries found — everyone already has a birth chart report.")
        if session:
            session.log("Checked for new entries — none found", status="info")
        return

    names = ", ".join(f["Name"] for f in new_friends)
    print(f"Found {len(new_friends)} new entr(ies): {names}\n")
    if session:
        session.log(f"Found {len(new_friends)} new entr(ies): {names}", status="info")

    # Step 1: Birth chart report
    print("=" * 50)
    print("STEP 1 OF 2 — Birth Chart Reports")
    print("=" * 50)
    run_reports(new_friends, bot_token, chat_id, log_tracking=True, session=session)

    # Step 2: Weekly prediction for this week
    print("\n" + "=" * 50)
    print("STEP 2 OF 2 — Weekly Predictions")
    print("=" * 50)
    run_weekly(new_friends, bot_token, chat_id, session=session)

    print(f"\nOnboarding complete for: {names}")


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GPT Astro — Daily & Weekly Vedic Predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --new                           Onboard new sign-ups (report + weekly)\n"
            "  %(prog)s --daily                         Today's predictions for everyone\n"
            "  %(prog)s --daily --date 2026-02-18       Specific date\n"
            "  %(prog)s --daily --filter \"Joseph\"       Only matching people\n"
            "  %(prog)s --weekly                         This week's predictions\n"
            "  %(prog)s --weekly --filter \"Joseph T C\"  Weekly for one person\n"
        ),
    )
    parser.add_argument("--new", action="store_true",
                        help="Onboard new entries: birth chart report + this week's prediction")
    parser.add_argument("--daily", action="store_true",
                        help="Generate daily predictions")
    parser.add_argument("--weekly", action="store_true",
                        help="Generate weekly predictions")
    parser.add_argument("--date", help="Target date for daily (YYYY-MM-DD), "
                        "or reference date for weekly (defaults to today)")
    parser.add_argument("--filter", dest="name_filter",
                        help="Only process people whose name contains this string "
                        "(case-insensitive)")
    # Single-person test mode (skips Google Sheet)
    parser.add_argument("--name", help="Person's name (test mode, skips Sheet)")
    parser.add_argument("--birth-date", dest="birth_date",
                        help="Birth date, e.g. 1990-01-15 (test mode)")
    parser.add_argument("--time", help="Birth time, e.g. 14:30 (test mode)")
    parser.add_argument("--place", help="Birth place, e.g. Mumbai (test mode)")
    parser.add_argument("--gender", help="Gender (test mode)")
    parser.add_argument("--guidance", help='Guidance topics (test mode)')
    parser.add_argument("--email", help="Email for delivery (test mode)")

    args = parser.parse_args()

    if not args.new and not args.daily and not args.weekly:
        parser.print_help()
        print("\nSpecify --new, --daily, or --weekly")
        sys.exit(1)

    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: invalid date format '{args.date}' — use YYYY-MM-DD")
            sys.exit(1)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — "
              "no Telegram delivery.\n")

    # Build friends list
    if args.name:
        if not all([args.birth_date, args.time, args.place]):
            print("Error: --name requires --birth-date, --time, and --place")
            sys.exit(1)
        friends = [{
            "Name": args.name,
            "Birth Date": args.birth_date,
            "Birth Time": args.time,
            "Birth Place": args.place,
            "Gender": args.gender or "",
            "Guidance": args.guidance or "",
            "Email": args.email or "",
        }]
        print(f"Test mode: single person — {args.name}\n")
    else:
        friends = get_friends_from_sheet()
        print(f"Loaded {len(friends)} people from Google Sheet\n")

    # Apply name filter
    if args.name_filter:
        filter_lower = args.name_filter.lower()
        friends = [f for f in friends if filter_lower in f["Name"].lower()]
        if not friends:
            print(f"No people matched filter: '{args.name_filter}'")
            sys.exit(1)
        print(f"Filtered to {len(friends)} person(s): "
              f"{', '.join(f['Name'] for f in friends)}\n")

    mode = "new" if args.new else ("daily" if args.daily else "weekly")
    session = SessionTracker(project="Astrowise", tool="Claude Code / GPT Astro")
    session.log(f"Loaded {len(friends)} people — mode: {mode}", status="info")

    # Run
    if args.new:
        run_new_entries(friends, bot_token, chat_id, session=session)
    elif args.daily:
        run_daily(friends, bot_token, chat_id, target_date=target_date, session=session)
    elif args.weekly:
        run_weekly(friends, bot_token, chat_id, ref_date=target_date, session=session)

    session.end()
    print("\n── SESSION CONTEXT (copy this into your next Claude session) ──")
    SessionTracker.print_context(project="Astrowise", last_n=3)


if __name__ == "__main__":
    main()
