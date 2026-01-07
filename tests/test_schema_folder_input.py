import re
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "schema-folder-input.md"


def test_schema_folder_input_fixture_is_valid():
    content = FIXTURE_PATH.read_text(encoding="utf-8")

    frontmatter_match = re.match(r"\A---\n(.*?)\n---\n", content, flags=re.DOTALL)
    assert frontmatter_match, "Expected YAML frontmatter enclosed by --- at the top of the file."

    frontmatter = frontmatter_match.group(1)
    assert "version:" in frontmatter, "Frontmatter must include version."
    assert "prompts:" in frontmatter, "Frontmatter must include prompts."

    body = content[frontmatter_match.end():]

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", flags=re.MULTILINE)
    headings = [(len(match.group(1)), match.group(2).strip()) for match in heading_pattern.finditer(body)]

    invalid_heading = next(
        (
            text
            for level, text in headings
            if level >= 3
        ),
        None,
    )
    assert (
        invalid_heading is None
    ), "Unsupported heading level found. Use bullet list items under ## Variant notes instead of ### headings."

    h1_headings = [text for level, text in headings if level == 1]
    assert len(h1_headings) == 1, "Expected exactly one H1 heading."
    assert (
        h1_headings[0] == "Character concept (staging selection)"
    ), "H1 heading must be 'Character concept (staging selection)'."

    allowed_h2 = {
        "Display name",
        "Elaborate prompt notes",
        "Draft edits (manual)",
        "Audit notes",
        "Variant notes",
    }
    h2_headings = [text for level, text in headings if level == 2]
    disallowed_h2 = [text for text in h2_headings if text not in allowed_h2]
    assert not disallowed_h2, f"Unsupported H2 headings found: {disallowed_h2}"
    assert "Variant notes" in h2_headings, "Expected a ## Variant notes section."
