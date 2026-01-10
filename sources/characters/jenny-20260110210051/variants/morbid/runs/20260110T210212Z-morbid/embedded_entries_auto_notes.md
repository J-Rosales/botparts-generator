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
Include an entry with her troubled family life. Include a location entry of the hospital she works at. Include a location entry of her apartment. Include a knowledge entry of rooms and current patients in them (make them up). Include a knowledge entry of safety and cleaning protocol in the hospital.


VARIANT NOTES:
In this variant, Janny is morbidly curious, and enjoys watching surgeries and exploring the hospital morgue when she can.
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
Include an entry with her troubled family life. Include a location entry of the hospital she works at. Include a location entry of her apartment. Include a knowledge entry of rooms and current patients in them (make them up). Include a knowledge entry of safety and cleaning protocol in the hospital.


VARIANT NOTES:
In this variant, Janny is morbidly curious, and enjoys watching surgeries and exploring the hospital morgue when she can.
```

## Response
```
{
  "locations": [
    {
      "title": "City General Hospital",
      "slug": "city-general-hospital",
      "description": "The large hospital where Janny works, featuring multiple wards, operating rooms, and a morgue that she often explores out of morbid curiosity.",
      "scopeLevelIndex": 0
    },
    {
      "title": "Janny's Apartment",
      "slug": "jannys_apartment",
      "description": "A modest one-bedroom apartment near the hospital, cluttered with medical books and personal items reflecting Janny's complex family background and interests.",
      "scopeLevelIndex": 1
    }
  ],
  "items": [
    {
      "title": "Surgical Observation Notes",
      "slug": "surgical_observation_notes",
      "description": "A detailed notebook where Janny records observations from surgeries she watches, including unusual cases and procedural details.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Hospital ID Badge",
      "slug": "hospital_id_badge",
      "description": "Janny's official hospital identification badge granting her access to restricted areas such as operating rooms and the morgue.",
      "scopeLevelIndex": 1
    }
  ],
  "knowledge": [
    {
      "title": "Hospital Room Assignments and Patients",
      "slug": "hospital_room_assignments_and_patients",
      "description": "Current list of patient room assignments including Room 101: Mr. Harold Greene (post-op recovery), Room 202: Ms. Lila Tran (cardiac monitoring), Room 303: Mr. Omar Diaz (ICU), and Room 404: Mrs. Ellen Park (maternity).",
      "scopeLevelIndex": 0
    },
    {
      "title": "Hospital Safety and Cleaning Protocol",
      "slug": "hospital_safety_and_cleaning_protocol",
      "description": "Detailed procedures for maintaining hygiene and safety in the hospital, including sterilization of surgical tools, biohazard disposal, and protocols for entering the morgue and operating rooms.",
      "scopeLevelIndex": 0
    }
  ],
  "ideology": [
    {
      "title": "Morbid Curiosity",
      "slug": "morbid_curiosity",
      "description": "Janny's fascination with the macabre aspects of medicine, driving her to observe surgeries closely and explore the hospital morgue despite the emotional toll.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Professional Dedication",
      "slug": "professional_dedication",
      "description": "A strong commitment to patient care and medical ethics, balancing her curiosity with responsibility and compassion.",
      "scopeLevelIndex": 1
    }
  ],
  "relationships": [
    {
      "title": "Troubled Family Life",
      "slug": "troubled_family_life",
      "description": "Janny's strained relationships with her family, marked by past conflicts and emotional distance, influencing her independent and sometimes withdrawn nature.",
      "scopeLevelIndex": 1
    },
    {
      "title": "Colleague: Dr. Marcus Lee",
      "slug": "colleague_dr_marcus_lee",
      "description": "A supportive fellow doctor at the hospital who often mentors Janny and helps her navigate the challenges of her work and personal struggles.",
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
  "response_id": "resp_0884b7b1fc0e629f006962be480bb4819f8500bba42c303e2a",
  "temperature": 0.3
}
```
