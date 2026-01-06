# Minimal 1-step Staging Draft + Manifest (Combined)

This document defines a **single-file, one-step authoring input** that merges the minimal staging draft content with a small, global manifest. It is intended to replace multi-file prompt folders for schema selection and provide a compact input for `bp author` in one pass.

## File format
Use **Markdown with YAML frontmatter**. The frontmatter is the manifest. The body is the minimum schema content.

### Example (combined manifest + minimum schema)

```md
---
version: 1
prompts:
  elaborate: default
  extract_fields: spec_v2
  rewrite_variants: compact
  tone: neutral
  style: neutral
  voice: neutral
prose_variant: schema-like # allowed: schema-like | hybrid
embedded_entries:
  transform_notes: |
    Always include a field medic kit, a recurring infirmary location, and a mentor tie.
    Prefer grounded, practical details over mythic artifacts.
  count:
    min: 2
    max: 4
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

## Extraction prompt notes
Ensure medical expertise and travel routine appear in the structured fields.

## Embedded entries notes
Ensure embedded entries cover knowledge, ideology, and a concrete relationship.

## Audit notes
Check that shortDescription is one sentence and that fragments are slugged.
```

---

## Manifest fields (frontmatter)

### `version`
Schema version for the combined file.

### `prompts`
Global prompt variant selection. These are **names** that map to prompt variants used internally.

- `elaborate`
- `extract_fields`
- `rewrite_variants`
- `tone`
- `style`
- `voice`

### `prose_variant`
Controls how `spec_v2` is expressed in prompts and outputs.

**Allowed values:**
- `schema-like` — rigid, low-entropy JSON structure, explicit constraints, minimal prose.
- `hybrid` — lightly structured JSON with embedded natural language and softer constraints.

### `embedded_entries`
Controls embedded entry generation.

- `transform_notes`: Free-form text that describes idiosyncrasies or constraints to apply when generating embedded entries.
- `count`: Desired range for the number of entries. The system should select a count within this range.

---

## Minimum schema body (Markdown section headers)

### Required sections
- `# Character concept (staging selection)`
- `## Display name`

### Optional sections
- `## Elaborate prompt notes`
- `## Draft edits (manual)`
- `## Extraction prompt notes`
- `## Embedded entries notes`
- `## Audit notes`

### Removed fields
- `## Slug` has been removed. Slugs are now automatically derived from the display name and appended with a short timestamp-based code for uniqueness.

---

## Authoring flow expectations
1. **Single step input**: user provides one combined file.
2. **Elaboration runs** on the concept + notes.
3. **One confirmation** after all elaborations.
4. **Automatic build** runs immediately after confirmation.
