from __future__ import annotations

import argparse
import difflib
import os
import sys
from pathlib import Path
from typing import Any, Iterable

from src import authoring
from src import llm_client
from src.generator import EMBEDDED_ENTRY_TYPES, build_site_data
from src.secrets import load_secrets_file

EMBEDDED_ENTRY_MAX = 2


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Botparts authoring and build CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Run deterministic build.")
    build_parser.add_argument(
        "--placeholders",
        type=_parse_placeholders,
        default=None,
        help="Number of placeholder profiles to emit.",
    )
    build_parser.add_argument(
        "--include-timestamps",
        action="store_true",
        help="Include timestamps in the report and index.json.",
    )
    build_parser.add_argument(
        "--strict-scope",
        action="store_true",
        help="Treat missing world packs or promotion gate failures as errors.",
    )

    author_parser = subparsers.add_parser("author", help="Authoring workflows.")
    author_subparsers = author_parser.add_subparsers(dest="author_command", required=True)
    author_canonical = author_subparsers.add_parser("canonical", help="Create new canonical character.")
    author_canonical.add_argument("--staging-file", help="Optional staging drafts file path.")
    author_canonical.add_argument("--prompt-category", default="elaborate")
    author_canonical.add_argument("--extract-category", default="extract_fields")
    author_canonical.add_argument("--tone-category", default="tone")
    author_canonical.add_argument("--voice-category", default="voice")
    author_canonical.add_argument("--style-category", default="style")
    author_canonical.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Skip automatic build after authoring completes.",
    )

    author_variants = author_subparsers.add_parser(
        "variants",
        help="Create character variants from staging drafts.",
    )
    author_variants.add_argument("--staging-file", help="Optional staging drafts file path.")
    author_variants.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Skip automatic build after authoring completes.",
    )

    author_schema = author_subparsers.add_parser(
        "schema",
        help="Create character from schema (.md file).",
    )
    author_schema.add_argument("schema_file", help="Schema .md file path.")
    author_schema.add_argument("--prompt-category", default="elaborate")
    author_schema.add_argument("--extract-category", default="extract_fields")
    author_schema.add_argument("--tone-category", default="tone")
    author_schema.add_argument("--voice-category", default="voice")
    author_schema.add_argument("--style-category", default="style")
    author_schema.add_argument("--idiosyncrasy-category", default="idiosyncrasy_module")
    author_schema.add_argument("--variant-category", default="rewrite_variants")
    author_schema.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Skip automatic build after authoring completes.",
    )

    author_schema_folder = author_subparsers.add_parser(
        "schema-folder",
        help="Create multiple characters from folder.",
    )
    author_schema_folder.add_argument("--prompt-category", default="elaborate")
    author_schema_folder.add_argument("--extract-category", default="extract_fields")
    author_schema_folder.add_argument("--tone-category", default="tone")
    author_schema_folder.add_argument("--voice-category", default="voice")
    author_schema_folder.add_argument("--style-category", default="style")
    author_schema_folder.add_argument("--idiosyncrasy-category", default="idiosyncrasy_module")
    author_schema_folder.add_argument("--variant-category", default="rewrite_variants")
    author_schema_folder.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Skip automatic build after authoring completes.",
    )

    clean_parser = subparsers.add_parser(
        "author-clean",
        help="Delete all authored character folders under sources/characters.",
    )
    clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List deletions without removing anything.",
    )
    clean_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip DELETE confirmation prompt.",
    )

    audit_parser = subparsers.add_parser("audit", help="Audit authored sources.")
    audit_subparsers = audit_parser.add_subparsers(dest="audit_command", required=False)
    audit_character = audit_subparsers.add_parser("character", help="Audit a single character.")
    audit_character.add_argument("slug")
    audit_parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "build":
        return _run_build(args)
    if args.command == "author":
        return _run_author(args)
    if args.command == "author-clean":
        return _run_author_clean(args)
    if args.command == "audit":
        return _run_audit(args)
    return 1


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


def _run_build(args: argparse.Namespace) -> int:
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
    return 0


def _maybe_auto_build(args: argparse.Namespace) -> int:
    if getattr(args, "no_auto_build", False):
        print("Auto-build skipped (--no-auto-build).")
        return 0
    placeholders = _parse_placeholders(os.environ.get("BOTPARTS_PLACEHOLDERS"))
    strict_scopes = os.environ.get("BOTPARTS_SCOPE_STRICT", "0") == "1"
    print("Running auto-build (bp build)...")
    build_site_data(
        Path.cwd(),
        placeholders=placeholders,
        include_timestamps=False,
        strict_scopes=strict_scopes,
    )
    print("Auto-build complete.")
    return 0


def _run_author(args: argparse.Namespace) -> int:
    load_secrets_file()
    try:
        _ = os.environ["BOTPARTS_LLM_API_KEY"]
    except KeyError:
        print(
            "BOTPARTS_LLM_API_KEY is required for authoring runs. "
            "Set it in your environment or copy .secrets.example to .secrets.",
            file=sys.stderr,
        )
        return 2

    workspace = Path.cwd()
    sources_root = workspace / "sources"
    prompts_root = workspace / "prompts"

    if args.author_command == "variants":
        result = _run_author_variants(args, sources_root, prompts_root)
    elif args.author_command == "schema":
        result = _run_author_schema(args, sources_root, prompts_root)
    elif args.author_command == "schema-folder":
        result = _run_author_schema_folder(args, sources_root, prompts_root)
    else:
        result = _run_author_canonical(args, sources_root, prompts_root)

    if result == 0 and not args.no_auto_build:
        return _maybe_auto_build(args)
    return result


