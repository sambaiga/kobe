# sample-project

Read this first. The full standard is the `coding-standards` skill (and the specialist skills it names); this file
is the short version for a session that does not load them.

## Commands

| Task | Command |
|---|---|
| Install and lock | `uv sync` (commit `uv.lock`) |
| Install the hooks (prek) | `make hooks` |
| Everything CI runs | `make check` |
| Tests | `uv run pytest` |
| Lint and format | `make lint`, `make fmt` |
| Types | `uv run ty check` |

Run Python and pytest as `uv run ...`. Never edit `uv.lock` by hand: change `pyproject.toml` and run `uv lock`.

## Rules that every change follows

1. **Correct first,** then measured, then fast. Vectorise (numpy, pandas), no row loops, `numpy.random.default_rng(seed)`.
2. **One focus per module,** said in its docstring; declarations, pure computation, I/O and command-line code live in
   separate modules; imports point one way.
3. **Names are plain and descriptive.** No `df`, `rng`, `tr`, `te`, `s`, `t`, `f`, `g`, `r`; no needless underscores.
4. **Google docstrings** on every public function and class, with `Args:` and `Returns:` where they apply; types
   live in the signature.
5. **Tests:** a unit test for every new function, edge cases included; a bug fix gets a test that fails on the old code;
   a refactor is checked old against new on real data.
6. **Checks before a commit:** `make check` (ruff, ty, deptry, the whole test suite).
7. **Git:** feature branch, conventional commit titles, stage explicit paths (never `git add -A`), no AI
   co-author trailer, open a pull request and wait to be told to merge.
8. One heavy job at a time on a laptop; heavy runs go to the server.
9. **Sources:** every number or fact that is not the project's own measurement comes with its original source (title,
   author, year, link) and the exact sentence it rests on; say whether it is a cause or a correlation and when it comes from
   a paper's limitations; mark what cannot be sourced as unverified and never fill the gap.
