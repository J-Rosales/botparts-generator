You are converting a single embedded entry input into a structured embedded entry.

You will receive:
- Entry type
- Name
- Description

Return JSON only with:
- title (string)
- slug (string, lowercase letters/digits/hyphens/underscores)
- description (string)
- score (number, optional)

Rules:
- Keep the description concise and grounded.
- Preserve the provided name as the title unless a minor normalization is needed.
- Output JSON only (no markdown, no commentary).
