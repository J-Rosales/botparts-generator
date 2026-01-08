from __future__ import annotations

from pathlib import Path

from src import cli


def test_resolve_manifest_prompt_retries(monkeypatch, tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    prompt_dir = prompts_root / "elaborate"
    prompt_dir.mkdir(parents=True)
    target = prompt_dir / "valid.md"
    target.write_text("Prompt body", encoding="utf-8")

    responses = iter(["valid.md"])

    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    resolved = cli._resolve_manifest_prompt(
        prompts_root,
        "elaborate",
        "missing.md",
        "prompts.elaborate",
    )
    assert resolved == target


def test_schema_template_prompts_skip_optional_prompting(monkeypatch, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sources_root = repo_root / "sources"
    template_prompts = cli._load_schema_template_prompts(sources_root)
    assert "idiosyncrasy_module" in template_prompts

    prompts_root = tmp_path / "prompts"
    prompt_dir = prompts_root / "idiosyncrasy_module"
    prompt_dir.mkdir(parents=True)
    prompt_name = template_prompts["idiosyncrasy_module"]
    target = prompt_dir / prompt_name
    target.write_text("Prompt body", encoding="utf-8")

    manifest_prompts = {
        "elaborate": "01_elaborate_v1.md",
        "extract_fields": "01_specv2_fields_v1.md",
        "tone": "01_neutral_v1.md",
        "style": "01_neutral_v1.md",
        "voice": "01_neutral_v1.md",
    }
    merged_prompts = {**template_prompts, **manifest_prompts}

    def fail_input(_: str) -> str:
        raise AssertionError("Input prompt was called unexpectedly.")

    monkeypatch.setattr("builtins.input", fail_input)

    resolved = cli._resolve_optional_manifest_prompt(
        prompts_root,
        "idiosyncrasy_module",
        merged_prompts,
        "idiosyncrasy_module",
    )
    assert resolved == target
