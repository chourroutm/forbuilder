<!--
Sync Impact Report
Version change: 2.0.0 → 2.0.1 (PATCH — Development Workflow: added gate requiring all tests to pass before a task is marked complete)
Modified principles:
  I. Test-First Development → I. Code Quality (new focus; TDD content moved to II)
  II. Simplicity & YAGNI → II. Testing Standards (materially expanded from Test-First)
  III. FORBILD Specification Fidelity — unchanged (retained; domain-critical)
  IV. Security & Privacy → IV. User Experience Consistency (removed; replaced)
  V. Observability → V. Performance Requirements (removed; replaced)
Added sections: None
Removed sections: None (same section headings retained; content restructured)
Templates requiring updates:
  ✅ plan-template.md — Constitution Check gate is fill-in-at-plan-time; no structural change needed.
                        Development Workflow review criteria updated in constitution body to match new principles.
  ✅ spec-template.md — Sections compatible with updated principles; no amendments needed.
  ✅ tasks-template.md — Test-First task ordering (write tests → fail → implement) still aligns with Principle II.
Follow-up TODOs:
  - Concrete performance thresholds (e.g., array generation time, memory ceiling) should be defined
    once benchmark data is available. Inserted as TODO in Principle V.
-->
# ForBuilder Constitution

## Core Principles

### I. Code Quality

All code merged into the main branch MUST meet the following standards:

- **Style**: Code MUST conform to PEP 8 and MUST pass `ruff` (or equivalent linter) with
  no suppressed warnings unless a documented rationale accompanies the suppression inline.
- **Naming**: Identifiers MUST be self-explanatory; single-letter names are forbidden outside
  mathematical loop indices that directly mirror the FORBILD specification's notation.
- **Responsibility**: Every function and module MUST have a single, clearly stated
  responsibility. Functions exceeding 40 logical lines MUST be split unless a documented
  justification is recorded in the PR.
- **Dead code**: Commented-out code, unused imports, and unreachable branches MUST NOT be
  merged. Remove or document as a deliberate placeholder with a TODO and a linked issue.
- **Dependencies**: Each new runtime dependency MUST be justified in the implementation plan
  with a documented alternative that was rejected; unexplained dependencies block merging.

### II. Testing Standards (NON-NEGOTIABLE)

Tests MUST be written before implementation and MUST fail before any production code is
added (Red-Green-Refactor). This cycle is strictly enforced and cannot be waived.

- **Coverage**: Line coverage MUST be ≥ 90% for all non-trivial modules. Coverage
  regressions introduced by a PR block merging.
- **Test categories** (all three MUST be present for any feature):
  - *Unit tests* (`tests/unit/`) — isolate individual functions; no I/O, no NumPy
    array allocations larger than needed to cover the case.
  - *Integration tests* (`tests/integration/`) — exercise the full phantom-generation
    pipeline end-to-end with realistic parameters.
  - *Numerical accuracy tests* (`tests/accuracy/`) — compare output arrays against
    reference FORBILD phantom data; MUST document the tolerance bound used.
- **Determinism**: Tests MUST be deterministic; any test that produces different results
  across runs without a fixed seed is a failing test.
- **Isolation**: Tests MUST NOT depend on execution order. Each test MUST set up and
  tear down its own state.

### III. FORBILD Specification Fidelity

Outputs MUST conform strictly to the FORBILD phantom specification. Numerical correctness
and reproducibility are non-negotiable: 8-bit array values produced MUST match reference
FORBILD phantom data within documented tolerance bounds. Any deviation from the specification
MUST be explicitly documented, justified, and approved before merging. The specification is
the ground truth; implementation convenience is not a valid reason to diverge from it.

### IV. User Experience Consistency

ForBuilder's public API MUST be predictable and consistent across all functions:

- **Signatures**: Array-returning functions MUST follow a uniform parameter order:
  `(shape, ..., dtype=np.uint8)`. Deviations require a documented rationale in the spec.
- **Return types**: Functions with the same conceptual purpose MUST return the same type.
  Polymorphic return types (e.g., array vs. scalar depending on input) are forbidden.
