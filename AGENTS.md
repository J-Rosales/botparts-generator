# AGENTS.md — botparts-generator

Date: 2025-12-30

## Repository role (authoritative)
This repository is the **deterministic content compiler** for the Botparts project.

It transforms curated source inputs into **static, site-consumable data**.

## Scope boundaries (non-negotiable)
This repository:
- consumes schemas (vendored)
- consumes source content
- produces compiled output under `dist/`

It MUST NOT:
- contain site UI code
- assume runtime user interaction
- modify schemas locally (vendored only)

## Responsibilities
Agents working here are responsible for:
- reading source inputs
- assembling canonical character data
- producing:
  - `index.json`
  - `characters/<slug>/manifest.json`
  - `characters/<slug>/fragments/**`
- ensuring deterministic output
- ensuring schema compliance

## Generator → Site contract
- Output root: `dist/src/data/`
- Directory structure must be complete and stable.
- `fragments/` directories must **always exist** per character.
- Empty directories must include a placeholder (e.g. `.keep`).

The generator is the **only authority** for the contents of `dist/`.

## What agents may do here
- Implement or refactor build logic
- Add deterministic transforms
- Add fixtures and test data
- Add validation and reproducibility tests
- Improve error diagnostics

## What agents must not do here
- Do not edit schemas except by re-vendoring.
- Do not import or reference site code.
- Do not introduce runtime-only or interactive behavior.

## Directory contract
Expected structure:
- /schemas/          (vendored, read-only)
- /sources/          (human-authored inputs)
- /src/              (generator logic)
- /dist/src/data/    (generated output)

## Testing expectations
Agents may generate:
- pytest tests invoking the generator
- schema validation of outputs
- reproducibility checks (same input → same output)

Tests must run offline and may use subprocess invocation.

## Mental model
Think of this repo as a **compiler**: input → deterministic output, nothing else.
