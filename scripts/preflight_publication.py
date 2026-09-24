#!/usr/bin/env python3
"""Static preflight for publishing this repository and running the final rehearsal."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "docs/PORTFOLIO.md",
    "docs/PUBLICATION_RUNBOOK.md",
    "docs/FINAL_RELEASE_REPORT.md",
    ".github/workflows/release.yml",
    ".github/workflows/final-rehearsal.yml",
    "security/policy.json",
)


def main() -> None:
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"missing publication files: {missing}")

    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    if len(workflows) != 13:
        raise SystemExit(f"expected 13 workflows, found {len(workflows)}")
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        if not re.search(r"^name:\s*\S", text, re.MULTILINE):
            raise SystemExit(f"workflow has no name: {workflow.name}")
        if not re.search(r"^on:\s*(?:$|\S)", text, re.MULTILINE):
            raise SystemExit(f"workflow has no trigger: {workflow.name}")

    rehearsal = (ROOT / ".github/workflows/final-rehearsal.yml").read_text(encoding="utf-8")
    for marker in (
        "workflow_dispatch:",
        "immutable-releases",
        "verify_disaster_recovery.sh",
        "generate_portfolio_evidence.py",
        "retention-days: 90",
    ):
        if marker not in rehearsal:
            raise SystemExit(f"final rehearsal is missing {marker}")

    forbidden_names = (".env", "id_rsa", "id_ed25519")
    tracked = [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]
    leaked_names = [str(path.relative_to(ROOT)) for path in tracked if path.name in forbidden_names]
    if leaked_names:
        raise SystemExit(f"potential secret files must not be published: {leaked_names}")

    print("publication-preflight: OK")


if __name__ == "__main__":
    main()
