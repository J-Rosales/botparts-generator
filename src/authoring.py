from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


HEADING_PATTERN = re.compile(r"^(?P<level>#+)\s+(?P<title>.+?)\s*$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRAGMENT_SECTION_TARGETS = {
    "description": ("spec_v2", "description.md"),
    "system_prompt": ("spec_v2", "system_prompt.md"),
    "first_message": ("spec_v2", "first_message.md"),
    "scenario": ("spec_v2", "scenario.md"),
    "post_history_instructions": ("spec_v2", "post_history_instructions.md"),
    "short_description": ("site", "shortDescription.md"),
    "shortdescription": ("site", "shortDescription.md"),
}


@dataclass(frozen=True)
class HeadingSection:
    title: str
    level: int
    content: str


@dataclass(frozen=True)
class AuditResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_staging_sections(text: str) -> list[HeadingSection]:
    sections: list[HeadingSection] = []
    current_title: str | None = None
    current_level: int | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_level, current_lines
        if current_title is None or current_level is None:
            return
        sections.append(
            HeadingSection(
                title=current_title,
                level=current_level,
                content="\n".join(current_lines).strip() + "\n",
            )
        )
        current_title = None
        current_level = None
        current_lines = []

    for line in text.splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            flush()
            current_title = match.group("title").strip()
            current_level = len(match.group("level"))
            current_lines = []
        else:
            current_lines.append(line)

    flush()
    return sections


def select_section_by_title(sections: Iterable[HeadingSection], title: str) -> HeadingSection | None:
    for section in sections:
        if section.title == title:
            return section
    return None


