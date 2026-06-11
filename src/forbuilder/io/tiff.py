"""TIFF read/write for GeneratedPhantom."""

from __future__ import annotations

import os

import numpy as np
import tifffile

from forbuilder.rasterizer import GeneratedPhantom


def write_tiff(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
    dz, dy, dx = phantom.voxel_size
    # tifffile resolution=(X, Y) in pixels-per-µm; Z spacing in mm via ImageJ metadata
    res_x = 1.0 / (dx * 1000.0)
    res_y = 1.0 / (dy * 1000.0)
    tifffile.imwrite(
        str(path),
        phantom.array,
        imagej=True,
        resolution=(res_x, res_y),
        metadata={"spacing": dz, "unit": "mm", "axes": "ZYX"},
    )


def read_tiff(path: str | os.PathLike) -> GeneratedPhantom:
    with tifffile.TiffFile(str(path)) as tf:
        array = tf.asarray().astype(np.uint8)
        ij = tf.imagej_metadata or {}
        dz = float(ij.get("spacing", 1.0))
        page = tf.pages[0]
        # Tags are RATIONAL (num, den) tuples; tifffile convention: XResolution first
        x_tag = page.tags["XResolution"].value
        y_tag = page.tags["YResolution"].value
        dx = 1.0 / (x_tag[0] / x_tag[1] * 1000.0)
        dy = 1.0 / (y_tag[0] / y_tag[1] * 1000.0)
    return GeneratedPhantom(array=array, voxel_size=(dz, dy, dx))
