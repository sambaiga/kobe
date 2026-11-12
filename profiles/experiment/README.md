# sample-project

A sample project.

## Run

```bash
uv sync                 # creates uv.lock the first time: commit it
make hooks              # git hooks, run by prek (or pre-commit)
make check              # ruff, ty, deptry, the layering contract and the tests
git switch -c feat/start # main is guarded: commit on a branch and open a pull request
make run                # score every condition and write results/scores.csv
```

## Layout

- `sample_package/`: the layers, bottom to top: `conditions.py` (declarations), `scoring.py` (pure computation),
  `analysis.py` (reads and writes results), `steps.py` (the command line). `make imports` fails if a lower layer imports a higher one.
- `tests/`: one test module per source module.
- `data/`, `notebooks/`, `paper/`: inputs, exploration and the write-up. Notebooks orchestrate and define no functions;
  everything they call lives in `sample_package/` with a test. `results/` is regenerated and is not committed.

Read `CLAUDE.md` for the working rules. Heavy runs go to the server, one job at a time on a laptop.
