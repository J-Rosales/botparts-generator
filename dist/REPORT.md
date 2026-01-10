# Botparts Generator Report

## Run Metadata
- Generator version: 0.1.0
- Placeholders enabled: False (0)

## Output Summary
- Real characters: 0
- Placeholder characters: 0
- Total characters emitted: 0
- Directories created:
  - src/data
  - src/export
  - src/export/characters

## Field Policy Summary
- Site-only fields emitted under x:
  - shortDescription (default: '')
  - spoilerTags (default: [])
  - aiTokens (default: None)
  - uploadDate (default: '')
  - placeholder (default: false for real characters)
- Tag partitioning: tags starting with 'spoiler:' move to spoilerTags; prefix stripped, trimmed, deduped.
- uploadDate formatting: YYYY-MM-DD (date-only); empty string when unknown.
- aiTokens type: number|null.

## Warnings
- None.
