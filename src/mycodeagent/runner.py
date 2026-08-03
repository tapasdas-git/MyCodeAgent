"""Omnigent process construction, execution, timeouts, and cleanup."""

from __future__ import annotations

import argparse
import os
import selectors
import signal
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import monotonic

from .paths import ALLOWED_EFFORTS, ROOT, SETTINGS_PATH, WORKFLOW_PATH
from .tasks import TaskSpec
from .tracing import print_structured_workflow_output, task_trace_path, write_trace, write_trace_output


@dataclass(frozen=True)
class WorkflowResult:
    """Terminal result of one Omnigent invocation."""

    exit_code: int
    report: str | None = None


def positive_timeout(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return parsed


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Terminate a runner and all child processes after a timeout."""
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:  # pragma: no cover
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover
            process.kill()
        process.wait()


def stream_process_output(
    command: list[str], *, environment: dict[str, str], timeout: int, trace_path: Path
) -> WorkflowResult:
    """Persist raw runner output while showing only its final structured report."""
    process = subprocess.Popen(
        command, cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, start_new_session=os.name == "posix",
    )
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    started_at = monotonic()
    started_at_wall = datetime.now().astimezone()
    raw_output: list[str] = []
    timed_out = False
    try:
        while selector.get_map():
            remaining = timeout - (monotonic() - started_at)
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in selector.select(timeout=min(0.25, remaining)):
                line = key.fileobj.readline()
                if line:
                    write_trace_output(trace_path, line)
                    raw_output.append(line)
                else:
                    selector.unregister(key.fileobj)
            if process.poll() is not None:
                for line in process.stdout:
                    write_trace_output(trace_path, line)
                    raw_output.append(line)
                try:
                    selector.unregister(process.stdout)
                except KeyError:
                    pass

        if timed_out:
            terminate_process_group(process)
            ended_at = datetime.now().astimezone()
            elapsed = monotonic() - started_at
            write_trace(trace_path, f"WORKFLOW_TIMEOUT started_at={started_at_wall.isoformat()} ended_at={ended_at.isoformat()} elapsed_seconds={elapsed:.2f} limit_seconds={timeout}")
            print(f"Workflow timed out at {ended_at.isoformat(timespec='seconds')} after {elapsed:.1f}s. Trace: {trace_path}", file=sys.stderr)
            return WorkflowResult(124)

        return_code = process.wait()
        report = print_structured_workflow_output(raw_output, trace_path)
        ended_at = datetime.now().astimezone()
        elapsed = monotonic() - started_at
        if return_code == 0 and report is None:
            return_code = 1
            write_trace(trace_path, "WORKFLOW_PROTOCOL_ERROR reason=missing_structured_final_report")
            print("Workflow failed validation: missing required structured final report.", file=sys.stderr)
        write_trace(trace_path, f"WORKFLOW_FINISHED exit_code={return_code} started_at={started_at_wall.isoformat()} ended_at={ended_at.isoformat()} elapsed_seconds={elapsed:.2f}")
        print(f"Workflow finished at {ended_at.isoformat(timespec='seconds')} after {elapsed:.1f}s (exit code {return_code}).")
        return WorkflowResult(return_code, report)
    finally:
        selector.close()


def execute_omnigent_stage(
    prompt: str, *, target_stage: str | None = None, timeout_seconds: int | None = None,
    task: TaskSpec, todo_path: Path, delivery_approved: bool = False,
) -> WorkflowResult:
    """Render the workflow and execute one Omnigent invocation for a task."""
    with SETTINGS_PATH.open("rb") as settings_file:
        settings = tomllib.load(settings_file)
    required = ("harness", "model", "effort", "time_limit_seconds")
    missing = [key for key in required if not settings.get(key)]
    if missing:
        raise SystemExit(f"Missing required runtime setting(s): {', '.join(missing)}")
    if settings["harness"] != "codex":
        raise SystemExit("workflow_runtime.toml must use the supported 'codex' harness")
    if not isinstance(settings["model"], str) or not settings["model"].strip():
        raise SystemExit("workflow_runtime.toml model must be a non-empty string")
    if settings["effort"] not in ALLOWED_EFFORTS:
        raise SystemExit(f"workflow_runtime.toml effort must be one of: {', '.join(sorted(ALLOWED_EFFORTS))}")
    timeout = int(settings["time_limit_seconds"]) if timeout_seconds is None else timeout_seconds
    if timeout <= 0:
        raise SystemExit("timeout must be greater than zero")

    trace_path = task_trace_path(task.task_id)
    environment = os.environ.copy()
    environment.update({
        "OMNIGENT_WORKFLOW_MODEL": str(settings["model"]), "OMNIGENT_WORKFLOW_EFFORT": str(settings["effort"]),
        "TASK_ID": task.task_id, "TASK_DIR": str(task.workspace.relative_to(ROOT)), "TODO_PATH": str(todo_path.resolve()),
    })
    if delivery_approved:
        environment["MYCODEAGENT_REVIEW_STATUS"] = "APPROVED"
    rendered_workflow = WORKFLOW_PATH.read_text(encoding="utf-8").replace("${OMNIGENT_WORKFLOW_MODEL}", str(settings["model"])).replace("${OMNIGENT_WORKFLOW_EFFORT}", str(settings["effort"]))

    with tempfile.TemporaryDirectory(prefix="omnigent-workflow-") as temp_dir:
        rendered_path = Path(temp_dir) / WORKFLOW_PATH.name
        rendered_path.write_text(rendered_workflow, encoding="utf-8")
        if target_stage:
            prompt = f"STAGE ONLY: {target_stage}\nInvoke only the named workflow stage. Do not invoke, delegate to, or perform any other stage.\n\n{prompt}"
        command = ["omnigent", "run", str(rendered_path), "--harness", str(settings["harness"]), "--model", str(settings["model"]), "--no-session", "-p", prompt]
        write_trace(trace_path, f"WORKFLOW_STARTED task={task.task_id} stage={target_stage or 'full'} timeout_seconds={timeout}")
        print(f"Trace: {trace_path}")
        print(f"Workflow started at {datetime.now().astimezone().isoformat(timespec='seconds')}")
        try:
            return stream_process_output(command, environment=environment, timeout=timeout, trace_path=trace_path)
        except OSError as exc:
            write_trace(trace_path, f"WORKFLOW_LAUNCH_ERROR error={exc}")
            print(f"Could not start workflow: {exc}", file=sys.stderr)
            return WorkflowResult(1)
