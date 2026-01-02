from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.generator import build_site_data
from tests.conftest import _copy_repo_for_build, load_json


def _build_workspace(tmp_path: Path, repo_root: Path, placeholders: int = 0) -> Path:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    build_site_data(workspace, placeholders=placeholders)
    return workspace


def test_tag_partitioning_and_dedupe(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    manifest_path = workspace / "sources" / "characters" / "example-bot" / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["tags"] = ["friendly", "spoiler: twist", "", "friendly", "spoiler:ending"]
    manifest["spoilerTags"] = ["twist", "ending", " "]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    build_site_data(workspace)
    output_root = workspace / "dist" / "src" / "data"
    index_data = load_json(output_root / "index.json")
    entry = next(entry for entry in index_data["entries"] if entry["slug"] == "example-bot")
    assert entry["tags"] == ["friendly"]
    assert entry["x"]["spoilerTags"] == ["twist", "ending"]


def test_placeholder_generation(tmp_path: Path, repo_root: Path) -> None:
    workspace = _build_workspace(tmp_path, repo_root, placeholders=3)
    output_root = workspace / "dist" / "src" / "data"
    index_data = load_json(output_root / "index.json")
    placeholder_entries = [entry for entry in index_data["entries"] if entry["slug"].startswith("placeholder-bot-")]
    assert len(placeholder_entries) == 3
    assert placeholder_entries[0]["slug"] == "placeholder-bot-01"
    assert placeholder_entries[0]["x"]["placeholder"] is True
    manifest_path = output_root / "characters" / "placeholder-bot-01" / "manifest.json"
    manifest = load_json(manifest_path)
    assert manifest["x"]["placeholder"] is True
    assert manifest["x"]["shortDescription"]


def test_output_completeness_empty_inputs(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    shutil.rmtree(workspace / "sources" / "characters")
    shutil.rmtree(workspace / "sources" / "site-seed")
    (workspace / "sources" / "characters").mkdir(parents=True)
    build_site_data(workspace)

    output_root = workspace / "dist" / "src" / "data"
    assert (output_root / "index.json").exists()
    index_data = load_json(output_root / "index.json")
    assert index_data["entries"] == []
    assert (output_root / "characters").exists()
    fragments_root = output_root / "fragments"
    assert fragments_root.exists()
    assert any(fragments_root.iterdir())


def test_fragment_copy_and_manifest_inventory(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    character_dir = workspace / "sources" / "characters" / "fragment-bot"
    (character_dir / "canonical").mkdir(parents=True)
    (character_dir / "fragments" / "spec_v2").mkdir(parents=True)
    (character_dir / "fragments" / "site").mkdir(parents=True)
    (character_dir / "variants" / "compact" / "spec_v2").mkdir(parents=True)

    spec_payload = {"slug": "fragment-bot", "name": "Fragment Bot", "description": "Fragmented."}
    (character_dir / "canonical" / "spec_v2_fields.md").write_text(
        json.dumps(spec_payload, indent=2), encoding="utf-8"
    )
    (character_dir / "canonical" / "shortDescription.md").write_text(
        "Canonical short description.\n", encoding="utf-8"
    )

    (character_dir / "fragments" / "spec_v2" / "description.md").write_text(
        "Line one.\r\nLine two.\r\n", encoding="utf-8"
    )
    (character_dir / "variants" / "compact" / "spec_v2" / "description.md").write_text(
        "Compact description.\n", encoding="utf-8"
    )

    build_site_data(workspace)
    output_root = workspace / "dist" / "src" / "data"
    fragments_root = output_root / "characters" / "fragment-bot" / "fragments"

    description_path = fragments_root / "spec_v2" / "description.md"
    assert description_path.exists()
    assert description_path.read_text(encoding="utf-8") == "Line one.\nLine two.\n"

    short_desc_path = fragments_root / "site" / "shortDescription.md"
    assert short_desc_path.exists()
    assert short_desc_path.read_text(encoding="utf-8") == "Canonical short description.\n"

    variant_desc_path = fragments_root / "variants" / "compact" / "spec_v2" / "description.md"
    assert variant_desc_path.exists()
    assert variant_desc_path.read_text(encoding="utf-8") == "Compact description.\n"

    manifest = load_json(output_root / "characters" / "fragment-bot" / "manifest.json")
    fragments_meta = manifest["x"]["fragments"]
    assert fragments_meta["spec_v2"]["description"] == "fragments/spec_v2/description.md"
    assert fragments_meta["site"]["shortDescription"] == "fragments/site/shortDescription.md"
    assert fragments_meta["fieldMap"]["first_message"] == "data.first_mes"
    assert fragments_meta["variants"]["compact"]["spec_v2"]["description"] == (
        "fragments/variants/compact/spec_v2/description.md"
    )
