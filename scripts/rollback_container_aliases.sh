#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 {plan|apply} OWNER/REPO RELEASE_TAG IMAGE SHA256_DIGEST ALIAS..." >&2
  exit 2
}

[[ $# -ge 6 ]] || usage

mode="$1"
repository="$2"
release_tag="$3"
image="$4"
target_digest="$5"
shift 5
aliases=("$@")

[[ "${mode}" == "plan" || "${mode}" == "apply" ]] || usage
[[ "${repository}" =~ ^[^/]+/[^/]+$ ]] || usage
[[ "${release_tag}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.-]+)?$ ]] || usage
[[ "${target_digest}" =~ ^sha256:[0-9a-f]{64}$ ]] || usage
[[ "${image}" != *@* && "${image}" != *:* ]] || {
  echo "IMAGE must not contain a tag or digest: ${image}" >&2
  exit 2
}

for alias in "${aliases[@]}"; do
  [[ "${alias}" =~ ^(latest|[0-9]+|[0-9]+\.[0-9]+)$ ]] || {
    echo "refusing non-floating alias: ${alias}" >&2
    exit 2
  }
done

for command_name in docker gh; do
  command -v "${command_name}" >/dev/null || {
    echo "${command_name} is required" >&2
    exit 1
  }
done

gh release verify "${release_tag}" --repo "${repository}"
release_body="$(gh release view "${release_tag}" --repo "${repository}" --json body --jq .body)"
expected_reference="${image}@${target_digest}"
grep -Fq "Immutable digest: \`${expected_reference}\`" <<<"${release_body}" || {
  echo "target digest is not recorded by immutable release ${release_tag}" >&2
  exit 1
}

gh attestation verify "oci://${expected_reference}" \
  --repo "${repository}" \
  --signer-workflow "${repository}/.github/workflows/release.yml"
docker buildx imagetools inspect "${expected_reference}" >/dev/null

echo "mode=${mode}"
echo "release=${release_tag}"
echo "verified-target=${expected_reference}"

for alias in "${aliases[@]}"; do
  destination="${image}:${alias}"
  if [[ "${mode}" == "plan" ]]; then
    echo "would-retarget=${destination} -> ${target_digest}"
    continue
  fi

  docker buildx imagetools create --tag "${destination}" "${expected_reference}"
  resolved="$(docker buildx imagetools inspect "${destination}" --format '{{.Manifest.Digest}}')"
  [[ "${resolved}" == "${target_digest}" ]] || {
    echo "post-rollback digest mismatch for ${destination}: ${resolved}" >&2
    exit 1
  }
  echo "retargeted=${destination} -> ${resolved}"
done
