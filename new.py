"""Create a new project from a profile.

The profiles in ``profiles/`` are real, runnable projects named ``sample-project`` (package ``sample_package``).
Generating a project copies the shared files and then the profile's files over them, renames the package
directory and replaces those sample names with yours. There is no template language: every profile file is
linted, type checked and tested in this repository's CI exactly as it stands.

Example:
    Start a library, or an experiment that needs a token for a private dependency::

        uv run python new.py my-library --profile library
        uv run python new.py my-study --profile experiment --private-token TWIGA_TOKEN
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROFILES_DIR = ROOT / "profiles"
PROFILES = ("library", "experiment")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
TOKEN_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
PRIVATE_MARKER = "# private-dependency-step"
# Tool caches and build artefacts that appear when a profile is linted or tested in place.
IGNORED_PARTS = {
    "__pycache__", ".DS_Store", ".ruff_cache", ".pytest_cache", ".mypy_cache", ".hypothesis", ".venv", "htmlcov",
    ".coverage", "coverage.xml", "uv.lock",
}  # fmt: skip
# Stored without the leading dot, so that prek and pre-commit do not treat the profile as a nested project of
# this repository; the generated project gets the real name.
RENAMED_FILES = {"pre-commit-config.yaml": ".pre-commit-config.yaml"}

SAMPLE_PACKAGE = "sample_package"
SAMPLE_PROJECT = "sample-project"
SAMPLE_DESCRIPTION = "A sample project."
SAMPLE_AUTHOR = "Sample Author"
SAMPLE_EMAIL = "author@example.com"
SAMPLE_OWNER = "sample-owner"
DEFAULT_OWNER = "OWNER"  # a visible placeholder until the GitHub account is known


def validate_name(name: str) -> str:
    """Check that a project name is lower-case words joined by single hyphens.

    Args:
        name: The proposed project name, for example ``my-study``.

    Returns:
        The name, unchanged.

    Raises:
        ValueError: If the name is not lower-case letters and digits in hyphen-joined words, starting with a letter.
    """
    if not NAME_PATTERN.fullmatch(name):
        raise ValueError(
            f"invalid project name {name!r}: use lower-case letters and digits in words joined by single hyphens"
        )
    return name


def package_name(name: str) -> str:
    """Derive the importable package name from the project name.

    Args:
        name: A valid project name.

    Returns:
        The name with hyphens replaced by underscores.
    """
    return name.replace("-", "_")


def profile_files(profile: str, profiles_dir: Path = PROFILES_DIR) -> dict[Path, Path]:
    """List the files a profile produces: the shared ones, overridden by the profile's own.

    Args:
        profile: ``library`` or ``experiment``.
        profiles_dir: The folder that holds ``base`` and the profiles.

    Returns:
        Source file for each destination path relative to the project root.

    Raises:
        ValueError: If the profile is unknown.
    """
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}: choose from {', '.join(PROFILES)}")
    files: dict[Path, Path] = {}
    for layer in ("base", profile):
        folder = profiles_dir / layer
        for source in sorted(folder.rglob("*")):
            relative = source.relative_to(folder)
            if source.is_file() and not IGNORED_PARTS.intersection(relative.parts) and source.suffix != ".pyc":
                files[relative.with_name(RENAMED_FILES.get(relative.name, relative.name))] = source
    return files


def private_step(token: str, indent: str) -> str:
    """Write the workflow step that lets git fetch a dependency from a private repository.

    Args:
        token: Name of the repository secret that holds the access token.
        indent: Leading whitespace of the marker line the step replaces.

    Returns:
        The YAML step, indented to match the marker.

    Raises:
        ValueError: If ``token`` is not an upper-case secret name.
    """
    if not TOKEN_PATTERN.fullmatch(token):
        raise ValueError(f"invalid secret name {token!r}: use upper-case letters, digits and underscores")
    url = '"https://x-access-token:${PRIVATE_TOKEN}@github.com/".insteadOf "https://github.com/"'
    lines = [
        "- name: Authenticate to the private dependency repository",
        "  env:",
        f"    PRIVATE_TOKEN: ${{{{ secrets.{token} }}}}",
        f"  run: git config --global url.{url}",
    ]
    return "\n".join(indent + line for line in lines)


def render(text: str, replacements: list[tuple[str, str]], private_token: str | None) -> str:
    """Replace the sample names in a file and resolve the private-dependency marker.

    Args:
        text: Content of one text file.
        replacements: Pairs of sample text and replacement, applied in order.
        private_token: Secret name for the private-dependency step, or ``None`` to remove the marker.

    Returns:
        The rendered text.
    """
    for sample, replacement in replacements:
        text = text.replace(sample, replacement)
    if PRIVATE_MARKER not in text:
        return text
    lines = []
    for line in text.split("\n"):
        if line.strip() != PRIVATE_MARKER:
            lines.append(line)
        elif private_token:
            lines.append(private_step(private_token, line[: len(line) - len(line.lstrip())]))
    return "\n".join(lines)


def generate(
    name: str,
    profile: str,
    destination: Path,
    *,
    description: str = SAMPLE_DESCRIPTION,
    author: str = SAMPLE_AUTHOR,
    email: str = SAMPLE_EMAIL,
    owner: str = DEFAULT_OWNER,
    private_token: str | None = None,
    init_git: bool = True,
) -> Path:
    """Create a project folder from a profile.

    Args:
        name: Project name, validated by :func:`validate_name`.
        profile: ``library`` or ``experiment``.
        destination: Folder in which the project folder is created.
        description: One-line project description for ``pyproject.toml``.
        author: Author name for ``pyproject.toml``.
        email: Author email for ``pyproject.toml``.
        owner: GitHub owner for the project URLs.
        private_token: Name of the secret for a private dependency, or ``None``.
        init_git: Run ``git init -b main`` in the new folder.

    Returns:
        The path of the new project folder.

    Raises:
        FileExistsError: If the project folder already exists.
        ValueError: If the name, profile or secret name is invalid.
    """
    validate_name(name)
    package = package_name(name)
    files = profile_files(profile)
    project = destination / name
    if project.exists():
        raise FileExistsError(f"{project} already exists")
    replacements = [
        (SAMPLE_DESCRIPTION, description),
        (SAMPLE_AUTHOR, author),
        (SAMPLE_EMAIL, email),
        (SAMPLE_OWNER, owner),
        (SAMPLE_PROJECT, name),
        (SAMPLE_PACKAGE, package),
    ]
    for relative, source in files.items():
        target = project / Path(*(package if part == SAMPLE_PACKAGE else part for part in relative.parts))
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_text(render(source.read_text(encoding="utf-8"), replacements, private_token), encoding="utf-8")
            shutil.copymode(source, target)
        except UnicodeDecodeError:
            shutil.copy2(source, target)
    if init_git:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=project, check=True)  # noqa: S607
    return project


def git_config(key: str) -> str | None:
    """Read one value from the user's git configuration.

    Args:
        key: The configuration key, for example ``user.name``.

    Returns:
        The value, or ``None`` when it is not set or git is missing.
    """
    try:
        result = subprocess.run(["git", "config", "--get", key], capture_output=True, text=True, check=False)  # noqa: S603, S607
    except FileNotFoundError:
        return None
    return result.stdout.strip() or None


def main(argv: list[str] | None = None) -> int:
    """Parse the command line and create the project.

    Args:
        argv: Command-line arguments; ``None`` reads them from ``sys.argv``.

    Returns:
        The process exit code: 0 on success, 2 for an invalid request.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", help="project name: lower-case words joined by hyphens, for example my-study")
    parser.add_argument("--profile", required=True, choices=PROFILES)
    parser.add_argument("--dest", type=Path, default=Path.cwd(), help="folder to create the project in")
    parser.add_argument("--description", default=SAMPLE_DESCRIPTION)
    parser.add_argument("--author", default=git_config("user.name") or SAMPLE_AUTHOR)
    parser.add_argument("--email", default=git_config("user.email") or SAMPLE_EMAIL)
    parser.add_argument(
        "--owner", default=git_config("github.user") or DEFAULT_OWNER, help="GitHub user or organisation"
    )
    parser.add_argument("--private-token", metavar="SECRET", help="secret name for a private dependency's token")
    parser.add_argument("--no-git", action="store_true", help="do not run git init")
    arguments = parser.parse_args(argv)
    try:
        project = generate(
            arguments.name,
            arguments.profile,
            arguments.dest,
            description=arguments.description,
            author=arguments.author,
            email=arguments.email,
            owner=arguments.owner,
            private_token=arguments.private_token,
            init_git=not arguments.no_git,
        )
    except (ValueError, FileExistsError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    steps = [
        "uv sync                  # creates uv.lock: commit it",
        "make hooks               # prek git hooks",
        "make check               # everything CI runs",
        "git switch -c feat/start # main is guarded: commit on a branch, then open a pull request",
    ]
    print(f"Created {project}\n\nNext:\n  cd {project}\n" + "\n".join(f"  {step}" for step in steps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
