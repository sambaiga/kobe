---
name: numerical-correctness
description: Rules for numerically and statistically correct code: floating-point comparison, stable formulas, aggregation, edge cases, scoring rules and metrics, and how to test them. Use when writing or reviewing a metric, score, interval, quantile, probability, statistical test or any formula, and when a result looks too good, too clean or sensitive to the input order. It records the metric bugs found in twiga PR 134 and 135.
---

# Numerical correctness: the checks that catch silent wrong answers

Load [[coding-standards]] first. A wrong number that looks reasonable is worse than a crash. Each rule below matches a defect that was found in this work.

## Floating point

1. **Never compare floats exactly.** `1.0 - 0.18` is `0.8200000000000001`, so `1 - tau <= levels[-1]` dropped a symmetric outer pair from the weighted interval score. Use `np.isclose`, `math.isclose` or an explicit tolerance named `tolerance`, and clip a computed level into the grid's range before using it.
2. **Stable formulas:** `np.log1p`, `np.expm1`, `scipy.special.logsumexp`, `softmax` with the maximum subtracted, `np.hypot`. Use survival functions for tail probabilities (`scipy.stats.chi2.sf`, `norm.sf`), not `1 - cdf`, which collapses to exactly 0 for large statistics and hides the p-value.
3. **Clip probabilities** to `[eps, 1 - eps]` before an inverse CDF so a level at 0 or 1 stays finite, and say what `eps` is.
4. **dtype:** accumulate in `float64`; check integer division and integer overflow in counts.

## Aggregation

5. **Ratio of sums, not mean of ratios,** for a normalised score such as the weighted quantile loss: `sum(loss) / sum(abs(y))`. A mean of per-series ratios was too small by the series length.
6. **Aggregate in the right unit.** For time series the unit of a significance test is the forecast day, not the hour; average within the unit first, then test across units.
7. **Mean, not median,** when averaging a proper score over points: the median of per-point interval scores is minimised by a badly over-confident forecast (a Winkler score reduced by the median does not stay proper).
8. **Integrals over a grid undercount what lies outside it.** A CRPS integrated over 1 % to 99 % leaves out the two outer 1 % tails and can only be lower than the closed form: say so in the docstring and compare scores only on the same grid.

## Edge cases to handle and test

9. Empty input, a single element, one fold, all-NaN slices (`np.nanmean` warns and returns NaN: decide what the caller gets), ties, constant series, a level at 0 or 1, and **crossing quantiles**. Crossing makes a lower bound exceed an upper bound and inverts interval metrics; rearrange (sort) at fixed levels before any interval, PIT or coverage score (Chernozhukov, Fernandez-Val and Galichon, 2010).
10. A function that needs two or more levels must say so and raise `ValueError`, not return 0 (a single level integrated to 0).
11. NaN must not vanish silently: a pivot or `groupby` that drops NaN columns removed a candidate from a comparison and raised a `KeyError` far from the cause.

## Scoring rules and statistics

12. Use **proper** scores for forecasts (pinball and CRPS for quantiles, interval score for intervals); do not decide a calibration claim with a score that is flat near the optimum. State what each metric can and cannot diagnose.
13. Serial correlation: Diebold-Mariano needs a bandwidth (state it); correct for multiple comparisons (Benjamini-Hochberg); read the effect size next to the p-value.
14. Reference values: compare against a closed form where one exists (the Gaussian CRPS), against a trivial forecast, and against the previous implementation on stored data.

## How to test a numerical function

15. **Known answers:** a closed form, a hand-computed value, the perfect forecast scoring zero or the minimum.
16. **Invariants:** non-negativity, symmetry, monotonicity in the right direction, scale and shift behaviour, `score(sorted) == score(reversed)` for rearranged inputs, the parts of a decomposition summing to the whole.
17. **Property tests** with `hypothesis` for invariants over random inputs; fix the seed of anything else.
18. **A regression test that fails on the old behaviour** (stash the fix and confirm). Never an assertion that cannot fail, such as `or True`.
19. **Refactor equivalence:** old against new on real saved data, report the maximum relative difference, and expect 0 where the formulas are identical.

## Review checklist

1. Any `==` on floats, any `1 - cdf`, any `log(1 + x)`?
2. Mean of ratios where a ratio of sums is meant? Median where a mean keeps the score proper?
3. What happens on empty, single, NaN, tied and crossing inputs?
4. Is the grid or truncation stated, and are scores compared only on the same grid?
5. Is there a closed-form, an invariant and a fails-on-old test?
