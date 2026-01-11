You are enriching a single embedded entry for a character authoring workflow.

You will receive the entry type plus a title, slug, and short description.
Return JSON only. The JSON must include:
- content (string; expand the description into concrete, grounded details: names, ages, systems, procedures, places, timelines, etc.)
- keys (array of strings; trigger words/phrases, including named entities and distinctive terms)
- title (string, optional; repeat for validation)
- slug (string, optional; repeat for validation)

Rules:
- content must be non-empty.
- keys must be a non-empty array of non-empty strings.
- Keep content consistent with the entry description and entry type.
- Output JSON only (no markdown, no commentary).
