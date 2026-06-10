"""Extract 2-D slices from a GeneratedPhantom or a phantom source."""

from __future__ import annotations

import os

import numpy as np

from forbuilder.rasterizer import GeneratedPhantom

_VALID_AXES = {"axial", "coronal", "sagittal"}


def get_slice(
    source: GeneratedPhantom | str | os.PathLike,
    axis: str,
    index: int,
    *,
    shape: tuple[int, int, int] | None = None,
    voxel_size: float | tuple[float, float, float] | None = None,
) -> np.ndarray:
    """Extract a 2-D uint8 slice from a phantom.

    Parameters
    ----------
    source:     A GeneratedPhantom, a built-in template name, or a path to a
                phantom spec file.
    axis:       One of ``"axial"``, ``"coronal"``, or ``"sagittal"``.
    index:      Voxel index along the chosen axis (0-based).
    shape:      Required when *source* is a string or path.
    voxel_size: Voxel size in mm. Required when *source* is a string or path.

    Returns
    -------
    2-D uint8 NumPy array.

    Raises
    ------
    ValueError  Unknown *axis*, out-of-bounds *index*, or missing *shape*.
    """
    if axis not in _VALID_AXES:
        raise ValueError(
            f"Unknown axis {axis!r}. Must be one of: {sorted(_VALID_AXES)}"
        )

    if not isinstance(source, GeneratedPhantom):
        if shape is None:
            raise ValueError(
                "shape must be provided when source is a template name or file path."
            )
        from forbuilder.loader import load_spec
        from forbuilder.rasterizer import rasterize

        spec = load_spec(source)
        vs = voxel_size if voxel_size is not None else 1.0
        source = rasterize(spec, shape=shape, voxel_size=vs)

    phantom: GeneratedPhantom = source
    nz, ny, nx = phantom.shape

    axis_size = {"axial": nz, "coronal": ny, "sagittal": nx}[axis]
    if not (0 <= index < axis_size):
        raise ValueError(
            f"index {index} is out of bounds for axis {axis!r} with size {axis_size}. "
            f"Valid range: 0 to {axis_size - 1}."
        )

    if axis == "axial":
        return phantom.array[index, :, :]
    elif axis == "coronal":
        return phantom.array[:, index, :]
    else:
        return phantom.array[:, :, index]
