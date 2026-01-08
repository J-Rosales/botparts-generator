# Embedded Entries LLM Log

## Input
```
Entry types:
- locations
- items
- knowledge
- ideology
- relationships

Target total entries: 2

NOTES:
Include persistent items inside the bunker, locations related to where you are and where she's from, relationships with people no longer with her, etc.
```

## Prompt
```
You are generating embedded entries for a character authoring workflow.

You will receive a list of entry types and a target total entry count.
Return JSON only. The JSON must be an object keyed by entry type. Each entry type value is a list of objects with:
- title (string)
- slug (string, lowercase letters/digits/hyphens/underscores)
- description (string)
- scopeLevelIndex (integer, optional; 0=world, 1=character, 2=variant)

Rules:
- Generate exactly the target total number of entries across all types.
- If you must choose fewer types to stay within the target, do so.
- If you have no ideas for a type, return an empty list for that type.
- Keep entries grounded, concrete, and reusable.
- If NOTES or variant context are provided, ensure the entries reflect those constraints.
- Output JSON only (no markdown, no commentary).

ENTRY TYPES:
Entry types:
- locations
- items
- knowledge
- ideology
- relationships

Target total entries: 2

NOTES:
Include persistent items inside the bunker, locations related to where you are and where she's from, relationships with people no longer with her, etc.
```

## Response
```
{
  "locations": [
    {
      "title": "Underground Bunker",
      "slug": "underground_bunker",
      "description": "A fortified underground shelter where the character currently resides, equipped with essential supplies and technology.",
      "scopeLevelIndex": 0
    }
  ],
  "items": [
    {
      "title": "Rusty Survival Knife",
      "slug": "rusty_survival_knife",
      "description": "A worn but reliable knife kept inside the bunker, used for various survival tasks and self-defense.",
      "scopeLevelIndex": 1
    }
  ],
  "knowledge": [],
  "ideology": [],
  "relationships": []
}
```

## Model
```json
{
  "api_base": "https://api.openai.com/v1",
  "max_output_tokens": null,
  "model": "gpt-4.1-mini",
  "provider": "openai",
  "response_id": "resp_0508b440d706566500695f4b156ee08193b8a0f66540e3c880",
  "temperature": 0.3
}
```
