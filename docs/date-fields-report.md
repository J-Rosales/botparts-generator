# Date Fields Behavior Report (botparts-generator)

This report documents the **current generator behavior** for date fields after the latest update, intended to align `botparts-schema` with actual output.

## Overview
- The generator now emits **both** `uploadDate` and `updatedAt`.
- When a character is created through the pipeline, `updatedAt` defaults to the same value as `uploadDate`.

## Field sources and precedence
Both fields are gathered in `src/generator.py::build_site_data`.

### `uploadDate`
Priority order:
1. `sources/site-seed/index.json` entry field `uploadDate`
2. `sources/characters/<slug>/manifest.json` field `uploadDate` (or in `x.uploadDate`)
3. `sources/characters/<slug>/manifest.json` legacy field `updated`
4. Default: `""` (empty string)

### `updatedAt`
Priority order:
1. `sources/site-seed/index.json` entry field `updatedAt`
2. `sources/characters/<slug>/manifest.json` field `updatedAt` (or in `x.updatedAt`)
3. `sources/characters/<slug>/manifest.json` field `updatedAt` (top-level fallback)
4. If missing, **defaults to `uploadDate`**

## Emission locations
The generator writes both fields to:

- **Character manifest** (`dist/src/export/characters/<slug>/manifest.json`)
  - `x.uploadDate`
  - `x.updatedAt`
  - `site.uploadDate`
  - `site.updatedAt`
- **Catalogue** (`dist/src/data/catalogue.json`)
  - `entries[].uploadDate`
  - `entries[].updatedAt`

## Formatting
Both fields are stored as strings. The generator does **no validation** beyond coercing non-string inputs via `str(...)`.
The canonical expectation is **date-only ISO-8601 (YYYY-MM-DD)**, with `""` representing unknown.

## Code references
- `src/generator.py::build_site_data` — constructs both date fields and writes them into manifest payloads and the catalogue.
- `src/generator.py::_extract_site_field` — extracts `uploadDate`/`updatedAt` from top-level or `x.*` in source manifests or site seed entries.
- `src/exporter.py::export_character_bundle` — persists `manifest_payload` to `dist/src/export/characters/<slug>/manifest.json`.
