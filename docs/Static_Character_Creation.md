# Static Character Creation (Canonical Inputs)

This repository is the deterministic compiler for Botparts character data. The build reads static, on-disk authoring inputs and emits byte-stable export packages under `dist/src/export/` with no network or LLM calls in the build path.

For the system-level mental model, see the Interconnected Systems Overview: `docs/Interconnected_Systems_Overview.md`.

## Canonical authoring layout

Each character lives under `sources/characters/<slug>/` and must include a canonical directory with stable, schema-aligned inputs:

```
sources/
  characters/
    <slug>/
      canonical/
        spec_v2_fields.md
        shortDescription.md
      fragments/
        entries/
          locations/
          items/
          knowledge/
          ideology/
          relationships/
```

### Required files

- `canonical/spec_v2_fields.md`
  - Contains a JSON object (inline JSON or fenced ```json) for the schema-v2 fields.
  - This data is merged into `manifest.json` by `src/generator.py::_load_authored_manifest`.
- `canonical/shortDescription.md`
  - Short, plain-text description.
  - Emitted under the schema extension block (`x.shortDescription`).

### Canonical embedded entries (locations, items, knowledge, ideology, relationships)

By the time a canonical character is considered “done,” you should also supply the **embedded entry fragments** that ground the character in concrete, reusable details. These are plain-text Markdown files authored under:

```
sources/characters/<slug>/fragments/entries/<type>/<entry_slug>.md
```

Supported entry types:
- `locations`
- `items`
- `knowledge`
- `ideology`
- `relationships`

Each file can be simple text (or Markdown with optional YAML frontmatter). The build reads these files as input only and emits their content into the `spec_v2` lorebook output; fragments are no longer emitted as standalone files.

#### How to author these with input strings/numbers (no LLM required)

When you draft the canonical spec (`spec_v2_fields.md`), also capture a short list of concrete, **string/number inputs** that should become embedded entries. These should line up with the casual “why this matters” ideas that you would later use to motivate variants (e.g., *“she never trusts authority after incident X”* or *“he spends every evening at the observatory”*).

Use a quick checklist like:
- **Locations**: 1–3 places the character reliably returns to (name + 1–2 sentence description).
- **Items**: 1–3 objects with story weight (name + what it implies).
- **Knowledge**: 1–3 facts the character uniquely knows (fact + source).
- **Ideology**: 1–3 beliefs or principles (belief + origin/pressure).
- **Relationships**: 1–3 ties (person + relationship status).

Optional for any embedded entry type: add a `scopeLevelIndex` that maps to scope layers
(0=world, 1=character, 2=variant) when you want to capture the intended scope explicitly.

Then turn each item into its own file:

```
sources/characters/<slug>/fragments/entries/relationships/older-sister.md
```

This keeps the canon grounded and makes later variants more consistent: the same **casual idea** used to justify a variant should already exist as a canonical fragment, so variants can emphasize, suppress, or reinterpret it without inventing new base facts.

### Deterministic build contract

- Inputs are read only from `sources/` and the vendored schemas; no network calls are performed.
- Output structure is stable and deterministic, including:
  - `dist/src/export/characters/<slug>/manifest.json`
  - `dist/src/export/characters/<slug>/spec_v2.schema-like.json`
  - `dist/src/export/characters/<slug>/spec_v2.hybrid.json`
  - `dist/src/export/characters/<slug>/<slug>.png` (raw source image when available)

## Related entry points

- Build: `src/generator.py::build_site_data`
- Authoring helpers: `src/authoring.py::scaffold_character`
