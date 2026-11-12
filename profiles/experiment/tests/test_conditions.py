"""Tests of the declarations: names are unique and the reference exists."""

import pytest

from sample_package.conditions import CONDITIONS, REFERENCE

pytestmark = pytest.mark.unit


def test_condition_names_are_unique():
    names = [condition.name for condition in CONDITIONS]
    assert len(names) == len(set(names))


def test_the_reference_is_one_of_the_conditions():
    assert REFERENCE in {condition.name for condition in CONDITIONS}
