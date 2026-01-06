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
**Status:** **Partial / conflicting**
- **Partial:** The CLI can already scaffold characters from a minimal schema (`_run_author_schema`) and write canonical files automatically.
- **Conflicting:** The current flow explicitly opens files in an editor (`authoring.try_open_in_editor`) and supports manual edits (e.g., `preliminary_draft.md`, `spec_v2_fields.md`, embedded entries). This is contrary to “no manual creation or editing.”
- **Implication:** The authoring flow must disable editor prompts and manual entry modes.

### 2) `bp author` should only offer three options
**Status:** **Partial**
- **Existing pieces:**
  - “Create a single character from a schema” is already implemented as schema authoring (`_run_author_schema`) with a single file input.
  - “Create schemas from file” is **not** a current option; there is no generator that reads an input file to produce multiple schemas.
  - “Create several characters from a folder” is **not** present; `_run_author_schema` handles one file at a time.
- **Implementation gap:** Add a folder-driven batch mode and a “generate schemas from file” mode.

### 3) Single confirmation after elaboration, then auto-build
**Status:** **Partial**
- **Partial:** There is a confirmation prompt flow in `_run_author` (for selecting sections, prompt templates, etc.).
- **Missing:** The flow still requests user decisions for extraction and embedded entries, and requires manual `bp build` invocation. No automatic build is triggered.
- **Change required:** Collapse prompts to a single post-elaboration confirmation and run `bp build` automatically afterward.

### 4) Embedded items auto-generated from a schema header transform
**Status:** **Missing**
- **Current behavior:** Embedded entries can be created from manual prompts or LLM output, or via per-entry authoring.
- **Requested behavior:** The minimum schema includes a header field describing embedded-entry “transform idiosyncrasies,” but the system should always auto-generate **2–4 random entries** from canonical domains (knowledge, ideology, relationship, etc.).
- **Gap:** No existing field in the minimal schema controls embedded-entry transforms, and the count is not randomized/hard-coded.

### 5) Slug removed from schema; system assigns slug + timestamp code
**Status:** **Missing**
- **Current behavior:** Slug is required in the staging draft schema (`parse_minimal_staging_draft`) and validated in `authoring.validate_slug`.
- **Requested behavior:** Slug should be removed from the schema entirely, and auto-generated with a timestamp-based suffix to avoid collisions.
- **Implication:** Authoring must generate slug from display name (or concept) + suffix, and remove slug input from the schema.

### 6) Add “prose variant” for spec_v2 (schema-like vs hybrid)
**Status:** **Missing / partial**
- **Partial:** “Variants” exist, but they are narrative deltas applied to canonical specs. They are not distinct “prose variants” of the base schema prompt.
- **Missing:** There is no distinct selection or template family for “schema-like” vs “hybrid” in `spec_v2` generation.
- **Change required:** Add a choice or default for prose variant, and ensure it drives the schema prompt (or embedded content) in deterministic authoring output.

---

## Contradictions to reconcile
- **Random embedded entry count** vs **deterministic outputs**: The repository’s compiler behavior is deterministic. A random count would violate that unless the random source is fixed (e.g., seeded by slug or build hash). This must be reconciled.
- **No manual edits** vs **existing manual scaffolds**: Current docs and tooling explicitly support manual edits. The new requirement implies removing or bypassing editor prompts and manual content files.

---

## Required documentation updates
- **Minimum schema document** should:
  - Remove slug field.
  - Add embedded-entry transform header.
  - Add prose variant selection (schema-like/hybrid).
  - Explain the new single-pass authoring flow.

The next section provides the new combined “minimum schema + manifest” draft.
