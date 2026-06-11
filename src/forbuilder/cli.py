"""Console-script entry points for FORBILD phantom generation."""

from __future__ import annotations

import argparse
import sys

import forbuilder as fb

_SUPPORTED_EXTENSIONS = (".tif", ".tiff", ".nii.gz", ".ome.zarr")


def _build_parser(prog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Generate a FORBILD phantom and save it to disk.",
    )
    parser.add_argument(
        "--shape",
        nargs=3,
        type=int,
        required=True,
        metavar=("NZ", "NY", "NX"),
        help="Output volume dimensions.",
    )
    parser.add_argument(
        "--voxel-size",
        nargs="+",
        type=float,
        required=True,
        metavar="V",
        help="Voxel size in mm. One value (isotropic) or three values VZ VY VX.",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="PATH",
        help="Destination file (.tif/.tiff, .nii.gz, .ome.zarr).",
    )
    return parser


def _run(template: str, args: argparse.Namespace) -> None:
    shape = tuple(args.shape)
    voxel_size = args.voxel_size

    for i, dim in enumerate(shape):
        if dim <= 0:
            sys.stderr.write(f"error: --shape[{i}] must be > 0, got {dim}\n")
            sys.exit(1)

    if len(voxel_size) not in (1, 3):
        sys.stderr.write(
            f"error: --voxel-size expects 1 or 3 values, got {len(voxel_size)}\n"
        )
        sys.exit(1)

    for v in voxel_size:
        if v <= 0:
            sys.stderr.write(f"error: --voxel-size must be > 0, got {v}\n")
            sys.exit(1)

    out = args.output
    if not any(out.endswith(ext) for ext in _SUPPORTED_EXTENSIONS):
        sys.stderr.write(
            f"error: unsupported output extension for '{out}'. "
            f"Supported: {', '.join(_SUPPORTED_EXTENSIONS)}\n"
        )
        sys.exit(1)

    vs = voxel_size[0] if len(voxel_size) == 1 else tuple(voxel_size)
    sys.stderr.write(f"Generating {template} phantom {shape} @ {vs} mm ...\n")
    phantom = fb.generate(template, shape=shape, voxel_size=vs)
    sys.stderr.write(f"Saving to {out} ...\n")
    fb.save(phantom, out)
    sys.stderr.write("Done.\n")


def head_main() -> None:
    _run("head", _build_parser("forbild-head-gen").parse_args())


def thorax_main() -> None:
    _run("thorax", _build_parser("forbild-thorax-gen").parse_args())
