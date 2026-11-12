"""Tests of the moving average: known answers, invariants and the documented errors."""

from hypothesis import given, strategies as st
import numpy as np
import pytest

from sample_package import moving_average

pytestmark = pytest.mark.unit


def test_a_window_of_three_averages_each_run_of_three_values():
    assert moving_average([1, 2, 3, 4, 5], 3) == pytest.approx([2.0, 3.0, 4.0])


def test_a_window_of_one_returns_the_series():
    assert moving_average([4.0, -1.0, 2.5], 1) == pytest.approx([4.0, -1.0, 2.5])


def test_a_window_as_long_as_the_series_returns_its_mean():
    assert moving_average([1.0, 2.0, 6.0], 3) == pytest.approx([3.0])


@pytest.mark.parametrize("window", [0, -1, 4])
def test_a_window_outside_the_series_is_rejected(window):
    with pytest.raises(ValueError, match="window must be between 1 and 3"):
        moving_average([1.0, 2.0, 3.0], window)


def test_a_two_dimensional_input_is_rejected():
    with pytest.raises(ValueError, match="one-dimensional"):
        moving_average(np.ones((2, 2)), 1)


@given(
    values=st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False), min_size=1, max_size=50),
    data=st.data(),
)
def test_every_average_lies_between_the_smallest_and_largest_value(values, data):
    window = data.draw(st.integers(min_value=1, max_value=len(values)))
    averages = moving_average(values, window)
    assert len(averages) == len(values) - window + 1
    tolerance = 1e-6 * max(1.0, max(abs(v) for v in values))
    assert averages.min() >= min(values) - tolerance
    assert averages.max() <= max(values) + tolerance
