# Codex Directive: Embedded Entries Authoring Modes
## 0) Implementation Order and Branch Discipline
- This directive depends on 03_embedded_entries_variant_elements.md and must be implemented after it.
- Do not begin any further authoring-flow directives until this directive is merged and tests pass.
- LOCKED until later directives:
  - Schema changes (no schema edits allowed).
  - Build-time LLM invocation (authoring-only).

## 1) Objective
- Replace Step 7 of the `bp author` flow with three explicit embedded-entry paths:
  1. **Automatically**: generate a bounded, random amount of items using a single LLM query, stored in markdown.
  2. **From Input Prompt**: accept `name: description` inputs to generate entries via LLM for each item.
  3. **Skip**: do not add embedded items.
- Ensure every generated entry still writes a fragment file via `authoring.write_embedded_entry(...)`.
- Keep the process deterministic on disk and audit-friendly by storing LLM prompts and outputs.

## 2) Non-goals
- Do not modify schemas or introduce new schema fields outside existing `x` usage.
- Do not alter build-time generator behavior (no LLM in `src/generator.py`).
- Do not introduce interactive UI beyond CLI prompts in `bp author`.
- Do not change embedded entry storage locations defined in Directive 03.

## 3) Current State Summary (Repo-grounded)
- Embedded entries are currently gathered with count-based prompts in `src/cli.py::_prompt_embedded_entries`.
- Each entry asks for title, slug, description, and optional score, then writes via `src/authoring.py::write_embedded_entry`.
- Entry types are defined in `src/generator.py::EMBEDDED_ENTRY_TYPES`.
- LLM prompt usage exists elsewhere in `src/cli.py` for elaboration/extraction steps.

## 4) Deliverables
- A new embedded-entry prompt mode selector in `bp author` for: Automatically, From Input Prompt, Skip.
- Automatic mode:
  - One LLM call produces entries across all `EMBEDDED_ENTRY_TYPES`.
  - The compiled prompt and raw LLM response are stored in markdown in the current run log directory.
  - Enforce bounded counts per type (reuse existing max=10 unless changed here).
- From Input Prompt mode:
  - Per entry type, read repeated `name: description` lines from the user.
  - Commands:
    - `CONTINUE` → move to next entry within the same type.
    - `NEXT` → move to the next entry type.
  - Each line triggers an LLM call that produces title, slug, description, and optional score.
- Skip mode: no entries are added; move directly to audit.
- All modes still call `authoring.write_embedded_entry(...)` for each generated entry.

## 5) Task Checklist (Itemized, Markable)
- [ ] Add a mode selector to `src/cli.py` to choose Automatic, From Input Prompt, or Skip.
- [ ] Implement Automatic mode:
  - [ ] Define a prompt template in `prompts/` (new category, e.g., `embedded_entries_auto/`).
  - [ ] Compile a single prompt that requests bounded counts for each entry type.
  - [ ] Persist prompt + response in `sources/characters/<slug>/runs/<run_id>/embedded_entries_auto.md`.
  - [ ] Parse response into structured entries per type and write via `authoring.write_embedded_entry(...)`.
- [ ] Implement From Input Prompt mode:
  - [ ] Add a line-based input loop per entry type in `src/cli.py`.
  - [ ] Parse `name: description` lines; reject invalid lines with a clear error.
  - [ ] Map `CONTINUE` and `NEXT` commands to control flow.
  - [ ] For each line, call the LLM with a per-entry prompt template in `prompts/embedded_entries_from_input/`.
  - [ ] Persist prompt + response per entry under `sources/characters/<slug>/runs/<run_id>/embedded_entries_from_input/`.
- [ ] Add parsing/validation helpers to `src/authoring.py` or `src/cli.py` for LLM response safety.
- [ ] Update `docs/` or `PROJECT.md` with the revised Step 7 description.

## 6) Acceptance Criteria
- Determinism conditions:
  - Written entry files are stable and sorted by slug within each type.
  - LLM prompt/response logs are saved deterministically under the run directory.
- User-flow behavior:
  - Automatic mode generates entries for each type without further prompts.
  - From Input Prompt mode honors `CONTINUE` and `NEXT`.
  - Skip mode bypasses entry creation and continues the pipeline.
- No schema edits or build-time LLM usage.

## 7) Tests
- Existing tests that must continue to pass:
  - `tests/test_build_pipeline.py`.
- New tests to add:
  - `tests/test_authoring_embedded_entries.py` covering:
    - Mode selection routing.
    - Parsing `name: description`, `CONTINUE`, and `NEXT`.
    - Bounded entry counts in Automatic mode.
  - Fixtures: a minimal character run directory with stored prompts/responses.

## 8) Risks and Pitfalls
- LLM response parsing ambiguity; must validate required fields (title, slug, description).
- Over-generation (exceeding bounds) must be trimmed deterministically.
- User input edge cases: blank lines, missing colon, repeated slugs.
- Failing to log prompts/responses makes audits harder.

## 9) Migration / Backwards Compatibility Notes
- Existing character sources remain valid; this change only affects `bp author` prompts.
- Older runs without embedded entry logs remain acceptable.
