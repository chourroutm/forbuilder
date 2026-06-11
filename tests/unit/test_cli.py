"""Unit tests for forbuilder.cli — argument parsing and error paths."""

from __future__ import annotations

import pytest

import forbuilder.cli as cli_mod

# ---------------------------------------------------------------------------
# T003: module exports
# ---------------------------------------------------------------------------


def test_head_main_callable():
    assert callable(cli_mod.head_main)


def test_thorax_main_callable():
    assert callable(cli_mod.thorax_main)


# ---------------------------------------------------------------------------
# T005: _build_parser accepts valid arguments
# ---------------------------------------------------------------------------


def test_parser_valid_shape_and_scalar_voxel_size():
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        ["--shape", "256", "256", "256", "--voxel-size", "0.5", "--output", "out.tif"]
    )
    assert args.shape == [256, 256, 256]
    assert args.voxel_size == [0.5]
    assert args.output == "out.tif"


def test_parser_anisotropic_voxel_size():
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        [
            "--shape", "64", "64", "32",
            "--voxel-size", "1.0", "1.0", "2.0",
            "--output", "out.nii.gz",
        ]
    )
    assert args.voxel_size == [1.0, 1.0, 2.0]


def test_parser_ome_zarr_extension():
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        ["--shape", "64", "64", "64", "--voxel-size", "1.0", "--output", "out.ome.zarr"]
    )
    assert args.output == "out.ome.zarr"


# ---------------------------------------------------------------------------
# T006: error paths — invalid inputs raise SystemExit or ValueError
# ---------------------------------------------------------------------------


def test_parser_rejects_non_integer_shape():
    parser = cli_mod._build_parser("forbild-head-gen")
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--shape", "256", "abc", "256", "--voxel-size", "1.0", "--output", "out.tif"]
        )


def test_run_rejects_zero_shape_dim(tmp_path):
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        ["--shape", "0", "64", "64", "--voxel-size", "1.0", "--output", str(tmp_path / "out.tif")]
    )
    with pytest.raises(SystemExit):
        cli_mod._run("head", args)


def test_run_rejects_negative_shape_dim(tmp_path):
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        ["--shape", "64", "-1", "64", "--voxel-size", "1.0", "--output", str(tmp_path / "out.tif")]
    )
    with pytest.raises(SystemExit):
        cli_mod._run("head", args)


def test_run_rejects_non_positive_voxel_size(tmp_path):
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        ["--shape", "64", "64", "64", "--voxel-size", "0.0", "--output", str(tmp_path / "out.tif")]
    )
    with pytest.raises(SystemExit):
        cli_mod._run("head", args)


def test_run_rejects_unsupported_extension(tmp_path):
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        ["--shape", "64", "64", "64", "--voxel-size", "1.0", "--output", str(tmp_path / "out.png")]
    )
    with pytest.raises(SystemExit):
        cli_mod._run("head", args)


def test_run_rejects_wrong_voxel_size_count(tmp_path):
    parser = cli_mod._build_parser("forbild-head-gen")
    args = parser.parse_args(
        [
            "--shape", "64", "64", "64",
            "--voxel-size", "1.0", "2.0",
            "--output", str(tmp_path / "out.tif"),
        ]
    )
    with pytest.raises(SystemExit):
        cli_mod._run("head", args)
