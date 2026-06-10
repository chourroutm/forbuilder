"""Unit tests for rasterizer — containment math and rasterization correctness."""

import numpy as np

from forbuilder.geometry import Cone, Cylinder, Ellipsoid, PhantomSpec, Sphere
from forbuilder.rasterizer import GeneratedPhantom, rasterize


def _spec(*components, background=0, name="test"):
    return PhantomSpec(name=name, background=background, components=list(components))


# ---------------------------------------------------------------------------
# GeneratedPhantom structure
# ---------------------------------------------------------------------------


class TestGeneratedPhantom:
    def test_is_dataclass(self):
        spec = _spec(Sphere(name="s", value=100, center=(0, 0, 0), radius=50.0))
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert isinstance(p, GeneratedPhantom)
        assert hasattr(p, "array")
        assert hasattr(p, "shape")
        assert hasattr(p, "voxel_size")
        assert hasattr(p, "spec")

    def test_array_dtype_is_uint8(self):
        spec = _spec(Sphere(name="s", value=100, center=(0, 0, 0), radius=50.0))
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert p.array.dtype == np.uint8

    def test_shape_tuple(self):
        spec = _spec(Sphere(name="s", value=100, center=(0, 0, 0), radius=50.0))
        p = rasterize(spec, shape=(3, 5, 7), voxel_size=1.0)
        assert p.shape == (3, 5, 7)
        assert p.array.shape == (3, 5, 7)

    def test_isotropic_voxel_size_stored_as_tuple(self):
        spec = _spec(Sphere(name="s", value=100, center=(0, 0, 0), radius=50.0))
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=2.0)
        assert p.voxel_size == (2.0, 2.0, 2.0)

    def test_anisotropic_voxel_size(self):
        spec = _spec(Sphere(name="s", value=100, center=(0, 0, 0), radius=50.0))
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=(1.0, 2.0, 3.0))
        assert p.voxel_size == (1.0, 2.0, 3.0)


# ---------------------------------------------------------------------------
# Background fill
# ---------------------------------------------------------------------------


class TestBackgroundFill:
    def test_tiny_sphere_fills_background(self):
        # sphere so small it touches no voxel centres
        spec = _spec(
            Sphere(name="s", value=200, center=(100, 100, 100), radius=0.001),
            background=42,
        )
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert np.all(p.array == 42)

    def test_background_value_used(self):
        spec = PhantomSpec(
            name="t",
            background=77,
            components=[Sphere(name="s", value=200, center=(999, 999, 999), radius=0.01)],
        )
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert np.all(p.array == 77)


# ---------------------------------------------------------------------------
# Sphere containment
# ---------------------------------------------------------------------------


class TestSphereRasterization:
    def test_large_sphere_fills_all_voxels(self):
        spec = _spec(Sphere(name="s", value=200, center=(0, 0, 0), radius=1000.0))
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert np.all(p.array == 200)

    def test_sphere_centred_on_grid(self):
        # 8x8x8 grid, 1mm voxels → spans ±4 mm; sphere radius 2mm centred at origin
        spec = _spec(Sphere(name="s", value=150, center=(0, 0, 0), radius=2.0))
        p = rasterize(spec, shape=(8, 8, 8), voxel_size=1.0)
        # centre voxels should be filled
        assert p.array[4, 4, 4] == 150
        # corner voxels should be background
        assert p.array[0, 0, 0] == 0

    def test_sphere_correct_unique_values(self):
        spec = _spec(Sphere(name="s", value=200, center=(0, 0, 0), radius=2.0))
        p = rasterize(spec, shape=(8, 8, 8), voxel_size=1.0)
        unique = set(p.array.flatten().tolist())
        assert unique == {0, 200}


# ---------------------------------------------------------------------------
# Ellipsoid containment
# ---------------------------------------------------------------------------


class TestEllipsoidRasterization:
    def test_axis_aligned_ellipsoid(self):
        # Wide along x, narrow along y and z
        spec = _spec(
            Ellipsoid(
                name="e",
                value=100,
                center=(0, 0, 0),
                semi_axes=(10.0, 1.0, 1.0),
            )
        )
        p = rasterize(spec, shape=(16, 8, 8), voxel_size=1.0)
        # Along z-axis (wide dim in voxel coords is axis 0 = z): many voxels filled
        assert p.array[8, 4, 4] == 100  # centre
        assert p.array[0, 4, 4] == 0  # far edge — outside 10mm radius

    def test_truncated_ellipsoid(self):
        spec = _spec(
            Ellipsoid(
                name="e",
                value=200,
                center=(0, 0, 0),
                semi_axes=(5.0, 5.0, 5.0),
                z_min=0.0,  # only upper half (z > 0)
            )
        )
        p = rasterize(spec, shape=(8, 8, 8), voxel_size=1.0)
        # Lower half (z < 0) should be background
        assert p.array[0, 4, 4] == 0  # z < 0


# ---------------------------------------------------------------------------
# Component priority (later overwrites earlier)
# ---------------------------------------------------------------------------


class TestComponentPriority:
    def test_later_component_overwrites_earlier(self):
        spec = PhantomSpec(
            name="t",
            background=0,
            components=[
                Sphere(name="outer", value=100, center=(0, 0, 0), radius=1000.0),
                Sphere(name="inner", value=200, center=(0, 0, 0), radius=1000.0),
            ],
        )
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert np.all(p.array == 200)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_two_calls_identical(self):
        spec = _spec(Sphere(name="s", value=150, center=(0, 0, 0), radius=3.0))
        p1 = rasterize(spec, shape=(8, 8, 8), voxel_size=1.0)
        p2 = rasterize(spec, shape=(8, 8, 8), voxel_size=1.0)
        assert np.array_equal(p1.array, p2.array)


# ---------------------------------------------------------------------------
# Cylinder containment
# ---------------------------------------------------------------------------


class TestCylinderRasterization:
    def test_large_cylinder_fills_grid(self):
        spec = _spec(
            Cylinder(
                name="c",
                value=130,
                center=(0, 0, 0),
                radius=1000.0,
                half_height=1000.0,
            )
        )
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert np.all(p.array == 130)


# ---------------------------------------------------------------------------
# Cone containment
# ---------------------------------------------------------------------------


class TestConeRasterization:
    def test_large_cone_fills_some_voxels(self):
        spec = _spec(
            Cone(
                name="cn",
                value=180,
                center=(0, 0, 0),
                base_radius=1000.0,
                height=1000.0,
            )
        )
        p = rasterize(spec, shape=(4, 4, 4), voxel_size=1.0)
        assert 180 in p.array
