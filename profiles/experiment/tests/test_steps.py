"""Tests of the command line: the same seed gives the same series, and run writes the table."""

import numpy as np
import pytest

from sample_package.steps import main, make_series

pytestmark = pytest.mark.integration


def test_the_same_seed_gives_the_same_series():
    assert np.array_equal(make_series(3, 50), make_series(3, 50))


def test_run_writes_the_results_and_status_finds_them(tmp_path, capsys):
    output = tmp_path / "scores.csv"
    assert main(["status", "--output", str(output)]) == 0
    assert "not found" in capsys.readouterr().out
    assert main(["run", "--length", "60", "--output", str(output)]) == 0
    assert output.exists()
    assert main(["status", "--output", str(output)]) == 0
    assert "found at" in capsys.readouterr().out
