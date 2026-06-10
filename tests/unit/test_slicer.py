"""Unit tests for the slicer module."""

import numpy as np
import pytest

from forbuilder.geometry import PhantomSpec, Sphere
from forbuilder.rasterizer import GeneratedPhantom, rasterize
from forbuilder.slicer import get_slice


def _make_phantom(shape=(8, 10, 12)) -> GeneratedPhantom:
    spec = PhantomSpec(
        name="test",
        background=0,
        components=[Sphere(name="s", value=200, center=(0, 0, 0), radius=100.0)],
    )
    return rasterize(spec, shape=shape, voxel_size=1.0)


class TestGetSlicePhantomInput:
    def test_axial_shape(self):
        p = _make_phantom((8, 10, 12))
        s = get_slice(p, "axial", 4)
        assert s.shape == (10, 12)

    def test_coronal_shape(self):
        p = _make_phantom((8, 10, 12))
        s = get_slice(p, "coronal", 5)
        assert s.shape == (8, 12)

    def test_sagittal_shape(self):
        p = _make_phantom((8, 10, 12))
        s = get_slice(p, "sagittal", 6)
        assert s.shape == (8, 10)

    def test_dtype_uint8(self):
        p = _make_phantom()
        assert get_slice(p, "axial", 0).dtype == np.uint8

    def test_axial_values(self):
        p = _make_phantom()
        assert np.array_equal(get_slice(p, "axial", 3), p.array[3, :, :])

    def test_coronal_values(self):
        p = _make_phantom()
        assert np.array_equal(get_slice(p, "coronal", 4), p.array[:, 4, :])

    def test_sagittal_values(self):
        p = _make_phantom()
        assert np.array_equal(get_slice(p, "sagittal", 5), p.array[:, :, 5])

    def test_axial_first_index(self):
        p = _make_phantom((8, 10, 12))
        s = get_slice(p, "axial", 0)
        assert np.array_equal(s, p.array[0, :, :])

    def test_axial_last_index(self):
        p = _make_phantom((8, 10, 12))
        s = get_slice(p, "axial", 7)
        assert np.array_equal(s, p.array[7, :, :])


class TestGetSliceValidation:
    def test_unknown_axis_raises(self):
        p = _make_phantom()
        with pytest.raises(ValueError, match="axis"):
            get_slice(p, "diagonal", 0)

    def test_axial_out_of_bounds_raises(self):
        p = _make_phantom((8, 10, 12))
        with pytest.raises(ValueError, match="index"):
            get_slice(p, "axial", 8)

    def test_coronal_out_of_bounds_raises(self):
        p = _make_phantom((8, 10, 12))
        with pytest.raises(ValueError, match="index"):
            get_slice(p, "coronal", 10)

    def test_sagittal_out_of_bounds_raises(self):
        p = _make_phantom((8, 10, 12))
        with pytest.raises(ValueError, match="index"):
            get_slice(p, "sagittal", 12)

    def test_negative_index_raises(self):
        p = _make_phantom()
        with pytest.raises(ValueError, match="index"):
            get_slice(p, "axial", -1)

    def test_string_source_missing_shape_raises(self):
        with pytest.raises(ValueError, match="shape"):
            get_slice("head", "axial", 0, voxel_size=1.0)


class TestGetSliceStringSource:
    def test_axial_shape(self):
        s = get_slice("head", "axial", 8, shape=(16, 16, 16), voxel_size=1.0)
        assert s.shape == (16, 16)

    def test_coronal_shape(self):
        s = get_slice("head", "coronal", 8, shape=(16, 16, 16), voxel_size=1.0)
        assert s.shape == (16, 16)

    def test_sagittal_shape(self):
        s = get_slice("head", "sagittal", 8, shape=(16, 16, 16), voxel_size=1.0)
        assert s.shape == (16, 16)

    def test_dtype_uint8(self):
        s = get_slice("head", "axial", 8, shape=(16, 16, 16), voxel_size=1.0)
        assert s.dtype == np.uint8

    def test_matches_full_phantom(self):
        p = rasterize(
            PhantomSpec(
                name="t",
                background=0,
                components=[Sphere(name="s", value=200, center=(0, 0, 0), radius=100.0)],
            ),
            shape=(8, 8, 8),
            voxel_size=1.0,
        )
        # Build same spec as string-based path
        s = get_slice(p, "axial", 4)
        assert np.array_equal(s, p.array[4, :, :])
