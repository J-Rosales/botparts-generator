---
version: 1
prompts:
  elaborate: 01_elaborate_v1.md
  extract_fields: 01_specv2_fields_v1.md
  tone: 01_neutral_v1.md
  style: 01_neutral_v1.md
  voice: 01_neutral_v1.md
prose_variant: schema-like # allowed: schema-like | hybrid
embedded_entries:
  transform_notes: |
    The system will always make 2 entries per canon embedded item type. Replace with transformation prompt.
---

# Character concept (staging selection)
Paste the character concept you want to select here.

> Note: This template is intentionally ignored by `bp author schema --schema-folder`. Clone it before authoring a new schema.

## Display name
Provide the display name the CLI should use.

## Elaborate prompt notes
Optional notes to guide the elaboration prompt.

## Draft edits (manual)
Notes or edits to apply after elaboration.

## Audit notes
Optional notes or expected checks after audit.
