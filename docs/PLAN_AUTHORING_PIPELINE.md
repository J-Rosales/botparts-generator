# Authoring + Deterministic Build Pipeline Plan (Codex Directive)

This plan defines an **interactive, LLM-assisted authoring tool** and a **deterministic build pipeline** that remain consistent with the existing botparts-generator architecture and tests. The plan is designed to be executed step-by-step by a future Codex run.

> Repo conventions observed:
> - Deterministic build is implemented in `src/generator.py` (see `build_site_data` + CLI `main()`).
> - Build outputs in `dist/src/data/` are validated by `tests/test_build_pipeline.py` and include `index.json`, `characters/<slug>/manifest.json`, and `fragments/` placeholders.
> - `dist/REPORT.md` is emitted and asserted in `tests/test_build_pipeline.py`.
> - Placeholder profiles are controlled by `--placeholders` / `BOTPARTS_PLACEHOLDERS` and timestamps by `--include-timestamps` / `BOTPARTS_INCLUDE_TIMESTAMPS`.

---

## 1) Goals and Non-goals

**Goals**
- Add an **interactive authoring CLI** (LLM-assisted, local-only) that writes **static, reviewable inputs** under `sources/`.
- Keep **deterministic build** behavior isolated and unchanged in `src/generator.py`.
- Add **provenance logging** for authoring runs (prompt hash, model params, input/output hashes).
- Enable **scalable character authoring** with a consistent folder scaffold.

**Non-goals**
- No changes to schemas under `schemas/` (vendored).
- No changes to site code or runtime LLM usage.
- No new UI frameworks or interactive runtime behavior.
- No modification to existing deterministic build logic during authoring tool introduction.

---

## 2) Proposed CLI surface (commands + flags)

### Commands
- `bp author` — interactive authoring menu (LLM-assisted, local-only).
- `bp build` — deterministic build (wraps or aliases existing `src/generator.py` CLI).
- `bp audit` — validates authored sources without building (fast checks + optional schema validation).

> TODO: Inspect how CLI entrypoints are wired today (e.g., `scripts/build-site-data.ps1` and any packaging config) before adding a new command runner.

### Flags / env vars
- **API key input method (env-only):**
  - `BOTPARTS_LLM_API_KEY` (required for authoring LLM calls; *no CLI flags* for secrets).
- **Placeholders (existing):**
  - `--placeholders` / `BOTPARTS_PLACEHOLDERS` remain **build-only** (never authoring).
- **Timestamps (existing):**
  - `--include-timestamps` / `BOTPARTS_INCLUDE_TIMESTAMPS` (build only; default off) controls timestamps in `dist/REPORT.md` and `dist/src/data/index.json`.

---

## 3) Data model and on-disk layout (authoring inputs)

### Canonical layout (new authoring inputs)
```
sources/characters/<slug>/
  meta.yaml
  staging_snapshot.md
  preliminary_draft.md
  canonical/
    spec_v2_fields.md
    shortDescription.md
  variants/
    <style>/
      spec_v2_fields.md
  fragments/                # future authored fragments, not used in build yet
  runs/<run_id>/
    prompt_ref.txt
    model.json
    input_hash.txt
    output.md
```

### Required fields in `meta.yaml`
- `slug` (string, required)
- `displayName` (string, required)
- `status` (enum: `draft`, `review`, `locked`)
- `createdAt` (optional, ISO 8601 string)
- `updatedAt` (optional, ISO 8601 string)
- `source` (optional string or list, provenance notes)

### Staging intake
- `staging_snapshot.md` is **intake-only**. The authoring tool snapshots a chosen heading section from a staging drafts file (see workflow) and writes it here.
- `preliminary_draft.md` is editable by humans before canonical extraction.

> TODO: Confirm current source ingestion expectations in `src/generator.py` and existing sample `sources/characters/example-bot/manifest.json` before wiring `canonical/` into builds.

---

## 4) Authoring workflow: step-by-step flow

### Create character flow
1. **Parse staging drafts**
   - Input file: `sources/staging_drafts.md` (or `sources/staging_drafts/*.md`; confirm naming).
   - Parse headings (`#`, `##`, etc.) to build a concept list.
2. **Prompt for heading name**
   - If not exact match, show top-N fuzzy matches and require numeric selection.
3. **Prompt for slug/package name**
   - Validate uniqueness against `sources/characters/`.
   - Create scaffold at `sources/characters/<slug>/` with required files.
4. **Prompt selection of LLM prompt templates**
   - Prompt templates stored under `prompts/` (see §5).
   - Selection is by filename.
5. **Run LLM elaboration**
   - Write run output to `runs/<run_id>/output.md`.
   - Optionally append or copy to `preliminary_draft.md`.
6. **Manual edit pause**
   - Provide instruction to edit `preliminary_draft.md` before proceeding.
   - CLI pauses and resumes after user confirmation.
7. **Run LLM “field extraction”**
   - Write `canonical/spec_v2_fields.md` and `canonical/shortDescription.md`.
   - Persist run logs under `runs/<run_id>/`.
8. **Run `bp audit character <slug>`**
   - Display errors/warnings.
9. **Export guidance**
   - Authoring never writes to `dist/` directly; recommend running `bp build` for deterministic output.

