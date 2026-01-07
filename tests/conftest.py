from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def build_command() -> str | None:
    return os.environ.get("BOTPARTS_BUILD_CMD")


def _copy_repo_for_build(tmp_path: Path, repo_root: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "dist")
    for item in repo_root.iterdir():
        if item.name in {".git", "dist"}:
            continue
        target = workspace / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=ignore)
        else:
            shutil.copy2(item, target)
    return workspace


def seed_character_sources(workspace: Path, slug: str = "example-bot") -> Path:
    character_dir = workspace / "sources" / "characters" / slug
    canonical_dir = character_dir / "canonical"
    canonical_dir.mkdir(parents=True, exist_ok=True)
    (character_dir / "variants").mkdir(parents=True, exist_ok=True)
    fragments_dir = character_dir / "fragments"
    fragments_dir.mkdir(parents=True, exist_ok=True)
    (fragments_dir / ".keep").write_text("", encoding="utf-8")
    spec_payload = {
        "slug": slug,
        "name": "Example Bot",
        "description": "An example character for generator tests.",
        "tags": ["friendly"],
    }
    (canonical_dir / "spec_v2_fields.md").write_text(
        json.dumps(spec_payload, indent=2),
        encoding="utf-8",
    )
    (canonical_dir / "shortDescription.md").write_text("Example short description.\n", encoding="utf-8")
    return character_dir


def _run_subprocess(command: str, cwd: Path) -> None:
    args = shlex.split(command)
    subprocess.run(args, check=True, cwd=cwd)


def _fallback_build(workspace: Path) -> None:
    from src.generator import build_site_data

    placeholders = int(os.environ.get("BOTPARTS_PLACEHOLDERS", "0") or "0")
    include_timestamps = os.environ.get("BOTPARTS_INCLUDE_TIMESTAMPS", "0") == "1"
    build_site_data(workspace, placeholders=placeholders, include_timestamps=include_timestamps)


@pytest.fixture()
def built_workspace(tmp_path: Path, repo_root: Path, build_command: str | None) -> Path:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
    seed_character_sources(workspace)
    if build_command:
        _run_subprocess(build_command, workspace)
    else:
        _fallback_build(workspace)
    return workspace


def hash_directory(directory: Path) -> str:
    hasher = hashlib.sha256()
    files = sorted(path for path in directory.rglob("*") if path.is_file())
    for file_path in files:
        relative = file_path.relative_to(directory)
        hasher.update(str(relative).encode("utf-8"))
        hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_json_files(root: Path) -> Iterable[Path]:
    return (path for path in root.rglob("*.json") if path.is_file())