def _run_author_canonical(
    args: argparse.Namespace,
    sources_root: Path,
    prompts_root: Path,
) -> int:
    staging_path = _select_staging_file(sources_root, args.staging_file)
    if staging_path is None:
        print("No staging drafts found under sources/.", file=sys.stderr)
        return 1
    sections = authoring.parse_staging_sections(staging_path.read_text(encoding="utf-8"))
    if not sections:
        print("No headings found in staging drafts.", file=sys.stderr)
        return 1
    section = _choose_section(sections)
    if section is None:
        print("Aborted.", file=sys.stderr)
        return 1

    slug = _prompt_slug(section.title, sources_root / "characters")
    if slug is None:
        print("Aborted.", file=sys.stderr)
        return 1
    display_name = _prompt_text("Display name (text; press Enter to use default)", default=section.title)
    print(f"Resolved slug: {slug}")
    print(f"Resolved display name: {display_name}")
    character_dir = authoring.scaffold_character(sources_root, slug, display_name)
    authoring.write_staging_snapshot(character_dir, section)

    elaborate_prompt = _select_prompt(prompts_root, args.prompt_category)
    tone_prompt = _select_prompt(prompts_root, args.tone_category, allow_skip=True)
    voice_prompt = _select_prompt(prompts_root, args.voice_category, allow_skip=True)
    style_prompt = _select_prompt(prompts_root, args.style_category, allow_skip=True)
    extract_prompt = _select_prompt(prompts_root, args.extract_category)

    prompt_paths = [elaborate_prompt]
    for optional_prompt in (tone_prompt, voice_prompt, style_prompt):
        if optional_prompt is not None:
            prompt_paths.append(optional_prompt)
    staging_snapshot = (character_dir / "staging_snapshot.md").read_text(encoding="utf-8")
    compiled_elaboration = _compile_prompt(prompt_paths, staging_snapshot, "CONCEPT SNIPPET")
    llm_result = _invoke_llm(compiled_elaboration, label="Elaboration")
    elaboration = llm_result.output_text
    run_id = authoring.build_run_id(slug)
    run_dir = character_dir / "runs" / run_id
    authoring.write_run_log(
        run_dir,
        prompt_paths,
        compiled_elaboration,
        model_info=llm_result.model_info,
        input_payload=staging_snapshot,
        output_text=elaboration,
    )
    preliminary_path = authoring.ensure_preliminary_draft(character_dir, elaboration, run_id=run_id)

    preliminary_rel = preliminary_path.relative_to(Path.cwd())
    run_output_rel = (run_dir / "output.md").relative_to(Path.cwd())
    print(f"Edit: {preliminary_rel.as_posix()}")
    print(f"Generated output preserved at: {run_output_rel.as_posix()}")
    authoring.try_open_in_editor(preliminary_path)
    input("Press enter once draft edits are saved...")
    draft_input = preliminary_path.read_text(encoding="utf-8")
    compiled_extraction = _compile_prompt([extract_prompt], draft_input, "DRAFT")
    llm_result = _invoke_llm(compiled_extraction, label="Extraction")
    extracted = llm_result.output_text
    run_dir = character_dir / "runs" / authoring.build_run_id(slug)
    authoring.write_run_log(
        run_dir,
        [extract_prompt],
        compiled_extraction,
        model_info=llm_result.model_info,
        input_payload=draft_input,
        output_text=extracted,
    )
    spec_text, short_desc = authoring.extract_output_sections(extracted)
    (character_dir / "canonical" / "spec_v2_fields.md").write_text(spec_text, encoding="utf-8")
    (character_dir / "canonical" / "shortDescription.md").write_text(short_desc + "\n", encoding="utf-8")

    audit = authoring.audit_character(sources_root, slug, strict=False)
    _print_audit(audit)
    if not audit.ok:
        return 1
    print("Authoring complete.")
    return 0


def _run_author_variants(
    args: argparse.Namespace,
    sources_root: Path,
    prompts_root: Path,
) -> int:
    character_slug = _select_character_slug(sources_root)
    if character_slug is None:
        print("Aborted.", file=sys.stderr)
        return 1
    character_dir = sources_root / "characters" / character_slug
    canonical_path = character_dir / "canonical" / "spec_v2_fields.md"
    if not canonical_path.exists() or not canonical_path.read_text(encoding="utf-8").strip():
        print(f"Missing canonical spec at {canonical_path}.", file=sys.stderr)
        return 1

    staging_path = _select_staging_file(sources_root, args.staging_file)
    if staging_path is None:
        print("No staging drafts found under sources/.", file=sys.stderr)
        return 1
    groups = authoring.parse_variant_groups(staging_path.read_text(encoding="utf-8"))
    if not groups:
        print("No variant groups found in staging drafts.", file=sys.stderr)
        return 1
    group = _choose_variant_group(groups)
    if group is None:
        print("Aborted.", file=sys.stderr)
        return 1
    if not group.variants:
        print(f"No variants found under '{group.title}'.", file=sys.stderr)
        return 1

    prompt_path = _select_prompt(prompts_root, "rewrite_variants")
    try:
        planned_variants = _plan_variants(group.variants)
    except ValueError as exc:
        print(f"Variant planning failed: {exc}", file=sys.stderr)
        return 1

    try:
        _apply_variant_edits(character_dir, canonical_path, prompt_path, planned_variants)
    except ValueError as exc:
        print(f"Variant delta validation failed: {exc}", file=sys.stderr)
        return 1

    print("Variant authoring complete. Run `bp build` to generate dist outputs.")
    return 0


def _run_author_schema(
    args: argparse.Namespace,
    sources_root: Path,
    prompts_root: Path,
) -> int:
    schema_path = Path(args.schema_file)
    return _run_author_schema_file(schema_path, args, sources_root, prompts_root)


def _run_author_schema_folder(
    args: argparse.Namespace,
    sources_root: Path,
    prompts_root: Path,
) -> int:
    schema_dir = sources_root / "schema_inputs"
    if not schema_dir.exists():
        print(f"Schema folder not found: {schema_dir}", file=sys.stderr)
        return 1
    schema_paths = sorted(
        path
        for path in schema_dir.iterdir()
        if path.suffix.lower() == ".md" and path.name != "schema_template.md"
    )
    if not schema_paths:
        print(f"No schema .md files found under {schema_dir}", file=sys.stderr)
        return 1
    failures = 0
    for schema_path in schema_paths:
        result = _run_author_schema_file(schema_path, args, sources_root, prompts_root)
        if result != 0:
            failures += 1
    if failures:
        print(f"Schema folder authoring completed with {failures} failure(s).", file=sys.stderr)
        return 1
    return 0


