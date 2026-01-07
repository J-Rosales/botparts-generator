# Scope Layers & World Packs

## Scope labels for fragment files

Fragment files may declare scope with either:

- **YAML frontmatter** at the top of the file:
  ```md
  ---
  scope: world
  ---
  Content starts here.
  ```
- **JSON sidecar** next to the fragment file:
  `fragment.md.scope.json`
  ```json
  { "scope": "character" }
  ```

Valid scope values are: `world`, `character`, `variant`.

If both frontmatter and sidecar are present, the sidecar wins and a warning is emitted.

## World pack directory layout

World packs live under `sources/world/<pack>/` and are optional.

```
sources/
  world/
    <pack>/
      PROMOTE.md           # Optional: promotion gate
      meta.yaml            # Optional: promoteWorld: true
      fragments/
        atlas.md
        atlas.md.scope.json
```

- `fragments/` is required for a pack to be considered during authoring.
- World-scoped fragments still **require promotion** via `PROMOTE.md` or `meta.yaml` with
  `promoteWorld: true` when authoring tools inspect them.
- Missing `sources/world/` is non-fatal; strict scope mode is now advisory only.

## Output routing

- Export packages no longer emit standalone fragment files.
- Scope labels remain authoring-time metadata used for validation and review.

## Strict scope mode

Enable strict mode with:

- CLI: `bp build --strict-scope`
- Env: `BOTPARTS_SCOPE_STRICT=1`

Strict mode is retained for backward compatibility but currently emits a warning instead of failing a build.
