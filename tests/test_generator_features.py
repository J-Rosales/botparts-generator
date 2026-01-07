from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.generator import build_site_data
from tests.conftest import _copy_repo_for_build, load_json, seed_character_sources


def _build_workspace(tmp_path: Path, repo_root: Path, placeholders: int = 0) -> Path:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace, slug="example-bot")
    build_site_data(workspace, placeholders=placeholders)
    return workspace


def test_tag_partitioning_and_dedupe(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    character_dir = seed_character_sources(workspace, slug="example-bot")
    manifest_path = character_dir / "manifest.json"
    manifest = {
        "slug": "example-bot",
        "tags": ["friendly", "spoiler: twist", "", "friendly", "spoiler:ending"],
        "spoilerTags": ["twist", "ending", " "],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    build_site_data(workspace)
    output_root = workspace / "dist" / "src" / "export"
    manifest_out = load_json(output_root / "characters" / "example-bot" / "manifest.json")
    assert manifest_out["tags"] == ["friendly"]
    assert manifest_out["x"]["spoilerTags"] == ["twist", "ending"]


def test_placeholder_generation(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace, slug="example-bot")
    summary = build_site_data(workspace, placeholders=3)
    assert any("Placeholders requested" in warning for warning in summary.warnings)


def test_output_completeness_empty_inputs(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    shutil.rmtree(workspace / "sources" / "characters", ignore_errors=True)
    shutil.rmtree(workspace / "sources" / "site-seed")
    (workspace / "sources" / "characters").mkdir(parents=True)
    build_site_data(workspace)

    output_root = workspace / "dist" / "src" / "export"
    assert (output_root / "characters").exists()
    assert not any((output_root / "characters").iterdir())
