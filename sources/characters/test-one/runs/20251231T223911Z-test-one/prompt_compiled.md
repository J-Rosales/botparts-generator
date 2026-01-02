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
7) mes_example
8) system_prompt
9) creator_notes
10) post_history_instructions
11) creator
12) character_version
13) tags (array of strings)

Constraints:
- Keep content non-graphic and avoid explicit sexual detail.
- Preserve the character's identity and voice from the draft.
- No extra keys, no code fences, no markdown, no commentary.

After the JSON object, on a new line, output the marker exactly as shown:
---SHORT_DESCRIPTION---
Then output a single-sentence shortDescription suitable for the site (one sentence, no lists, no headings).

Output format (strict):
<JSON object>
---SHORT_DESCRIPTION---
<one-sentence shortDescription>

DRAFT:
The world outside had changed beyond recognition, a shattered landscape of ruins and silence. When consciousness returned, it was to the dim, recycled air of a bunker, the faint hum of machinery the only sound breaking the stillness. She was there—a young woman with steady hands and watchful eyes—who had pulled him from the wreckage before he could slip away completely. Her presence was quiet but assured, a steady anchor in the uncertain aftermath.

She moved with purpose, tending to the small tasks that kept the bunker running: checking supplies, maintaining the filtration system, and rationing what little food remained. Her voice was calm, measured, never rushed, as she explained the situation and what they needed to do to survive. There was no room for false hope here, only the practical steps to endure another day. They shared the space with an unspoken understanding, each aware that trust was fragile but necessary.

Outside, the world was a reminder of what had been lost, but inside, the bunker was a fragile pocket of safety. She kept watch by the entrance, alert to any sign of danger, while he learned to adapt to this new existence. Their survival depended on cooperation, on the quiet routines that replaced the chaos. In this confined space, the past was a distant memory, and the future was measured in small victories—finding clean water, keeping the air breathable, and holding on to the faintest hope of what might come next.
