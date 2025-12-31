from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tests.conftest import hash_directory, iter_json_files, load_json


@pytest.fixture()
def output_root(built_workspace: Path) -> Path:
    return built_workspace / "dist" / "src" / "data"


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
    output_root = workspace / "dist" / "src" / "data"

    from tests.conftest import _fallback_build, _run_subprocess  # local import to avoid pytest collection issues

    if build_command:
        _run_subprocess(build_command, workspace)
    else:
        _fallback_build(workspace)
    assert output_root.exists(), "dist/src/data should be produced"
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
    assert json_files, "Expected JSON outputs in dist/src/data"

    for json_path in json_files:
        if json_path.name == "index.json":
            index_data = load_json(json_path)
            if not index_data.get("entries"):
                continue
        schema = _schema_for_path(json_path, repo_root)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(load_json(json_path)), key=lambda err: err.path)
        assert not errors, f"Schema validation failed for {json_path}: {errors}"


def test_contract_completeness(output_root: Path) -> None:
    index_path = output_root / "index.json"
    assert index_path.exists(), "index.json must exist"

    characters_root = output_root / "characters"
    assert characters_root.exists(), "characters directory must exist"

    fragments_root = output_root / "fragments"
    assert fragments_root.exists(), "fragments directory must exist"
    assert any(fragments_root.iterdir()), "fragments directory must include placeholder files"

    for character_dir in characters_root.iterdir():
        if not character_dir.is_dir():
            continue
        manifest_path = character_dir / "manifest.json"
        assert manifest_path.exists(), f"Missing manifest.json for {character_dir.name}"

        fragments_dir = character_dir / "fragments"
        assert fragments_dir.exists(), f"Missing fragments/ for {character_dir.name}"
        entries = [path for path in fragments_dir.iterdir() if path.is_file()]
        assert entries, f"fragments/ must contain files or a placeholder for {character_dir.name}"
        assert any(path.name in {".keep", ".gitkeep"} or path.stat().st_size > 0 for path in entries), (
            f"fragments/ must be non-empty or include a placeholder for {character_dir.name}"
        )


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
    index_data = load_json(output_root / "index.json")
    assert index_data["entries"], "Expected at least one entry for site-only field checks"
    entry = index_data["entries"][0]
    entry_x = entry.get("x", {})
    assert entry_x.get("shortDescription") == ""
    assert entry_x.get("spoilerTags") == []
    assert entry_x.get("aiTokens") is None
    assert entry_x.get("uploadDate") != ""

    manifest_path = output_root / "characters" / entry["slug"] / "manifest.json"
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
