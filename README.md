MyCodeAgent 

MyCodeAgent is an autonomous, agentic task-execution engine and CLI tool designed to automate software feature development, adversarial code reviews, changelog updates, and GitHub Pull Request delivery.

By combining high-reasoning AI models (for code creation and automated security/guideline reviews) with deterministic Python scripting (for Git lifecycle management and changelog generation), MyCodeAgent delivers a controlled task-resolution workflow with minimal token usage and high reliability.

***
💡 Key Features & Architecture

```text
                               ┌────────────────────────────────────────┐
                               │ 1. TASK PICKUP                         │
                               │    Parses 'ready' tasks from TODO.md   │
                               └──────────────────┬─────────────────────┘
                                                  │
                                                  v
                               ┌────────────────────────────────────────┐
                               │ 2. IMPLEMENT TASK (AI Agent)           │
                               │    Isolated workspace creation         │
                               │    Generates code, dependencies & tests│
                               └──────────────────┬─────────────────────┘
                                                  │
                                                  v
                               ┌────────────────────────────────────────┐
                               │ 3. ADVERSARIAL CODE REVIEW (AI Agent)   │
                               │    Inspects diffs vs. guidelines       │
                               │    Verifies 100% test suite pass rate  │
                               │    Scans for security & key leaks      │
                               └─────────┬────────────────────┬─────────┘
                                         │                    │
                                [CHANGES_REQUESTED]        [APPROVED]
                                         │                    │
                                         v                    v
                                  ┌───────────────────┐   ┌───────────────────┐
                                  │ FIX & RE-REVIEW   │   │ 4. UPDATE CHANGELOG│
                                  │ (ONE ATTEMPT)     │   │    Deterministic  │
                                  └───────────────────┘   │    Python Script  │
                                                    └─────────┬─────────┘
                                                              │
                                                              v
                                                    ┌───────────────────┐
                                                    │ 5. CREATE PULL REQ│
                                                    │    Pushes branch  │
                                                    │    Opens GitHub PR│
                                                    └───────────────────┘

Automated Task Ingestion: Scans TODO.md for structured tasks marked as ready.

Isolated Task Workspaces: Generates feature implementations and unit tests within scoped task directories to avoid cross-task pollution.

Adversarial Code Review: Evaluates task changes against customized guidelines (codeReviewGuideline.md), test suite execution results, and security scans before approving. `CHANGES_REQUESTED` findings are sent back to the implementation agent for one targeted remediation attempt; only an explicit `APPROVED` result proceeds to delivery.

Deterministic Delivery Pipeline: Executes branch creation, changelog tracking, and GitHub PR creation using deterministic Python helpers (saving tokens and eliminating non-deterministic Git errors).

🛠️ Technology Stack & Dependencies
Language & Runtime: Python 3.8+ (Recommended Python 3.11+)

Agent Framework & Runner: Omnigent Core Engine (omnigent)

Version Control & Integration: Git, GitHub CLI (gh)

Testing Frameworks: pytest, Python unittest

Configuration Formats: YAML (.yaml), TOML (.toml), Markdown (.md)

***
📋 Prerequisites

🔧 Installing the Omnigent Core Engine

pip install omnigent

omnigent setup


Before setting up MyCodeAgent in a fresh environment, ensure the following dependencies and tools are installed and configured:

Python 3.8+
Check installation:
python3 --version

Git
Installed and configured with your target repository:
git --version

GitHub CLI (gh)
Required for automated Pull Request creation during the delivery stage.
Authenticate your active session:
gh auth login
gh auth status

Omnigent Binary / Core Runner
Ensure omnigent is installed and accessible in your environment's $PATH:
omnigent --version

***
📁 Project Directory Structure

For MyCodeAgent to locate configuration files and source code correctly, ensure your repository root matches this layout. The CLI loads `coding_agent.yaml` as its active Codex/Omnigent workflow definition; `omnigent_bugfix_workflow.yaml` is not used by the current CLI.

```text
MyCodeAgent/                        # Project Root Directory
├── TODO.md                        # Task queue file containing structured tasks
├── CHANGELOG.md                   # Automated release changelog
├── codeReviewGuideline.md         # Enterprise review & security standards
├── pyproject.toml                 # Package configuration & entry points
├── workflow_runtime.toml          # Model, harness, and timeout runtime settings
├── coding_agent.yaml              # Active Codex/Omnigent workflow stages
├── git_approval.toml             # Approved Git identity & remote repository rules
├── README.md                      # Documentation
├── scripts/
│   └── workflow_helpers.py        # Deterministic Python scripts (Changelog & PR)
└── src/
    └── mycodeagent/
        ├── __init__.py        # Package initialization
        ├── __main__.py        # CLI argument routing and console entry point
        ├── paths.py           # Repository paths and runtime constants
        ├── tasks.py           # TODO parsing, workspace validation, task states
        ├── tracing.py         # Secret-redacted task traces and terminal reports
        ├── runner.py          # Omnigent process, timeout, and cleanup logic
        ├── delivery.py        # Deterministic changelog and PR helper execution
        └── submission.py      # One-task and explicit batch submission modes


🚀 Quickstart & Installation
Clone the Repository

git clone https://github.com/tapasdas-git/MyCodeAgent.git

cd MyCodeAgent

Create and Activate Virtual Environment

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install MyCodeAgent in Editable Mode

pip install -e .

📖 Usage Guide

### Execute the automated workflow

`submit` processes the first `ready` task in `TODO.md` and exits. Select the level of automation with `--mode`:

