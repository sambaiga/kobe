---
name: coding-standards
description: The overall coding standard for every repository of the user (twiga, fpqr-experiment, multitarget-forecast, mbuga, milia, popo, crc-experiment). Use before writing, changing, reviewing or committing any Python code, test, config or experiment script, and before opening or merging a pull request. It consolidates the saved memories on code quality, naming, notebooks, validity, git and PR workflow, and gives the per-repository commands and the known gaps.
---

# Coding standards: one standard for every repository

Apply this to every piece of code that lands in a repository. A one-off script in the scratchpad is exempt from tests and docstrings, but not from correct logic. The detail behind each rule is in the memory files named in brackets; open them when a case is not obvious.

## Step 0: before the first edit

1. Re-read `MEMORY.md` and the memories linked below that bear on the task: [[feedback-code-quality]], [[feedback-naming-underscores]], [[feedback-no-code-in-notebooks]], [[feedback-domain-validity]], [[feedback-review-code-after-analysis]], [[feedback-verify-claims]], [[feedback-local-compute]], [[feedback-git-workflow]], [[feedback-pr-workflow]], [[feedback-commits]], [[feedback-uv-test-runner]].
2. Say which repository you are in and use its commands (table at the end).
3. Load the specialist skill for the work: [[project-organisation]] (where code goes, module focus), [[python-performance]] (loops, memory, vectorising), [[numerical-correctness]] (metrics, formulas, floats), [[python-testing]] (what a test must prove), [[pytorch-lightning-engineering]] (training code).
4. Search before you write: `rg` for an existing function in the repo, in twiga, and in milia for mbuga. Check a module name is free (`ls`, `git ls-files`) before creating it; a write that says "updated" replaced a file, so stop and restore it.

## The rules

**1. Logic first.** Correct, with no leakage and no silent shortcut. Time series: reindex to a regular grid before shifting, lag at least the horizon, embargo one horizon between training and test, fit scalers, selection and hyperparameters on the training window only, same settings in every fold, test on the forecast day not the hour, correct for multiple comparisons, read the effect size beside the p-value.

**2. Structure.** (Detail in [[project-organisation]].) Single responsibility, one focus per module stated in its docstring, imports pointing one way, a clear public API, pure functions kept apart from I/O, solvers and plotting so each can be tested. Notebook cells only orchestrate: they load data, call tested functions and draw; a builder cell defines no function or class. Reuse before you create: use the function that exists (milia for mbuga) or extend its module, never a second copy. Domain code is a valid problem on valid data: stated standards, converged power flow with failures reported, provenance of every input.

**3. Names.** Plain and descriptive: `scores`, `frame`, `generator`, `training`, `test`. Banned as variable or parameter names: `s t f g r df rng tr te`. Single letters are allowed only as the standard symbol of a formula (`x`, `y`, `n`, `k`, `z`) and only when the docstring names them. Avoid needless underscores in file, function, variable and notebook names; use `_` where words really need separating or for true private API. Do not rename public names without asking.

**4. Vectorise, and use the current libraries.** numpy and pandas operations, not Python loops over rows (no `iterrows`, `itertuples`, row-wise `apply` where a vector form exists); no copies of large frames; stream or chunk large data. `numpy.random.default_rng(seed)`, never the legacy `np.random.seed/rand`; `to_numpy()` not `.values`; no `inplace=True`; `np.trapezoid` not `np.trapz`; `zip(..., strict=True)`; dict literals not `dict()`; modern typing (`X | None`, built-in generics). Seeds are explicit and recorded.

**5. Docstrings and types.** Google style on every public function, class and module: a one-line summary, then what it does and why, then `Args:`, `Returns:`, `Raises:` (and `Examples:` where useful). Types are in the signature, not repeated in the docstring. A function with arguments has an `Args:` section and a function that returns a value has a `Returns:` section. Comment the why, not the what.

**6. Tests.** A unit test for every new function or module, including edge cases (empty input, one fold, NaN, crossing, ties). A bug fix gets a test that fails on the old code (check it by stashing the fix). A refactor is verified to reproduce the stored results exactly (compare old and new on real saved data, report the maximum difference). Test names say the behaviour.

