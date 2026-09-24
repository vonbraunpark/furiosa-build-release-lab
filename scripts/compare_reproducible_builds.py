#!/usr/bin/env python3
"""Compare two artifact directories and emit JSON and Markdown evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--json-report", type=Path, required=True)
    parser.add_argument("--markdown-report", type=Path, required=True)
    args = parser.parse_args()

    first = inventory(args.first)
    second = inventory(args.second)
    names = sorted(set(first) | set(second))
    entries = [
        {
            "artifact": name,
            "first_sha256": first.get(name),
            "second_sha256": second.get(name),
            "reproducible": first.get(name) == second.get(name),
        }
        for name in names
    ]
    reproducible = bool(entries) and all(item["reproducible"] for item in entries)

    report = {
        "schema_version": 1,
        "reproducible": reproducible,
        "artifact_count": len(entries),
        "artifacts": entries,
    }
    args.json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    rows = [
        "# Reproducible build report",
        "",
        f"Overall result: **{'PASS' if reproducible else 'FAIL'}**",
        "",
        "| Artifact | Build A SHA-256 | Build B SHA-256 | Result |",
        "| --- | --- | --- | --- |",
    ]
    for item in entries:
        rows.append(
            f"| `{item['artifact']}` | `{item['first_sha256'] or 'missing'}` | "
            f"`{item['second_sha256'] or 'missing'}` | "
            f"{'PASS' if item['reproducible'] else 'FAIL'} |"
        )
    args.markdown_report.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"reproducible-build: {'PASS' if reproducible else 'FAIL'}")
    raise SystemExit(0 if reproducible else 1)


if __name__ == "__main__":
    main()
