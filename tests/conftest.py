from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def _run_subprocess(command: str, cwd: Path) -> None:
    args = shlex.split(command)
    subprocess.run(args, check=True, cwd=cwd)


def _fallback_build(workspace: Path) -> None:
    sources_root = workspace / "sources"
    output_root = workspace / "dist" / "src" / "data"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    site_seed = sources_root / "site-seed" / "index.json"
    if site_seed.exists():
        shutil.copy2(site_seed, output_root / "index.json")

    characters_root = sources_root / "characters"
    if not characters_root.exists():
        return

    for character_dir in characters_root.iterdir():
        if not character_dir.is_dir():
            continue
        manifest_source = character_dir / "manifest.json"
        if not manifest_source.exists():
            continue
        dest_dir = output_root / "characters" / character_dir.name
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_source, dest_dir / "manifest.json")

        fragments_source = character_dir / "fragments"
        fragments_dest = dest_dir / "fragments"
        fragments_dest.mkdir(parents=True, exist_ok=True)
        if fragments_source.exists():
            for fragment in fragments_source.iterdir():
                if fragment.is_file():
                    shutil.copy2(fragment, fragments_dest / fragment.name)
        if not any(fragments_dest.iterdir()):
            (fragments_dest / ".keep").write_text("", encoding="utf-8")


@pytest.fixture()
def built_workspace(tmp_path: Path, repo_root: Path, build_command: str | None) -> Path:
    workspace = _copy_repo_for_build(tmp_path, repo_root)
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
