# Data Model: FORBILD Phantom Package

**Feature**: `001-forbild-phantom-package`
**Date**: 2026-06-10
**Source**: [spec.md](spec.md) | [research.md](research.md)

---

## Entities

### Component (abstract base)

Represents one geometric object in a phantom definition.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `str` | non-empty, unique within spec | Human-readable identifier (e.g. `"outer_skull"`) |
| `value` | `int` | 0–255 | Unsigned 8-bit attenuation value assigned to all voxels inside this component |
| `priority` | `int` | ≥ 0 | Rasterization order; higher priority overwrites lower. Components defined later in the list have higher priority. |

**Validation rules**:
- `name` MUST be a non-empty string with no leading/trailing whitespace.
- `value` MUST be an integer in [0, 255]; values outside this range MUST be rejected at
  load time with a descriptive `ValueError`.

---

### Ellipsoid (extends Component)

An optionally rotated, optionally truncated ellipsoid.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `center` | `tuple[float, float, float]` | finite values | Centre `(cz, cy, cx)` in mm |
| `semi_axes` | `tuple[float, float, float]` | all > 0 | Semi-axes `(az, ay, ax)` in mm |
| `euler_angles` | `tuple[float, float, float]` | `[−π, π]` each | ZYX Euler rotation angles in radians |
| `z_min` | `float \| None` | < `z_max` if set | Lower z truncation plane in mm (inclusive) |
| `z_max` | `float \| None` | > `z_min` if set | Upper z truncation plane in mm (inclusive) |

**Containment test** (vectorised, for a 2D slice at physical z = z_k):
1. Shift: `dz = z_k − cz`, `dy = y_grid − cy`, `dx = x_grid − cx`
2. Apply inverse ZYX rotation (3×3 matrix) to `(dz, dy, dx)` → `(dz', dy', dx')`
3. Inside: `(dz'/az)² + (dy'/ay)² + (dx'/ax)² ≤ 1`
4. If `z_min` or `z_max` set: additionally require `z_min ≤ z_k ≤ z_max`

---

### Cylinder (extends Component)

An axis-aligned or rotated cylinder with a circular cross-section.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `center` | `tuple[float, float, float]` | finite values | Centre `(cz, cy, cx)` in mm |
| `radius` | `float` | > 0 | Cross-section radius in mm |
| `half_height` | `float` | > 0 | Half the cylinder's axial length in mm |
| `axis` | `tuple[float, float, float]` | unit vector | Direction of the cylinder axis (default `(1,0,0)` = z-axis in (z,y,x)) |

**Containment test**: Project the point onto the axis; check axial distance ≤ `half_height`
and radial distance (perpendicular to axis) ≤ `radius`.

---

### Sphere (extends Component)

A sphere (degenerate ellipsoid, no rotation).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `center` | `tuple[float, float, float]` | finite values | Centre `(cz, cy, cx)` in mm |
| `radius` | `float` | > 0 | Radius in mm |

**Containment test**: `(z_k−cz)² + (y−cy)² + (x−cx)² ≤ radius²`

---

### Cone (extends Component)

A right circular cone, apex at top.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `center` | `tuple[float, float, float]` | finite values | Centre of the base `(cz, cy, cx)` in mm |
| `base_radius` | `float` | > 0 | Radius of the circular base in mm |
| `height` | `float` | > 0 | Height of the cone (apex to base) in mm |
| `axis` | `tuple[float, float, float]` | unit vector | Direction from base to apex (default `(1,0,0)` = upward along z) |

**Containment test**: Compute axial distance `h` from base; check `0 ≤ h ≤ height`
and radial distance ≤ `base_radius × (1 − h / height)`.

---

### PhantomSpec

The complete declarative description of a phantom, loaded from a template name or file.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `str` | non-empty | Identifier for the phantom (e.g. `"head"`, `"thorax"`) |
| `background` | `int` | 0–255 | Value assigned to voxels not covered by any component |
| `components` | `list[Component]` | ≥ 1 | Ordered list; later entries have higher rasterization priority |

**Validation rules**:
- `components` MUST contain at least one entry.
- Component names within a `PhantomSpec` MUST be unique.
- `background` MUST be in [0, 255].

---

### GeneratedPhantom

The in-memory result of rasterizing a `PhantomSpec` onto a voxel grid.

| Field | Type | Description |
|-------|------|-------------|
| `array` | `np.ndarray` shape `(nz, ny, nx)` dtype `uint8` | The rasterized phantom volume |
| `shape` | `tuple[int, int, int]` | `(nz, ny, nx)` |
| `voxel_size` | `tuple[float, float, float]` | Physical voxel dimensions `(dz, dy, dx)` in mm |
| `spec` | `PhantomSpec` | Reference to the phantom definition used |

---

### VoxelGrid (internal)

Not exposed publicly; used by the rasterizer.

| Field | Type | Description |
|-------|------|-------------|
| `shape` | `tuple[int, int, int]` | `(nz, ny, nx)` |
| `voxel_size` | `tuple[float, float, float]` | `(dz, dy, dx)` in mm |
| `origin` | `tuple[float, float, float]` | Physical coordinates of the `[0,0,0]` voxel corner in mm (default: centred on phantom spec origin) |

**Coordinate mapping** (voxel index `(iz, iy, ix)` → physical mm):
```
z = origin_z + (iz + 0.5) × dz
y = origin_y + (iy + 0.5) × dy
x = origin_x + (ix + 0.5) × dx
```
(voxel centres, consistent with standard medical image coordinate conventions)

---

## State Transitions

```
source (template name or file path)
    │
    ▼ load / validate
PhantomSpec (+ optional overrides applied)
    │
    ▼ rasterize onto VoxelGrid
GeneratedPhantom
    │
    ▼ save(path)
File on disk (.tif | .nii.gz | .ome.zarr)
```

---

## Geometry File Schema (JSON)

```json
{
  "name": "string (required)",
  "background": "integer 0-255 (required)",
  "components": [
    {
      "name": "string (required)",
      "type": "ellipsoid | cylinder | sphere | cone (required)",
      "value": "integer 0-255 (required)",
      "center": [cz, cy, cx],
      "semi_axes": [az, ay, ax],
      "euler_angles": [ez, ey, ex],
      "z_min": "float | null",
      "z_max": "float | null"
    }
  ]
}
```

Type-specific required fields:
- `ellipsoid`: `center`, `semi_axes`; optional: `euler_angles` (default `[0,0,0]`), `z_min`, `z_max`
- `cylinder`: `center`, `radius`, `half_height`; optional: `axis` (default `[1,0,0]`)
- `sphere`: `center`, `radius`
- `cone`: `center`, `base_radius`, `height`; optional: `axis` (default `[1,0,0]`)
