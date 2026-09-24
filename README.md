# furiosa-build-release-lab

A production-oriented build and release lab demonstrating a C++17 library,
CMake builds, pybind11 Python bindings, native Python wheel packaging, and an
installable Ubuntu `.deb` development package plus a versioned OCI container.

## Implemented pipeline

```text
C++ library -> CMake -> pybind11 extension
      |
      +-> pybind11 extension -> Python 3.10-3.13 CI matrix
      |                              |
      |                              +-> cibuildwheel -> manylinux_2_28 wheels
      |                                                    |
      |                                                    +-> installed-wheel tests
      |                                                    +-> GitHub artifact upload
      |
      +-> versioned libfastmath.so -> CPack -> Ubuntu .deb
                                             |
                                             +-> clean-container installation
                                             +-> external CMake consumer test
                                             +-> removal verification
                                             +-> GitHub artifact upload
      |
      +-> fastmath-cli -> multi-stage Docker build -> runtime smoke test
                                                   |
                                                   +-> SemVer tags
                                                   +-> immutable SHA tag
                                                   +-> GHCR publication
      |
      +-> v* tag -> version + CHANGELOG gate
                         |
                         +-> successful Security gate for exact commit
                         +-> wheels + DEB -> SPDX SBOM + SHA256SUMS
                         +-> tested container -> GHCR digest + attestations
                         +-> draft GitHub Release -> publish -> verify
                         +-> retain -> recover -> rollback floating aliases
```

The sample `fastmath` library exposes:

- `add(int, int)`
- `dot_product(vector<double>, vector<double>)`

## Prerequisites

- Python 3.10 or newer
- A C++17 compiler
- CMake 3.20 or newer

The Python build dependencies are declared in `pyproject.toml` and are installed
in an isolated environment by the build frontend.

## Build and test the C++ library

```bash
python -m pip install cmake
./scripts/build_local.sh
```

## Build the wheel

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip build
./scripts/build_wheel.sh
```

The wheel is written to `dist/`.

## Verify the packaged artifact

The verification script installs the wheel into a fresh virtual environment
and runs the Python tests outside the source tree. This catches missing native
extensions and accidental imports from local sources.

```bash
./scripts/verify_wheel.sh
```

## Build portable manylinux wheels

The manylinux build targets CPython 3.10 through 3.13 on x86_64. Each wheel is
built inside a `manylinux_2_28` container, repaired with `auditwheel`, installed
in an isolated test environment, and exercised by the Python test suite.

Local execution requires Docker:

```bash
python -m pip install cibuildwheel==4.2.1
./scripts/build_manylinux_wheels.sh
```

Expected artifacts:

```text
wheelhouse/
├── furiosa_build_release_lab-0.1.0-cp310-...-manylinux_2_28_x86_64.whl
├── furiosa_build_release_lab-0.1.0-cp311-...-manylinux_2_28_x86_64.whl
├── furiosa_build_release_lab-0.1.0-cp312-...-manylinux_2_28_x86_64.whl
└── furiosa_build_release_lab-0.1.0-cp313-...-manylinux_2_28_x86_64.whl
```

## Build the Ubuntu DEB package

The native package contains the versioned shared library, public C++ header,
and CMake package metadata. It deliberately does not contain the Python
extension; Python distribution remains the responsibility of the wheels. The
`FASTMATH_BUILD_NATIVE_PACKAGE` option keeps these artifact graphs isolated.

Required Ubuntu packages are `build-essential`, `cmake`, and `dpkg-dev`.

```bash
./scripts/build_deb.sh
```

Expected artifact:

```text
dist/deb/fastmath_0.1.0_amd64.deb
```

Verify the package by installing it, configuring and compiling an independent
CMake consumer, running that executable, and removing the package:

```bash
./scripts/verify_deb.sh
```

After installation, a downstream CMake project can use the library without
referencing this repository:

```cmake
find_package(fastmath 0.1 CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE fastmath::fastmath)
```

The package installs these public interfaces under the platform's standard
GNU install directories:

```text
/usr/include/fastmath/fastmath.hpp
/usr/lib/<multiarch>/libfastmath.so -> libfastmath.so.0
/usr/lib/<multiarch>/libfastmath.so.0 -> libfastmath.so.0.1.0
/usr/lib/<multiarch>/cmake/fastmath/
```

## Build and verify the container image

The multi-stage `Dockerfile` compiles and tests `fastmath-cli` in an Ubuntu
24.04 builder, then copies only the executable into a separate runtime image.
The resulting container runs as numeric non-root user `65532:65532`.

```bash
./scripts/build_container.sh
./scripts/verify_container.sh
```

Override the default local image name when needed:

```bash
IMAGE_TAG=furiosa-build-release-lab:dev ./scripts/build_container.sh
IMAGE_TAG=furiosa-build-release-lab:dev ./scripts/verify_container.sh
```

Expected behavior:

```text
$ docker run --rm furiosa-build-release-lab:local --version
fastmath-cli 0.1.0

