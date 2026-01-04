from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src import authoring

GENERATOR_VERSION = "0.1.0"
SITE_ONLY_FIELDS = {
    "shortDescription": "",
    "spoilerTags": [],
    "aiTokens": None,
    "uploadDate": "",
}


@dataclass
class BuildSummary:
    real_count: int
    placeholder_count: int
    total_count: int
    created_dirs: list[str]
    warnings: list[str]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _ensure_dir(path: Path, created_dirs: set[Path]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    created_dirs.add(path)


def _normalize_tag_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _partition_tags(
    tags: list[Any] | None,
    spoiler_tags: list[Any] | None,
    warnings: list[str],
    slug: str,
) -> tuple[list[str], list[str]]:
    clean_tags: list[str] = []
    clean_spoilers: list[str] = []
    seen_tags: set[str] = set()
    seen_spoilers: set[str] = set()

    def add_tag(target: list[str], seen: set[str], tag_value: str) -> None:
        if tag_value in seen:
            return
        target.append(tag_value)
        seen.add(tag_value)

    for raw in tags or []:
        value = _normalize_tag_value(raw)
        if value is None:
            warnings.append(f"[{slug}] Dropped empty tag from tags list.")
            continue
        if value.lower().startswith("spoiler:"):
            spoiler_value = value[len("spoiler:") :].strip()
            if not spoiler_value:
                warnings.append(f"[{slug}] Dropped empty spoiler tag from tags list.")
                continue
            add_tag(clean_spoilers, seen_spoilers, spoiler_value)
        else:
            add_tag(clean_tags, seen_tags, value)

    for raw in spoiler_tags or []:
        value = _normalize_tag_value(raw)
        if value is None:
            warnings.append(f"[{slug}] Dropped empty tag from spoilerTags list.")
            continue
        add_tag(clean_spoilers, seen_spoilers, value)

    return clean_tags, clean_spoilers


def _extract_site_field(source: dict[str, Any], key: str) -> Any:
    if key in source:
        return source.get(key)
    extension = source.get("x")
    if isinstance(extension, dict) and key in extension:
        return extension.get(key)
    return None


def _coerce_ai_tokens(value: Any, warnings: list[str], slug: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        warnings.append(f"[{slug}] aiTokens value ignored because it is a boolean.")
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, (float, str)):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            warnings.append(f"[{slug}] aiTokens value '{value}' is not a number; using null.")
            return None
        return parsed
    warnings.append(f"[{slug}] aiTokens value '{value}' is not supported; using null.")
    return None


def _build_fragment_files(
    content: dict[str, Any],
    fragments_dir: Path,
    created_dirs: set[Path],
) -> dict[str, str]:
    _ensure_dir(fragments_dir, created_dirs)
    fragments: dict[str, str] = {}

    def write_fragment(filename: str, text: str) -> None:
        (fragments_dir / filename).write_text(text, encoding="utf-8")

    persona = content.get("persona")
    if isinstance(persona, str) and persona.strip():
        write_fragment("persona.txt", persona.strip())
        fragments["persona"] = "fragments/persona.txt"

    scenario = content.get("scenario")
    if isinstance(scenario, str) and scenario.strip():
        write_fragment("scenario.txt", scenario.strip())
        fragments["scenario"] = "fragments/scenario.txt"

    system_prompt = content.get("systemPrompt") or content.get("system_prompt")
    if isinstance(system_prompt, str) and system_prompt.strip():
        write_fragment("system_prompt.txt", system_prompt.strip())
        fragments["system_prompt"] = "fragments/system_prompt.txt"

    lore = content.get("lore")
    if isinstance(lore, str) and lore.strip():
        write_fragment("lore.txt", lore.strip())
        fragments["lore"] = "fragments/lore.txt"

    examples = content.get("examples")
    if isinstance(examples, str) and examples.strip():
        write_fragment("examples.txt", examples.strip())
        fragments["examples"] = "fragments/examples.txt"
    elif isinstance(examples, list) and examples:
        cleaned = [str(item).strip() for item in examples if str(item).strip()]
        if cleaned:
            write_fragment("examples.txt", "\n\n".join(cleaned))
            fragments["examples"] = "fragments/examples.txt"

    greetings: list[str] = []
    first_message = content.get("firstMessage")
    if isinstance(first_message, str) and first_message.strip():
        greetings.append(first_message.strip())
    alternate = content.get("alternateGreetings")
    if isinstance(alternate, list):
        greetings.extend([str(item).strip() for item in alternate if str(item).strip()])
    explicit_greetings = content.get("greetings")
    if isinstance(explicit_greetings, list):
        greetings.extend([str(item).strip() for item in explicit_greetings if str(item).strip()])

    if greetings:
        (fragments_dir / "greetings.json").write_text(
            json.dumps(greetings, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        fragments["greetings"] = "fragments/greetings.json"

    if not any(fragments_dir.iterdir()):
        (fragments_dir / ".keep").write_text("", encoding="utf-8")

    return fragments


def _build_variant_fragments(
    variants_root: Path | None,
    fragments_dir: Path,
    created_dirs: set[Path],
) -> dict[str, str]:
    variants: dict[str, str] = {}
    if variants_root is None or not variants_root.exists():
        return variants
    for style_dir in sorted(path for path in variants_root.iterdir() if path.is_dir()):
        spec_path = style_dir / "spec_v2_fields.md"
        if not spec_path.exists():
            continue
        relative_target = Path("fragments") / "variants" / style_dir.name / "spec_v2_fields.md"
        target_path = fragments_dir / "variants" / style_dir.name
        _ensure_dir(target_path, created_dirs)
        (target_path / "spec_v2_fields.md").write_text(spec_path.read_text(encoding="utf-8"), encoding="utf-8")
        variants[style_dir.name] = str(relative_target.as_posix())
    return variants


def _merge_manifest_data(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in {"content", "provenance", "x"} and isinstance(value, dict):
            current = merged.get(key)
            if isinstance(current, dict):
                nested = dict(current)
                nested.update(value)
                merged[key] = nested
            else:
                merged[key] = dict(value)
        else:
            merged[key] = value
    return merged


def _load_authored_manifest(character_dir: Path, warnings: list[str]) -> dict[str, Any] | None:
    # Deterministic, local-only inputs: the canonical spec fields are read from
    # sources/characters/<slug>/canonical/spec_v2_fields.md and merged with
    # manifest.json. No network or runtime data is consulted here.
    canonical_dir = character_dir / "canonical"
    spec_path = canonical_dir / "spec_v2_fields.md"
    if not spec_path.exists():
        return None
    spec_fields = authoring.load_spec_fields(spec_path)
    if not spec_fields:
        return None
    if not isinstance(spec_fields, dict):
        warnings.append(f"[{character_dir.name}] spec_v2_fields.md must contain a JSON object.")
        return None
    meta_path = character_dir / "meta.yaml"
    if meta_path.exists():
        meta = authoring.parse_meta_yaml(meta_path)
    else:
        meta = {}
    slug = spec_fields.get("slug") or meta.get("slug")
    if slug:
        spec_fields["slug"] = slug
    if not spec_fields.get("name"):
        display_name = meta.get("displayName")
        if display_name:
            spec_fields["name"] = display_name
    short_description = authoring.load_short_description(canonical_dir / "shortDescription.md")
    if short_description:
        # Site-only metadata stays under the schema extension block (x).
        spec_fields.setdefault("x", {})
        if isinstance(spec_fields["x"], dict):
            spec_fields["x"].setdefault("shortDescription", short_description)
    return spec_fields


def _map_modules(source_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for module in source_manifest.get("modules", []) or []:
        if not isinstance(module, dict):
            continue
        module_id = module.get("id")
        label = module.get("label")
        if not module_id or not label:
            continue
        kind = module.get("type") or module.get("kind") or "toggle"
        if kind not in {"required", "toggle", "oneOf"}:
            kind = "toggle"
        target_key = module.get("contentKey") or module.get("target") or "content"
        target = f"content.{target_key}" if target_key else "content"
        mapped = {
            "id": module_id,
            "label": label,
            "kind": kind,
            "target": target,
            "op": "replace",
        }
        if module.get("group"):
            mapped["group"] = module["group"]
        if module.get("defaultEnabled") is not None:
            mapped["defaultEnabled"] = bool(module.get("defaultEnabled"))
        modules.append(mapped)
    return modules


def _map_transforms(source_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    transforms: list[dict[str, Any]] = []
    for transform in source_manifest.get("transforms", []) or []:
        if not isinstance(transform, dict):
            continue
        transform_id = transform.get("id")
        label = transform.get("label")
        if not transform_id or not label:
            continue
        mapped = {
            "id": transform_id,
            "label": label,
            "kind": transform.get("kind", "presentation"),
            "renderer": transform.get("renderer", "spec_v2_json"),
        }
        transforms.append(mapped)
    return transforms


def _placeholder_manifest(index: int) -> dict[str, Any]:
    slug = f"placeholder-bot-{index:02d}"
    return {
        "slug": slug,
        "name": f"Placeholder Bot {index:02d}",
        "description": "Placeholder character used for layout testing.",
        "shortDescription": "Placeholder profile for layout checks.",
        "tags": [
            "demo",
            "layout",
            "training",
            "spoiler:twist" if index % 2 == 0 else "spoiler:ending",
        ],
        "redistributeAllowed": "unknown",
        "provenance": {
            "original": {
                "url": f"https://example.com/placeholders/{slug}",
                "label": "Placeholder source",
            },
            "backup": None,
            "notes": "Placeholder entry for local testing.",
        },
        "uploadDate": f"2025-01-{index:02d}",
        "aiTokens": 800 + index * 25,
        "content": {
            "persona": "This is a placeholder persona used for layout validation.",
            "firstMessage": "Hello! I'm a placeholder character for layout testing.",
            "alternateGreetings": [
                "Placeholder greeting A.",
                "Placeholder greeting B.",
            ],
            "systemPrompt": "Stay neutral and focus on layout testing.",
        },
        "modules": [
            {
                "id": "base-persona",
                "label": "Base Persona",
                "type": "required",
                "contentKey": "persona",
            },
            {
                "id": "first-message",
                "label": "First Message",
                "type": "toggle",
                "defaultEnabled": True,
                "contentKey": "firstMessage",
            },
        ],
        "transforms": [
            {
                "id": "default",
                "label": "Default",
                "kind": "presentation",
                "renderer": "spec_v2_json",
            }
        ],
    }


def build_site_data(
    workspace_root: Path,
    placeholders: int = 0,
    include_timestamps: bool = False,
) -> BuildSummary:
    # This build is intentionally deterministic: identical inputs under sources/
    # must emit byte-identical dist/src/data outputs. Avoid non-deterministic
    # sources (network calls, current time, random) unless explicitly gated.
    warnings: list[str] = []
    created_dirs: set[Path] = set()

    sources_root = workspace_root / "sources"
    dist_root = workspace_root / "dist"
    output_root = dist_root / "src" / "data"

    if output_root.exists():
        shutil.rmtree(output_root)

    _ensure_dir(output_root, created_dirs)
    _ensure_dir(output_root / "characters", created_dirs)
    _ensure_dir(output_root / "fragments", created_dirs)
    (output_root / "fragments" / ".keep").write_text("", encoding="utf-8")

    site_seed_path = sources_root / "site-seed" / "index.json"
    site_seed: dict[str, Any] = {}
    if site_seed_path.exists():
        site_seed = _load_json(site_seed_path)

    site_entries_by_slug = {
        entry.get("slug"): entry
        for entry in site_seed.get("entries", [])
        if isinstance(entry, dict) and entry.get("slug")
    }

    character_sources: list[dict[str, Any]] = []
    characters_root = sources_root / "characters"
    if characters_root.exists():
        for character_dir in sorted(characters_root.iterdir(), key=lambda path: path.name):
            if not character_dir.is_dir():
                continue
            manifest_path = character_dir / "manifest.json"
            authored_manifest = _load_authored_manifest(character_dir, warnings)
            source_manifest: dict[str, Any]
            if manifest_path.exists():
                source_manifest = _load_json(manifest_path)
                if authored_manifest:
                    source_manifest = _merge_manifest_data(source_manifest, authored_manifest)
            else:
                if not authored_manifest:
                    warnings.append(f"[{character_dir.name}] Missing manifest.json in sources.")
                    continue
                source_manifest = authored_manifest
            source_manifest["_source_dir"] = character_dir
            character_sources.append(source_manifest)

    real_slugs = {manifest.get("slug") for manifest in character_sources if manifest.get("slug")}

    placeholder_manifests: list[dict[str, Any]] = []
    placeholder_count = max(placeholders, 0)
    if placeholder_count:
        placeholder_slugs = {f"placeholder-bot-{index:02d}" for index in range(1, placeholder_count + 1)}
        if real_slugs & placeholder_slugs:
            warnings.append("Placeholder slug collision detected; skipping placeholder generation.")
            placeholder_count = 0
        else:
            placeholder_manifests = [_placeholder_manifest(index) for index in range(1, placeholder_count + 1)]

    all_manifests = character_sources + placeholder_manifests

    entries: list[dict[str, Any]] = []
    for source_manifest in all_manifests:
        slug = source_manifest.get("slug") or "unknown"
        site_entry = site_entries_by_slug.get(slug, {})

        tags_input = source_manifest.get("tags")
        if tags_input is None:
            tags_input = site_entry.get("tags", [])
        spoiler_input = _extract_site_field(source_manifest, "spoilerTags")
        if spoiler_input is None:
            spoiler_input = _extract_site_field(site_entry, "spoilerTags")
        tags, spoiler_tags = _partition_tags(tags_input or [], spoiler_input or [], warnings, slug)

        short_description = (
            _extract_site_field(source_manifest, "shortDescription")
            or _extract_site_field(site_entry, "shortDescription")
            or SITE_ONLY_FIELDS["shortDescription"]
        )
        if short_description is None:
            short_description = SITE_ONLY_FIELDS["shortDescription"]
        elif not isinstance(short_description, str):
            short_description = str(short_description)
        upload_date = (
            _extract_site_field(site_entry, "uploadDate")
            or _extract_site_field(source_manifest, "uploadDate")
            or source_manifest.get("updated")
            or SITE_ONLY_FIELDS["uploadDate"]
        )
        if upload_date is None:
            upload_date = SITE_ONLY_FIELDS["uploadDate"]
        elif not isinstance(upload_date, str):
            upload_date = str(upload_date)
        ai_tokens = _coerce_ai_tokens(
            _extract_site_field(source_manifest, "aiTokens")
            or _extract_site_field(site_entry, "aiTokens"),
            warnings,
            slug,
        )
        site_fields = {
            "shortDescription": short_description,
            "spoilerTags": spoiler_tags,
            "aiTokens": ai_tokens,
            "uploadDate": upload_date,
        }
        if source_manifest in placeholder_manifests:
            site_fields["placeholder"] = True
        else:
            site_fields["placeholder"] = False

        content = source_manifest.get("content", {}) if isinstance(source_manifest.get("content"), dict) else {}
        character_dir = output_root / "characters" / slug
        _ensure_dir(character_dir, created_dirs)
        fragments_dir = character_dir / "fragments"
        fragments = _build_fragment_files(content, fragments_dir, created_dirs)
        source_dir = source_manifest.get("_source_dir")
        variants_root = Path(source_dir) / "variants" if source_dir else None
        variants = _build_variant_fragments(
            variants_root,
            fragments_dir,
            created_dirs,
        )

        manifest_x = dict(source_manifest.get("x") or {})
        manifest_x.update(site_fields)
        if variants:
            manifest_x["variants"] = variants

        base = {"fragments": fragments}
        modules = _map_modules(source_manifest)
        transforms = _map_transforms(source_manifest)

        manifest_payload = {
            "slug": slug,
            "name": source_manifest.get("name") or site_entry.get("name") or slug,
            "description": source_manifest.get("description") or site_entry.get("description") or "",
            "tags": tags,
            "redistributeAllowed": source_manifest.get("redistributeAllowed")
            or site_entry.get("redistributeAllowed")
            or "unknown",
            "provenance": source_manifest.get("provenance") or site_entry.get("provenance") or {
                "original": {"url": "https://example.com/unknown"}
            },
            "base": base,
            "modules": modules,
            "transforms": transforms,
            "x": manifest_x,
        }

        manifest_path = output_root / "characters" / slug / "manifest.json"
        _write_json(manifest_path, manifest_payload)

        entry_x = dict(site_entry.get("x") or {})
        entry_x.update(site_fields)
        entry_payload: dict[str, Any] = {
            "slug": slug,
            "name": manifest_payload["name"],
            "description": manifest_payload["description"],
            "tags": tags,
            "featured": bool(site_entry.get("featured", False)),
            "dataPath": f"data/characters/{slug}/manifest.json",
            "redistributeAllowed": manifest_payload["redistributeAllowed"],
            "provenance": manifest_payload["provenance"],
            "x": entry_x,
        }
        if site_entry.get("thumbnailPath"):
            entry_payload["thumbnailPath"] = site_entry["thumbnailPath"]
        if site_entry.get("version"):
            entry_payload["version"] = site_entry["version"]
        if site_entry.get("updatedAt"):
            entry_payload["updatedAt"] = site_entry["updatedAt"]
        entries.append(entry_payload)

    entries = sorted(entries, key=lambda entry: entry["slug"])

    index_payload: dict[str, Any] = {
        "entries": entries,
    }
    if site_seed.get("siteTitle"):
        index_payload["siteTitle"] = site_seed["siteTitle"]
    if site_seed.get("siteDescription"):
        index_payload["siteDescription"] = site_seed["siteDescription"]
    if include_timestamps:
        index_payload["generatedAt"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    _write_json(output_root / "index.json", index_payload)

    report_path = dist_root / "REPORT.md"
    report_path.write_text(
        _render_report(
            BuildSummary(
                real_count=len(character_sources),
                placeholder_count=placeholder_count,
                total_count=len(entries),
                created_dirs=sorted(str(path.relative_to(dist_root)) for path in created_dirs),
                warnings=warnings,
            ),
            include_timestamps=include_timestamps,
        ),
        encoding="utf-8",
    )

    return BuildSummary(
        real_count=len(character_sources),
        placeholder_count=placeholder_count,
        total_count=len(entries),
        created_dirs=sorted(str(path.relative_to(dist_root)) for path in created_dirs),
        warnings=warnings,
    )


def _render_report(summary: BuildSummary, include_timestamps: bool) -> str:
    lines = [
        "# Botparts Generator Report",
        "",
        "## Run Metadata",
        f"- Generator version: {GENERATOR_VERSION}",
        f"- Placeholders enabled: {summary.placeholder_count > 0} ({summary.placeholder_count})",
    ]
    if include_timestamps:
        lines.append(f"- Timestamp: {datetime.utcnow().isoformat(timespec='seconds')}Z")

    lines.extend(
        [
            "",
            "## Output Summary",
            f"- Real characters: {summary.real_count}",
            f"- Placeholder characters: {summary.placeholder_count}",
            f"- Total characters emitted: {summary.total_count}",
            "- Directories created:",
        ]
    )
    if summary.created_dirs:
        lines.extend([f"  - {directory}" for directory in summary.created_dirs])
    else:
        lines.append("  - (none)")

    lines.extend(
        [
            "",
            "## Field Policy Summary",
            "- Site-only fields emitted under x:",
            f"  - shortDescription (default: '{SITE_ONLY_FIELDS['shortDescription']}')",
            f"  - spoilerTags (default: {SITE_ONLY_FIELDS['spoilerTags']})",
            f"  - aiTokens (default: {SITE_ONLY_FIELDS['aiTokens']})",
            f"  - uploadDate (default: '{SITE_ONLY_FIELDS['uploadDate']}')",
            "  - placeholder (default: false for real characters)",
            "- Tag partitioning: tags starting with 'spoiler:' move to spoilerTags; prefix stripped, trimmed, deduped.",
            "- uploadDate formatting: YYYY-MM-DD (date-only); empty string when unknown.",
            "- aiTokens type: number|null.",
            "",
            "## Warnings",
        ]
    )
    if summary.warnings:
        lines.extend([f"- {warning}" for warning in summary.warnings])
    else:
        lines.append("- None.")

    return "\n".join(lines) + "\n"


def _parse_placeholders(value: str | None) -> int:
    if not value:
        return 0
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid placeholder count: {value}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("Placeholder count must be >= 0")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Botparts site data.")
    parser.add_argument(
        "--placeholders",
        type=_parse_placeholders,
        default=None,
        help="Number of placeholder profiles to emit.",
    )
    parser.add_argument(
        "--include-timestamps",
        action="store_true",
        help="Include timestamps in the report and index.json.",
    )
    args = parser.parse_args()

    placeholders_env = os.environ.get("BOTPARTS_PLACEHOLDERS")
    placeholders = args.placeholders
    if placeholders is None:
        placeholders = _parse_placeholders(placeholders_env)

    build_site_data(Path.cwd(), placeholders=placeholders, include_timestamps=args.include_timestamps)


if __name__ == "__main__":
    main()
