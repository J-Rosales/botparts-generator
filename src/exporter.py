from __future__ import annotations

import base64
import json
import re
import struct
import zlib
from pathlib import Path
from typing import Any

from src import authoring

EMBEDDED_ENTRY_TYPES = ("locations", "items", "knowledge", "ideology", "relationships")
EMBEDDED_ENTRY_FILENAME = re.compile(r"^[a-z0-9][a-z0-9_-]*\.md$")
EMBEDDED_ENTRY_PLACEHOLDERS = {".keep", ".gitkeep"}
SCOPE_LAYERS = {"world", "character", "variant"}
PROSE_VARIANTS = ("schema-like", "hybrid")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_spec_v2_template() -> dict[str, Any]:
    template_path = Path(__file__).resolve().parent / "spec_v2_template.json"
    return _load_json(template_path)


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


def _normalize_scope(value: Any, warnings: list[str], context: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text not in SCOPE_LAYERS:
        warnings.append(f"[{context}] Unrecognized scope '{value}' for embedded entry.")
        return None
    return text


def _load_scope_sidecar(path: Path, warnings: list[str], context: str) -> str | None:
    sidecar_path = path.with_name(path.name + ".scope.json")
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


def _coerce_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _emit_embedded_entry_fragments(
    source_dir: Path,
    output_root: Path,
    warnings: list[str],
    slug: str,
) -> dict[str, list[str]]:
    entries_root = source_dir / "fragments" / "entries"
    embedded_entries: dict[str, list[str]] = {entry_type: [] for entry_type in EMBEDDED_ENTRY_TYPES}
    output_entries_root = output_root / "fragments" / "entries"
    output_entries_root.mkdir(parents=True, exist_ok=True)

    if not entries_root.exists():
        (output_entries_root / ".keep").write_text("", encoding="utf-8")
        for entry_type in EMBEDDED_ENTRY_TYPES:
            entry_dir = output_entries_root / entry_type
            entry_dir.mkdir(parents=True, exist_ok=True)
            (entry_dir / ".keep").write_text("", encoding="utf-8")
        return embedded_entries
    if not entries_root.is_dir():
        warnings.append(f"[{slug}] Embedded entries root is not a directory; skipping.")
        (output_entries_root / ".keep").write_text("", encoding="utf-8")
        return embedded_entries

    for entry_type in EMBEDDED_ENTRY_TYPES:
        source_type_dir = entries_root / entry_type
        output_type_dir = output_entries_root / entry_type
        output_type_dir.mkdir(parents=True, exist_ok=True)
        if not source_type_dir.exists() or not source_type_dir.is_dir():
            (output_type_dir / ".keep").write_text("", encoding="utf-8")
            continue

        candidates: list[Path] = []
        for path in sorted(source_type_dir.iterdir(), key=lambda item: item.name):
            if path.is_dir():
                warnings.append(
                    f"[{slug}] Embedded entry '{entry_type}/{path.name}' is a directory; skipping."
                )
                continue
            if path.name in EMBEDDED_ENTRY_PLACEHOLDERS:
                continue
            if not EMBEDDED_ENTRY_FILENAME.match(path.name):
                warnings.append(
                    f"[{slug}] Embedded entry '{entry_type}/{path.name}' does not match naming rules; skipping."
                )
                continue
            candidates.append(path)

        if not candidates:
            (output_type_dir / ".keep").write_text("", encoding="utf-8")
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

    return embedded_entries


def _build_character_book(
    source_dir: Path,
    warnings: list[str],
    slug: str,
    display_name: str,
) -> dict[str, Any] | None:
    entries_root = source_dir / "fragments" / "entries"
    if not entries_root.exists() or not entries_root.is_dir():
        return None

    entries: list[dict[str, Any]] = []
    insertion_order = 0
    for entry_type in EMBEDDED_ENTRY_TYPES:
        type_dir = entries_root / entry_type
        if not type_dir.exists() or not type_dir.is_dir():
            continue
        for path in sorted(type_dir.iterdir(), key=lambda item: item.name):
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
            raw_text = path.read_text(encoding="utf-8")
            frontmatter, body = _parse_frontmatter(raw_text)
            sidecar_scope = _load_scope_sidecar(path, warnings, slug)
            frontmatter_scope = _normalize_scope(frontmatter.get("scope"), warnings, slug)
            if sidecar_scope and frontmatter_scope and sidecar_scope != frontmatter_scope:
                warnings.append(
                    f"[{slug}] Scope sidecar overrides frontmatter for {path.name} "
                    f"({frontmatter_scope} -> {sidecar_scope})."
                )
            scope = sidecar_scope or frontmatter_scope or "character"
            content = body.strip()
            if not content:
                warnings.append(f"[{slug}] Embedded entry '{entry_type}/{path.name}' is empty; skipping.")
                continue
            entry_slug = path.stem
            entry = {
                "keys": [entry_slug],
                "content": content,
                "extensions": {"entryType": entry_type},
                "enabled": True,
                "insertion_order": insertion_order,
            }
            if scope:
                entry["extensions"]["scope"] = scope
            entry["name"] = entry_slug
            entries.append(entry)
            insertion_order += 1

    if not entries:
        return None

    return {
        "name": f"{display_name} Lorebook",
        "description": "",
        "extensions": {},
        "entries": entries,
    }


def _build_spec_v2_card(
    spec_fields: dict[str, Any],
    slug: str,
    short_description: str | None,
    embedded_book: dict[str, Any] | None,
    fallback_name: str,
    fallback_description: str,
    fallback_tags: list[str],
    variant_slug: str | None = None,
    prose_variant: str | None = None,
) -> dict[str, Any]:
    template = _load_spec_v2_template()
    data = template.get("data")
    if not isinstance(data, dict):
        data = {}
        template["data"] = data

    data["name"] = _coerce_string(spec_fields.get("name") or fallback_name)
    data["description"] = _coerce_string(spec_fields.get("description") or fallback_description)
    data["personality"] = _coerce_string(spec_fields.get("personality"))
    data["scenario"] = _coerce_string(spec_fields.get("scenario"))
    data["first_mes"] = _coerce_string(spec_fields.get("first_mes"))
    data["mes_example"] = _coerce_string(spec_fields.get("mes_example"))
    data["creator_notes"] = _coerce_string(spec_fields.get("creator_notes"))
    data["system_prompt"] = _coerce_string(spec_fields.get("system_prompt"))
    data["post_history_instructions"] = _coerce_string(spec_fields.get("post_history_instructions"))
    data["alternate_greetings"] = _coerce_string_list(spec_fields.get("alternate_greetings"))
    data["tags"] = _coerce_string_list(spec_fields.get("tags") or fallback_tags)
    data["creator"] = _coerce_string(spec_fields.get("creator"))
    data["character_version"] = _coerce_string(spec_fields.get("character_version"))

    extensions = data.get("extensions")
    if not isinstance(extensions, dict):
        extensions = {}
    botparts = extensions.get("botparts")
    if not isinstance(botparts, dict):
        botparts = {}
    botparts["slug"] = slug
    if variant_slug:
        botparts["variant"] = variant_slug
    if prose_variant:
        botparts["proseVariant"] = prose_variant
    if short_description:
        botparts["shortDescription"] = short_description
    extensions["botparts"] = botparts
    data["extensions"] = extensions

    if embedded_book:
        data["character_book"] = embedded_book

    return template


def _build_text_chunk(keyword: str, text: str) -> bytes:
    keyword_bytes = keyword.encode("latin-1")
    text_bytes = text.encode("latin-1")
    data = keyword_bytes + b"\x00" + text_bytes
    length = struct.pack(">I", len(data))
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return length + chunk_type + data + struct.pack(">I", crc)


def _embed_text_chunk(png_bytes: bytes, chunk: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    if not png_bytes.startswith(signature):
        raise ValueError("Invalid PNG signature.")
    offset = len(signature)
    while offset < len(png_bytes):
        if offset + 8 > len(png_bytes):
            break
        length = int.from_bytes(png_bytes[offset : offset + 4], "big")
        chunk_type = png_bytes[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        if chunk_end > len(png_bytes):
            break
        if chunk_type == b"IEND":
            return png_bytes[:offset] + chunk + png_bytes[offset:]
        offset = chunk_end
    raise ValueError("Unable to locate IEND chunk in PNG.")


def _write_png_with_embedded_json(
    source_path: Path,
    target_path: Path,
    payload: dict[str, Any],
) -> None:
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    encoded = base64.b64encode(json_text.encode("utf-8")).decode("ascii")
    text_chunk = _build_text_chunk("chara", encoded)
    png_bytes = source_path.read_bytes()
    output = _embed_text_chunk(png_bytes, text_chunk)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(output)


def _copy_png(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(source_path.read_bytes())


def _find_character_image(image_root: Path, stem: str) -> Path | None:
    if not image_root.exists():
        return None
    candidates = sorted(path for path in image_root.iterdir() if path.is_file() and path.stem == stem)
    if not candidates:
        return None
    pngs = [path for path in candidates if path.suffix.lower() == ".png"]
    if pngs:
        return pngs[0]
    return None


def export_character_bundle(
    workspace_root: Path,
    source_dir: Path,
    slug: str,
    manifest_payload: dict[str, Any],
    warnings: list[str],
    created_dirs: set[Path],
) -> None:
    canonical_path = source_dir / "canonical" / "spec_v2_fields.md"
    spec_fields = authoring.load_spec_fields(canonical_path)
    if not isinstance(spec_fields, dict):
        warnings.append(f"[{slug}] Canonical spec_v2_fields.md missing or invalid; export skipped.")
        return

    draft_path = source_dir / "preliminary_draft.md"
    draft_text = draft_path.read_text(encoding="utf-8") if draft_path.exists() else None
    short_description = authoring.load_short_description(source_dir / "canonical" / "shortDescription.md") or ""
    display_name = manifest_payload.get("name") or slug
    embedded_book = _build_character_book(source_dir, warnings, slug, display_name)

    export_root = workspace_root / "dist" / "src" / "export"
    export_character_root = export_root / "characters" / slug
    export_character_root.mkdir(parents=True, exist_ok=True)
    created_dirs.add(export_character_root)
    embedded_entries = _emit_embedded_entry_fragments(
        source_dir,
        export_character_root,
        warnings,
        slug,
    )
    base_payload = manifest_payload.get("base")
    if not isinstance(base_payload, dict):
        base_payload = {"fragments": {}}
        manifest_payload["base"] = base_payload
    fragments_payload = base_payload.get("fragments")
    if not isinstance(fragments_payload, dict):
        fragments_payload = {}
        base_payload["fragments"] = fragments_payload
    fragments_extensions = fragments_payload.get("x")
    if not isinstance(fragments_extensions, dict):
        fragments_extensions = {}
        fragments_payload["x"] = fragments_extensions
    fragments_extensions["embeddedEntries"] = embedded_entries

    for prose_variant in PROSE_VARIANTS:
        card_payload = _build_spec_v2_card(
            spec_fields,
            slug=slug,
            short_description=short_description,
            embedded_book=embedded_book,
            fallback_name=display_name,
            fallback_description=manifest_payload.get("description") or "",
            fallback_tags=manifest_payload.get("tags") or [],
            prose_variant=prose_variant,
        )
        if prose_variant == "hybrid" and draft_text is not None:
            card_payload["data"]["first_mes"] = draft_text
        _write_json(export_character_root / f"spec_v2.{prose_variant}.json", card_payload)
    _write_json(export_character_root / "manifest.json", manifest_payload)

    meta_path = source_dir / "meta.yaml"
    meta = authoring.parse_meta_yaml(meta_path) if meta_path.exists() else {}
    image_stem = meta.get("imageStem")
    image_root = workspace_root / "sources" / "image_inputs"
    image_key = image_stem.strip() if isinstance(image_stem, str) and image_stem.strip() else slug
    image_path = _find_character_image(image_root, image_key)
    if image_path is None:
        warnings.append(f"[{slug}] PNG not found under sources/image_inputs; image export skipped.")
    else:
        png_target = export_character_root / "avatarImage.png"
        _copy_png(image_path, png_target)

    variants_root = source_dir / "variants"
    if not variants_root.exists():
        return
    for variant_dir in sorted(path for path in variants_root.iterdir() if path.is_dir()):
        spec_path = variant_dir / "spec_v2_fields.md"
        if not spec_path.exists():
            continue
        try:
            variant_fields = authoring.apply_variant_delta(canonical_path, spec_path)
        except ValueError as exc:
            warnings.append(f"[{slug}] Variant '{variant_dir.name}' export skipped: {exc}")
            continue
        variant_embedded_book = _build_character_book(variant_dir, warnings, slug, display_name)
        if variant_embedded_book is None:
            variant_embedded_book = embedded_book
        variant_root = export_character_root / "variants" / variant_dir.name
        variant_root.mkdir(parents=True, exist_ok=True)
        created_dirs.add(variant_root)
        _emit_embedded_entry_fragments(
            variant_dir,
            variant_root,
            warnings,
            f"{slug}:{variant_dir.name}",
        )
        for prose_variant in PROSE_VARIANTS:
            variant_payload = _build_spec_v2_card(
                variant_fields,
                slug=slug,
                short_description=short_description,
                embedded_book=variant_embedded_book,
                fallback_name=display_name,
                fallback_description=manifest_payload.get("description") or "",
                fallback_tags=manifest_payload.get("tags") or [],
                variant_slug=variant_dir.name,
                prose_variant=prose_variant,
            )
            if prose_variant == "hybrid" and draft_text is not None:
                variant_payload["data"]["first_mes"] = draft_text
            _write_json(variant_root / f"spec_v2.{prose_variant}.json", variant_payload)
        if image_path is None:
            warnings.append(
                f"[{slug}] PNG not found for variant '{variant_dir.name}'; image export skipped."
            )
        else:
            png_target = variant_root / "avatarImage.png"
            _copy_png(image_path, png_target)