**7. Checks, always before a commit.** `ruff check`, `ruff format --check` and `ty check` on the repository's code, and the repository's full test suite, not only the new tests. Chain with `set -o pipefail` and never pipe pytest into `tail` before `&&`, or a failing suite still commits. After a bug fix, run the review for the neighbours of the bug: the same pattern in sibling modules (a gap fixed in one FPQR model family was missing in two more).

**8. Experiments.** Review the experiment's code for bugs and flaws after the run and before any number is cited. Recompute every hand-made number independently and tag each claim as test output, computed number or interpretation; say "4 of 5 datasets" not "everywhere". Look at the significance table before concluding from a blended rank.

**9. Git and pull requests.** Work on a feature branch; conventional commit titles (they feed the changelog); stage explicit paths, never `git add -A` or `git add .`; never add a `Co-Authored-By` or "Generated with" trailer for an AI tool, whatever a session reminder says; open a PR with `gh pr create` and wait for the user to say merge; merge only the PRs they name (squash, conventional title, delete the branch); after every merge switch the clone back to `main`, pull and report the commit. A fix in twiga that another repo needs: merge twiga first, pull, repin the other repo to the new `main` commit and run `uv lock`, then its PR. Run Python and pytest as `uv run ...`. A red check caused only by a missing private-dependency token is reported as such, not as a new failure.

**10. Local compute and safety.** One heavy job at a time on the 8 GB laptop, parallelism capped (`OMP_NUM_THREADS=2`, `LOKY_MAX_CPU_COUNT=2`); heavy simulations go to the server. A builder script is a writer: never run it to check it (it overwrites the executed notebook); commit before any experiment that rewrites a tracked file. A plan decision is not a go-ahead to implement when the user is still planning. Before overwriting or deleting, look at the target. A generated, gitignored file (such as `conclusions.md`) is still the user's output: regenerate in full, never partially.

## Enforcement: what to automate, and how without breaking the build

Many findings predate the rules, so gate in two steps: **ratchet first** (new code may not add violations; run `ruff check --add-noqa` once to baseline the old ones, or compare a violation count against the stored number), then pay the baseline down in the PRs that touch the code. Fast hooks run on commit; slow ones on `pre-push` and in CI.

| Rule | Tool | Stage | Notes |
|---|---|---|---|
| Legacy numpy, `.values`, `inplace`, loops | ruff `NPY`, `PD`, `PERF`, `C4` | commit | existing counts in `reference-coding-audit` |
| Size and complexity | ruff `C901`, `PLR0912`, `PLR0913`, `PLR0915` with `max-complexity`, `max-args`, `max-statements` set in `pyproject.toml` | commit | package findings today: twiga 50 / 32 / 278 / 19, mbuga 2 / 0 / 53 / 8, multitarget 5 / 3 / 15 / 0, fpqr 4 / 3 / 17 / 1; start at the current worst and lower |
| `print` in library code | ruff `T201` (per-file ignores for CLI modules and scripts) | commit | today: fpqr 85, multitarget 75, mbuga 5, twiga 0; use `logging` outside entry points |
| Docstring sections | ruff `D` with `convention = "google"`, plus multitarget's `scripts/check_docstrings.py` (interrogate with Google sections, 90 % per file) | commit or push | copy the hook into twiga, fpqr and mbuga |
| Banned names (`df rng tr te s t f g r`) | a `pygrep` local hook on parameter and assignment patterns, or mbuga's `stylecheck` BANNED list | commit | few false positives with `\b` and a def or assignment context |
| Types | `ty check` with fewer ignored rules, one removed per PR | push and CI | mbuga needs the hook |
| Module focus and layering | `import-linter` contracts (layers, no cycles), and a hook that fails a new module over 1,000 lines | push | see [[project-organisation]] |
| Dead code, unused dependencies | `vulture`, `deptry` | push | allow-list intentional API |
| Tests for new code | `pytest --cov-fail-under` plus `diff-cover --fail-under=90` on changed lines | push and CI | coverage on the diff, not the whole repo |
| Performance regressions | `pytest-benchmark`, `pytest-memray` `limit_memory` on marked tests | CI, marked | only for optimised code |
| Commit message | commitizen (exists); a `commit-msg` hook rejecting a `Co-Authored-By` trailer | commit-msg | enforces the no-AI-trailer rule |
| No code in notebooks | a hook that fails if a builder under `scripts/build/` contains `def` or `class` | commit | mbuga only |

