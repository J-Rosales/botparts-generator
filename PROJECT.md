# PROJECT.md — botparts-generator

## Role
`botparts-generator` is the **content compiler** for the Botparts project.

It takes source inputs (original bots, rewrites, notes) and produces **static, deploy‑ready character packages** that conform to shared schemas.

## Architecture Constraints (Non‑Negotiable)
- No live LLM usage.
- No summarization or inference.
- Only deterministic operations:
  - concatenation
  - replacement
  - injection
- Outputs must be byte‑stable for identical inputs.

## Repository Topology (Botparts)
- `botparts-schemas` → source of truth for all JSON Schemas.
- `botparts-generator` → produces exports.
- `botparts-site` → consumes exports.

## Schemas
Schemas are vendored from `botparts-schemas` via **git subtree**.

- Local path: `schemas/`
- Do **not** edit schema files here.
- Schema changes must be made upstream.

## Output Contract (Produced)
Generator outputs must include:

- `index.json`
- `data/characters/<slug>/manifest.json`
- `data/characters/<slug>/fragments/**`

All outputs must validate against the vendored schemas.

## Assembly Model
- Base character + fragment modules.
- Modules/toggles select static fragments.
- Transform definitions describe rendering preferences only.
- The generator may pre‑emit compiled outputs, but must preserve fragment structure.

## Codex Rules
When working in this repo:
- Implement loading, validation, assembly, and export logic only.
- Never embed site/UI concerns.
- Never change schemas locally.
- If a feature cannot be expressed with current schemas, produce a **schema change request** instead.

## Generator Flags (Local Dev)
- `--placeholders <N>` or `BOTPARTS_PLACEHOLDERS=<N>`: emit N deterministic placeholder profiles for layout testing. Default: 0.

## Tag Partitioning Rule
- Tags prefixed with `spoiler:` are stripped of the prefix and emitted as `spoilerTags` (stored under `x`), while the remaining tags stay in `tags`.
