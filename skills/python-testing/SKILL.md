---
name: python-testing
description: How to write meaningful pytest tests for the user's Python repositories, including regression tests for bug fixes, old-versus-new equivalence for refactors, property-based tests, fixtures for Lightning and pandas code, markers, coverage of changed lines and performance or memory budgets. Use when adding a function, fixing a bug, refactoring, reviewing tests, or deciding what to test.
---

# Python testing: tests that fail when the code is wrong

Load [[coding-standards]] first. A test is worth writing when it can fail for a reason that matters. Tests for the repository run with `uv run pytest`; the full suite runs before every commit, with `set -o pipefail`.

## What every change needs

1. **New function or module:** a unit test of its behaviour with the edge cases (empty, one element, NaN, ties, boundary values, wrong input raising the documented error with `pytest.raises(..., match=...)`).
2. **Bug fix:** a test that **fails on the old code and passes on the fix**. Prove it: `git stash push -- <fixed files>`, run the test, expect red, `git stash pop`. A test that passes both ways proves nothing.
3. **Refactor:** an equivalence test or script that runs the old and the new implementation on real saved data and reports the maximum difference (zero when the formulas are identical). Put a small version in the suite with a closed-form or hand-computed reference.
4. **New configuration field or option:** a forwarding test that the value reaches the object that uses it, for every model family that accepts it (a source-level or constructor-level assertion), plus a validation test for the invalid combinations.

## How to write a good test

5. Name the behaviour: `test_a_head_that_crosses_scores_the_same_interval_as_its_sorted_twin`. One behaviour per test; arrange, act, assert.
6. Assert something that can fail. Never `assert x or True`, never only "it ran without error" when a value can be checked. Use `pytest.approx` with an explicit tolerance for floats; never `==` on floats.
7. Parametrise (`@pytest.mark.parametrize`) over cases instead of copying a test; give the ids meaning.
8. Fixtures build the smallest object that shows the behaviour: a 2-layer module, a 32-row frame, a 5-level quantile array. Put shared ones in `conftest.py`; keep tests independent of order and of each other.
9. Determinism: every random draw from `np.random.default_rng(seed)` or a seeded `torch.Generator`; no network, no wall-clock, no files outside `tmp_path`; use `monkeypatch` for environment and module-level settings.
10. Test public behaviour, not private structure; test private helpers only when they carry the logic and have no public path.

## Kinds of test

11. **Property-based** (`hypothesis`) for invariants over many inputs: a score is non-negative, a monotone network is monotone, a rearranged forecast is sorted, a decomposition sums to its total. Constrain strategies (`floats(allow_nan=False, min_value=..., max_value=...)`) and keep examples few in CI.
12. **Golden or snapshot** tests on stored results for the numbers a paper cites; update them deliberately, with the reason in the commit.
13. **Training behaviour** (Lightning): a tiny module and a 2-to-6-epoch `Trainer` on CPU, asserting the learning rates, which weights validation saw, which optimiser stepped. See [[pytorch-lightning-engineering]].
14. **Numerical functions:** known answers, invariants, edge cases, fails-on-old. See [[numerical-correctness]].
15. **Performance and memory budgets** for code that was optimised: a test that the vectorised path agrees with the loop reference and, where it matters, `pytest-benchmark` or `pytest-memray` (`@pytest.mark.limit_memory`) so a regression is caught. Keep these in a marked group that is not in the default fast run. See [[python-performance]].

## Organisation

16. The tests tree mirrors the source tree (`tests/unit/models/nn/core/test_averaging.py` for `twiga/models/nn/core/averaging.py`); markers `unit`, `integration`, `slow` as in `pyproject.toml`; slow tests run in a separate CI job.
17. Coverage is a floor, not a goal: set `--cov-fail-under` per repository, and require coverage of **changed lines** (`diff-cover`) so new code is tested even where old code is not. Doctests (`--doctest-modules`) for examples in docstrings.
18. A flaky test is a bug in the test or the code: find the cause (seed, order, time, thread count); do not retry it into passing.

## Review checklist

1. Does each new test fail on the code it guards (checked by stashing the fix)?
2. Any assertion that cannot fail? Any exact float comparison?
3. Edge cases covered: empty, one, NaN, ties, boundary, invalid input?
4. Seeds fixed, no network or wall-clock, files only in `tmp_path`?
5. Does a refactor carry an equivalence check on real saved data?
6. Is the full suite green, and is changed-line coverage met?
