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

- `fragments/` is required for a pack to emit content.
- World-scoped fragments **require promotion** via `PROMOTE.md` or `meta.yaml` with
  `promoteWorld: true`.
- Missing `sources/world/` is non-fatal unless strict scope mode is enabled.

## Output routing

- World pack fragments are emitted under:
  `dist/src/data/fragments/world/<pack>/<scope>/filename`
- Character fragments remain under each character’s
  `dist/src/data/characters/<slug>/fragments/`.
- Variant fragments remain under
  `dist/src/data/characters/<slug>/fragments/variants/`.

## Strict scope mode

Enable strict mode with:

- CLI: `bp build --strict-scope`
- Env: `BOTPARTS_SCOPE_STRICT=1`

Strict mode turns missing world packs or promotion gate violations into errors.
