"""Unit tests for load_spec() and apply_overrides()."""

import json
import pathlib

import pytest

from forbuilder.geometry import PhantomSpec, Sphere
from forbuilder.loader import apply_overrides, load_spec

# ---------------------------------------------------------------------------
# load_spec — built-in templates
# ---------------------------------------------------------------------------


class TestLoadSpecTemplates:
    def test_load_head_returns_phantom_spec(self):
        spec = load_spec("head")
        assert isinstance(spec, PhantomSpec)

    def test_load_head_name(self):
        spec = load_spec("head")
        assert spec.name == "head"

    def test_load_head_has_components(self):
        spec = load_spec("head")
        assert len(spec.components) >= 30

    def test_load_thorax_returns_phantom_spec(self):
        spec = load_spec("thorax")
        assert isinstance(spec, PhantomSpec)

    def test_load_thorax_has_components(self):
        spec = load_spec("thorax")
        assert len(spec.components) >= 10

    def test_unknown_template_raises_value_error(self):
        with pytest.raises(ValueError, match="head_v2"):
            load_spec("head_v2")

    def test_unknown_template_error_lists_available(self):
        with pytest.raises(ValueError, match="head"):
            load_spec("nonexistent_phantom")


# ---------------------------------------------------------------------------
# load_spec — JSON file path
# ---------------------------------------------------------------------------


class TestLoadSpecFromFile:
    def _write_spec(self, tmp_path: pathlib.Path, spec_dict: dict) -> pathlib.Path:
        p = tmp_path / "spec.json"
        p.write_text(json.dumps(spec_dict))
        return p

    def _minimal_spec(self) -> dict:
        return {
            "name": "minimal",
            "background": 0,
            "components": [
                {
                    "name": "sphere_1",
                    "type": "sphere",
                    "value": 200,
                    "center": [0.0, 0.0, 0.0],
                    "radius": 5.0,
                }
            ],
        }

    def test_load_from_json_file(self, tmp_path):
        p = self._write_spec(tmp_path, self._minimal_spec())
        spec = load_spec(str(p))
        assert isinstance(spec, PhantomSpec)
        assert spec.name == "minimal"
        assert len(spec.components) == 1

    def test_load_from_pathlib_path(self, tmp_path):
        p = self._write_spec(tmp_path, self._minimal_spec())
        spec = load_spec(str(p))
        assert spec is not None

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_spec(str(tmp_path / "nonexistent.json"))

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not valid json {{{{")
        with pytest.raises(Exception):
            load_spec(str(p))

    def test_all_component_types_load(self, tmp_path):
        spec_dict = {
            "name": "multi",
            "background": 0,
            "components": [
                {
                    "name": "e1",
                    "type": "ellipsoid",
                    "value": 100,
                    "center": [0, 0, 0],
                    "semi_axes": [1.0, 2.0, 3.0],
                },
                {
                    "name": "s1",
                    "type": "sphere",
                    "value": 150,
                    "center": [0, 0, 0],
                    "radius": 2.0,
                },
                {
                    "name": "cy1",
                    "type": "cylinder",
                    "value": 120,
                    "center": [0, 0, 0],
                    "radius": 1.0,
                    "half_height": 2.0,
                },
                {
                    "name": "co1",
                    "type": "cone",
                    "value": 80,
                    "center": [0, 0, 0],
                    "base_radius": 1.5,
                    "height": 3.0,
                },
            ],
        }
        p = self._write_spec(tmp_path, spec_dict)
        spec = load_spec(str(p))
        assert len(spec.components) == 4


# ---------------------------------------------------------------------------
# apply_overrides
# ---------------------------------------------------------------------------


class TestApplyOverrides:
    def _make_spec(self) -> PhantomSpec:
        return PhantomSpec(
            name="test",
            background=0,
            components=[
                Sphere(name="a", value=100, center=(0, 0, 0), radius=1.0),
                Sphere(name="b", value=150, center=(1, 1, 1), radius=2.0),
            ],
        )

    def test_override_changes_value(self):
        spec = self._make_spec()
        new_spec = apply_overrides(spec, {"a": 200})
        comp = next(c for c in new_spec.components if c.name == "a")
        assert comp.value == 200

    def test_override_does_not_affect_other_components(self):
        spec = self._make_spec()
        new_spec = apply_overrides(spec, {"a": 200})
        comp_b = next(c for c in new_spec.components if c.name == "b")
        assert comp_b.value == 150

    def test_override_returns_copy_not_original(self):
        spec = self._make_spec()
        apply_overrides(spec, {"a": 200})
        original_a = next(c for c in spec.components if c.name == "a")
        assert original_a.value == 100  # original unchanged

    def test_empty_overrides_returns_equivalent_spec(self):
        spec = self._make_spec()
        new_spec = apply_overrides(spec, {})
        assert len(new_spec.components) == len(spec.components)

    def test_unknown_component_name_raises(self):
        spec = self._make_spec()
        with pytest.raises(ValueError, match="xyz"):
            apply_overrides(spec, {"xyz": 100})

    def test_override_value_out_of_range_raises(self):
        spec = self._make_spec()
        with pytest.raises(ValueError, match="256"):
            apply_overrides(spec, {"a": 256})

    def test_override_value_negative_raises(self):
        spec = self._make_spec()
        with pytest.raises(ValueError, match="-1"):
            apply_overrides(spec, {"a": -1})


# ---------------------------------------------------------------------------
# Optional YAML support (T034)
# ---------------------------------------------------------------------------


class TestLoadSpecYaml:
    def test_yaml_file_loads(self, tmp_path):
        yaml_text = (
            "name: simple\n"
            "background: 0\n"
            "components:\n"
            "  - name: ball\n"
            "    type: sphere\n"
            "    value: 200\n"
            "    center: [0.0, 0.0, 0.0]\n"
            "    radius: 50.0\n"
        )
        p = tmp_path / "spec.yaml"
        p.write_text(yaml_text)
        spec = load_spec(str(p))
        assert isinstance(spec, PhantomSpec)
        assert len(spec.components) == 1
        assert spec.components[0].value == 200

    def test_yml_extension_works(self, tmp_path):
        yaml_text = (
            "name: t\nbackground: 0\ncomponents:\n"
            "  - {name: s, type: sphere, value: 100, center: [0,0,0], radius: 10}\n"
        )
        p = tmp_path / "spec.yml"
        p.write_text(yaml_text)
        spec = load_spec(str(p))
        assert spec.name == "t"


# ---------------------------------------------------------------------------
# Unknown component type
# ---------------------------------------------------------------------------


class TestUnknownComponentType:
    def test_unknown_type_raises(self, tmp_path):
        import json as _json

        spec_dict = {
            "name": "bad",
            "background": 0,
            "components": [{"name": "x", "type": "cube", "value": 100, "center": [0, 0, 0]}],
        }
        p = tmp_path / "bad.json"
        p.write_text(_json.dumps(spec_dict))
        with pytest.raises(ValueError, match="cube"):
            load_spec(str(p))
