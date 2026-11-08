"""Tests for optimized-versus-original image size comparison."""

from app.evaluators.size_delta import size_comparison


def test_smaller_image_is_a_negative_delta():
    result = size_comparison(
        optimized_bytes=180_000_000,
        baseline_bytes=900_000_000,
        baseline_status="passed",
    )
    assert result["delta_bytes"] == -720_000_000
    assert result["delta_percent"] == -80.0


def test_larger_image_is_a_positive_delta():
    result = size_comparison(
        optimized_bytes=120,
        baseline_bytes=100,
        baseline_status="passed",
    )
    assert result["delta_bytes"] == 20
    assert result["delta_percent"] == 20.0


def test_failed_baseline_has_no_delta():
    result = size_comparison(
        optimized_bytes=180_000_000,
        baseline_bytes=None,
        baseline_status="failed",
    )
    assert result["delta_bytes"] is None
    assert result["delta_percent"] is None
    assert result["baseline_status"] == "failed"


def test_zero_baseline_omits_percent():
    result = size_comparison(
        optimized_bytes=10,
        baseline_bytes=0,
        baseline_status="passed",
    )
    assert result["delta_bytes"] == 10
    assert result["delta_percent"] is None
