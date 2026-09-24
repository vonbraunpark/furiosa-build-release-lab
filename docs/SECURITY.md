# Security policy and enforcement

## Required controls

Every pull request and `main` commit runs the `Security Enforcement` workflow:

| Control | Scope | Blocking behavior |
| --- | --- | --- |
| CodeQL | C++ and Python source | CodeQL analysis must complete successfully |
| Dependency review | New PR dependencies | High/Critical vulnerability or unapproved license fails |
| pip-audit | Resolved Python project dependencies | Any known dependency vulnerability fails |
| Trivy filesystem | Dependencies, IaC, embedded secrets | Repository policy is evaluated |
| Trivy container | OS and library packages, secrets | Repository policy is evaluated |
| Policy validation | Policy and exception files | Invalid or expired exception fails |

The final `Security gate` job succeeds only when every control succeeds. The
release workflow queries the commit's check runs and refuses to build release
artifacts unless that exact commit already has a successful security gate.

## Vulnerability thresholds

- Critical vulnerabilities are blocked even when no fix is available.
- High vulnerabilities are blocked when a fixed version exists.
- Unfixed High findings are reported for triage but do not block by default.
- High and Critical infrastructure misconfigurations are blocked.
- Every detected secret is blocked.

The canonical settings are in `security/policy.json`.

## License policy

Pull requests may introduce dependencies only under the SPDX licenses listed
in `security/policy.json`. The list permits common permissive licenses and
MPL-2.0. Copyleft licenses not present in the allowlist fail dependency review
instead of relying on an incomplete denylist.

Dependency Review is available for public repositories and for eligible private
repositories with GitHub Advanced Security. If it is unavailable, do not mark
the check optional; either make the portfolio repository public or configure
the required GitHub security entitlement.

## Exceptions

Exceptions belong in `security/exceptions.json` and require:

- vulnerability or rule ID;
- exact package or target;
- accountable owner;
- technical justification;
- creation and expiration dates.

An exception can last at most 30 days. Expired, future-dated, duplicated, or
incomplete exceptions fail before scanners run. Example:

```json
{
  "id": "CVE-2099-1234",
  "package": "example-package",
  "owner": "release-engineering",
  "reason": "Not reachable in the packaged runtime; upgrade tracked separately.",
  "created": "2099-01-01",
  "expires": "2099-01-15"
}
```

Never use an exception to suppress a detected secret.

## Supply-chain maintenance

The Trivy action is pinned to a reviewed full commit SHA. GitHub-maintained
actions use supported major versions, and Dependabot opens weekly update pull
requests for Actions and Python dependencies. Updates must pass the same
security, compatibility, ABI, and reproducibility checks before merge.