def _run_author_schema_file(
    schema_path: Path,
    args: argparse.Namespace,
    sources_root: Path,
    prompts_root: Path,
) -> int:
    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}", file=sys.stderr)
        return 1
    if schema_path.suffix.lower() != ".md":
        print(f"Schema file must be a .md file: {schema_path}", file=sys.stderr)
        return 1
    try:
        draft = authoring.parse_minimal_staging_draft(schema_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"Schema parsing failed: {exc}", file=sys.stderr)
        return 1

    display_name = draft.display_name.strip()
    characters_root = sources_root / "characters"
    existing_slugs = {path.name for path in authoring.list_character_dirs(sources_root)}
    authoring_prose_variant = (
        "schema-like" if draft.manifest.prose_variant == "all" else draft.manifest.prose_variant
    )
    slug_plan: list[tuple[str, str]] = []
    slug = authoring.generate_slug(display_name, existing_slugs)
    try:
        authoring.validate_slug(slug)
    except ValueError as exc:
        print(f"Generated slug '{slug}' is invalid: {exc}", file=sys.stderr)
        return 1
    if (characters_root / slug).exists():
        print(f"Slug '{slug}' already exists. Re-run to generate a new timestamp.", file=sys.stderr)
        return 1
    existing_slugs.add(slug)
    slug_plan.append((authoring_prose_variant, slug))
    print(f"Generated slug: {slug_plan[0][1]}")

    character_dirs: list[tuple[str, str, Path]] = []
    try:
        for prose_variant, slug in slug_plan:
            character_dir = authoring.scaffold_character(
                sources_root,
                slug,
                display_name,
                image_stem=schema_path.stem,
            )
            character_dirs.append((prose_variant, slug, character_dir))
            authoring.write_staging_snapshot(
                character_dir,
                authoring.HeadingSection(title="Character concept", level=1, content=draft.concept + "\n"),
            )

        manifest_prompts = draft.manifest.prompts
        elaborate_prompt = _resolve_manifest_prompt(
            prompts_root,
            args.prompt_category,
            manifest_prompts["elaborate"],
            "prompts.elaborate",
        )
        tone_prompt = _resolve_manifest_prompt(
            prompts_root,
            args.tone_category,
            manifest_prompts["tone"],
            "prompts.tone",
        )
        voice_prompt = _resolve_manifest_prompt(
            prompts_root,
            args.voice_category,
            manifest_prompts["voice"],
            "prompts.voice",
        )
        style_prompt = _resolve_manifest_prompt(
            prompts_root,
            args.style_category,
            manifest_prompts["style"],
            "prompts.style",
        )
        extract_prompt = _resolve_manifest_prompt(
            prompts_root,
            args.extract_category,
            manifest_prompts["extract_fields"],
            "prompts.extract_fields",
        )

        prompt_paths = [elaborate_prompt]
        for optional_prompt in (tone_prompt, voice_prompt, style_prompt):
            if optional_prompt is not None:
                prompt_paths.append(optional_prompt)

        elaboration_input = _build_schema_elaboration_input(draft)
        compiled_elaboration = _compile_prompt(prompt_paths, elaboration_input, "CONCEPT SNIPPET")
        llm_result = _invoke_llm(compiled_elaboration, label="Elaboration")
        elaboration = llm_result.output_text
        _enforce_third_person_user_voice(voice_prompt, elaboration, "Elaboration")
        for _, slug, character_dir in character_dirs:
            run_id = authoring.build_run_id(slug)
            run_dir = character_dir / "runs" / run_id
            authoring.write_run_log(
                run_dir,
                prompt_paths,
                compiled_elaboration,
                model_info=llm_result.model_info,
                input_payload=elaboration_input,
                output_text=elaboration,
            )

        draft_text = _apply_schema_draft_edits(elaboration, draft.draft_edits)
        for _, _, character_dir in character_dirs:
            (character_dir / "preliminary_draft.md").write_text(draft_text, encoding="utf-8")
        primary_dir = character_dirs[0][2]
        primary_path = primary_dir / "preliminary_draft.md"
        print(f"Review and edit: {primary_path.relative_to(Path.cwd()).as_posix()}")
        authoring.try_open_in_editor(primary_path)
        input("Press Enter once draft edits are saved...")
        draft_input = primary_path.read_text(encoding="utf-8")
        for _, _, character_dir in character_dirs:
            (character_dir / "preliminary_draft.md").write_text(draft_input, encoding="utf-8")

        refreshed_draft = authoring.parse_minimal_staging_draft(
            schema_path.read_text(encoding="utf-8")
        )
        variant_notes = refreshed_draft.variant_notes
        variant_drafts = _parse_variant_notes(variant_notes)

        for _, _, character_dir in character_dirs:
            _generate_embedded_entries_from_notes(
                character_dir,
                prompts_root,
                draft.manifest.embedded_entries_transform_notes,
            )
        embedded_entries_summary = _summarize_embedded_entries(
            character_dirs[0][2] / "fragments" / "entries"
        )

        idiosyncrasy_prompt = _resolve_optional_manifest_prompt(
            prompts_root,
            args.idiosyncrasy_category,
            manifest_prompts,
            "idiosyncrasy_module",
        )
        idiosyncrasy_input = _format_idiosyncrasy_payload(
            draft_input,
            embedded_entries_summary,
            variant_notes,
        )
        compiled_idiosyncrasy = _compile_prompt(
            [idiosyncrasy_prompt],
            idiosyncrasy_input,
            "IDIOSYNCRASY INPUT",
        )
        llm_result = _invoke_llm(compiled_idiosyncrasy, label="Idiosyncrasy module")
        run_dir = character_dirs[0][2] / "runs" / authoring.build_run_id(character_dirs[0][1])
        authoring.write_run_log(
            run_dir,
            [idiosyncrasy_prompt],
            compiled_idiosyncrasy,
            model_info=llm_result.model_info,
            input_payload=idiosyncrasy_input,
            output_text=llm_result.output_text,
        )
        system_prompt_module, post_history_module = _parse_idiosyncrasy_module(
            llm_result.output_text
        )

        for prose_variant, slug, character_dir in character_dirs:
            extraction_input = _build_schema_extraction_input(
                draft_input,
                prose_variant,
            )
            compiled_extraction = _compile_prompt([extract_prompt], extraction_input, "DRAFT")
            llm_result = _invoke_llm(compiled_extraction, label="Extraction")
            extracted = llm_result.output_text
            _enforce_third_person_user_voice(
                voice_prompt,
                extracted,
                f"Extraction output for {slug}",
            )
            run_dir = character_dir / "runs" / authoring.build_run_id(slug)
            authoring.write_run_log(
                run_dir,
                [extract_prompt],
                compiled_extraction,
                model_info=llm_result.model_info,
                input_payload=extraction_input,
                output_text=extracted,
            )
            spec_text, short_desc = authoring.extract_output_sections(extracted)
            try:
                spec_payload = authoring.parse_json_payload(spec_text, label="spec_v2")
            except ValueError as exc:
                raise ValueError(f"Spec_v2 JSON parsing failed: {exc}") from exc
            spec_payload["slug"] = slug
            if system_prompt_module:
                spec_payload["system_prompt"] = system_prompt_module
            if post_history_module:
                spec_payload["post_history_instructions"] = post_history_module
            authoring.validate_spec_v2_llm_output(spec_payload)
            (character_dir / "canonical" / "spec_v2_fields.md").write_text(
                authoring.json_dumps(spec_payload),
                encoding="utf-8",
            )
            (character_dir / "canonical" / "shortDescription.md").write_text(
                short_desc + "\n",
                encoding="utf-8",
            )

            if variant_drafts:
                variant_prompt = _resolve_optional_manifest_prompt(
                    prompts_root,
                    args.variant_category,
                    manifest_prompts,
                    "rewrite_variants",
                )
                try:
                    planned_variants = _plan_variants(variant_drafts)
                except ValueError as exc:
                    raise ValueError(f"Variant planning failed: {exc}") from exc
                applied_variants = _apply_variant_edits(
                    character_dir,
                    character_dir / "canonical" / "spec_v2_fields.md",
                    variant_prompt,
                    planned_variants,
                )
                for variant_slug, description in applied_variants:
                    variant_dir = character_dir / "variants" / variant_slug
                    _generate_embedded_entries_from_notes(
                        variant_dir,
                        prompts_root,
                        draft.manifest.embedded_entries_transform_notes,
                        variant_context=description,
                        embedded_entries=embedded_entries_summary,
                    )

            if len(character_dirs) > 1:
                print(f"Audit for {slug} ({prose_variant})")
            audit = authoring.audit_character(sources_root, slug, strict=False)
            _print_audit(audit)
            if not audit.ok:
                return 1
    except Exception as exc:
        if character_dirs:
            paths = [path for _, _, path in character_dirs if path.exists()]
            for path in paths:
                print(f"Schema workflow failed; cleaned up {path}.", file=sys.stderr)
            authoring.delete_character_dirs(paths)
        print(f"Schema workflow failed: {exc}", file=sys.stderr)
        return 1

    print("Schema authoring complete.")
    return 0


