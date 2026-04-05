# Skills Context

## `ingest-sync/`
Project skill for NileshBrain-style knowledge bases. It compares `raw/` against `wiki/ingested.md`, instructs the agent to auto-ingest any untracked markdown sources into wiki pages, then refreshes qmd indexing and embeddings.

## `ingest-sync/SKILL.md`
Defines the end-to-end ingest-sync workflow, including repo validation, qmd preflight checks, automatic ingest behavior, tracker updates, and post-ingest `qmd update` / `qmd embed` handling.

## `ingest-sync/scripts/compare_ingested.py`
Helper script that deterministically compares markdown files under `raw/` with tracker entries in `wiki/ingested.md` and returns JSON listing missing, tracked, and stale entries.

## `wiki-bootstrap/`
Skill for scaffolding a generic LLM wiki repository with NileshBrain-style defaults. It creates the standard `raw/` and `wiki/` layout, writes starter docs and tracker pages, and tries to set up qmd non-destructively.

## `wiki-bootstrap/SKILL.md`
Defines when to use the bootstrap flow, how to pass a target directory, which starter files are created, and the rules around non-destructive qmd setup and vector fallback behavior.

## `wiki-bootstrap/scripts/bootstrap_repo.py`
Bootstrap helper that creates missing directories and starter files, optionally overwrites those starter files when requested, checks or installs `qmd`, inspects `wiki` and `raw` collections, runs `qmd update`, and attempts `qmd embed` only when vector support looks healthy.
