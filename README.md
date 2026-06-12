# forbuilder

Create FORBILD digital phantom volumes as 3-D uint8 arrays.

## Installation

```bash
pip install forbuilder
```

Dependencies pulled in automatically: `numpy`, `tifffile`, `nibabel`, `zarr`, `ome-zarr-models`.
OME-Zarr output is validated against the [OME-NGFF 0.5 spec](https://ngff.openmicroscopy.org/0.5/) via `ome-zarr-models`.

## Usage

```python
import forbuilder as fb

# Generate a 256³ head phantom at 0.5 mm isotropic resolution
phantom = fb.generate("head", shape=(256, 256, 256), voxel_size=0.5)

# The result is a named tuple with a uint8 NumPy array and voxel size
print(phantom.array.shape)   # (256, 256, 256)
print(phantom.array.dtype)   # uint8

# Extract a single axial slice (zero-based index)
slice_2d = fb.get_slice(phantom, axis="axial", index=128)
print(slice_2d.shape)        # (256, 256)

# Save to disk — format is inferred from the extension
fb.save(phantom, "head.tif")       # multi-page TIFF
fb.save(phantom, "head.nii.gz")    # NIfTI-1 compressed
fb.save(phantom, "head.nii")       # NIfTI-1 uncompressed
fb.save(phantom, "head.ome.zarr")  # OME-Zarr v0.5

# Load a previously saved phantom (TIFF, NIfTI, or OME-Zarr)
phantom2 = fb.load("head.tif")
phantom3 = fb.load("head.nii.gz")
phantom4 = fb.load("head.nii")
phantom5 = fb.load("head.ome.zarr")

# Override a component's grey value before rasterizing
phantom_custom = fb.generate(
    "head",
    shape=(256, 256, 256),
    voxel_size=0.5,
    overrides={"grey_matter": 180},
)
```

Built-in templates: `"head"`, `"thorax"`. A path to a `.json` or `.yaml` geometry file can be used in place of a template name.

## Command-line interface

Two console scripts are provided for generating phantoms without writing Python.

### `forbild-head-gen`

```bash
# Isotropic voxel size
forbild-head-gen --shape 256 256 256 --voxel-size 0.5 --output head.tif

# Anisotropic voxel size (Z Y X order)
forbild-head-gen --shape 128 256 256 --voxel-size 1.0 0.5 0.5 --output head.nii.gz

# OME-Zarr output
forbild-head-gen --shape 256 256 256 --voxel-size 0.5 --output head.ome.zarr
```

### `forbild-thorax-gen`

```bash
forbild-thorax-gen --shape 256 256 256 --voxel-size 0.5 --output thorax.tif
forbild-thorax-gen --shape 128 256 256 --voxel-size 1.0 0.5 0.5 --output thorax.nii.gz
forbild-thorax-gen --shape 256 256 256 --voxel-size 0.5 --output thorax.ome.zarr
```

**Options** (same for both commands):

| Flag | Required | Description |
|------|----------|-------------|
| `--shape NZ NY NX` | yes | Output volume dimensions |
| `--voxel-size V` or `--voxel-size VZ VY VX` | yes | Voxel size in mm (isotropic or anisotropic) |
| `--output PATH` | yes | Destination file (`.tif`/`.tiff`, `.nii`, `.nii.gz`, `.ome.zarr`) |
