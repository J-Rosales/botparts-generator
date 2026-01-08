from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src import authoring
from src import cli
from src.llm_client import LLMResult


def test_parse_variant_groups() -> None:
    text = (
        "# Root\n"
        "## Intro\n"
        "### Group Alpha\n"
        "Ignored line\n"
        "#### Calm Tone\n"
        "First line\n"
        "Second line\n"
        "#### Storm Front\n"
        "Variant two\n"
        "### Group Beta\n"
        "#### Quiet Mode\n"
        "Only line\n"
    )
    groups = authoring.parse_variant_groups(text)
    assert [group.title for group in groups] == ["Group Alpha", "Group Beta"]
    assert [variant.title for variant in groups[0].variants] == ["Calm Tone", "Storm Front"]
    assert groups[0].variants[0].description == "First line\nSecond line\n"
    assert groups[1].variants[0].description == "Only line\n"


def test_parse_variant_groups_level_three_only() -> None:
    text = (
        "### Calm Tone\n"
        "First line\n"
        "Second line\n"
        "### Storm Front\n"
        "Variant two\n"
    )
    groups = authoring.parse_variant_groups(text)
    assert [group.title for group in groups] == ["Variants"]
    assert [variant.title for variant in groups[0].variants] == ["Calm Tone", "Storm Front"]
    assert groups[0].variants[0].description == "First line\nSecond line\n"
    assert groups[0].variants[1].description == "Variant two\n"


def test_parse_variant_groups_bullets() -> None:
    text = (
        "- Infected: A variant where the apocalypse is caused by a virus.\n"
        "- Gay: Everything is the same, she just happens to be gay.\n"
    )
    groups = authoring.parse_variant_groups(text)
    assert [group.title for group in groups] == ["Variants"]
    assert [variant.title for variant in groups[0].variants] == ["Infected", "Gay"]
    assert groups[0].variants[0].description == "A variant where the apocalypse is caused by a virus.\n"
    assert groups[0].variants[1].description == "Everything is the same, she just happens to be gay.\n"


def test_parse_variant_groups_schema_format() -> None:
    text = (
        "---\n"
        "version: 1\n"
        "---\n"
        "# Character concept (staging selection)\n"
        "Example.\n"
        "## Display name\n"
        "Example\n"
        "## Elaborate prompt notes\n"
        "None.\n"
        "## Draft edits (manual)\n"
        "None.\n"
        "## Audit notes\n"
        "None.\n"
        "## Variant Notes\n"
        "- Infected: A variant where the apocalypse is caused by a virus.\n"
        "- Prepper: Highly trained and armed.\n"
    )
    groups = authoring.parse_variant_groups(text)
    assert [group.title for group in groups] == ["Variants"]
    assert [variant.title for variant in groups[0].variants] == ["Infected", "Prepper"]
    assert groups[0].variants[0].description == "A variant where the apocalypse is caused by a virus.\n"
    assert groups[0].variants[1].description == "Highly trained and armed.\n"


def test_author_variants_creates_runs_and_drafts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path
    sources_root = workspace / "sources"
    prompts_root = workspace / "prompts"
    canonical_path = sources_root / "characters" / "alpha-bot" / "canonical" / "spec_v2_fields.md"
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_path.write_text('{"name": "Alpha Bot"}', encoding="utf-8")
    (sources_root / "characters" / "alpha-bot" / "variants").mkdir(parents=True, exist_ok=True)

    staging_path = sources_root / "staging_drafts.md"
    staging_path.write_text(
        "### Variant Group\n"
        "#### Calm Tone\n"
        "Stay steady.\n"
        "#### Storm Front\n"
        "Heightened tension.\n",
        encoding="utf-8",
    )

    prompt_path = prompts_root / "rewrite_variants" / "01_compact_v1.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("Rewrite prompt", encoding="utf-8")

    monkeypatch.chdir(workspace)

    inputs = iter(["1", "1", "1", "", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    opened: list[Path] = []

    def fake_open(path: Path) -> bool:
        opened.append(path)
        return True

    monkeypatch.setattr(authoring, "try_open_in_editor", fake_open)
    monkeypatch.setattr(
        cli,
        "_invoke_llm",
        lambda *_args, **_kwargs: LLMResult(
            output_text='{"name": "Variant"}',
            model_info={"model": "stub"},
        ),
    )

    args = SimpleNamespace(staging_file=None)
    assert cli._run_author_variants(args, sources_root, prompts_root) == 0

    calm_path = sources_root / "characters" / "alpha-bot" / "variants" / "calm-tone" / "spec_v2_fields.md"
    storm_path = (
        sources_root / "characters" / "alpha-bot" / "variants" / "storm-front" / "spec_v2_fields.md"
    )
    assert calm_path.exists()
    assert storm_path.exists()
    assert calm_path.read_text(encoding="utf-8") == '{"name": "Variant"}\n'
    assert storm_path.read_text(encoding="utf-8") == '{"name": "Variant"}\n'

    assert opened == [calm_path, storm_path]
    for variant_slug in ("calm-tone", "storm-front"):
        runs_root = (
            sources_root / "characters" / "alpha-bot" / "variants" / variant_slug / "runs"
        )
        run_dirs = [path for path in runs_root.iterdir() if path.is_dir()]
        assert run_dirs
        assert (run_dirs[0] / "prompt_ref.txt").exists()
