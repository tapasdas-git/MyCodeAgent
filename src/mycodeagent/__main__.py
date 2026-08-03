#!/usr/bin/env python3
"""CLI argument routing for MyCodeAgent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .delivery import run_approved_delivery
from .paths import ROOT
from .runner import execute_omnigent_stage, positive_timeout
from .submission import submit_ready_queue
from .tasks import get_task_spec, parse_todo_file
from .worktrees import run_submission_in_worktree


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser without performing workflow work."""
    parser = argparse.ArgumentParser(prog="mycodeagent", description="MyCodeAgent Workflow CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    submit_parser = subparsers.add_parser("submit", help="Run the first ready task in TODO.md order")
    submit_parser.add_argument("--todo", type=Path, default=ROOT / "TODO.md", help="Path to TODO.md file")
    submit_parser.add_argument("--mode", choices=("1", "2", "3"), default="2", help="1=implementation only; 2=implementation and review (default); 3=implementation, review, and PR.")
    submit_parser.add_argument("--all", action="store_true", help="Explicitly process all ready tasks sequentially (default: one task only).")
    submit_parser.add_argument("--task-id", help="Select one ready task explicitly (required with --worktree when multiple tasks are ready).")
    submit_parser.add_argument("--worktree", action="store_true", help="Create an isolated feature worktree from origin/main for one task.")
    submit_parser.add_argument("--stop-on-error", action="store_true", help="Stop the queue after the first failed task (default: continue to later tasks).")
    submit_parser.add_argument("--timeout-seconds", type=positive_timeout, default=None, help="Maximum runtime for one workflow invocation.")

    for stage_cmd in ("run", "verify", "review", "deliver"):
        stage_parser = subparsers.add_parser(stage_cmd, help=f"Run the '{stage_cmd}' workflow stage")
        stage_parser.add_argument("task_id", help="Task ID (e.g., TASK-101)")
        stage_parser.add_argument("--todo", type=Path, default=ROOT / "TODO.md", help="Path to TODO.md file")
        stage_parser.add_argument("--timeout-seconds", type=positive_timeout, default=None, help="Maximum runtime for one workflow invocation.")
        if stage_cmd == "deliver":
            stage_parser.add_argument("--approved", action="store_true", help="Explicitly authorize delivery after an APPROVED review.")
        if stage_cmd == "review":
            stage_parser.add_argument("--remediate", action="store_true", help="Make one targeted fix attempt after findings, then re-review.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.command:
        build_parser().print_help()
        return 1
    try:
        tasks = parse_todo_file(args.todo)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.command == "submit":
        if args.all and args.mode == "3":
            print("Refusing batch delivery: mode 3 may create a PR for only one explicitly selected task.", file=sys.stderr)
            return 1
        if args.worktree:
            if args.all:
                print("Refusing --all with --worktree; start one task worktree per command.", file=sys.stderr)
                return 1
            selected_task = (args.task_id or next((task_id for task_id, info in tasks.items() if info["state"] == "ready"), None))
            if selected_task is None:
                print("No task with state 'ready' found in TODO.md.", file=sys.stderr)
                return 1
            try:
                return run_submission_in_worktree(args.todo, task_id=selected_task, mode=args.mode, timeout_seconds=args.timeout_seconds)
            except (RuntimeError, ValueError) as exc:
                print(f"Worktree workflow refused: {exc}", file=sys.stderr)
                return 1
        return submit_ready_queue(args.todo, timeout_seconds=args.timeout_seconds, once=not args.all, stop_on_error=args.stop_on_error, mode=args.mode)

    target_task = args.task_id.upper()
    if target_task not in tasks:
        print(f"Task ID '{target_task}' not found in {args.todo.name}.", file=sys.stderr)
        return 1
    try:
        task = get_task_spec(args.todo, target_task)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.command == "verify":
        print(f"Running implementation and review loop for {target_task} without delivery...")
        return execute_omnigent_stage(
            f"IMPLEMENT AND REVIEW ONLY\nExecute the bounded implementation and review loop for {target_task}. Stop after the final review result and do not update the changelog or create a pull request.",
            timeout_seconds=args.timeout_seconds, task=task, todo_path=args.todo,
        ).exit_code
    if args.command == "review":
        if args.remediate:
            print(f"Running review and targeted remediation loop for {target_task} without delivery...")
            prompt = f"REVIEW AND REMEDIATE ONLY\nReview {target_task}. If findings are returned, send the complete findings to the implementation agent for one targeted fix attempt, then re-review. Stop after the final review result without delivery."
        else:
            print(f"Running read-only review for {target_task} without remediation or delivery...")
            prompt = f"REVIEW ONLY\nReview {target_task} once. Report findings or approval, then stop. Do not invoke implementation, update the changelog, or create a pull request."
        return execute_omnigent_stage(prompt, timeout_seconds=args.timeout_seconds, task=task, todo_path=args.todo).exit_code
    if args.command == "deliver" and not args.approved:
        print("Refusing delivery: re-run with --approved after an APPROVED review result.", file=sys.stderr)
        return 1

    if args.command == "deliver":
        return run_approved_delivery(task, timeout_seconds=args.timeout_seconds or 600)

    if args.command == "run":
        print(f"Running implementation stage for {target_task}...")
        return execute_omnigent_stage(
            f"Target stage troubleshooting for {target_task} using implement_task.",
            target_stage="implement_task", timeout_seconds=args.timeout_seconds, task=task, todo_path=args.todo,
        ).exit_code


if __name__ == "__main__":
    raise SystemExit(main())
