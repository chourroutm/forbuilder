"""Load a PhantomSpec from a built-in template name or a JSON/YAML geometry file."""

from __future__ import annotations

import copy
import importlib.resources
import json
from pathlib import Path

from forbuilder._logging import logger
from forbuilder.geometry import (
    Component,
    Cone,
    Cylinder,
    Ellipsoid,
    PhantomSpec,
    Sphere,
)

_BUILTIN_TEMPLATES = {"head", "thorax"}


def _component_from_dict(d: dict) -> Component:
    kind = d.get("type", "").lower()
    center = tuple(float(v) for v in d["center"])
    name = d["name"]
    value = int(d["value"])

    if kind == "ellipsoid":
        return Ellipsoid(
            name=name,
            value=value,
            center=center,
            semi_axes=tuple(float(v) for v in d["semi_axes"]),
            euler_angles=tuple(float(v) for v in d.get("euler_angles", [0.0, 0.0, 0.0])),
            z_min=d.get("z_min"),
            z_max=d.get("z_max"),
        )
    if kind == "sphere":
        return Sphere(name=name, value=value, center=center, radius=float(d["radius"]))
    if kind == "cylinder":
        return Cylinder(
            name=name,
            value=value,
            center=center,
            radius=float(d["radius"]),
            half_height=float(d["half_height"]),
            axis=tuple(float(v) for v in d.get("axis", [1.0, 0.0, 0.0])),
        )
    if kind == "cone":
        return Cone(
            name=name,
            value=value,
            center=center,
            base_radius=float(d["base_radius"]),
            height=float(d["height"]),
            axis=tuple(float(v) for v in d.get("axis", [1.0, 0.0, 0.0])),
        )
    raise ValueError(f"Unknown component type {kind!r} for component {name!r}")


def _spec_from_dict(d: dict) -> PhantomSpec:
    components = [_component_from_dict(c) for c in d["components"]]
    return PhantomSpec(
        name=d["name"],
        background=int(d.get("background", 0)),
        components=components,
    )


def load_spec(source: str) -> PhantomSpec:
    """Load a PhantomSpec from a built-in template name or a geometry file path.

    Parameters
    ----------
    source: Built-in template name (``"head"``, ``"thorax"``) or path to a
            ``.json`` / ``.yaml`` / ``.yml`` geometry file.

    Returns
    -------
    PhantomSpec

    Raises
    ------
    ValueError        Unknown template name (not a path, not a known template).
    FileNotFoundError Path does not exist on disk.
    """
    path = Path(source)

    if path.suffix or path.exists():
        return _load_from_file(path)

    if source in _BUILTIN_TEMPLATES:
        return _load_builtin(source)

    available = ", ".join(sorted(_BUILTIN_TEMPLATES))
    raise ValueError(
        f"Unknown template name {source!r}. "
        f"Available built-in templates: {available}"
    )


def _load_builtin(name: str) -> PhantomSpec:
    logger.debug("Loading built-in template %r", name)
    pkg = importlib.resources.files("forbuilder.phantoms")
    data = (pkg / f"{name}.json").read_text(encoding="utf-8")
    return _spec_from_dict(json.loads(data))


def _load_from_file(path: Path) -> PhantomSpec:
    if not path.exists():
        raise FileNotFoundError(f"Geometry file not found: {path}")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _spec_from_dict(_load_yaml(path))
    logger.debug("Loading geometry file %s", path)
    return _spec_from_dict(json.loads(path.read_text(encoding="utf-8")))


def _load_yaml(path: Path) -> dict:
    import importlib.util

    if importlib.util.find_spec("yaml") is None:
        raise ImportError(
            "PyYAML is required for YAML geometry files. "
            "Install it with: pip install forbuilder[yaml]"
        )
    import yaml  # noqa: PLC0415

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def apply_overrides(spec: PhantomSpec, overrides: dict[str, int]) -> PhantomSpec:
    """Return a copy of *spec* with component attenuation values replaced.

    Parameters
    ----------
    spec:      Source PhantomSpec (not modified in place).
    overrides: Mapping of component name to new uint8 value.

    Returns
    -------
    A new PhantomSpec with updated values.

    Raises
    ------
    ValueError If any key does not match a component name, or any value is
               outside [0, 255].
    """
    if not overrides:
        return copy.deepcopy(spec)

    component_names = {c.name for c in spec.components}
    for key, val in overrides.items():
        if key not in component_names:
            raise ValueError(
                f"Override key {key!r} does not match any component name in "
                f"spec {spec.name!r}. Known names: {sorted(component_names)}"
            )
        if not (0 <= val <= 255):
            raise ValueError(
                f"Override value {val} for component {key!r} must be in [0, 255]"
            )

    new_components = []
    for comp in spec.components:
        if comp.name in overrides:
            new_comp = copy.copy(comp)
            new_comp.value = overrides[comp.name]
            new_components.append(new_comp)
        else:
            new_components.append(copy.copy(comp))

    return PhantomSpec(
        name=spec.name,
        background=spec.background,
        components=new_components,
    )
