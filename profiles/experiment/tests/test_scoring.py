"""Tests of the pure scoring functions: known answers, invariants and documented errors."""

from hypothesis import given, strategies as st
import numpy as np
import pytest

from sample_package.scoring import mean_absolute_error, moving_average_forecast, score_window

pytestmark = pytest.mark.unit


def test_the_forecast_of_each_value_is_the_mean_of_the_values_before_it():
    assert moving_average_forecast([1.0, 2.0, 3.0, 4.0, 5.0], 2) == pytest.approx([1.5, 2.5, 3.5])


@pytest.mark.parametrize("window", [0, 5])
def test_a_window_outside_the_series_is_rejected(window):
    with pytest.raises(ValueError, match="window must be between 1 and 4"):
        moving_average_forecast([1.0, 2.0, 3.0, 4.0, 5.0], window)


def test_the_error_of_a_perfect_forecast_is_zero():
    assert mean_absolute_error([1.0, 2.0], [1.0, 2.0]) == 0.0


def test_the_error_is_the_mean_absolute_difference():
    assert mean_absolute_error([0.0, 0.0], [1.0, -3.0]) == pytest.approx(2.0)


def test_shapes_that_differ_are_rejected():
    with pytest.raises(ValueError, match="shapes differ"):
        mean_absolute_error([1.0, 2.0], [1.0])


def test_an_empty_series_cannot_be_scored():
    with pytest.raises(ValueError, match="empty"):
        mean_absolute_error([], [])


def test_a_constant_series_is_forecast_exactly():
    assert score_window(np.full(20, 3.0), 4) == pytest.approx(0.0)


@given(st.lists(st.floats(min_value=-1e3, max_value=1e3, allow_nan=False), min_size=5, max_size=40))
def test_the_error_is_never_negative(values):
    assert score_window(values, 2) >= 0.0
