---
name: project-organisation
description: How to organise a Python project so that every module and package has one focus: layering, module size, where new code goes, how to split an oversized module without breaking users, and how to separate declarations, pure computation, I/O and command-line code. Use when creating a module or package, adding a feature, reviewing structure, or when a file has grown past one responsibility.
---

# Project organisation: one module, one job

Load [[coding-standards]] first. A reader should be able to say what a module is for in one sentence, and find any behaviour by guessing its module name.

## The rule

1. **One focus per module.** Describe it in one sentence in the module docstring (`"""Weight averaging for the neural forecasters: EMA or SWA."""`). If the sentence needs "and" between unrelated things, it is two modules. Name the module for its purpose (`averaging.py`, `optimizers.py`, `scoring.py`), never `utils.py`, `helpers.py`, `misc.py` or `common.py`.
2. **Size is a smell, not a limit.** Look at a module past about 500 lines, split one past about 1,000, and stop at once when it holds more than about 15 public functions or classes of unrelated kinds. A long module of one kind (a declarative table of conditions, a registry) is fine; a long module that mixes kinds is not.
3. **Separate the four kinds of code,** each in its own module or package:
   - **declarations:** configuration, condition tables, registries, constants (data, no logic);
   - **pure computation:** metrics, transforms, models (no file, network, plotting or printing; fully unit-testable);
   - **I/O and orchestration:** loading, saving, running, caching, analysis pipelines;
   - **entry points:** command-line parsing and printing only, thin, calling the layers below.
4. **Plotting is its own layer.** Computation returns data; a plotting module draws it; a notebook or script only orchestrates and defines no functions.

## Layering

5. Packages form layers with imports pointing one way: `data -> core (features, metrics, config) -> distributions and models -> forecaster/orchestration -> experiments and CLI`. A lower layer never imports a higher one; no cycles. Write the layers down in the package docstring and, to enforce them, in an `import-linter` contract.
6. **Public API:** each package's `__init__.py` re-exports the names users need with `__all__`; everything else is reachable by its module path. Leading-underscore names are private; do not import them from another module.
7. **Registries and plug-ins** follow one pattern per repository (a name to class registry, a function that builds from a config); do not add a second pattern.
8. **Config is data.** Pydantic models for settings, validated at the boundary; no settings read deep inside computation; every option reaches every place that uses it (see [[pytorch-lightning-engineering]], rule 5).

## Where new code goes

9. Search first (`rg`), in the repo and in the library it should reuse (milia for mbuga): extend the module that already has the focus. Create a module only when no existing focus fits, check the name is free, and add it to the package's `__init__` exports and docs.
10. **Layout.** A library keeps its package at the repository root (`<package>/`, with `py.typed` inside), not under `src/`; `tests/` mirrors it, and `scripts/` holds the development helpers. Run everything from the root with `uv run` so that the working tree is the package under test, and keep `packages = ["<package>"]` in the hatch wheel target.
10. A new feature touches, in order: the pure function (with its test), the config field and its validation, the wiring in every consumer, the experiment condition or entry point, the documentation. Do not start at the entry point.
11. **Tests mirror the source tree** (`tests/unit/<package path>/test_<module>.py`); a new module brings its test module.

## Splitting a module that grew too big

12. Split by responsibility, not by line count: group functions that change together and share state. Move one group at a time into a new module named for it.
13. Keep the old import path working: re-export the moved names from the old module (or the package `__init__`) for one release, with a deprecation note, so no caller breaks.
14. Verify behaviour is unchanged: the full test suite plus an old-versus-new equivalence run on real saved data. Commit the move alone, with no behaviour change in the same commit.
15. Do not rename public names or move files without asking when other repositories import them.

## Measured in this user's repositories (2026-11-12)

- **Focused, to copy:** twiga `models/nn/core/{optimizers,averaging}.py` (one job each); fpqr-experiment `tail_adaptive/` separates conditions (declarations), scoring (pure), analysis (I/O), design (comparisons) and steps (command line).
- **To split when touched:** `umeme/style/diagrams.py` (9,888 lines, 10 classes, 224 functions: group by diagram family); twiga `core/plot/evaluation.py` (2,322 lines), `forecaster/base.py` (1,831), `experiment/engine.py` (1,777), `core/data/processing.py` (1,607 lines of 36 functions with no class); fpqr-experiment `tail_adaptive/hypotheses.py` (1,239 lines mixing hypothesis definitions with their evaluation code). Do not split them as a side effect of another change: open a dedicated, behaviour-free PR.

## Review checklist

1. Can the module's purpose be said in one sentence, and does its name say it?
2. Does it mix declarations, computation, I/O and entry-point code?
3. Do imports go only downwards, with no cycle and no private import across modules?
4. Is the public API in `__init__` with `__all__`?
5. Is there a test module that mirrors it, and does the move keep every old import working?
