# Minimal 1-step Staging Draft + Manifest (Combined)

This document defines a **single-file, one-step authoring input** that merges the minimal staging draft content with a small, global manifest. It is intended to replace multi-file prompt folders for schema selection and provide a compact input for `bp author` in one pass.

## File format
Use **Markdown with YAML frontmatter**. The frontmatter is the manifest. The body is the minimum schema content.

### Example (combined manifest + minimum schema)

```md
---
version: 1
prompts:
  elaborate: 01_elaborate_v1.md
  extract_fields: 01_specv2_fields_v1.md
  idiosyncrasy_module: 01_idiosyncrasy_module_v1.md
  rewrite_variants: 01_compact_v1.md
  tone: 01_neutral_v1.md
  style: 01_neutral_v1.md
  voice: 01_neutral_v1.md
prose_variant: schema-like # allowed: schema-like | hybrid | all
embedded_entries:
  transform_notes: |
    Always include a field medic kit, a recurring infirmary location, and a mentor tie.
    Prefer grounded, practical details over mythic artifacts.
---

# Character concept (staging selection)
Naive scout turned field medic who documents every village she visits and
collects small, worn trinkets from each rescue. She is curious, kind, and
easily distracted by local folklore.

## Display name
Liora, the Field Medic

## Elaborate prompt notes
Emphasize gentle humor, practical survival skills, and a habit of journaling.

## Draft edits (manual)
Keep the tone warm and grounded; avoid high-fantasy magic.

## Audit notes
Check that shortDescription is one sentence and that fragments are slugged.

## Variant notes
### Variant Group
#### Calm Tone
She trusts others more quickly and avoids grim humor.
```

---

## Manifest fields (frontmatter)

### `version`
Schema version for the combined file.

### `prompts`
Global prompt variant selection. These are **names** that map to prompt variants used internally.

- `elaborate`
- `extract_fields`
- `idiosyncrasy_module`
- `rewrite_variants`
- `tone`
- `style`
- `voice`

Values must match filenames in `prompts/<category>/` (e.g., `01_elaborate_v1.md`).

### `prose_variant`
Controls how `spec_v2` is expressed in prompts and outputs.

**Allowed values:**
- `schema-like` — rigid, low-entropy JSON structure, explicit constraints, minimal prose.
- `hybrid` — lightly structured JSON with embedded natural language and softer constraints.
- `all` — run both variants and export both prose styles for a single canonical character.

### `embedded_entries`
Controls embedded entry generation.

- `transform_notes`: Free-form text that describes idiosyncrasies or constraints to apply when generating embedded entries.
- The generator always produces **exactly 2** embedded entries (deterministic). Range-based counts are deprecated.

---

## Minimum schema body (Markdown section headers)

### Required sections
- `# Character concept (staging selection)`
- `## Display name`

### Optional sections
- `## Elaborate prompt notes`
- `## Draft edits (manual)`
- `## Audit notes`
- `## Variant notes`

### Removed fields
- `## Slug` has been removed. Slugs are now automatically derived from the display name and appended with a short timestamp-based code for uniqueness.

---

## Formal parsing rules (strict)
- The file **must** start with a single YAML frontmatter block; additional frontmatter blocks are rejected.
- Frontmatter **must** include `version` (integer) and `prompts` (mapping).
- Required headings must appear **exactly once** with the exact levels shown above.
- Optional headings may appear **at most once** and must use `##` level headings.
- Unknown or additional headings are rejected to avoid ambiguous nesting.
- Body content is normalized before use (line endings normalized to `\n`, trailing whitespace trimmed).

---

## Authoring flow expectations
1. **Single step input**: user provides one combined file.
2. **Elaboration runs** on the concept + notes.
3. **One confirmation** after elaboration when the preliminary draft is ready for manual edits.
4. `prose_variant` is applied only when inserting the styled draft into `spec_v2` fields.
   When set to `all`, both `schema-like` and `hybrid` exports are emitted for the same character slug.
5. **Embedded entries** are generated from `embedded_entries.transform_notes` (fixed count = 2).
6. **Idiosyncrasy module** is generated once per character and written into
   `system_prompt` + `post_history_instructions`.
7. **Variant notes** (if present) create additional variant deltas after canonical extraction.
8. **Automatic build** runs immediately after confirmation unless `--no-auto-build` is supplied.
