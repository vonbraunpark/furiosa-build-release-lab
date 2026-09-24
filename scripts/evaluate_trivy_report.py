#!/usr/bin/env python3
"""Apply repository security policy to one or more Trivy JSON reports."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path, required=True)
    parser.add_argument("--report", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    policy = load(args.policy)
    raw_exceptions = load(args.exceptions)["exceptions"]
    today = date.today()
    exceptions = {
        (item["id"], item["package"])
        for item in raw_exceptions
        if datetime.strptime(item["expires"], "%Y-%m-%d").date() >= today
    }

    findings: list[dict[str, str | bool]] = []
    blocked_misconfig = set(policy["misconfigurations"]["block_severities"])

    for report_path in args.report:
        document = load(report_path)
        for result in document.get("Results") or []:
            target = result.get("Target", "unknown")
            for vulnerability in result.get("Vulnerabilities") or []:
                severity = vulnerability.get("Severity", "UNKNOWN").upper()
                identifier = vulnerability.get("VulnerabilityID", "UNKNOWN")
                package = vulnerability.get("PkgName", "unknown")
                fixed = bool(vulnerability.get("FixedVersion"))
                blocked = (
                    severity == "CRITICAL" and policy["vulnerabilities"]["block_critical"]
                ) or (
                    severity == "HIGH"
                    and (
                        (fixed and policy["vulnerabilities"]["block_high_with_fix"])
                        or (not fixed and policy["vulnerabilities"]["block_unfixed_high"])
                    )
                )
                excepted = (identifier, package) in exceptions
                findings.append(
                    {
                        "type": "vulnerability",
                        "id": identifier,
                        "package": package,
                        "severity": severity,
                        "target": target,
                        "fixed": fixed,
                        "excepted": excepted,
                        "blocked": blocked and not excepted,
                    }
                )

            for issue in result.get("Misconfigurations") or []:
                severity = issue.get("Severity", "UNKNOWN").upper()
                identifier = issue.get("ID", "UNKNOWN")
                excepted = (identifier, target) in exceptions
                findings.append(
                    {
                        "type": "misconfiguration",
                        "id": identifier,
                        "package": target,
                        "severity": severity,
                        "target": target,
                        "fixed": False,
                        "excepted": excepted,
                        "blocked": severity in blocked_misconfig and not excepted,
                    }
                )

            for secret in result.get("Secrets") or []:
                identifier = secret.get("RuleID", "SECRET")
                excepted = (identifier, target) in exceptions
                findings.append(
                    {
                        "type": "secret",
                        "id": identifier,
                        "package": target,
                        "severity": secret.get("Severity", "CRITICAL").upper(),
                        "target": target,
                        "fixed": False,
                        "excepted": excepted,
                        "blocked": policy["secrets"]["block_all"] and not excepted,
                    }
                )

    blocked = [item for item in findings if item["blocked"]]
    lines = [
        "# Security policy evaluation",
        "",
        f"Result: **{'FAIL' if blocked else 'PASS'}**",
        "",
        f"- Total findings: {len(findings)}",
        f"- Blocking findings: {len(blocked)}",
        f"- Active exceptions: {len(exceptions)}",
        "",
        "| Type | ID | Package/target | Severity | Fix available | Excepted | Blocked |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in findings:
        lines.append(
            f"| {item['type']} | `{item['id']}` | `{item['package']}` | "
            f"{item['severity']} | {item['fixed']} | {item['excepted']} | {item['blocked']} |"
        )
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"security-policy-evaluation: {'FAIL' if blocked else 'PASS'}")
    raise SystemExit(1 if blocked else 0)


if __name__ == "__main__":
    main()
