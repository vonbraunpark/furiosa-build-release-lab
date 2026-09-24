#!/usr/bin/env python3
"""Fail when workflow artifact retention diverges from the release policy."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / ".github" / "retention-policy.json"


def workflow(name: str) -> str:
    path = ROOT / ".github" / "workflows" / name
    if not path.is_file():
        raise SystemExit(f"Missing required workflow: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def retention_values(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"^\s*retention-days:\s*(\d+)\s*$", text, re.MULTILINE)]


def main() -> None:
    policy = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    action_policy = policy["actions"]
    handoff_days = action_policy["release_handoff_days"]

    if retention_values(workflow("release.yml")).count(handoff_days) < 2:
        raise SystemExit(
            f"release.yml must retain both wheel and DEB artifacts for {handoff_days} days"
        )

    for name in ("wheels.yml", "deb.yml"):
        if handoff_days not in retention_values(workflow(name)):
            raise SystemExit(f"{name} must use retention-days: {handoff_days}")

    expected = {
        "compatibility.yml": action_policy["engineering_report_days"],
        "abi.yml": action_policy["engineering_report_days"],
        "reproducibility.yml": action_policy["engineering_report_days"],
        "security.yml": action_policy["engineering_report_days"],
        "disaster-recovery.yml": action_policy["disaster_recovery_report_days"],
        "rollback.yml": action_policy["rollback_record_days"],
        "final-rehearsal.yml": action_policy["rollback_record_days"],
    }
    for name, days in expected.items():
        if days not in retention_values(workflow(name)):
            raise SystemExit(f"{name} must use retention-days: {days}")

    if "environment: release-rollback" not in workflow("rollback.yml"):
        raise SystemExit("rollback.yml must use the protected release-rollback environment")
    if policy["immutable_release"]["tags"] != "never-reuse":
        raise SystemExit("immutable release tags must use the never-reuse policy")

    print("retention-policy: OK")


if __name__ == "__main__":
    main()
