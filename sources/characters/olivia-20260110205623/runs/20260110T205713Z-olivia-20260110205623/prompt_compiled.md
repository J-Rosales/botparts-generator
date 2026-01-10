You are extracting spec_v2 fields from a preliminary character draft.

Input:
- The full preliminary_draft.md text.

Task:
Return a single JSON object with the following keys in this exact order. Values must be strings unless otherwise noted. If a field is unknown, use an empty string. Do not invent new facts beyond trivial connective tissue from the draft.

Keys (in order):
1) slug
2) name
3) description
4) personality
5) scenario
6) first_mes
7) alternate_greetings (array of strings)
8) mes_example
9) system_prompt
10) creator_notes
11) post_history_instructions
12) creator
13) character_version
14) tags (array of strings)

Constraints:
- Keep content non-graphic and avoid explicit sexual detail.
- Preserve the character's identity and voice from the draft.
- first_mes and each alternate_greetings entry must describe a different situation and tone.
- Each greeting should name the season, location, and named people where possible.
- first_mes must be a paragraph or two (multi-sentence), not a single line. Use the space to describe multiple surrounding elements (environment, time of day, location, nearby people, the character’s reactions, and any immediate setting cues).
- Each alternate_greetings entry must be a paragraph or two (multi-sentence), not a single line. Avoid repeating the same fact within a single entry (no internal redundancy). Use the extra space to describe multiple surrounding elements (environment, time of day, location, nearby people, the character’s reactions, and any immediate setting cues).
- In first_mes and alternate_greetings, try to avoid repeating {{user}} multiple times in the same entry; mention {{user}} once, then rely on pronouns or implied context.
- mes_example must contain exactly 4 examples in this format:
  <START>...<END>
  Separate examples with double newlines.
  Make the four examples orthogonal: different characters/situations and distinct formats
  (dialogue-only, pure narrative, hybrid, and a clearly different fourth format).
- No extra keys, no code fences, no markdown, no commentary.

After the JSON object, on a new line, output the marker exactly as shown:
---SHORT_DESCRIPTION---
Then output a single-sentence shortDescription suitable for the site (one sentence, no lists, no headings).

Output format (strict):
<JSON object>
---SHORT_DESCRIPTION---
<one-sentence shortDescription>

DRAFT:
The first thing {{user}} notices is the quiet. Not the kind of quiet that’s just absence of noise, but the kind that feels like a soft blanket pulled over the world, muffling everything into a gentle hush. The kind of quiet that makes the faint hum of a ventilation system sound like a lullaby. Eyes blink open to dim, artificial light—warm but not harsh—casting long shadows across a room that smells faintly of metal and something earthy, like damp soil or old wood. It’s the kind of smell that’s oddly comforting, like the scent of a basement after rain, or a library that’s been closed for a while.

There’s no immediate rush, no sharp edges to the moment. Just the slow, deliberate realization that the world outside isn’t the one {{user}} remembers. The air feels recycled, filtered, and the walls are lined with shelves holding canned goods, jars of preserved food, and a few well-worn books. A small radio sits on a table, silent for now, but ready to crackle to life at any moment. Somewhere nearby, a faint drip of water echoes softly, steady and reassuring.

Movement catches {{user}}’s attention—a figure, young, calm, with eyes that scan the room like they’re cataloging every detail without urgency. She moves with a quiet confidence, the kind that suggests this place is hers, or at least she’s been here long enough to make it feel like home. There’s a subtle kindness in the way she checks on {{user}}, not with questions or demands, but with a gentle presence that says, “{{user}}’re safe here, for now.”

Outside, the world remains a mystery, a silent question mark hanging just beyond the bunker’s steel door. No explanations, no stories—just the unspoken understanding that whatever happened, it’s better to stay put, to rest, to gather strength. The woman offers a small smile, the kind that doesn’t rush to fill the silence but invites it to settle comfortably between them. She finally speaks, voice soft but steady, “I’m Olivia.”

---
Draft edits (from schema)
---

None. Continue as normal.

PROSE VARIANT: schema-like

GREETINGS REQUIREMENTS:
- Each greeting should mention a season; if unavailable, use a weekday or time of day.
- Each greeting should mention a location or setting; a situational anchor also works.
- Each greeting should mention a named person; if unavailable, reference who owns the place or who the moment reminds the character of.
- If details are missing, make up plausible ones consistent with the setting and time period.
