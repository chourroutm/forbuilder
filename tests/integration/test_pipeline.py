"""Integration tests — full generate → inspect → slice → save pipeline."""

import json

import numpy as np
import pytest

import forbuilder as fb

# ---------------------------------------------------------------------------
# US1 — generate()
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_returns_generated_phantom(self):
        p = fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)
        assert p is not None

    def test_shape_correct(self):
        p = fb.generate("head", shape=(32, 48, 64), voxel_size=1.0)
        assert p.array.shape == (32, 48, 64)

    def test_dtype_uint8(self):
        p = fb.generate("head", shape=(16, 16, 16), voxel_size=1.0)
        assert p.array.dtype == np.uint8

    def test_isotropic_voxel_size(self):
        p = fb.generate("head", shape=(16, 16, 16), voxel_size=0.5)
        assert p.voxel_size == (0.5, 0.5, 0.5)

    def test_anisotropic_voxel_size(self):
        p = fb.generate("head", shape=(16, 16, 16), voxel_size=(2.0, 1.0, 1.0))
        assert p.voxel_size == (2.0, 1.0, 1.0)

    def test_deterministic(self):
        p1 = fb.generate("head", shape=(16, 16, 16), voxel_size=1.0)
        p2 = fb.generate("head", shape=(16, 16, 16), voxel_size=1.0)
        assert np.array_equal(p1.array, p2.array)

    def test_thorax_template(self):
        p = fb.generate("thorax", shape=(16, 16, 16), voxel_size=2.0)
        assert p.array.shape == (16, 16, 16)

    def test_negative_shape_raises(self):
        with pytest.raises(ValueError, match="shape"):
            fb.generate("head", shape=(-1, 32, 32), voxel_size=1.0)

    def test_zero_shape_raises(self):
        with pytest.raises(ValueError, match="shape"):
            fb.generate("head", shape=(0, 32, 32), voxel_size=1.0)

    def test_zero_voxel_size_raises(self):
        with pytest.raises(ValueError, match="voxel_size"):
            fb.generate("head", shape=(16, 16, 16), voxel_size=0.0)

    def test_negative_voxel_size_raises(self):
        with pytest.raises(ValueError, match="voxel_size"):
            fb.generate("head", shape=(16, 16, 16), voxel_size=-1.0)

    def test_unknown_template_raises(self):
        with pytest.raises(ValueError, match="head_v99"):
            fb.generate("head_v99", shape=(16, 16, 16), voxel_size=1.0)

    def test_from_custom_json_file(self, tmp_path):
        spec = {
            "name": "simple",
            "background": 0,
            "components": [
                {
                    "name": "ball",
                    "type": "sphere",
                    "value": 200,
                    "center": [0.0, 0.0, 0.0],
                    "radius": 50.0,
                }
            ],
        }
        p = tmp_path / "spec.json"
        p.write_text(json.dumps(spec))
        phantom = fb.generate(str(p), shape=(8, 8, 8), voxel_size=1.0)
        assert np.all(phantom.array == 200)


# ---------------------------------------------------------------------------
# US1 — save()
# ---------------------------------------------------------------------------


