from __future__ import annotations

import argparse
import json
import re
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
EMBEDDED_ENTRY_TYPES = ("locations", "items", "knowledge", "ideology", "relationships")
EMBEDDED_ENTRY_LIMIT = 50
EMBEDDED_ENTRY_FILENAME = re.compile(r"^[a-z0-9][a-z0-9_-]*\.md$")
EMBEDDED_ENTRY_PLACEHOLDERS = {".keep", ".gitkeep"}
SCOPE_LAYERS = {"world", "character", "variant"}
SCOPE_SIDECAR_SUFFIX = ".scope.json"
WORLD_PROMOTION_FILES = ("PROMOTE.md", "meta.yaml")


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


def _normalize_scope(value: Any, warnings: list[str], context: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text not in SCOPE_LAYERS:
        warnings.append(f"[{context}] Unrecognized scope '{value}'; expected {sorted(SCOPE_LAYERS)}.")
        return None
    return text


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        return {}, text
    frontmatter_lines = lines[1:end_index]
    body_lines = lines[end_index + 1 :]
    metadata: dict[str, str] = {}
    for raw in frontmatter_lines:
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        metadata[key.strip()] = value.strip()
    body = "\n".join(body_lines)
    if text.endswith("\n"):
        body += "\n"
    return metadata, body


def _load_scope_sidecar(path: Path, warnings: list[str], context: str) -> str | None:
    sidecar_path = path.with_name(path.name + SCOPE_SIDECAR_SUFFIX)
    if not sidecar_path.exists():
        return None
    try:
        payload = _load_json(sidecar_path)
    except json.JSONDecodeError:
        warnings.append(f"[{context}] Invalid JSON in scope sidecar {sidecar_path.name}.")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"[{context}] Scope sidecar {sidecar_path.name} must be an object.")
        return None
    return _normalize_scope(payload.get("scope"), warnings, context)


def _read_scoped_fragment(
    path: Path,
    warnings: list[str],
    context: str,
    default_scope: str,
) -> tuple[str, str]:
    raw_text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(raw_text)
    frontmatter_scope = _normalize_scope(frontmatter.get("scope"), warnings, context)
    sidecar_scope = _load_scope_sidecar(path, warnings, context)
    if sidecar_scope and frontmatter_scope and sidecar_scope != frontmatter_scope:
        warnings.append(
            f"[{context}] Scope sidecar overrides frontmatter ({frontmatter_scope} -> {sidecar_scope})."
        )
    scope = sidecar_scope or frontmatter_scope or default_scope
    return scope, body


def _world_pack_promoted(pack_dir: Path, warnings: list[str], context: str) -> bool:
    if (pack_dir / "PROMOTE.md").exists():
        return True
    meta_path = pack_dir / "meta.yaml"
    if meta_path.exists():
        meta = authoring.parse_meta_yaml(meta_path)
        value = meta.get("promoteWorld")
        if value is None:
            value = meta.get("promote")
        if isinstance(value, bool):
            return value
        if value is not None:
            warnings.append(f"[{context}] meta.yaml promoteWorld must be true/false.")
    return False


