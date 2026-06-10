"""Performance benchmarks for forbuilder rasterization."""

import numpy as np
import pytest

import forbuilder as fb
from forbuilder.geometry import PhantomSpec, Sphere
from forbuilder.rasterizer import rasterize


@pytest.fixture
def small_head():
    return fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)


@pytest.fixture
def medium_head():
    return fb.generate("head", shape=(128, 128, 128), voxel_size=1.0)


def test_rasterize_small(benchmark):
    spec = PhantomSpec(
        name="bench",
        background=0,
        components=[Sphere(name="s", value=200, center=(0, 0, 0), radius=100.0)],
    )
    result = benchmark(rasterize, spec, shape=(64, 64, 64), voxel_size=1.0)
    assert result.array.dtype == np.uint8


def test_rasterize_head_64(benchmark):
    result = benchmark(fb.generate, "head", shape=(64, 64, 64), voxel_size=1.0)
    assert result.array.shape == (64, 64, 64)


def test_rasterize_head_128(benchmark):
    result = benchmark(fb.generate, "head", shape=(128, 128, 128), voxel_size=1.0)
    assert result.array.shape == (128, 128, 128)


def test_get_slice_axial(benchmark, small_head):
    result = benchmark(fb.get_slice, small_head, "axial", 32)
    assert result.shape == (64, 64)


def test_get_slice_coronal(benchmark, small_head):
    result = benchmark(fb.get_slice, small_head, "coronal", 32)
    assert result.shape == (64, 64)


def test_get_slice_sagittal(benchmark, small_head):
    result = benchmark(fb.get_slice, small_head, "sagittal", 32)
    assert result.shape == (64, 64)
