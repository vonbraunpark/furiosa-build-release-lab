#!/usr/bin/env python3
"""Validate release assets, generate SHA256SUMS, and compose release notes."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


TAG_PATTERN = re.compile(
    r"^v(?P<version>(?P<core>\d+\.\d+\.\d+)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?)$"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def release_changelog(changelog: Path, core_version: str) -> str:
    text = changelog.read_text(encoding="utf-8")
    section = re.search(
        rf"^## \[{re.escape(core_version)}\](?:\s+-\s+\d{{4}}-\d{{2}}-\d{{2}})?\s*$"
        rf"(?P<body>.*?)(?=^## \[|^\[[^\]]+\]:|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if section is None:
        raise SystemExit(f"Unable to extract CHANGELOG section for {core_version}")
    return section.group("body").strip()


def validate_assets(assets_dir: Path) -> list[Path]:
    wheels = sorted(assets_dir.glob("*.whl"))
    debs = sorted(assets_dir.glob("*.deb"))
    sboms = sorted(assets_dir.glob("*.spdx.json"))
    expected_abis = {"cp310", "cp311", "cp312", "cp313"}
    found_abis = {
        abi for abi in expected_abis if any(f"-{abi}-" in wheel.name for wheel in wheels)
    }

    if len(wheels) != 4 or found_abis != expected_abis:
        raise SystemExit(
            f"Expected one wheel for each of {sorted(expected_abis)}; "
            f"found {[wheel.name for wheel in wheels]}"
        )
    if len(debs) != 1:
        raise SystemExit(f"Expected exactly one DEB package; found {[deb.name for deb in debs]}")
    if len(sboms) != 1:
        raise SystemExit(
            f"Expected exactly one SPDX JSON SBOM; found {[sbom.name for sbom in sboms]}"
        )
    return sorted([*wheels, *debs, *sboms], key=lambda path: path.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--digest", required=True)
    args = parser.parse_args()

    tag_match = TAG_PATTERN.fullmatch(args.tag)
    if tag_match is None:
        raise SystemExit(f"Invalid release tag: {args.tag}")

    artifacts = validate_assets(args.assets_dir)
    checksum_file = args.assets_dir / "SHA256SUMS"
    checksum_file.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in artifacts),
        encoding="utf-8",
    )

    version = tag_match.group("version")
    changelog = release_changelog(args.changelog, tag_match.group("core"))
    notes = (
        f"{changelog}\n\n"
        "## Container image\n\n"
        f"- Version: `{args.image}:{version}`\n"
        f"- Immutable digest: `{args.image}@{args.digest}`\n\n"
        "## Integrity\n\n"
        "Verify every downloaded asset with `SHA256SUMS`, then verify its "
        "GitHub artifact attestation. The SPDX JSON document is the release SBOM.\n"
    )
    args.notes.write_text(notes, encoding="utf-8")

    print(f"Prepared {len(artifacts)} artifacts plus {checksum_file.name}")


if __name__ == "__main__":
    main()
