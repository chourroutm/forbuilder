# Feature Spec: forbuilder CLI

**Feature**: Command-line interface for FORBILD phantom generation
**Branch**: `002-cli` | **Date**: 2026-06-11 | **Plan**: [plan.md](plan.md)

## Summary

Add two console scripts — `forbild-head-gen` and `forbild-thorax-gen` — so users can
generate the FORBILD head and thorax phantoms directly from the terminal. Each script
accepts shape, voxel size, and output path arguments and writes the phantom to disk in
TIFF, NIfTI, or OME-Zarr format (inferred from the file extension). No new phantom logic
is introduced; the scripts are thin wrappers around the existing `forbuilder.generate`
and `forbuilder.save` public API.

## User Stories

### US1 (P1) — Generate a head phantom from the command line

**As a** researcher who has installed `forbuilder`,
**I want to** run `forbild-head-gen --shape 256 256 256 --voxel-size 0.5 --output head.tif`
**so that** I can produce a FORBILD head phantom file without writing Python.

**Acceptance criteria**:
- `forbild-head-gen --shape NZ NY NX --voxel-size V --output PATH` exits 0 and writes a
  non-empty file at PATH.
- `--voxel-size` accepts a single float (isotropic) or three floats `VZ VY VX` (anisotropic).
- `--shape` accepts exactly three positive integers.
- Output format is inferred from PATH extension: `.tif`/`.tiff`, `.nii.gz`, `.ome.zarr`.
- `--help` prints usage and exits 0.
- Invalid inputs (non-positive shape/voxel-size, unsupported extension) exit non-zero and
  print a human-readable error to stderr.

### US2 (P2) — Generate a thorax phantom from the command line

**As a** researcher who has installed `forbuilder`,
**I want to** run `forbild-thorax-gen --shape 512 512 512 --voxel-size 1.0 --output thorax.nii.gz`
**so that** I can produce a FORBILD thorax phantom file without writing Python.

**Acceptance criteria**:
- Identical interface to `forbild-head-gen` but generates the thorax phantom.
- All three output formats (`.tif`/`.tiff`, `.nii.gz`, `.ome.zarr`) are supported.
- Invalid inputs exit non-zero with a descriptive stderr message.
