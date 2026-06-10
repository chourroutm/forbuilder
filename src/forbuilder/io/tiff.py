"""Write a GeneratedPhantom to a multi-page TIFF file."""

from __future__ import annotations

import os

import tifffile

from forbuilder.rasterizer import GeneratedPhantom


def write_tiff(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
    """Write *phantom* to a multi-page TIFF with voxel-spacing metadata.

    Parameters
    ----------
    phantom: The phantom to write.
    path:    Destination path (e.g. ``"output.tif"``).
    """
    dz, dy, dx = phantom.voxel_size
    # tifffile expects resolution as (pixels_per_unit_y, pixels_per_unit_x)
    # We store voxel size in mm; tifffile unit tag uses "um" by convention → convert
    res_y = 1.0 / (dy * 1000.0)  # mm → um → pixels per um
    res_x = 1.0 / (dx * 1000.0)

    tifffile.imwrite(
        str(path),
        phantom.array,
        imagej=True,
        resolution=(res_y, res_x),
        metadata={"spacing": dz, "unit": "mm", "axes": "ZYX"},
    )
