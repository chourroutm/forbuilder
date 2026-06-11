# Implementation Plan: forbuilder CLI

**Branch**: `002-cli` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)

## Summary

Add two console-script entry points (`forbild-head-gen`, `forbild-thorax-gen`) to the
existing `forbuilder` package. Both are implemented in a single module
`src/forbuilder/cli.py` using `argparse` from the Python standard library. No new runtime
dependencies are introduced. Each script is a thin wrapper: it parses arguments, calls
`forbuilder.generate` with the hardcoded template name, then calls `forbuilder.save`.

## Technical Context

**Language/Version**: Python 3.12
**New dependencies**: None — `argparse` is stdlib.
**Entry points**:
```
forbild-head-gen   = "forbuilder.cli:head_main"
forbild-thorax-gen = "forbuilder.cli:thorax_main"
```

## Constitution Check

### Pre-Design Check (GATE — passes)

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Code Quality | ✅ PASS | Single-module CLI; delegates to existing API; ruff enforced |
| II. Testing Standards | ✅ PASS | TDD cycle enforced; unit + integration tests required |
| III. FORBILD Fidelity | ✅ PASS | CLI is a thin wrapper; no phantom generation logic introduced |
| IV. UX Consistency | ✅ PASS | Error messages include invalid value + valid range + param name |
| V. Performance | ✅ PASS | No performance-sensitive code; delegates to existing rasterizer |

### Dependency Justification

No new runtime dependencies. `argparse` is part of the Python standard library.

## Project Structure Changes

```text
src/forbuilder/
└── cli.py           # NEW: shared arg parser + head_main() / thorax_main() entry points

tests/unit/
└── test_cli.py      # NEW: unit tests for argument parsing and error paths

tests/integration/
└── test_cli_integration.py  # NEW: end-to-end subprocess tests for both commands

pyproject.toml       # UPDATED: add [project.scripts] with forbild-head-gen and forbild-thorax-gen
specs/002-cli/
├── spec.md
├── plan.md
└── tasks.md
```

## CLI Interface

```
forbild-head-gen   --shape NZ NY NX --voxel-size V [VZ VY VX] --output PATH
forbild-thorax-gen --shape NZ NY NX --voxel-size V [VZ VY VX] --output PATH
```

Both commands share the same argument set; only the phantom template differs.

## Module Design

```python
# src/forbuilder/cli.py

def _build_parser(prog: str) -> argparse.ArgumentParser: ...
def _run(template: str, args: argparse.Namespace) -> None: ...
def head_main() -> None:    _run("head",   _build_parser("forbild-head-gen").parse_args())
def thorax_main() -> None:  _run("thorax", _build_parser("forbild-thorax-gen").parse_args())
```

## Complexity Tracking

> No violations — zero new dependencies; single new module well under 40 lines.
