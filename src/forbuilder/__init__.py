"""forbuilder — create FORBILD digital phantom volumes as 3-D uint8 arrays."""

from __future__ import annotations

import os

import numpy as np

from forbuilder._version import __version__
from forbuilder.geometry import Component, PhantomSpec
from forbuilder.loader import apply_overrides, load_spec
from forbuilder.rasterizer import GeneratedPhantom, rasterize

__all__ = [
    "__version__",
    "generate",
    "get_components",
    "get_slice",
    "load",
    "save",
    "GeneratedPhantom",
    "PhantomSpec",
    "Component",
]


def generate(
    source: str,
    shape: tuple[int, int, int],
    voxel_size: "float | tuple[float, float, float]",
    *,
    overrides: "dict[str, int] | None" = None,
) -> GeneratedPhantom:
    """Generate a 3-D FORBILD phantom array.

    Parameters
    ----------
    source:     Built-in template name (``"head"``, ``"thorax"``) or path to a
                ``.json`` / ``.yaml`` geometry file.
    shape:      Output dimensions ``(nz, ny, nx)`` — all must be > 0.
    voxel_size: Voxel size in mm. Scalar → isotropic; tuple ``(dz, dy, dx)``.
    overrides:  Optional mapping of component name → new uint8 value (0-255).

    Returns
    -------
    GeneratedPhantom

    Raises
    ------
    ValueError  Invalid shape/voxel_size, unknown template, bad override key/value.

    Example
    -------
    >>> import forbuilder as fb
    >>> p = fb.generate("head", shape=(256, 256, 256), voxel_size=0.5)
    >>> p.array.shape
    (256, 256, 256)
    """
    # Validate shape
    for i, dim in enumerate(shape):
        if dim <= 0:
            raise ValueError(
                f"shape[{i}] must be > 0, got {dim}"
            )

    # Validate voxel_size
    if isinstance(voxel_size, (int, float)):
        vs_values = [voxel_size]
    else:
        vs_values = list(voxel_size)
    for v in vs_values:
        if v <= 0:
            raise ValueError(f"voxel_size must be > 0, got {v}")

    spec = load_spec(source)
    if overrides:
        spec = apply_overrides(spec, overrides)
    return rasterize(spec, shape=shape, voxel_size=voxel_size)


def get_components(source: str) -> "list[Component]":
    """Return the list of component definitions from a template or geometry file.

    Parameters
    ----------
    source: Built-in template name or path to a ``.json`` / ``.yaml`` file.

    Returns
    -------
    Ordered list of Component objects (rasterization priority: last wins).

    Example
    -------
    >>> import forbuilder as fb
    >>> comps = fb.get_components("head")
    >>> len(comps) >= 30
    True
    """
    return load_spec(source).components


def get_slice(
    source: "str | GeneratedPhantom",
    axis: str,
    index: int,
    *,
    shape: "tuple[int, int, int] | None" = None,
    voxel_size: "float | tuple[float, float, float] | None" = None,
) -> "np.ndarray":
    """Extract a single 2-D cross-section from a phantom.

    Parameters
    ----------
    source:     A ``GeneratedPhantom`` or a source string (template name / file path).
                When a string is provided, ``shape`` and ``voxel_size`` are required.
    axis:       ``"axial"``, ``"coronal"``, or ``"sagittal"``.
    index:      Zero-based slice index along the chosen axis.
    shape:      Required when *source* is a string.
    voxel_size: Required when *source* is a string.

    Returns
    -------
    2-D uint8 NumPy array.

    Raises
    ------
    ValueError  Out-of-bounds index, invalid axis, missing shape/voxel_size.

    Example
    -------
    >>> import forbuilder as fb
    >>> s = fb.get_slice("head", "axial", 128, shape=(256,256,256), voxel_size=0.5)
    >>> s.shape
    (256, 256)
    """
    from forbuilder.slicer import get_slice as _get_slice

    return _get_slice(source, axis=axis, index=index, shape=shape, voxel_size=voxel_size)


def load(path: "str | os.PathLike") -> GeneratedPhantom:
    """Load a phantom from a NIfTI file on disk.

    Parameters
    ----------
    path: Source file path (``.nii`` or ``.nii.gz``).

    Returns
    -------
    GeneratedPhantom with the array cast to uint8 and voxel size read from
    the NIfTI header.

    Raises
    ------
    ValueError  Unrecognised or unsupported file extension.

    Example
    -------
    >>> import forbuilder as fb
    >>> p = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)
    >>> fb.save(p, "head.nii.gz")
    >>> p2 = fb.load("head.nii.gz")
    >>> p2.array.shape
    (64, 64, 64)
    """
    from forbuilder.io import load as _load

    return _load(path)


def save(
    phantom: GeneratedPhantom,
    path: "str | os.PathLike",
) -> None:
    """Write a phantom to disk in TIFF, NIfTI, or OME-Zarr v0.5 format.

    The output format is inferred from the file extension:
    - ``.tif`` / ``.tiff``    → multi-page TIFF (ImageJ compatible)
    - ``.nii`` / ``.nii.gz``  → NIfTI-1 (uncompressed / compressed)
    - ``.ome.zarr``           → OME-Zarr v0.5 (OME-NGFF 0.5, Zarr v3)

    Parameters
    ----------
    phantom: The generated phantom to save.
    path:    Destination file path.

    Raises
    ------
    ValueError  Unrecognised file extension.

    Example
    -------
    >>> import forbuilder as fb
    >>> p = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)
    >>> fb.save(p, "head.tif")
    """
    from forbuilder.io import save as _save

    _save(phantom, path)
