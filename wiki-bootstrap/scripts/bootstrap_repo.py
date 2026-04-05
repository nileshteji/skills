#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

VECTOR_UNAVAILABLE_MARKERS = (
    "sqlite-vec is not available",
    "sqlite-vec extension is unavailable",
)


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def combined_output(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr) if part).strip()

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(args: list[str], cwd: Path | None = None) -> CommandResult:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    return CommandResult(
        args=args,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def has_vector_unavailable_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in VECTOR_UNAVAILABLE_MARKERS)


def humanize_repo_name(name: str) -> str:
    cleaned = name.replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else "Knowledge Base"


def canonical_path(path: Path) -> str:
    try:
        return path.expanduser().resolve().as_posix()
    except FileNotFoundError:
        return path.expanduser().absolute().as_posix()


def parse_collection_path(output: str) -> str | None:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Path:"):
            return stripped.split(":", 1)[1].strip()
    return None


def ensure_directory(path: Path, created: list[str], existing: list[str]) -> None:
    if path.is_dir():
        existing.append(path.as_posix())
        return
    path.mkdir(parents=True, exist_ok=True)
    created.append(path.as_posix())


def make_starter_files(repo_root: Path, today: str) -> dict[str, str]:
    repo_dir_name = repo_root.name or "knowledge-base"
    repo_display_name = humanize_repo_name(repo_dir_name)

    claude_md = textwrap.dedent(
        f"""
        # {repo_display_name} — LLM Wiki Schema

        This repository is an LLM-maintained knowledge base. Humans add sources, review outputs, and ask questions. Agents build and maintain the wiki.

        ## Directory Structure

        ```
        {repo_dir_name}/
        ├── CLAUDE.md          # Schema, conventions, and workflows
        ├── AGENTS.md          # Operational instructions for coding agents
        ├── raw/               # Immutable source documents
        │   └── assets/        # Downloaded images and attachments
        ├── wiki/              # LLM-maintained markdown pages
        │   ├── index.md       # Master catalog of wiki pages
        │   ├── log.md         # Chronological record of operations
        │   ├── ingested.md    # Tracker for raw/ ingestion state
        │   ├── overview.md    # High-level summary of the knowledge base
        │   ├── sources/       # One page per ingested source
        │   ├── entities/      # People, orgs, tools, products
        │   ├── concepts/      # Ideas, techniques, frameworks, theories
        │   └── synthesis/     # Cross-source analysis and reusable answers
        └── .obsidian/         # Optional Obsidian config, if used
        ```

        ## Conventions

        ### Page Types

        - **Source summaries** (`wiki/sources/`) — one page per ingested source
        - **Entity pages** (`wiki/entities/`) — people, organizations, tools, products
        - **Concept pages** (`wiki/concepts/`) — ideas, frameworks, techniques, theories
        - **Synthesis pages** (`wiki/synthesis/`) — comparisons, analyses, reusable answers
        - **Overview** (`wiki/overview.md`) — high-level summary of the knowledge base

        ### File Naming

        - Use lowercase kebab-case filenames
        - Keep names short but descriptive
        - Prefer updating overlapping pages instead of creating near-duplicates

        ### Frontmatter

        Every wiki page should have YAML frontmatter:

        ```yaml
        ---
        title: Page Title
        type: source | entity | concept | synthesis | overview
        created: YYYY-MM-DD
        updated: YYYY-MM-DD
        tags: [relevant, tags]
        sources: [list of raw filenames or wiki source pages]
        ---
        ```

        Index, log, and tracker pages may use lighter frontmatter when needed.

        ### Links

        - Use Obsidian-style wikilinks: `[[page-name]]` or `[[page-name|Display Text]]`
        - Cross-link aggressively
        - When updating a page, check whether neighboring pages also need new links

        ## Ingestion Tracking

        `wiki/ingested.md` tracks every file in `raw/` and its ingestion status.

        Tracker format:

        ```markdown
        | File | Status | Date Ingested |
        |------|--------|---------------|
        | `raw/some-note.md` | ingested | 2026-04-05 |
        | `raw/assets/some-paper.md` | pending | — |
        ```

        Status values:

        - `ingested` — fully processed, wiki pages created or updated
        - `pending` — present in `raw/` but not yet processed
        - `skipped` — intentionally not ingested

        ## Workflows

        ### Ingest

        When a new source is added to `raw/`:

        1. Read the source thoroughly
        2. Create a source summary in `wiki/sources/`
        3. Create or update relevant pages in `wiki/entities/`
        4. Create or update relevant pages in `wiki/concepts/`
        5. Add or improve wikilinks
        6. Update `wiki/index.md`
        7. Append an entry to `wiki/log.md`
        8. Mark the source in `wiki/ingested.md`

        ### Query

        When answering questions from the knowledge base:

        1. Start from `wiki/index.md`
        2. Read the relevant wiki pages and source summaries
        3. Synthesize an answer grounded in the repo contents
        4. If the answer is reusable, save it as a synthesis page

        ### Lint

        When health-checking the repo:

        1. Scan all wiki pages
        2. Look for contradictions, stale claims, missing pages, weak cross-links, and orphan content
        3. Fix issues carefully and record meaningful maintenance in `wiki/log.md`

        ## qmd Workflow

        Use `qmd` to index and search this repo.

        Preflight:

        ```bash
        command -v qmd
        qmd collection list
        qmd collection show wiki
        qmd collection show raw
        ```

        Refresh the index:

        ```bash
        qmd update
        qmd status
        ```

        If vector support is healthy:

        ```bash
        qmd embed
        qmd status
        ```

        Do not use `qmd collection sync`.

        ## Principles

        - Keep `raw/` immutable
        - Prefer updating existing pages over duplicates
        - Flag uncertainty and contradictions explicitly
        - Keep claims traceable to sources
        - Keep pages focused and readable on their own
        """
    ).strip() + "\n"

    agents_md = textwrap.dedent(
        """
        # AGENTS.md

        This repository is an LLM-maintained wiki with qmd-backed search.

        ## Structure

        - `raw/` holds immutable source material
        - `raw/assets/` holds downloaded attachments
        - `wiki/` holds agent-maintained markdown pages
        - `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, and `wiki/synthesis/` group page types
        - `wiki/index.md` catalogs pages
        - `wiki/log.md` records operations
        - `wiki/ingested.md` tracks source ingestion state
        - `CLAUDE.md` defines the schema and conventions

        ## Agent Rules

        - Do not modify files under `raw/` unless the user explicitly asks
        - Treat `raw/` as immutable source material
        - Use lowercase kebab-case for new wiki filenames
        - Include YAML frontmatter on wiki content pages
        - Use Obsidian-style wikilinks between related pages
        - Prefer updating overlapping pages over creating duplicates
        - Flag contradictions when sources disagree
        - Update `wiki/index.md`, `wiki/log.md`, and `wiki/ingested.md` during ingest work
        - Keep claims traceable to the sources that support them

        ## Core Workflows

        ### Ingest

        1. Read the source in `raw/`
        2. Create or update `wiki/sources/`, `wiki/entities/`, and `wiki/concepts/`
        3. Add wikilinks and cross-references
        4. Update `wiki/index.md`
        5. Append to `wiki/log.md`
        6. Mark the source in `wiki/ingested.md`

        ### Query

        1. Start from `wiki/index.md`
        2. Read the relevant pages
        3. Answer from repo evidence
        4. Save reusable answers in `wiki/synthesis/` when appropriate

        ### Lint

        1. Check for stale claims, contradictions, weak cross-links, and orphan pages
        2. Fix problems carefully
        3. Record meaningful maintenance in `wiki/log.md`

        ## qmd Commands

        ```bash
        qmd status
        qmd collection list
        qmd collection show wiki
        qmd collection show raw
        qmd update
        qmd embed
        ```

        Do not use `qmd collection sync`.
        """
    ).strip() + "\n"

    index_md = textwrap.dedent(
        f"""
        ---
        title: Wiki Index
        type: index
        updated: {today}
        ---

        # Wiki Index

        Master catalog of all pages in the knowledge base.

        ## Overview

        - [[overview|Overview]] — High-level summary of the knowledge base

        ## Sources

        _No source summary pages yet._

        ## Entities

        _No entity pages yet._

        ## Concepts

        _No concept pages yet._

        ## Synthesis

        _No synthesis pages yet._

        ## Tracking

        - [[ingested|Ingestion Tracker]] — Which raw files have been processed
        """
    ).strip() + "\n"

    log_md = textwrap.dedent(
        f"""
        ---
        title: Wiki Log
        type: log
        updated: {today}
        ---

        # Wiki Log

        Chronological record of all wiki operations.

        ## [{today}] init | Wiki initialized

        Set up the LLM wiki scaffold: `raw/`, `wiki/`, starter tracker pages, schema docs, and qmd-ready directories.
        """
    ).strip() + "\n"

    ingested_md = textwrap.dedent(
        f"""
        ---
        title: Ingestion Tracker
        type: tracker
        updated: {today}
        ---

        # Ingestion Tracker

        | File | Status | Date Ingested |
        |------|--------|---------------|
        """
    ).strip() + "\n"

    overview_md = textwrap.dedent(
        f"""
        ---
        title: Overview
        type: overview
        created: {today}
        updated: {today}
        tags: []
        sources: []
        ---

        # {repo_display_name} — Overview

        This knowledge base has just been initialized.

        ## Current Focus

        Start by adding source material under `raw/`, then ingest it into `wiki/` pages with cross-links.

        ## How It Works

        1. **Add sources** — place articles, papers, notes, or transcripts under `raw/`
        2. **Ingest** — convert sources into wiki pages with summaries, entities, concepts, and links
        3. **Explore** — browse the wiki, follow links, and refine the structure over time
        4. **Ask questions** — answer from the wiki and save reusable answers back into `wiki/synthesis/`
        5. **Lint** — periodically clean up contradictions, stale claims, and weak cross-references

        ## Starter Stats

        - Sources ingested: 0
        - Source pages: 0
        - Entity pages: 0
        - Concept pages: 0
        - Synthesis pages: 0
        """
    ).strip() + "\n"

    return {
        "CLAUDE.md": claude_md,
        "AGENTS.md": agents_md,
        "wiki/index.md": index_md,
        "wiki/log.md": log_md,
        "wiki/ingested.md": ingested_md,
        "wiki/overview.md": overview_md,
    }


