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

## Local Authoring Secrets
Authoring commands (e.g. `bp author`, `bp audit`) can load local environment variables from a repo-root `.secrets` file.

1. Copy `.secrets.example` to `.secrets`.
2. Fill in your local values (e.g. `BOTPARTS_LLM_API_KEY`).

The `.secrets` file is gitignored and **never** read during deterministic builds (`bp build`).

## Tag Partitioning Rule
- Tags prefixed with `spoiler:` are stripped of the prefix and emitted as `spoilerTags` (stored under `x`), while the remaining tags stay in `tags`.
