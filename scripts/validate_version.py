#!/usr/bin/env python3
"""Validate release tags against the version declared by CMake."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PROJECT_PATTERN = re.compile(
    r"project\(\s*fastmath\s+VERSION\s+(\d+)\.(\d+)\.(\d+)", re.IGNORECASE
)
TAG_PATTERN = re.compile(
    r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def project_version(cmake_file: Path) -> tuple[int, int, int]:
    match = PROJECT_PATTERN.search(cmake_file.read_text(encoding="utf-8"))
    if match is None:
        raise SystemExit(f"Unable to read project version from {cmake_file}")
    return tuple(int(part) for part in match.groups())


def python_version(pyproject_file: Path) -> tuple[int, int, int]:
    text = pyproject_file.read_text(encoding="utf-8")
    project = re.search(
        r"^\[project\]\s*(?P<body>.*?)(?=^\[|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if project is None:
        raise SystemExit(f"Unable to find [project] in {pyproject_file}")
    version = re.search(
        r'^version\s*=\s*"(?P<value>[^"]+)"\s*$',
        project.group("body"),
        flags=re.MULTILINE,
    )
    if version is None:
        raise SystemExit(f"Unable to read project.version from {pyproject_file}")
    value = version.group("value")
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value)
    if match is None:
        raise SystemExit(f"Unsupported Python package version: {value}")
    return tuple(int(part) for part in match.groups())


def changelog_contains(changelog: Path, version: str) -> None:
    heading = re.compile(rf"^## \[{re.escape(version)}\](?:\s+-\s+\d{{4}}-\d{{2}}-\d{{2}})?$", re.MULTILINE)
    if heading.search(changelog.read_text(encoding="utf-8")) is None:
        raise SystemExit(f"CHANGELOG has no release section for {version}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Release tag such as v0.1.0 or v0.1.0-rc.1")
    parser.add_argument(
        "--cmake-file",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "CMakeLists.txt",
    )
    parser.add_argument(
        "--pyproject-file",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "pyproject.toml",
    )
    parser.add_argument("--changelog", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    version = project_version(args.cmake_file)
    package_version = python_version(args.pyproject_file)
    if package_version != version:
        raise SystemExit(
            f"Python package version {package_version} does not match CMake version {version}"
        )

    version_text = ".".join(map(str, version))
    print(f"project-version={version_text}")

    if args.tag is None:
        return

    tag_match = TAG_PATTERN.fullmatch(args.tag)
    if tag_match is None:
        raise SystemExit(
            "Release tag must use vMAJOR.MINOR.PATCH or "
            "vMAJOR.MINOR.PATCH-prerelease format"
        )

    tag_version = tuple(int(part) for part in tag_match.groups()[:3])
    if tag_version != version:
        raise SystemExit(
            f"Tag core version {tag_version} does not match project version {version}"
        )

    release_kind = "prerelease" if tag_match.group(4) else "stable"
    print(f"release-kind={release_kind}")

    if args.changelog is not None:
        changelog_contains(args.changelog, version_text)

    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as stream:
            stream.write(f"version={version_text}\n")
            stream.write(f"release_kind={release_kind}\n")
            stream.write(f"is_prerelease={'true' if release_kind == 'prerelease' else 'false'}\n")


if __name__ == "__main__":
    main()
