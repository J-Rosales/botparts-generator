from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


HEADING_PATTERN = re.compile(r"^(?P<level>#+)\s+(?P<title>.+?)\s*$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


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
    if not SLUG_PATTERN.match(slug):
        raise ValueError(f"Invalid slug '{slug}'. Use lowercase letters, digits, and hyphens.")


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


def write_run_log(
    run_dir: Path,
    prompt_path: Path,
    prompt_compiled: str,
    model_info: dict[str, Any],
    input_payload: str,
    output_text: str,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_ref = run_dir / "prompt_ref.txt"
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    prompt_ref.write_text(f"{prompt_path.as_posix()}\nsha256:{prompt_hash}\n", encoding="utf-8")
    (run_dir / "prompt_compiled.md").write_text(prompt_compiled, encoding="utf-8")

    (run_dir / "model.json").write_text(
        json_dumps(model_info),
        encoding="utf-8",
    )
    input_hash = hashlib.sha256(input_payload.encode("utf-8")).hexdigest()
    (run_dir / "input_hash.txt").write_text(f"sha256:{input_hash}\n", encoding="utf-8")
    (run_dir / "output.md").write_text(output_text, encoding="utf-8")


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