| Mode | Command | What it runs | Final task state on clean workflow exit |
| --- | --- | --- | --- |
| 1 | `mycodeagent submit --mode 1` | Implementation only | `implemented` |
| 2 (default) | `mycodeagent submit --mode 2` | Implementation, tests, review, at most one remediation, re-review | `reviewed` |
| 3 | `mycodeagent submit --mode 3` | Mode 2, then deterministic changelog and PR delivery only after verified `APPROVED` | `delivered` |

Run the default mode (mode 2):

```bash
mycodeagent submit
```

```bash
# Mode 1 — implementation only
mycodeagent submit --mode 1

# Mode 2 — implementation and bounded review, without PR delivery
mycodeagent submit --mode 2

# Mode 3 — full workflow; deterministic PR delivery only after verified APPROVED review
mycodeagent submit --mode 3
```

Use a custom TODO file:

```bash
mycodeagent submit --todo /path/to/custom_todo.md
```

Before a task starts it is marked `working`. A timeout, runner failure, or invalid task configuration becomes `failed`. `reviewed` means the workflow process finished; inspect its trace to confirm `APPROVED` and any PR URL before manually changing task state.

### Batch mode

Process all ready tasks sequentially, continuing after failures:

```bash
mycodeagent submit --all
```

Stop the batch after the first failure:

```bash
mycodeagent submit --all --stop-on-error
```

For safety, batch mode cannot be combined with mode 3 because it could create multiple PRs.

### Parallel task worktrees

Use one Git worktree per task when more than one task needs its own pull request.
Each worktree must start from `origin/main`; do not create a new task branch from
another task's feature branch. The CLI resolves the repository from the current
worktree, so the same virtual environment and `mycodeagent` command can be used.

Let Python create and run a clean worktree for TASK-104:

```bash
mycodeagent submit --task-id TASK-104 --worktree --mode 3 --timeout-seconds 600
```

This creates a sibling worktree at `.mycodeagent-worktrees/task-104` beside the
primary checkout, on `feature/task-104` from `origin/main`. The selected task
section is frozen as private worktree metadata and logs remain in the primary
checkout. Run another task with its own `--task-id` command and terminal. Its
implementation, changelog update, commit, push, and PR are isolated from
TASK-104. Remove a worktree only after its PR is safely delivered or no longer
needed:

```bash
git worktree remove ../.mycodeagent-worktrees/task-104
```

### Direct modes

Use a direct command when you already know the task ID:

| Command | Action |
| --- | --- |
| `mycodeagent run TASK-101` | Implementation only |
| `mycodeagent verify TASK-101` | Implementation, review, bounded remediation, re-review; no PR |
| `mycodeagent review TASK-101` | Read-only review; no implementation changes |
| `mycodeagent review TASK-101 --remediate` | Review, one targeted fix attempt when needed, re-review; no PR |
| `mycodeagent deliver TASK-101 --approved` | Explicitly authorized PR delivery after an approved review |

Each workflow invocation is one-shot. The default runtime limit is 600 seconds; set a limit per command when needed:

```bash
mycodeagent run TASK-101 --timeout-seconds 900
mycodeagent review TASK-101 --remediate --timeout-seconds 600
```

### Monitoring task runs

Each invocation writes an append-only trace to `logs/<TASK_ID>.logs`. The trace
contains workflow start/finish markers, local start and end timestamps, elapsed
duration, selected stage mode, complete raw agent output, and timeout or launch
errors. To keep the terminal readable, it shows only the final structured agent
report; inspect the trace for the live/raw stream. Monitor an active run in
another terminal:

tail -f logs/TASK-101.logs

Direct Script Execution (Human-in-the-Loop Fallback)

To execute changelog updates or GitHub PR generation directly via the deterministic helper scripts:

Append task entry to CHANGELOG.md
python3 scripts/workflow_helpers.py changelog --task-id "TASK-100"

Create feature branch, commit, push, and open Pull Request on GitHub
python3 scripts/workflow_helpers.py pr --task-id "TASK-100" --task-dir "flight_booking"

📝 Defining Tasks in TODO.md

### Coding-agent implementation contract

`mycodeagent` invokes Codex through `coding_agent.yaml`. The task description is the source of truth; the coding agent must translate its architecture and acceptance criteria into implementation, tests, and a reviewable result. For every task, the implementation stage must:

- inspect the referenced repository files before choosing dependencies or APIs;
- keep changes inside the task's stated workspace boundary;
- map every acceptance criterion to at least one test;
- inject external integrations behind interfaces and use fakes/mocks in tests; and
- report the task ID, changed files, acceptance-test evidence, and any unsupported requirement rather than silently substituting an unrelated design.

For an AI-agent task, naming an LLM provider is an implementation requirement. For example, a Groq ReAct feature must include a dynamically configured Groq adapter, validated tool inputs and outputs, and an explicit thought/action/observation loop with a bounded iteration count. A key lookup alone is not an LLM integration. Business-critical checks—such as price, inventory, policy, and booking confirmation—must remain deterministic code and must not rely on model output.

The Omnigent workflow is the outer development pipeline (implement, review, changelog, delivery). It is distinct from any multi-agent runtime that the task asks the coding agent to build.

TASK-100 | ready | high | Build Flight Booking Agent in flight_booking

  Description:
  Implement a flight search and booking module that processes natural language requests.

  Architecture & Boundaries:
Framework: Python 3.11+, Pydantic v2
Isolated Boundary: Source code lives in flight_booking/Coding/, tests in flight_booking/test/
Mocks: Mock external airline APIs for unit tests.

  Acceptance:
Isolated directory flight_booking/ created.
Dependencies defined in flight_booking/Coding/requirements.txt.
All unit tests pass with 100% pass rate.
