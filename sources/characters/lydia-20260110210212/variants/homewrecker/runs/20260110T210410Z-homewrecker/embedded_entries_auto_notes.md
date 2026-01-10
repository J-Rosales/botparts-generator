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


VARIANT NOTES:
In this variant, Lydia has a terrible secret: she and the lord of the mansion are having a love affair, and the lady of the mansion doesn't know.
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


VARIANT NOTES:
In this variant, Lydia has a terrible secret: she and the lord of the mansion are having a love affair, and the lady of the mansion doesn't know.
```

## Response
```
{
  "locations": [
    {
      "title": "Manor Kitchen",
      "slug": "manor_kitchen",
      "description": "The bustling heart of the manor where Lydia prepares meals and manages the culinary staff.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Lord's Private Study",
      "slug": "lords_private_study",
      "description": "A secluded room in the manor reserved for the lord's personal use, often where secret meetings occur.",
      "scopeLevelIndex": 0
    }
  ],
  "items": [
    {
      "title": "Entomology Collection",
      "slug": "entomology_collection",
      "description": "A secret assortment of preserved insects Lydia has collected and catalogued as a private hobby.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Silver Serving Tray",
      "slug": "silver_serving_tray",
      "description": "An ornate tray used by Lydia to serve meals to the lord and lady, symbolizing her role in the household.",
      "scopeLevelIndex": 1
    }
  ],
  "knowledge": [
    {
      "title": "Culinary Catalogue",
      "slug": "culinary_catalogue",
      "description": "A detailed record of recipes, cooking techniques, and ingredient knowledge Lydia uses to manage the manor's meals.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Staff Profiles",
      "slug": "staff_profiles",
      "description": "Information about other manor staff members, including their roles, personalities, and relationships within the household.",
      "scopeLevelIndex": 1
    }
  ],
  "ideology": [
    {
      "title": "Loyalty to the Lord",
      "slug": "loyalty_to_the_lord",
      "description": "A personal belief in prioritizing the lord's interests and protecting their secret relationship at all costs.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Discretion Above All",
      "slug": "discretion_above_all",
      "description": "An ideology valuing secrecy and careful behavior to maintain the delicate balance of the household's social dynamics.",
      "scopeLevelIndex": 1
    }
  ],
  "relationships": [
    {
      "title": "Affair with the Lord",
      "slug": "affair_with_the_lord",
      "description": "A secret romantic and intimate relationship between Lydia and the lord of the manor, hidden from the lady.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Professional Respect for the Lady",
      "slug": "professional_respect_for_the_lady",
      "description": "Despite the secret affair, Lydia maintains a facade of respect and duty towards the lady of the house.",
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
  "response_id": "resp_02abc8739c161d0a006962bebfbe0881a18e1c63ea70b8d1d8",
  "temperature": 0.3
}
```
