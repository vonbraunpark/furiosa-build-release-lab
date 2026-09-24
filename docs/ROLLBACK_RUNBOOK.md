# Immutable release rollback and recovery runbook

## Initial response

1. Stop deployment promotion and identify the affected version, commit, and
   OCI digest.
2. Preserve logs and do not delete the published release, tag, image, SBOM, or
   attestations.
3. Choose the most recent known-good immutable release.
4. Verify its release, assets, checksums, SBOM attestations, and OCI provenance.

## Container alias rollback

Open **Actions → Container Alias Rollback → Run workflow**.

1. Select `plan`.
2. Enter the known-good release tag and the exact digest recorded in its
   release notes.
3. Enter only floating aliases, for example `latest 1 1.2`.
4. Review the verification output and proposed alias changes.
5. Run again with `apply`, enter `ROLLBACK <tag>` as confirmation, and approve
   the protected `release-rollback` environment deployment.
6. Confirm every alias resolves to the requested digest and archive the
   generated rollback record.

This operation does not modify the release, its version tag, or its digest.
Wheel and DEB consumers must pin or reinstall the selected known-good immutable
release; existing files are never overwritten.

## Disaster-recovery drill

The monthly workflow selects the latest stable release unless a tag is supplied
manually. It performs the following recovery path from public release records:

1. Download every release asset into a clean temporary directory.
2. Verify release immutability and each local asset against the release.
3. Check `SHA256SUMS`.
4. Verify package provenance, SPDX SBOM attestations, and container provenance.
5. Validate the SPDX 2.3 document structure.
6. Pull the container by the digest preserved in release notes.
7. Run both container smoke tests and save a dated report.

## Forward recovery

Rollback stabilizes consumers but does not repair the defective version.
Create a fix on the normal development branch, increment the patch version,
update `CHANGELOG.md`, run the complete release pipeline, and publish a new
immutable release. Record the affected and replacement versions in the incident
report.

## Failure handling

- Missing release or asset: stop; investigate retention-policy violation.
- Checksum or release verification failure: treat as possible tampering.
- Missing attestation: stop promotion and inspect the original workflow run.
- Missing OCI digest: do not substitute a mutable tag; restore from an approved
  registry backup or rebuild as a new version.
- Smoke-test failure: keep aliases on the last verified digest and escalate.
