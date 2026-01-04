# Codex Directive: Static Character Creation
## 0) Implementation Order and Branch Discipline
- This directive must be implemented before 02_variant_pipeline_human_llm.md.
- Do not begin 02_variant_pipeline_human_llm.md until this directive is merged and tests pass.
- LOCKED until later directives:
  - `sources/characters/<slug>/variants/**`
  - `sources/characters/<slug>/fragments/**`
  - `src/generator.py::_build_variant_fragments`
  - `src/authoring.py::write_run_log`

## 1) Objective
- Preserve the deterministic build contract in `src/generator.py::build_site_data` while clarifying the static authoring inputs it consumes.
- Document and enforce stable on-disk conventions under `sources/characters/<slug>/canonical/` for spec_v2 input fields.
- Ensure `dist/src/data/index.json` and `dist/src/data/characters/<slug>/manifest.json` are emitted consistently and auditable.
- Capture the repo’s deterministic guarantees (no LLM calls in build; byte-stable outputs) in code comments/tests without behavior changes.
- Align documentation with the Interconnected Systems Overview (`docs/Interconnected_Systems_Overview.md`).

## 2) Non-goals
- Do not change or re-vendor any schemas under `schemas/`.
- Do not add LLM calls or runtime interactivity to the build.
- Do not introduce new variant or fragment semantics (reserved for later directives).
- Do not modify site UI or any runtime consumer of `dist/`.

## 3) Current State Summary (Repo-grounded)
- Deterministic build is implemented in `src/generator.py::build_site_data`, which reads `sources/site-seed/index.json` and `sources/characters/*/manifest.json` plus authored canonical fields from `sources/characters/<slug>/canonical/spec_v2_fields.md` via `_load_authored_manifest`.
- Content fragments are emitted by `src/generator.py::_build_fragment_files`, which writes persona/scenario/system_prompt/lore/examples/greetings into `dist/src/data/characters/<slug>/fragments/` and ensures a `.keep` placeholder when empty.
- Authoring scaffolds are created by `src/authoring.py::scaffold_character`, which lays out `canonical/`, `variants/`, `fragments/`, and `runs/` folders, plus `meta.yaml`.
- The CLI build entry point is `src/cli.py` (`bp build`) and delegates to `build_site_data`.
- Determinism and schema compliance are enforced in `tests/test_build_pipeline.py::test_build_reproducibility` and `tests/test_build_pipeline.py::test_schema_compliance`.

## 4) Deliverables
- Documentation updates (likely in `README.md` or a new `docs/` page) that clarify deterministic static inputs and the stable folder conventions for canonical spec_v2 fields.
- Any helper refactors in `src/generator.py` that improve auditability without changing emitted outputs (e.g., explicit comments, clearer helper boundaries).
- A short, repo-grounded note referencing `docs/Interconnected_Systems_Overview.md` as the conceptual baseline.

## 5) Task Checklist (Itemized, Markable)
- [ ] Document the canonical authoring directory layout and required files under `sources/characters/<slug>/canonical/` in `README.md` (or a new doc under `docs/`).
- [ ] Add code comments in `src/generator.py::build_site_data` and `_load_authored_manifest` reinforcing determinism and schema boundaries.
- [ ] Add or update a small audit/validation helper (if needed) without changing build output; keep diffs additive and reviewable.
- [ ] Reference `docs/Interconnected_Systems_Overview.md` in the new/updated documentation.

## 6) Acceptance Criteria
- Determinism conditions:
  - `bp build` produces byte-identical `dist/src/data` for identical inputs, matching `tests/test_build_pipeline.py::test_build_reproducibility`.
  - No LLM or network calls are introduced into build paths.
- What to run:
  - `bp build` (or `python -m src.generator`) on a clean workspace.
  - `pytest tests/test_build_pipeline.py`.
  - Verify outputs: `dist/src/data/index.json`, `dist/src/data/characters/<slug>/manifest.json`, and `dist/src/data/characters/<slug>/fragments/.keep` when empty.
- Expected console behavior:
  - Build remains quiet unless errors occur; report at `dist/REPORT.md` is updated as today.

## 7) Tests
- Existing tests that must continue to pass:
  - `tests/test_build_pipeline.py` (reproducibility, schema compliance, contract completeness).
  - `tests/test_generator_features.py` (site-only field behavior).
- New tests to add (if any):
  - `tests/test_authoring_layout.py` to assert canonical folder expectations (reads only; no build output changes).
  - Fixtures: use `tests/fixtures` or `tmp_path` to create minimal `sources/characters/<slug>/canonical/spec_v2_fields.md`.
- Any added test dependencies must go in `requirements-test.txt` only.

## 8) Risks and Pitfalls
- Accidentally changing emitted JSON (key ordering, timestamps, or formatting) when refactoring helpers.
- Introducing schema-adjacent fields outside of the `x` extension block.
- Modifying `sources/characters/<slug>/variants/` or fragments behavior prematurely (reserved for later directives).
- Allowing placeholder data to leak into real entries.
- Over-documenting features that are not yet implemented (keep scope aligned with current code).

## 9) Migration / Backwards Compatibility Notes
- Existing authored characters remain valid; canonical `spec_v2_fields.md` continues to override/merge with `manifest.json` via `_load_authored_manifest`.
- Partial or draft authoring data should continue to emit warnings (not hard errors) unless audit strictness is explicitly enabled.
- Build should ignore missing variant/fragments authoring inputs until later directives implement them.
