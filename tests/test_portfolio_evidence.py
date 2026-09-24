#!/usr/bin/env python3
"""Unit tests for live portfolio evidence generation."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_portfolio_evidence", ROOT / "scripts/generate_portfolio_evidence.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PortfolioEvidenceTest(unittest.TestCase):
    def test_generates_report_from_verified_public_release(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        assets = [
            {"name": f"furiosa_build_release_lab-0.1.0-{python}-manylinux.whl"}
            for python in MODULE.EXPECTED_PYTHONS
        ] + [
            {"name": "fastmath_0.1.0_amd64.deb"},
            {"name": "furiosa-build-release-lab-0.1.0.spdx.json"},
            {"name": "SHA256SUMS"},
        ]

        def fake_gh_json(endpoint: str):
            if endpoint == "repos/example/furiosa-build-release-lab":
                return {
                    "visibility": "public",
                    "private": False,
                    "html_url": "https://github.com/example/furiosa-build-release-lab",
                    "default_branch": "main",
                }
            if endpoint.endswith("/immutable-releases"):
                return {"enabled": True}
            if endpoint.endswith("/releases/tags/v0.1.0"):
                return {
                    "draft": False,
                    "html_url": "https://github.com/example/furiosa-build-release-lab/releases/tag/v0.1.0",
                    "assets": assets,
                    "body": f"Immutable digest: `ghcr.io/example/furiosa-build-release-lab@sha256:{digest}`",
                }
            if endpoint.endswith("/git/ref/tags/v0.1.0"):
                return {"object": {"type": "commit", "sha": commit}}
            if "/check-runs?" in endpoint:
                return {"check_runs": [{"name": "Security gate", "conclusion": "success"}]}
            raise AssertionError(endpoint)

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            recovery = directory / "recovery.md"
            recovery.write_text("\n".join(MODULE.REQUIRED_RECOVERY_MARKERS), encoding="utf-8")
            report = directory / "report.md"
            machine = directory / "evidence.json"
            argv = [
                "generate_portfolio_evidence.py",
                "--repository", "example/furiosa-build-release-lab",
                "--tag", "v0.1.0",
                "--recovery-report", str(recovery),
                "--run-url", "https://github.com/example/repo/actions/runs/1",
                "--output", str(report),
                "--json-output", str(machine),
            ]
            with patch.object(MODULE, "gh_json", side_effect=fake_gh_json), patch.object(sys, "argv", argv):
                MODULE.main()

            self.assertIn("Defensible portfolio statement", report.read_text(encoding="utf-8"))
            evidence = json.loads(machine.read_text(encoding="utf-8"))
            self.assertEqual(evidence["release_commit"], commit)
            self.assertEqual(evidence["security_gate"], "PASS")

    def test_rejects_missing_python_wheel(self) -> None:
        with self.assertRaises(SystemExit):
            MODULE.require_release_assets(["package-cp310.whl", "file.deb", "x.spdx.json", "SHA256SUMS"])


if __name__ == "__main__":
    unittest.main()
