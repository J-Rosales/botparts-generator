# Codex Directive: Scope Layer System (Narrative Bounding)
## 0) Implementation Order and Branch Discipline
- This directive must be implemented before final rollout (no subsequent directive file).
- Do not begin final rollout until this directive is merged and tests pass.
- LOCKED until this directive:
  - `sources/world/**` (new world packs live here)
  - `src/generator.py` changes that route fragments by scope

## 1) Objective
- Introduce explicit scope layers: World Canon, Character Canon, Variant Delta.
- Define a deterministic labeling mechanism (frontmatter tags or JSON sidecars) to route content by scope.
- Add promotion gates so world-level changes require explicit intent/approval, keeping default variant generation local.
- Provide a shared world-pack input path under `sources/world/` that can be used across multiple characters without duplication.
- Ensure build behavior handles missing world packs gracefully (non-fatal unless strict mode is enabled).
- Align scope-layer terminology with `docs/Interconnected_Systems_Overview.md`.

## 2) Non-goals
- Do not modify any schemas or add new schema fields outside `x` extensions.
- Do not introduce runtime interaction or LLM calls during build.
- Do not add UI or site-consumer logic.
- Do not restructure existing canonical/variant inputs beyond additive labeling.

## 3) Current State Summary (Repo-grounded)
- No world-level inputs exist today; build reads only `sources/site-seed/index.json` and per-character sources in `sources/characters/` via `src/generator.py::build_site_data`.
- Fragments are emitted strictly per character from `content` fields in `_build_fragment_files` and variants in `_build_variant_fragments`.
- Authoring scaffolds (`src/authoring.py::scaffold_character`) create per-character `fragments/` and `variants/` directories, but there is no scope labeling yet.

## 4) Deliverables
- A documented scope labeling format (e.g., YAML frontmatter with `scope: world|character|variant`) for fragment files.
- A `sources/world/<pack>/` layout for shared world canon inputs, with deterministic emission into `dist/src/data/fragments/world/` (or similar) without schema changes.
- Build-time routing logic that places fragments in the correct output namespace and includes scope metadata under `manifest.x`.
- A “promotion gate” rule: world-scoped entries require an explicit opt-in file (e.g., `sources/world/<pack>/PROMOTE.md` or `meta.yaml` flag).

## 5) Task Checklist (Itemized, Markable)
- [ ] Define world-pack directory structure and required files under `sources/world/<pack>/`.
- [ ] Specify scope labeling format for fragment files (frontmatter tags or JSON sidecars), including validation rules.
- [ ] Update `src/generator.py` to discover world packs, route outputs by scope, and default to non-fatal behavior when packs are missing.
- [ ] Add promotion gate logic (explicit approval file/flag) to allow world-scoped content into output.
- [ ] Update documentation and audit guidance to explain scope layers and shared world packs.

## 6) Acceptance Criteria
- Determinism conditions:
  - World pack discovery and routing are deterministic (sorted traversal; stable outputs).
  - Missing `sources/world/` does not fail builds unless strict mode is enabled.
- What to run:
  - `bp build` (with and without `sources/world/` present).
  - `pytest tests/test_build_pipeline.py`.
  - Verify outputs: world fragments emitted under the documented output namespace and referenced via `manifest.x`.
- Expected console behavior:
  - Build remains quiet unless errors occur; promotion gate failures are warnings (or errors in strict mode).

## 7) Tests
- Existing tests that must continue to pass:
  - `tests/test_build_pipeline.py`.
- New tests to add:
  - `tests/test_scope_layers.py` verifying scope labeling, world pack discovery, and promotion gate behavior.
  - Fixtures: `sources/world/example-pack/` with labeled fragments; character sources that reference world packs.
- Any added test dependencies must go in `requirements-test.txt` only.

## 8) Risks and Pitfalls
- Blurring scope boundaries and accidentally promoting variant content to world canon.
- Introducing breaking changes for characters without world packs.
- Non-deterministic ordering of world pack entries.
- Overloading `manifest.x` with conflicting keys.
- Failing to implement promotion gates, resulting in unintended global changes.

## 9) Migration / Backwards Compatibility Notes
- Existing characters and sources remain valid without world packs.
- World pack adoption is opt-in and additive; no required changes to existing characters.
- Partial world pack data should be ignored unless promotion gates are satisfied.