$ docker run --rm furiosa-build-release-lab:local
fastmath self-test passed: add=30 dot_product=32
```

## Container version tags

`.github/workflows/container.yml` builds and loads a local test image first.
Only an image that passes the CLI smoke test and non-root-user check can be
published to GitHub Container Registry.

| Git event | Published tags |
| --- | --- |
| `main` push or manual run | `sha-<12-character-commit>` |
| stable tag `v1.2.3` | `1.2.3`, `1.2`, `1`, `latest`, `sha-<commit>` |
| prerelease tag `v1.2.3-rc.1` | `1.2.3-rc.1`, `sha-<commit>` |
| pull request | no publication; build and test only |

The human-readable SemVer tags provide release discovery, while the SHA tag
provides immutable source traceability. `latest`, major, and minor aliases are
not assigned to prereleases. Release tags are validated against the numeric
version in `CMakeLists.txt` before publication. For SemVer major zero releases,
the unstable `0` alias is intentionally omitted while `0.x` remains available.

Example after a `v0.1.0` tag push:

```text
ghcr.io/<owner>/furiosa-build-release-lab:0.1.0
ghcr.io/<owner>/furiosa-build-release-lab:0.1
ghcr.io/<owner>/furiosa-build-release-lab:latest
ghcr.io/<owner>/furiosa-build-release-lab:sha-<12-character-commit>
```

## Unified tag-driven release

Only `.github/workflows/release.yml` handles release tags. The individual
wheel, DEB, and container workflows retain their validation and manual-run
roles but do not independently react to tags, preventing duplicate releases.

Before any release build starts, the workflow verifies that:

- the tag uses `vMAJOR.MINOR.PATCH` or prerelease SemVer syntax;
- the numeric tag version matches both `CMakeLists.txt` and `pyproject.toml`;
- `CHANGELOG.md` contains a matching version section.

Before pushing the first release tag, enable **Settings → Releases → Enable
release immutability** in the GitHub repository. GitHub creates a signed release
attestation only for immutable releases; the final verification step fails if
the setting is missing or if any published asset differs from its attestation.

The release dependency graph is:

```text
validate version + CHANGELOG
        |
        +-------------------+
        |                   |
        v                   v
manylinux wheels        Ubuntu DEB
        |                   |
        +---------+---------+
                  |
                  v
        Docker build, test, push
                  |
                  v
      verify 4 wheels + 1 DEB
                  |
       generate SPDX JSON SBOM
                  |
     attest packages + container
                  |
          generate SHA256SUMS
                  |
                  v
       draft GitHub Release
                  |
        upload verified assets
                  |
                  v
       publish + verify release
```

The first release is triggered with:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Expected GitHub Release assets:

```text
furiosa_build_release_lab-0.1.0-cp310-...-manylinux_2_28_x86_64.whl
furiosa_build_release_lab-0.1.0-cp311-...-manylinux_2_28_x86_64.whl
furiosa_build_release_lab-0.1.0-cp312-...-manylinux_2_28_x86_64.whl
furiosa_build_release_lab-0.1.0-cp313-...-manylinux_2_28_x86_64.whl
fastmath_0.1.0_amd64.deb
furiosa-build-release-lab-0.1.0.spdx.json
SHA256SUMS
```

Release notes are taken from the matching CHANGELOG section and include both
the readable container version and its immutable registry digest. Stable
releases become `latest`; prereleases remain explicitly marked as prereleases.

## Supply-chain verification

Each wheel and DEB receives its build-provenance attestation in the job that
actually builds it. The pipeline then produces one SPDX 2.3 JSON SBOM covering
the package release directory and binds every package to it with a separate
SBOM attestation. `SHA256SUMS` and the SBOM itself also receive provenance
attestations.

The published OCI image includes BuildKit `mode=max` provenance and an SBOM in
GHCR. A GitHub-signed provenance attestation is also attached to the image by
digest. The workflow verifies the OCI attestation immediately after publishing
the image, then re-verifies all package attestations before creating a release.

After the draft becomes public, the pipeline verifies the immutable GitHub
Release attestation and every uploaded asset. Artifact verification also pins
the expected signer to this repository's `.github/workflows/release.yml`. A
consumer can repeat the checks:

```bash
gh auth login

