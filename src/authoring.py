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
EMBEDDED_ENTRY_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CANONICAL_REQUIRED_FILES = ("spec_v2_fields.md", "shortDescription.md")


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


@dataclass(frozen=True)
class EmbeddedEntry:
    title: str
    slug: str
    description: str
    score: int | float | None = None


@dataclass(frozen=True)
class VariantDraft:
    title: str
    description: str


@dataclass(frozen=True)
class VariantGroup:
    title: str
    variants: list[VariantDraft]


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


def parse_variant_groups(text: str) -> list[VariantGroup]:
    groups: list[VariantGroup] = []
    current_group_title: str | None = None
    current_variants: list[VariantDraft] = []
    current_variant_title: str | None = None
    current_variant_lines: list[str] = []

    def flush_variant() -> None:
        nonlocal current_variant_title, current_variant_lines, current_variants
        if current_variant_title is None:
            return
        content = "\n".join(current_variant_lines).strip()
        if content:
            content += "\n"
        current_variants.append(
            VariantDraft(title=current_variant_title, description=content)
        )
        current_variant_title = None
        current_variant_lines = []

    def flush_group() -> None:
        nonlocal current_group_title, current_variants
        if current_group_title is None:
            return
        flush_variant()
        groups.append(VariantGroup(title=current_group_title, variants=current_variants))
        current_group_title = None
        current_variants = []

    for line in text.splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            level = len(match.group("level"))
            title = match.group("title").strip()
            if level <= 3:
                flush_group()
                if level == 3:
                    current_group_title = title
                continue
            if level == 4 and current_group_title:
                flush_variant()
                current_variant_title = title
                current_variant_lines = []
                continue
            if current_variant_title:
                current_variant_lines.append(line)
            continue
        if current_variant_title is not None:
            current_variant_lines.append(line)
            continue

    flush_group()
    return groups


def select_section_by_title(sections: Iterable[HeadingSection], title: str) -> HeadingSection | None:
    for section in sections:
        if section.title == title:
            return section
    return None


