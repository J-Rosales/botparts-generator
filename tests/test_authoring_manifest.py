from __future__ import annotations

import pytest

from src import authoring


def test_parse_combined_manifest() -> None:
    text = """---
version: 1
prompts:
  elaborate: 01_elaborate_v1.md
  extract_fields: 01_specv2_fields_v1.md
  tone: 01_neutral_v1.md
  style: 01_neutral_v1.md
  voice: 01_neutral_v1.md
prose_variant: hybrid
embedded_entries:
  transform_notes: |
    Always include a field medic kit.
---
# Character concept (staging selection)
Gentle scout who keeps a travel journal.

## Display name
Liora, the Field Medic
"""
    draft = authoring.parse_minimal_staging_draft(text)
    assert draft.manifest.version == 1
    assert draft.manifest.prompts["elaborate"] == "01_elaborate_v1.md"
    assert draft.manifest.prose_variant == "hybrid"
    assert "field medic kit" in draft.manifest.embedded_entries_transform_notes
    assert draft.display_name == "Liora, the Field Medic"


def test_parse_manifest_allows_all_prose_variant() -> None:
    text = """---
version: 1
prompts:
  elaborate: 01_elaborate_v1.md
  extract_fields: 01_specv2_fields_v1.md
  tone: 01_neutral_v1.md
  style: 01_neutral_v1.md
  voice: 01_neutral_v1.md
prose_variant: all
---
# Character concept (staging selection)
Concept here.

## Display name
Alpha
"""
    draft = authoring.parse_minimal_staging_draft(text)
    assert draft.manifest.prose_variant == "all"


def test_parse_combined_manifest_rejects_duplicate_sections() -> None:
    text = """---
version: 1
prompts:
  elaborate: 01_elaborate_v1.md
  extract_fields: 01_specv2_fields_v1.md
  tone: 01_neutral_v1.md
  style: 01_neutral_v1.md
  voice: 01_neutral_v1.md
---
# Character concept (staging selection)
Concept here.

## Display name
Alpha

## Display name
Beta
"""
    with pytest.raises(ValueError, match="Duplicate section"):
        authoring.parse_minimal_staging_draft(text)


def test_parse_combined_manifest_requires_frontmatter() -> None:
    text = "# Character concept (staging selection)\nConcept\n"
    with pytest.raises(ValueError, match="frontmatter"):
        authoring.parse_minimal_staging_draft(text)


def test_validate_spec_v2_llm_output() -> None:
    payload = {
        "mes_example": (
            "<START>Dialogue only line one.<END>\n\n"
            "<START>Pure narrative description of a scene.<END>\n\n"
            "<START>Hybrid: dialogue with narration around it.<END>\n\n"
            "<START>Distinct format: bullet-like beats in prose.<END>"
        ),
        "first_mes": "In winter at the harbor, Jonas greets you by name.",
        "alternate_greetings": [
            "In spring at the observatory, Mira waves to you.",
            "During summer in Kyoto, Aiko meets you by the gate.",
            "On a fall evening outside the library, Rafael smiles.",
        ],
    }
    authoring.validate_spec_v2_llm_output(payload)


def test_validate_spec_v2_llm_output_rejects_bad_mes_example() -> None:
    payload = {
        "mes_example": "<START>Only one example.<END>",
        "first_mes": "In winter at the harbor, Jonas greets you by name.",
        "alternate_greetings": [
            "In spring at the observatory, Mira waves to you.",
        ],
    }
    with pytest.raises(ValueError, match="mes_example"):
        authoring.validate_spec_v2_llm_output(payload)