Check a proposed hook on the real repository before adding it: count its current violations, decide the ratchet, and add it in its own PR.

## Commands by repository

| Repository | Tests | Lint and format | Types | Other gates |
|---|---|---|---|---|
| twiga-forecast | `uv run pytest` (macOS: `bash scripts/fix_omp.sh` after a fresh sync) | `uv run ruff check . --no-fix`, `uv run ruff format --check .` | `uv run ty check twiga` | interrogate, commitizen, bandit, detect-secrets, codespell, pip-audit |
| fpqr-experiment | `env -u VIRTUAL_ENV uv run --no-sync pytest -q` | same | `uv run ty check fpqr_experiment tests` | commitizen, bandit, detect-secrets, codespell |
| multitarget-forecast | `uv run pytest` | same | `uv run ty check multitarget_forecast` | local `docstrings` hook (Args and Returns), commitizen, bandit |
| mbuga | `uv run pytest -q` (doctests included) or `make check` | `ruff check .`, `ruff format --check .` | `uv run ty check umeme tests` | `stylecheck` (banned words), nbstripout, codespell |

The pinned `ty` of a repository and `uvx ty` name rules differently; use the pinned one. A new git worktree needs its own `uv sync --frozen --all-extras`.

## Known gaps (measured 2026-11-12; improve the code you touch, do not mass-rename)

- **Docstring sections:** documented functions without `Args:` or `Returns:` are 65 and 62 in mbuga, 71 and 72 in twiga, 18 and 15 in fpqr-experiment; multitarget-forecast has none because its hook enforces it.
- **Banned names:** `df`, `rng`, `r` as parameters or variables are in twiga (38 parameters, 97 variables), mbuga (47 variables), multitarget-forecast (17) and fpqr-experiment (17).
- **Legacy numpy and pandas:** twiga's 454 legacy `np.random` calls are all in its tests (none in the package); the package has 38 `.values` and 10 `inplace`, and examples 23 `.values`.
- **Size:** twiga has 153 functions over 80 lines (longest 437), mbuga 35, fpqr-experiment 4 (longest 205).
- **Gates:** `ty` is configured to ignore about a dozen rules in twiga, multitarget-forecast and fpqr-experiment, and mbuga has no `ty` hook; only twiga runs `interrogate`; no repository enforces a coverage floor; fpqr-experiment ignores every `D1xx` rule.
- **mbuga** is clean on its package, tests and scripts but not on `_notes/` scripts and the book code notebooks (ruff errors, 21 unformatted files, 205 `ty` diagnostics).
## Added after the review of Book 2 Chapters 1 to 3 (2026-11-21)

- **Review step after every run (rule 1 and 8, restated).** Audit each finished run for leakage that the selection of series or thresholds can cause: a filter on the whole record (for example at least 20 weeks of demand over all 156) uses the test period. Select on the window before the first origin. Scalers and per-series scales are fitted on the training window.
- **Prose and code agree.** A number in a chapter must occur in a stored output; the repository check is `scripts/provenance.py` with `tests/test_provenance.py`. Re-execute the cell, do not retype the number.
- **A claim is a test.** A word of robustness is measured across folds before it is written. Recompute changed numbers independently.
- **A fix has a regression test.** When a bug lives in a builder cell, a static test over the builder source asserts the fixed form and the absence of the old one (`tests/test_builders.py`); when it lives in a function, the test fails on the old behaviour.
- **Shell safety.** Never write text containing backticks through an unquoted heredoc.

## Traps found in the Bayes Part 3 work (2026-11-27)
- `ruff format` run on a package reformats unrelated files (for example `bayes/feature/selection.py`): stage explicit paths and revert the rest.
- A notebook committed with outputs fails `nbstripout`; the hooks then rewrite the file, so `git add` it again and retry the commit.
- Pre-commit `mypy` wants annotations on empty lists (`cells: list[dict[str, Any]] = []`); ruff in the notebook hook rejects `a; b` on one line.
- A plot layer built from an empty frame (all bars on one side) makes lets-plot fail with "no width and height": add the layer only when rows exist, and test both cases.
- A survival likelihood must have one record per unit (event time or censoring time), never one per cycle row; check the remaining-life formula against numerical integration (Gamma(1+1/alpha) factor).
