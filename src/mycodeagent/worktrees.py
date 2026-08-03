"""Task-scoped Git worktree creation and isolated workflow launching."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .paths import ROOT, TRACE_DIR
from .tasks import get_task_section, get_task_spec, parse_todo_file, update_task_state


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *arguments], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


def _worktree_path(task_id: str) -> Path:
    """Keep task worktrees beside the primary checkout, never inside its diff."""
    return ROOT.parent / ".mycodeagent-worktrees" / task_id.lower()


def _branch_exists(branch: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(ROOT), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def _create_worktree(task_id: str) -> Path:
    branch = f"feature/{task_id.lower()}"
    destination = _worktree_path(task_id)
    if destination.exists():
        raise RuntimeError(f"Worktree path already exists: {destination}")
    if _branch_exists(branch):
        raise RuntimeError(f"Branch already exists: {branch}. Reuse or remove its existing worktree explicitly.")

    _git("fetch", "origin", "main")
    base_revision = _git("rev-parse", "--verify", "origin/main^{commit}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _git("worktree", "add", "-b", branch, str(destination), base_revision)
    return destination


def _write_work_order(workspace: Path, todo_path: Path, task_id: str) -> tuple[Path, str]:
    """Freeze only the selected task where the isolated agent can read it."""
    work_order_dir = workspace / ".mycodeagent" / "work-orders"
    work_order_dir.mkdir(parents=True, exist_ok=True)
    work_order = work_order_dir / f"{task_id}.md"
    section = get_task_section(todo_path, task_id)
    work_order.write_text(section, encoding="utf-8")
    work_order.chmod(0o600)
    visible_todo = workspace / "TODO.md"
    original_todo = visible_todo.read_text(encoding="utf-8")
    if f"## {task_id} |" not in original_todo:
        visible_todo.write_text(
            original_todo.rstrip() + "\n\n<!-- MyCodeAgent active work order; removed after this run. -->\n\n" + section,
            encoding="utf-8",
        )
    return work_order, original_todo


def run_submission_in_worktree(
    todo_path: Path, *, task_id: str, mode: str, timeout_seconds: int | None
) -> int:
    """Run one selected ready task in a clean branch/worktree created from main."""
    task_id = task_id.upper()
    task = get_task_spec(todo_path, task_id)
    if task.state != "ready":
        raise ValueError(f"Task {task_id} must be in state 'ready' to create a worktree")

    workspace = _create_worktree(task_id)
    work_order, original_workspace_todo = _write_work_order(workspace, todo_path, task_id)
    if not update_task_state(todo_path, task_id, "working", expected_state="ready"):
        raise RuntimeError(f"Could not mark {task_id} working after creating its worktree")

    command = [sys.executable, "-m", "mycodeagent", "submit", "--todo", str(work_order), "--mode", mode]
    if timeout_seconds is not None:
        command.extend(["--timeout-seconds", str(timeout_seconds)])
    environment = os.environ.copy()
    environment.update({
        "MYCODEAGENT_ROOT": str(workspace),
        "MYCODEAGENT_TRACE_DIR": str(TRACE_DIR),
        "MYCODEAGENT_WORKFLOW_PATH": str(ROOT / "coding_agent.yaml"),
        "MYCODEAGENT_HELPER_PATH": str(ROOT / "scripts" / "workflow_helpers.py"),
        "MYCODEAGENT_APPROVAL_PATH": str(ROOT / "git_approval.toml"),
    })
    print(f"Worktree: {workspace}")
    print(f"Branch: feature/{task_id.lower()} (base: origin/main)")
    try:
        try:
            completed = subprocess.run(command, cwd=workspace, env=environment, check=False)
        except OSError as exc:
            update_task_state(todo_path, task_id, "failed", expected_state="working")
            raise RuntimeError(f"Could not start isolated task workflow: {exc}") from exc
    finally:
        (workspace / "TODO.md").write_text(original_workspace_todo, encoding="utf-8")

    child_state = parse_todo_file(work_order).get(task_id, {}).get("state", "failed")
    if child_state not in {"implemented", "reviewed", "delivered", "failed"}:
        child_state = "failed"
    if not update_task_state(todo_path, task_id, child_state, expected_state="working"):
        raise RuntimeError(f"Worktree completed, but primary TODO state for {task_id} could not be updated")
    return completed.returncode
