# Project TODOs

## TASK-040 | completed | P0 | Fix authentication token expiration bug
- Outcome: Refresh tokens automatically 5 minutes before expiration to prevent session drops.
- Depends on: None
- Repository: /path/to/repo
- Harness: primary-name
- Night-ready: yes
- Acceptance:
  - User session remains uninterrupted during active 2-hour window.
  - Unit tests verify silent token refresh trigger.
- Approved by: Alex Mercer
- Approval reference: 2026-07-20 Slack sign-off

## TASK-041 | working | P1 | Add request latency metrics to dashboard
- Outcome: Expose Prometheus metrics for P95 and P99 HTTP request response times.
- Depends on: TASK-040
- Repository: /path/to/repo
- Harness: primary-name
- Acceptance:
  - Metric endpoint `/metrics` exposes `http_request_duration_seconds`.
  - Grafana panel imports metrics cleanly.
- Approved by: Dev Lead
- Approval reference: 2026-07-21 Jira SWAF-041

## TASK-042 | completed | P1 | Implement palindrome utility function
- Outcome: Pure Python function that checks if input string is a valid palindrome, ignoring case and special characters.
- Depends on: None
- Repository: /path/to/repo
- Harness: primary-name
- Night-ready: yes
- Acceptance:
  - Returns `True` for "A man, a plan, a canal: Panama".
  - Returns `False` for "hello world".
  - Unit test suite passes with >= 95% coverage.
- Approved by: Code Reviewer
- Approval reference: 2026-07-22 PR review thread

## TASK-043 | Completed | P2 | Update CLI logging to support JSON output
- Outcome: Allow passing `--format=json` to output structured logs.
- Depends on: None
- Acceptance:
  - Console outputs valid JSON lines when flag is present.
- Approved by: Tech Lead
- Approval reference: 2026-07-23 Arch Sync

## TASK-044 | blocked | P3 | Refactor legacy database connector
- Outcome: Replace deprecated ORM call patterns with async context managers.
- Depends on: TASK-045
- Acceptance:
  - Database pool cleanly releases connections after timeout.
- Approved by: Alex Mercer
- Approval reference: 2026-07-25 Architecture board

## SWAF-045 | reviewed | P1 | Implement Fibonacci series utility module
- Outcome: Pure Python module and unit tests for fibonacci, handling edge cases containing sequence generation logic and CLI interface.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyCodeAgent.git
- Harness: primary-name
- Night-ready: yes
- Acceptance:
  - Source: `workspace/fibonacci/Coding/`
  - Test file created at `workspace/fibonacci/test/test_checker.py`.
  - Utility function `fibonacci(n: int) -> list[int]` correctly handles edge cases (N=0, N=1, negative inputs).
  - Calling `fibonacci(10)` returns `[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]`.
  - Automated unit test suite passes with 100% code coverage.
- Approved by: Tech Lead
- Approval reference: 2026-07-30 Arch Sync
## TASK-046 | failed | P1 | Implement palindrome detection utility module 
- Outcome: Pure Python module and unit tests for palindrome detection, handling edge cases, case-insensitivity, and special characters.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyCodeAgent.git
- Harness: primary-name
- Night-ready: yes
- Acceptance:
  - Source: `workspace/palindrome/Coding/`
  - Test file created at `workspace/palindrome/test/test_checker.py`.
  - Function `is_palindrome(text: str) -> bool` ignores spaces, punctuation, and casing.
  - Returns `True` for "A man, a plan, a canal: Panama".
  - Returns `False` for "Hello World".
  - Unit test suite passes with 100% test coverage.
- Approved by: Tech Lead
- Approval reference: 2026-07-30 Arch Sync

## TASK-047 | completed | P3 | Create a utility module in `prime_checker` to verify prime numbers and return prime factors.
- Outcome: Pure Python module and unit tests for palindrome detection, handling edge cases, case-insensitivity, and special characters.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyOmnigent.git
- Harness: primary-name
- Night-ready: yes
Acceptance:
  - Source file created at `prime_checker/Coding/checker.py`.
  - Test file created at `prime_checker/test/test_checker.py`.
  - Function `is_prime(n: int) -> bool` correctly identifies prime numbers (e.g., returns `True` for 7, `False` for 4, and `False` for numbers <= 1).
  - Function `get_prime_factors(n: int) -> list[int]` returns prime factors (e.g., `[2, 3, 3]` for 18).
  - Unit test suite passes with 100% test coverage.
- Approved by: Tech Lead
- Approval reference: 2026-07-30 Arch Sync

