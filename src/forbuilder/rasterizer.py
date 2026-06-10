"""Slice-by-slice vectorised rasterizer for FORBILD phantom geometries."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from forbuilder._logging import logger
from forbuilder.geometry import Cone, Cylinder, Ellipsoid, PhantomSpec, Sphere


@dataclass
class GeneratedPhantom:
    """Result of rasterizing a PhantomSpec onto a voxel grid.

    Parameters
    ----------
    array:      3-D uint8 NumPy array of shape (nz, ny, nx).
    shape:      (nz, ny, nx).
    voxel_size: Physical voxel dimensions (dz, dy, dx) in mm.
    spec:       The PhantomSpec used to produce this phantom.
    """

    array: np.ndarray
    shape: tuple[int, int, int]
    voxel_size: tuple[float, float, float]
    spec: PhantomSpec


# ---------------------------------------------------------------------------
# Rotation helper
# ---------------------------------------------------------------------------


def _zyx_rotation_matrix(ez: float, ey: float, ex: float) -> np.ndarray:
    """3x3 ZYX Euler rotation matrix."""
    cz, sz = math.cos(ez), math.sin(ez)
    cy, sy = math.cos(ey), math.sin(ey)
    cx, sx = math.cos(ex), math.sin(ex)
    return np.array(
        [
            [cy * cz, cz * sx * sy - cx * sz, cx * cz * sy + sx * sz],
            [cy * sz, cx * cz + sx * sy * sz, cx * sy * sz - cz * sx],
            [-sy, cy * sx, cx * cy],
        ]
    )


# ---------------------------------------------------------------------------
# Per-component containment masks (2-D, vectorised over y and x)
# ---------------------------------------------------------------------------


def _ellipsoid_mask(
    comp: Ellipsoid, z_k: float, y_g: np.ndarray, x_g: np.ndarray
) -> np.ndarray:
    if comp.z_min is not None and z_k < comp.z_min:
        return np.zeros(y_g.shape, dtype=bool)
    if comp.z_max is not None and z_k > comp.z_max:
        return np.zeros(y_g.shape, dtype=bool)

    cz, cy, cx = comp.center
    az, ay, ax = comp.semi_axes
    ez, ey, ex = comp.euler_angles

    dz = float(z_k - cz)
    dy = y_g - cy
    dx = x_g - cx

    if ez == 0.0 and ey == 0.0 and ex == 0.0:
        return (dz / az) ** 2 + (dy / ay) ** 2 + (dx / ax) ** 2 <= 1.0

    rot_t = _zyx_rotation_matrix(ez, ey, ex).T
    dz_r = rot_t[0, 0] * dz + rot_t[0, 1] * dy + rot_t[0, 2] * dx
    dy_r = rot_t[1, 0] * dz + rot_t[1, 1] * dy + rot_t[1, 2] * dx
    dx_r = rot_t[2, 0] * dz + rot_t[2, 1] * dy + rot_t[2, 2] * dx
    return (dz_r / az) ** 2 + (dy_r / ay) ** 2 + (dx_r / ax) ** 2 <= 1.0


def _sphere_mask(
    comp: Sphere, z_k: float, y_g: np.ndarray, x_g: np.ndarray
) -> np.ndarray:
    cz, cy, cx = comp.center
    return (z_k - cz) ** 2 + (y_g - cy) ** 2 + (x_g - cx) ** 2 <= comp.radius**2


def _cylinder_mask(
    comp: Cylinder, z_k: float, y_g: np.ndarray, x_g: np.ndarray
) -> np.ndarray:
    cz, cy, cx = comp.center
    az, ay, ax = comp.axis
    dz = float(z_k - cz)
    dy = y_g - cy
    dx = x_g - cx
    proj = dz * az + dy * ay + dx * ax
    rad_z = dz - proj * az
    rad_y = dy - proj * ay
    rad_x = dx - proj * ax
    return (np.abs(proj) <= comp.half_height) & (
        rad_z**2 + rad_y**2 + rad_x**2 <= comp.radius**2
    )


def _cone_mask(
    comp: Cone, z_k: float, y_g: np.ndarray, x_g: np.ndarray
) -> np.ndarray:
    cz, cy, cx = comp.center
    az, ay, ax = comp.axis
    dz = float(z_k - cz)
    dy = y_g - cy
    dx = x_g - cx
    h = dz * az + dy * ay + dx * ax
    valid_h = (h >= 0) & (h <= comp.height)
    r_limit = comp.base_radius * (1.0 - h / comp.height)
    rad_z = dz - h * az
    rad_y = dy - h * ay
    rad_x = dx - h * ax
    return valid_h & (rad_z**2 + rad_y**2 + rad_x**2 <= r_limit**2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _normalise_voxel_size(v: float | tuple) -> tuple[float, float, float]:
    if isinstance(v, (int, float)):
        return (float(v),) * 3
    return tuple(float(x) for x in v)


def rasterize(
    spec: PhantomSpec,
    shape: tuple[int, int, int],
    voxel_size: float | tuple[float, float, float],
) -> GeneratedPhantom:
    """Rasterize a PhantomSpec onto a voxel grid, slice by slice along z.

    Parameters
    ----------
    spec:       Phantom definition.
    shape:      Output dimensions (nz, ny, nx).
    voxel_size: Voxel size in mm — scalar (isotropic) or (dz, dy, dx).

    Returns
    -------
    GeneratedPhantom with a uint8 array of the given shape.
    """
    nz, ny, nx = shape
    dz, dy, dx = _normalise_voxel_size(voxel_size)

    # Place phantom origin at array centre
    origin_z = -(nz * dz) / 2.0
    origin_y = -(ny * dy) / 2.0
    origin_x = -(nx * dx) / 2.0

    iy = np.arange(ny, dtype=np.float64)
    ix = np.arange(nx, dtype=np.float64)
    y_g, x_g = np.meshgrid(
        origin_y + (iy + 0.5) * dy,
        origin_x + (ix + 0.5) * dx,
        indexing="ij",
    )

    output = np.full((nz, ny, nx), fill_value=spec.background, dtype=np.uint8)

    for iz in range(nz):
        logger.debug("Rasterizing slice %d / %d", iz + 1, nz)
        z_k = origin_z + (iz + 0.5) * dz
        sl = output[iz]

        for comp in spec.components:
            if isinstance(comp, Ellipsoid):
                mask = _ellipsoid_mask(comp, z_k, y_g, x_g)
            elif isinstance(comp, Sphere):
                mask = _sphere_mask(comp, z_k, y_g, x_g)
            elif isinstance(comp, Cylinder):
                mask = _cylinder_mask(comp, z_k, y_g, x_g)
            elif isinstance(comp, Cone):
                mask = _cone_mask(comp, z_k, y_g, x_g)
            else:
                continue
            sl[mask] = comp.value

    # Warn for components whose value does not appear anywhere in the output
    for comp in spec.components:
        if not np.any(output == comp.value):
            logger.warning(
                "Component %r (value=%d) covers zero voxels at the requested resolution.",
                comp.name,
                comp.value,
            )

    logger.debug("Rasterization complete: shape=%s, voxel_size=%s", shape, (dz, dy, dx))
    return GeneratedPhantom(
        array=output,
        shape=(nz, ny, nx),
        voxel_size=(dz, dy, dx),
        spec=spec,
    )
