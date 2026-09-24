#!/usr/bin/env python3
"""Validate security policy and time-bounded vulnerability exceptions."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    policy = load(ROOT / "security" / "policy.json")
    exception_document = load(ROOT / "security" / "exceptions.json")

    if policy.get("schema_version") != 1 or exception_document.get("schema_version") != 1:
        raise SystemExit("unsupported security policy schema")

    allowed = policy["licenses"]["allowed"]
    if not allowed or len(allowed) != len(set(allowed)) or "MIT" not in allowed:
        raise SystemExit("license allowlist must be non-empty, unique, and include MIT")

    maximum_days = policy["exceptions"]["maximum_days"]
    required = set(policy["exceptions"]["required_fields"])
    today = date.today()
    seen: set[tuple[str, str]] = set()

    for item in exception_document["exceptions"]:
        missing = required - item.keys()
        if missing:
            raise SystemExit(f"security exception is missing: {sorted(missing)}")
        key = (item["id"], item["package"])
        if key in seen:
            raise SystemExit(f"duplicate security exception: {key}")
        seen.add(key)
        created = datetime.strptime(item["created"], "%Y-%m-%d").date()
        expires = datetime.strptime(item["expires"], "%Y-%m-%d").date()
        if created > today or expires < created:
            raise SystemExit(f"invalid security exception date range: {key}")
        if expires < today:
            raise SystemExit(f"expired security exception: {key} expired {expires}")
        if (expires - created).days > maximum_days:
            raise SystemExit(f"security exception exceeds {maximum_days} days: {key}")
        if not item["owner"].strip() or not item["reason"].strip():
            raise SystemExit(f"security exception needs owner and reason: {key}")

    security_workflow = (ROOT / ".github" / "workflows" / "security.yml").read_text(
        encoding="utf-8"
    )
    for identifier in allowed:
        if identifier not in security_workflow:
            raise SystemExit(f"security workflow license allowlist is missing {identifier}")
    trivy_references = re.findall(r"aquasecurity/trivy-action@([^\s]+)", security_workflow)
    if len(trivy_references) != 2 or any(
        re.fullmatch(r"[0-9a-f]{40}", reference) is None
        for reference in trivy_references
    ):
        raise SystemExit("every Trivy action reference must use a full commit SHA")

    release_workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    if "Security gate" not in release_workflow or "security-preflight" not in release_workflow:
        raise SystemExit("release workflow must enforce the commit security gate")

    print("security-policy: OK")


if __name__ == "__main__":
    main()
