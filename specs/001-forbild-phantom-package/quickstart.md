# Quickstart Validation Guide: FORBILD Phantom Package

**Feature**: `001-forbild-phantom-package`
**Date**: 2026-06-10

This guide describes how to validate that the package works end-to-end after implementation.
It is a runnable verification checklist, not a tutorial.

---

## Prerequisites

```bash
# Install the package with all optional extras
pip install -e ".[dev,yaml]"

# Verify installation
python -c "import forbuilder; print(forbuilder.__version__)"
```

---

## Validation 1: Generate the FORBILD head phantom (P1 — core)

```python
import forbuilder as fb
import numpy as np

phantom = fb.generate("head", shape=(256, 256, 256), voxel_size=0.5)

# Shape and dtype checks
assert phantom.array.shape == (256, 256, 256)
assert phantom.array.dtype == np.uint8
assert phantom.voxel_size == (0.5, 0.5, 0.5)
assert phantom.spec.name == "head"

# Value range — must contain at least background + at least one tissue value
assert phantom.array.min() >= 0
assert phantom.array.max() <= 255
assert len(np.unique(phantom.array)) > 1

print("Validation 1 PASSED")
```

**Expected outcome**: No assertion errors; unique value count ≥ 10 for the head phantom.

---

## Validation 2: Determinism

```python
phantom_a = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)
phantom_b = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)

assert np.array_equal(phantom_a.array, phantom_b.array), "Outputs are not identical"
print("Validation 2 PASSED")
```

---

## Validation 3: Anisotropic voxel size

```python
phantom = fb.generate("head", shape=(128, 256, 256), voxel_size=(2.0, 1.0, 1.0))
assert phantom.shape == (128, 256, 256)
assert phantom.voxel_size == (2.0, 1.0, 1.0)
print("Validation 3 PASSED")
```

---

## Validation 4: Component override

```python
components_default = fb.get_components("head")
outer_default = next(c for c in components_default if c.name == "outer_skull")

phantom_modified = fb.generate(
    "head", shape=(64, 64, 64), voxel_size=1.0, overrides={"outer_skull": 100}
)
phantom_default  = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)

# Verify override actually changed some voxels
assert not np.array_equal(phantom_modified.array, phantom_default.array)
print("Validation 4 PASSED")
```

---

## Validation 5: Inspect components (P2)

```python
components = fb.get_components("head")

assert len(components) >= 30, f"Expected ≥30 components, got {len(components)}"

for c in components:
    assert hasattr(c, "name")
    assert hasattr(c, "value")
    assert 0 <= c.value <= 255

print(f"Validation 5 PASSED — {len(components)} components found")
```

---

## Validation 6: Slice extraction without full volume (P3)

```python
import sys

# Measure memory: slice only should not require full 3D allocation
axial = fb.get_slice("head", "axial", 128, shape=(256, 256, 256), voxel_size=0.5)
assert axial.shape == (256, 256)
assert axial.dtype == np.uint8

coronal = fb.get_slice("head", "coronal", 64, shape=(256, 256, 256), voxel_size=0.5)
assert coronal.shape == (256, 256)

sagittal = fb.get_slice("head", "sagittal", 64, shape=(256, 256, 256), voxel_size=0.5)
assert sagittal.shape == (256, 256)

print("Validation 6 PASSED")
```

---

## Validation 7: Input validation errors

```python
import pytest

# Negative dimension
with pytest.raises(ValueError, match="shape"):
    fb.generate("head", shape=(-1, 256, 256), voxel_size=1.0)

# Zero voxel size
with pytest.raises(ValueError, match="voxel_size"):
    fb.generate("head", shape=(64, 64, 64), voxel_size=0.0)

# Unknown template
with pytest.raises(ValueError, match="head_v2"):
    fb.generate("head_v2", shape=(64, 64, 64), voxel_size=1.0)

# Override out of range
with pytest.raises(ValueError, match="256"):
    fb.generate("head", shape=(64, 64, 64), voxel_size=1.0, overrides={"outer_skull": 256})

# Slice out of bounds
phantom = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)
with pytest.raises(ValueError, match="index"):
    fb.get_slice(phantom, "axial", 999)

print("Validation 7 PASSED")
```

---

## Validation 8: Save to TIFF

```python
import tempfile, pathlib

phantom = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)

with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / "head.tif"
    fb.save(phantom, path)
    assert path.exists()
    assert path.stat().st_size > 0
    print(f"TIFF written: {path.stat().st_size} bytes")

print("Validation 8 PASSED")
```

---

## Validation 9: Save to NIfTI

```python
import tempfile, pathlib

phantom = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)

with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / "head.nii.gz"
    fb.save(phantom, path)
    assert path.exists()
    assert path.stat().st_size > 0
    print(f"NIfTI written: {path.stat().st_size} bytes")

print("Validation 9 PASSED")
```

---

## Validation 10: Save to OME-Zarr v0.5

```python
import tempfile, pathlib, json
import zarr

phantom = fb.generate("head", shape=(64, 64, 64), voxel_size=1.0)

with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp) / "head.ome.zarr"
    fb.save(phantom, path)

    # Verify Zarr v3 format and OME-NGFF 0.5 metadata
    store = zarr.open_group(str(path), mode="r")
    assert "ome" in store.attrs
    meta = store.attrs["ome"]
    assert "multiscales" in meta
    ms = meta["multiscales"][0]
    assert ms["version"] == "0.5"
    assert len(ms["axes"]) == 3
    assert ms["axes"][0]["unit"] == "millimeter"

    # Verify array exists and matches
    arr = store["0"]
    assert arr.shape == (64, 64, 64)

print("Validation 10 PASSED")
```

---

## Validation 11: Load from custom JSON geometry file

```python
import tempfile, pathlib, json

custom_spec = {
    "name": "simple_sphere",
    "background": 0,
    "components": [
        {
            "name": "sphere_1",
            "type": "sphere",
            "value": 200,
            "center": [0.0, 0.0, 0.0],
            "radius": 5.0
        }
    ]
}

with tempfile.TemporaryDirectory() as tmp:
    spec_path = pathlib.Path(tmp) / "simple.json"
    spec_path.write_text(json.dumps(custom_spec))

    phantom = fb.generate(str(spec_path), shape=(32, 32, 32), voxel_size=0.5)
    assert phantom.spec.name == "simple_sphere"
    assert 200 in phantom.array  # sphere voxels should be present
    print(f"Custom phantom: {phantom.array.shape}, values: {set(phantom.array.flatten())}")

print("Validation 11 PASSED")
```

---

## Validation 12: FORBILD thorax phantom

```python
phantom = fb.generate("thorax", shape=(128, 128, 64), voxel_size=2.0)
assert phantom.array.shape == (128, 128, 64)
assert len(fb.get_components("thorax")) >= 20

print("Validation 12 PASSED")
```

---

## Full run

```bash
# Run all accuracy tests (including tolerance check against reference data)
pytest tests/accuracy/ -v

# Run integration tests
pytest tests/integration/ -v

# Run benchmarks (informational)
pytest tests/benchmarks/ -v --benchmark-only
```

**Expected**: All accuracy tests pass with max absolute error ≤ 1 grayscale unit vs.
FORBILD reference data. All integration tests green. Benchmark results printed to stdout.
