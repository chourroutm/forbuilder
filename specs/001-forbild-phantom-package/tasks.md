---
description: "Task list for FORBILD Phantom Package"
---

# Tasks: FORBILD Phantom Package

**Input**: Design documents from `specs/001-forbild-phantom-package/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/public-api.md ✅

**TDD discipline** (Constitution Principle II — NON-NEGOTIABLE): Every test task MUST be
run before its implementation task to confirm failures. Implementation tasks MUST pass all
tests in their designated test file before the task is marked complete.

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: US1 = Generate Phantom, US2 = Inspect Components, US3 = Extract Slices
- Exact file paths included in every task description

---

## Phase 1: Setup

**Purpose**: Project initialization — package scaffold, tooling, test structure

- [X] T001 Initialize `pyproject.toml` with package metadata (`name = "forbuilder"`), runtime dependencies (`numpy`, `tifffile`, `nibabel`, `zarr>=3.0`), and optional extras (`[yaml]` → pyyaml; `[dev]` → pytest, pytest-cov, pytest-benchmark, ruff)
- [X] T002 Create `src/forbuilder/` directory tree with empty stub files: `__init__.py`, `_version.py`, `_logging.py`, `geometry.py`, `loader.py`, `rasterizer.py`, `slicer.py`, `io/__init__.py`, `io/tiff.py`, `io/nifti.py`, `io/zarr_.py`, `phantoms/__init__.py`
- [X] T003 [P] Configure `ruff` in `pyproject.toml` (`[tool.ruff]`: `line-length = 100`, `select = ["E", "F", "I", "N", "W"]`; `[tool.ruff.format]`)
- [X] T004 [P] Configure `pytest` and `pytest-cov` in `pyproject.toml` (`[tool.pytest.ini_options]`: `testpaths = ["tests"]`; `[tool.coverage.run]`: `source = ["src/forbuilder"]`, `branch = true`)
- [X] T005 [P] Create test directory tree with stub `conftest.py` files: `tests/unit/`, `tests/integration/`, `tests/accuracy/reference/`, `tests/benchmarks/`; verify `pytest --collect-only` exits without errors

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data types, geometry loading, and bundled phantom JSON definitions.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Write failing unit tests for all geometry dataclasses (`Ellipsoid`, `Cylinder`, `Sphere`, `Cone`) and `PhantomSpec` validation in `tests/unit/test_geometry.py`; run `pytest tests/unit/test_geometry.py` and confirm all FAIL
- [X] T007 Implement `Ellipsoid`, `Cylinder`, `Sphere`, `Cone`, and `PhantomSpec` dataclasses with field validation (value in [0,255], semi-axes > 0, unique component names) in `src/forbuilder/geometry.py`; run `pytest tests/unit/test_geometry.py` and confirm all pass
- [X] T008 [P] Implement module-level logger in `src/forbuilder/_logging.py` — `logging.getLogger("forbuilder")`; no handler setup (caller's responsibility per Principle IV)
- [X] T009 Write failing unit tests for `load_spec()` — template resolution (`"head"`, `"thorax"`), JSON file loading, unknown template error, missing file error — in `tests/unit/test_loader.py`; confirm all FAIL
- [X] T010 Implement `load_spec(source: str) -> PhantomSpec` in `src/forbuilder/loader.py` — resolve built-in template name via `importlib.resources` or file path; parse JSON; raise `ValueError` listing available templates for unknown names; run `pytest tests/unit/test_loader.py` and confirm all pass
- [X] T011 Create FORBILD 3D head phantom geometry in `src/forbuilder/phantoms/head.json` — all 34 truncated ellipsoid components with FORBILD-specified centre (mm), semi-axes (mm), Euler angles (rad), uint8 attenuation values, and z-plane truncation bounds; `background = 0`
- [X] T012 [P] Create FORBILD 3D thorax phantom geometry in `src/forbuilder/phantoms/thorax.json` — all components per FORBILD thorax specification using the same JSON schema as `head.json`

**Checkpoint**: `pytest tests/unit/` passes. `load_spec("head")` and `load_spec("thorax")` return valid `PhantomSpec` objects. User story work may begin.

---

## Phase 3: User Story 1 — Generate Standard Phantom (Priority: P1) 🎯 MVP

**Goal**: `fb.generate(source, shape, voxel_size)` returns a 3D `uint8` array matching
FORBILD reference data within ≤1 grayscale unit. `fb.save(phantom, path)` writes TIFF,
NIfTI, and OME-Zarr v0.5 files.

**Independent Test**: Call `fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)`;
verify shape `(64, 64, 64)`, dtype `uint8`, determinism (two calls bit-for-bit identical);
save to all three formats and verify files are non-empty.

### Tests for User Story 1 ⚠️ Write and confirm FAIL before implementing

- [X] T013 [US1] Write failing unit tests for rasterizer — containment math for each geometry type on tiny 8×8×8 synthetic arrays, background fill, component priority order — in `tests/unit/test_rasterizer.py`; confirm all FAIL
- [X] T014 [P] [US1] Write failing integration test for `generate()` — shape, dtype, determinism, isotropic and anisotropic voxel size, invalid parameter errors — in `tests/integration/test_pipeline.py`; confirm FAIL
- [X] T015 [P] [US1] Write failing accuracy tests comparing `generate("head", ...)` against reference arrays stored in `tests/accuracy/reference/`; generate and commit reference arrays; confirm tests FAIL against current stubs

### Implementation for User Story 1

- [X] T016 [US1] Implement `rasterizer.py` — `rasterize(spec, shape, voxel_size) -> GeneratedPhantom` using slice-by-slice (z-axis) vectorised NumPy operations; containment tests for all four geometry types including Ellipsoid rotation and truncation; emit DEBUG per slice, WARNING for zero-voxel components — in `src/forbuilder/rasterizer.py`
- [X] T017 [US1] Wire `generate(source, shape, voxel_size, *, overrides=None) -> GeneratedPhantom` into `src/forbuilder/__init__.py` — calls `load_spec()` then `rasterize()`; validate all parameters before any computation; run `pytest tests/unit/test_rasterizer.py tests/integration/test_pipeline.py tests/accuracy/test_fidelity.py` and confirm all pass
- [X] T018 [US1] Write failing unit tests for all three I/O writers in `tests/unit/test_io.py` — file created, non-zero size, extension dispatching, unknown extension error; confirm FAIL
- [X] T019 [P] [US1] Implement TIFF writer in `src/forbuilder/io/tiff.py` — `write_tiff(phantom, path)` using `tifffile.imwrite`; voxel spacing stored in ImageJ metadata (`spacing`, `unit = "um"` converted from mm)
- [X] T020 [P] [US1] Implement NIfTI-1 writer in `src/forbuilder/io/nifti.py` — `write_nifti(phantom, path)` using `nibabel.Nifti1Image`; diagonal affine from `voxel_size`; `xyzt_units` set to mm; save as `.nii.gz`
- [X] T021 [P] [US1] Implement OME-Zarr v0.5 writer in `src/forbuilder/io/zarr_.py` — `write_zarr(phantom, path)` using `zarr.open_group(zarr_format=3)`; array at path `"0"`; OME-NGFF 0.5 `multiscales` metadata written to `store.attrs["ome"]` with axes `(z, y, x)` in mm and scale `(dz, dy, dx)`
- [X] T022 [US1] Implement `save(phantom, path) -> None` dispatcher in `src/forbuilder/io/__init__.py` — infer format from extension (`.tif`/`.tiff`, `.nii.gz`, `.ome.zarr`); raise `ValueError` for unknown extensions; wire into `src/forbuilder/__init__.py`; run `pytest tests/unit/test_io.py` and confirm all pass
- [X] T023 [US1] Implement benchmark in `tests/benchmarks/test_benchmarks.py` — time 256×256×256 head phantom generation; assert ≤ 60 s; record baseline wall time in a comment for regression tracking

**Checkpoint**: All US1 tests pass. End-to-end `generate → save` works for all three formats. Accuracy ≤1 grayscale unit verified.

---

## Phase 4: User Story 2 — Inspect Phantom Components (Priority: P2)

**Goal**: `fb.get_components(source)` returns the full component list without rasterizing.
`overrides` parameter in `fb.generate()` correctly replaces individual attenuation values.

**Independent Test**: Call `fb.get_components("head")`; verify ≥30 components each with
correct attributes. Call `fb.generate("head", ..., overrides={"outer_skull": 100})` and
verify modified voxels differ from default output.

### Tests for User Story 2 ⚠️ Write and confirm FAIL before implementing

- [X] T024 [US2] Write failing unit tests for `get_components()` and `apply_overrides()` — component count, attribute presence, override value validation, unknown key error, out-of-range value error — in `tests/unit/test_loader.py`; confirm FAIL

### Implementation for User Story 2

- [X] T025 [US2] Implement `apply_overrides(spec, overrides) -> PhantomSpec` in `src/forbuilder/loader.py` — validate all keys exist, all values in [0,255]; return copy with updated values; raise `ValueError` with descriptive message for violations
- [X] T026 [US2] Wire `get_components(source) -> list[Component]` into `src/forbuilder/__init__.py`; run `pytest tests/unit/test_loader.py` and confirm all pass
- [X] T027 [US2] Extend `tests/integration/test_pipeline.py` to cover component list length and attribute check for `"head"` and `"thorax"`, and override round-trip (generate with override, verify changed voxels); confirm passing

**Checkpoint**: US1 and US2 both independently testable and passing.

---

## Phase 5: User Story 3 — Extract 2D Slices (Priority: P3)

**Goal**: `fb.get_slice(source, axis, index, ...)` returns a correct 2D `uint8` array
without allocating the full 3D volume when called with a string source.

**Independent Test**: Call `fb.get_slice("head", "axial", 32, shape=(64,64,64), voxel_size=1.0)`;
verify shape `(64, 64)` and dtype `uint8`. Verify out-of-bounds index raises `ValueError`
with axis name and valid range in the message.

### Tests for User Story 3 ⚠️ Write and confirm FAIL before implementing

- [X] T028 [US3] Write failing unit tests for `get_slice()` — axial/coronal/sagittal shape correctness, dtype, out-of-bounds error message content, values match corresponding full-array slice — in `tests/unit/test_slicer.py`; confirm FAIL

### Implementation for User Story 3

- [X] T029 [US3] Implement `src/forbuilder/slicer.py` — `get_slice(source_or_phantom, axis, index, *, shape=None, voxel_size=None) -> np.ndarray`; for string source compute only the requested z-slice (axial) or rasterize a single row/column plane (coronal/sagittal) without allocating the full 3D array; validate index bounds with descriptive error
- [X] T030 [US3] Wire `get_slice()` into `src/forbuilder/__init__.py`; run `pytest tests/unit/test_slicer.py` and confirm all pass
- [X] T031 [US3] Extend `tests/integration/test_pipeline.py` to cover axial, coronal, and sagittal slices from both a `GeneratedPhantom` and a string source; verify values match the corresponding 3D array layer; confirm passing

**Checkpoint**: All three user stories independently testable and passing.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, documentation, optional YAML support, full validation run

- [X] T032 Add docstrings to all public functions in `src/forbuilder/__init__.py` — each MUST include: one-line purpose, parameters (name, type, valid range), return type, one usage example (constitution Principle IV)
- [X] T033 [P] Add docstrings to all non-trivial internal functions in `src/forbuilder/geometry.py`, `loader.py`, `rasterizer.py`, `slicer.py`, `io/tiff.py`, `io/nifti.py`, `io/zarr_.py`
- [X] T034 [P] Add optional YAML support in `src/forbuilder/loader.py` — `_load_yaml()` helper guarded by `importlib.util.find_spec("yaml")`; raise `ImportError` with install hint if pyyaml absent; add YAML load test to `tests/unit/test_loader.py`
- [X] T035 Run `ruff check src/ tests/` and `ruff format --check src/ tests/`; fix all violations; verify zero errors remain
- [X] T036 Run `pytest --cov=src/forbuilder --cov-report=term-missing`; add targeted tests for any module below 90% line coverage
- [X] T037 Run all 12 validation scenarios from `specs/001-forbild-phantom-package/quickstart.md`; record 256³ benchmark wall time; update `TODO(PERF_BASELINE)` in `.specify/memory/constitution.md` Principle V with the measured value

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
  - T006 → T007 (tests before implementation)
  - T009 → T010 → [T011, T012] (tests before implementation; JSON files after loader)
- **US1 (Phase 3)**: Depends on Phase 2; T013/T014/T015 must FAIL before T016
- **US2 (Phase 4)**: Depends on Phase 2; T024 must FAIL before T025; independent of US1
- **US3 (Phase 5)**: Depends on Phase 2; T028 must FAIL before T029; independent of US1/US2
- **Polish (Phase 6)**: Depends on all user story phases complete

### Parallel Opportunities

```
Phase 1:  T001 → [T002, T003, T004, T005]

Phase 2:  T006 → T007          (geometry chain)
          T008                  (logging, independent)
          T009 → T010 → [T011, T012]  (loader + JSON)

Phase 3:  [T013, T014, T015] → T016 → T017
          T018 → [T019, T020, T021] → T022 → T023

Phases 4+5 can run in parallel with each other after Phase 2:
  Phase 4: T024 → T025 → T026 → T027
  Phase 5: T028 → T029 → T030 → T031
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: US1
4. **STOP and VALIDATE**: run quickstart validations 1–10; run accuracy tests
5. Ship if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → generates phantom + saves all three formats → **MVP**
3. US2 → component inspection + overrides → extend
4. US3 → 2D slice extraction → extend
5. Polish → quality gates, docs, YAML, release candidate

---

## Notes

- `[P]` tasks operate on different files — safe to run in parallel
- `[Story]` label maps each task to a user story for traceability to spec.md
- TDD cycle is mandatory; every implementation task requires its test task to have been confirmed failing first (Constitution Principle II)
- Commit at each task boundary; reference task ID in commit message (e.g. `feat: T016 implement slice-by-slice rasterizer`)
- `zarr_.py` uses a trailing underscore to avoid shadowing the `zarr` package at import time
