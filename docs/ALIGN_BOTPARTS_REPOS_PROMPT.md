# Alignment Prompt for botparts-site + botparts-schema

Use the following prompt in the sibling repositories to align with the new export-package contract:

---

We have updated **botparts-generator** to make `dist/src/export/` the canonical output. Please align this repository with the new package contract:

## New export package contract
- Output root: `dist/src/export/characters/<slug>/`
- Required files per character:
  - `manifest.json` (categorization + site info; `x.proseVariants` lists `["schema-like","hybrid"]`)
  - `spec_v2.schema-like.json`
  - `spec_v2.hybrid.json`
  - `<slug>.png` (raw PNG; **no embedded JSON at build time**)
- Variants (when present):
  - `dist/src/export/characters/<slug>/variants/<variant_slug>/spec_v2.schema-like.json`
  - `dist/src/export/characters/<slug>/variants/<variant_slug>/spec_v2.hybrid.json`
  - `dist/src/export/characters/<slug>/variants/<variant_slug>/<slug>--<variant_slug>.png`

## Key behavioral changes
- `dist/src/data/` is no longer produced.
- Fragment outputs and world packs are **authoring inputs only**; they are no longer emitted as standalone files.
- PNG metadata embedding is deferred to **download-time** (handled by the consumer, not the generator).
- A single canonical character slug now has **both prose styles** (schema-like + hybrid) derived from the same canonical spec.

## botparts-site requests
- Update data ingestion to read `dist/src/export/` packages instead of `dist/src/data/`.
- Remove dependencies on `index.json`, fragment paths, and scope layer outputs.
- When offering downloads, embed the selected `spec_v2.*.json` into the PNG **at download time**.
- Expose both prose variants in the UI (if applicable), keyed by `spec_v2.schema-like.json` vs `spec_v2.hybrid.json`.

## botparts-schema requests
- Update schemas to reflect the new package layout.
- Ensure `manifest.json` schema focuses on categorization/site info plus `x.proseVariants` and optional `x.variantSlugs`.
- Remove/relax schema requirements that referenced fragment paths or scope-layer outputs.

Please confirm any schema or API changes needed so we can keep the generator and consumers aligned.

---
