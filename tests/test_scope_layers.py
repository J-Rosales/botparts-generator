from __future__ import annotations

from pathlib import Path

from src.generator import build_site_data
from tests.conftest import _copy_repo_for_build, load_json, seed_character_sources


def test_world_packs_ignored_in_export(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace, slug="bunker-survivor")
    build_site_data(workspace)

    output_root = workspace / "dist" / "src" / "export"
    manifest_path = output_root / "characters" / "bunker-survivor" / "manifest.json"
    manifest = load_json(manifest_path)
    manifest_x = manifest.get("x", {})
    assert "scopeLayers" not in manifest_x
    assert "worldPacks" not in manifest_x


def test_strict_scope_flag_warns(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace, slug="scope-bot")
    summary = build_site_data(workspace, strict_scopes=True)
    assert any("Strict scope mode is ignored" in warning for warning in summary.warnings)