def _build_world_fragments(
    sources_root: Path,
    output_root: Path,
    created_dirs: set[Path],
    warnings: list[str],
    strict_scopes: bool,
) -> dict[str, dict[str, list[str]]]:
    world_root = sources_root / "world"
    if not world_root.exists():
        if strict_scopes:
            raise RuntimeError("Strict scope mode enabled: sources/world is missing.")
        return {}
    if not world_root.is_dir():
        message = "sources/world exists but is not a directory."
        if strict_scopes:
            raise RuntimeError(message)
        warnings.append(message)
        return {}

    world_output_root = output_root / "fragments" / "world"
    _ensure_dir(world_output_root, created_dirs)
    (world_output_root / ".keep").write_text("", encoding="utf-8")

    world_fragments: dict[str, dict[str, list[str]]] = {}
    for pack_dir in sorted(world_root.iterdir(), key=lambda path: path.name):
        if not pack_dir.is_dir():
            continue
        pack_name = pack_dir.name
        pack_context = f"world/{pack_name}"
        promoted = _world_pack_promoted(pack_dir, warnings, pack_context)
        fragments_dir = pack_dir / "fragments"
        if not fragments_dir.exists():
            warnings.append(f"[{pack_context}] Missing fragments/ directory; skipping pack.")
            continue
        if not fragments_dir.is_dir():
            warnings.append(f"[{pack_context}] fragments/ is not a directory; skipping pack.")
            continue

        pack_output_root = world_output_root / pack_name
        pack_scopes: dict[str, list[str]] = {scope: [] for scope in SCOPE_LAYERS}
        wrote_any = False

        for fragment_path in sorted(fragments_dir.iterdir(), key=lambda path: path.name):
            if fragment_path.is_dir():
                warnings.append(f"[{pack_context}] Nested directory {fragment_path.name} ignored.")
                continue
            if fragment_path.name.endswith(SCOPE_SIDECAR_SUFFIX):
                continue
            scope, body = _read_scoped_fragment(fragment_path, warnings, pack_context, default_scope="world")
            if scope == "world" and not promoted:
                message = f"[{pack_context}] World-scoped fragment '{fragment_path.name}' blocked by promotion gate."
                if strict_scopes:
                    raise RuntimeError(message)
                warnings.append(message)
                continue
            scope_dir = pack_output_root / scope
            _ensure_dir(scope_dir, created_dirs)
            target_path = scope_dir / fragment_path.name
            target_path.write_text(body, encoding="utf-8")
            relative = Path("fragments") / "world" / pack_name / scope / fragment_path.name
            pack_scopes[scope].append(relative.as_posix())
            wrote_any = True

        if pack_output_root.exists() and not wrote_any:
            _ensure_dir(pack_output_root, created_dirs)
            (pack_output_root / ".keep").write_text("", encoding="utf-8")
        if any(pack_scopes.values()):
            world_fragments[pack_name] = {
                scope: sorted(paths) for scope, paths in pack_scopes.items() if paths
            }

    return world_fragments


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


def _extract_world_packs(source_manifest: dict[str, Any], warnings: list[str], slug: str) -> list[str]:
    extension = source_manifest.get("x")
    if not isinstance(extension, dict):
        return []
    raw = extension.get("worldPacks", [])
    if raw is None:
        return []
    if not isinstance(raw, list):
        warnings.append(f"[{slug}] x.worldPacks must be a list of pack names.")
        return []
    packs: list[str] = []
    seen: set[str] = set()
    for value in raw:
        name = str(value).strip()
        if not name:
            continue
        if name in seen:
            continue
        packs.append(name)
        seen.add(name)
    return sorted(packs)


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


