# Codex Directive: Variant Authoring From Staging Drafts
## 0) Implementation Order and Branch Discipline
- This directive must be implemented after 02_variant_pipeline_human_llm.md.
- Do not modify `src/generator.py` output semantics for variants; build remains deterministic and unchanged.
- LOCKED until later directives:
  - `src/generator.py::_build_fragment_files`
  - `src/generator.py::_build_variant_fragments` (behavior changes; use only for documentation references here)
  - `sources/characters/<slug>/fragments/**`
  - `sources/world/**`

## 1) Objective
- Implement an authoring workflow for **creating character variants** inside `bp author`.
- Drive variant selection from `sources/staging_drafts.md`:
  - `###` headers choose a **variant group**.
  - `####` headers under the chosen `###` define **variant names**.
  - The prose under each `####` is the **variant description** prompt.
- Produce variant deltas under `sources/characters/<slug>/variants/<variant_name>/spec_v2_fields.md`.
- Open generated draft deltas in VS Code for manual edits and pause execution until the user confirms.
- Apply delta schemas to the canonical character to emit variant fragments (embedded entries, etc.).
- Deprecate `seed_phrase.txt` for variant authoring in this workflow.

## 2) Non-goals
- Do not add LLM calls to `bp build` or `src/generator.py`.
- Do not change schemas or add new schema fields.
- Do not emit any new `dist/` outputs beyond existing deterministic behavior.
- Do not require seed phrases; any existing `seed_phrase.txt` remains optional and ignored.

## 3) Current State Summary (Repo-grounded)
- `src/authoring.py::scaffold_character` already creates a `variants/` directory per character.
- `src/generator.py::_build_variant_fragments` copies `variants/<variant_name>/spec_v2_fields.md` into `dist/src/data/characters/<slug>/fragments/variants/<variant_name>/spec_v2_fields.md` and records `manifest.x.variants`.
- `bp author` currently supports canonical authoring but does not create variants.
- `authoring.write_run_log` exists for provenance logging of LLM runs.
- Prompt templates for variants exist under `prompts/rewrite_variants/`.

## 4) Deliverables
- A new `bp author` workflow: **Create character variants**.
- Variant discovery and prompting based on `###` and `####` headers in `sources/staging_drafts.md`.
- Variant delta draft generation per variant, with manual edit pause (VS Code).
- Deterministic application of deltas to produce variant fragments and embedded entries.
- Provenance logging for each variant LLM run under `sources/characters/<slug>/variants/<variant_name>/runs/<run_id>/`.
- Documentation updates clarifying deprecation of `seed_phrase.txt` for this workflow.

## 5) Workflow Details
### 5.1 Prompting and Selection
- Prompt user to choose an existing character slug.
- Load `sources/staging_drafts.md` and parse all `###` headers.
- User selects a `###` header (variant group).
- Find all `####` headers within that section.
- Each `####` title becomes `variant_name` (slugified, validated).
- The text under each `####` becomes the **variant description** prompt.

### 5.2 LLM Draft Generation
- For each variant:
  - Compile a prompt that includes:
    - Canonical card (from `sources/characters/<slug>/canonical/spec_v2_fields.md`).
    - Variant description (natural language).
  - Generate a **delta-only** `spec_v2_fields.md`.
  - Store draft at `sources/characters/<slug>/variants/<variant_name>/spec_v2_fields.md`.
  - Log run details with `authoring.write_run_log`.

### 5.3 Manual Edit Pause
- Open each draft file in VS Code using `authoring.try_open_in_editor`.
- Pause execution until user confirms edits (`input("Press enter once draft edits are saved...")`).

### 5.4 Delta Application
- Parse the delta schema and apply it to the canonical character to determine:
  - Variant-specific fragment changes.
  - Variant-specific embedded entries (locations/items/knowledge/ideology/relationships).
- Write any required variant fragment files under:
  - `sources/characters/<slug>/variants/<variant_name>/spec_v2_fields.md` (delta)
  - `sources/characters/<slug>/fragments/entries/**` (if variant authoring creates embedded entries to reuse).

## 6) Acceptance Criteria
- New `bp author` option exists and runs end-to-end without touching build logic.
- Variant delta files are created from `####` descriptions and logged with run metadata.
- Manual edit pause opens drafts in VS Code and blocks until confirmation.
- Delta application produces variant fragments deterministically.
- `seed_phrase.txt` is not required or written by this workflow.

## 7) Tests
- Add tests that:
  - Parse `sources/staging_drafts.md` for `###` and `####` headers.
  - Verify variant directories are created under `sources/characters/<slug>/variants/<variant_name>/`.
  - Ensure delta drafts are opened for manual edits (mock editor) and preserved.
  - Confirm `authoring.write_run_log` is invoked for variants.
- Existing build tests must continue to pass.

## 8) Risks and Pitfalls
- Mis-parsing markdown headers (ensure robust section boundary handling).
- Variant naming collisions or invalid slugs from header titles.
- Merging delta fields incorrectly into canonical data.
- Accidentally requiring `seed_phrase.txt` or older variant layouts.
- Generating non-delta payloads (full canonical cards) for variants.

## 9) Migration / Backwards Compatibility Notes
- Existing `variants/` directories and `seed_phrase.txt` files remain valid and are not deleted.
- Characters without variants remain valid and continue to build.
- Variant authoring remains a pre-build, deterministic workflow; `bp build` consumes outputs as-is.