- **Error messages**: Raised exceptions MUST include the invalid value, the valid range or
  expected type, and the parameter name. Bare `ValueError("bad input")` is forbidden.
- **Documentation**: Every public function MUST have a docstring with: purpose (one line),
  parameters (name, type, valid range), return type, and at least one usage example.
- **Logging**: The library MUST emit structured log messages at DEBUG (computation steps),
  WARNING (recoverable anomalies), and ERROR (failures) using Python's `logging` module.
  Silent failures are forbidden — every error condition MUST be logged or raised.

### V. Performance Requirements

Computational efficiency is a first-class constraint for a numerical library:

- **Array generation**: Generating a standard 256×256×256 FORBILD head phantom MUST complete
  in under 30 seconds on a single CPU core (PERF_BASELINE: 2.69 s measured 2026-06-10 on
  WSL2/Linux, Python 3.12, NumPy; 512³ extrapolates to ~21 s). Benchmarks MUST be included
  in `tests/benchmarks/` and run in CI.
- **Memory**: Peak memory usage during phantom generation MUST NOT exceed 3× the size of
  the output array. In-place operations MUST be preferred over intermediate copies where
  NumPy semantics allow.
- **Vectorization**: Pixel/voxel loops MUST use NumPy vectorized operations. Python-level
  loops over array elements are forbidden unless a vectorized equivalent is provably absent
  and the rationale is documented.
- **Regression guard**: Any PR that increases benchmark runtime by more than 10% relative
  to the baseline MUST include a documented justification; unexplained regressions block
  merging.

## Technology Stack & Constraints

- **Language**: Python 3.12
- **Package type**: Pure library (no CLI entry point, no server process)
- **Core dependencies**: NumPy for array operations; additional dependencies require explicit
  justification and MUST be approved before introduction
- **Testing framework**: pytest; tests live in `tests/` at the repository root, organized
  into `unit/`, `integration/`, `accuracy/`, and `benchmarks/` subdirectories
- **Linting/formatting**: `ruff` for linting and formatting (enforces PEP 8 and import order)
- **Compatibility target**: Python 3.12+; backwards compatibility with earlier versions is
  out of scope unless a concrete, documented user need is approved

## Development Workflow

- All work begins with a feature specification (`/speckit-specify`) and an implementation
  plan (`/speckit-plan`) before any code is written
- Every PR MUST include a Constitution Check section in the implementation plan confirming
  compliance with all five principles above
- Complexity violations (e.g., adding a dependency, a function exceeding 40 lines) MUST be
  recorded in the Complexity Tracking table with justification; unexplained violations block
  merging
- Code review MUST verify: code quality (Principle I), test coverage and TDD discipline
  (Principle II), specification fidelity (Principle III), API consistency (Principle IV),
  and performance (Principle V)
- **No task may be marked complete until all tests in the repository pass.** A task whose
  implementation causes any previously passing test to fail MUST fix the regression before
  advancing to the next task. This gate is non-negotiable and applies to every task in
  every phase.
- Commits are made at logical task boundaries; commit messages SHOULD reference the task
  ID from `tasks.md`

## Governance

This constitution supersedes all informal conventions and prior verbal agreements.
Amendments follow this procedure:

1. Propose the amendment as a PR updating this file with a version bump and written
   rationale for the bump type (MAJOR / MINOR / PATCH per semantic versioning rules below)
2. At least one reviewer MUST approve, explicitly confirming the version bump type is correct
3. All dependent templates (`plan-template.md`, `spec-template.md`, `tasks-template.md`)
   MUST be updated in the same PR when the amendment affects them
4. `LAST_AMENDED_DATE` MUST be set to the merge date in ISO format (YYYY-MM-DD)

**Versioning policy**:
- MAJOR — backward-incompatible governance changes: principle removals or redefinitions
- MINOR — new principle or section added, or materially expanded guidance
- PATCH — clarifications, wording fixes, non-semantic refinements

All PRs MUST include a Constitution Check in the implementation plan. Violations require
documented justification; unexplained violations block merging.

**Version**: 2.0.1 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-10