def ensure_qmd_available() -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": False,
        "installed": False,
        "install_attempted": False,
        "install_method": None,
        "path": None,
        "notes": [],
    }

    qmd_path = shutil.which("qmd")
    if qmd_path:
        result["available"] = True
        result["path"] = qmd_path
        result["notes"].append("qmd already available on PATH")
        return result

    for method, command in (
        ("npm", ["npm", "install", "-g", "@tobilu/qmd"]),
        ("bun", ["bun", "install", "-g", "@tobilu/qmd"]),
    ):
        if shutil.which(method) is None:
            continue

        result["install_attempted"] = True
        result["install_method"] = method
        install_result = run_command(command)
        result["install_command"] = " ".join(command)
        result["install_returncode"] = install_result.returncode
        result["install_output"] = install_result.combined_output

        qmd_path = shutil.which("qmd")
        if install_result.ok and qmd_path:
            result["available"] = True
            result["installed"] = True
            result["path"] = qmd_path
            result["notes"].append(f"installed qmd with {method}")
            return result

        result["notes"].append(f"failed to install qmd with {method}")

    if not result["install_attempted"]:
        result["notes"].append("qmd missing and neither npm nor bun is available")
    elif not result["available"]:
        result["notes"].append("qmd install was attempted but qmd is still unavailable")

    return result


