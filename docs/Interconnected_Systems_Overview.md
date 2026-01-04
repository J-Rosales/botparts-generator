# Interconnected Systems Overview

## 1. Static Character Creation (End-to-End)
The static character creation system is the foundation of the project. It defines a deterministic, reproducible pipeline that transforms authored inputs into a complete `spec_v2` character card. This process emphasizes schema compliance, validation, and repeatability: given the same inputs, the generator always produces the same outputs. The goal is to ensure that a character has a single, stable canonical representation that can be trusted as a baseline.

In implementation terms, this system consumes curated text fields, structured metadata, and optional fragments, then assembles them into a finalized card. No live inference or runtime generation occurs here; all intelligence and creativity are resolved upstream. This makes the resulting artifacts portable, auditable, and suitable for static hosting or downstream tools such as SillyTavern.

This static layer is intentionally conservative. It encodes identity, baseline personality, and core description—the elements that define “who this character is” regardless of context. Every other system in the project either builds upon or selectively diverges from this canonical base, but never replaces its role as the anchor of truth.

## 2. Character Variant Pipeline (Human + LLM Authoring)
The character variant pipeline introduces controlled divergence from the canonical base without fragmenting authorship. Variants begin as short, human-written natural language justifications—statements about past conditions or alternate trajectories—and are progressively elaborated through a mix of LLM-assisted expansion and optional manual refinement. Each variant is therefore causally motivated, not cosmetic.

Implementation-wise, this pipeline treats variants as deltas applied to the canonical card. The author can choose to rely on fast, automated generation or intervene at intermediate stages to inject creativity and judgment. The output of this process is not a runtime toggle, but a set of alternative static `spec_v2` cards that are each internally coherent and schema-valid.

Crucially, variants do not overwrite the base; they coexist as parallel interpretations. On disk, each variant lives under `sources/characters/<slug>/variants/<variant_name>/`, anchored by a human-written `seed_phrase.txt` and a delta-only `spec_v2_fields.md`. This allows users, at consumption time, to select the version of the character that best matches their desired tone, relationship state, or narrative context, while preserving consistency and traceability across all versions.

## 3. Embedded Entries as Variant Elements
Many of the differences between variants are best expressed not as monolithic text fields, but as conditional, embedded entries. These include locations tied to personal history, significant items, specialized knowledge, ideological leanings, and relationships with other characters. Each entry represents a small, scoped unit of context that can be injected only when relevant.

From an implementation perspective, these entries are generated during the variant pipeline and attached to the character as embedded lorebook-style data. They are parameterized in number and scope to avoid overload, and they remain clearly associated with the main character rather than redefining the world at large. This mirrors how SillyTavern lorebooks operate, but with stronger guarantees about provenance and intent.

This approach allows variants to feel richer and more reactive without bloating the base card. Instead of restating backstory everywhere, the system relies on targeted injections that activate when specific topics, entities, or situations arise during interaction.

**On-disk format (deterministic, optional):**
- Author embedded entries as Markdown files (optionally with YAML frontmatter) under
  `sources/characters/<slug>/fragments/entries/<type>/<entry_slug>.md`.
- Supported entry types: `locations`, `items`, `knowledge`, `ideology`, `relationships`.
- Filenames must be slug-like (`[a-z0-9][a-z0-9_-]*.md`) and are copied verbatim into
  `dist/src/data/characters/<slug>/fragments/entries/<type>/`.

## 4. Scope Layer System (Narrative Bounding)
The scope layer system exists to prevent implausible or narratively absurd outcomes during variant generation. It formalizes the idea that not all consequences of a variant justification are equal: some changes are personal and local, while others would imply alterations to shared world canon. By default, variant generation is bounded to character- or variant-level scope.

In practice, each generated consequence is implicitly or explicitly classified by scope (world, character, or variant) and impact (local, regional, global). World-level changes require explicit author intent or manual promotion; they are never introduced automatically as side effects. This keeps multiple variants of the same character—and multiple characters in the same setting—compatible with one another.

This system interacts with all others by acting as a governor. It allows the static creation pipeline to remain stable, the variant pipeline to explore meaningful divergence, and embedded entries to add depth, all while preserving a coherent shared setting. The result is flexibility without drift, and creativity without loss of plausibility.
