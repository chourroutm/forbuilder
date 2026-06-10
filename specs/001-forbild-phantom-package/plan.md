# Implementation Plan: FORBILD Phantom Package

**Branch**: `001-forbild-phantom-package` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-forbild-phantom-package/spec.md`

## Summary

Build `forbuilder` — a minimal Python library that rasterizes FORBILD digital phantom
geometries (head, thorax, and any custom phantom described in a JSON/YAML file) into 3D
unsigned 8-bit NumPy arrays. The library accepts either a built-in template name or a file
path as input, and can write the resulting volume to TIFF, NIfTI, or OME-Zarr v0.5 format.
The rasterization engine processes the volume z-slice by z-slice using vectorised NumPy
operations to stay within strict memory bounds. Four runtime dependencies are required:
`numpy`, `tifffile`, `nibabel`, `zarr>=3.0`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**:
- `numpy` — vectorised array operations (foundational; no alternative)
- `tifffile` — multi-page TIFF write with voxel-spacing metadata
- `nibabel` — NIfTI-1 compressed write with affine matrix
- `zarr>=3.0` — OME-Zarr v0.5 (Zarr v3 format) write

**Optional extras**:
- `pyyaml` — YAML geometry file support (`pip install forbuilder[yaml]`)
- `pytest`, `pytest-cov`, `pytest-benchmark` — dev/test (`pip install forbuilder[dev]`)
- `ruff` — linting and formatting (`pip install forbuilder[dev]`)

**Storage**: No database; geometry definitions bundled as JSON files under
`src/forbuilder/phantoms/`; output files written to caller-specified paths.

**Testing**: pytest with pytest-cov (≥90% line coverage required), pytest-benchmark for
performance regression tracking.

**Target Platform**: Any POSIX or Windows system with Python 3.12+; no OS-specific APIs.

**Project Type**: Pure Python library (installable via pip, no CLI, no server).

**Performance Goals**:
- 256×256×256 phantom generation: ≤ 60 s on a single CPU core (from spec SC-002)
- Peak memory during generation: ≤ 3× the output array size
- Slice extraction: no full 3D array allocation (from spec SC-005)

**Constraints**:
- Output values MUST match FORBILD reference data with max absolute error ≤ 1 (SC-003)
- All input validation MUST happen before any computation starts (SC-006)
- Four runtime deps maximum (constitution Principle I — dependency justification required)

**Scale/Scope**: Single-library package; ~600–900 lines of production code across 8 modules.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (GATE — passes)

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Code Quality | ✅ PASS | `ruff` enforced in CI; single-responsibility modules planned; all 4 deps justified below |
| II. Testing Standards | ✅ PASS | TDD cycle enforced; 3 test categories (unit, integration, accuracy) required; benchmarks in `tests/benchmarks/` |
| III. FORBILD Fidelity | ✅ PASS | Geometry values taken verbatim from FORBILD spec; accuracy tests verify ≤1 grayscale unit error |
| IV. UX Consistency | ✅ PASS | Uniform 4-function API defined in contracts; error messages specified per contract |
| V. Performance | ✅ PASS | Slice-by-slice rasterization bounds memory to <3×; benchmarks defined; 10% regression gate |

### Dependency Justification (Principle I — Complexity Table)

| Dependency | Why Needed | Simpler Alternative Rejected Because |
|------------|------------|--------------------------------------|
| `numpy` | Vectorised 3D array operations; the output IS a NumPy array | No alternative; pure Python loops over 256³ voxels would take minutes |
| `tifffile` | Multi-page scientific TIFF with voxel spacing metadata | `imageio` pulls in Pillow + codec plugins (heavier); stdlib has no TIFF support |
| `nibabel` | Correct NIfTI-1 binary header with affine matrix | Reimplementing NIfTI-1 header (348 bytes, 38 typed fields) is error-prone and out of scope |
| `zarr>=3.0` | Zarr v3 array storage required by OME-Zarr v0.5 (OME-NGFF 0.5) | No alternative for zarr format; `ome-zarr` package not yet stable for zarr v3 |

### Post-Design Re-Check (GATE — passes)

All five principles satisfied by the design in Phase 1 artifacts. No unresolved violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-forbild-phantom-package/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── public-api.md    # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── forbuilder/
    ├── __init__.py          # Re-exports: generate, get_components, get_slice, save
    ├── _version.py          # Package version string
    ├── _logging.py          # Module-level logger; no handler setup (caller's responsibility)
    ├── geometry.py          # Dataclasses: Ellipsoid, Cylinder, Sphere, Cone, PhantomSpec
    ├── loader.py            # load_spec(source) → PhantomSpec; resolves template names + files
    ├── rasterizer.py        # rasterize(spec, shape, voxel_size) → GeneratedPhantom
    ├── slicer.py            # get_slice implementation; single-slice rasterization path
    ├── io/
    │   ├── __init__.py      # save() dispatcher based on file extension
    │   ├── tiff.py          # write_tiff(phantom, path)
    │   ├── nifti.py         # write_nifti(phantom, path)
    │   └── zarr_.py         # write_zarr(phantom, path)   (zarr_ to avoid shadowing module)
    └── phantoms/
        ├── head.json        # FORBILD 3D head phantom geometry (34 components)
        └── thorax.json      # FORBILD 3D thorax phantom geometry

tests/
├── unit/
│   ├── test_geometry.py     # Component dataclass validation, containment math
│   ├── test_loader.py       # Template resolution, file loading, override application
│   ├── test_rasterizer.py   # Rasterization correctness on tiny synthetic phantoms
│   ├── test_slicer.py       # Slice shape, dtype, out-of-bounds errors
│   └── test_io.py           # Writer round-trips (write + stat; no image content check)
├── integration/
│   └── test_pipeline.py     # End-to-end: generate → inspect → slice → save (all formats)
├── accuracy/
│   ├── reference/           # Reference FORBILD phantom slices (stored as small NPY files)
│   └── test_fidelity.py     # Max absolute error ≤ 1 vs. reference data
└── benchmarks/
    └── test_benchmarks.py   # pytest-benchmark: 256³ generation time; memory profiling

pyproject.toml               # Build config (setuptools/hatchling), dependency declaration
```

**Structure Decision**: Single Python package layout using `src/` to avoid import
ambiguity. `io/` sub-package groups the three format writers. Built-in phantom JSON
files are bundled as package data under `forbuilder/phantoms/` and accessed via
`importlib.resources`.

## Complexity Tracking

> No violations beyond the four justified dependencies above.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| 4 runtime dependencies | Each maps to a required output format or core computation | See Dependency Justification table above |
