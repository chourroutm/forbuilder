"""Format dispatcher for phantom file I/O."""

from __future__ import annotations

import os
from pathlib import Path

from forbuilder.rasterizer import GeneratedPhantom

_TIFF_EXTENSIONS = {".tif", ".tiff"}
_NIFTI_EXTENSIONS = {".nii.gz", ".nii"}
_ZARR_EXTENSIONS = {".ome.zarr"}


def save(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
    """Write *phantom* to disk; format inferred from the file extension.

    Parameters
    ----------
    phantom: The phantom to write.
    path:    Destination path. Supported extensions:
             ``.tif`` / ``.tiff`` → TIFF,
             ``.nii`` / ``.nii.gz`` → NIfTI-1,
             ``.ome.zarr`` → OME-Zarr v0.5.

    Raises
    ------
    ValueError  Unrecognised or missing file extension.

    Example
    -------
    >>> from forbuilder.io import save
    >>> save(phantom, "head.tif")
    """
    p = Path(path)
    name = p.name.lower()

    if name.endswith(".nii.gz") or name.endswith(".nii"):
        from forbuilder.io.nifti import write_nifti

        write_nifti(phantom, p)
        return

    if name.endswith(".ome.zarr"):
        from forbuilder.io.zarr_ import write_zarr

        write_zarr(phantom, p)
        return

    suffix = p.suffix.lower()
    if suffix in _TIFF_EXTENSIONS:
        from forbuilder.io.tiff import write_tiff

        write_tiff(phantom, p)
        return

    raise ValueError(
        f"Unrecognised file extension in {str(path)!r}. "
        "Supported: .tif, .tiff, .nii, .nii.gz, .ome.zarr"
    )


def load(path: str | os.PathLike) -> GeneratedPhantom:
    """Read a NIfTI phantom from disk; format inferred from the file extension.

    Parameters
    ----------
    path: Source file path. Supported extensions:
          ``.nii`` / ``.nii.gz`` → NIfTI-1.

    Raises
    ------
    ValueError  Unrecognised or unsupported file extension.
    """
    p = Path(path)
    name = p.name.lower()

    if name.endswith(".nii.gz") or name.endswith(".nii"):
        from forbuilder.io.nifti import read_nifti

        return read_nifti(p)

    raise ValueError(
        f"Unrecognised or unsupported file extension in {str(path)!r}. "
        "Supported for loading: .nii, .nii.gz"
    )
