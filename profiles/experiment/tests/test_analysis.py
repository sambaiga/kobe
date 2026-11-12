"""Tests of the I/O layer: the comparison with the reference and the round trip through a file."""

import numpy as np
import pandas as pd
import pytest

from sample_package.analysis import compare, read, write
from sample_package.conditions import REFERENCE, Condition

pytestmark = pytest.mark.integration


def test_the_reference_changes_by_zero_percent():
    frame = compare(np.cumsum(np.ones(50)))
    assert frame.loc[REFERENCE, "change_percent"] == pytest.approx(0.0)


def test_a_missing_reference_is_reported():
    with pytest.raises(ValueError, match="reference condition"):
        compare(np.arange(30.0), (Condition("other", 2),))


def test_a_table_survives_a_round_trip_through_a_file(tmp_path):
    frame = compare(np.cumsum(np.random.default_rng(0).standard_normal(100)))
    write(frame, tmp_path / "nested" / "scores.csv")
    pd.testing.assert_frame_equal(read(tmp_path / "nested" / "scores.csv"), frame, check_exact=False, rtol=1e-12)
