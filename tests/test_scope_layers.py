from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import _copy_repo_for_build, load_json


def test_world_pack_emission(built_workspace: Path) -> None:
    output_root = built_workspace / "dist" / "src" / "data"
    world_root = output_root / "fragments" / "world" / "example-pack"

    atlas_path = world_root / "world" / "atlas.md"
    assert atlas_path.exists()
    atlas_text = atlas_path.read_text(encoding="utf-8")
    assert "scope:" not in atlas_text
    assert "Atlas Wardens" in atlas_text

    field_notes = world_root / "character" / "field_notes.md"
    assert field_notes.exists()


def test_scope_layers_manifest_metadata(built_workspace: Path) -> None:
    output_root = built_workspace / "dist" / "src" / "data"
    manifest_path = output_root / "characters" / "bunker-survivor" / "manifest.json"
    manifest = load_json(manifest_path)

    scope_layers = manifest["x"]["scopeLayers"]
    assert scope_layers["world"]["packs"] == ["example-pack"]
    assert "fragments/world/example-pack/world/atlas.md" in scope_layers["world"]["fragments"]
    assert "character" in scope_layers
    assert "variant" in scope_layers


def test_world_pack_promotion_gate(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    fragments_dir = workspace / "sources" / "world" / "holdback-pack" / "fragments"
    fragments_dir.mkdir(parents=True, exist_ok=True)
    (fragments_dir / "restricted.md").write_text(
        "---\nscope: world\n---\nBlocked without promotion.\n",
        encoding="utf-8",
    )

    from src.generator import build_site_data

    summary = build_site_data(workspace, strict_scopes=False)
    blocked_output = (
        workspace
        / "dist"
        / "src"
        / "data"
        / "fragments"
        / "world"
        / "holdback-pack"
        / "world"
        / "restricted.md"
    )
    assert not blocked_output.exists()
    assert any("holdback-pack" in warning for warning in summary.warnings)

    with pytest.raises(RuntimeError):
        build_site_data(workspace, strict_scopes=True)
