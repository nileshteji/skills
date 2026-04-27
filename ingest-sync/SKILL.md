---
name: ingest-sync
description: "Compare raw/ against wiki/ingested.md in a NileshBrain-style repo, automatically ingest any untracked markdown sources into the wiki, update tracker files, and report issues. Use when you want one command to detect new raw files and process them without extra indexing tooling."
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
3. Update wiki pages and trackers without extra indexing steps
4. Report missing tracked files, contradictions, and ambiguities clearly

## Preflight

Run these checks first:

```bash
python3 <skill-dir>/scripts/compare_ingested.py .
find raw -type f \( -name "*.md" -o -name "*.markdown" \)
find wiki -type f | sort
```

If the repository is missing expected directories or tracker files, stop and tell the user what is missing.

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
2. Create a detailed source summary page in `wiki/sources/`.
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

## Writing Style for Wiki Pages

The wiki is meant to be read by a human, not just used as a machine index.
Write pages so they are clear, useful, and worth reading later.

When writing or updating wiki pages:

- prefer elaborated summaries over terse notes
- explain the core idea, why it matters, and how it connects to nearby topics
- preserve concrete details, examples, decisions, timelines, and named people when relevant
- synthesize multiple points into readable prose instead of dumping bullet fragments
- use headings and structure so long pages stay scannable
- include concise bullet lists only when they improve readability
- make entity and concept pages feel like durable reference pages, not scratch notes
- when a source is dense, capture both the high-level takeaway and the important specifics

Aim for wiki pages that someone could read later to actually understand the topic without reopening the raw file immediately.
## Search and Discovery Guidance

Do not rely on external indexing tools for this skill.
Use normal file discovery and direct reading instead:

```bash
find raw -type f \( -name "*.md" -o -name "*.markdown" \)
rg -n "term" wiki raw
```

When deciding whether to update an existing wiki page or create a new one:

1. Search `wiki/` for relevant entity names, concepts, aliases, and phrases.
2. Read the best candidate pages directly.
3. Merge into existing pages when the topic already exists.
4. Create a new page only when no good existing page fits.

## No-Op Case

If `missing_from_tracker` is empty:

1. Do not modify wiki content unnecessarily.
2. Report that no new raw files needed ingest.
3. Still report any files tracked in `wiki/ingested.md` but missing on disk.

## Output Format

### Ingest Summary
- New raw files detected
- Wiki pages created
- Wiki pages updated
- Tracker entries added

### Issues
- Files tracked in `wiki/ingested.md` but missing on disk
- Any ingest ambiguities or contradictions found
- Any schema or structure problems that blocked ingest

## Rules

- Do not ask for per-file confirmation.
- Do not modify files under `raw/`.
- Do not mark a file as `ingested` unless the wiki updates are complete.
- Do not introduce indexing, embedding, or collection-management steps.
- If no supporting wiki/entity/concept page exists yet, create it.
- If a matching page already exists, update it instead of creating duplicates.
