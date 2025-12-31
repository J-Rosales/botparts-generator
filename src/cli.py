from __future__ import annotations

import argparse
import difflib
import os
import sys
from pathlib import Path
from typing import Iterable

from src import authoring
from src.generator import build_site_data


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

    author_parser = subparsers.add_parser("author", help="Interactive authoring workflow.")
    author_parser.add_argument("--staging-file", help="Optional staging drafts file path.")
    author_parser.add_argument("--prompt-category", default="elaborate")
    author_parser.add_argument("--extract-category", default="extract_fields")

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
    build_site_data(Path.cwd(), placeholders=placeholders, include_timestamps=args.include_timestamps)
    return 0


def _run_author(args: argparse.Namespace) -> int:
    api_key = os.environ.get("BOTPARTS_LLM_API_KEY")
    if not api_key:
        print("BOTPARTS_LLM_API_KEY is required for authoring runs.", file=sys.stderr)
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
    display_name = _prompt_text("Display name", default=section.title)
    character_dir = authoring.scaffold_character(sources_root, slug, display_name)
    authoring.write_staging_snapshot(character_dir, section)

    elaborate_prompt = _select_prompt(prompts_root, args.prompt_category)
    extract_prompt = _select_prompt(prompts_root, args.extract_category)

    preliminary_path = character_dir / "preliminary_draft.md"
    elaboration = _invoke_llm_stub(elaborate_prompt, section.content)
    run_dir = character_dir / "runs" / authoring.build_run_id(slug)
    authoring.write_run_log(
        run_dir,
        elaborate_prompt,
        model_info={"model": "stub", "temperature": 0, "provider": "local"},
        input_payload=section.content,
        output_text=elaboration,
    )
    preliminary_path.write_text(elaboration, encoding="utf-8")

    input("Edit preliminary_draft.md as needed, then press Enter to continue...")
    draft_input = preliminary_path.read_text(encoding="utf-8")
    extracted = _invoke_llm_stub(extract_prompt, draft_input)
    run_dir = character_dir / "runs" / authoring.build_run_id(slug)
    authoring.write_run_log(
        run_dir,
        extract_prompt,
        model_info={"model": "stub", "temperature": 0, "provider": "local"},
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


def _run_audit(args: argparse.Namespace) -> int:
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
    selection = _prompt_text("Select staging file by number")
    if not selection.isdigit():
        return None
    choice = int(selection)
    if 1 <= choice <= len(paths):
        return paths[choice - 1]
    return None


def _choose_section(sections: list[authoring.HeadingSection]) -> authoring.HeadingSection | None:
    titles = [section.title for section in sections]
    query = _prompt_text("Heading name")
    exact = authoring.select_section_by_title(sections, query)
    if exact:
        return exact
    matches = difflib.get_close_matches(query, titles, n=5, cutoff=0.3)
    if not matches:
        return None
    print("No exact match. Select one of the following:")
    for index, title in enumerate(matches, start=1):
        print(f"{index}. {title}")
    selection = _prompt_text("Select heading by number")
    if not selection.isdigit():
        return None
    choice = int(selection)
    if 1 <= choice <= len(matches):
        return authoring.select_section_by_title(sections, matches[choice - 1])
    return None


def _prompt_slug(title: str, characters_root: Path) -> str:
    default_slug = authoring.slugify(title)
    while True:
        slug = _prompt_text("Slug", default=default_slug)
        authoring.validate_slug(slug)
        if (characters_root / slug).exists():
            print(f"Slug '{slug}' already exists. Choose another.")
            continue
        return slug


def _select_prompt(prompts_root: Path, category: str) -> Path:
    templates = authoring.list_prompt_templates(prompts_root, category)
    if not templates:
        raise FileNotFoundError(f"No prompts found in {prompts_root / category}")
    for index, path in enumerate(templates, start=1):
        print(f"{index}. {path.name}")
    selection = _prompt_text(f"Select prompt for {category} by number")
    if not selection.isdigit():
        raise ValueError("Prompt selection requires a numeric choice.")
    choice = int(selection)
    if not (1 <= choice <= len(templates)):
        raise ValueError("Prompt selection out of range.")
    return templates[choice - 1]


def _invoke_llm_stub(prompt_path: Path, input_text: str) -> str:
    prompt_text = prompt_path.read_text(encoding="utf-8").strip()
    short_desc = _first_nonempty_line(input_text)[:140]
    return f\"{prompt_text}\\n\\n{input_text.strip()}\\n\\n---SHORT_DESCRIPTION---\\n{short_desc}\\n\"


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _prompt_text(label: str, default: str | None = None) -> str:
    suffix = f\" [{default}]\" if default else \"\"
    response = input(f\"{label}{suffix}: \").strip()
    return response or (default or \"\")


def _print_audit(audit: authoring.AuditResult) -> None:
    for warning in audit.warnings:
        print(f\"WARNING: {warning}\")
    for error in audit.errors:
        print(f\"ERROR: {error}\")


if __name__ == \"__main__\":
    raise SystemExit(main())
