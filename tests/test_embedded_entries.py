from __future__ import annotations

from pathlib import Path

from tests.conftest import load_json


def test_embedded_entry_fragments_emitted(output_root: Path) -> None:
    manifest_path = output_root / "characters" / "bunker-survivor" / "manifest.json"
    manifest = load_json(manifest_path)
    embedded_entries = manifest.get("x", {}).get("embeddedEntries")
    assert embedded_entries is not None

    assert embedded_entries["locations"] == [
        "fragments/entries/locations/anchorage.md",
        "fragments/entries/locations/harbor.md",
    ]
    assert embedded_entries["items"] == [
        "fragments/entries/items/compass.md",
        "fragments/entries/items/lantern.md",
    ]
    assert embedded_entries["relationships"] == []

    entries_root = output_root / "characters" / "bunker-survivor" / "fragments" / "entries"
    assert (entries_root / "locations" / "anchorage.md").exists()
    assert (entries_root / "locations" / "harbor.md").exists()
    assert (entries_root / "items" / "compass.md").exists()
    assert (entries_root / "items" / "lantern.md").exists()
    assert (entries_root / "relationships" / ".keep").exists()
