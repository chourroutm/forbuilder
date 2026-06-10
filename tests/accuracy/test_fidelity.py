"""Numerical accuracy tests — output must match reference data within tolerance."""

import pathlib

import numpy as np
import pytest

import forbuilder as fb

REFERENCE_DIR = pathlib.Path(__file__).parent / "reference"
TOLERANCE = 1  # max absolute error in grayscale units (constitution Principle III)


def _reference_path(name: str) -> pathlib.Path:
    return REFERENCE_DIR / f"{name}.npy"


def _save_reference(name: str, array: np.ndarray) -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(_reference_path(name), array)


# Generate reference arrays if they don't exist yet (run once, then committed)
@pytest.fixture(scope="session", autouse=True)
def generate_references():
    """Generate reference arrays on first run if not present."""
    if not _reference_path("head_32_voxel1").exists():
        p = fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)
        _save_reference("head_32_voxel1", p.array)
    if not _reference_path("head_16_voxel2").exists():
        p = fb.generate("head", shape=(16, 16, 16), voxel_size=2.0)
        _save_reference("head_16_voxel2", p.array)


class TestHeadPhantomFidelity:
    def test_head_32_matches_reference(self):
        ref = np.load(_reference_path("head_32_voxel1"))
        p = fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)
        max_err = int(np.max(np.abs(p.array.astype(int) - ref.astype(int))))
        assert max_err <= TOLERANCE, (
            f"Max absolute error {max_err} exceeds tolerance {TOLERANCE}"
        )

    def test_head_16_matches_reference(self):
        ref = np.load(_reference_path("head_16_voxel2"))
        p = fb.generate("head", shape=(16, 16, 16), voxel_size=2.0)
        max_err = int(np.max(np.abs(p.array.astype(int) - ref.astype(int))))
        assert max_err <= TOLERANCE, (
            f"Max absolute error {max_err} exceeds tolerance {TOLERANCE}"
        )

    def test_head_output_range_valid(self):
        p = fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)
        assert p.array.min() >= 0
        assert p.array.max() <= 255

    def test_head_has_multiple_tissue_values(self):
        p = fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)
        unique_values = len(np.unique(p.array))
        assert unique_values >= 5, (
            f"Expected ≥5 unique tissue values, got {unique_values}"
        )

    def test_head_background_present(self):
        """Background (0) should appear outside the skull at default resolution."""
        p = fb.generate("head", shape=(32, 32, 32), voxel_size=1.0)
        assert 0 in p.array
