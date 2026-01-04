# Codex Directive: Embedded Entries as Variant Elements
## 0) Implementation Order and Branch Discipline
- This directive must be implemented before 04_scope_layers_narrative_bounding.md.
- Do not begin 04_scope_layers_narrative_bounding.md until this directive is merged and tests pass.
- LOCKED until later directives:
  - `sources/world/**`
  - Any global scope routing logic in `src/generator.py` (reserved for Directive 04)

## 1) Objective
- Define deterministic, on-disk representations for embedded entries (locations, items, knowledge, ideology, relationships) as variant consequences.
- Ensure embedded entries are stored under `sources/characters/<slug>/fragments/` in a normalized, audit-friendly layout.
- Extend generator inventory logic to emit embedded entries as fragments without modifying schemas.
- Add guardrails against combinatorial explosion (limits, naming conventions, and “only include if exists” rules).
- Maintain deterministic output rules and keep all build-time logic free of LLM calls.
- Use `docs/Interconnected_Systems_Overview.md` as the conceptual baseline for embedded-entry terminology.

## 2) Non-goals
- Do not change schema files or the manifest schema structure.
- Do not introduce any runtime LLM generation during build.
- Do not merge or interpret variant deltas beyond deterministic file discovery.
- Do not implement world-level scope routing (reserved for Directive 04).

## 3) Current State Summary (Repo-grounded)
- The build emits fragments based on canonical `content` fields in `src/generator.py::_build_fragment_files` (persona, scenario, system_prompt, lore, examples, greetings).
- Variant fragments are currently limited to copying `spec_v2_fields.md` into `dist/src/data/characters/<slug>/fragments/variants/<style>/` via `src/generator.py::_build_variant_fragments`.
- Authoring scaffolds include `sources/characters/<slug>/fragments/` with a `.keep` placeholder (`src/authoring.py::scaffold_character`).
- Contract completeness tests require fragments directories to exist and be non-empty (`tests/test_build_pipeline.py::test_contract_completeness`).

## 4) Deliverables
- A documented on-disk layout for embedded entries under `sources/characters/<slug>/fragments/entries/<type>/` (e.g., `locations/`, `items/`, `knowledge/`, `ideology/`, `relationships/`).
- Generator logic to inventory these entries and emit deterministic fragment references under `dist/src/data/characters/<slug>/fragments/` (without schema changes).
- Guardrail rules (max entries per type, naming conventions, and deterministic sorting).

## 5) Task Checklist (Itemized, Markable)
- [x] Define file format for embedded entries (e.g., Markdown with YAML frontmatter or JSON) under `sources/characters/<slug>/fragments/entries/<type>/<entry_slug>.md`.
- [x] Update `src/generator.py` to copy embedded entry files into `dist/src/data/characters/<slug>/fragments/entries/...` with stable ordering and a `.keep` placeholder where appropriate.
- [x] Add a manifest extension under `manifest.x` to list embedded entry fragment paths (no schema changes; keep in `x`).
- [x] Add guardrails: max entries per type, allowed filename pattern, and skip rules for empty/missing directories.
- [x] Update audit documentation to explain embedded entry expectations and optionality.

## 6) Acceptance Criteria
- Determinism conditions:
  - Embedded entries are copied in sorted order with byte-stable outputs.
  - Builds remain reproducible per `tests/test_build_pipeline.py::test_build_reproducibility`.
- What to run:
  - `bp build` or `python -m src.generator`.
  - `pytest tests/test_build_pipeline.py`.
  - Verify outputs: `dist/src/data/characters/<slug>/fragments/entries/<type>/` exists when authored, includes `.keep` when empty.
- Expected console behavior:
  - Build remains quiet unless errors occur; warnings (if any) are reported via `dist/REPORT.md`.

## 7) Tests
- Existing tests that must continue to pass:
  - `tests/test_build_pipeline.py`.
  - `tests/test_generator_features.py`.
- New tests to add:
  - `tests/test_embedded_entries.py` verifying fragment discovery, sorting, and path emission under `manifest.x`.
  - Fixtures: minimal embedded entries under `sources/characters/<slug>/fragments/entries/locations/` and `items/`.
- Any added test dependencies must go in `requirements-test.txt` only.

## 8) Risks and Pitfalls
- Overloading existing fragment keys and breaking schema validation.
- Non-deterministic filesystem traversal (must sort directory entries).
- Naming collisions across embedded entry types.
- Excessive entry counts leading to large outputs; enforce limits.
- Failing to include `.keep` placeholders for empty directories.

## 9) Migration / Backwards Compatibility Notes
- Characters without embedded entries remain valid and should build without errors.
- Embedded entries are additive; existing fragment outputs remain unchanged unless new files are authored.
- Missing fragment directories should be treated as “no entries” rather than a build failure.
