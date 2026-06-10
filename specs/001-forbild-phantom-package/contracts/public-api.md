# Contract: Public Python API

**Feature**: `001-forbild-phantom-package`
**Date**: 2026-06-10
**Source**: [research.md](../research.md) | [data-model.md](../data-model.md)

All four functions are importable directly from the `forbuilder` top-level namespace.

---

## `forbuilder.generate`

Generate a 3D phantom array from a built-in template or a geometry file.

```python
def generate(
    source: str,
    shape: tuple[int, int, int],
    voxel_size: float | tuple[float, float, float],
    *,
    overrides: dict[str, int] | None = None,
) -> GeneratedPhantom:
```

**Parameters**:

| Name | Type | Constraints | Description |
|------|------|-------------|-------------|
| `source` | `str` | non-empty | Built-in template name (`"head"`, `"thorax"`) or path to a `.json` / `.yaml` / `.yml` geometry file |
| `shape` | `tuple[int, int, int]` | all > 0 | Output array dimensions as `(nz, ny, nx)` — number of voxels per axis |
| `voxel_size` | `float` or `tuple[float, float, float]` | all > 0 | Voxel size in mm. A single float is broadcast to `(dz, dy, dx)` (isotropic). |
| `overrides` | `dict[str, int] \| None` | values in [0,255] | Map of component name → replacement uint8 value. Applied after loading, before rasterization. |

**Returns**: `GeneratedPhantom` — see [data-model.md](../data-model.md).

**Raises**:
- `ValueError` — if `source` is not a recognised template name and does not exist as a file path; if any `shape` dimension ≤ 0; if any `voxel_size` ≤ 0; if any override value is outside [0, 255]; if an override key does not match any component name.
- `FileNotFoundError` — if `source` is a file path that does not exist.
- `json.JSONDecodeError` / `yaml.YAMLError` — if the geometry file is malformed.
- `MemoryError` — propagated unmodified if array allocation fails.

**Logging**:
- `DEBUG` — emitted at the start of each z-slice rasterization.
- `WARNING` — emitted for each component that covers zero voxels at the given resolution.
- `ERROR` — emitted and exception re-raised on unhandled failure.

**Example**:
```python
import forbuilder as fb

phantom = fb.generate("head", shape=(256, 256, 256), voxel_size=0.5)
phantom = fb.generate("head", shape=(256, 256, 256), voxel_size=(1.0, 0.5, 0.5))
phantom = fb.generate(
    "/data/custom.json",
    shape=(128, 128, 64),
    voxel_size=1.0,
    overrides={"outer_skull": 220},
)
```

---

## `forbuilder.get_components`

Retrieve the list of component definitions from a template or geometry file, without
generating any array.

```python
def get_components(source: str) -> list[Component]:
```

**Parameters**:

| Name | Type | Constraints | Description |
|------|------|-------------|-------------|
| `source` | `str` | non-empty | Built-in template name or path to a geometry file |

**Returns**: An ordered list of `Component` objects (Ellipsoid, Cylinder, Sphere, or Cone)
as defined in [data-model.md](../data-model.md). The list order matches rasterization
priority (last component in list wins on overlap).

**Raises**: Same as `generate()` for source-loading errors.

**Example**:
```python
components = fb.get_components("head")
for c in components:
    print(c.name, c.value)
```

---

## `forbuilder.get_slice`

Extract a single 2D cross-section without generating or holding the full 3D array.

```python
def get_slice(
    source: str | GeneratedPhantom,
    axis: Literal["axial", "coronal", "sagittal"],
    index: int,
    *,
    shape: tuple[int, int, int] | None = None,
    voxel_size: float | tuple[float, float, float] | None = None,
) -> np.ndarray:
```

**Parameters**:

| Name | Type | Constraints | Description |
|------|------|-------------|-------------|
| `source` | `str` or `GeneratedPhantom` | — | Template name, file path, or an already-generated phantom |
| `axis` | `str` | one of `"axial"`, `"coronal"`, `"sagittal"` | The plane to slice through |
| `index` | `int` | 0 ≤ index < axis_length | Which slice to extract (zero-based along the chosen axis) |
| `shape` | `tuple[int, int, int] \| None` | required when `source` is a `str` | Volume shape to use when computing from a template/file |
| `voxel_size` | `float` or `tuple \| None` | required when `source` is a `str` | Voxel size in mm when computing from a template/file |

**Axis → returned shape mapping**:

| `axis` | Returned 2D shape |
|--------|------------------|
| `"axial"` | `(ny, nx)` |
| `"coronal"` | `(nz, nx)` |
| `"sagittal"` | `(nz, ny)` |

**Returns**: `np.ndarray` dtype `uint8`, 2D.

**Raises**:
- `ValueError` — if `index` is out of range (error message states index, valid range, and axis name); if `shape` or `voxel_size` are missing when `source` is a string; if `axis` is not one of the three valid values.

**Memory note**: When `source` is a `str`, only the requested z-slice (or row/column) is
computed; the full 3D array is never allocated.

**Example**:
```python
# From an already-generated phantom:
axial = fb.get_slice(phantom, "axial", 128)

# From a template, without generating the full volume:
coronal = fb.get_slice("head", "coronal", 64, shape=(256, 256, 256), voxel_size=0.5)
```

---

## `forbuilder.save`

Write a generated phantom to disk in TIFF, NIfTI, or OME-Zarr format.

```python
def save(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
```

**Parameters**:

| Name | Type | Constraints | Description |
|------|------|-------------|-------------|
| `phantom` | `GeneratedPhantom` | — | The phantom to save |
| `path` | `str` or `PathLike` | valid filesystem path | Output path; format determined by extension |

**Extension → format mapping**:

| Extension | Format | Library |
|-----------|--------|---------|
| `.tif`, `.tiff` | TIFF (multi-page, ImageJ compatible) | `tifffile` |
| `.nii.gz` | NIfTI-1 compressed | `nibabel` |
| `.ome.zarr` | OME-Zarr v0.5 (OME-NGFF 0.5), single resolution | `zarr` |

**Metadata written**:
- **TIFF**: voxel spacing stored in ImageJ metadata (`spacing`, `unit = "um"` converted from mm). Shape as `(z, y, x)`.
- **NIfTI**: affine matrix from voxel sizes (diagonal, no rotation); `xyzt_units` set to mm.
- **OME-Zarr**: OME-NGFF v0.5 metadata written into `zarr.json` (Zarr v3) under `attributes.ome.multiscales`; axes `(z, y, x)` with `unit = "millimeter"`; `coordinateTransformations` scale set to `(dz, dy, dx)`.

**Raises**:
- `ValueError` — if `path` has an unrecognised or missing extension.
- `OSError` — propagated unmodified if the filesystem write fails.

**Example**:
```python
fb.save(phantom, "output.tif")
fb.save(phantom, "output.nii.gz")
fb.save(phantom, "output.ome.zarr")
```

---

## Built-in Template Names

| Name | Description | Components | Source |
|------|-------------|------------|--------|
| `"head"` | FORBILD 3D head phantom | 34 truncated ellipsoids | Lauritsch & Härer (1998) |
| `"thorax"` | FORBILD 3D thorax phantom | ~35 mixed primitives | FORBILD group |

Templates are bundled as JSON files under `forbuilder/phantoms/` and resolved at import
time. Unrecognised names trigger a `ValueError` listing the available templates.