### `bp author` menu
1. **Create character**
   - Reads: staging drafts file.
   - Writes: scaffold + run logs + preliminary/canonical files.
   - Validations: slug uniqueness, template selection.
2. **Edit character**
   - Reads: `meta.yaml` to show paths.
   - Writes: none (opens file pointers, minimal automation).
3. **Export character**
   - Writes: `.exports/<slug>/` (gitignored) for optional external use.
   - Validations: ensure canonical fields exist.
4. **Duplicate character**
   - Reads: existing `sources/characters/<slug>/`.
   - Writes: new slug folder with updated `meta.yaml`.
5. **Audit character**
   - Reads: `meta.yaml`, `canonical/`, `variants/`.
   - Writes: none (reports issues).
6. **Exit**

---

## 5) LLM prompt templates: structure and versioning

### Directory layout
```
prompts/
  elaborate/
    01_elaborate_v1.md
  extract_fields/
    01_specv2_fields_v1.md
  rewrite_variants/
    01_compact_v1.md
```

### Versioning + provenance
- Selection by filename; file contents are immutable once referenced.
- Store prompt provenance per run:
  - `runs/<run_id>/prompt_ref.txt` → prompt file path + SHA256 hash
  - `runs/<run_id>/model.json` → model name + params
  - `runs/<run_id>/input_hash.txt` → hash of input payload

---

## 6) Deterministic build integration

- **Build consumes authored inputs** from `sources/characters/<slug>/canonical/` as source fields.
- **Variants** (`variants/<style>/spec_v2_fields.md`) are included in manifests (if schema supports) and copied to `dist/src/data/characters/<slug>/fragments/` as deterministic static fragments.
- **Fragments** remain on-disk with placeholders to satisfy the “fragments directory guarantee” validated in `tests/test_build_pipeline.py`.
- **Build must never call LLMs** and must preserve deterministic output (see `tests/test_build_pipeline.py::test_build_reproducibility`).

> TODO: Inspect `src/assemble.py`, `src/emit_spec_v2.py`, and any current source parsing in `src/generator.py` to align how `canonical/` maps to manifest and fragments.

---

## 7) Audit strategy

### `bp audit` checks
- Required files exist (e.g., `meta.yaml`, `canonical/spec_v2_fields.md`).
- `meta.yaml` status gating:
  - `draft` → warnings allowed, but missing canonical fields triggers warning.
  - `locked` → missing canonical fields is an error.
- Canonical fields are non-empty where required.
- Optional: run JSON schema validation for build outputs (consistent with `tests/test_build_pipeline.py::test_schema_compliance`).

### Reporting
- Errors: non-zero exit code, list of file paths + missing fields.
- Warnings: non-zero count but exit code 0 unless `--strict` is provided.

---

## 8) Testing plan (Python tests)

### Authoring tool tests (no LLM calls)
- `test_author_parse_staging` — verifies heading parsing from staging drafts file.
- `test_author_scaffold_creation` — ensures correct directory structure + `meta.yaml` content.
- `test_author_prompt_selection_and_run_log` — uses a mocked LLM call; verifies `runs/<run_id>/` files written.
- `test_audit_validations` — checks error/warning behavior for `draft` vs `locked`.

### Deterministic build tests
- Keep existing reproducibility + schema checks in `tests/test_build_pipeline.py`.
- Add tests to ensure new authoring inputs **do not alter** deterministic output unless explicitly wired.

---

## 9) Implementation sequencing (phased)

**Phase 1: Scaffold + staging snapshot + audit**
- Add `bp author` scaffolding and staging snapshot parsing.
- Add `bp audit` for required-file checks.

**Phase 2: Prompt selection + run logging (LLM stubbed)**
- Add prompt selection by filename.
- Add `runs/<run_id>/` with prompt refs + model.json + input hash.
- LLM call is a stub (no network).

**Phase 3: Integrate actual LLM call (guarded by env var)**
- Enable LLM only when `BOTPARTS_LLM_API_KEY` is present.
- Hard fail if missing when authoring requires LLM.
- Ensure build path does not import LLM modules.

**Phase 4: Variants + fragments manifests**
- Add deterministic mapping of `variants/` into dist fragments and manifests.
- Ensure `dist/src/data/fragments/` and per-character `fragments/` remain non-empty.

**Phase 5: Export tooling (optional)**
- Add `.exports/` outputs for optional external sharing, gitignored.

---

## 10) Pitfalls and guardrails

- **Build never calls LLMs.** Keep authoring tool isolated and optional.
- **Authoring outputs are committed inputs** under `sources/` and are the only LLM-authored artifacts.
- **Prompt versions are immutable and hashed** for provenance.
- **Avoid combinatorial explosion**: prefer manifests + fragments rather than full materialization.
- **Staging drafts are not canonical**: `staging_snapshot.md` is intake-only, never a build input.
- **Do not change schemas locally** (vendored under `schemas/`).

---

### Immediate next step for a Codex run
1. Inspect current build entrypoint (`src/generator.py::main`), current source layout under `sources/`, and any `scripts/` usage.
2. Add the authoring CLI skeleton without touching build logic.
3. Add tests for authoring scaffolding and audit checks.
