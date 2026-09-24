# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog, and the project uses Semantic Versioning.

## [Unreleased]

## [0.1.0] - 2026-09-22

### Added

- C++17 `fastmath` library with CMake unit tests.
- pybind11 Python extension and CPython 3.10–3.13 manylinux wheels.
- CPack-based Ubuntu `.deb` package with install, consumer, and removal tests.
- Multi-stage non-root Docker image with SemVer and immutable SHA tags.
- Tag-driven release validation, SHA256 checksums, and GitHub Release publishing.
- SPDX SBOM generation, build provenance and SBOM attestations, container
  attestations, and post-publication release verification.
- Immutable-release retention policy, protected container-alias rollback,
  monthly disaster-recovery verification, and machine-readable policy audit.
- Ubuntu/GCC/Clang/Python compatibility matrix, controlled C++ export surface,
  Libabigail ABI checks, and isolated byte-for-byte package rebuild comparison.
- CodeQL, dependency and license review, Python auditing, source and container
  scanning, expiring exceptions, and release-enforced security gates.
- Public deployment runbook, clean-room end-to-end release rehearsal, and a
  live GitHub API-backed Markdown/JSON portfolio evidence generator.