def _run_author_clean(args: argparse.Namespace) -> int:
    sources_root = Path.cwd() / "sources"
    characters_root = sources_root / "characters"
    print(f"Authoring characters root: {characters_root.resolve()}")
    character_dirs = authoring.list_character_dirs(sources_root)
    if not character_dirs:
        print("No authored character directories found.")
        return 0
    print("Directories slated for deletion:")
    for path in character_dirs:
        print(f"- {path.resolve()}")
    if args.dry_run:
        print("Dry run complete; no deletions performed.")
        return 0
    if not args.yes:
        token = input("Type DELETE to confirm deletion: ").strip()
        if token != "DELETE":
            print("Deletion aborted.", file=sys.stderr)
            return 1
    authoring.delete_character_dirs(character_dirs)
    print("Deletion complete.")
    return 0


def _run_audit(args: argparse.Namespace) -> int:
    load_secrets_file()
    sources_root = Path.cwd() / "sources"
    if args.audit_command == "character":
        audit = authoring.audit_character(sources_root, args.slug, strict=args.strict)
        _print_audit(audit)
        return 0 if audit.ok else 1
    audits = []
    characters_root = sources_root / "characters"
    if characters_root.exists():
        for character_dir in sorted(path for path in characters_root.iterdir() if path.is_dir()):
            audits.append(authoring.audit_character(sources_root, character_dir.name, strict=args.strict))
    if not audits:
        print("No characters found to audit.")
        return 0
    exit_code = 0
    for audit in audits:
        _print_audit(audit)
        if not audit.ok:
            exit_code = 1
    return exit_code


def _select_staging_file(sources_root: Path, provided: str | None) -> Path | None:
    if provided:
        path = Path(provided)
        return path if path.exists() else None
    paths = authoring.find_staging_draft_paths(sources_root)
    if not paths:
        return None
    if len(paths) == 1:
        return paths[0]
    for index, path in enumerate(paths, start=1):
        print(f"{index}. {path}")
    choice = _prompt_numeric_choice(
        f"Select staging file by number (1-{len(paths)})",
        minimum=1,
        maximum=len(paths),
    )
    return paths[choice - 1] if choice is not None else None


def _choose_section(sections: list[authoring.HeadingSection]) -> authoring.HeadingSection | None:
    titles = [section.title for section in sections]
    query = _prompt_text("Heading title (exact text; press Enter to cancel)")
    if not query:
        return None
    exact = authoring.select_section_by_title(sections, query)
    if exact:
        return exact
    matches = difflib.get_close_matches(query, titles, n=5, cutoff=0.3)
    if not matches:
        return None
    print("No exact match. Select one of the following:")
    for index, title in enumerate(matches, start=1):
        print(f"{index}. {title}")
    choice = _prompt_numeric_choice(
        f"Select heading by number (1-{len(matches)})",
        minimum=1,
        maximum=len(matches),
    )
    if choice is None:
        return None
    return authoring.select_section_by_title(sections, matches[choice - 1])


