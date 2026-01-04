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
