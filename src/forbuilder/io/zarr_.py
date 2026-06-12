"""OME-Zarr v0.5 read/write for GeneratedPhantom (OME-NGFF 0.5, Zarr v3)."""

from __future__ import annotations

import os

import numpy as np
import zarr

from forbuilder.rasterizer import GeneratedPhantom


def read_zarr(path: str | os.PathLike) -> GeneratedPhantom:
    store = zarr.open_group(str(path), mode="r")
    array = np.asarray(store["0"], dtype=np.uint8)
    scale = (
        store.attrs["ome"]["multiscales"][0]["datasets"][0]
        ["coordinateTransformations"][0]["scale"]
    )
    dz, dy, dx = (float(s) for s in scale)
    return GeneratedPhantom(array=array, voxel_size=(dz, dy, dx))


def write_zarr(phantom: GeneratedPhantom, path: str | os.PathLike) -> None:
    """Write *phantom* to an OME-Zarr v0.5 directory store.

    The array is stored at path ``"0"`` within a Zarr v3 group.
    OME-NGFF 0.5 multiscales metadata is written to ``store.attrs["ome"]``.

    Parameters
    ----------
    phantom: The phantom to write.
    path:    Destination path (e.g. ``"output.ome.zarr"``).
    """
    dz, dy, dx = phantom.voxel_size
    store = zarr.open_group(str(path), mode="w", zarr_format=3)
    arr = store.create_array(
        "0", shape=phantom.shape, dtype="uint8", dimension_names=("z", "y", "x")
    )
    arr[:] = phantom.array
    store.attrs["ome"] = {
        "version": "0.5",
        "multiscales": [
            {
                "name": phantom.spec.name if phantom.spec is not None else None,
                "axes": [
                    {"name": "z", "type": "space", "unit": "millimeter"},
                    {"name": "y", "type": "space", "unit": "millimeter"},
                    {"name": "x", "type": "space", "unit": "millimeter"},
                ],
                "datasets": [
                    {
                        "path": "0",
                        "coordinateTransformations": [
                            {"type": "scale", "scale": [dz, dy, dx]}
                        ],
                    }
                ],
            }
        ],
    }
