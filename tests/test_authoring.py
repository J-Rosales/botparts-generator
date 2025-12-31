from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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
        [prompt_path],
        prompt_compiled="Compiled prompt",
        model_info={"model": "stub"},
        input_payload="input",
        output_text="output",
    )
    assert (run_dir / "prompt_ref.txt").exists()
    assert (run_dir / "prompt_compiled.md").exists()
    assert (run_dir / "model.json").exists()
    assert (run_dir / "input_hash.txt").exists()
    assert (run_dir / "output.md").exists()


def test_ensure_preliminary_draft_appends(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    character_dir = authoring.scaffold_character(sources_root, "alpha-bot", "Alpha Bot")
    draft_path = authoring.ensure_preliminary_draft(character_dir, "First draft\n", run_id="run-1")
    assert draft_path.exists()
    assert draft_path.read_text(encoding="utf-8") == "First draft\n"

    draft_path = authoring.ensure_preliminary_draft(character_dir, "Second draft\n", run_id="run-2")
    expected = "First draft\n\n---\nElaboration appended run-2\n---\n\nSecond draft\n"
    assert draft_path.read_text(encoding="utf-8") == expected


def test_list_and_delete_character_dirs(tmp_path: Path) -> None:
    sources_root = tmp_path / "sources"
    characters_root = sources_root / "characters"
    (characters_root / "alpha").mkdir(parents=True)
    (characters_root / "bravo").mkdir(parents=True)
    extra_file = sources_root / "notes.md"
    extra_file.write_text("Keep me", encoding="utf-8")

    dirs = authoring.list_character_dirs(sources_root)
    assert {path.name for path in dirs} == {"alpha", "bravo"}

    authoring.delete_character_dirs(dirs)
    assert not (characters_root / "alpha").exists()
    assert not (characters_root / "bravo").exists()
    assert extra_file.exists()


def test_try_open_in_editor_uses_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "preliminary_draft.md"
    calls: list[list[str]] = []

    def fake_popen(cmd: list[str]) -> SimpleNamespace:
        calls.append(cmd)
        return SimpleNamespace()

    monkeypatch.setenv("BOTPARTS_EDITOR", "echo --reuse-window")
    monkeypatch.setattr(authoring.subprocess, "Popen", fake_popen)

    assert authoring.try_open_in_editor(target) is True
    assert calls == [["echo", "--reuse-window", str(target)]]


def test_try_open_in_editor_returns_false_without_editor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("BOTPARTS_EDITOR", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    monkeypatch.setattr(authoring.shutil, "which", lambda _: None)

    assert authoring.try_open_in_editor(tmp_path / "preliminary_draft.md") is False


@pytest.mark.parametrize("status,expect_error", [("draft", False), ("locked", True)])
def test_audit_validations(tmp_path: Path, status: str, expect_error: bool) -> None:
    sources_root = tmp_path / "sources"
    character_dir = authoring.scaffold_character(sources_root, "alpha-bot", "Alpha Bot", status=status)
    (character_dir / "canonical" / "spec_v2_fields.md").write_text("", encoding="utf-8")
    (character_dir / "canonical" / "shortDescription.md").write_text("", encoding="utf-8")
    audit = authoring.audit_character(sources_root, "alpha-bot", strict=False)
    assert bool(audit.errors) is expect_error
