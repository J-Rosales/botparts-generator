# Botparts Generator Report

## Run Metadata
- Generator version: 0.1.0
- Placeholders enabled: False (0)

## Output Summary
- Real characters: 1
- Placeholder characters: 0
- Total characters emitted: 1
- Directories created:
  - src\export
  - src\export\characters
  - src\export\characters\pearl-20260110052021
  - src\export\characters\pearl-20260110052021\variants\morbid

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
- [pearl-20260110051937] Missing manifest.json in sources.
- [pearl-20260110052021] PNG not found under sources/image_inputs; image export skipped.
- [pearl-20260110052021] PNG not found for variant 'morbid'; image export skipped.
