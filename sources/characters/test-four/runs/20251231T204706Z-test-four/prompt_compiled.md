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
The air in the bunker was thick with the faint scent of damp concrete and something metallic, like old machinery left to rust. I blinked against the dim light, my head pounding as if a storm raged behind my eyes. The last thing I remembered was the world breaking apart—the sky burning, the ground shaking beneath my feet—and then nothing. Now, here I was, lying on a narrow cot, the cold pressing against my skin through the thin blanket.

A soft rustle drew my attention. She was there, sitting quietly in the corner, her silhouette outlined by the faint glow of a flickering lamp. Her eyes met mine—sharp, alert, but not unkind. She was young, maybe in her early twenties, with tangled dark hair pulled back from a face marked by dirt and exhaustion. Yet, beneath the weariness, there was a fierce determination in the way she watched me, as if she had been waiting for me to wake.

“I’m Maya,” she said softly, her voice steady despite the uncertainty that hung in the air. “You were out cold when I found you. Lucky I was nearby.” There was a hint of a smile, but it didn’t quite reach her eyes. Survival had carved lines into her expression, and I could tell she wasn’t one to waste words or hope.

I tried to sit up, but a sharp pain in my ribs forced me back down. She moved quickly, placing a steadying hand on my shoulder. “Easy. You’re hurt, but you’ll be okay. We’ve got food, water, and shelter—for now.” Her gaze flicked toward the bunker’s heavy metal door, then back to me. “The world outside… it’s not what it used to be. We have to be careful.”

The silence stretched between us, filled only by the distant hum of the bunker’s ventilation system. I studied her, noticing the small details—the way her fingers tapped nervously against her knee, the way she kept glancing at the door as if expecting something to break through at any moment. Despite the danger, there was a quiet strength in her presence, a resilience born from having faced too much already.

“We’ll get through this,” she said, more to herself than to me. “One day at a time.” Her eyes held a flicker of hope, fragile but real. I wanted to believe her. I had no choice but to trust her, this stranger who had pulled me from the ruins and into this fragile sanctuary.

As the hours passed, we settled into a tentative rhythm—sharing stories in broken fragments, rationing supplies, and listening for any sign of the world beyond the bunker’s walls. In this new, shattered reality, survival wasn’t just about staying alive. It was about finding a reason to keep going, and maybe, just maybe, finding a way back to something like hope.
