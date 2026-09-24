# Release retention and rollback policy

## Protected evidence

Published immutable releases are permanent audit records. Their Git tag,
wheel, DEB, SBOM, checksum file, release attestation, and artifact attestations
must not be replaced or reused. A withdrawn version remains available as
evidence and is superseded by a new patch release.

Release container digests are retained indefinitely. Cleanup automation must
never select a digest referenced by an immutable release. Only untagged,
non-release development images older than 30 days may be proposed for deletion,
and deletion requires a separate reviewed operation.

## Retention matrix

| Record | Retention | Reason |
| --- | ---: | --- |
| Immutable GitHub Release assets | Indefinite | Recovery source and audit evidence |
| Release Git tags | Never reuse | A tag identifies exactly one released commit |
| Release OCI digests and attestations | Indefinite | Rollback and provenance verification |
| Wheel/DEB workflow handoff artifacts | 14 days | Temporary transfer; duplicated in the release |
| Compatibility, ABI, and reproducibility reports | 30 days | Engineering review evidence |
| Vulnerability and policy reports | 30 days | Security review evidence |
| Disaster-recovery drill reports | 30 days | Recent operational evidence |
| Rollback execution records | 90 days | Change-control and incident evidence |
| Untagged non-release images | Review after 30 days | Storage control without risking releases |

The machine-readable source is `.github/retention-policy.json`. The retention
audit fails when workflow settings drift from it. Repository or organization
Actions retention settings must be at least 90 days so they do not shorten the
rollback-record policy.

## Rollback rules

1. Never move, recreate, or reuse an immutable release tag.
2. Never alter an immutable release asset or its checksum.
3. Select a known-good digest recorded in an already verified release.
4. Run rollback in `plan` mode first.
5. Require approval through the protected `release-rollback` environment.
6. In `apply` mode, move only floating OCI aliases such as `latest`, `1`, or
   `1.2`; the release digest and version tag remain unchanged.
7. Publish the correction as a new patch version after the incident is stable.

Deleting a release or package is not a rollback mechanism. Any exceptional
deletion requires an independently reviewed security or legal decision outside
these workflows.
