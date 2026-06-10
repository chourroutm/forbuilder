"""Write a GeneratedPhantom to an OME-Zarr v0.5 store (OME-NGFF 0.5, Zarr v3)."""

from __future__ import annotations

import os

import zarr

from forbuilder.rasterizer import GeneratedPhantom


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
    arr = store.create_array("0", shape=phantom.shape, dtype="uint8")
    arr[:] = phantom.array
    store.attrs["ome"] = {
        "multiscales": [
            {
                "version": "0.5",
                "name": phantom.spec.name,
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
                "coordinateTransformations": [
                    {"type": "scale", "scale": [1.0, 1.0, 1.0]}
                ],
            }
        ]
    }
