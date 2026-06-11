"""Unit tests for I/O writers."""


import numpy as np
import pytest

from forbuilder.geometry import PhantomSpec, Sphere
from forbuilder.rasterizer import GeneratedPhantom, rasterize


def _make_phantom(shape=(8, 8, 8)) -> GeneratedPhantom:
    spec = PhantomSpec(
        name="test",
        background=0,
        components=[Sphere(name="s", value=200, center=(0, 0, 0), radius=100.0)],
    )
    return rasterize(spec, shape=shape, voxel_size=1.0)


class TestTiffWriter:
    def test_creates_file(self, tmp_path):
        from forbuilder.io.tiff import write_tiff

        p = tmp_path / "out.tif"
        write_tiff(_make_phantom(), p)
        assert p.exists()
        assert p.stat().st_size > 0

    def test_round_trip_shape(self, tmp_path):
        import tifffile

        from forbuilder.io.tiff import write_tiff

        phantom = _make_phantom((4, 6, 8))
        p = tmp_path / "out.tif"
        write_tiff(phantom, p)
        loaded = tifffile.imread(str(p))
        assert loaded.shape == (4, 6, 8)

    def test_round_trip_dtype(self, tmp_path):
        import tifffile

        from forbuilder.io.tiff import write_tiff

        p = tmp_path / "out.tif"
        write_tiff(_make_phantom(), p)
        loaded = tifffile.imread(str(p))
        assert loaded.dtype == np.uint8


class TestNiftiWriter:
    def test_creates_file_gz(self, tmp_path):
        from forbuilder.io.nifti import write_nifti

        p = tmp_path / "out.nii.gz"
        write_nifti(_make_phantom(), p)
        assert p.exists()
        assert p.stat().st_size > 0

    def test_creates_file_uncompressed(self, tmp_path):
        from forbuilder.io.nifti import write_nifti

        p = tmp_path / "out.nii"
        write_nifti(_make_phantom(), p)
        assert p.exists()
        assert p.stat().st_size > 0

    def test_round_trip_shape(self, tmp_path):
        import nibabel as nib

        from forbuilder.io.nifti import write_nifti

        phantom = _make_phantom((4, 6, 8))
        p = tmp_path / "out.nii.gz"
        write_nifti(phantom, p)
        loaded = nib.load(str(p))
        assert tuple(loaded.shape) == (4, 6, 8)


class TestZarrWriter:
    def test_creates_directory(self, tmp_path):
        from forbuilder.io.zarr_ import write_zarr

        p = tmp_path / "out.ome.zarr"
        write_zarr(_make_phantom(), p)
        assert p.exists()

    def test_ome_ngff_metadata(self, tmp_path):
        import zarr

        from forbuilder.io.zarr_ import write_zarr

        p = tmp_path / "out.ome.zarr"
        write_zarr(_make_phantom(), p)
        store = zarr.open_group(str(p), mode="r")
        assert "ome" in store.attrs
        ms = store.attrs["ome"]["multiscales"][0]
        assert ms["version"] == "0.5"

    def test_array_shape(self, tmp_path):
        import zarr

        from forbuilder.io.zarr_ import write_zarr

        phantom = _make_phantom((4, 6, 8))
        p = tmp_path / "out.ome.zarr"
        write_zarr(phantom, p)
        store = zarr.open_group(str(p), mode="r")
        assert store["0"].shape == (4, 6, 8)


class TestSaveDispatcher:
    def test_tiff_dispatched(self, tmp_path):
        from forbuilder.io import save

        p = tmp_path / "out.tif"
        save(_make_phantom(), p)
        assert p.exists()

    def test_nifti_gz_dispatched(self, tmp_path):
        from forbuilder.io import save

        p = tmp_path / "out.nii.gz"
        save(_make_phantom(), p)
        assert p.exists()

    def test_nifti_uncompressed_dispatched(self, tmp_path):
        from forbuilder.io import save

        p = tmp_path / "out.nii"
        save(_make_phantom(), p)
        assert p.exists()

    def test_zarr_dispatched(self, tmp_path):
        from forbuilder.io import save

        p = tmp_path / "out.ome.zarr"
        save(_make_phantom(), p)
        assert p.exists()

    def test_unknown_extension_raises(self, tmp_path):
        from forbuilder.io import save

        with pytest.raises(ValueError, match=".xyz"):
            save(_make_phantom(), tmp_path / "out.xyz")

    def test_tiff_alt_extension(self, tmp_path):
        from forbuilder.io import save

        p = tmp_path / "out.tiff"
        save(_make_phantom(), p)
        assert p.exists()
