"""Unit tests for geometry dataclasses and PhantomSpec validation."""


import pytest

from forbuilder.geometry import (
    Cone,
    Cylinder,
    Ellipsoid,
    PhantomSpec,
    Sphere,
)

# ---------------------------------------------------------------------------
# Ellipsoid
# ---------------------------------------------------------------------------


class TestEllipsoid:
    def test_basic_construction(self):
        e = Ellipsoid(
            name="outer",
            value=200,
            center=(0.0, 0.0, 0.0),
            semi_axes=(9.6, 12.0, 12.5),
        )
        assert e.name == "outer"
        assert e.value == 200
        assert e.center == (0.0, 0.0, 0.0)
        assert e.semi_axes == (9.6, 12.0, 12.5)

    def test_default_euler_angles_are_zero(self):
        e = Ellipsoid(name="e", value=100, center=(0, 0, 0), semi_axes=(1, 1, 1))
        assert e.euler_angles == (0.0, 0.0, 0.0)

    def test_default_truncation_is_none(self):
        e = Ellipsoid(name="e", value=100, center=(0, 0, 0), semi_axes=(1, 1, 1))
        assert e.z_min is None
        assert e.z_max is None

    def test_value_boundary_0(self):
        e = Ellipsoid(name="e", value=0, center=(0, 0, 0), semi_axes=(1, 1, 1))
        assert e.value == 0

    def test_value_boundary_255(self):
        e = Ellipsoid(name="e", value=255, center=(0, 0, 0), semi_axes=(1, 1, 1))
        assert e.value == 255

    def test_value_negative_raises(self):
        with pytest.raises(ValueError, match="value"):
            Ellipsoid(name="e", value=-1, center=(0, 0, 0), semi_axes=(1, 1, 1))

    def test_value_over_255_raises(self):
        with pytest.raises(ValueError, match="value"):
            Ellipsoid(name="e", value=256, center=(0, 0, 0), semi_axes=(1, 1, 1))

    def test_non_positive_semi_axis_raises(self):
        with pytest.raises(ValueError, match="semi_axes"):
            Ellipsoid(name="e", value=100, center=(0, 0, 0), semi_axes=(0, 1, 1))

    def test_negative_semi_axis_raises(self):
        with pytest.raises(ValueError, match="semi_axes"):
            Ellipsoid(name="e", value=100, center=(0, 0, 0), semi_axes=(1, -1, 1))

    def test_z_min_greater_than_z_max_raises(self):
        with pytest.raises(ValueError, match="z_min"):
            Ellipsoid(
                name="e",
                value=100,
                center=(0, 0, 0),
                semi_axes=(1, 1, 1),
                z_min=5.0,
                z_max=1.0,
            )

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            Ellipsoid(name="", value=100, center=(0, 0, 0), semi_axes=(1, 1, 1))

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            Ellipsoid(name="  ", value=100, center=(0, 0, 0), semi_axes=(1, 1, 1))


# ---------------------------------------------------------------------------
# Sphere
# ---------------------------------------------------------------------------


class TestSphere:
    def test_basic_construction(self):
        s = Sphere(name="eye", value=180, center=(3.0, -2.0, 0.0), radius=1.5)
        assert s.radius == 1.5

    def test_zero_radius_raises(self):
        with pytest.raises(ValueError, match="radius"):
            Sphere(name="s", value=100, center=(0, 0, 0), radius=0.0)

    def test_negative_radius_raises(self):
        with pytest.raises(ValueError, match="radius"):
            Sphere(name="s", value=100, center=(0, 0, 0), radius=-1.0)


# ---------------------------------------------------------------------------
# Cylinder
# ---------------------------------------------------------------------------


class TestCylinder:
    def test_basic_construction(self):
        c = Cylinder(
            name="cyl", value=150, center=(0, 0, 0), radius=2.0, half_height=5.0
        )
        assert c.radius == 2.0
        assert c.half_height == 5.0

    def test_default_axis(self):
        c = Cylinder(name="c", value=100, center=(0, 0, 0), radius=1.0, half_height=1.0)
        assert c.axis == (1.0, 0.0, 0.0)

    def test_zero_radius_raises(self):
        with pytest.raises(ValueError, match="radius"):
            Cylinder(name="c", value=100, center=(0, 0, 0), radius=0.0, half_height=1.0)

    def test_zero_half_height_raises(self):
        with pytest.raises(ValueError, match="half_height"):
            Cylinder(name="c", value=100, center=(0, 0, 0), radius=1.0, half_height=0.0)


# ---------------------------------------------------------------------------
# Cone
# ---------------------------------------------------------------------------


class TestCone:
    def test_basic_construction(self):
        c = Cone(name="cone", value=120, center=(0, 0, 0), base_radius=3.0, height=6.0)
        assert c.base_radius == 3.0
        assert c.height == 6.0

    def test_default_axis(self):
        c = Cone(name="c", value=100, center=(0, 0, 0), base_radius=1.0, height=2.0)
        assert c.axis == (1.0, 0.0, 0.0)

    def test_zero_base_radius_raises(self):
        with pytest.raises(ValueError, match="base_radius"):
            Cone(name="c", value=100, center=(0, 0, 0), base_radius=0.0, height=1.0)

    def test_zero_height_raises(self):
        with pytest.raises(ValueError, match="height"):
            Cone(name="c", value=100, center=(0, 0, 0), base_radius=1.0, height=0.0)


# ---------------------------------------------------------------------------
# PhantomSpec
# ---------------------------------------------------------------------------


class TestPhantomSpec:
    def _make_component(self, name="comp", value=100):
        return Sphere(name=name, value=value, center=(0, 0, 0), radius=1.0)

    def test_basic_construction(self):
        spec = PhantomSpec(
            name="test",
            background=0,
            components=[self._make_component()],
        )
        assert spec.name == "test"
        assert spec.background == 0

    def test_background_boundary_0(self):
        spec = PhantomSpec(name="t", background=0, components=[self._make_component()])
        assert spec.background == 0

    def test_background_boundary_255(self):
        spec = PhantomSpec(name="t", background=255, components=[self._make_component()])
        assert spec.background == 255

    def test_background_negative_raises(self):
        with pytest.raises(ValueError, match="background"):
            PhantomSpec(name="t", background=-1, components=[self._make_component()])

    def test_background_over_255_raises(self):
        with pytest.raises(ValueError, match="background"):
            PhantomSpec(name="t", background=256, components=[self._make_component()])

    def test_empty_components_raises(self):
        with pytest.raises(ValueError, match="components"):
            PhantomSpec(name="t", background=0, components=[])

    def test_duplicate_component_names_raises(self):
        c1 = self._make_component("dup")
        c2 = self._make_component("dup")
        with pytest.raises(ValueError, match="duplicate"):
            PhantomSpec(name="t", background=0, components=[c1, c2])

    def test_empty_spec_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            PhantomSpec(name="", background=0, components=[self._make_component()])