def _build_embedded_entry_fragments(
    source_dir: Path | None,
    fragments_dir: Path,
    created_dirs: set[Path],
    warnings: list[str],
    slug: str,
) -> dict[str, list[str]]:
    if source_dir is None:
        return {}
    entries_root = source_dir / "fragments" / "entries"
    if not entries_root.exists():
        return {}
    if not entries_root.is_dir():
        warnings.append(f"[{slug}] Embedded entries root is not a directory; skipping.")
        return {}

    embedded_entries: dict[str, list[str]] = {}
    output_entries_root = fragments_dir / "entries"
    seen_types: set[str] = set()

    for entry_type in EMBEDDED_ENTRY_TYPES:
        source_type_dir = entries_root / entry_type
        if not source_type_dir.exists() or not source_type_dir.is_dir():
            continue
        seen_types.add(entry_type)
        output_type_dir = output_entries_root / entry_type
        _ensure_dir(output_type_dir, created_dirs)

        candidates = []
        for path in sorted(source_type_dir.iterdir(), key=lambda item: item.name):
            if path.is_dir():
                warnings.append(f"[{slug}] Embedded entry '{entry_type}/{path.name}' is a directory; skipping.")
                continue
            if path.name in EMBEDDED_ENTRY_PLACEHOLDERS:
                continue
            if not EMBEDDED_ENTRY_FILENAME.match(path.name):
                warnings.append(
                    f"[{slug}] Embedded entry '{entry_type}/{path.name}' does not match naming rules; skipping."
                )
                continue
            candidates.append(path)

        if len(candidates) > EMBEDDED_ENTRY_LIMIT:
            warnings.append(
                f"[{slug}] Embedded entry '{entry_type}' exceeds limit of {EMBEDDED_ENTRY_LIMIT}; truncating."
            )
            candidates = candidates[:EMBEDDED_ENTRY_LIMIT]

        if not candidates:
            (output_type_dir / ".keep").write_text("", encoding="utf-8")
            embedded_entries[entry_type] = []
            continue

        entry_paths: list[str] = []
        for path in candidates:
            target = output_type_dir / path.name
            target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            entry_paths.append(
                str((Path("fragments") / "entries" / entry_type / path.name).as_posix())
            )
        embedded_entries[entry_type] = entry_paths

    unknown_types = sorted(
        path.name for path in entries_root.iterdir() if path.is_dir() and path.name not in EMBEDDED_ENTRY_TYPES
    )
    if unknown_types:
        warnings.append(f"[{slug}] Embedded entry types not recognized: {', '.join(unknown_types)}.")

    if not seen_types:
        _ensure_dir(output_entries_root, created_dirs)
        (output_entries_root / ".keep").write_text("", encoding="utf-8")

    return embedded_entries


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
    strict_scopes: bool = False,
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

    world_fragments = _build_world_fragments(
        sources_root,
        output_root,
        created_dirs,
        warnings,
        strict_scopes=strict_scopes,
    )

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
        embedded_entries = _build_embedded_entry_fragments(
            Path(source_dir) if source_dir else None,
            fragments_dir,
            created_dirs,
            warnings,
            slug,
        )
        world_packs = _extract_world_packs(source_manifest, warnings, slug)
        world_scope_fragments: list[str] = []
        for pack_name in world_packs:
            pack_fragments = world_fragments.get(pack_name, {})
            for scope_paths in pack_fragments.values():
                world_scope_fragments.extend(scope_paths)

        manifest_x = dict(source_manifest.get("x") or {})
        manifest_x.update(site_fields)
        if variants:
            manifest_x["variants"] = variants
        if embedded_entries:
            manifest_x["embeddedEntries"] = embedded_entries
        if world_packs:
            manifest_x["worldPacks"] = world_packs

        scope_layers = {
            "world": {
                "packs": world_packs,
                "fragments": sorted(set(world_scope_fragments)),
            },
            "character": {
                "fragments": sorted(set(fragments.values())),
                "embeddedEntries": embedded_entries,
            },
            "variant": {
                "fragments": sorted(set(variants.values())),
            },
        }
        manifest_x["scopeLayers"] = scope_layers

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
    parser.add_argument(
        "--strict-scope",
        action="store_true",
        help="Treat missing world packs or promotion gate failures as errors.",
    )
    args = parser.parse_args()

    placeholders_env = os.environ.get("BOTPARTS_PLACEHOLDERS")
    placeholders = args.placeholders
    if placeholders is None:
        placeholders = _parse_placeholders(placeholders_env)

    strict_env = os.environ.get("BOTPARTS_SCOPE_STRICT", "0")
    strict_scopes = args.strict_scope or strict_env == "1"
    build_site_data(
        Path.cwd(),
        placeholders=placeholders,
        include_timestamps=args.include_timestamps,
        strict_scopes=strict_scopes,
    )


if __name__ == "__main__":
    main()