class TestSave:
    def _phantom(self):
        return fb.generate("head", shape=(16, 16, 16), voxel_size=1.0)

    def test_save_tiff(self, tmp_path):
        path = tmp_path / "out.tif"
        fb.save(self._phantom(), path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_save_nifti_gz(self, tmp_path):
        path = tmp_path / "out.nii.gz"
        fb.save(self._phantom(), path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_save_nifti_uncompressed(self, tmp_path):
        path = tmp_path / "out.nii"
        fb.save(self._phantom(), path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_save_ome_zarr(self, tmp_path):
        path = tmp_path / "out.ome.zarr"
        fb.save(self._phantom(), path)
        assert path.exists()

    def test_save_unknown_extension_raises(self, tmp_path):
        path = tmp_path / "out.xyz"
        with pytest.raises(ValueError, match=".xyz"):
            fb.save(self._phantom(), path)

    def test_tiff_round_trip_shape(self, tmp_path):
        import tifffile

        path = tmp_path / "out.tif"
        p = self._phantom()
        fb.save(p, path)
        loaded = tifffile.imread(str(path))
        assert loaded.shape == p.array.shape

    def test_nifti_gz_round_trip_shape(self, tmp_path):
        import nibabel as nib

        path = tmp_path / "out.nii.gz"
        p = self._phantom()
        fb.save(p, path)
        loaded = nib.load(str(path))
        assert tuple(loaded.shape) == p.array.shape

    def test_nifti_uncompressed_round_trip_shape(self, tmp_path):
        import nibabel as nib

        path = tmp_path / "out.nii"
        p = self._phantom()
        fb.save(p, path)
        loaded = nib.load(str(path))
        assert tuple(loaded.shape) == p.array.shape

    def test_load_tif_round_trip(self, tmp_path):
        path = tmp_path / "out.tif"
        p = self._phantom()
        fb.save(p, path)
        result = fb.load(path)
        assert result.array.shape == p.array.shape
        assert result.array.dtype == p.array.dtype
        assert np.array_equal(result.array, p.array)
        assert result.voxel_size == pytest.approx(p.voxel_size)

    def test_load_ome_zarr_round_trip(self, tmp_path):
        path = tmp_path / "out.ome.zarr"
        p = self._phantom()
        fb.save(p, path)
        result = fb.load(path)
        assert result.array.shape == p.array.shape
        assert result.array.dtype == p.array.dtype
        assert np.array_equal(result.array, p.array)
        assert result.voxel_size == pytest.approx(p.voxel_size)

    def test_load_nifti_gz_round_trip(self, tmp_path):
        path = tmp_path / "out.nii.gz"
        p = self._phantom()
        fb.save(p, path)
        result = fb.load(path)
        assert result.array.shape == p.array.shape
        assert result.array.dtype == p.array.dtype
        assert np.array_equal(result.array, p.array)
        assert result.voxel_size == pytest.approx(p.voxel_size)

    def test_load_nifti_uncompressed_round_trip(self, tmp_path):
        path = tmp_path / "out.nii"
        p = self._phantom()
        fb.save(p, path)
        result = fb.load(path)
        assert result.array.shape == p.array.shape
        assert result.array.dtype == p.array.dtype
        assert np.array_equal(result.array, p.array)
        assert result.voxel_size == pytest.approx(p.voxel_size)

    def test_ome_zarr_metadata(self, tmp_path):
        import zarr

        path = tmp_path / "out.ome.zarr"
        p = self._phantom()
        fb.save(p, path)
        store = zarr.open_group(str(path), mode="r")
        assert "ome" in store.attrs
        ms = store.attrs["ome"]["multiscales"][0]
        assert ms["version"] == "0.5"
        assert len(ms["axes"]) == 3


# ---------------------------------------------------------------------------
# US2 — get_components() and overrides
# ---------------------------------------------------------------------------


class TestGetComponents:
    def test_returns_list(self):
        components = fb.get_components("head")
        assert isinstance(components, list)
        assert len(components) >= 30

    def test_thorax_has_components(self):
        components = fb.get_components("thorax")
        assert len(components) >= 10

    def test_each_component_has_name_and_value(self):
        for c in fb.get_components("head"):
            assert hasattr(c, "name")
            assert hasattr(c, "value")
            assert 0 <= c.value <= 255

    def test_override_changes_voxel_values(self):
        p_default = fb.generate("head", shape=(16, 16, 16), voxel_size=1.0)
        p_modified = fb.generate(
            "head", shape=(16, 16, 16), voxel_size=1.0, overrides={"outer_skull": 50}
        )
        assert not np.array_equal(p_default.array, p_modified.array)

    def test_override_unknown_key_raises(self):
        with pytest.raises(ValueError, match="xyz_unknown"):
            fb.generate(
                "head", shape=(8, 8, 8), voxel_size=1.0, overrides={"xyz_unknown": 100}
            )

    def test_override_out_of_range_raises(self):
        with pytest.raises(ValueError, match="256"):
            fb.generate(
                "head", shape=(8, 8, 8), voxel_size=1.0, overrides={"outer_skull": 256}
            )


# ---------------------------------------------------------------------------
# US3 — get_slice()
# ---------------------------------------------------------------------------


class TestGetSlice:
    def _phantom(self):
        return fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)

    def test_axial_shape(self):
        p = self._phantom()
        s = fb.get_slice(p, "axial", 16)
        assert s.shape == (32, 32)

    def test_coronal_shape(self):
        p = self._phantom()
        s = fb.get_slice(p, "coronal", 16)
        assert s.shape == (32, 32)

    def test_sagittal_shape(self):
        p = self._phantom()
        s = fb.get_slice(p, "sagittal", 16)
        assert s.shape == (32, 32)

    def test_dtype_uint8(self):
        p = self._phantom()
        s = fb.get_slice(p, "axial", 0)
        assert s.dtype == np.uint8

    def test_axial_values_match_full_array(self):
        p = self._phantom()
        s = fb.get_slice(p, "axial", 10)
        assert np.array_equal(s, p.array[10, :, :])

    def test_coronal_values_match_full_array(self):
        p = self._phantom()
        s = fb.get_slice(p, "coronal", 10)
        assert np.array_equal(s, p.array[:, 10, :])

    def test_sagittal_values_match_full_array(self):
        p = self._phantom()
        s = fb.get_slice(p, "sagittal", 10)
        assert np.array_equal(s, p.array[:, :, 10])

    def test_out_of_bounds_raises(self):
        p = self._phantom()
        with pytest.raises(ValueError, match="index"):
            fb.get_slice(p, "axial", 999)

    def test_from_string_source_axial(self):
        s = fb.get_slice(
            "head", "axial", 16, shape=(32, 32, 32), voxel_size=1.0
        )
        assert s.shape == (32, 32)
        assert s.dtype == np.uint8

    def test_string_source_missing_shape_raises(self):
        with pytest.raises((ValueError, TypeError)):
            fb.get_slice("head", "axial", 16, voxel_size=1.0)
