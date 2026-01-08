from __future__ import annotations

import json

import pytest

from src import authoring
from src.cli import _parse_embedded_entries_input, _resolve_embedded_entries_mode
from src.generator import EMBEDDED_ENTRY_TYPES


def test_embedded_entries_mode_resolution() -> None:
    assert _resolve_embedded_entries_mode(1) == "auto"
    assert _resolve_embedded_entries_mode(2) == "from_input"
    assert _resolve_embedded_entries_mode(3) == "skip"
    with pytest.raises(ValueError):
        _resolve_embedded_entries_mode(0)


def test_parse_embedded_entries_input() -> None:
    assert _parse_embedded_entries_input("Name: Description") == (
        "ENTRY",
        "Name",
        "Description",
    )
    assert _parse_embedded_entries_input("CONTINUE") == ("CONTINUE", None, None)
    assert _parse_embedded_entries_input("NEXT") == ("NEXT", None, None)
    with pytest.raises(ValueError):
        _parse_embedded_entries_input("MissingColon")


def test_auto_mode_bounded_entries() -> None:
    entries = [
        {
            "title": f"Title {index}",
            "slug": f"slug-{index:02d}",
            "description": f"Description {index}",
        }
        for index in range(12)
    ]
    payload = {entry_type: entries for entry_type in EMBEDDED_ENTRY_TYPES}
    parsed = authoring.parse_embedded_entries_auto_response(
        json.dumps(payload),
        EMBEDDED_ENTRY_TYPES,
        max_per_type=10,
    )
    for entry_type in EMBEDDED_ENTRY_TYPES:
        slugs = [entry.slug for entry in parsed[entry_type]]
        assert slugs == [f"slug-{index:02d}" for index in range(10)]


def test_select_embedded_entries_respects_target() -> None:
    entries_by_type = {
        "items": [
            authoring.EmbeddedEntry(title="Item A", slug="item-a", description="A"),
            authoring.EmbeddedEntry(title="Item B", slug="item-b", description="B"),
            authoring.EmbeddedEntry(title="Item C", slug="item-c", description="C"),
        ],
        "locations": [
            authoring.EmbeddedEntry(title="Location A", slug="loc-a", description="A"),
            authoring.EmbeddedEntry(title="Location B", slug="loc-b", description="B"),
        ],
    }
    selected = authoring.select_embedded_entries(entries_by_type, 2)
    assert len(selected) == 4
    assert [entry.slug for _, entry in selected] == ["item-a", "item-b", "loc-a", "loc-b"]
