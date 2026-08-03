"""TODO.md parsing, workspace validation, and task state updates."""

from __future__ import annotations

import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .paths import ROOT

TASK_HEADING = re.compile(
    r"^##\s+([A-Z0-9]+-\d+)\s*\|\s*(\w+)\s*\|\s*(P[0-3])\s*\|\s*(.+?)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class TaskSpec:
    """The safe, resolved execution scope for one TODO task."""

    task_id: str
    state: str
    priority: str
    title: str
    workspace: Path


def parse_todo_file(todo_path: Path) -> dict[str, dict[str, str]]:
    """Parse TODO.md and return task metadata in document order."""
    if not todo_path.exists():
        print(f"Error: Could not find {todo_path}", file=sys.stderr)
        raise SystemExit(1)

    tasks: dict[str, dict[str, str]] = {}
    for match in TASK_HEADING.finditer(todo_path.read_text(encoding="utf-8")):
        task_id, state, priority, title = match.groups()
        if task_id in tasks:
            raise ValueError(f"Duplicate task ID in {todo_path}: {task_id}")
        tasks[task_id] = {"state": state.lower(), "priority": priority, "title": title}
    return tasks


def get_task_spec(todo_path: Path, task_id: str) -> TaskSpec:
    """Read the selected task's scoped workspace and reject unsafe paths."""
    content = todo_path.read_text(encoding="utf-8")
    matches = list(TASK_HEADING.finditer(content))
    for index, match in enumerate(matches):
        parsed_id, state, priority, title = match.groups()
        if parsed_id != task_id:
            continue

        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        section = content[match.end() : section_end]
        source_match = re.search(r"^\s*-\s*Source:\s*`?([^`\n]+)`?\s*$", section, re.MULTILINE)
        if source_match is None:
            raise ValueError(f"Task {task_id} must declare a Source workspace path")

        source_value = source_match.group(1).strip()
        source_path = (ROOT / source_value).resolve()
        try:
            source_path.relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"Task {task_id} source path escapes the repository: {source_value}") from exc

        workspace = source_path.parent if source_path.name == "Coding" else source_path
        if workspace == ROOT:
            raise ValueError(f"Task {task_id} workspace cannot be the repository root")
        return TaskSpec(task_id, state.lower(), priority, title, workspace)

    raise ValueError(f"Task ID '{task_id}' not found in {todo_path.name}")


def get_task_section(todo_path: Path, task_id: str) -> str:
    """Return one complete task section for an immutable external work order."""
    content = todo_path.read_text(encoding="utf-8")
    matches = list(TASK_HEADING.finditer(content))
    for index, match in enumerate(matches):
        if match.group(1) == task_id:
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            return content[match.start() : section_end].strip() + "\n"
    raise ValueError(f"Task ID '{task_id}' not found in {todo_path.name}")


def get_first_ready_task(tasks: dict[str, dict[str, str]]) -> str | None:
    """Find the first task marked with state ``ready``."""
    return next((task_id for task_id, info in tasks.items() if info["state"] == "ready"), None)


def update_task_state(
    todo_path: Path,
    task_id: str,
    new_state: str,
    *,
    expected_state: str | None = None,
) -> bool:
    """Atomically change one task state, optionally guarding its prior state."""
    content = todo_path.read_text(encoding="utf-8")
    heading = re.compile(
        rf"^(##\s+{re.escape(task_id)}\s*\|\s*)(\w+)(\s*\|\s*P[0-3]\s*\|.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        if expected_state is not None and match.group(2).lower() != expected_state.lower():
            return match.group(0)
        return f"{match.group(1)}{new_state}{match.group(3)}"

    updated, replacements = heading.subn(replace, content, count=1)
    if replacements != 1 or updated == content:
        return False
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=todo_path.parent, delete=False) as temp_file:
        temp_file.write(updated)
        temporary_path = Path(temp_file.name)
    temporary_path.replace(todo_path)
    return True
