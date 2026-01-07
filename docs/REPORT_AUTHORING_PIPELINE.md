# Authoring Pipeline Verification Report

## Verification summary
- **bp author entrypoint**: `src/cli.py` (`main()` → `_run_author`) orchestrates the interactive authoring flow.
- **Authoring helpers**: `src/authoring.py` provides scaffolding, prompt template discovery, run logging, and parsing helpers.
- **Prompt template loading**: `_select_prompt()` in `src/cli.py` lists templates via `authoring.list_prompt_templates()` from `prompts/<category>/` and selects by filename.
- **Run logs + provenance**: `authoring.write_run_log()` writes:
  - `prompt_ref.txt` (template path + sha256)
  - `prompt_compiled.md` (fully assembled prompt sent to the model)
  - `model.json` (model name + params)
  - `input_hash.txt` (hash of input payload)
  - `output.md` (raw model output)
- **Variant authoring**: variant runs reuse `authoring.write_run_log()` under
  `sources/characters/<slug>/variants/<variant_name>/runs/<run_id>/` to capture prompt hashes,
  model/config, input hash, and output text.
- **Elaboration output**: `_run_author` writes elaboration output to `sources/characters/<slug>/preliminary_draft.md` (overwrite).
- **Extraction output**: `_run_author` reads `preliminary_draft.md`, extracts sections, and writes:
  - `sources/characters/<slug>/canonical/spec_v2_fields.md`
  - `sources/characters/<slug>/canonical/shortDescription.md`

## Files/entrypoints involved
- **CLI**: `src/cli.py` (`bp author`, `bp audit`, `bp build`)
- **Authoring module**: `src/authoring.py` (scaffold, prompt discovery, run logs, output parsing)
- **Prompt templates**: `prompts/elaborate/01_elaborate_v1.md`, `prompts/extract_fields/01_specv2_fields_v1.md`
- **Canonical output consumption**: `src/generator.py::_load_authored_manifest` reads `canonical/spec_v2_fields.md` and `canonical/shortDescription.md`
- **Variant output consumption**: `src/exporter.py::export_character_bundle` applies
  `variants/<variant_name>/spec_v2_fields.md` to emit `dist/src/export/characters/<slug>/variants/<variant_name>/spec_v2.*.json`

## Missing pieces found and minimal changes applied
1. **Missing prompt_compiled.md in run logs**
   - Added `prompt_compiled.md` writing in `authoring.write_run_log()`.
   - Added prompt compilation in `_run_author` that concatenates template + labeled input.
2. **Prompt templates were placeholders**
   - Replaced both templates with full, requirement-compliant prompt text.
3. **Extraction stub did not emit JSON**
   - Adjusted the authoring stub to emit a minimal JSON object plus `---SHORT_DESCRIPTION---` marker during extraction.

## Checklist verification
- ✅ Prompt template selection by filename from `prompts/` is implemented in `_select_prompt()`.
- ✅ Compiled prompt is written to `runs/<run_id>/prompt_compiled.md`.
- ✅ `prompt_ref.txt` includes template path + SHA256 hash.
- ✅ `model.json`, `input_hash.txt`, and `output.md` are written per run.
- ✅ `preliminary_draft.md` is updated after elaboration (overwrite behavior).
- ✅ Extraction reads `preliminary_draft.md` and writes canonical outputs.
- ✅ Deterministic build does not call LLM code (authoring is isolated in CLI).
- ✅ Tests remain scoped; only adjusted existing tests to align with new logging.