def _choose_variant_group(groups: list[authoring.VariantGroup]) -> authoring.VariantGroup | None:
    titles = [group.title for group in groups]
    while True:
        print("\nVariant groups:")
        for index, title in enumerate(titles, start=1):
            print(f"{index}. {title}")
        response = input("Select variant group by number (press Enter to cancel): ").strip()
        if not response:
            return None
        if response.isdigit():
            choice = int(response)
            if 1 <= choice <= len(groups):
                return groups[choice - 1]
        exact = authoring.select_section_by_title(
            [authoring.HeadingSection(title=group.title, level=3, content="") for group in groups],
            response,
        )
        if exact:
            for group in groups:
                if group.title == exact.title:
                    return group
        print("Invalid selection. Try again.", file=sys.stderr)


def _select_character_slug(sources_root: Path) -> str | None:
    character_dirs = authoring.list_character_dirs(sources_root)
    if not character_dirs:
        print("No authored characters found under sources/characters.", file=sys.stderr)
        return None
    print("\nAvailable characters:")
    for index, path in enumerate(character_dirs, start=1):
        print(f"{index}. {path.name}")
    while True:
        response = input("Select character by number or slug (press Enter to cancel): ").strip()
        if not response:
            return None
        if response.isdigit():
            choice = int(response)
            if 1 <= choice <= len(character_dirs):
                return character_dirs[choice - 1].name
        if any(path.name == response for path in character_dirs):
            return response
        print("Invalid selection. Try again.", file=sys.stderr)


def _prompt_slug(title: str, characters_root: Path) -> str | None:
    default_slug = authoring.slugify(title)
    if default_slug:
        try:
            authoring.validate_slug(default_slug)
        except ValueError:
            default_slug = ""
    while True:
        suffix = f" [{default_slug}]" if default_slug else ""
        response = input(
            "Enter character slug (example: naive-scout)"
            f"{suffix} (press Enter to accept default, or type 'q' to cancel): "
        ).strip()
        if response.lower() == "q":
            return None
        slug = response or default_slug
        if not slug:
            print("Slug is required. Aborting.", file=sys.stderr)
            return None
        try:
            authoring.validate_slug(slug)
        except ValueError as exc:
            print(f"{exc} Aborting.", file=sys.stderr)
            return None
        if (characters_root / slug).exists():
            print(f"Slug '{slug}' already exists. Choose another.")
            continue
        return slug


def _select_prompt(prompts_root: Path, category: str, allow_skip: bool = False) -> Path | None:
    templates = authoring.list_prompt_templates(prompts_root, category)
    if not templates:
        if allow_skip:
            print(f"No prompts found in {prompts_root / category}; skipping.")
            return None
        raise FileNotFoundError(f"No prompts found in {prompts_root / category}")
    if allow_skip:
        print("0. Skip")
    for index, path in enumerate(templates, start=1):
        print(f"{index}. {path.name}")
    if allow_skip:
        choice = _prompt_numeric_choice_optional(
            f"Select prompt for {category} by number",
            minimum=1,
            maximum=len(templates),
        )
        if choice is None:
            return None
        return templates[choice - 1]
    choice = _prompt_numeric_choice(
        f"Select prompt for {category} by number (1-{len(templates)})",
        minimum=1,
        maximum=len(templates),
    )
    if choice is None:
        raise ValueError("Prompt selection requires a numeric choice.")
    return templates[choice - 1]


def _resolve_manifest_prompt(
    prompts_root: Path,
    category: str,
    template_name: str,
    prompt_key: str,
) -> Path:
    prompt_dir = prompts_root / category
    while True:
        resolved = _resolve_prompt_candidate(prompt_dir, template_name)
        if resolved is not None:
            return resolved
        print(
            f"Missing prompt template for {prompt_key}='{template_name}'.",
            file=sys.stderr,
        )
        print(f"Expected directory: {prompt_dir}", file=sys.stderr)
        template_name = input(f"Enter template name for {prompt_key}: ").strip()
        if not template_name:
            print("Template name is required.", file=sys.stderr)


def _resolve_prompt_candidate(prompt_dir: Path, template_name: str) -> Path | None:
    candidates = [prompt_dir / template_name]
    if not template_name.endswith(".md"):
        candidates.append(prompt_dir / f"{template_name}.md")
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _compile_prompt(prompt_paths: Iterable[Path], input_text: str, input_label: str) -> str:
    prompt_blocks = [path.read_text(encoding="utf-8").strip() for path in prompt_paths]
    normalized_input = input_text.strip()
    prompt_blocks.append(f"{input_label}:\n{normalized_input}")
    return "\n\n".join(block for block in prompt_blocks if block) + "\n"


def _enforce_third_person_user_voice(voice_prompt: Path | None, output_text: str, label: str) -> None:
    if voice_prompt is None or voice_prompt.name != "third_person_user_v1.md":
        return
    matches = authoring.detect_second_person_pronouns(output_text)
    if matches:
        joined = ", ".join(matches)
        raise ValueError(
            f"{label} output contains second-person pronouns ({joined}) while using "
            f"{voice_prompt.name}. Replace with {{user}} references only."
        )


def _compile_variant_prompt(
    prompt_paths: Iterable[Path],
    canonical_text: str,
    variant_description: str,
) -> str:
    prompt_blocks = [path.read_text(encoding="utf-8").strip() for path in prompt_paths]
    prompt_blocks.append(f"CANONICAL CARD:\n{canonical_text.strip()}")
    prompt_blocks.append(f"VARIANT DESCRIPTION:\n{variant_description.strip()}")
    return "\n\n".join(block for block in prompt_blocks if block) + "\n"


def _format_variant_prompt_payload(canonical_text: str, variant_description: str) -> str:
    return "\n\n".join(
        [
            "CANONICAL CARD:",
            canonical_text.strip(),
            "",
            "VARIANT DESCRIPTION:",
            variant_description.strip(),
        ]
    ).strip() + "\n"


def _resolve_optional_manifest_prompt(
    prompts_root: Path,
    category: str,
    manifest_prompts: dict[str, str],
    prompt_key: str,
) -> Path:
    template_name = manifest_prompts.get(prompt_key, "").strip()
    if template_name:
        return _resolve_manifest_prompt(prompts_root, category, template_name, f"prompts.{prompt_key}")
    return _select_prompt(prompts_root, category)


def _parse_variant_notes(variant_notes: str) -> list[authoring.VariantDraft]:
    if not variant_notes.strip():
        return []
    groups = authoring.parse_variant_groups(variant_notes)
    variants: list[authoring.VariantDraft] = []
    for group in groups:
        variants.extend(group.variants)
    return variants


