# Autonomous Build Prompt: mcptest

> **A pytest plugin for testing MCP servers without spinning up an LLM.**

| Key | Value |
|-|-|
| Language | Python 3.10+ |
| Distribution | PyPI (pip install pytest-mcptest) |
| License | MIT |
| Category | AI Tooling / Testing |

## Instructions

You are building **mcptest** from scratch as an autonomous agent. Complete all 6 phases below in order. Do NOT ask for human input — make reasonable decisions and keep moving. Read `SPEC.md` in this directory for the full project specification before starting.

## Phase 1: Initialize

Create the project from scratch with proper structure.

```bash
# mkdir mcptest && cd mcptest
# uv init --lib
# uv add pytest httpx pydantic mcp
# uv add --dev pytest-cov ruff
```

- Initialize a git repository
- Create the standard project structure for Python 3.10+
- Install all dependencies listed in the spec
- Create a `CLAUDE.md` with project conventions (coding style, commit format, test patterns)
- Make an initial commit: "chore: initialize mcptest project"

## Phase 2: Plan

Read `SPEC.md` thoroughly and create `PLAN.md`:

- Break down ALL core features into ordered implementation tasks
- Each task should be small enough to implement and test in one step
- Identify the critical path (what must be built first)
- Note any architectural decisions and their rationale
- List all CLI commands / API surfaces to implement
- Commit: "docs: add implementation plan"

## Phase 3: Implement

Follow `PLAN.md` step by step:

- Implement the core architecture first (protocols, base classes, plugin system)
- Then implement each feature one at a time
- Write clean, idiomatic Python 3.10+ code
- Follow the conventions in `CLAUDE.md`
- Commit after each logical unit of work with descriptive messages
- If a design decision isn't specified in the spec, choose the simplest working approach

## Phase 4: Test

Write comprehensive tests and ensure everything passes:

```bash
# uv run pytest
# uv run ruff check .
```

- Write unit tests for all core logic
- Write integration tests for CLI commands / public API
- Test edge cases and error paths
- Achieve >80% code coverage on core modules
- Fix any failing tests before proceeding
- Commit: "test: add comprehensive test suite"

## Phase 5: Refine

Polish the code and fix any issues:

```bash
# uv run ruff check . --fix
# uv run ruff format .
```

- Run linter and fix all issues
- Run formatter
- Review all public APIs for consistency and usability
- Ensure all CLI commands work exactly as documented in the spec
- Verify error messages are clear and actionable
- Remove any dead code or TODOs
- Commit: "refactor: polish and lint cleanup"

## Phase 6: Finish

Finalize the project for release:

- Write a comprehensive README.md with:
  - Project description and motivation
  - Installation instructions
  - Quick-start usage examples
  - Full CLI/API reference
  - Contributing guide section
  - License
- Create a `.pre-commit-hooks.yaml` if the spec mentions pre-commit integration
- Create a GitHub Actions CI workflow (`.github/workflows/ci.yml`)
- Verify ALL success criteria from `SPEC.md` are met
- Run the full test suite one final time
- Final commit: "docs: add README and CI configuration"

## Guardrails

- **No placeholders**: Every function must have a real implementation, not `pass` or `TODO`
- **No over-engineering**: Build exactly what the spec says, nothing more
- **Test everything**: If it's a core feature, it has a test
- **Commit often**: Small, logical commits with descriptive messages
- **Stay focused**: If you hit a blocker, simplify the approach rather than adding complexity
