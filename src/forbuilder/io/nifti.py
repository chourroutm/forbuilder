"""Write a GeneratedPhantom to a compressed NIfTI-1 file."""

from __future__ import annotations

import os

import nibabel as nib
import numpy as np

from forbuilder.rasterizer import GeneratedPhantom


def write_nifti(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
    """Write *phantom* to a NIfTI-1 compressed file (``.nii.gz``).

    Parameters
    ----------
    phantom: The phantom to write.
    path:    Destination path (e.g. ``"output.nii.gz"``).
    """
    dz, dy, dx = phantom.voxel_size
    # Diagonal affine: voxel size in mm along each axis
    affine = np.diag([dx, dy, dz, 1.0])
    img = nib.Nifti1Image(phantom.array, affine=affine)
    # Set spatial units to mm
    img.header.set_xyzt_units(xyz="mm")
    nib.save(img, str(path))
