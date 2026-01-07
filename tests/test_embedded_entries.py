from __future__ import annotations

from pathlib import Path

from src.generator import build_site_data
from tests.conftest import _copy_repo_for_build, load_json, seed_character_sources


def test_embedded_entries_exported(tmp_path: Path, repo_root: Path) -> None:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    character_dir = seed_character_sources(workspace, slug="entry-bot")
    entries_root = character_dir / "fragments" / "entries"
    (entries_root / "locations").mkdir(parents=True, exist_ok=True)
    (entries_root / "items").mkdir(parents=True, exist_ok=True)
    (entries_root / "locations" / "harbor.md").write_text("Harbor notes.", encoding="utf-8")
    (entries_root / "items" / "compass.md").write_text("Compass notes.", encoding="utf-8")

    build_site_data(workspace)
    output_root = workspace / "dist" / "src" / "export"
    spec_path = output_root / "characters" / "entry-bot" / "spec_v2.schema-like.json"
    spec_payload = load_json(spec_path)
    book = spec_payload["data"]["character_book"]
    entry_types = {entry["extensions"]["entryType"] for entry in book["entries"]}
    entry_names = {entry["name"] for entry in book["entries"]}
    assert entry_types == {"locations", "items"}
    assert entry_names == {"harbor", "compass"}
