"""Private task traces and concise terminal report rendering."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from .paths import TRACE_DIR

SECRET_PATTERN = re.compile(
    r"(?i)(\b(?:[A-Za-z0-9]+_)?(?:api[_-]?key|secret|password|token)\b\s*(?:=|:)\s*)([^\s,;]+)"
)


def redact_secrets(message: str) -> str:
    return SECRET_PATTERN.sub(r"\1[REDACTED]", message)


def task_trace_path(task_id: str) -> Path:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    trace_path = TRACE_DIR / f"{task_id}.logs"
    trace_path.touch(exist_ok=True)
    trace_path.chmod(0o600)
    return trace_path


def write_trace(trace_path: Path, message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with trace_path.open("a", encoding="utf-8") as trace_file:
        trace_file.write(f"[{timestamp}] {redact_secrets(message)}\n")


def write_trace_output(trace_path: Path, line: str) -> None:
    with trace_path.open("a", encoding="utf-8") as trace_file:
        trace_file.write(redact_secrets(line))


def print_structured_workflow_output(raw_output: list[str], trace_path: Path) -> str | None:
    """Show the final agent report and return it when it follows the protocol."""
    output = "".join(raw_output).strip()
    if not output:
        return None
    report_starts = [
        output.rfind("# Task workflow:"),
        output.rfind("# Implementation:"),
        output.rfind("## Pull request"),
        output.rfind("## Changelog"),
    ]
    report_start = max(report_starts)
    if report_start >= 0:
        report = output[report_start:]
        print(f"\n{report}")
        return report
    review_start = max(output.rfind("APPROVED"), output.rfind("CHANGES_REQUESTED"))
    if review_start >= 0:
        report = output[review_start:]
        print(f"\n{report}")
        return report
    print("\n# Workflow output\n## Outcome\n- The agent did not return the required structured final report.")
    print(f"## Details\n- Full raw output: {trace_path}")
    return None