## TASK-101 | completed | P1 | [FEATURE] Build Agentic Flight Booking Engine in `workspace/flight_booking_agent/`
- Outcome: Implement a multi-agent flight search and booking engine using Python and Pydantic as a new core feature. Process natural language requests, query flight options, evaluate preferences, and handle booking state validation.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyCodeAgent.git
- Harness: primary-name
- Night-ready: yes
- Architecture & Tech Stack:
  - Framework: Python 3.11+, Pydantic (v2) for structured schema validations
  - Target Architecture Pattern: ReAct routing and tool-calling loop. Use the standard agentic runtime policy in `coding_agent.yaml`.
  - Groq Tool-Calling Protocol: Use Groq native chat-completions tool calling with declared function schemas and `tool_choice="auto"`. Keep per-request message history; append the assistant tool-call message and each matching `role: "tool"` observation with its `tool_call_id`. Support multiple tool calls in one model response.
    1. Search Agent: Queries flight database/mock API.
    2. Preference/Policy Agent: Filters options based on budget, seat preference, and bag policies.
    3. Booking Agent: Handles reservation execution and confirmation generation.
- Provider: Use Groq through an injectable adapter and load `GROQ_API_KEY` dynamically.
- Booking Safety: Resolve the canonical flight record before reserving; validate price, inventory, policy, authorization, and request identity in deterministic code. Searching or selecting an option must not reserve inventory.
- Workspace Boundary:
  - Source: `workspace/flight_booking_agent/Coding/`
  - Tests: `workspace/flight_booking_agent/test/`
  - Requirements: `workspace/flight_booking_agent/Coding/requirements.txt`
  - Rule: All files and modifications must stay strictly inside `workspace/flight_booking_agent/`. Do not modify root or external repository files.
- Acceptance:
  - Isolated workspace created at `workspace/flight_booking_agent/`.
  - Source files created under `workspace/flight_booking_agent/Coding/`:
    - `requirements.txt`: Local dependencies (`pydantic>=2.0.0`, `groq`, `pytest`).
    - `schemas.py`: Pydantic models for `FlightQuery`, `FlightOption`, and `BookingConfirmation`.
    - `tools.py`: Mock Flight Search API and Mock Reservation Gateway.
    - `agents.py`: Groq client/adapter boundary, Search Agent, Preference/Policy Agent, Booking Agent, and ReAct Supervisor Orchestrator.
  - Test files created under `workspace/flight_booking_agent/test/`:
    - `test_flight_search.py`: Intent parsing and policy filtering.
    - `test_booking_flow.py`: End-to-end booking, authorization, idempotency, budget, and inventory failures.
    - `test_react_protocol.py`: Native Groq tool-call history, invalid/multiple calls, and loop termination.
    - `test_runtime_harness.py`: Standard runtime-harness policy and invalid model output before side effects.
  - Test suite passes with 100% pass rate locally.
- Approved by: Tech Lead
- Approval reference: 2026-08-01 Arch Sync

## TASK-102 | reviewed | P3 | [SMOKE] Build a label-normalization utility for mode-3 workflow validation
- Source: `workspace/mode3_smoke/Coding/`
- Outcome: Create a small, dependency-free Python utility and isolated tests so the complete implementation, review, and delivery workflow can be exercised without external APIs or existing task files.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyCodeAgent.git
- Harness: codex
- Night-ready: no
- Workspace Boundary:
  - Application code: `workspace/mode3_smoke/Coding/`
  - Tests: `workspace/mode3_smoke/test/`
  - Do not modify files outside `workspace/mode3_smoke/`.
- Acceptance:
  - Create `workspace/mode3_smoke/Coding/label_normalizer.py` with `normalize_label(value: str) -> str`.
  - The function trims leading/trailing whitespace, case-folds text, collapses internal whitespace, and joins words with `-`.
  - `normalize_label("  Hello   World  ")` returns `"hello-world"`.
  - `normalize_label("MiXeD Case")` returns `"mixed-case"`.
  - Empty or whitespace-only input raises `ValueError`; non-string input raises `TypeError`.
  - Create `workspace/mode3_smoke/test/test_label_normalizer.py` covering every acceptance criterion.
  - Run `venv/bin/python -m pytest -q workspace/mode3_smoke/test` and report a passing result.
- Approved by: Tech Lead
- Approval reference: 2026-08-02 mode-3 smoke-test authorization

## TASK-103 | reviewed | P2 | [FEATURE] Build Currency Exchange Engine in `workspace/currency_exchange/`
- Outcome: Implement a pure Python currency exchange and conversion module with Pydantic schema validation and mock exchange rate lookup tools.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyOCodeAgent.git
- Harness: primary-name
- Night-ready: yes
- Architecture & Tech Stack:
  - Framework: Python 3.11+, Pydantic (v2)
  - Pattern: Tool-Calling / Utility Router Pattern
    1. Exchange Rate Provider Tool: Mock API returns exchange rates for common currencies (USD, INR, EUR, GBP).
    2. Conversion Engine: Validates input currency codes, calculates conversion amounts, and formats output.
- API Key & Secrets Management:
  - Environment Variable: Expects `EXCHANGE_API_KEY` loaded dynamically via `os.getenv()`.
  - Security Requirement: Do not hardcode API keys in any file.
  - Mocking in Tests: Unit tests must use `unittest.mock` or `pytest` fixtures so tests pass completely offline.
- Workspace Boundary:
  - Source: `workspace/currency_exchange/Coding/`
  - Tests: `workspace/currency_exchange/test/`
  - Requirements: `workspace/currency_exchange/Coding/requirements.txt`
  - Rule: All generated files must stay strictly inside `workspace/currency_exchange/`. Do not edit files outside this directory.
