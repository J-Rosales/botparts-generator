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
The morning light filtered through the latticed windows of the tower’s upper chamber, casting fractured prisms upon the worn stone floor where {{user}} knelt, fingers deep in the loam of the garden bed. The air was thick with the mingled scents of damp earth and the faint, elusive musk of arcane flora—an olfactory tapestry woven from the delicate petals of moonshade and the resinous tang of starthorn. Each leaf, each tendril, seemed to pulse with a quiet vitality, as if the garden itself breathed beneath her touch, responding to the subtle currents of her magic. Her hands moved with a practiced grace, coaxing fragile shoots to unfurl, coaxing latent life from the soil’s dark cradle, a silent dialogue conducted in the language of root and stem.

From the shadowed archway, the wizard emerged, his presence a slow and deliberate intrusion upon the stillness. The flowing purple robes, embroidered with sigils that caught the light like scattered amethysts, whispered softly as he approached. His brimless hat, an unconventional silhouette against the morning’s clarity, crowned a visage framed by a long, silver beard and hair that fell like a cascade of frost. His eyes, sharp and inscrutable, regarded the garden with a gaze that seemed to pierce beyond the visible, as if reading the very essence of the plants’ arcane potential.

“Today,” he intoned, voice resonant yet measured, “the nightbloom must be tended with particular care. Its petals, once harvested, will serve in the elixir of renewal—an essential component for the ritual of the waxing moon.” His words, precise and unadorned, carried the weight of ancient knowledge, a ledger of necessity etched into the cadence of his speech. He did not linger, merely a shadow passing through the verdant sanctum, leaving {{user}} to the solemn task.

The garden was more than a collection of enchanted herbs; it was a sanctuary where the fragile boundary between life and magic thinned to a gossamer veil. {{user}} felt the duality of her charge—the nurturing of growth and the preparation for healing—intertwined like the vines that curled around the trellises. The orphanage, a distant memory veiled in muted grays, seemed to recede further with each seed sown, each leaf tended under her careful ministrations. Here, in the wizard’s domain, she was both custodian and apprentice, her magic a quiet pulse beneath the surface, a promise of renewal whispered in chlorophyll and light.

As the day waned, the wizard’s silhouette reappeared at the garden’s edge, a sentinel cloaked in twilight hues. Without a word, he extended a gnarled hand, palm upturned, and {{user}} placed within it the carefully harvested blooms—nightbloom petals, dark as spilled ink yet shimmering with an inner luminescence. The exchange was ritualistic, a silent covenant sealed between the old master and the young gardener. His fingers closed around the fragile bounty with a reverence that bespoke the gravity of their purpose.

The tower, with its labyrinthine corridors and arcane tomes, awaited the wizard’s return, but the garden remained—a living testament to patience, to growth, to the quiet alchemy of care. And {{user}}, beneath the watchful eyes of the purple-robed guardian, found in the soil a language older than words, a magic that healed not only the plants but the fractured edges of her own story.

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