def _plan_variants(
    variants: list[authoring.VariantDraft],
) -> list[tuple[str, str, str]]:
    planned: list[tuple[str, str, str]] = []
    seen_slugs: set[str] = set()
    for variant in variants:
        variant_slug = authoring.slugify(variant.title)
        authoring.validate_slug(variant_slug)
        if variant_slug in seen_slugs:
            raise ValueError(f"Duplicate variant slug '{variant_slug}' in variant notes.")
        seen_slugs.add(variant_slug)
        description = variant.description.strip()
        if not description:
            raise ValueError(f"Missing variant description for '{variant.title}'.")
        planned.append((variant.title, variant_slug, description))
    return planned


def _apply_variant_edits(
    character_dir: Path,
    canonical_path: Path,
    prompt_path: Path,
    planned_variants: list[tuple[str, str, str]],
) -> list[tuple[str, str]]:
    canonical_text = canonical_path.read_text(encoding="utf-8")
    applied: list[tuple[str, str]] = []
    for _, variant_slug, description in planned_variants:
        variant_dir = character_dir / "variants" / variant_slug
        variant_dir.mkdir(parents=True, exist_ok=True)
        spec_path = variant_dir / "spec_v2_fields.md"

        input_payload = _format_variant_prompt_payload(canonical_text, description)
        compiled_prompt = _compile_variant_prompt([prompt_path], canonical_text, description)
        llm_result = _invoke_llm(compiled_prompt, label=f"Variant rewrite ({variant_slug})")
        spec_path.write_text(llm_result.output_text.rstrip() + "\n", encoding="utf-8")
        run_dir = variant_dir / "runs" / authoring.build_run_id(variant_slug)
        authoring.write_run_log(
            run_dir,
            [prompt_path],
            compiled_prompt,
            model_info=llm_result.model_info,
            input_payload=input_payload,
            output_text=llm_result.output_text,
        )

        variant_rel = spec_path.relative_to(Path.cwd())
        print(f"Edit variant draft: {variant_rel.as_posix()}")
        authoring.try_open_in_editor(spec_path)
        input("Press enter once draft edits are saved...")
        delta_fields = authoring.load_spec_fields(spec_path)
        if not isinstance(delta_fields, dict):
            raise ValueError(f"Variant delta for '{variant_slug}' must be a JSON object.")
        authoring.apply_variant_delta(canonical_path, spec_path)
        _print_variant_fragment_summary(delta_fields, variant_slug)
        applied.append((variant_slug, description))
    return applied


def _format_idiosyncrasy_payload(
    draft_text: str,
    embedded_entries: str,
    variant_notes: str,
) -> str:
    sections = ["DRAFT:\n" + draft_text.strip()]
    if embedded_entries:
        sections.append("EMBEDDED ENTRIES:\n" + embedded_entries)
    if variant_notes.strip():
        sections.append("VARIANT NOTES:\n" + variant_notes.strip())
    return "\n\n".join(sections).strip() + "\n"


def _parse_idiosyncrasy_module(output_text: str) -> tuple[str, str]:
    payload = authoring.parse_json_payload(output_text, label="idiosyncrasy module")
    system_prompt = str(payload.get("system_prompt") or "").strip()
    post_history = str(payload.get("post_history_instructions") or "").strip()
    return system_prompt, post_history


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text.strip()
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            body = "\n".join(lines[idx + 1 :]).strip()
            return body
    return text.strip()


def _summarize_embedded_entries(entries_root: Path) -> str:
    summaries: list[str] = []
    if not entries_root.exists() or not entries_root.is_dir():
        return ""
    for entry_type in EMBEDDED_ENTRY_TYPES:
        type_dir = entries_root / entry_type
        if not type_dir.exists() or not type_dir.is_dir():
            continue
        for path in sorted(type_dir.iterdir(), key=lambda item: item.name):
            if path.is_dir():
                continue
            if path.name in {".keep", ".gitkeep"}:
                continue
            body = _strip_frontmatter(path.read_text(encoding="utf-8"))
            if not body:
                continue
            summaries.append(f"- {entry_type}/{path.stem}: {body}")
    return "\n".join(summaries).strip()


def _invoke_llm(compiled_prompt: str, label: str = "LLM request") -> llm_client.LLMResult:
    config = llm_client.load_llm_config()
    print(f"Loading... {label} in progress.")
    sys.stdout.flush()
    result = llm_client.invoke_llm(compiled_prompt, config)
    print(f"{label} complete.")
    return result


