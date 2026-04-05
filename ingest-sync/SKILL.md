---
name: ingest-sync
description: "Compare raw/ against wiki/ingested.md in a NileshBrain-style repo, automatically ingest any untracked markdown sources into the wiki, then refresh qmd and embed pending vectors when available. Use when you want one command to detect new raw files, process them, update tracker files, and run qmd update/embed."
model: sonnet
color: cyan
---

# Ingest Sync

Use this skill in a NileshBrain-style repository with this structure:

- `raw/` for immutable markdown sources
- `wiki/` for LLM-maintained pages
- `wiki/ingested.md` as the ingestion tracker
- `wiki/index.md` and `wiki/log.md`
- `CLAUDE.md` describing the wiki schema

## Goals

1. Detect markdown files in `raw/` that are missing from `wiki/ingested.md`
2. Automatically ingest all missing files in one pass
3. Refresh the qmd index
4. Run qmd embeddings when vector support is available
5. Continue even if embedding is unavailable or fails, and report that clearly

## Preflight

Run these checks first:

```bash
command -v qmd
qmd status
python3 <skill-dir>/scripts/compare_ingested.py .
```

Treat vector mode as unavailable if `qmd status` or `qmd embed` reports either of these:

- `sqlite-vec is not available`
- `sqlite-vec extension is unavailable`

If `qmd` is missing, stop and tell the user.

## Comparison Helper

Use the bundled helper to compare `raw/` with `wiki/ingested.md`:

```bash
python3 scripts/compare_ingested.py .
```

It returns JSON with:

- `raw_markdown_files`
- `tracked_files`
- `missing_from_tracker`
- `tracked_missing_on_disk`
- `status_by_file`

## Automatic Ingest Workflow

For every file in `missing_from_tracker`, do all of the following without asking for confirmation:

1. Read the source file thoroughly.
2. Create a source summary page in `wiki/sources/`.
3. Create or update relevant entity pages in `wiki/entities/`.
4. Create or update relevant concept pages in `wiki/concepts/`.
5. Add cross-links with Obsidian wikilinks.
6. Update `wiki/index.md`.
7. Append an entry to `wiki/log.md`.
8. Mark the file as `ingested` in `wiki/ingested.md` with today’s date.

Follow the repo schema in `CLAUDE.md`:

- use YAML frontmatter on every wiki page
- use lowercase kebab-case filenames for generated wiki pages
- keep raw sources immutable
- prefer updating overlapping pages over creating duplicates
- flag contradictions when sources conflict
- keep claims traceable to the source file being ingested

## qmd Refresh Workflow

After wiki edits are complete:

```bash
qmd update
qmd status
```

If vector support is available, run:

```bash
qmd embed
qmd status
```

If `qmd embed` fails because vector support is unavailable, do **not** roll back wiki edits. Report that ingest succeeded but embeddings were skipped or failed.

## No-Op Case

If `missing_from_tracker` is empty:

1. Do not modify wiki content unnecessarily.
2. Still inspect `qmd status`.
3. If qmd reports pending embeddings and vector mode is healthy, run `qmd embed`.
4. Report that no new raw files needed ingest.

## Output Format

### Ingest Summary
- New raw files detected
- Wiki pages created
- Wiki pages updated
- Tracker entries added

### qmd Status
- Whether `qmd update` ran
- Whether `qmd embed` ran
- Whether vector mode was available
- Remaining pending embeddings, if any

### Issues
- Files tracked in `wiki/ingested.md` but missing on disk
- Any ingest ambiguities or contradictions found
- Any embedding failures

## Rules

- Do not ask for per-file confirmation.
- Do not modify files under `raw/`.
- Do not mark a file as `ingested` unless the wiki updates are complete.
- Do not use `qmd collection sync`.
- Use `qmd update` and `qmd embed` only as described above.
- If no supporting wiki/entity/concept page exists yet, create it.
- If a matching page already exists, update it instead of creating duplicates.
