"""Dataclasses for FORBILD phantom geometry primitives and phantom specification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


def _check_name(name: str, field_name: str = "name") -> None:
    if not name or not name.strip():
        raise ValueError(f"{field_name} must be a non-empty string, got {name!r}")


def _check_value(value: int, field_name: str = "value") -> None:
    if not (0 <= value <= 255):
        raise ValueError(f"{field_name} must be in [0, 255], got {value}")


def _check_positive(v: float, field_name: str) -> None:
    if v <= 0:
        raise ValueError(f"{field_name} must be > 0, got {v}")


@dataclass
class Ellipsoid:
    """An optionally rotated, optionally z-truncated ellipsoid.

    Parameters
    ----------
    name:         Unique identifier within a PhantomSpec.
    value:        uint8 attenuation value (0-255).
    center:       (cz, cy, cx) centre in mm.
    semi_axes:    (az, ay, ax) semi-axes in mm; all must be > 0.
    euler_angles: ZYX Euler rotation angles in radians (default all-zero).
    z_min:        Lower z truncation plane in mm (inclusive), or None.
    z_max:        Upper z truncation plane in mm (inclusive), or None.
    """

    name: str
    value: int
    center: tuple[float, float, float]
    semi_axes: tuple[float, float, float]
    euler_angles: tuple[float, float, float] = (0.0, 0.0, 0.0)
    z_min: float | None = None
    z_max: float | None = None

    def __post_init__(self) -> None:
        _check_name(self.name)
        _check_value(self.value)
        for ax in self.semi_axes:
            if ax <= 0:
                raise ValueError(f"semi_axes must all be > 0, got {self.semi_axes}")
        if self.z_min is not None and self.z_max is not None:
            if self.z_min >= self.z_max:
                raise ValueError(
                    f"z_min ({self.z_min}) must be < z_max ({self.z_max})"
                )


@dataclass
class Sphere:
    """A sphere (no rotation).

    Parameters
    ----------
    name:   Unique identifier within a PhantomSpec.
    value:  uint8 attenuation value (0-255).
    center: (cz, cy, cx) centre in mm.
    radius: Radius in mm; must be > 0.
    """

    name: str
    value: int
    center: tuple[float, float, float]
    radius: float

    def __post_init__(self) -> None:
        _check_name(self.name)
        _check_value(self.value)
        _check_positive(self.radius, "radius")


@dataclass
class Cylinder:
    """A right circular cylinder (axis-aligned or rotated).

    Parameters
    ----------
    name:        Unique identifier within a PhantomSpec.
    value:       uint8 attenuation value (0-255).
    center:      (cz, cy, cx) centre in mm.
    radius:      Cross-section radius in mm; must be > 0.
    half_height: Half the axial length in mm; must be > 0.
    axis:        Unit vector for the cylinder axis; default = z-axis (1,0,0).
    """

    name: str
    value: int
    center: tuple[float, float, float]
    radius: float
    half_height: float
    axis: tuple[float, float, float] = (1.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        _check_name(self.name)
        _check_value(self.value)
        _check_positive(self.radius, "radius")
        _check_positive(self.half_height, "half_height")


@dataclass
class Cone:
    """A right circular cone (apex up, base at centre).

    Parameters
    ----------
    name:        Unique identifier within a PhantomSpec.
    value:       uint8 attenuation value (0-255).
    center:      (cz, cy, cx) centre of the base in mm.
    base_radius: Radius of the circular base in mm; must be > 0.
    height:      Height from base to apex in mm; must be > 0.
    axis:        Unit vector from base to apex; default = z-axis (1,0,0).
    """

    name: str
    value: int
    center: tuple[float, float, float]
    base_radius: float
    height: float
    axis: tuple[float, float, float] = (1.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        _check_name(self.name)
        _check_value(self.value)
        _check_positive(self.base_radius, "base_radius")
        _check_positive(self.height, "height")


Component = Union[Ellipsoid, Sphere, Cylinder, Cone]


@dataclass
class PhantomSpec:
    """Complete declarative description of a phantom.

    Parameters
    ----------
    name:       Identifier for this phantom (e.g. "head").
    background: uint8 value for voxels not covered by any component (0-255).
    components: Ordered list; later entries have higher rasterization priority.
                Must contain at least one entry; all names must be unique.
    """

    name: str
    background: int
    components: list[Component]

    def __post_init__(self) -> None:
        _check_name(self.name)
        _check_value(self.background, "background")
        if not self.components:
            raise ValueError("components must contain at least one entry")
        seen: set[str] = set()
        for c in self.components:
            if c.name in seen:
                raise ValueError(
                    f"duplicate component name {c.name!r} — all names must be unique"
                )
            seen.add(c.name)