def _prompt_text(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{label}{suffix}: ").strip()
    return response or (default or "")


def _prompt_embedded_entries(character_dir: Path, prompts_root: Path) -> None:
    print("\nEmbedded entries (optional). Add canonical fragments for reuse in variants.")
    mode = _prompt_embedded_entries_mode()
    if mode == "skip":
        print("Skipping embedded entries.")
        return
    run_dir = character_dir / "runs" / authoring.build_run_id(character_dir.name)
    if mode == "auto":
        _prompt_embedded_entries_auto(character_dir, prompts_root, run_dir)
        return
    _prompt_embedded_entries_from_input(character_dir, prompts_root, run_dir)


def _prompt_embedded_entries_mode() -> str:
    print("Select embedded entry authoring mode:")
    print("1. Automatically (generate entries with one LLM call).")
    print("2. From Input Prompt (provide name: description lines).")
    print("3. Skip embedded entries.")
    while True:
        response = input("Mode selection (1-3, press Enter to skip): ").strip()
        if not response:
            return "skip"
        if not response.isdigit():
            print("Invalid input. Expected a numeric selection.", file=sys.stderr)
            continue
        try:
            return _resolve_embedded_entries_mode(int(response))
        except ValueError as exc:
            print(f"{exc} Try again.", file=sys.stderr)


def _resolve_embedded_entries_mode(choice: int) -> str:
    mapping = {1: "auto", 2: "from_input", 3: "skip"}
    if choice not in mapping:
        raise ValueError("Invalid embedded entry mode selection.")
    return mapping[choice]


def _prompt_embedded_entries_auto(
    character_dir: Path,
    prompts_root: Path,
    run_dir: Path,
) -> None:
    prompt_path = _select_prompt(prompts_root, "embedded_entries_auto")
    input_payload = _format_embedded_entries_auto_payload(EMBEDDED_ENTRY_TYPES, EMBEDDED_ENTRY_MAX)
    compiled_prompt = _compile_prompt([prompt_path], input_payload, "ENTRY TYPES")
    llm_result = _invoke_llm(compiled_prompt, label="Embedded entries (auto)")
    authoring.write_embedded_entries_log(
        run_dir / "embedded_entries_auto.md",
        prompt_compiled=compiled_prompt,
        output_text=llm_result.output_text,
        model_info=llm_result.model_info,
        input_payload=input_payload,
    )
    try:
        entries_by_type = authoring.parse_embedded_entries_auto_response(
            llm_result.output_text,
            EMBEDDED_ENTRY_TYPES,
            EMBEDDED_ENTRY_MAX,
        )
    except ValueError as exc:
        print(f"Embedded entry parsing failed: {exc}", file=sys.stderr)
        return
    selected = authoring.select_embedded_entries(entries_by_type, EMBEDDED_ENTRY_MAX)
    if len(selected) < EMBEDDED_ENTRY_MAX:
        print(
            f"Embedded entry generation produced {len(selected)} entries; expected {EMBEDDED_ENTRY_MAX}.",
            file=sys.stderr,
        )
        return
    for entry_type, entry in selected:
        frontmatter = {"title": entry.title}
        if entry.scope_level_index is not None:
            frontmatter["scopeLevelIndex"] = entry.scope_level_index
        authoring.write_embedded_entry(
            character_dir,
            entry_type=entry_type,
            entry_slug=entry.slug,
            body=entry.description,
            frontmatter=frontmatter,
        )


def _prompt_embedded_entries_from_input(
    character_dir: Path,
    prompts_root: Path,
    run_dir: Path,
) -> None:
    prompt_path = _select_prompt(prompts_root, "embedded_entries_from_input")
    for entry_type in EMBEDDED_ENTRY_TYPES:
        print(f"\nEnter {entry_type} entries (name: description).")
        print("Type CONTINUE to skip an entry prompt, NEXT to move to the next entry type.")
        entries: list[authoring.EmbeddedEntry] = []
        seen_slugs: set[str] = set()
        attempt_index = 0
        while len(entries) < EMBEDDED_ENTRY_MAX:
            raw_line = input(f"{entry_type} input: ").strip()
            try:
                kind, name, description = _parse_embedded_entries_input(raw_line)
            except ValueError as exc:
                print(f"{exc} Try again.", file=sys.stderr)
                continue
            if kind == "NEXT":
                break
            if kind == "CONTINUE":
                continue
            input_payload = _format_embedded_entries_input_payload(entry_type, name, description)
            compiled_prompt = _compile_prompt([prompt_path], input_payload, "ENTRY INPUT")
            llm_result = _invoke_llm(compiled_prompt, label="Embedded entry")
            attempt_index += 1
            try:
                entry = authoring.parse_embedded_entry_response(llm_result.output_text)
            except ValueError as exc:
                print(f"Embedded entry parsing failed: {exc}", file=sys.stderr)
                continue
            log_path = (
                run_dir
                / "embedded_entries_from_input"
                / entry_type
                / f"entry_{attempt_index:02d}_{entry.slug}.md"
            )
            authoring.write_embedded_entries_log(
                log_path,
                prompt_compiled=compiled_prompt,
                output_text=llm_result.output_text,
                model_info=llm_result.model_info,
                input_payload=input_payload,
            )
            if entry.slug in seen_slugs:
                print(f"Duplicate slug '{entry.slug}' for {entry_type}; skipping entry.")
                continue
            seen_slugs.add(entry.slug)
            entries.append(entry)
        entries_sorted = sorted(entries, key=lambda entry: entry.slug)
        for entry in entries_sorted:
            frontmatter = {"title": entry.title}
            if entry.scope_level_index is not None:
                frontmatter["scopeLevelIndex"] = entry.scope_level_index
            authoring.write_embedded_entry(
                character_dir,
                entry_type=entry_type,
                entry_slug=entry.slug,
                body=entry.description,
                frontmatter=frontmatter,
            )


def _prompt_entry_slug(default_slug: str) -> str:
    while True:
        response = _prompt_text("Entry slug", default=default_slug)
        slug = response.strip()
        try:
            authoring.validate_embedded_entry_slug(slug)
        except ValueError as exc:
            print(f"{exc} Try again.", file=sys.stderr)
            continue
        return slug


def _prompt_entry_count(label: str, maximum: int) -> int:
    while True:
        response = input(f"{label} (0-{maximum}, press Enter to skip): ").strip()
        if not response:
            return 0
        if not response.isdigit():
            print("Invalid input. Expected a number.", file=sys.stderr)
            continue
        count = int(response)
        if 0 <= count <= maximum:
            return count
        print(f"Count out of range (0-{maximum}).", file=sys.stderr)


def _print_variant_fragment_summary(delta_fields: dict[str, Any], variant_slug: str) -> None:
    fragment_keys = {
        "persona",
        "scenario",
        "systemPrompt",
        "system_prompt",
        "lore",
        "examples",
        "firstMessage",
        "alternateGreetings",
        "greetings",
        "first_mes",
        "mes_example",
    }
    touched = sorted(key for key in delta_fields.keys() if key in fragment_keys)
    if touched:
        print(f"Variant '{variant_slug}' updates fragment fields: {', '.join(touched)}")
    else:
        print(f"Variant '{variant_slug}' does not update fragment fields.")


def _prompt_numeric_value_optional(label: str) -> int | None:
    response = input(f"{label}: ").strip()
    if not response:
        return None
    try:
        return int(response)
    except ValueError:
        print("Invalid number. Skipping numeric value.", file=sys.stderr)
        return None


def _prompt_numeric_choice(label: str, minimum: int, maximum: int) -> int | None:
    response = input(f"{label} (press Enter to cancel): ").strip()
    if not response:
        return None
    if not response.isdigit():
        print("Invalid input. Expected a numeric selection. Aborting.", file=sys.stderr)
        return None
    choice = int(response)
    if not (minimum <= choice <= maximum):
        print(f"Selection out of range ({minimum}-{maximum}). Aborting.", file=sys.stderr)
        return None
    return choice


def _prompt_numeric_choice_optional(label: str, minimum: int, maximum: int) -> int | None:
    response = input(f"{label} ({minimum}-{maximum}, 0 to skip; press Enter to skip): ").strip()
    if not response or response == "0":
        return None
    if not response.isdigit():
        print("Invalid input. Expected a numeric selection. Aborting.", file=sys.stderr)
        return None
    choice = int(response)
    if not (minimum <= choice <= maximum):
        print(f"Selection out of range ({minimum}-{maximum}). Aborting.", file=sys.stderr)
        return None
    return choice


def _print_audit(audit: authoring.AuditResult) -> None:
    for warning in audit.warnings:
        print(f"WARNING: {warning}")
    for error in audit.errors:
        print(f"ERROR: {error}")


def _parse_embedded_entries_input(line: str) -> tuple[str, str | None, str | None]:
    cleaned = line.strip()
    if not cleaned:
        raise ValueError("Input cannot be blank. Use NAME: description, CONTINUE, or NEXT.")
    upper = cleaned.upper()
    if upper in {"CONTINUE", "NEXT"}:
        return upper, None, None
    if ":" not in cleaned:
        raise ValueError("Expected format 'name: description'.")
    name, description = (part.strip() for part in cleaned.split(":", 1))
    if not name or not description:
        raise ValueError("Both name and description are required.")
    return "ENTRY", name, description


def _format_embedded_entries_auto_payload(entry_types: Iterable[str], target: int) -> str:
    lines = [f"- {entry_type}" for entry_type in entry_types]
    return "Entry types:\n" + "\n".join(lines) + f"\n\nTarget total entries: {target}"


def _format_embedded_entries_input_payload(entry_type: str, name: str, description: str) -> str:
    return f"Entry type: {entry_type}\nName: {name}\nDescription: {description}"


def _build_schema_elaboration_input(draft: authoring.MinimalStagingDraft) -> str:
    if draft.elaborate_notes:
        return f"{draft.concept}\n\nELABORATION NOTES:\n{draft.elaborate_notes}"
    return draft.concept


def _apply_schema_draft_edits(elaboration: str, draft_edits: str) -> str:
    if not draft_edits:
        return elaboration.rstrip() + "\n"
    return (
        elaboration.rstrip()
        + "\n\n---\nDraft edits (from schema)\n---\n\n"
        + draft_edits.strip()
        + "\n"
    )


def _build_schema_extraction_input(
    draft_text: str,
    prose_variant: str,
) -> str:
    base = draft_text.rstrip()
    notes: list[str] = []
    if prose_variant:
        notes.append(f"PROSE VARIANT: {prose_variant}")
    notes.append(
        "GREETINGS REQUIREMENTS:\n"
        "- Each greeting should mention a season; if unavailable, use a weekday or time of day.\n"
        "- Each greeting should mention a location or setting; a situational anchor also works.\n"
        "- Each greeting should mention a named person; if unavailable, reference who owns the place "
        "or who the moment reminds the character of.\n"
        "- If details are missing, make up plausible ones consistent with the setting and time period."
    )
    if notes:
        return base + "\n\n" + "\n\n".join(notes) + "\n"
    return base + "\n"


def _generate_embedded_entries_from_notes(
    target_dir: Path,
    prompts_root: Path,
    notes: str,
    variant_context: str | None = None,
    embedded_entries: str | None = None,
) -> None:
    prompt_path = _resolve_embedded_entries_prompt(prompts_root)
    input_payload = _format_embedded_entries_auto_payload(EMBEDDED_ENTRY_TYPES, EMBEDDED_ENTRY_MAX)
    if notes.strip():
        input_payload = f"{input_payload}\n\nNOTES:\n{notes.strip()}\n"
    if embedded_entries:
        input_payload = f"{input_payload}\n\nCANONICAL EMBEDDED ENTRIES:\n{embedded_entries.strip()}\n"
    if variant_context:
        input_payload = f"{input_payload}\n\nVARIANT NOTES:\n{variant_context.strip()}\n"
    compiled_prompt = _compile_prompt([prompt_path], input_payload, "ENTRY TYPES")
    llm_result = _invoke_llm(compiled_prompt, label="Embedded entries (notes)")
    run_dir = target_dir / "runs" / authoring.build_run_id(target_dir.name)
    authoring.write_embedded_entries_log(
        run_dir / "embedded_entries_auto_notes.md",
        prompt_compiled=compiled_prompt,
        output_text=llm_result.output_text,
        model_info=llm_result.model_info,
        input_payload=input_payload,
    )
    try:
        entries_by_type = authoring.parse_embedded_entries_auto_response(
            llm_result.output_text,
            EMBEDDED_ENTRY_TYPES,
            EMBEDDED_ENTRY_MAX,
        )
    except ValueError as exc:
        print(f"Embedded entry parsing failed: {exc}", file=sys.stderr)
        return
    selected = authoring.select_embedded_entries(entries_by_type, EMBEDDED_ENTRY_MAX)
    if len(selected) < EMBEDDED_ENTRY_MAX:
        print(
            f"Embedded entry generation produced {len(selected)} entries; expected {EMBEDDED_ENTRY_MAX}.",
            file=sys.stderr,
        )
        return
    (target_dir / "fragments").mkdir(parents=True, exist_ok=True)
    for entry_type, entry in selected:
        frontmatter = {"title": entry.title}
        if entry.scope_level_index is not None:
            frontmatter["scopeLevelIndex"] = entry.scope_level_index
        authoring.write_embedded_entry(
            target_dir,
            entry_type=entry_type,
            entry_slug=entry.slug,
            body=entry.description,
            frontmatter=frontmatter,
        )


def _resolve_embedded_entries_prompt(prompts_root: Path) -> Path:
    templates = authoring.list_prompt_templates(prompts_root, "embedded_entries_auto")
    if not templates:
        raise FileNotFoundError(f"No prompts found in {prompts_root / 'embedded_entries_auto'}")
    return templates[0]


if __name__ == "__main__":
    raise SystemExit(main())
