"""Compare an optimized image with the image built from the original Dockerfile."""

from __future__ import annotations


def size_comparison(
    *,
    optimized_bytes: int | None,
    baseline_bytes: int | None,
    baseline_status: str,
) -> dict:
    """Return the byte and percent change from the original image.

    A negative delta means the optimized image is smaller. Percent is omitted
    when the original image size is zero or the original build did not pass.
    """
    delta: int | None = None
    percent: float | None = None
    if (
        baseline_status == "passed"
        and isinstance(optimized_bytes, int)
        and isinstance(baseline_bytes, int)
        and baseline_bytes >= 0
    ):
        delta = optimized_bytes - baseline_bytes
        if baseline_bytes > 0:
            percent = round(delta / baseline_bytes * 100, 1)
    return {
        "baseline_status": baseline_status,
        "baseline_image_size_bytes": baseline_bytes,
        "optimized_image_size_bytes": optimized_bytes,
        "delta_bytes": delta,
        "delta_percent": percent,
    }
