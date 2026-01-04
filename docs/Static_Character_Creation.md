# Static Character Creation (Canonical Inputs)

This repository is the deterministic compiler for Botparts character data. The build reads static, on-disk authoring inputs and emits byte-stable output under `dist/src/data/` with no network or LLM calls in the build path.

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
```

### Required files

- `canonical/spec_v2_fields.md`
  - Contains a JSON object (inline JSON or fenced ```json) for the schema-v2 fields.
  - This data is merged into `manifest.json` by `src/generator.py::_load_authored_manifest`.
- `canonical/shortDescription.md`
  - Short, plain-text description.
  - Emitted under the schema extension block (`x.shortDescription`).

### Deterministic build contract

- Inputs are read only from `sources/` and the vendored schemas; no network calls are performed.
- Output structure is stable and deterministic, including:
  - `dist/src/data/index.json`
  - `dist/src/data/characters/<slug>/manifest.json`
  - `dist/src/data/characters/<slug>/fragments/.keep` when fragments are empty

## Related entry points

- Build: `src/generator.py::build_site_data`
- Authoring helpers: `src/authoring.py::scaffold_character`

