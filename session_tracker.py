"""
session_tracker.py — Reusable AI session context logger.

Tracks actions performed during a session with Claude, GPT, or any AI tool.
Persists session logs so future sessions can load context of what was done before.

Zero required dependencies — uses only Python stdlib.
Optional: Google Sheet export (needs gspread + google-auth).

──────────────────────────────────────────────────────
QUICK START
──────────────────────────────────────────────────────

    from session_tracker import SessionTracker

    # 1. Start a session at the top of your script / conversation
    s = SessionTracker(project="Astrowise", tool="Claude Code")

    # 2. Log each action as it happens
    s.log("Loaded 8 people from Google Sheet")
    s.log("Generated birth chart for Kunal Agarwal", detail="emailed PDF")
    s.log("Weekly prediction for Joseph T C failed",
          status="failed", detail="Error in message stream")
    s.log("Re-ran after deleting bad file", detail="success on retry")

    # 3. End the session (writes a summary + closes)
    s.end()

    # 4. At the START of a new session — load previous context
    context = SessionTracker.context(project="Astrowise", last_n=3)
    print(context)          # paste this into your first message to Claude

──────────────────────────────────────────────────────
HOW IT WORKS
──────────────────────────────────────────────────────
Sessions are saved as JSON in:
    <storage_dir>/<project>/<YYYY-MM-DD_HHMMSS>.json

Default storage_dir is ~/.session_tracker (global, works across projects).
Override with: SessionTracker(project="X", storage_dir="./my_sessions")

Status values: "done" ✓  "failed" ✗  "skipped" –  "info" ·
"""

from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_STORAGE_DIR = Path.home() / ".session_tracker"

STATUS_ICONS = {
    "done":    "✓",
    "failed":  "✗",
    "skipped": "–",
    "info":    "·",
    "warning": "⚠",
}


# ── SessionTracker ────────────────────────────────────────────────────────────