def inspect_collection(name: str) -> dict[str, Any]:
    show_result = run_command(["qmd", "collection", "show", name])
    info: dict[str, Any] = {
        "name": name,
        "exists": show_result.ok,
        "status": "present" if show_result.ok else "missing",
        "path": parse_collection_path(show_result.combined_output),
        "command_output": show_result.combined_output,
    }
    return info


def configure_collections(repo_root: Path) -> dict[str, Any]:
    collection_report: dict[str, Any] = {
        "list_ok": False,
        "list_output": "",
        "collections": {},
        "ready_for_update": True,
        "notes": [],
    }

    list_result = run_command(["qmd", "collection", "list"])
    collection_report["list_ok"] = list_result.ok
    collection_report["list_output"] = list_result.combined_output
    if not list_result.ok:
        collection_report["ready_for_update"] = False
        collection_report["notes"].append("failed to inspect qmd collections")
        return collection_report

    for name, relative_path in (("wiki", "wiki"), ("raw", "raw")):
        target_path = canonical_path(repo_root / relative_path)
        inspected = inspect_collection(name)
        entry: dict[str, Any] = {
            "name": name,
            "target_path": target_path,
            "status": inspected["status"],
            "existing_path": inspected["path"],
            "notes": [],
        }

        if inspected["exists"]:
            existing_path = inspected["path"]
            if existing_path and canonical_path(Path(existing_path)) == target_path:
                entry["status"] = "existing"
                entry["notes"].append("collection already points to the target path")
            else:
                entry["status"] = "conflict"
                entry["notes"].append(
                    "collection name already exists and points to a different path"
                )
                collection_report["ready_for_update"] = False
        else:
            add_result = run_command(
                ["qmd", "collection", "add", target_path, "--name", name]
            )
            entry["add_output"] = add_result.combined_output
            if add_result.ok:
                entry["status"] = "added"
                entry["notes"].append("collection created successfully")
            else:
                entry["status"] = "add_failed"
                entry["notes"].append("failed to add collection")
                collection_report["ready_for_update"] = False

        collection_report["collections"][name] = entry

    return collection_report


