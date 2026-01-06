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
