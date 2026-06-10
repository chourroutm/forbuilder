# Research: FORBILD Phantom Package

**Feature**: `001-forbild-phantom-package`
**Date**: 2026-06-10

## Decision 1: Runtime Dependencies

**Decision**: Four runtime dependencies — `numpy`, `tifffile`, `nibabel`, `zarr`.

**Rationale**:
- `numpy` — foundational; no viable alternative for vectorised 3D array operations in Python.
- `tifffile` — the canonical scientific TIFF library; lighter transitive footprint than
  `imageio` (which pulls in Pillow and other format codecs). Supports multi-page TIFF for
  3D volumes and preserves voxel metadata via ImageJ/OME-TIFF tags.
- `nibabel` — the only maintained pure-Python library for reading and writing NIfTI-1/2
  files correctly (header, affine, data type handling). Reimplementing NIfTI I/O is not
  viable given the binary header complexity.
- `zarr` — required for any Zarr array storage. OME-Zarr v0.5 (OME-NGFF 0.5) metadata
  is a JSON dict written to `.zattrs`; no `ome-zarr` package is needed.

**Alternatives considered**:
- `imageio` instead of `tifffile`: rejected — heavier dependency tree (Pillow, ffmpeg
  plugins), less control over multi-dimensional TIFF metadata.
- `ome-zarr` alongside `zarr`: rejected — `ome-zarr` provides convenience helpers but
  adds a non-trivial transitive dependency for metadata we can write as a plain dict.
- Stdlib `struct` instead of `nibabel`: rejected — NIfTI-1 header is 348 bytes with 38
  typed fields and a complex extension mechanism; reimplementation is error-prone.

---

## Decision 2: Geometry File Format

**Decision**: JSON (`.json`) as the primary geometry file format;
YAML (`.yml` / `.yaml`) as an optional extra (`pip install forbuilder[yaml]`).

**Rationale**: JSON is stdlib and adds zero runtime dependencies. The geometry definitions
for a FORBILD phantom (20–40 components) are verbose but not so complex that YAML's
indentation syntax offers a material authoring advantage over JSON. Researchers who prefer
YAML can opt in via `forbuilder[yaml]` which adds `pyyaml`.

**Alternatives considered**:
- TOML (stdlib in Python 3.11+): readable but awkward for nested lists of heterogeneous
  objects (components with different geometry types).
- CSV: rejected — cannot express nested geometry attributes.

---

## Decision 3: Rasterization Memory Strategy

**Decision**: Process the volume slice-by-slice along the z-axis using vectorised NumPy
operations per slice. Allocate the output array once up front; for each z-slice, compute a
2D meshgrid of (y, x) physical coordinates, evaluate component containment, and write
results into the corresponding output slice in-place.

**Rationale**: Keeps peak transient memory bounded to
`output_array + 2 × shape[y] × shape[x] × float64`. For 512³ at float64 that is
~134 MB output + ~4 MB per temporary — well within the 3× constitutional bound (~402 MB).
A full 3D meshgrid would require 3 × 512³ × 8 bytes ≈ 3.2 GB transient — unacceptable.

**Alternatives considered**:
- Full 3D meshgrid: rejected — exceeds memory bound for large volumes.
- Numba JIT compilation: rejected — adds a compile-time dependency and warmup cost that
  is disproportionate for a library of this scope.
- Cython extension: rejected — same reasoning as Numba; also complicates packaging.

---

## Decision 4: FORBILD Geometry Primitives

**Decision**: Four geometry types — `Ellipsoid` (with optional z-plane truncation),
`Cylinder`, `Sphere`, `Cone`.

**Rationale**: The published FORBILD head and thorax phantoms use almost exclusively
truncated ellipsoids. Cylinder, Sphere, and Cone are included for complete coverage of any
FORBILD-compatible custom geometry file. `Sphere` is a special case of `Ellipsoid`
(equal semi-axes, no rotation) and shares its containment test code path.

**Containment tests** (vectorised form, per z-slice at z = z_k):
- **Ellipsoid** (possibly rotated): apply inverse Euler rotation to (x−cx, y−cy, z_k−cz),
  then check `(x'/ax)² + (y'/ay)² + (z'/az)² ≤ 1`. For truncated ellipsoid, additionally
  check `z_lo ≤ z_k ≤ z_hi`.
