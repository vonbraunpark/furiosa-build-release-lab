#!/usr/bin/env python3
"""Generate a portfolio report from live, verifiable GitHub release evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_PYTHONS = ("cp310", "cp311", "cp312", "cp313")
REQUIRED_RECOVERY_MARKERS = (
    "Release and asset integrity: PASS",
    "SHA256 checksums: PASS",
    "Provenance and SBOM attestations: PASS",
    "SPDX 2.3 structure: PASS",
    "Container pull and smoke tests: PASS",
)


def gh_json(*arguments: str) -> Any:
    command = ["gh", "api", *arguments]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def resolve_tag_commit(repository: str, tag: str) -> str:
    reference = gh_json(f"repos/{repository}/git/ref/tags/{tag}")
    target = reference["object"]
    if target["type"] == "tag":
        target = gh_json(f"repos/{repository}/git/tags/{target['sha']}")["object"]
    if target["type"] != "commit":
        raise SystemExit(f"tag {tag} does not resolve to a commit")
    return target["sha"]


def require_release_assets(names: list[str]) -> None:
    missing = [python for python in EXPECTED_PYTHONS if not any(python in name and name.endswith(".whl") for name in names)]
    if missing:
        raise SystemExit(f"release is missing wheels for: {', '.join(missing)}")
    for description, pattern in (
        ("Ubuntu DEB", r"\.deb$"),
        ("SPDX SBOM", r"\.spdx\.json$"),
        ("SHA256SUMS", r"^SHA256SUMS$"),
    ):
        if not any(re.search(pattern, name) for name in names):
            raise SystemExit(f"release is missing {description}")


def require_recovery_report(path: Path) -> None:
    report = path.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_RECOVERY_MARKERS if marker not in report]
    if missing:
        raise SystemExit(f"recovery report is missing PASS evidence: {missing}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True, help="OWNER/REPO")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--recovery-report", required=True, type=Path)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if re.fullmatch(r"[^/]+/[^/]+", args.repository) is None:
        raise SystemExit("repository must use OWNER/REPO format")
    if re.fullmatch(r"v\d+\.\d+\.\d+(?:[-.][0-9A-Za-z.-]+)?", args.tag) is None:
        raise SystemExit("tag must be a SemVer release tag")

    repository = gh_json(f"repos/{args.repository}")
    if repository.get("visibility") != "public" or repository.get("private"):
        raise SystemExit("portfolio evidence requires a public repository")

    # This endpoint returns success only when immutable releases are enabled.
    gh_json(f"repos/{args.repository}/immutable-releases")
    release = gh_json(f"repos/{args.repository}/releases/tags/{args.tag}")
    if release.get("draft"):
        raise SystemExit("release is still a draft")

    commit = resolve_tag_commit(args.repository, args.tag)
    assets = sorted(asset["name"] for asset in release.get("assets", []))
    require_release_assets(assets)
    require_recovery_report(args.recovery_report)

    body = release.get("body") or ""
    digest_match = re.search(r"ghcr\.io/[^\s`]+@sha256:[0-9a-f]{64}", body)
    if digest_match is None:
        raise SystemExit("release notes do not record an immutable GHCR digest")
    image = digest_match.group(0)

    check_runs = gh_json(
        f"repos/{args.repository}/commits/{commit}/check-runs?per_page=100"
    ).get("check_runs", [])
    security = [run for run in check_runs if run.get("name") == "Security gate"]
    if not any(run.get("conclusion") == "success" for run in security):
        raise SystemExit("release commit has no successful Security gate")

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    evidence = {
        "schema_version": 1,
        "generated_at": generated_at,
        "repository": repository["html_url"],
        "visibility": repository["visibility"],
        "default_branch": repository["default_branch"],
        "release_tag": args.tag,
        "release_url": release["html_url"],
        "release_commit": commit,
        "release_immutable": True,
        "release_assets": assets,
        "container": image,
        "security_gate": "PASS",
        "disaster_recovery": "PASS",
        "rehearsal_run": args.run_url,
    }

    rows = "\n".join(f"| `{name}` | GitHub Release asset |" for name in assets)
    report = f"""# Final release evidence

Generated from live GitHub API data and a successful clean-room recovery run.

| Evidence | Result |
| --- | --- |
| Public source repository | [{args.repository}]({repository['html_url']}) |
| Immutable release | [{args.tag}]({release['html_url']}) |
| Release commit | [`{commit}`]({repository['html_url']}/commit/{commit}) |
| Security enforcement gate | PASS |
| Clean-room artifact and container recovery | PASS |
| Final rehearsal workflow | [run]({args.run_url}) |
| Immutable container | `{image}` |

## Published artifacts

| Artifact | Evidence source |
| --- | --- |
{rows}

## Defensible portfolio statement

Designed and implemented a tag-driven C++/Python release system that builds and
tests manylinux wheels, an Ubuntu DEB, and a non-root OCI image; publishes them
as one immutable GitHub Release; generates checksums and SPDX SBOM evidence;
attests build provenance; enforces vulnerability and license policy; and proves
recoverability by rehydrating and testing the release from public artifacts.

## Scope boundary

This report proves the `{args.tag}` rehearsal recorded above. It does not claim
performance, adoption, or availability beyond the linked workflow evidence.

- Generated at: `{generated_at}`
- Machine-readable evidence: `portfolio-evidence.json`
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    args.json_output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("portfolio-evidence: PASS")


if __name__ == "__main__":
    main()
