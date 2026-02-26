"""
token_tracker.py — Reusable LLM token usage & cost tracker.

Logs prompt/completion tokens and estimated USD cost to a Google Sheet tab
called "Token Usage". Drop this file into any project — zero project-specific
code inside.

Requirements:
    pip install gspread google-auth

    Optionally, for accurate token counts (instead of estimates):
    pip install tiktoken

Usage:
    from token_tracker import TokenTracker

    tracker = TokenTracker(
        credentials_file="credentials.json",
        spreadsheet_name="My Sheet (Responses)",
    )

    # Log after any LLM call — pass the raw prompt + response text.
    # Tokens are estimated automatically (or provide exact counts).
    tracker.log(
        label="Alice",
        report_type="Birth Chart",
        period="2026-02-21",
        prompt_text=my_prompt,
        completion_text=gpt_response,
        model="gpt-4o",                    # see PRICING dict below
        exact_prompt_tokens=None,          # override estimate if you have it
        exact_completion_tokens=None,
    )

Supported model keys (case-insensitive prefix match):
    gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo,
    claude-opus-4, claude-sonnet-4, claude-haiku-4,
    claude-3-opus, claude-3-sonnet, claude-3-haiku,
    gemini-1.5-pro, gemini-1.5-flash

Add custom models anytime by editing the PRICING dict.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

# ── Model pricing table (USD per 1M tokens) ─────────────────────────────────
# Update this whenever pricing changes.

PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o":           {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":      {"input": 0.15,  "output":  0.60},
    "gpt-4-turbo":      {"input": 10.00, "output": 30.00},
    "gpt-4":            {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo":    {"input":  0.50, "output":  1.50},
    # Anthropic
    "claude-opus-4":    {"input": 15.00, "output": 75.00},
    "claude-sonnet-4":  {"input":  3.00, "output": 15.00},
    "claude-haiku-4":   {"input":  0.80, "output":  4.00},
    "claude-3-opus":    {"input": 15.00, "output": 75.00},
    "claude-3-sonnet":  {"input":  3.00, "output": 15.00},
    "claude-3-haiku":   {"input":  0.25, "output":  1.25},
    # Google
    "gemini-1.5-pro":   {"input":  1.25, "output":  5.00},
    "gemini-1.5-flash": {"input":  0.075,"output":  0.30},
}

SHEET_NAME   = "Token Usage"
SHEET_HEADERS = [
    "Timestamp", "Label", "Report Type", "Period", "Model",
    "Prompt Tokens", "Completion Tokens", "Total Tokens", "Est. Cost (USD)",
]

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ── Token estimation ─────────────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """Estimate token count from text.

    Uses tiktoken (cl100k_base) if available, otherwise falls back to the
    common approximation of 1 token per 4 characters.
    """
    if not text:
        return 0
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return max(1, len(text) // 4)


def _resolve_model_pricing(model: str) -> Optional[dict[str, float]]:
    """Return pricing dict for the given model string (prefix match)."""
    model_lower = model.lower()
    # Exact match first
    if model_lower in PRICING:
        return PRICING[model_lower]
    # Prefix match (e.g. "gpt-4o-2024-11" → "gpt-4o")
    for key, price in PRICING.items():
        if model_lower.startswith(key):
            return price
    return None


def _calc_cost(prompt_tokens: int, completion_tokens: int, model: str) -> Optional[float]:
    """Return estimated USD cost, or None if model is unknown."""
    price = _resolve_model_pricing(model)
    if not price:
        return None
    cost = (prompt_tokens * price["input"] + completion_tokens * price["output"]) / 1_000_000
    return round(cost, 6)


# ── TokenTracker ─────────────────────────────────────────────────────────────

class TokenTracker:
    """Tracks LLM token usage + cost to a Google Sheet tab.

    Args:
        credentials_file: Path to Google service account JSON key file.
        spreadsheet_name: Name of the Google Spreadsheet to write to.
    """

    def __init__(self, credentials_file: str, spreadsheet_name: str):
        self._creds_file      = credentials_file
        self._spreadsheet_name = spreadsheet_name
        self._ws              = None   # lazy-init on first log()

    # ── Internal helpers ────────────────────────────────────────────────────

    def _client(self) -> gspread.Client:
        creds = Credentials.from_service_account_file(self._creds_file, scopes=_SCOPES)
        return gspread.authorize(creds)

    def _worksheet(self) -> Optional[gspread.Worksheet]:
        """Return the Token Usage worksheet, creating it if needed."""
        if self._ws is not None:
            return self._ws
        try:
            gc = self._client()
            wb = gc.open(self._spreadsheet_name)
        except Exception as e:
            print(f"[token_tracker] Could not open '{self._spreadsheet_name}': {e}")
            return None

        try:
            self._ws = wb.worksheet(SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            try:
                self._ws = wb.add_worksheet(title=SHEET_NAME, rows=5000, cols=12)
                self._ws.append_row(SHEET_HEADERS)
                # Freeze header row
                wb.batch_update({"requests": [{
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": self._ws.id,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                }]})
                print(f"[token_tracker] Created '{SHEET_NAME}' sheet.")
            except Exception as e:
                print(f"[token_tracker] Could not create sheet: {e}")
                return None

        return self._ws

    # ── Public API ──────────────────────────────────────────────────────────

    def log(
        self,
        label: str,
        report_type: str,
        period: str,
        prompt_text: str = "",
        completion_text: str = "",
        model: str = "gpt-4o",
        exact_prompt_tokens: Optional[int] = None,
        exact_completion_tokens: Optional[int] = None,
    ) -> Optional[dict]:
        """Append one token-usage row to the sheet.

        Args:
            label:                   Person/job name, e.g. "Kunal Agarwal"
            report_type:             "Birth Chart", "Monthly", "Weekly", "Daily"
            period:                  e.g. "February 2026" or "2026-02-21"
            prompt_text:             Raw prompt sent to the model (used for estimation)
            completion_text:         Raw response from the model
            model:                   Model key, e.g. "gpt-4o" (see PRICING)
            exact_prompt_tokens:     Override estimate with exact prompt token count
            exact_completion_tokens: Override estimate with exact completion token count

        Returns:
            dict with token counts and cost, or None on failure.
        """
        p_tokens = exact_prompt_tokens    if exact_prompt_tokens    is not None else _estimate_tokens(prompt_text)
        c_tokens = exact_completion_tokens if exact_completion_tokens is not None else _estimate_tokens(completion_text)
        total    = p_tokens + c_tokens
        cost     = _calc_cost(p_tokens, c_tokens, model)
        cost_str = f"${cost:.6f}" if cost is not None else "unknown model"

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            label,
            report_type,
            period,
            model,
            p_tokens,
            c_tokens,
            total,
            cost_str,
        ]

        ws = self._worksheet()
        if ws:
            try:
                ws.append_row(row)
                print(f"  [token_tracker] {label} / {report_type}: "
                      f"{total:,} tokens ~ {cost_str}")
            except Exception as e:
                print(f"  [token_tracker] Warning: could not write row: {e}")
        else:
            print(f"  [token_tracker] (sheet unavailable) {label}: "
                  f"{total:,} tokens ~ {cost_str}")

        return {"prompt_tokens": p_tokens, "completion_tokens": c_tokens,
                "total_tokens": total, "cost_usd": cost}

    def weekly_summary(self, days: int = 7) -> dict:
        """Return token/cost totals for the past N days.

        Returns:
            dict with keys: rows, total_tokens, total_cost_usd, by_model, by_type
        """
        ws = self._worksheet()
        if not ws:
            return {}

        cutoff = datetime.now() - timedelta(days=days)
        rows   = ws.get_all_records()
        recent = []
        for r in rows:
            try:
                ts = datetime.strptime(r.get("Timestamp", ""), "%Y-%m-%d %H:%M")
                if ts >= cutoff:
                    recent.append(r)
            except ValueError:
                continue

        total_tokens = sum(r.get("Total Tokens", 0) for r in recent)

        total_cost = 0.0
        for r in recent:
            raw = str(r.get("Est. Cost (USD)", "0")).replace("$", "")
            try:
                total_cost += float(raw)
            except ValueError:
                pass

        by_model: dict[str, dict] = {}
        by_type:  dict[str, dict] = {}
        for r in recent:
            m = r.get("Model", "unknown")
            t = r.get("Report Type", "unknown")
            tok = r.get("Total Tokens", 0)

            by_model.setdefault(m, {"count": 0, "tokens": 0})
            by_model[m]["count"]  += 1
            by_model[m]["tokens"] += tok

            by_type.setdefault(t, {"count": 0, "tokens": 0})
            by_type[t]["count"]  += 1
            by_type[t]["tokens"] += tok

        return {
            "rows":           len(recent),
            "total_tokens":   total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_model":       by_model,
            "by_type":        by_type,
        }

    def print_weekly_summary(self, days: int = 7) -> None:
        """Print a human-readable weekly token/cost summary."""
        s = self.weekly_summary(days=days)
        if not s:
            print("[token_tracker] No data available.")
            return

        print(f"\n{'='*48}")
        print(f"TOKEN USAGE — last {days} days")
        print(f"{'='*48}")
        print(f"  Reports processed : {s['rows']}")
        print(f"  Total tokens      : {s['total_tokens']:,}")
        print(f"  Estimated cost    : ${s['total_cost_usd']:.4f} USD")

        if s["by_model"]:
            print("\n  By model:")
            for m, v in s["by_model"].items():
                print(f"    {m:<22} {v['count']:>3} calls   {v['tokens']:>8,} tokens")

        if s["by_type"]:
            print("\n  By report type:")
            for t, v in s["by_type"].items():
                print(f"    {t:<22} {v['count']:>3} reports {v['tokens']:>8,} tokens")

        print(f"{'='*48}\n")
