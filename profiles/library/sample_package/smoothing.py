"""Smoothing of one-dimensional series: the moving average, with no Python loop."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def moving_average(values: ArrayLike, window: int) -> NDArray[np.float64]:
    """Average each run of ``window`` consecutive values.

    The cumulative sum makes the cost linear in the length of the series instead of
    ``len(values) * window``, and a float64 accumulator keeps the rounding error small.

    Args:
        values: One-dimensional series of finite numbers.
        window: Number of values in each average; at least 1 and at most ``len(values)``.

    Returns:
        The ``len(values) - window + 1`` averages, in time order.

    Raises:
        ValueError: If ``values`` is not one-dimensional, or ``window`` is outside ``1..len(values)``.
    """
    series = np.asarray(values, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"values must be one-dimensional, got {series.ndim} dimensions")
    if not 1 <= window <= series.size:
        raise ValueError(f"window must be between 1 and {series.size}, got {window}")
    cumulative = np.cumsum(series)
    cumulative = np.concatenate(([0.0], cumulative))
    return (cumulative[window:] - cumulative[:-window]) / window