def run_qmd_refresh() -> dict[str, Any]:
    refresh: dict[str, Any] = {
        "update": {"ran": False, "ok": False, "output": ""},
        "status_after_update": {"ok": False, "output": ""},
        "embed": {"ran": False, "ok": False, "status": "skipped", "output": ""},
        "status_after_embed": {"ok": False, "output": ""},
        "vector_available": None,
        "notes": [],
    }

    update_result = run_command(["qmd", "update"])
    refresh["update"] = {
        "ran": True,
        "ok": update_result.ok,
        "output": update_result.combined_output,
    }
    if not update_result.ok:
        refresh["notes"].append("qmd update failed")
        return refresh

    status_result = run_command(["qmd", "status"])
    refresh["status_after_update"] = {
        "ok": status_result.ok,
        "output": status_result.combined_output,
    }
    if not status_result.ok:
        refresh["notes"].append("qmd status failed after update")
        return refresh

    if has_vector_unavailable_marker(status_result.combined_output):
        refresh["vector_available"] = False
        refresh["embed"] = {
            "ran": False,
            "ok": False,
            "status": "vector_unavailable",
            "output": status_result.combined_output,
        }
        refresh["notes"].append("vector support is unavailable; skipped qmd embed")
        return refresh

    refresh["vector_available"] = True
    embed_result = run_command(["qmd", "embed"])
    if has_vector_unavailable_marker(embed_result.combined_output):
        refresh["embed"] = {
            "ran": True,
            "ok": False,
            "status": "vector_unavailable",
            "output": embed_result.combined_output,
        }
        refresh["vector_available"] = False
        refresh["notes"].append("qmd embed reported unavailable vector support")
        return refresh

    refresh["embed"] = {
        "ran": True,
        "ok": embed_result.ok,
        "status": "ran" if embed_result.ok else "failed",
        "output": embed_result.combined_output,
    }
    if not embed_result.ok:
        refresh["notes"].append("qmd embed failed")
        return refresh

    final_status = run_command(["qmd", "status"])
    refresh["status_after_embed"] = {
        "ok": final_status.ok,
        "output": final_status.combined_output,
    }
    if not final_status.ok:
        refresh["notes"].append("qmd status failed after embed")

    return refresh


def bootstrap_repo(
    target_dir: Path,
    overwrite_existing: bool = False,
    skip_qmd: bool = False,
) -> dict[str, Any]:
    today = date.today().isoformat()
    repo_root = target_dir.expanduser().resolve()
    repo_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "repo_root": repo_root.as_posix(),
        "created_directories": [],
        "existing_directories": [],
        "created_files": [],
        "overwritten_files": [],
        "skipped_files": [],
        "qmd": {
            "skipped": skip_qmd,
            "install": None,
            "collections": None,
            "refresh": None,
        },
        "notes": [],
    }

    required_directories = [
        repo_root / "raw",
        repo_root / "raw" / "assets",
        repo_root / "wiki",
        repo_root / "wiki" / "sources",
        repo_root / "wiki" / "entities",
        repo_root / "wiki" / "concepts",
        repo_root / "wiki" / "synthesis",
    ]

    for directory in required_directories:
        ensure_directory(
            directory,
            report["created_directories"],
            report["existing_directories"],
        )

    starter_files = make_starter_files(repo_root, today)
    for relative_path, content in starter_files.items():
        path = repo_root / relative_path
        existed_before = path.exists()
        if existed_before and not overwrite_existing:
            report["skipped_files"].append(path.as_posix())
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if existed_before:
            report["overwritten_files"].append(path.as_posix())
        else:
            report["created_files"].append(path.as_posix())

    if skip_qmd:
        report["notes"].append("skipped qmd setup by request")
        return report

    qmd_install = ensure_qmd_available()
    report["qmd"]["install"] = qmd_install
    if not qmd_install["available"]:
        report["notes"].append("repo scaffold created, but qmd is unavailable")
        return report

    collections = configure_collections(repo_root)
    report["qmd"]["collections"] = collections
    if not collections["ready_for_update"]:
        report["notes"].append(
            "repo scaffold created, but qmd collections are not ready for update"
        )
        return report

    refresh = run_qmd_refresh()
    report["qmd"]["refresh"] = refresh
    if not refresh["update"]["ok"]:
        report["notes"].append("repo scaffold created, but qmd update failed")
    elif refresh["embed"]["status"] in {"failed", "vector_unavailable"}:
        report["notes"].append("repo scaffold created; qmd embed did not complete cleanly")

    return report


