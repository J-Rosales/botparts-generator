from __future__ import annotations

import shutil
from pathlib import Path

from src.generator import build_site_data
from tests.conftest import _copy_repo_for_build, load_json, seed_character_sources


def test_variants_optional_when_missing(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace, slug="example-bot")
    build_site_data(workspace)

    output_root = workspace / "dist" / "src" / "export"
    manifest = load_json(output_root / "characters" / "example-bot" / "manifest.json")
    manifest_x = manifest.get("x", {})
    assert "variantSlugs" not in manifest_x, "Variants should be optional when no variant inputs exist"


def test_variants_discovery_with_delta_spec(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace, slug="bunker-survivor")
    fixture_dir = (
        repo_root
        / "fixtures"
        / "variant_sources"
        / "sources"
        / "characters"
        / "test-one"
        / "variants"
        / "calm-tone"
    )
    target_dir = workspace / "sources" / "characters" / "test-one" / "variants" / "calm-tone"
    target_dir.mkdir(parents=True, exist_ok=True)
    for file_path in fixture_dir.iterdir():
        if file_path.is_file():
            shutil.copy2(file_path, target_dir / file_path.name)

    build_site_data(workspace)

    output_root = workspace / "dist" / "src" / "export"
    variant_root = output_root / "characters" / "bunker-survivor" / "variants" / "calm-tone"
    assert (variant_root / "spec_v2.schema-like.json").exists()
    assert (variant_root / "spec_v2.hybrid.json").exists()

    manifest = load_json(output_root / "characters" / "bunker-survivor" / "manifest.json")
    manifest_x = manifest.get("x", {})
    assert manifest_x.get("variantSlugs") == ["calm-tone"]
