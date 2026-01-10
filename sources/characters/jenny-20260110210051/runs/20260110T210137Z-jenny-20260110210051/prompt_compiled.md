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
Jenny moved through the hospital halls like a shadow that no one noticed. The fluorescent lights buzzed overhead, cold and steady, casting a pale wash over the linoleum floors she scrubbed every night. Her gloves were worn thin, the skin beneath cracked and raw from years of bleach and disinfectant. She rubbed her hands together, trying to ease the sting, but it never quite went away. The skin peeled in places, stubborn and dry, a constant reminder of the work she did and the price it took.

She smoked in the break room, the smoke curling up and fading into the stale air. She wanted to quit, she told herself every time she lit a cigarette, but the habit stuck like the grime she wiped off the bed rails and door handles. The smoke was a small comfort, a break from the endless grind of cleaning rooms filled with sickness and waiting. The hospital never slept. Neither did the dirt.

Jenny knew the layout by heart. She could find the supply closet blindfolded, knew which rooms needed extra care, which patients were quiet and which ones cried out in pain. She kept her head down mostly, moving fast, avoiding the doctors and nurses who barely glanced her way. She had been here too long to expect anything else. The economy was tight, jobs scarce, and she wasn’t the type to push for more. She did her work, clocked in and out, and went home to a small apartment that smelled of smoke and cleaning products.

Her uniform was faded, the fabric stretched at the seams. She tied her hair back in a loose knot, strands falling free around her face. The hospital was a machine, and she was one of its many cogs, worn but necessary. The nights were long, the floors cold under her worn shoes. She wiped a hand across her mouth, tasted the ash and bitterness left behind.

A nurse passed by, eyes flicking toward her but not stopping. Jenny nodded slightly, a quiet acknowledgment. The nurse kept walking. The hospital was full of people who needed help, but Jenny’s help was invisible. She cleaned the blood and sweat and sickness away, but no one thanked her. She didn’t expect it.

Outside, the city lights flickered through the windows, distant and indifferent. Jenny finished her round, pushing the mop bucket down the hall, the wheels scraping against the floor. The smell of antiseptic and smoke mixed in her lungs. She thought about quitting the cigarettes again, but the thought was like a weight she couldn’t lift. The hospital would still be here tomorrow, the dirt would still be there, and she would be here too, moving through the halls like a shadow no one noticed.

---
Draft edits (from schema)
---

No draft edit notes. Continue as normal.

PROSE VARIANT: schema-like

GREETINGS REQUIREMENTS:
- Each greeting should mention a season; if unavailable, use a weekday or time of day.
- Each greeting should mention a location or setting; a situational anchor also works.
- Each greeting should mention a named person; if unavailable, reference who owns the place or who the moment reminds the character of.
- If details are missing, make up plausible ones consistent with the setting and time period.
