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
Pearl’s mercenary company was, for now, little more than a name scrawled on a weathered wooden sign hanging crookedly outside a cramped, cluttered room at the edge of town. The sign read “Pearl’s Ventures,” its faded letters promising more than the single occupant could yet deliver. At twenty-three, she carried the restless energy of someone who believed the world was full of opportunities waiting to be seized, even if the odds were stacked against her. The town’s outskirts, where the shadows of dense woods met the cracked cobblestones, were a fitting place for her to start—far enough from the bustling center to avoid scrutiny, close enough to hear the distant hum of trade and politics.

Inside, the room smelled faintly of woodsmoke and damp earth, mingling with the sharp tang of metal tools and leather scraps. Pearl sat cross-legged on a threadbare rug, her fingers busy mending a torn strap on a battered leather satchel. She wasn’t a warrior by any measure; her swordplay was awkward, her aim with a bow uncertain, and her knowledge of battlefield tactics mostly theoretical. Yet, she had something rarer in these uncertain times: a relentless optimism and a willingness to take on any odd job that might bring coin. From courier runs through dangerous woods to negotiating with wary townsfolk, she handled it all with a bright smile and an unshakable can-do attitude.

Her company was a one-woman operation, but Pearl treated it as if it were a growing institution. She kept detailed ledgers, noting every coin earned and spent, every contact made, every rumor overheard in the tavern’s dim corners. She understood that building a mercenary guild was not just about fighting—it was about weaving a network of trust, reputation, and opportunity. The local lord’s militia might scoff at her lack of muscle, but Pearl knew that influence often came from persistence and adaptability rather than brute strength.

Outside, the faint murmur of the town’s political currents drifted through the cracked window. The recent instability in the region had left many smallholders and tradespeople uneasy, and that unease translated into a steady trickle of work for someone willing to step into the gaps. Pearl’s mind often wandered to the larger picture: a world where mercenary companies could serve as stabilizing forces, where adventuring guilds could channel restless energies into rebuilding fractured communities. She imagined a future where her company would grow beyond her solitary efforts, where skilled fighters, tacticians, and negotiators would join under a shared banner.

For now, though, the immediate task was simpler. A local farmer had requested help retrieving a lost mule from the edge of the forest, and Pearl was preparing her gear for the trek. The forest was thick with low magic—whispers of old enchantments and lingering spirits—but nothing too dangerous for someone cautious and curious. She packed a small satchel with essentials, checked the worn map she’d pieced together from various sources, and stepped outside into the cool, fading light of afternoon.

The air was filled with the soft rustle of leaves and the distant clatter of a blacksmith’s hammer. Pearl’s footsteps were light but purposeful as she moved through the uneven streets, nodding to familiar faces who greeted her with a mix of amusement and respect. They saw her as an oddity—a mercenary without a sword arm strong enough to swing a blade properly, a company with no employees—but also as a spark of something new in a town that had grown too used to stagnation.

As she approached the forest’s edge, Pearl paused to breathe in the scent of pine and damp moss. The world beyond the town’s borders was uncertain, but it was also full of possibility. She tightened the straps on her satchel, squared her shoulders, and stepped forward, ready to make her mark one small job at a time. The path ahead was quiet, but Pearl’s mind was alive with plans—not just for the lost mule, but for the future of her company and the role it might play in shaping a more connected, resilient world.

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
