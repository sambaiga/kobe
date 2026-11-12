"""Pure computation: forecasts and scores from arrays, with no file, plot or print."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def moving_average_forecast(series: ArrayLike, window: int) -> NDArray[np.float64]:
    """Forecast each value as the mean of the ``window`` values before it.

    Args:
        series: One-dimensional series of finite numbers.
        window: Number of past values to average; at least 1 and below ``len(series)``.

    Returns:
        The ``len(series) - window`` forecasts of ``series[window:]``, in time order.

    Raises:
        ValueError: If ``series`` is not one-dimensional or ``window`` is outside ``1..len(series) - 1``.
    """
    values = np.asarray(series, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError(f"series must be one-dimensional, got {values.ndim} dimensions")
    if not 1 <= window < values.size:
        raise ValueError(f"window must be between 1 and {values.size - 1}, got {window}")
    cumulative = np.concatenate(([0.0], np.cumsum(values)))
    return (cumulative[window:-1] - cumulative[: -window - 1]) / window


def mean_absolute_error(actual: ArrayLike, forecast: ArrayLike) -> float:
    """Average absolute difference between observations and forecasts.

    Args:
        actual: Observed values.
        forecast: Forecast values, the same shape as ``actual``.

    Returns:
        The mean absolute error.

    Raises:
        ValueError: If the shapes differ or the input is empty.
    """
    observed, predicted = np.asarray(actual, dtype=np.float64), np.asarray(forecast, dtype=np.float64)
    if observed.shape != predicted.shape:
        raise ValueError(f"shapes differ: {observed.shape} and {predicted.shape}")
    if observed.size == 0:
        raise ValueError("cannot score an empty series")
    return float(np.abs(observed - predicted).mean())


def score_window(series: ArrayLike, window: int) -> float:
    """Score the moving-average forecast of one window length on a series.

    Args:
        series: One-dimensional series of finite numbers.
        window: Number of past values the forecast averages.

    Returns:
        The mean absolute error of the forecasts of ``series[window:]``.
    """
    values = np.asarray(series, dtype=np.float64)
    return mean_absolute_error(values[window:], moving_average_forecast(values, window))
