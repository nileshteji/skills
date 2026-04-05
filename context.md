# Skills Context

## `ingest-sync/`
Project skill for NileshBrain-style knowledge bases. It compares `raw/` against `wiki/ingested.md`, instructs the agent to auto-ingest any untracked markdown sources into wiki pages, then refreshes qmd indexing and embeddings.

## `ingest-sync/SKILL.md`
Defines the end-to-end ingest-sync workflow, including repo validation, qmd preflight checks, automatic ingest behavior, tracker updates, and post-ingest `qmd update` / `qmd embed` handling.

## `ingest-sync/scripts/compare_ingested.py`
Helper script that deterministically compares markdown files under `raw/` with tracker entries in `wiki/ingested.md` and returns JSON listing missing, tracked, and stale entries.
