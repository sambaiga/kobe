"""Tests of the generator: names, file lists, renaming, the private-dependency marker and the sample names."""

from pathlib import Path

import pytest

import new


@pytest.mark.parametrize("name", ["a", "my-study", "twiga2", "a-b-c"])
def test_valid_names_are_accepted(name):
    assert new.validate_name(name) == name


@pytest.mark.parametrize("name", ["", "My-Study", "my_study", "-a", "a-", "a--b", "1abc", "my study"])
def test_invalid_names_are_rejected(name):
    with pytest.raises(ValueError, match="invalid project name"):
        new.validate_name(name)


def test_the_package_name_replaces_hyphens_with_underscores():
    assert new.package_name("my-long-study") == "my_long_study"


def test_a_profile_adds_its_files_to_the_shared_ones():
    library, experiment = new.profile_files("library"), new.profile_files("experiment")
    shared = Path("scripts/check_docstrings.py")
    assert shared in library and shared in experiment
    assert Path("sample_package/smoothing.py") in library
    assert Path("sample_package/scoring.py") in experiment
    assert Path("sample_package/smoothing.py") not in experiment


def test_an_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="unknown profile"):
        new.profile_files("book")


def test_the_private_step_names_the_secret_and_keeps_the_indent():
    step = new.private_step("TWIGA_TOKEN", "      ")
    assert "secrets.TWIGA_TOKEN" in step
    assert all(line.startswith("      ") for line in step.splitlines())


def test_a_secret_name_must_be_upper_case():
    with pytest.raises(ValueError, match="invalid secret name"):
        new.private_step("twiga-token", "")


def test_the_marker_is_replaced_by_the_step_or_removed():
    text = "a:\n  steps:\n    # private-dependency-step\n    - run: x"
    with_step = new.render(text, [], "TOKEN")
    assert "secrets.TOKEN" in with_step and new.PRIVATE_MARKER not in with_step
    without = new.render(text, [], None)
    assert without == "a:\n  steps:\n    - run: x"


@pytest.mark.parametrize("profile", new.PROFILES)
def test_a_generated_project_has_no_sample_names_left(profile, tmp_path):
    project = new.generate("demo-study", profile, tmp_path, init_git=False)
    for path in project.rglob("*"):
        assert "sample_package" not in path.parts
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for sample in (new.SAMPLE_PACKAGE, new.SAMPLE_PROJECT, new.SAMPLE_OWNER, new.PRIVATE_MARKER):
                assert sample not in text, f"{sample} left in {path}"


def test_the_package_directory_follows_the_layout_of_the_profile(tmp_path):
    library = new.generate("demo-lib", "library", tmp_path, init_git=False)
    experiment = new.generate("demo-exp", "experiment", tmp_path, init_git=False)
    assert (library / "demo_lib" / "__init__.py").is_file()
    assert (experiment / "demo_exp" / "scoring.py").is_file()
    assert 'name = "demo-lib"' in (library / "pyproject.toml").read_text(encoding="utf-8")


def test_the_metadata_is_written_into_the_project(tmp_path):
    project = new.generate(
        "demo-lib", "library", tmp_path, description="Does a thing.", author="Ada", email="ada@x.org",
        owner="ada", init_git=False,
    )  # fmt: skip
    text = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "Does a thing." in text and "Ada" in text and "ada@x.org" in text
    assert "github.com/ada/demo-lib" in text


def test_the_private_token_reaches_the_workflows_only_when_given(tmp_path):
    plain = new.generate("demo-a", "experiment", tmp_path, init_git=False)
    private = new.generate("demo-b", "experiment", tmp_path, private_token="MY_TOKEN", init_git=False)
    for name in ("ci.yaml", "security.yaml"):
        assert "MY_TOKEN" not in (plain / ".github" / "workflows" / name).read_text(encoding="utf-8")
        assert "secrets.MY_TOKEN" in (private / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_an_existing_folder_is_never_overwritten(tmp_path):
    new.generate("demo-a", "library", tmp_path, init_git=False)
    with pytest.raises(FileExistsError):
        new.generate("demo-a", "library", tmp_path, init_git=False)


def test_the_command_line_reports_a_bad_name_with_exit_code_two(tmp_path, capsys):
    assert new.main(["Bad_Name", "--profile", "library", "--dest", str(tmp_path)]) == 2
    assert "invalid project name" in capsys.readouterr().err


def test_git_is_initialised_on_main(tmp_path):
    project = new.generate("demo-a", "library", tmp_path)
    assert (project / ".git").is_dir()


@pytest.mark.parametrize("profile", new.PROFILES)
def test_the_hook_config_is_stored_without_its_dot_and_generated_with_it(profile, tmp_path):
    assert Path("pre-commit-config.yaml") not in new.profile_files(profile)
    assert Path(".pre-commit-config.yaml") in new.profile_files(profile)
    project = new.generate("demo-study", profile, tmp_path, init_git=False)
    assert (project / ".pre-commit-config.yaml").is_file()
    assert not (project / "pre-commit-config.yaml").exists()


def test_tool_caches_and_artefacts_in_a_profile_folder_are_not_copied(tmp_path):
    for layer in ("base", "library"):
        (tmp_path / layer).mkdir()
    (tmp_path / "base" / "keep.txt").write_text("x", encoding="utf-8")
    for junk in (
        ".ruff_cache/0.1/abc",
        "__pycache__/m.pyc",
        ".venv/bin/python",
        "coverage.xml",
        "uv.lock",
        ".coverage",
    ):
        target = tmp_path / "library" / junk
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("junk", encoding="utf-8")
    assert list(new.profile_files("library", tmp_path)) == [Path("keep.txt")]
