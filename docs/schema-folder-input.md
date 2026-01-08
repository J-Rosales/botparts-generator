# Schema-folder input format

This document describes the markdown format consumed by `bp author schema-folder`.

## Required structure
1. A YAML frontmatter block enclosed by `---` at the top and bottom of the file.
2. A **single H1** exactly equal to `# Character concept (staging selection)`.
3. Required H2 sections from the allowed list below.

### Required H2 sections
- `## Display name`
- `## Elaborate prompt notes`
- `## Draft edits (manual)`
- `## Audit notes`
- `## Variant notes`

### Variant notes rules
- Variants may be written as **bullet list items** under `## Variant notes`.
- Variant names may also be written as `###` headings under `## Variant notes`.
- `###` headings are only allowed under `## Variant notes`. Elsewhere, `###` headings are rejected.

## Full example
```
---
version: 1
prompts:
  elaborate: 01_elaborate_v1.md
  extract_fields: 01_specv2_fields_v1.md
  tone: chill_v1.md
  style: casual_v1.md
  voice: third_person_user_v1.md
prose_variant: all
embedded_entries:
  transform_notes: |
    Include persistent items inside the bunker, locations related to where you are and where she's from, relationships with people no longer with her, etc.
---

# Character concept (staging selection)
Set in modern times in America, you wake up to find that a young woman named Olivia rescued you from an undisclosed apocalyptic scenario. She dragged you into her bunker and now you must survive as long as you can until someone rescues you or you decide to venture out into the ruined world.

## Display name
Olivia

## Elaborate prompt notes
None. Continue as normal.

## Draft edits (manual)
None. Continue as normal.

## Audit notes
None. Continue as normal.

## Variant notes
### Infected
A variant where the apocalypse is caused by a virus that makes people into zombies. She was bitten recently and is hiding it from you.

### Gay
Everything is the same, she just happens to be gay, only showing romantic interest in other women. One of her `knowledge` embedded items should be about her ex girlfriend.

### Prepper
Instead of a regular person in a tough situation, Olivia is a conspiracy theorist, and had been preparing for the apocalypse. She's highly knowledgeable about guns, state law and survival. Very libertarian.
```
