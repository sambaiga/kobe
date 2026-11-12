---
name: python-performance
description: How to write Python that is fast and light on memory, and to vectorise it, in numpy, pandas, PyTorch and Lightning code. Use when writing or reviewing any computation over arrays, frames, time series, metrics, simulations or training loops, when code is slow or runs out of memory (the user's laptop has 8 GB), or before replacing a loop. Rule one is to profile first.
---

# Python performance: measure, vectorise, then shrink memory

Load [[coding-standards]] first. The order is fixed: **correct, then measured, then fast.** Never optimise on a guess, and never trade correctness for speed (check an optimised version reproduces the old one exactly on real saved data).

## 1. Measure first

- Time: `time.perf_counter` or `timeit` for a snippet, `cProfile` (`python -m cProfile -o out.prof`, read with `snakeviz`) or `py-spy record` for a whole run, `line_profiler` for one hot function.
- Memory: `tracemalloc` for Python allocations, `memray run` (Linux and macOS) for native and numpy allocations, `resource.getrusage(...).ru_maxrss` for the peak. The laptop has 8 GB: budget the peak of a job before running it, and run one heavy job at a time with `OMP_NUM_THREADS=2`.
- Record the number before and after in the PR. A change that gives under 10 % is not worth its complexity.

## 2. Vectorise with numpy

- Replace a Python loop over rows, levels or folds by an array operation. Count with a comparison and a sum, not a loop: the PIT of a forecast is `(quantiles <= observed[None]).sum(axis=0) - 1`, not a loop over observations.
- Use broadcasting (`values[:, None] - levels[None, :]`) and `einsum` for contractions; `np.searchsorted` for many lookups into one sorted array; `np.cumsum`, `np.diff`, `np.maximum` for piecewise-linear and pinball-type formulas (`np.maximum(tau * e, (tau - 1) * e)`).
- Reduce over an axis instead of looping and appending: `np.trapezoid(y, x, axis=1)` (not `np.trapz`), `np.nanmean(x, axis=0)`.
- Windows without copies: `np.lib.stride_tricks.sliding_window_view`. Views are free; `reshape` of a contiguous array is a view, `ravel` may copy, `flatten` always copies.
- Random numbers: `rng = np.random.default_rng(seed)` and draw whole arrays (`rng.standard_normal((draws, n))`), never `np.random.seed` or `np.random.rand`.

## 3. Memory

- Pick the dtype: `float32` halves memory for large arrays when the precision is not needed (keep `float64` for accumulations, CRPS integrals and anything compared against a tolerance). Use `int32` or `uint8` for indices and flags, `bool` for masks.
- Avoid temporaries in long expressions: `np.add(a, b, out=a)` or in-place `+=` when the operand is not needed again; compute in chunks over the largest axis and write into a preallocated array.
- Do not `.copy()` a large frame to be safe. Select columns before the heavy step, not after.
- Large data on disk: Parquet or `.npz` per fold, `np.load(..., mmap_mode="r")`, `pd.read_parquet(columns=[...])`, iterate files and keep only the summary. Delete what you no longer need (`del`) before the next fold.
- Sorting and `argsort` allocate: sort once and reuse the order.

## 4. pandas

- No `iterrows`, `itertuples` loops or row-wise `apply` where a column expression, `groupby(...).transform/agg`, `merge`, `np.where` or `Series.map` exists. Prefer `.to_numpy()` to `.values`; no `inplace=True`; enable copy-on-write (`pd.options.mode.copy_on_write = True`) so chained assignment cannot silently copy or alias.
- Use `category` dtype for repeated labels (dataset, head, seed), Arrow-backed dtypes for strings, `pd.to_datetime` once with a format, and `pivot_table` or `groupby` instead of building frames in a loop and concatenating row by row (collect in a list, `pd.concat` once).
- For data that no longer fits comfortably, move the heavy step to Polars or DuckDB (lazy, columnar) instead of chunking pandas by hand.

## 5. Only after a profile says so

- Numba (`@njit`) for an unavoidable scalar loop with numpy arrays (no pandas inside); JAX or `torch.compile` when the same array program runs many times. Keep the plain Python version as the tested reference and compare outputs.
- Parallelism: `joblib` with `n_jobs=2` on the laptop, more on the server; seed each worker from a spawned `SeedSequence`.

## 6. PyTorch and Lightning

- No Python loop over batch rows, quantile levels or horizons: stack into a tensor and use `torch.where`, `cumsum`, `gather`. Fused optimiser updates use the `foreach` ops (`torch._foreach_add_` and friends: private API, guard it with a test against the plain loop).
- Inference and evaluation under `torch.inference_mode()`; log `.detach()`ed scalars only (a logged tensor with a graph keeps the whole step alive). `optimizer.zero_grad(set_to_none=True)`.
- Speed: `torch.compile` for a stable-shape model, mixed precision (`bf16`) on hardware that supports it, `DataLoader(num_workers=..., persistent_workers=True)` (on macOS workers spawn: keep the dataset picklable), `pin_memory=True` only for CUDA. Memory: gradient accumulation instead of a bigger batch; activation checkpointing for deep models.
- See [[pytorch-lightning-engineering]] for the training-loop pitfalls.

## Review checklist

1. Is there a measurement (time and peak memory) before and after?
2. Any Python loop over rows, levels, folds or horizons that an axis operation replaces?
3. Any needless copy, any `float64` where `float32` is enough, any array built by repeated append?
4. Does the faster version reproduce the old result exactly (maximum difference reported)?
5. Is the plain reference implementation kept as a test oracle?
