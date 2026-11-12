"""Reading, writing and comparing results; the only module that touches files."""

from pathlib import Path

import numpy as np
import pandas as pd

from .conditions import CONDITIONS, REFERENCE, Condition
from .scoring import score_window


def compare(series: np.ndarray, conditions: tuple[Condition, ...] = CONDITIONS) -> pd.DataFrame:
    """Score every condition on one series and compare it with the reference.

    Args:
        series: One-dimensional series of finite numbers.
        conditions: The conditions to score; the reference must be among them.

    Returns:
        One row per condition with its window, mean absolute error and the relative change from the
        reference in percent (negative is better).

    Raises:
        ValueError: If the reference condition is missing from ``conditions``.
    """
    errors = {condition.name: score_window(series, condition.window) for condition in conditions}
    if REFERENCE not in errors:
        raise ValueError(f"the reference condition {REFERENCE!r} is not among the conditions")
    frame = pd.DataFrame(
        {"window": {c.name: c.window for c in conditions}, "mae": errors},
    ).rename_axis("condition")
    frame["change_percent"] = 100 * (frame["mae"] / errors[REFERENCE] - 1)
    return frame


def write(frame: pd.DataFrame, path: Path) -> None:
    """Write a results table as CSV, creating the folder.

    Args:
        frame: The results table.
        path: Destination file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path)


def read(path: Path) -> pd.DataFrame:
    """Read a results table written by :func:`write`.

    Args:
        path: The CSV file.

    Returns:
        The table, indexed by condition.
    """
    return pd.read_csv(path, index_col="condition")
