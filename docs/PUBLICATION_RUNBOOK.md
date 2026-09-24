# Public deployment and final rehearsal

This runbook turns the repository into public, auditable evidence. Do not mark
the milestone complete until every acceptance check at the end is supported by
a public URL.

## 1. Local publication preflight

```bash
python3 scripts/preflight_publication.py
python3 scripts/validate_version.py --tag v0.1.0 --changelog CHANGELOG.md
python3 scripts/validate_security_policy.py
python3 scripts/audit_retention_policy.py
./scripts/build_local.sh
```

Confirm that the source tree contains no credentials, private keys, internal
hostnames, proprietary data, or generated build directories. This repository
is designed to use only `GITHUB_TOKEN`; no long-lived publishing token belongs
in the source tree.

## 2. Publish the source repository

Create an empty public repository named `furiosa-build-release-lab`, then push
the reviewed source to its `main` branch. With GitHub CLI this is:

```bash
git init -b main
git add .
git commit -m "Complete production release engineering lab"
gh repo create OWNER/furiosa-build-release-lab --public --source=. --remote=origin --push
```

The Git author name and email must be configured before committing. Never copy
credentials into the repository to make this command work.

## 3. Configure repository controls

1. Enable **Settings → Releases → Release immutability**.
2. Create the `release-rollback` environment, add a required reviewer, and
   prevent self-review when the repository plan supports it.
3. Allow GitHub Actions to create attestations and publish packages using the
   scoped `GITHUB_TOKEN` permissions already declared in each workflow.
4. After the first `main` workflow run creates its check names, add a branch
   ruleset for `main` that requires a pull request and the following checks:
   `C++ build and test`, every supported Python package test,
   `Compatibility report`, `ABI compatibility`, `Reproducible packages`, and
   `Security gate`.
5. Keep force pushes and branch deletion disabled for `main`.

Required checks must exist in the repository before they can be selected in a
ruleset. Use the exact check names emitted by Actions rather than guessing.

## 4. Rehearse the unified release

Wait for the `main` commit's workflows, especially `Security gate`, to pass.
Create the release tag only on that exact commit:

```bash
git switch main
git pull --ff-only
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
gh run list --workflow release.yml --limit 1
gh run watch RUN_ID --exit-status
```

The release workflow must publish four manylinux wheels, one Ubuntu DEB, an
SPDX JSON SBOM, `SHA256SUMS`, an attested GHCR image, and a GitHub Release. A
failed tag run is evidence of a failed rehearsal; fix forward with a new
version. Never delete and reuse a published release tag.

## 5. Run the independent final rehearsal

```bash
gh workflow run final-rehearsal.yml --ref main -f release_tag=v0.1.0
gh run list --workflow final-rehearsal.yml --limit 1
gh run watch RUN_ID --exit-status
gh run download RUN_ID --name final-release-evidence-v0.1.0-RUN_ID
```

This workflow starts from the public release, not from handoff artifacts. It
verifies release and asset attestations, checks SHA-256 digests and the SPDX
document, pulls the container by digest, runs its smoke tests, verifies the
successful security gate on the tag commit, and creates Markdown plus JSON
portfolio evidence.

## Acceptance checks

- The repository URL is public and renders the README and license.
- All required `main` checks pass and the ruleset is active.
- `v0.1.0` is a published immutable release with the expected seven asset
  classes and recorded GHCR digest.
- `gh release verify v0.1.0 --repo OWNER/furiosa-build-release-lab` succeeds.
- The final rehearsal workflow succeeds from a clean GitHub-hosted runner.
- `FINAL_RELEASE_REPORT.md` and `portfolio-evidence.json` are downloaded from
  the final rehearsal run and their public evidence links are valid.
- The manual rollback workflow's plan stage succeeds; do not execute `apply`
  merely to create portfolio evidence.
