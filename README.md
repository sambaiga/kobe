<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo.svg" alt="kobe: profiles, generator, skills" width="480">
  </picture>
</p>

*Kobe* is Swahili for tortoise, the animal that carries its foundation on its back. This repository is where a new Python project starts, and what every project stands on: two ready profiles, the coding skills that go with them, and a small generator.

```bash
uv run python new.py my-study --profile experiment            # a research or reproducibility repo
uv run python new.py my-library --profile library             # a package published to PyPI
uv run python new.py my-study --profile experiment --private-token TWIGA_TOKEN   # a private git dependency
cd my-study && uv sync && make hooks && make check
```

## The profiles

Both start from the same base and differ only where a library and an experiment really differ.

| | `library` | `experiment` |
|---|---|---|
| Layout | `src/<package>/`, one module per focus, public API in `__init__.py`, `py.typed` | `<package>/` in layers: `conditions` (declarations), `scoring` (pure), `analysis` (I/O), `steps` (command line), with an import contract |
| Also has | optional extras, Python 3.12 and 3.13 matrix, PyPI publishing by trusted publishing on a `v*` tag, changelog by commitizen | `data/`, `notebooks/`, `paper/`, regenerated `results/` (not committed), `make run` and `make status`, optional private-dependency token |
| Test floor | coverage at least 80 % | coverage at least 70 % |

## What every project gets

- **uv:** `requires-python`, `.python-version`, dependency groups (PEP 735) with `default-groups`, `required-version`, a
  committed `uv.lock`, `uv sync --locked` in CI, `uv build` and `uv publish --trusted-publishing always`, `uvx` for
  one-off tools.
- **prek** runs the hooks (a fast Rust drop-in for pre-commit that reads the same `.pre-commit-config.yaml`; `uvx
  pre-commit` works unchanged if you ever need it): ruff, codespell, secret and private-key detection, bandit,
  the `uv-lock` check, commitizen, a hook that rejects AI co-author trailers, and on push: `ty`, a Google-docstring
  check, and `deptry`.
- **ruff** with limits on complexity, branches and statements, no `print` in library code, numpy and pandas
  checks, and Google docstrings; **ty** type checking starting with no ignored rules.
- **pytest** with strict markers and config, warnings as errors, branch coverage with a floor, `hypothesis` for
  invariants, and `diff-cover` requiring 90 % coverage of the lines a pull request changes.
- **GitHub Actions** pinned by commit SHA, least-privilege permissions, `persist-credentials: false`, a weekly
  `pip-audit`, `zizmor` to audit the workflows, a main-branch guard, and Dependabot for the actions and the lock file.
- A `CLAUDE.md` with the working rules and a pull request template with the checklist.

## The skills

`skills/` holds the coding skills (`coding-standards`, `python-performance`, `python-testing`,
`numerical-correctness`, `project-organisation`, `pytorch-lightning-engineering`). This copy is the source of truth:
`skills/install.sh` links each one into `~/.claude/skills` so an edit here is live in every project. It skips a
skill that already exists there as a real folder; move that folder away first.

## Changing the standard

Edit the profile files directly: they are plain files, not templates. CI generates each profile into a temporary
project and runs ruff, ty, deptry, the import contract, the tests and the hooks on it, so a profile that stops working
fails here first. A new project takes a snapshot; to bring an older project up to date, diff it against the profile.

## Choices worth knowing

- **No template engine.** A new project is a snapshot, so copier's `update` was not needed, and plain files can be
  linted and tested. If you later want to push changes to existing projects, copier is the natural next step.
- **prek is 0.x.** It is used because it is faster and compatible with the existing config; the `pygrep`, `python` and
  `system` hook types this repo uses were checked. Fall back to `uvx pre-commit` if it ever misbehaves.
- **ty is young.** It starts strict here; keep it pinned and treat any ignored rule as debt with a date.
- **Not verified here:** the GitHub workflows run only on GitHub (the generated project's tests and hooks are run locally and in
  this repository's CI); `uv publish` and the Dependabot `uv` ecosystem should be checked on the first real release and the first Dependabot run.
