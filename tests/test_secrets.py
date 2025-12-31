from __future__ import annotations

import os
from pathlib import Path

from src.secrets import load_secrets_file


def test_load_secrets_missing_file_does_nothing(tmp_path: Path, monkeypatch) -> None:
    missing = tmp_path / ".secrets"
    monkeypatch.delenv("MISSING_SECRETS_TEST", raising=False)
    load_secrets_file(missing)
    assert "MISSING_SECRETS_TEST" not in os.environ


def test_load_secrets_parses_key_value(tmp_path: Path, monkeypatch) -> None:
    secrets_file = tmp_path / ".secrets"
    secrets_file.write_text(
        "\n# comment\n\nBOTPARTS_LLM_API_KEY=sk-test\nINVALID\n=NOPE\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("BOTPARTS_LLM_API_KEY", raising=False)
    loaded = load_secrets_file(secrets_file)
    assert os.environ["BOTPARTS_LLM_API_KEY"] == "sk-test"
    assert loaded == {"BOTPARTS_LLM_API_KEY": "sk-test"}


def test_load_secrets_does_not_override_existing_env(tmp_path: Path, monkeypatch) -> None:
    secrets_file = tmp_path / ".secrets"
    secrets_file.write_text("BOTPARTS_LLM_API_KEY=sk-new\n", encoding="utf-8")
    monkeypatch.setenv("BOTPARTS_LLM_API_KEY", "sk-existing")
    loaded = load_secrets_file(secrets_file)
    assert os.environ["BOTPARTS_LLM_API_KEY"] == "sk-existing"
    assert loaded == {}
