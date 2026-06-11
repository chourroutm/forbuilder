# Tasks: forbuilder CLI

**Input**: Design documents from `/specs/002-cli/`

**Prerequisites**: plan.md ✅, spec.md ✅

**TDD Gate**: Tests are written before production code. A newly written test starts
failing (Red) because the feature doesn't exist yet — this confirms the test is genuine.
Production code is then added to make it pass (Green). No task may be marked complete
until ALL tests in the repository pass.

---

## Phase 1: Setup

**Purpose**: Register the new feature directory and wire the console-script entry points.

- [ ] T001 Update `.specify/feature.json` to point to `specs/002-cli`
- [ ] T002 Add `[project.scripts]` entries `forbild-head-gen` and `forbild-thorax-gen` in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared CLI module skeleton that both entry points will use.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Write failing unit test: importing `forbuilder.cli` exposes `head_main` and `thorax_main` callables in `tests/unit/test_cli.py`
- [ ] T004 Create `src/forbuilder/cli.py` with `_build_parser()`, `_run()`, `head_main()`, `thorax_main()` stubs (makes T003 pass)

**Checkpoint**: `python -c "from forbuilder.cli import head_main, thorax_main"` succeeds.

---

## Phase 3: User Story 1 — `forbild-head-gen` (Priority: P1) 🎯 MVP

**Goal**: `forbild-head-gen --shape NZ NY NX --voxel-size V --output PATH` generates and saves a head phantom.

**Independent Test**:
```
forbild-head-gen --shape 32 32 32 --voxel-size 1.0 --output /tmp/head_test.tif
```
File `/tmp/head_test.tif` must exist and be non-empty; exit code must be 0.

### Tests for User Story 1

> **Write these tests first. Each will fail (Red) until the implementation is added.**

- [ ] T005 [P] [US1] Unit tests: `_build_parser` accepts valid `--shape`, `--voxel-size` (scalar and 3-value), `--output` in `tests/unit/test_cli.py`
- [ ] T006 [P] [US1] Unit tests: error paths — non-positive shape dim, non-positive voxel-size, unsupported extension all cause `SystemExit` or `ValueError` in `tests/unit/test_cli.py`
- [ ] T007 [US1] Integration test: `forbild-head-gen --shape 32 32 32 --voxel-size 1.0 --output <tmp>.tif` exits 0 and writes a non-empty file; repeated for `.nii.gz` and `.ome.zarr` in `tests/integration/test_cli_integration.py`
- [ ] T008 [US1] Integration test: bad args (zero shape, bad extension) exit non-zero with text on stderr in `tests/integration/test_cli_integration.py`

### Implementation for User Story 1

- [ ] T009 [US1] Implement `_build_parser(prog)` with `--shape` (3 ints), `--voxel-size` (1 or 3 floats), `--output` (str) in `src/forbuilder/cli.py`
- [ ] T010 [US1] Implement `_run(template, args)`: validate positive shape/voxel-size, call `fb.generate()` + `fb.save()`, print progress to stderr; exit non-zero on failure in `src/forbuilder/cli.py`
- [ ] T011 [US1] Wire `head_main()` to call `_run("head", ...)` in `src/forbuilder/cli.py`

**Checkpoint**: All T005–T011 tests pass; US1 acceptance criteria met.

---

## Phase 4: User Story 2 — `forbild-thorax-gen` (Priority: P2)

**Goal**: `forbild-thorax-gen` works identically to `forbild-head-gen` but generates the thorax phantom.

**Independent Test**:
```
forbild-thorax-gen --shape 32 32 32 --voxel-size 1.0 --output /tmp/thorax_test.tif
```
Exit 0; file non-empty.

### Tests for User Story 2

> **Write these tests first. Each will fail (Red) until the implementation is added.**

- [ ] T012 [P] [US2] Integration test: `forbild-thorax-gen --shape 32 32 32 --voxel-size 1.0 --output <tmp>.tif` exits 0 and writes a non-empty file; repeated for `.nii.gz` and `.ome.zarr` in `tests/integration/test_cli_integration.py`
- [ ] T013 [US2] Integration test: bad args exit non-zero with stderr message in `tests/integration/test_cli_integration.py`

### Implementation for User Story 2

- [ ] T014 [US2] Wire `thorax_main()` to call `_run("thorax", ...)` in `src/forbuilder/cli.py` (depends on T012–T013 being Red)

**Checkpoint**: All T012–T014 tests pass; US2 acceptance criteria met.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T015 [P] Update `README.md` with CLI usage examples for both `forbild-head-gen` and `forbild-thorax-gen` covering all three output formats
- [ ] T016 Run `ruff check src/forbuilder/cli.py tests/unit/test_cli.py tests/integration/test_cli_integration.py` and fix any issues
- [ ] T017 Verify `pytest --cov=src/forbuilder --cov-fail-under=90` passes with new tests included

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion.
- **US1 (Phase 3)**: Depends on Phase 2 completion.
- **US2 (Phase 4)**: Depends on Phase 3 completion (reuses `_run()` and `_build_parser()`).
- **Polish (Phase 5)**: Depends on Phases 3 and 4 completion.

### TDD Order Within Each Story

1. Write tests → confirm they fail (Red — feature doesn't exist yet).
2. Implement production code → confirm tests pass (Green).
3. All repo tests must pass before marking any task complete.

### Parallel Opportunities

- T005 and T006 can be written in parallel (different test functions).
- T007 and T008 can be written in parallel.
- T012 and T013 can be written in parallel.
- T015 and T016 can run in parallel in Phase 5.

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Phase 1: Setup (T001–T002)
2. Phase 2: Foundational (T003–T004)
3. Phase 3: US1 (T005–T011)
4. **Validate**: `forbild-head-gen --shape 64 64 64 --voxel-size 1.0 --output head.tif` works.
5. Proceed to US2.

### Incremental Delivery

1. Setup + Foundational → module importable.
2. US1 → `forbild-head-gen` works for all three output formats.
3. US2 → `forbild-thorax-gen` works for all three output formats.
4. Polish → README updated, linting clean, coverage ≥ 90%.

---

## Notes

- [P] = parallelisable (different files or non-conflicting sections).
- [US1] / [US2] = user story label for traceability.
- No task is complete until the full test suite (`pytest`) passes.
