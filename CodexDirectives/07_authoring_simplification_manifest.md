# Codex Directive: Authoring Pipeline Simplification + Manifest Enforcement

This directive operationalizes the requirements in:
- `docs/REPORT_AUTHORING_SIMPLIFICATION.md`
- `docs/Minimal_Staging_Draft_Manifest.md`

It also incorporates updated clarifications provided by product direction.

## Goals
- Implement a single-file authoring input with strict parsing rules.
- Enforce deterministic behavior for embedded entries (always count = 2).
- Allow non-reproducible slugs (timestamp-based uniqueness is acceptable).
- Validate prompt template selection with an interactive retry loop.
- Constrain manual edits to the stated windows only.
- Wire `prose_variant` exactly at the spec_v2 insertion step.
- Provide a `--no-auto-build` CLI flag.
- Strengthen LLM generation constraints for `spec_v2` (mes_example / greetings).

---

## Implementation checklist

### A) Schema & manifest parsing (single-file authoring input)
[ ] - Define a strict parser for the combined Markdown + YAML frontmatter file:
      - Accept only a single YAML frontmatter block at top of file.
      - Require `version` and `prompts` keys in frontmatter.
      - Require `# Character concept (staging selection)` and `## Display name` sections.
      - Reject duplicate required headers or ambiguous nesting.
      - Validate that optional headers appear at most once.
      - Produce actionable error messages with line numbers where feasible.
[ ] - Document the formal parsing rules in `docs/Minimal_Staging_Draft_Manifest.md` (best-practice aligned: single frontmatter, normalized headings, explicit required sections).
[ ] - Ensure the parsed body content is normalized (trim trailing whitespace, normalize line endings) before use in downstream prompts.

### B) Prompt template selection with interactive retry
[ ] - When reading `prompts.*` values from frontmatter, attempt to resolve each template in its proper folder.
[ ] - If a template is missing:
      - Print a clear error stating which prompt key and value failed.
      - Show the expected directory (e.g., `prompts/<category>/`).
      - Re-prompt the user to enter a valid template name for that key.
      - Repeat until a valid template is selected (no silent fallback).
[ ] - Ensure this interactive retry loop is the only place that prompts for template corrections.

### C) Embedded entries determinism (always 2)
[ ] - Ignore `embedded_entries.count.min/max` and always generate exactly **2** embedded entries.
[ ] - Update docs to state the fixed count (2) and deprecate the range behavior in the combined manifest example.
[ ] - Keep `embedded_entries.transform_notes` as the only embedded-entry customization surface.

### D) Slug policy (non-reproducible timestamps allowed)
[ ] - Remove slug from the schema input; generate slug automatically.
[ ] - Use a timestamp-based suffix for uniqueness (explicitly non-reproducible).
[ ] - Update any slug validation/requirements to accept the new scheme.
[ ] - Document that slugs are non-reproducible and may change on each run.

### E) Manual edit constraints
[ ] - Allow manual edits only at two windows:
      1) The initial combined input file (before running `bp author`).
      2) The pause after elaboration drafts are created, when the program stops for user review.
[ ] - Remove or disable editor prompts and manual entry paths outside those two windows.
[ ] - Ensure any previous manual editing modes (embedded entry authoring, extraction overrides) are disabled or hidden in the simplified flow.

### F) Prose variant wiring (single step only)
[ ] - Use `prose_variant` only at the point where:
      - The natural language premise has been processed by style/tone/voice prompts.
      - The transformed text is about to be inserted into `spec_v2` fields.
[ ] - Do not apply `prose_variant` earlier in elaboration or later in extraction/rewrites.
[ ] - Document this pipeline placement explicitly in `docs/Minimal_Staging_Draft_Manifest.md`.

### G) Auto-build flag
[ ] - Add CLI flag `--no-auto-build` for `bp author`.
[ ] - Default behavior remains: auto-build runs after the single confirmation step.
[ ] - When `--no-auto-build` is present, skip build and exit cleanly.

### H) LLM spec_v2 generation constraints (mes_example + greetings)
[ ] - When generating `spec_v2` via LLM:
      - Enforce `mes_example` to contain **exactly 4 examples**.
      - Use the format: `<START>...<END>` for each example.
      - Separate examples with **double newlines** (`\n\n`).
      - Ensure examples are **orthogonal**:
        - Different characters and situations.
        - Different formats (dialogue-only, pure narrative, hybrid, and a clearly different fourth format).
[ ] - For `first_mes` and each element of `alternate_greetings`:
      - Each must be set in a **different situation** with **different tone**.
      - Each must specify **season, location, and named people** where possible.
[ ] - Add explicit prompt instructions and/or validation logic to enforce these rules.
[ ] - Fail fast with a clear error if the LLM output violates the formatting constraints.

---

## Deliverables
[ ] - Code changes implementing the simplified authoring flow per above.
[ ] - Documentation updates in both referenced docs to reflect the new rules and constraints.
[ ] - Tests (if present in repo structure) covering:
      - Manifest parsing strictness.
      - Prompt template retry behavior.
      - Embedded entry fixed count = 2.
      - `mes_example` formatting validation.
      - `first_mes` / `alternate_greetings` constraints.

