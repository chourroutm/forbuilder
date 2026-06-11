"""NIfTI-1 read/write for GeneratedPhantom."""

from __future__ import annotations

import os

import nibabel as nib
import numpy as np

from forbuilder.rasterizer import GeneratedPhantom


def write_nifti(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
    dz, dy, dx = phantom.voxel_size
    affine = np.diag([dx, dy, dz, 1.0])
    img = nib.Nifti1Image(phantom.array, affine=affine)
    img.header.set_xyzt_units(xyz="mm")
    nib.save(img, str(path))


def read_nifti(path: str | os.PathLike) -> GeneratedPhantom:
    img = nib.load(str(path))
    array = np.asarray(img.dataobj, dtype=np.uint8)
    # get_zooms() returns (dx, dy, dz); voxel_size convention is (dz, dy, dx)
    dx, dy, dz = (float(z) for z in img.header.get_zooms()[:3])
    return GeneratedPhantom(array=array, voxel_size=(dz, dy, dx))
