from __future__ import annotations

from pathlib import Path

import pytest

from src import authoring


def test_author_parse_staging() -> None:
    text = "# Alpha\nLine 1\n## Beta\nLine 2\nLine 3\n"
    sections = authoring.parse_staging_sections(text)
    assert [section.title for section in sections] == ["Alpha", "Beta"]
    assert sections[0].content.strip() == "Line 1"
    assert sections[1].content.strip() == "Line 2\nLine 3"


def test_author_scaffold_creation(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    character_dir = authoring.scaffold_character(sources_root, "alpha-bot", "Alpha Bot")
    assert (character_dir / "meta.yaml").exists()
    assert (character_dir / "canonical" / "spec_v2_fields.md").exists()
    assert (character_dir / "canonical" / "shortDescription.md").exists()
    fragments_dir = character_dir / "fragments"
    assert (fragments_dir / ".keep").exists()
    assert (character_dir / "runs").exists()


def test_author_prompt_selection_and_run_log(tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    (prompts_root / "elaborate").mkdir(parents=True)
    prompt_path = prompts_root / "elaborate" / "01_elaborate_v1.md"
    prompt_path.write_text("Prompt body", encoding="utf-8")
    templates = authoring.list_prompt_templates(prompts_root, "elaborate")
    assert templates == [prompt_path]

    run_dir = tmp_path / "runs" / "run-1"
    authoring.write_run_log(
        run_dir,
        prompt_path,
        model_info={"model": "stub"},
        input_payload="input",
        output_text="output",
    )
    assert (run_dir / "prompt_ref.txt").exists()
    assert (run_dir / "model.json").exists()
    assert (run_dir / "input_hash.txt").exists()
    assert (run_dir / "output.md").exists()


@pytest.mark.parametrize("status,expect_error", [("draft", False), ("locked", True)])
def test_audit_validations(tmp_path: Path, status: str, expect_error: bool) -> None:
    sources_root = tmp_path / "sources"
    character_dir = authoring.scaffold_character(sources_root, "alpha-bot", "Alpha Bot", status=status)
    (character_dir / "canonical" / "spec_v2_fields.md").write_text("", encoding="utf-8")
    (character_dir / "canonical" / "shortDescription.md").write_text("", encoding="utf-8")
    audit = authoring.audit_character(sources_root, "alpha-bot", strict=False)
    assert bool(audit.errors) is expect_error
