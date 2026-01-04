from __future__ import annotations

import shutil
from pathlib import Path

from src.generator import build_site_data
from tests.conftest import _copy_repo_for_build, load_json


def test_variants_optional_when_missing(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    build_site_data(workspace)

    output_root = workspace / "dist" / "src" / "data"
    index_data = load_json(output_root / "index.json")
    assert index_data["entries"], "Expected at least one character entry"
    slug = index_data["entries"][0]["slug"]

    manifest = load_json(output_root / "characters" / slug / "manifest.json")
    manifest_x = manifest.get("x", {})
    assert "variants" not in manifest_x, "Variants should be optional when no variant inputs exist"


def test_variants_discovery_with_delta_spec(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
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

    output_root = workspace / "dist" / "src" / "data"
    variant_path = (
        output_root
        / "characters"
        / "bunker-survivor"
        / "fragments"
        / "variants"
        / "calm-tone"
        / "spec_v2_fields.md"
    )
    assert variant_path.exists(), "Expected variant delta spec to be copied into dist fragments"
    assert variant_path.read_text(encoding="utf-8") == (
        fixture_dir / "spec_v2_fields.md"
    ).read_text(encoding="utf-8")

    manifest = load_json(output_root / "characters" / "bunker-survivor" / "manifest.json")
    manifest_x = manifest.get("x", {})
    assert manifest_x.get("variants") == {
        "calm-tone": "fragments/variants/calm-tone/spec_v2_fields.md"
    }
