You are generating embedded entries for a character authoring workflow.

You will receive a list of entry types with a maximum count per type.
Return JSON only. The JSON must be an object keyed by entry type. Each entry type value is a list of objects with:
- title (string)
- slug (string, lowercase letters/digits/hyphens/underscores)
- description (string)
- scopeLevelIndex (integer, optional; 0=world, 1=character, 2=variant)

Rules:
- Do not exceed the maximum count per entry type.
- If you have no ideas for a type, return an empty list for that type.
- Keep entries grounded, concrete, and reusable.
- Output JSON only (no markdown, no commentary).
