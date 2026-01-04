from __future__ import annotations

import argparse
import difflib
import os
import sys
from pathlib import Path
from typing import Iterable

from src import authoring
from src import llm_client
from src.generator import build_site_data
from src.secrets import load_secrets_file


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

    author_parser = subparsers.add_parser("author", help="Interactive authoring workflow.")
    author_parser.add_argument("--staging-file", help="Optional staging drafts file path.")
    author_parser.add_argument("--prompt-category", default="elaborate")
    author_parser.add_argument("--extract-category", default="extract_fields")
    author_parser.add_argument("--tone-category", default="tone")
    author_parser.add_argument("--voice-category", default="voice")
    author_parser.add_argument("--style-category", default="style")

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
    llm_result = _invoke_llm(compiled_elaboration)
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
    llm_result = _invoke_llm(compiled_extraction)
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
    print("Authoring complete. Run `bp build` to generate dist outputs.")
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


def _compile_prompt(prompt_paths: Iterable[Path], input_text: str, input_label: str) -> str:
    prompt_blocks = [path.read_text(encoding="utf-8").strip() for path in prompt_paths]
    normalized_input = input_text.strip()
    prompt_blocks.append(f"{input_label}:\n{normalized_input}")
    return "\n\n".join(block for block in prompt_blocks if block) + "\n"


def _invoke_llm(compiled_prompt: str) -> llm_client.LLMResult:
    config = llm_client.load_llm_config()
    return llm_client.invoke_llm(compiled_prompt, config)


def _prompt_text(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{label}{suffix}: ").strip()
    return response or (default or "")


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


if __name__ == "__main__":
    raise SystemExit(main())