def print_human_report(report: dict[str, Any]) -> None:
    print("Wiki Bootstrap Summary")
    print(f"Target: {report['repo_root']}")
    print()

    print("Directories")
    if report["created_directories"]:
        print("  Created:")
        for path in report["created_directories"]:
            print(f"    - {path}")
    if report["existing_directories"]:
        print("  Already existed:")
        for path in report["existing_directories"]:
            print(f"    - {path}")
    if not report["created_directories"] and not report["existing_directories"]:
        print("  None")
    print()

    print("Files")
    if report["created_files"]:
        print("  Created:")
        for path in report["created_files"]:
            print(f"    - {path}")
    if report["overwritten_files"]:
        print("  Overwritten:")
        for path in report["overwritten_files"]:
            print(f"    - {path}")
    if report["skipped_files"]:
        print("  Skipped existing:")
        for path in report["skipped_files"]:
            print(f"    - {path}")
    if (
        not report["created_files"]
        and not report["overwritten_files"]
        and not report["skipped_files"]
    ):
        print("  None")
    print()

    print("qmd")
    if report["qmd"]["skipped"]:
        print("  Skipped by request")
    else:
        install = report["qmd"]["install"]
        if install is None:
            print("  qmd step was not run")
        else:
            availability = "available" if install["available"] else "unavailable"
            print(f"  Install status: {availability}")
            if install.get("path"):
                print(f"  qmd path: {install['path']}")
            for note in install.get("notes", []):
                print(f"  - {note}")

        collections = report["qmd"]["collections"]
        if collections is not None:
            print("  Collections:")
            for name in ("wiki", "raw"):
                entry = collections["collections"].get(name)
                if not entry:
                    continue
                print(f"    - {name}: {entry['status']}")
                print(f"      target: {entry['target_path']}")
                if entry.get("existing_path"):
                    print(f"      existing: {entry['existing_path']}")
                for note in entry.get("notes", []):
                    print(f"      note: {note}")
            if collections.get("notes"):
                for note in collections["notes"]:
                    print(f"  - {note}")

        refresh = report["qmd"]["refresh"]
        if refresh is not None:
            print("  Refresh:")
            print(
                f"    - qmd update: {'ok' if refresh['update']['ok'] else 'failed'}"
            )
            embed_status = refresh["embed"]["status"]
            print(f"    - qmd embed: {embed_status}")
            if refresh["vector_available"] is not None:
                print(
                    f"    - vector support: {'available' if refresh['vector_available'] else 'unavailable'}"
                )
            for note in refresh.get("notes", []):
                print(f"    - note: {note}")
    print()

    if report["notes"]:
        print("Notes")
        for note in report["notes"]:
            print(f"  - {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a generic LLM wiki repository with NileshBrain-style defaults."
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Directory to bootstrap. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Overwrite existing starter files instead of skipping them.",
    )
    parser.add_argument(
        "--skip-qmd",
        action="store_true",
        help="Skip qmd install, collection setup, update, and embed steps.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        report = bootstrap_repo(
            target_dir=Path(args.target_dir),
            overwrite_existing=args.overwrite_existing,
            skip_qmd=args.skip_qmd,
        )
    except Exception as exc:
        error_report = {
            "error": str(exc),
            "target_dir": Path(args.target_dir).expanduser().as_posix(),
        }
        if args.json:
            print(json.dumps(error_report, indent=2, sort_keys=True))
        else:
            print("Wiki Bootstrap Failed")
            print(f"Target: {error_report['target_dir']}")
            print(f"Error: {error_report['error']}")
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human_report(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
