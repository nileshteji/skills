#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

TRACKER_ROW_RE = re.compile(
    r"^\|\s*`(?P<file>raw/[^`]+)`\s*\|\s*(?P<status>[^|]+?)\s*\|\s*(?P<date>[^|]+?)\s*\|\s*$"
)


def is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def scan_raw_markdown(repo_root: Path) -> list[str]:
    raw_dir = repo_root / "raw"
    files: list[str] = []
    for path in raw_dir.rglob("*.md"):
        rel = path.relative_to(repo_root)
        if is_hidden(rel):
            continue
        files.append(rel.as_posix())
    return sorted(files)


def parse_tracker(repo_root: Path) -> dict[str, dict[str, str]]:
    tracker_path = repo_root / "wiki" / "ingested.md"
    tracked: dict[str, dict[str, str]] = {}
    for line in tracker_path.read_text(encoding="utf-8").splitlines():
        match = TRACKER_ROW_RE.match(line)
        if not match:
            continue
        file_path = match.group("file").strip()
        tracked[file_path] = {
            "status": match.group("status").strip(),
            "date": match.group("date").strip(),
        }
    return tracked


def main() -> int:
    repo_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    raw_dir = repo_root / "raw"
    wiki_dir = repo_root / "wiki"
    tracker_path = wiki_dir / "ingested.md"

    if not raw_dir.is_dir():
        print(json.dumps({"error": f"Missing raw directory: {raw_dir}"}, indent=2))
        return 1

    if not wiki_dir.is_dir():
        print(json.dumps({"error": f"Missing wiki directory: {wiki_dir}"}, indent=2))
        return 1

    if not tracker_path.is_file():
        print(json.dumps({"error": f"Missing tracker file: {tracker_path}"}, indent=2))
        return 1

    raw_files = scan_raw_markdown(repo_root)
    tracked = parse_tracker(repo_root)
    tracked_files = sorted(tracked.keys())

    raw_set = set(raw_files)
    tracked_set = set(tracked_files)

    result = {
        "repo_root": repo_root.as_posix(),
        "raw_markdown_files": raw_files,
        "tracked_files": tracked_files,
        "missing_from_tracker": sorted(raw_set - tracked_set),
        "tracked_missing_on_disk": sorted(tracked_set - raw_set),
        "status_by_file": tracked,
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