- **Cylinder** (axis-aligned or rotated): project point onto cylinder axis, check radial
  distance and axial extent.
- **Cone**: project point onto cone axis, check radial constraint `r ≤ R × (1 − h/H)`.

---

## Decision 5: Built-in Template Names

**Decision**: Ship with two built-in templates: `"head"` (FORBILD 3D head phantom) and
`"thorax"` (FORBILD 3D thorax phantom). Additional templates can be contributed as JSON
files bundled under `forbuilder/phantoms/`.

**Rationale**: The user's input stated the package "can deal with any part of the FORBILD
spec". Both the head and thorax phantoms are the primary published FORBILD reference
objects and are sufficient to cover the spec. The file-path input mode allows arbitrary
custom phantoms without any package change.

---

## Decision 6: OME-Zarr v0.5 Metadata Structure

**Decision**: Use `zarr>=3.0` with `zarr_format=3` (Zarr v3). Write OME-NGFF v0.5
`multiscales` metadata as group attributes nested under the `"ome"` key in the Zarr v3
`zarr.json` consolidated metadata file.

**Rationale**: OME-Zarr v0.5 (OME-NGFF 0.5) is built on Zarr v3, not Zarr v2. In Zarr v3
the `.zattrs` sidecar file does not exist; all group/array metadata is consolidated into
`zarr.json`. The `zarr>=3.0` Python package handles this automatically when opening a group
with `zarr_format=3`. Setting group attributes via `store.attrs["ome"] = {...}` writes the
metadata into the `"attributes"` key of `zarr.json`.

**Required structure** (written via `store.attrs["ome"] = ...`):
```json
{
  "multiscales": [{
    "version": "0.5",
    "name": "<phantom_name>",
    "axes": [
      {"name": "z", "type": "space", "unit": "millimeter"},
      {"name": "y", "type": "space", "unit": "millimeter"},
      {"name": "x", "type": "space", "unit": "millimeter"}
    ],
    "datasets": [{
      "path": "0",
      "coordinateTransformations": [
        {"type": "scale", "scale": [vz, vy, vx]}
      ]
    }],
    "coordinateTransformations": [
      {"type": "scale", "scale": [1.0, 1.0, 1.0]}
    ]
  }]
}
```

**Usage pattern**:
```python
import zarr

store = zarr.open_group("output.ome.zarr", mode="w", zarr_format=3)
store.create_array("0", shape=phantom.shape, dtype="uint8", data=phantom.array)
store.attrs["ome"] = {"multiscales": [...]}
```

The array is stored at path `"0"` within the Zarr v3 group (single-resolution, no pyramid).

**Alternatives considered**:
- Zarr v2 with `.zattrs`: rejected — OME-Zarr v0.5 requires Zarr v3; using v2 would
  produce an OME-NGFF v0.4-compatible file, not v0.5.
- `ome-zarr` package on top of zarr v3: rejected — not yet fully updated for Zarr v3 at
  the time of writing; metadata can be written directly as shown above.

---

## Decision 7: Public API Shape

**Decision**: Four public functions, all in `forbuilder` top-level namespace.

```python
forbuilder.generate(source, shape, voxel_size, *, overrides=None) -> GeneratedPhantom
forbuilder.get_components(source) -> list[Component]
forbuilder.get_slice(phantom_or_source, axis, index, shape=None, voxel_size=None) -> np.ndarray
forbuilder.save(phantom, path) -> None
```

- `source` is either a built-in template name (str, e.g. `"head"`) or a filesystem path
  to a JSON/YAML geometry file.
- `shape` is `(nz, ny, nx)` — number of voxels per axis.
- `voxel_size` is `(dz, dy, dx)` in mm, or a single float for isotropic.
- `overrides` is an optional `dict[str, int]` mapping component name → new uint8 value.
- `save()` infers the output format from the file extension
  (`.tif` / `.tiff` → TIFF; `.nii.gz` → NIfTI; `.ome.zarr` → OME-Zarr).
