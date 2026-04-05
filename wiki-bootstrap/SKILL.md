---
name: wiki-bootstrap
description: "Scaffold a generic LLM wiki repository with NileshBrain-style defaults: raw/, wiki/, starter tracker files, CLAUDE.md, AGENTS.md, and qmd setup. Use when creating a new personal knowledge base or filling in missing wiki repo structure."
model: sonnet
color: cyan
---

# Wiki Bootstrap

Use this skill to initialize or repair an LLM-maintained markdown wiki repository.

It defaults to the NileshBrain layout, but the wording is generic so the scaffold can be reused for any personal or team knowledge base.

## When to Use

- Creating a new LLM wiki repo
- Filling in missing `raw/` / `wiki/` structure in an existing repo
- Adding starter `CLAUDE.md`, `AGENTS.md`, and tracker pages
- Setting up `qmd` collections for `wiki` and `raw`

## Inputs

Accept either of these patterns:

- explicit target path from the user, for example `/skill:wiki-bootstrap ~/Developer/my-wiki`
- no path, which means bootstrap the current working directory

Default to non-destructive behavior.
Do not overwrite existing files unless the user explicitly asks.

## Bundled Bootstrap Script

Run the helper script:

```bash
python3 <skill-dir>/scripts/bootstrap_repo.py <target-dir>
```

Examples:

```bash
python3 <skill-dir>/scripts/bootstrap_repo.py .
python3 <skill-dir>/scripts/bootstrap_repo.py ~/Developer/my-wiki
```

If the user explicitly asks to replace starter files, use:

```bash
python3 <skill-dir>/scripts/bootstrap_repo.py <target-dir> --overwrite-existing
```

## What the Script Does

1. Creates the default repo structure:
   - `raw/`
   - `raw/assets/`
   - `wiki/`
   - `wiki/sources/`
   - `wiki/entities/`
   - `wiki/concepts/`
   - `wiki/synthesis/`
2. Creates starter files when missing:
   - `wiki/index.md`
   - `wiki/log.md`
   - `wiki/ingested.md`
   - `wiki/overview.md`
   - `CLAUDE.md`
   - `AGENTS.md`
3. Fills those files with starter content for:
   - wiki schema
   - YAML frontmatter conventions
   - ingest/query/lint workflow
   - tracker table format
   - wikilink conventions
   - qmd maintenance workflow
4. Ensures `qmd` is available:
   - checks `command -v qmd`
   - if missing, tries `npm install -g @tobilu/qmd`
   - if `npm` is unavailable, falls back to `bun install -g @tobilu/qmd`
5. Inspects qmd collections and configures missing ones for `wiki` and `raw`
6. Runs `qmd update`
7. Runs `qmd embed` only when vector support appears healthy
8. Reports created files, skipped files, qmd setup status, and any limitations

## Recommended Workflow

1. Resolve the target directory from the user's request.
2. Run the bootstrap script.
3. Read the script output carefully.
4. If qmd setup was incomplete, explain the limitation clearly without rolling back the scaffold.
5. Summarize:
   - directories created
   - files created
   - files skipped because they already existed
   - qmd install/setup results
   - vector/embed limitations

## Rules

- Default to non-destructive behavior.
- If the target directory already contains part of the structure, create only the missing pieces.
- Do not delete or rewrite user-authored files unless the user explicitly asks.
- Do not rename or remove existing qmd collections automatically.
- If qmd collection names already point at another repo, report the conflict and stop short of destructive changes.
- If `qmd embed` fails because vector support is unavailable, keep the scaffold and report the failure clearly.
- Do not use `qmd collection sync`.
- Use `qmd update` and `qmd embed` only as described above.

## Good Follow-Up Suggestions

After the scaffold completes, suggest a small next step such as:

- add source markdown files under `raw/`
- run the ingest workflow
- inspect `qmd status`
- open the repo in Obsidian if the user uses it
