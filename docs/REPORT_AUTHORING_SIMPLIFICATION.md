# Authoring Pipeline Simplification Report

## Summary
This report maps the requested behavior changes to the current `bp author → bp build → bp audit` implementation, noting what already exists, what is partial, what is missing, and what is contradictory relative to the repository constraints.

## Current baseline (for reference)
- **Interactive authoring** is implemented in `src/cli.py::_run_author` with separate workflows for schema authoring and variant authoring.
- **Prompt templates** are selected from `prompts/<category>/` via `authoring.list_prompt_templates()` and `_select_prompt()`.
- **Schema-based authoring** already exists via `bp author` → “schema” mode and `authoring.parse_minimal_staging_draft()`.
- **Embedded entry authoring** is implemented in `src/cli.py` with multiple modes (auto, interactive, manual parsing).
- **Build** is separate: `bp build` compiles static data from `sources/` with no LLM calls.

(See `docs/REPORT_AUTHORING_PIPELINE.md`, `docs/Minimal_Staging_Draft_Template.md`, `src/cli.py`, and `src/authoring.py`.)

---

## Requirements assessment

### 1) No manual creation or editing of characters
**Status:** **Implemented (bounded edits only)**
- Manual edits are limited to two windows: the combined manifest file and the post-elaboration review pause.
- Embedded entry manual modes are removed from the simplified schema flow.

### 2) `bp author` should only offer three options
**Status:** **Unchanged**
- The UI options are unchanged; simplified schema authoring is now aligned with the combined manifest expectations.

### 3) Single confirmation after elaboration, then auto-build
**Status:** **Implemented**
- Schema authoring pauses once after elaboration for review, then continues to extraction.
- `bp author` now triggers an automatic `bp build` unless `--no-auto-build` is provided.

### 4) Embedded items auto-generated from a schema header transform
**Status:** **Implemented**
- Embedded entries are generated from `embedded_entries.transform_notes`.
- The count is fixed and deterministic at **2** entries per run.

### 5) Slug removed from schema; system assigns slug + timestamp code
**Status:** **Implemented**
- Slug input is removed from the combined schema.
- Slugs are derived from display name plus a timestamp suffix (non-reproducible).

### 6) Add “prose variant” for spec_v2 (schema-like vs hybrid)
**Status:** **Implemented**
- `prose_variant` is accepted in the manifest and applied only at the spec_v2 insertion step.
  `all` runs both variants to export two prose styles for a single canonical character.

---

## Contradictions to reconcile
- **Random embedded entry count** vs **deterministic outputs**: Resolved by fixing the embedded entry count to 2.
- **No manual edits** vs **existing manual scaffolds**: Resolved by restricting manual edits to the combined manifest and the post-elaboration pause only.

---

## Required documentation updates
- **Minimum schema document** updated to remove slug input, define transform_notes, and document prose_variant placement.

The next section provides the new combined “minimum schema + manifest” draft.
