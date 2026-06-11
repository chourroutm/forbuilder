"""Integration tests for the forbild-head-gen and forbild-thorax-gen CLI entry points."""

from __future__ import annotations

import subprocess
import sys

import pytest


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "forbuilder.cli"] + args,
        capture_output=True,
        text=True,
    )


def _run_ep(entry_point: str, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [entry_point] + args,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# T007: forbild-head-gen happy paths — all three output formats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ext", [".tif", ".nii.gz", ".ome.zarr"])
def test_head_gen_exits_0_and_writes_file(tmp_path, ext):
    out = tmp_path / f"head{ext}"
    result = _run_ep(
        "forbild-head-gen",
        ["--shape", "32", "32", "32", "--voxel-size", "1.0", "--output", str(out)],
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert out.stat().st_size > 0


# ---------------------------------------------------------------------------
# T008: forbild-head-gen error paths — bad args exit non-zero with stderr
# ---------------------------------------------------------------------------


def test_head_gen_zero_shape_exits_nonzero(tmp_path):
    out = tmp_path / "out.tif"
    result = _run_ep(
        "forbild-head-gen",
        ["--shape", "0", "32", "32", "--voxel-size", "1.0", "--output", str(out)],
    )
    assert result.returncode != 0
    assert result.stderr.strip()


def test_head_gen_bad_extension_exits_nonzero(tmp_path):
    out = tmp_path / "out.png"
    result = _run_ep(
        "forbild-head-gen",
        ["--shape", "32", "32", "32", "--voxel-size", "1.0", "--output", str(out)],
    )
    assert result.returncode != 0
    assert result.stderr.strip()


# ---------------------------------------------------------------------------
# T012: forbild-thorax-gen happy paths — all three output formats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ext", [".tif", ".nii.gz", ".ome.zarr"])
def test_thorax_gen_exits_0_and_writes_file(tmp_path, ext):
    out = tmp_path / f"thorax{ext}"
    result = _run_ep(
        "forbild-thorax-gen",
        ["--shape", "32", "32", "32", "--voxel-size", "1.0", "--output", str(out)],
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert out.stat().st_size > 0


# ---------------------------------------------------------------------------
# T013: forbild-thorax-gen error paths
# ---------------------------------------------------------------------------


def test_thorax_gen_zero_shape_exits_nonzero(tmp_path):
    out = tmp_path / "out.tif"
    result = _run_ep(
        "forbild-thorax-gen",
        ["--shape", "0", "32", "32", "--voxel-size", "1.0", "--output", str(out)],
    )
    assert result.returncode != 0
    assert result.stderr.strip()


def test_thorax_gen_bad_extension_exits_nonzero(tmp_path):
    out = tmp_path / "out.png"
    result = _run_ep(
        "forbild-thorax-gen",
        ["--shape", "32", "32", "32", "--voxel-size", "1.0", "--output", str(out)],
    )
    assert result.returncode != 0
    assert result.stderr.strip()
