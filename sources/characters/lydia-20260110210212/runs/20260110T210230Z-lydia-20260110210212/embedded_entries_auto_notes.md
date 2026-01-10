# Embedded Entries LLM Log

## Input
```
Entry types:
- locations
- items
- knowledge
- ideology
- relationships

Target entries per type: 2

NOTES:
Include an entry with a catalogue of her culinary knowledge. She has entries about other staff in the manor as well as the Lord and Lady of the house. She also has a secret hobby of an entomological collection.
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

Target entries per type: 2

NOTES:
Include an entry with a catalogue of her culinary knowledge. She has entries about other staff in the manor as well as the Lord and Lady of the house. She also has a secret hobby of an entomological collection.
```

## Response
```
{
  "locations": [
    {
      "title": "Manor Kitchen",
      "slug": "manor_kitchen",
      "description": "The bustling kitchen of the manor where meals are prepared and culinary secrets are kept.",
      "scopeLevelIndex": 0
    },
    {
      "title": "Entomology Study",
      "slug": "entomology_study",
      "description": "A private room in the manor dedicated to the secret hobby of collecting and studying insects.",
      "scopeLevelIndex": 1
    }
  ],
  "items": [
    {
      "title": "Insect Specimen Collection",
      "slug": "insect_specimen_collection",
      "description": "A carefully curated collection of preserved insects, showcasing a variety of species.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Chef's Knife Set",
      "slug": "chefs_knife_set",
      "description": "A set of high-quality knives used for preparing meals in the manor kitchen.",
      "scopeLevelIndex": 0
    }
  ],
  "knowledge": [
    {
      "title": "Culinary Catalogue",
      "slug": "culinary_catalogue",
      "description": "A detailed catalogue of recipes, cooking techniques, and ingredient knowledge used in the manor.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Manor Staff Profiles",
      "slug": "manor_staff_profiles",
      "description": "Information and background details about the various staff members serving in the manor.",
      "scopeLevelIndex": 1
    }
  ],
  "ideology": [],
  "relationships": [
    {
      "title": "Lord of the Manor",
      "slug": "lord_of_the_manor",
      "description": "The relationship and duties connected to the Lord overseeing the manor.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Lady of the Manor",
      "slug": "lady_of_the_manor",
      "description": "The relationship and interactions with the Lady of the manor, including social expectations.",
      "scopeLevelIndex": 1
    }
  ]
}
```

## Model
```json
{
  "api_base": "https://api.openai.com/v1",
  "max_output_tokens": null,
  "model": "gpt-4.1-mini",
  "provider": "openai",
  "response_id": "resp_0f4a7800c05795ed006962be5edca881a29ffd0a80d400cc25",
  "temperature": 0.3
}
```