- Acceptance:
  - Isolated workspace directory created at `workspace/currency_exchange/`.
  - Source files created under `workspace/currency_exchange/Coding/`:
    - `requirements.txt`: Local dependencies (`pydantic>=2.0.0`, `pytest`).
    - `schemas.py`: Pydantic models for `ConversionRequest` and `ConversionResult`.
    - `converter.py`: Core logic for fetching rates and performing conversions.
  - Test files created under `workspace/currency_exchange/test/`:
    - `test_converter.py`: Verifies conversion logic, currency validation, and offline rate lookup mocks.
  - Test suite passes with 100% pass rate locally.
- Approved by: Tech Lead
- Approval reference: 2026-08-02 Arch Sync
## TASK-104 | delivered | P2 | [FEATURE] Build Prompt Sanitizer Engine in `workspace/prompt_optimizer/`
- Outcome: Implement a Python-based utility module with Pydantic validation that sanitizes user prompts (stripping PII/secrets) and formats them into structured LLM system/user prompt pairs.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyCodeAgent.git
- Harness: primary-name
- Night-ready: yes
- Architecture & Tech Stack:
  - Framework: Python 3.11+, Pydantic (v2)
  - Pattern: Rule-Based Processing & Formatting Pipeline
    1. Secret/PII Scanner: Detects and redacts potential API keys, credit card patterns, and email addresses.
    2. Prompt Formatter: Converts raw user input into structured `SystemMessage` and `UserMessage` schemas.
- API Key & Secrets Management:
  - Environment Variable: Expects `PROMPT_OPT_KEY` loaded dynamically via `os.getenv()`.
  - Security Requirement: Do not hardcode API keys or credentials in any source or test file.
  - Mocking in Tests: Unit tests must run offline using local test inputs and standard assertions without external network calls.
- Workspace Boundary:
  - Source: `workspace/prompt_optimizer/Coding/`
  - Tests: `workspace/prompt_optimizer/test/`
  - Requirements: `workspace/prompt_optimizer/Coding/requirements.txt`
  - Rule: All generated files must stay strictly inside `workspace/prompt_optimizer/`. Do not edit files outside this directory.
- Acceptance:
  - Isolated workspace directory created at `workspace/prompt_optimizer/`.
  - Source files created under `workspace/prompt_optimizer/Coding/`:
    - `requirements.txt`: Local dependencies (`pydantic>=2.0.0`, `pytest`).
    - `schemas.py`: Pydantic models for `RawPrompt`, `SanitizedPrompt`, and `FormattedLLMPrompt`.
    - `sanitizer.py`: Core logic for PII/secret redaction and prompt formatting.
  - Test files created under `workspace/prompt_optimizer/test/`:
    - `test_sanitizer.py`: Verifies redaction rules (emails, API keys), error handling, and structured formatting.
  - Test suite passes with 100% pass rate locally.
- Approved by: Tech Lead
- Approval reference: 2026-08-02 Arch Sync

## TASK-105 | delivered | P2 | [FEATURE] Build LRU Cache Data Structure in `workspace/lru_cache/`
- Outcome: Implement a thread-safe, generic Least Recently Used (LRU) Cache data structure in Python with capacity limits and Pydantic validation for cache stats.
- Depends on: None
- Repository: https://github.com/tapasdas-git/MyOmnigent.git
- Harness: primary-name
- Night-ready: yes
- Architecture & Tech Stack:
  - Framework: Python 3.11+, Pydantic (v2)
  - Data Structure / Pattern: Doubly Linked List + Hash Map (or `collections.OrderedDict`) for $O(1)$ lookups and updates.
    1. LRUCache Engine: Supports `get(key)`, `put(key, value)`, `clear()`, and `get_stats()`.
    2. Stats Tracker: Tracks hit rate, miss rate, current size, and total capacity.
- API Key & Secrets Management:
  - Security Requirement: No network calls or API keys required for this internal data structure.
- Workspace Boundary:
  - Source: `workspace/lru_cache/Coding/`
  - Tests: `workspace/lru_cache/test/`
  - Requirements: `workspace/lru_cache/Coding/requirements.txt`
  - Rule: All generated files must stay strictly inside `workspace/lru_cache/`. Do not edit files outside this directory.
- Acceptance:
  - Isolated workspace directory created at `workspace/lru_cache/`.
  - Source files created under `workspace/lru_cache/Coding/`:
    - `requirements.txt`: Local dependencies (`pydantic>=2.0.0`, `pytest`).
    - `schemas.py`: Pydantic models for `CacheStats` and `CacheEntry`.
    - `cache.py`: Core `LRUCache` class implementation with eviction policies.
  - Test files created under `workspace/lru_cache/test/`:
    - `test_cache.py`: Verifies $O(1)$ updates, eviction order when capacity limit is reached, cache hits/misses stats, and edge cases.
  - Test suite passes with 100% pass rate locally.
- Approved by: Tech Lead
- Approval reference: 2026-08-02 Arch Sync
