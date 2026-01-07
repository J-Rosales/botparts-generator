from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tests.conftest import hash_directory, iter_json_files, load_json


@pytest.fixture()
def output_root(built_workspace: Path) -> Path:
    return built_workspace / "dist" / "src" / "export"


def _load_schema(schema_name: str, repo_root: Path) -> dict:
    return load_json(repo_root / "schemas" / schema_name)


def _schema_for_path(path: Path, repo_root: Path) -> dict:
    if path.name == "index.json":
        return _load_schema("index.schema.json", repo_root)
    if path.name == "manifest.json":
        return _load_schema("manifest.schema.json", repo_root)
    return _load_schema("character.schema.json", repo_root)


def test_build_reproducibility(
    tmp_path: Path,
    repo_root: Path,
    build_command: str | None,
) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(repo_root, workspace, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    output_root = workspace / "dist" / "src" / "export"

    from tests.conftest import _fallback_build, _run_subprocess  # local import to avoid pytest collection issues

    if build_command:
        _run_subprocess(build_command, workspace)
    else:
        _fallback_build(workspace)
    assert output_root.exists(), "dist/src/export should be produced"
    first_hash = hash_directory(output_root)

    shutil.rmtree(output_root)
    if build_command:
        _run_subprocess(build_command, workspace)
    else:
        _fallback_build(workspace)
    second_hash = hash_directory(output_root)

    assert first_hash == second_hash, "Build output should be deterministic"


def test_schema_compliance(output_root: Path, repo_root: Path) -> None:
    json_files = list(iter_json_files(output_root))
    assert json_files, "Expected JSON outputs in dist/src/export"

    for json_path in json_files:
        if json_path.name != "manifest.json":
            continue
        schema = _schema_for_path(json_path, repo_root)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(load_json(json_path)), key=lambda err: err.path)
        assert not errors, f"Schema validation failed for {json_path}: {errors}"


def test_contract_completeness(output_root: Path) -> None:
    characters_root = output_root / "characters"
    assert characters_root.exists(), "characters directory must exist"

    for character_dir in characters_root.iterdir():
        if not character_dir.is_dir():
            continue
        manifest_path = character_dir / "manifest.json"
        assert manifest_path.exists(), f"Missing manifest.json for {character_dir.name}"
        assert (character_dir / "spec_v2.schema-like.json").exists()
        assert (character_dir / "spec_v2.hybrid.json").exists()


def test_no_site_coupling(repo_root: Path) -> None:
    forbidden_patterns = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in [
            r"botparts-site",
            r"botparts_site",
            r"botparts\.site",
            r"site/src",
            r"site\\src",
        ]
    ]

    checked_dirs = [repo_root / "src", repo_root / "scripts"]
    for directory in checked_dirs:
        if not directory.exists():
            continue
        for file_path in directory.rglob("*.py"):
            content = file_path.read_text(encoding="utf-8")
            if "site-seed" in content:
                content = content.replace("site-seed", "")
            assert not any(pattern.search(content) for pattern in forbidden_patterns), (
                f"Site coupling detected in {file_path}"
            )


def test_site_only_fields_present(output_root: Path) -> None:
    characters_root = output_root / "characters"
    slug = next(path.name for path in characters_root.iterdir() if path.is_dir())
    manifest_path = output_root / "characters" / slug / "manifest.json"
    manifest = load_json(manifest_path)
    manifest_x = manifest.get("x", {})
    assert manifest_x.get("shortDescription") == ""
    assert manifest_x.get("spoilerTags") == []
    assert manifest_x.get("aiTokens") is None
    assert manifest_x.get("uploadDate") != ""


def test_report_artifact(output_root: Path) -> None:
    report_path = output_root.parents[1] / "REPORT.md"
    assert report_path.exists(), "REPORT.md should be emitted at dist/REPORT.md"
    report_text = report_path.read_text(encoding="utf-8")
    assert "## Run Metadata" in report_text
    assert "## Output Summary" in report_text
    assert "## Field Policy Summary" in report_text
    assert "## Warnings" in report_text
    assert "Timestamp:" not in report_text