class SessionTracker:
    """Logs actions in an AI-assisted session and persists them for future context.

    Args:
        project:     Project name, e.g. "Astrowise". Used to group sessions.
        tool:        AI tool used, e.g. "Claude Code", "ChatGPT", "Cursor".
        storage_dir: Directory to store session JSON files.
                     Defaults to ~/.session_tracker
        auto_save:   Save to disk after every log() call (crash-safe). Default True.
    """

    def __init__(
        self,
        project: str,
        tool: str = "Claude Code",
        storage_dir: Optional[str | Path] = None,
        auto_save: bool = True,
    ):
        self.project    = project
        self.tool       = tool
        self.auto_save  = auto_save
        self._started   = datetime.now()
        self._session_id = self._started.strftime("%Y-%m-%d_%H%M%S")
        self._actions: list[dict] = []
        self._ended: Optional[datetime] = None
        self._summary_note = ""

        self._dir = Path(storage_dir or DEFAULT_STORAGE_DIR) / _safe(project)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._filepath = self._dir / f"{self._session_id}.json"

        if auto_save:
            self._save()   # write skeleton immediately so the file exists

        print(f"[session] Started — project={project!r}  tool={tool!r}")

    # ── Logging ──────────────────────────────────────────────────────────────

    def log(
        self,
        action: str,
        status: str = "done",
        detail: str = "",
    ) -> None:
        """Record one action.

        Args:
            action: Short description of what was done, e.g.
                    "Generated birth chart for Kunal Agarwal"
            status: "done" | "failed" | "skipped" | "info" | "warning"
            detail: Optional extra detail, e.g. "emailed PDF to kunal@gmail.com"
        """
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action":    action,
            "status":    status,
            "detail":    detail,
        }
        self._actions.append(entry)

        icon = STATUS_ICONS.get(status, "·")
        line = f"  {icon} {action}"
        if detail:
            line += f"  ({detail})"
        print(f"[session] {line.strip()}")

        if self.auto_save:
            self._save()

    def end(self, summary_note: str = "") -> str:
        """Close the session, write final summary, and return the summary string.

        Args:
            summary_note: Optional free-text note appended to the summary.
        """
        self._ended = datetime.now()
        self._summary_note = summary_note
        self._save()
        summary = self.summary()
        print(f"\n[session] Ended — {len(self._actions)} actions logged.")
        return summary

    # ── Summary / display ────────────────────────────────────────────────────

    def summary(self) -> str:
        """Return a formatted summary of this session."""
        end_time = self._ended or datetime.now()
        duration = end_time - self._started
        minutes  = int(duration.total_seconds() // 60)

        lines = [
            f"Session: {self.project}  |  Tool: {self.tool}",
            f"Started: {self._started.strftime('%Y-%m-%d %H:%M')}  "
            f"Duration: {minutes}m",
            "─" * 50,
        ]

        done    = [a for a in self._actions if a["status"] == "done"]
        failed  = [a for a in self._actions if a["status"] == "failed"]
        skipped = [a for a in self._actions if a["status"] == "skipped"]

        lines.append(f"Actions: {len(self._actions)} total  "
                     f"({len(done)} done, {len(failed)} failed, "
                     f"{len(skipped)} skipped)")
        lines.append("")

        for a in self._actions:
            icon = STATUS_ICONS.get(a["status"], "·")
            line = f"{icon} {a['action']}"
            if a["detail"]:
                line += f"\n    {a['detail']}"
            lines.append(line)

        if self._summary_note:
            lines += ["", f"Note: {self._summary_note}"]

        return "\n".join(lines)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save(self) -> None:
        data = {
            "session_id":   self._session_id,
            "project":      self.project,
            "tool":         self.tool,
            "started":      self._started.isoformat(),
            "ended":        self._ended.isoformat() if self._ended else None,
            "summary_note": self._summary_note,
            "actions":      self._actions,
        }
        try:
            self._filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[session] Warning: could not save session: {e}")

    # ── Class-level helpers ──────────────────────────────────────────────────

    @classmethod
    def context(
        cls,
        project: str,
        last_n: int = 5,
        storage_dir: Optional[str | Path] = None,
        days: int = 30,
    ) -> str:
        """Return a context string from recent sessions — paste into new AI session.

        Args:
            project:     Project name to load sessions for.
            last_n:      Max number of recent sessions to include.
            storage_dir: Where sessions are stored (default: ~/.session_tracker).
            days:        Only include sessions from the last N days.

        Returns:
            Formatted string ready to paste as context into Claude / GPT / etc.
        """
        sessions = cls._load_sessions(project, last_n=last_n,
                                      storage_dir=storage_dir, days=days)
        if not sessions:
            return f"[session_tracker] No previous sessions found for '{project}'."

        lines = [
            "╔══════════════════════════════════════════════════╗",
            f"  SESSION CONTEXT — {project}",
            f"  Last {len(sessions)} session(s) | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "╚══════════════════════════════════════════════════╝",
            "",
        ]

        for s in sessions:
            started = s.get("started", "")[:16].replace("T", " ")
            tool    = s.get("tool", "")
            actions = s.get("actions", [])
            note    = s.get("summary_note", "")

            done    = sum(1 for a in actions if a["status"] == "done")
            failed  = sum(1 for a in actions if a["status"] == "failed")

            lines.append(f"┌─ {started}  [{tool}]  "
                         f"{len(actions)} actions ({done} done, {failed} failed)")

            for a in actions:
                icon   = STATUS_ICONS.get(a["status"], "·")
                detail = f"  →  {a['detail']}" if a.get("detail") else ""
                lines.append(f"│  {icon} {a['action']}{detail}")

            if note:
                lines.append(f"│  📝 {note}")

            lines.append("│")

        # Remove trailing │
        if lines and lines[-1] == "│":
            lines.pop()

        lines += [
            "══════════════════════════════════════════════════",
            "",
        ]
        return "\n".join(lines)

    @classmethod
    def print_context(cls, project: str, last_n: int = 5,
                      storage_dir: Optional[str | Path] = None) -> None:
        """Print the context string to stdout."""
        print(cls.context(project=project, last_n=last_n, storage_dir=storage_dir))

    @classmethod
    def _load_sessions(
        cls,
        project: str,
        last_n: int = 10,
        storage_dir: Optional[str | Path] = None,
        days: int = 30,
    ) -> list[dict]:
        """Load the N most recent session JSON files for a project."""
        base = Path(storage_dir or DEFAULT_STORAGE_DIR) / _safe(project)
        if not base.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        files  = sorted(base.glob("*.json"), reverse=True)  # newest first

        sessions = []
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                started = datetime.fromisoformat(data.get("started", ""))
                if started < cutoff:
                    break
                sessions.append(data)
                if len(sessions) >= last_n:
                    break
            except Exception:
                continue

        return list(reversed(sessions))   # chronological order

    @classmethod
    def export_to_sheet(
        cls,
        project: str,
        credentials_file: str,
        spreadsheet_name: str,
        last_n: int = 50,
        storage_dir: Optional[str | Path] = None,
    ) -> None:
        """Export recent session logs to a Google Sheet tab called 'Session Log'.

        Requires: pip install gspread google-auth
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            print("[session] gspread not installed — skipping Sheet export.")
            return

        sessions = cls._load_sessions(project, last_n=last_n, storage_dir=storage_dir)
        if not sessions:
            print("[session] No sessions to export.")
            return

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds  = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        gc     = gspread.authorize(creds)

        try:
            wb = gc.open(spreadsheet_name)
        except Exception as e:
            print(f"[session] Could not open '{spreadsheet_name}': {e}")
            return

        SHEET = "Session Log"
        try:
            ws = wb.worksheet(SHEET)
            ws.clear()
        except gspread.exceptions.WorksheetNotFound:
            ws = wb.add_worksheet(title=SHEET, rows=5000, cols=8)

        headers = ["Session ID", "Project", "Tool", "Started", "Timestamp",
                   "Status", "Action", "Detail"]
        rows = [headers]
        for s in sessions:
            for a in s.get("actions", []):
                rows.append([
                    s.get("session_id", ""),
                    s.get("project", ""),
                    s.get("tool", ""),
                    s.get("started", "")[:16].replace("T", " "),
                    a.get("timestamp", ""),
                    a.get("status", ""),
                    a.get("action", ""),
                    a.get("detail", ""),
                ])

        ws.update(rows)
        print(f"[session] Exported {len(rows)-1} actions to '{SHEET}' sheet.")


# ── Utilities ─────────────────────────────────────────────────────────────────

def _safe(name: str) -> str:
    """Make a string safe for use as a directory name."""
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
