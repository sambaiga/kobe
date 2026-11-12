"""The command line: ``uv run python -m sample_package.steps run``. Parses arguments and prints; no logic."""

import argparse
from pathlib import Path

import numpy as np

from .analysis import compare, read, write
from .conditions import CONDITIONS

DEFAULT_OUTPUT = Path("results/scores.csv")


def make_series(seed: int, length: int) -> np.ndarray:
    """Draw a random-walk series, the same for the same seed.

    Args:
        seed: Seed of the generator.
        length: Number of values.

    Returns:
        The series.
    """
    generator = np.random.default_rng(seed)
    return np.cumsum(generator.standard_normal(length))


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser with the ``status`` and ``run`` commands.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="show whether results exist")
    status.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    run = commands.add_parser("run", help="score every condition and write the table")
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--length", type=int, default=200)
    run.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a command.

    Args:
        argv: Command-line arguments; ``None`` reads them from ``sys.argv``.

    Returns:
        The process exit code.
    """
    arguments = build_parser().parse_args(argv)
    if arguments.command == "status":
        done = arguments.output.exists()
        print(f"{len(CONDITIONS)} conditions; results {'found at' if done else 'not found at'} {arguments.output}")
        return 0
    frame = compare(make_series(arguments.seed, arguments.length))
    write(frame, arguments.output)
    print(read(arguments.output).round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