# Download the release and check file digests.
gh release download v0.1.0 --repo OWNER/furiosa-build-release-lab --dir release-assets
(cd release-assets && sha256sum --check SHA256SUMS)

# Verify provenance and the SBOM claim for a downloaded package.
gh attestation verify release-assets/PACKAGE.whl \
  --repo OWNER/furiosa-build-release-lab
gh attestation verify release-assets/PACKAGE.whl \
  --repo OWNER/furiosa-build-release-lab \
  --predicate-type https://spdx.dev/Document/v2.3

# Verify the image by immutable digest and the GitHub Release itself.
gh attestation verify \
  oci://ghcr.io/OWNER/furiosa-build-release-lab@sha256:DIGEST \
  --repo OWNER/furiosa-build-release-lab
gh release verify v0.1.0 --repo OWNER/furiosa-build-release-lab
gh release verify-asset v0.1.0 release-assets/PACKAGE.whl \
  --repo OWNER/furiosa-build-release-lab
```

The repository script runs the same gates in automation:

```bash
./scripts/verify_release.sh all \
  OWNER/furiosa-build-release-lab \
  v0.1.0 \
  release-assets \
  ghcr.io/OWNER/furiosa-build-release-lab@sha256:DIGEST
```

## Rollback, retention, and disaster recovery

An immutable release is retained as evidence instead of being edited or
replaced. Rollback therefore means selecting a previously verified release
digest and moving only mutable container aliases such as `latest`, `1`, and
`1.2`. Version tags, digests, wheel and DEB files remain unchanged.

The manual `Container Alias Rollback` workflow has two stages:

- `plan` verifies the immutable release, recorded digest, provenance, and
  registry manifest without changing a tag;
- `apply` requires the exact `ROLLBACK <tag>` confirmation and approval from
  the protected `release-rollback` environment before retargeting aliases.

Create that environment in **Settings → Environments → New environment**, add
required reviewers, and prevent self-review where the repository plan supports
it. The workflow saves a rollback record for 90 days.

`Release Disaster Recovery Drill` runs monthly and can also target a specified
release manually. It downloads a release into a clean directory, verifies all
integrity and supply-chain evidence, validates the SPDX document, pulls the
container by its recorded digest, and runs the smoke tests. Reports are retained
for 30 days.

Retention values are defined in `.github/retention-policy.json` and enforced by
`Release Retention Audit`. Operational procedures are documented in
`docs/RELEASE_POLICY.md` and `docs/ROLLBACK_RUNBOOK.md`.

## Compatibility, ABI, and reproducibility

`Multi-environment Compatibility` tests the native library on Ubuntu 22.04 and
24.04 with both GCC and Clang. Every native job installs the CMake package and
builds an independent consumer against that installation. A separate matrix
builds, installs, and tests the extension with CPython 3.10 through 3.13.

The shared library uses hidden visibility by default and explicitly exports
only its supported API. Before the first release, the ABI workflow checks the
approved `0.1.0` symbol baseline. After a version tag exists, it builds the
latest tag and current source and uses Libabigail to reject backward-
incompatible ELF ABI changes.

`Reproducible Packages` performs two isolated builds with different absolute
paths. It fixes the source timestamp and relevant process state, removes source
and build paths from compiler output, and compares Wheel and DEB SHA-256 values.
Any difference fails the workflow and produces diffoscope text and HTML
evidence. See `docs/COMPATIBILITY.md` and `docs/REPRODUCIBLE_BUILDS.md` for the
exact support and guarantee boundaries.

## Security enforcement

`Security Enforcement` is a required aggregate gate covering C++ and Python
CodeQL analysis, pull-request dependency and SPDX-license review, pip-audit,
Trivy repository scanning, and a locally built container scan. Scanner JSON and
human-readable policy reports are retained for 30 days.

The repository policy blocks every Critical vulnerability, every fixable High
vulnerability, High/Critical misconfigurations, and detected secrets. Exceptions
must identify an owner and reason and expire within 30 days. The Release
workflow queries GitHub Checks and refuses to build a tag unless the exact
commit already passed `Security gate`.

The Trivy action is pinned to a reviewed full commit SHA. Dependabot checks
GitHub Actions and Python dependencies weekly. See `docs/SECURITY.md` and the
machine-readable files under `security/` for thresholds, license allowlist, and
the exception process.

## Final public release rehearsal

After publishing the repository and completing the first immutable release,
run `Final Public Release Rehearsal` with its release tag. It rehydrates the
release on a clean GitHub-hosted runner, repeats integrity, attestation, SBOM,
and container runtime verification, confirms the release commit's security
gate, and generates Markdown plus JSON portfolio evidence from live GitHub API
data. The checked-in report remains explicitly pending until that run succeeds.

The complete publication sequence, repository control settings, acceptance
criteria, and portfolio presentation are documented in
`docs/PUBLICATION_RUNBOOK.md`, `docs/PORTFOLIO.md`, and
`docs/FINAL_RELEASE_REPORT.md`.

## GitHub Actions

Thirteen workflows separate validation, distribution, security, compatibility,
and recovery:

- `.github/workflows/ci.yml`: C++ tests plus a Python 3.10-3.13 matrix that
  builds, installs, and tests a native wheel on every push and pull request.
- `.github/workflows/wheels.yml`: manually triggered `cibuildwheel` validation
  that produces tested manylinux wheels as a workflow artifact.
- `.github/workflows/deb.yml`: builds in a clean Ubuntu 24.04 container, runs
  the native tests, installs the generated package, validates it through an
  external CMake consumer, removes it, and uploads the `.deb` artifact.
- `.github/workflows/container.yml`: builds a multi-stage image with Buildx,
  tests it before publication, generates SemVer and SHA tags, and publishes
  non-PR builds to GHCR using `GITHUB_TOKEN`.
- `.github/workflows/release.yml`: exclusively handles `v*` tags and publishes
  wheels, DEB, SPDX SBOM, checksums, attested GHCR image, CHANGELOG-derived
  notes, and a verified immutable GitHub Release through one gated pipeline.
- `.github/workflows/retention-audit.yml`: prevents retention settings from
  drifting away from the machine-readable policy.
- `.github/workflows/disaster-recovery.yml`: rehydrates and verifies the latest
  stable or manually selected release every month.
- `.github/workflows/rollback.yml`: performs approved plan/apply rollback of
  floating GHCR aliases to a verified historical digest.
- `.github/workflows/compatibility.yml`: tests the OS/compiler/Python support
  matrix and the installed external CMake consumer.
- `.github/workflows/abi.yml`: enforces the bootstrap symbol baseline and then
  compares releases with Libabigail.
- `.github/workflows/reproducibility.yml`: rebuilds Wheel and DEB packages twice
  and retains hash and diffoscope evidence.
- `.github/workflows/security.yml`: aggregates CodeQL, dependency/license,
  Python, source, secret, IaC, and container security controls into one gate.
- `.github/workflows/final-rehearsal.yml`: independently rehydrates a public
  immutable release and emits live, linkable portfolio evidence.

The manylinux job has read-only repository permissions and does not publish to
PyPI or create a GitHub Release. Publishing remains a separate release-stage
responsibility.

Expected usage after installation:

```python
import fastmath

