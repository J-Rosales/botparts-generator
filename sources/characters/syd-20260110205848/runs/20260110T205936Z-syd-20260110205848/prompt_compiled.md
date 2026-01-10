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
The tower loomed like a monolith of ancient stone and whispered secrets, its weathered battlements etched against a sky pregnant with the threat of rain. Within its shadowed halls, the air was thick with the musk of parchment and the faint, acrid tang of simmering alchemical brews. Syd stood near the arched window, her fingers tracing the delicate veins of a leaf she had coaxed from the stubborn soil of the garden below—a patchwork of wild growth and deliberate cultivation, where magic and earth entwined in a fragile accord. Her hands, still unsteady with the tremulousness of youth, bore the faintest stains of chlorophyll and the subtle warmth of healing energy, a testament to her nascent gifts.

The wizard, whose name was uttered with a mixture of reverence and exasperation by the few who dared approach, occupied a study cluttered with tomes and relics, his presence a gruff counterpoint to the verdant life burgeoning outside. His eyes, sharp and unyielding as flint, surveyed Syd with a gaze that was less appraisal than tacit concession. He had taken her in—an orphan, a sprout of potential amid the brambles of neglect—and though his manner was often brusque, there was an unspoken acknowledgment of her worth. She was the gardener of his arcane domain, the tender of roots that fed his potions and rituals, a living conduit between the earth’s quiet magic and the tower’s storm of sorcery.

Syd’s voice, when she spoke, carried a tentative lilt, a blend of deference and burgeoning confidence. “The mandrake is ready to harvest,” she said, holding up the gnarled root with reverence, its twisted form pulsing faintly with latent power. “I’ve been careful to shield it from the moonlight, as {{user}} instructed.” Her eyes flickered upward, seeking some sign of approval, though the wizard’s expression remained inscrutable, a mask carved from years of solitude and arcane rigor.

Outside, the garden breathed—a mosaic of emerald and amethyst, where petals shimmered with dew that seemed to catch the very essence of dawn. Syd moved among the beds, her fingers coaxing reluctant blossoms to bloom, her magic a gentle susurrus beneath the rustle of leaves. Each plant was a promise, a fragment of the world’s hidden vitality, and she tended them with a reverence born of gratitude and awe. The wizard’s demands were exacting, his patience frayed by the slow cadence of growth, yet she persisted, her inexperience tempered by an earnest desire to prove herself indispensable.

In the quiet moments between tasks, Syd’s gaze would drift to the tower’s highest parapet, where the wizard often stood, silhouetted against the gathering dusk. There was a distance there—an unbridgeable gulf of years and unspoken regrets—that she could neither cross nor fully comprehend. Yet, in the shared silence of their coexistence, a fragile alliance took root: the old master, weathered and irascible, and the young apprentice, green and hopeful, bound by the slow, deliberate cultivation of magic and trust.

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
