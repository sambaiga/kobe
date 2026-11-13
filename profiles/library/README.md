# sample-project

A sample project.

## Install

```bash
uv sync                 # creates uv.lock the first time: commit it
make hooks              # git hooks, run by prek (or pre-commit)
make check              # ruff, ty, deptry and the tests
git switch -c feat/start # main is guarded: commit on a branch and open a pull request
```

## Layout

- `sample_package/`: the library, at the repository root and not under `src/`, as in twiga, popo and milia; one module per focus (`smoothing.py` is the example), the public API in `__init__.py`, and `py.typed` so that users' type checkers read the annotations.
- `tests/unit/`: mirrors the source tree.
- `scripts/`: small command-line helpers (`check_docstrings.py` is a hook).
- `.github/workflows/`: CI, security and the PyPI release (tags `v*`, trusted publishing).

Read `CLAUDE.md` for the working rules.

## Release

```bash
uv run cz bump --changelog   # bumps the version, writes CHANGELOG.md, tags vX.Y.Z
git push --follow-tags       # the tag starts .github/workflows/publish_pypi.yaml
```