def slugify(value: str) -> str:
    raw = value.strip().lower()
    raw = re.sub(r"[^a-z0-9\s-]", "", raw)
    raw = re.sub(r"\s+", "-", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw


def validate_slug(slug: str) -> None:
    if len(slug) < 3 or not SLUG_PATTERN.match(slug):
        raise ValueError(
            "Invalid slug. Use at least 3 characters with lowercase letters, digits, "
            "and hyphens only (example: kemono-scout)."
        )


def find_staging_draft_paths(sources_root: Path) -> list[Path]:
    drafts_file = sources_root / "staging_drafts.md"
    if drafts_file.exists():
        return [drafts_file]
    drafts_dir = sources_root / "staging_drafts"
    if drafts_dir.exists() and drafts_dir.is_dir():
        return sorted(drafts_dir.glob("*.md"))
    return []


def scaffold_character(
    sources_root: Path,
    slug: str,
    display_name: str,
    status: str = "draft",
) -> Path:
    validate_slug(slug)
    character_dir = sources_root / "characters" / slug
    if character_dir.exists():
        raise FileExistsError(f"Character '{slug}' already exists.")
    (character_dir / "canonical").mkdir(parents=True, exist_ok=True)
    (character_dir / "variants").mkdir(parents=True, exist_ok=True)
    fragments_dir = character_dir / "fragments"
    fragments_dir.mkdir(parents=True, exist_ok=True)
    (fragments_dir / ".keep").write_text("", encoding="utf-8")
    (fragments_dir / "spec_v2").mkdir(parents=True, exist_ok=True)
    (fragments_dir / "spec_v2" / ".keep").write_text("", encoding="utf-8")
    (fragments_dir / "site").mkdir(parents=True, exist_ok=True)
    (fragments_dir / "site" / ".keep").write_text("", encoding="utf-8")
    (character_dir / "runs").mkdir(parents=True, exist_ok=True)

    meta_path = character_dir / "meta.yaml"
    meta_payload = [
        f"slug: {slug}",
        f"displayName: {display_name}",
        f"status: {status}",
    ]
    meta_path.write_text("\n".join(meta_payload) + "\n", encoding="utf-8")

    (character_dir / "staging_snapshot.md").write_text("", encoding="utf-8")
    (character_dir / "preliminary_draft.md").write_text("", encoding="utf-8")
    (character_dir / "canonical" / "spec_v2_fields.md").write_text("", encoding="utf-8")
    (character_dir / "canonical" / "shortDescription.md").write_text("", encoding="utf-8")
    return character_dir


def write_staging_snapshot(character_dir: Path, section: HeadingSection) -> None:
    snapshot_path = character_dir / "staging_snapshot.md"
    snapshot_path.write_text(section.content, encoding="utf-8")


def list_prompt_templates(prompts_root: Path, category: str) -> list[Path]:
    template_dir = prompts_root / category
    if not template_dir.exists():
        return []
    return sorted(path for path in template_dir.iterdir() if path.is_file())


def list_character_dirs(sources_root: Path) -> list[Path]:
    characters_root = sources_root / "characters"
    if not characters_root.exists():
        return []
    resolved_root = characters_root.resolve()
    directories: list[Path] = []
    for path in sorted(characters_root.iterdir()):
        if path.is_symlink():
            continue
        if not path.is_dir():
            continue
        resolved_path = path.resolve()
        if resolved_path.parent != resolved_root:
            continue
        directories.append(path)
    return directories


def delete_character_dirs(dirs: list[Path]) -> None:
    for path in dirs:
        if path.is_symlink():
            continue
        if path.is_dir():
            shutil.rmtree(path)


def write_run_log(
    run_dir: Path,
    prompt_paths: Iterable[Path],
    prompt_compiled: str,
    model_info: dict[str, Any],
    input_payload: str,
    output_text: str,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_ref = run_dir / "prompt_ref.txt"
    prompt_entries: list[str] = []
    for prompt_path in prompt_paths:
        prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        prompt_entries.append(f"{prompt_path.as_posix()}\nsha256:{prompt_hash}")
    prompt_ref.write_text("\n\n".join(prompt_entries) + "\n", encoding="utf-8")
    (run_dir / "prompt_compiled.md").write_text(prompt_compiled, encoding="utf-8")

    (run_dir / "model.json").write_text(
        json_dumps(model_info),
        encoding="utf-8",
    )
    input_hash = hashlib.sha256(input_payload.encode("utf-8")).hexdigest()
    (run_dir / "input_hash.txt").write_text(f"sha256:{input_hash}\n", encoding="utf-8")
    (run_dir / "output.md").write_text(output_text, encoding="utf-8")


def ensure_preliminary_draft(
    character_dir: Path,
    elaboration_text: str,
    run_id: str | None = None,
) -> Path:
    draft_path = character_dir / "preliminary_draft.md"
    cleaned_text = elaboration_text.rstrip("\n") + "\n"
    if not draft_path.exists():
        draft_path.write_text(cleaned_text, encoding="utf-8")
        return draft_path

    existing = draft_path.read_text(encoding="utf-8")
    if not existing.strip():
        draft_path.write_text(cleaned_text, encoding="utf-8")
        return draft_path

    # Append with a delimiter to avoid overwriting any author edits.
    run_label = run_id or "unknown-run"
    delimiter = f"\n\n---\nElaboration appended {run_label}\n---\n\n"
    draft_path.write_text(existing.rstrip() + delimiter + cleaned_text, encoding="utf-8")
    return draft_path


def try_open_in_editor(path: Path) -> bool:
    editor_cmd = os.environ.get("BOTPARTS_EDITOR") or os.environ.get("EDITOR")
    if editor_cmd:
        cmd = shlex.split(editor_cmd, posix=os.name != "nt")
    else:
        code_path = shutil.which("code")
        if not code_path:
            return False
        cmd = [code_path, "--reuse-window"]
    if not cmd:
        return False
    cmd.append(str(path))
    try:
        subprocess.Popen(cmd)
    except Exception:
        print("Note: Unable to open editor automatically.")
        return False
    return True


def json_dumps(payload: Any) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def parse_meta_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if text.strip().startswith("{"):
        import json

        return json.loads(text)
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if current_list_key and stripped.startswith("-"):
            value = stripped[1:].strip()
            data[current_list_key].append(_parse_scalar(value))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list_key = key
            continue
        current_list_key = None
        data[key] = _parse_scalar(value)
    return data


def _parse_scalar(value: str) -> Any:
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "none"}:
        return None
    if value.isdigit():
        return int(value)
    if value.startswith("[") and value.endswith("]"):
        import json

        return json.loads(value)
    return value.strip("\"")


def load_spec_fields(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    payload_text = _extract_json_payload(text)
    if payload_text is None:
        return {}
    import json

    return json.loads(payload_text)


def _extract_json_payload(text: str) -> str | None:
    fenced = re.search(r"```json\s*(?P<body>[\s\S]*?)\s*```", text)
    if fenced:
        return fenced.group("body")
    if text.startswith("{") and text.endswith("}"):
        return text
    return None


def load_short_description(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def audit_character(sources_root: Path, slug: str, strict: bool = False) -> AuditResult:
    errors: list[str] = []
    warnings: list[str] = []
    character_dir = sources_root / "characters" / slug
    if not character_dir.exists():
        errors.append(f"Missing character directory: {character_dir}")
        return AuditResult(errors=errors, warnings=warnings)

    meta_path = character_dir / "meta.yaml"
    if not meta_path.exists():
        errors.append(f"Missing meta.yaml at {meta_path}")
        return AuditResult(errors=errors, warnings=warnings)

    meta = parse_meta_yaml(meta_path)
    status = str(meta.get("status", "draft"))

    canonical_dir = character_dir / "canonical"
    required_files = [
        (canonical_dir / "spec_v2_fields.md", "canonical/spec_v2_fields.md"),
        (canonical_dir / "shortDescription.md", "canonical/shortDescription.md"),
    ]
    for path, label in required_files:
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            message = f"Missing or empty {label} for {slug}."
            if status == "locked":
                errors.append(message)
            else:
                warnings.append(message)

    fragments_dir = character_dir / "fragments"
    if not fragments_dir.exists():
        warnings.append(f"Missing fragments/ directory for {slug}.")
    else:
        entries = list(fragments_dir.iterdir())
        if not entries:
            warnings.append(f"fragments/ is empty for {slug}; include .keep placeholder.")

    prompt_refs = _collect_prompt_refs(character_dir / "runs")
    for family in ("tone", "voice", "style"):
        if not _has_prompt_family(prompt_refs, family):
            message = f"Missing {family} prompt selection for {slug}."
            if status == "locked":
                errors.append(message)
            else:
                warnings.append(message)

    if strict and warnings:
        errors.extend(warnings)
        warnings = []

    return AuditResult(errors=errors, warnings=warnings)


def build_run_id(slug: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{slug}"


def extract_output_sections(output_text: str) -> tuple[str, str]:
    marker = "---SHORT_DESCRIPTION---"
    if marker in output_text:
        spec_text, short_text = output_text.split(marker, 1)
        return spec_text.strip() + "\n", short_text.strip()
    match = re.search(r"SHORT_DESCRIPTION:\s*(?P<short>.+)", output_text)
    if match:
        short_text = match.group("short").strip()
        spec_text = output_text[: match.start()].strip()
        return spec_text + "\n", short_text
    return output_text.strip() + "\n", ""


def parse_fragment_sections(output_text: str) -> dict[str, str]:
    sections = parse_staging_sections(output_text)
    fragments: dict[str, str] = {}
    for section in sections:
        normalized = _normalize_fragment_title(section.title)
        if normalized not in FRAGMENT_SECTION_TARGETS:
            continue
        fragments[normalized] = section.content.strip() + "\n"
    return fragments


def write_extracted_fragments(character_dir: Path, output_text: str) -> list[str]:
    fragments = parse_fragment_sections(output_text)
    if not fragments:
        return ["No fragment sections found in extraction output; skipping fragment writes."]

    fragments_root = character_dir / "fragments"
    spec_v2_dir = fragments_root / "spec_v2"
    site_dir = fragments_root / "site"
    spec_v2_dir.mkdir(parents=True, exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)

    for key, text in fragments.items():
        target_group, filename = FRAGMENT_SECTION_TARGETS[key]
        target_dir = spec_v2_dir if target_group == "spec_v2" else site_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / filename).write_text(text, encoding="utf-8")
    return []


def _collect_prompt_refs(runs_dir: Path) -> list[str]:
    if not runs_dir.exists():
        return []
    refs: list[str] = []
    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        prompt_ref_path = run_dir / "prompt_ref.txt"
        if not prompt_ref_path.exists():
            continue
        for line in prompt_ref_path.read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if not entry or entry.startswith("sha256:"):
                continue
            refs.append(entry)
    return refs


def _has_prompt_family(prompt_refs: Iterable[str], family: str) -> bool:
    marker = f"/prompts/{family}/"
    marker_alt = f"prompts/{family}/"
    for entry in prompt_refs:
        if marker in entry or marker_alt in entry:
            return True
    return False


def _normalize_fragment_title(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", title.strip().lower())
    return normalized.strip("_")