def merge_spec_fields(base: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in delta.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_spec_fields(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def apply_variant_delta(canonical_path: Path, delta_path: Path) -> dict[str, Any]:
    canonical_fields = load_spec_fields(canonical_path)
    if not isinstance(canonical_fields, dict):
        raise ValueError("Canonical spec_v2_fields.md must contain a JSON object.")
    delta_fields = load_spec_fields(delta_path)
    if not isinstance(delta_fields, dict):
        raise ValueError("Variant spec_v2_fields.md must contain a JSON object.")
    return merge_spec_fields(canonical_fields, delta_fields)


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


def validate_embedded_entry_slug(slug: str) -> None:
    if not slug or not EMBEDDED_ENTRY_SLUG_PATTERN.match(slug):
        raise ValueError(
            "Invalid entry slug. Use lowercase letters, digits, hyphens, or underscores "
            "(example: observatory-bench)."
        )


def parse_embedded_entries_auto_response(
    output_text: str,
    entry_types: Iterable[str],
    max_per_type: int,
) -> dict[str, list[EmbeddedEntry]]:
    payload = _parse_json_payload(output_text, label="embedded entries")
    entries_by_type: dict[str, list[EmbeddedEntry]] = {}
    for entry_type in entry_types:
        raw_entries = payload.get(entry_type, [])
        if raw_entries is None:
            raw_entries = []
        if not isinstance(raw_entries, list):
            raise ValueError(f"Embedded entries for '{entry_type}' must be a list.")
        parsed = [_parse_embedded_entry_item(item, entry_type) for item in raw_entries]
        parsed_sorted = sorted(parsed, key=lambda entry: entry.slug)
        parsed_sorted = _dedupe_sorted_embedded_entries(parsed_sorted)
        entries_by_type[entry_type] = parsed_sorted[:max_per_type]
    return entries_by_type


def parse_embedded_entry_response(output_text: str) -> EmbeddedEntry:
    payload = _parse_json_payload(output_text, label="embedded entry")
    return _parse_embedded_entry_item(payload, None)


def parse_embedded_entry_input_line(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError("Expected 'name: description' format.")
    name, description = (part.strip() for part in line.split(":", 1))
    if not name or not description:
        raise ValueError("Both name and description are required.")
    return name, description


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
    canonical_dir = character_dir / "canonical"
    for filename in CANONICAL_REQUIRED_FILES:
        (canonical_dir / filename).write_text("", encoding="utf-8")
    return character_dir


def write_embedded_entry(
    character_dir: Path,
    entry_type: str,
    entry_slug: str,
    body: str,
    frontmatter: dict[str, str | int | float] | None = None,
) -> Path:
    validate_embedded_entry_slug(entry_slug)
    entries_dir = character_dir / "fragments" / "entries" / entry_type
    entries_dir.mkdir(parents=True, exist_ok=True)
    entry_path = entries_dir / f"{entry_slug}.md"
    lines: list[str] = []
    if frontmatter:
        lines.append("---")
        for key, value in frontmatter.items():
            lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")
    if body.strip():
        lines.append(body.strip())
        lines.append("")
    entry_path.write_text("\n".join(lines), encoding="utf-8")
    return entry_path


def write_embedded_entries_log(
    log_path: Path,
    prompt_compiled: str,
    output_text: str,
    model_info: dict[str, Any],
    input_payload: str | None = None,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    sections: list[str] = ["# Embedded Entries LLM Log", ""]
    if input_payload:
        sections.extend(["## Input", "```", input_payload.strip(), "```", ""])
    sections.extend(
        [
            "## Prompt",
            "```",
            prompt_compiled.strip(),
            "```",
            "",
            "## Response",
            "```",
            output_text.strip(),
            "```",
            "",
            "## Model",
            "```json",
            json_dumps(model_info).strip(),
            "```",
            "",
        ]
    )
    log_path.write_text("\n".join(sections), encoding="utf-8")


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


def _parse_json_payload(text: str, label: str) -> dict[str, Any]:
    import json

    payload_text = _extract_json_payload(text.strip())
    if payload_text is None:
        raise ValueError(f"Expected JSON payload for {label}.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} payload must be a JSON object.")
    return payload


def _parse_embedded_entry_item(item: Any, entry_type: str | None) -> EmbeddedEntry:
    if not isinstance(item, dict):
        raise ValueError("Embedded entry must be a JSON object.")
    title = _require_text_field(item.get("title"), "title", entry_type)
    slug = _require_text_field(item.get("slug"), "slug", entry_type)
    validate_embedded_entry_slug(slug)
    description = _require_text_field(item.get("description"), "description", entry_type)
    score = item.get("score")
    if score is not None and not (isinstance(score, (int, float)) and not isinstance(score, bool)):
        raise ValueError("Embedded entry score must be a number.")
    return EmbeddedEntry(title=title, slug=slug, description=description, score=score)


def _require_text_field(value: Any, field: str, entry_type: str | None) -> str:
    if not isinstance(value, str):
        type_label = f" for {entry_type}" if entry_type else ""
        raise ValueError(f"Embedded entry {field} must be a string{type_label}.")
    cleaned = value.strip()
    if not cleaned:
        type_label = f" for {entry_type}" if entry_type else ""
        raise ValueError(f"Embedded entry {field} cannot be empty{type_label}.")
    return cleaned


def _dedupe_sorted_embedded_entries(entries: list[EmbeddedEntry]) -> list[EmbeddedEntry]:
    seen: set[str] = set()
    deduped: list[EmbeddedEntry] = []
    for entry in entries:
        if entry.slug in seen:
            continue
        seen.add(entry.slug)
        deduped.append(entry)
    return deduped


def load_short_description(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def canonical_required_paths(canonical_dir: Path) -> list[tuple[Path, str]]:
    return [
        (canonical_dir / filename, f"canonical/{filename}")
        for filename in CANONICAL_REQUIRED_FILES
    ]


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
    for path, label in canonical_required_paths(canonical_dir):
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
