# Codex Directive: Variant Pipeline (Human + LLM Authoring)
## 0) Implementation Order and Branch Discipline
- This directive must be implemented before 03_embedded_entries_variant_elements.md.
- Do not begin 03_embedded_entries_variant_elements.md until this directive is merged and tests pass.
- LOCKED until later directives:
  - `src/generator.py::_build_fragment_files`
  - `src/generator.py::_build_variant_fragments` (behavior changes; use only for documentation references here)
  - `sources/characters/<slug>/fragments/**`
  - `sources/world/**`

## 1) Objective
- Define “variant as delta” authoring rules that are human- and LLM-friendly while remaining deterministic at build time.
- Extend authoring documentation to describe variant seed phrases and prompt-family usage (Tone/Voice/Style) without changing build output semantics.
- Establish a concrete on-disk layout under `sources/characters/<slug>/variants/<variant_name>/` for variant inputs.
- Require provenance logging for all variant authoring runs (prompt hash, model params, input hash, output hash).
- Preserve the separation between authoring-time LLM usage and build-time determinism.
- Align variant terminology with `docs/Interconnected_Systems_Overview.md` so cross-system language remains consistent.

## 2) Non-goals
- Do not add LLM dependencies or calls to `bp build` or `src/generator.py`.
- Do not modify schema files or introduce new schema fields.
- Do not change how `dist/src/data` is emitted in this phase.
- Do not emit variant fragments into `dist/` beyond what is already deterministic.

## 3) Current State Summary (Repo-grounded)
- Authoring CLI (`src/cli.py::main`) already supports LLM-assisted `bp author` runs with prompt category selection for tone/voice/style.
- Prompt templates live under `prompts/` with categories (`prompts/tone/`, `prompts/voice/`, `prompts/style/`) and are selected by filename in `src/cli.py::_select_prompt`.
- Provenance logging exists via `src/authoring.py::write_run_log`, which writes `runs/<run_id>/prompt_ref.txt`, `model.json`, `input_hash.txt`, and `output.md`.
- Variant files are already referenced by the build pipeline: `src/generator.py::_build_variant_fragments` copies `sources/characters/<slug>/variants/<style>/spec_v2_fields.md` into `dist/src/data/characters/<slug>/fragments/variants/<style>/spec_v2_fields.md` and records them under `manifest.x.variants`.

## 4) Deliverables
- Documentation describing the variant-as-delta contract and authoring flow, including directory layout and provenance requirements.
- A proposed prompt-family matrix (Tone/Voice/Style) and variant seed phrase storage format under `sources/characters/<slug>/variants/<variant_name>/`.
- Updated audit guidance clarifying that variants are authored pre-build and included deterministically.

## 5) Task Checklist (Itemized, Markable)
- [ ] Define variant folder layout in docs: `sources/characters/<slug>/variants/<variant_name>/spec_v2_fields.md`, `seed_phrase.txt`, `notes.md`, and `runs/<run_id>/`.
- [ ] Specify that `spec_v2_fields.md` contains only delta fields for the variant (no full spec).
- [ ] Document the Tone/Voice/Style prompt-family pipeline and how each contributes to variant deltas.
- [ ] Extend authoring run documentation to require prompt hashing and model/config capture for variant runs (reuse `authoring.write_run_log`).
- [ ] Add/extend audit documentation to ensure variant directories are optional and validated only if present.

## 6) Acceptance Criteria
- Determinism conditions:
  - `bp build` output remains unchanged for existing inputs (variant authoring is pre-build and deterministic once written).
  - No new runtime dependencies are required for build.
- What to run:
  - `bp author` (variant authoring workflow, documented but not required for build).
  - `bp build` (ensure deterministic output is unchanged).
- Expected console behavior:
  - Authoring logs remain under `sources/characters/<slug>/runs/` (quiet unless errors).

## 7) Tests
- Existing tests that must continue to pass:
  - `tests/test_authoring.py` (authoring scaffolds and run logs).
  - `tests/test_build_pipeline.py` (reproducibility and schema compliance).
- New tests to add:
  - `tests/test_variants_layout.py` verifying optional variant directory discovery and that missing variants do not error.
  - Fixtures: minimal `sources/characters/<slug>/variants/<variant_name>/spec_v2_fields.md` with delta JSON block.
- Any added test dependencies must go in `requirements-test.txt` only.

## 8) Risks and Pitfalls
- Treating variants as full manifests instead of deltas (breaks intent and increases drift).
- Failing to capture prompt/model hashes, making variant provenance non-auditable.
- Allowing variant layout to collide with canonical inputs.
- Introducing build-time behavior changes inadvertently while updating docs.
- Unclear naming conventions that lead to duplicate or ambiguous variant directories.

## 9) Migration / Backwards Compatibility Notes
- Existing characters without variants remain valid and should continue to build.
- Any new variant directories are optional; build should ignore missing or empty variant folders.
- Variant deltas should not override canonical fields unless explicitly merged during authoring review (build remains deterministic).
