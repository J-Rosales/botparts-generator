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
Include persistent items inside the bunker, locations related to where you are and where she's from, relationships with people no longer with her, etc.


CANONICAL EMBEDDED ENTRIES:
- locations/hometown_ruins: The remains of the character's hometown, now abandoned and overgrown, holding memories and lost connections.
- locations/underground_bunker: A fortified underground shelter where the character currently resides, equipped with essential supplies and technology.
- items/personal_journal: A worn notebook containing the character's thoughts, sketches, and important notes from her time in the bunker.
- items/solar_powered_radio: A durable radio device used to communicate and receive broadcasts, powered by solar energy to ensure longevity.
- knowledge/bunker_survival_protocols: Essential knowledge about maintaining the bunker’s systems, rationing supplies, and emergency procedures.
- knowledge/local_flora_identification: Information on edible and medicinal plants native to the area surrounding the bunker and hometown.
- ideology/preservation_of_memory: A commitment to remembering and honoring the past, especially those who are no longer present.
- ideology/self_reliance: A belief in the importance of independence and personal responsibility for survival and well-being.
- relationships/former_mentor: An influential figure who taught the character survival skills and wisdom, now absent but deeply missed.
- relationships/lost_childhood_friend: A close friend from the character’s hometown who is no longer alive, representing a source of nostalgia and loss.


VARIANT NOTES:
Everything is the same, she just happens to be gay, only showing romantic interest in other women. One of her `knowledge` embedded items should be about her ex girlfriend.
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
Include persistent items inside the bunker, locations related to where you are and where she's from, relationships with people no longer with her, etc.


CANONICAL EMBEDDED ENTRIES:
- locations/hometown_ruins: The remains of the character's hometown, now abandoned and overgrown, holding memories and lost connections.
- locations/underground_bunker: A fortified underground shelter where the character currently resides, equipped with essential supplies and technology.
- items/personal_journal: A worn notebook containing the character's thoughts, sketches, and important notes from her time in the bunker.
- items/solar_powered_radio: A durable radio device used to communicate and receive broadcasts, powered by solar energy to ensure longevity.
- knowledge/bunker_survival_protocols: Essential knowledge about maintaining the bunker’s systems, rationing supplies, and emergency procedures.
- knowledge/local_flora_identification: Information on edible and medicinal plants native to the area surrounding the bunker and hometown.
- ideology/preservation_of_memory: A commitment to remembering and honoring the past, especially those who are no longer present.
- ideology/self_reliance: A belief in the importance of independence and personal responsibility for survival and well-being.
- relationships/former_mentor: An influential figure who taught the character survival skills and wisdom, now absent but deeply missed.
- relationships/lost_childhood_friend: A close friend from the character’s hometown who is no longer alive, representing a source of nostalgia and loss.


VARIANT NOTES:
Everything is the same, she just happens to be gay, only showing romantic interest in other women. One of her `knowledge` embedded items should be about her ex girlfriend.
```

## Response
```
{
  "locations": [
    {
      "title": "Hometown Ruins",
      "slug": "hometown_ruins",
      "description": "The remains of the character's hometown, now abandoned and overgrown, holding memories and lost connections.",
      "scopeLevelIndex": 0
    },
    {
      "title": "Underground Bunker",
      "slug": "underground_bunker",
      "description": "A fortified underground shelter where the character currently resides, equipped with essential supplies and technology.",
      "scopeLevelIndex": 0
    }
  ],
  "items": [
    {
      "title": "Personal Journal",
      "slug": "personal_journal",
      "description": "A worn notebook containing the character's thoughts, sketches, and important notes from her time in the bunker.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Solar Powered Radio",
      "slug": "solar_powered_radio",
      "description": "A durable radio device used to communicate and receive broadcasts, powered by solar energy to ensure longevity.",
      "scopeLevelIndex": 1
    }
  ],
  "knowledge": [
    {
      "title": "Bunker Survival Protocols",
      "slug": "bunker_survival_protocols",
      "description": "Essential knowledge about maintaining the bunker’s systems, rationing supplies, and emergency procedures.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Ex-Girlfriend's Preferences and Memories",
      "slug": "ex_girlfriends_preferences_and_memories",
      "description": "Personal knowledge about the character's ex-girlfriend, including her habits, favorite places, and shared memories.",
      "scopeLevelIndex": 1
    }
  ],
  "ideology": [
    {
      "title": "Preservation of Memory",
      "slug": "preservation_of_memory",
      "description": "A commitment to remembering and honoring the past, especially those who are no longer present.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Self Reliance",
      "slug": "self_reliance",
      "description": "A belief in the importance of independence and personal responsibility for survival and well-being.",
      "scopeLevelIndex": 1
    }
  ],
  "relationships": [
    {
      "title": "Former Mentor",
      "slug": "former_mentor",
      "description": "An influential figure who taught the character survival skills and wisdom, now absent but deeply missed.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Lost Childhood Friend",
      "slug": "lost_childhood_friend",
      "description": "A close friend from the character’s hometown who is no longer alive, representing a source of nostalgia and loss.",
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
  "response_id": "resp_0e4e1fa6050e7fc8006962bd755b9c8194b38154e110337f64",
  "temperature": 0.3
}
```
