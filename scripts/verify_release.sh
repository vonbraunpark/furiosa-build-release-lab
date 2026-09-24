#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 {artifacts|release|all} OWNER/REPO TAG ASSETS_DIR IMAGE@DIGEST" >&2
  exit 2
}

[[ $# -eq 5 ]] || usage

mode="$1"
repository="$2"
tag="$3"
assets_dir="$4"
image="$5"
signer_workflow="${repository}/.github/workflows/release.yml"

case "${mode}" in
  artifacts|release|all) ;;
  *) usage ;;
esac

command -v gh >/dev/null || {
  echo "gh is required" >&2
  exit 1
}

[[ -d "${assets_dir}" ]] || {
  echo "asset directory not found: ${assets_dir}" >&2
  exit 1
}

verify_artifacts() {
  (
    cd "${assets_dir}"
    sha256sum --check SHA256SUMS
  )

  shopt -s nullglob
  local packages=("${assets_dir}"/*.whl "${assets_dir}"/*.deb)
  local metadata=("${assets_dir}"/*.spdx.json "${assets_dir}"/SHA256SUMS)

  [[ ${#packages[@]} -gt 0 ]] || {
    echo "no wheel or DEB packages found in ${assets_dir}" >&2
    exit 1
  }

  for artifact in "${packages[@]}"; do
    gh attestation verify "${artifact}" \
      --repo "${repository}" \
      --signer-workflow "${signer_workflow}"
    gh attestation verify "${artifact}" \
      --repo "${repository}" \
      --predicate-type https://spdx.dev/Document/v2.3 \
      --signer-workflow "${signer_workflow}"
  done

  for artifact in "${metadata[@]}"; do
    gh attestation verify "${artifact}" \
      --repo "${repository}" \
      --signer-workflow "${signer_workflow}"
  done

  gh attestation verify "oci://${image}" \
    --repo "${repository}" \
    --signer-workflow "${signer_workflow}"
}

verify_release() {
  gh release verify "${tag}" --repo "${repository}"

  shopt -s nullglob
  local assets=("${assets_dir}"/*)
  [[ ${#assets[@]} -gt 0 ]] || {
    echo "no release assets found in ${assets_dir}" >&2
    exit 1
  }

  for asset in "${assets[@]}"; do
    gh release verify-asset "${tag}" "${asset}" --repo "${repository}"
  done
}

if [[ "${mode}" == "artifacts" || "${mode}" == "all" ]]; then
  verify_artifacts
fi

if [[ "${mode}" == "release" || "${mode}" == "all" ]]; then
  verify_release
fi
