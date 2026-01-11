import json
from pathlib import Path

from src import exporter


def _write_spec_fields(path: Path, payload: dict) -> None:
    body = json.dumps(payload, indent=2)
    path.write_text(f"```json\n{body}\n```\n", encoding="utf-8")


def test_export_character_bundle_uses_draft_for_hybrid(tmp_path: Path) -> None:
    workspace_root = tmp_path
    source_dir = tmp_path / "sources" / "characters" / "echo"
    canonical_dir = source_dir / "canonical"
    canonical_dir.mkdir(parents=True)
    _write_spec_fields(canonical_dir / "spec_v2_fields.md", {"first_mes": "Spec hello"})
    (canonical_dir / "shortDescription.md").write_text("Short desc", encoding="utf-8")

    draft_text = "Draft greeting.\n\nSecond line.\n"
    (source_dir / "preliminary_draft.md").write_text(draft_text, encoding="utf-8")

    warnings: list[str] = []
    created_dirs: set[Path] = set()
    exporter.export_character_bundle(
        workspace_root=workspace_root,
        source_dir=source_dir,
        slug="echo",
        manifest_payload={"name": "Echo", "description": "Desc", "tags": ["tag"]},
        warnings=warnings,
        created_dirs=created_dirs,
    )

    export_root = workspace_root / "dist" / "src" / "export" / "characters" / "echo"
    hybrid_payload = json.loads((export_root / "spec_v2.hybrid.json").read_text(encoding="utf-8"))
    schema_payload = json.loads(
        (export_root / "spec_v2.schema-like.json").read_text(encoding="utf-8")
    )

    assert hybrid_payload["data"]["first_mes"] == draft_text
    assert schema_payload["data"]["first_mes"] == "Spec hello"


def test_export_character_bundle_filters_system_prompt_rules(tmp_path: Path) -> None:
    workspace_root = tmp_path
    source_dir = tmp_path / "sources" / "characters" / "delta"
    canonical_dir = source_dir / "canonical"
    canonical_dir.mkdir(parents=True)
    system_prompt_payload = {
        "default_behaviors": ["Stay calm."],
        "conditional_rules": [
            {"condition": "variant == 'Storm Front'", "behavior": "Raise tension."},
            {"condition": "variant == 'Calm Tone'", "behavior": "Lower tension."},
            "If variant 'Storm Front' is active, be terse.",
        ],
        "response_shape_constraints": ["Keep replies short."],
        "avoidances": ["No shouting."],
    }
    _write_spec_fields(
        canonical_dir / "spec_v2_fields.md",
        {"system_prompt": json.dumps(system_prompt_payload)},
    )
    (canonical_dir / "shortDescription.md").write_text("Short desc", encoding="utf-8")

    variant_dir = source_dir / "variants" / "storm-front"
    variant_dir.mkdir(parents=True, exist_ok=True)
    _write_spec_fields(variant_dir / "spec_v2_fields.md", {"name": "Delta Storm"})

    warnings: list[str] = []
    created_dirs: set[Path] = set()
    exporter.export_character_bundle(
        workspace_root=workspace_root,
        source_dir=source_dir,
        slug="delta",
        manifest_payload={"name": "Delta", "description": "Desc", "tags": ["tag"]},
        warnings=warnings,
        created_dirs=created_dirs,
    )

    export_root = workspace_root / "dist" / "src" / "export" / "characters" / "delta"
    schema_payload = json.loads(
        (export_root / "spec_v2.schema-like.json").read_text(encoding="utf-8")
    )
    system_prompt = json.loads(schema_payload["data"]["system_prompt"])
    assert "conditional_rules" not in system_prompt

    variant_payload = json.loads(
        (export_root / "variants" / "storm-front" / "spec_v2.schema-like.json").read_text(
            encoding="utf-8"
        )
    )
    variant_system_prompt = json.loads(variant_payload["data"]["system_prompt"])
    rules = variant_system_prompt["conditional_rules"]
    assert rules
    conditions = []
    for rule in rules:
        if isinstance(rule, dict):
            conditions.append(rule.get("condition", ""))
        else:
            conditions.append(rule)
    assert all("storm front" in condition.lower() for condition in conditions)
