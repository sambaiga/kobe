"""Check docstring coverage and Google-style sections for each Python file.

Used as a pre-commit hook. A file fails when either:

* its docstring coverage, as measured by interrogate, is below the threshold
  (90% by default), or
* a documented function takes arguments but has no ``Args:`` section, or
  returns a value but has no ``Returns:`` (or ``Yields:``) section.

Example:
    Check two files with the default threshold::

        python scripts/check_docstrings.py sample_package/scoring.py scripts/check_docstrings.py
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path
import sys

from interrogate.config import InterrogateConfig
from interrogate.coverage import InterrogateCoverage

DEFAULT_THRESHOLD = 90.0


@dataclass
class FileReport:
    """Docstring findings for one file.

    Attributes:
        path: File that was checked.
        coverage: Percentage of documentable objects that have a docstring.
        missing_sections: Human-readable descriptions of missing Google sections.
    """

    path: Path
    coverage: float
    missing_sections: list[str] = field(default_factory=list)

    def passes(self, threshold: float) -> bool:
        """Report whether the file meets the coverage threshold and has all sections.

        Args:
            threshold: Minimum acceptable coverage, in percent.

        Returns:
            True when coverage is at least ``threshold`` and no section is missing.
        """
        return self.coverage >= threshold and not self.missing_sections


def measure_coverage(paths: list[Path]) -> dict[Path, float]:
    """Measure docstring coverage for each file with interrogate.

    Private helpers count towards coverage; ``__init__`` methods and magic
    methods do not, because Google style documents constructor arguments in the
    class docstring.

    Args:
        paths: Python files to measure.

    Returns:
        Coverage in percent, keyed by file path. Files with nothing to document
        are reported as fully covered.
    """
    # interrogate's config is an attrs class, whose generated signature ty cannot see.
    config = InterrogateConfig(ignore_init_method=True, ignore_magic=True)  # ty: ignore[unknown-argument]
    results = InterrogateCoverage(paths=[str(path) for path in paths], conf=config).get_coverage()
    coverage = {Path(result.filename).resolve(): result.perc_covered for result in results.file_results}
    return {path: coverage.get(path.resolve(), 100.0) for path in paths}


def returns_value(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Decide whether a function's annotation declares a return value.

    Args:
        function: Parsed function definition.

    Returns:
        True when the return annotation exists and is not ``None``.
    """
    annotation = function.returns
    if annotation is None:
        return False
    return not (isinstance(annotation, ast.Constant) and annotation.value is None)


def is_property(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Decide whether a function is decorated as a property.

    Args:
        function: Parsed function definition.

    Returns:
        True for ``@property`` and ``@cached_property`` methods, whose summary
        line already describes the value.
    """
    for decorator in function.decorator_list:
        name = decorator.attr if isinstance(decorator, ast.Attribute) else getattr(decorator, "id", "")
        if name in {"property", "cached_property"}:
            return True
    return False


def find_missing_sections(path: Path) -> list[str]:
    """List documented functions that lack an ``Args:`` or ``Returns:`` section.

    Args:
        path: Python file to inspect.

    Returns:
        One message per missing section, in source order.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    problems = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        docstring = ast.get_docstring(node)
        if not docstring or node.name == "__init__" or is_property(node):
            continue
        arguments = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        names = [argument.arg for argument in arguments if argument.arg not in {"self", "cls"}]
        if node.args.vararg:
            names.append(node.args.vararg.arg)
        if node.args.kwarg:
            names.append(node.args.kwarg.arg)
        if names and "Args:" not in docstring:
            problems.append(f"line {node.lineno}: {node.name}() has arguments but no Args: section")
        if returns_value(node) and "Returns:" not in docstring and "Yields:" not in docstring:
            problems.append(f"line {node.lineno}: {node.name}() returns a value but has no Returns: section")
    return sorted(problems, key=lambda message: int(message.split(":")[0].removeprefix("line ")))


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Arguments to parse; ``None`` reads them from ``sys.argv``.

    Returns:
        Parsed arguments with ``files`` and ``fail_under``.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path, help="Python files to check.")
    parser.add_argument(
        "--fail-under",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum docstring coverage per file, in percent (default {DEFAULT_THRESHOLD:g}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the check and print a report of failing files.

    Args:
        argv: Command-line arguments; ``None`` reads them from ``sys.argv``.

    Returns:
        Process exit code: 0 when every file passes, 1 otherwise.
    """
    arguments = parse_arguments(argv)
    files = [path for path in arguments.files if path.suffix == ".py"]
    if not files:
        return 0
    coverage = measure_coverage(files)
    reports = [FileReport(path, coverage[path], find_missing_sections(path)) for path in files]
    failures = [report for report in reports if not report.passes(arguments.fail_under)]
    for report in failures:
        print(f"{report.path}: docstring coverage {report.coverage:.1f}% (minimum {arguments.fail_under:g}%)")
        for message in report.missing_sections:
            print(f"    {message}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
