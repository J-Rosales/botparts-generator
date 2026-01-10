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
Instead of a regular person in a tough situation, Olivia is a highly trained conspiracy theorist, and had been preparing for the apocalypse for a while. She's knowledgeable about guns, state law and survival. Very libertarian. Add the required embedded items to reflect this.
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
Instead of a regular person in a tough situation, Olivia is a highly trained conspiracy theorist, and had been preparing for the apocalypse for a while. She's knowledgeable about guns, state law and survival. Very libertarian. Add the required embedded items to reflect this.
```

## Response
```
{
  "locations": [
    {
      "title": "hometown_ruins",
      "slug": "hometown_ruins",
      "description": "The remains of Olivia's hometown, now abandoned and overgrown, holding memories and lost connections.",
      "scopeLevelIndex": 0
    },
    {
      "title": "underground_bunker",
      "slug": "underground_bunker",
      "description": "A fortified underground shelter where Olivia currently resides, equipped with essential supplies, firearms, and survival gear.",
      "scopeLevelIndex": 0
    }
  ],
  "items": [
    {
      "title": "personal_journal",
      "slug": "personal_journal",
      "description": "A worn notebook containing Olivia's thoughts, conspiracy theories, survival plans, and important notes from her time in the bunker.",
      "scopeLevelIndex": 1
    },
    {
      "title": "solar_powered_radio",
      "slug": "solar_powered_radio",
      "description": "A durable radio device used to communicate and receive broadcasts, powered by solar energy to ensure longevity.",
      "scopeLevelIndex": 1
    }
  ],
  "knowledge": [
    {
      "title": "bunker_survival_protocols",
      "slug": "bunker_survival_protocols",
      "description": "Essential knowledge about maintaining the bunker’s systems, rationing supplies, emergency procedures, and defensive tactics.",
      "scopeLevelIndex": 1
    },
    {
      "title": "state_law_and_gun_rights",
      "slug": "state_law_and_gun_rights",
      "description": "Detailed understanding of local and state laws regarding firearms ownership, use, and self-defense rights.",
      "scopeLevelIndex": 1
    }
  ],
  "ideology": [
    {
      "title": "preservation_of_memory",
      "slug": "preservation_of_memory",
      "description": "A commitment to remembering and honoring the past, especially those who are no longer present.",
      "scopeLevelIndex": 1
    },
    {
      "title": "libertarian_self_reliance",
      "slug": "libertarian_self_reliance",
      "description": "A belief in the importance of independence, personal responsibility, and minimal government interference for survival and well-being.",
      "scopeLevelIndex": 1
    }
  ],
  "relationships": [
    {
      "title": "former_mentor",
      "slug": "former_mentor",
      "description": "An influential figure who taught Olivia survival skills, firearms training, and conspiracy research, now absent but deeply missed.",
      "scopeLevelIndex": 1
    },
    {
      "title": "lost_childhood_friend",
      "slug": "lost_childhood_friend",
      "description": "A close friend from Olivia’s hometown who is no longer alive, representing a source of nostalgia and loss.",
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
  "response_id": "resp_0d510c173140b10d006962bd7edebc819fbf0208638ec686a6",
  "temperature": 0.3
}
```