assert fastmath.add(10, 20) == 30
assert fastmath.dot_product([1.0, 2.0], [3.0, 4.0]) == 11.0
```

## Repository layout

```text
cpp/                 C++ headers and implementation
python/              pybind11 binding code
src/fastmath/         Python package facade
tests/cpp/            Native unit test
tests/python/         Installed-package tests
tests/consumer/       Independent installed-DEB CMake consumer
apps/                 Container smoke-test CLI
cmake/                Installed CMake package configuration template
scripts/              Reproducible local build and verification commands
docs/                 Release policy and operational recovery runbook
abi/                  Approved bootstrap ABI export baseline
security/             Machine-readable thresholds and expiring exceptions
.github/workflows/    CI, packaging, container, and unified release workflows
Dockerfile            Multi-stage non-root container image
.dockerignore         Minimal, reproducible Docker build context
CHANGELOG.md           Versioned human-readable release history
CMakeLists.txt        Native build graph
pyproject.toml        Python build and package metadata
```

## Milestone status

Milestones 1-9 are implemented and locally validated. Milestone 10 adds the
public deployment runbook, independent end-to-end rehearsal, and evidence
generator. Its checked-in status remains `PENDING LIVE GITHUB REHEARSAL` until
the repository is public and the generated report contains real GitHub URLs.
