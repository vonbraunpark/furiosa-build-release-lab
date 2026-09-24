#!/usr/bin/env bash
set -euo pipefail

image_tag="${IMAGE_TAG:-furiosa-build-release-lab:local}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to verify the container image locally." >&2
  exit 1
fi

version_output="$(docker run --rm "${image_tag}" --version)"
self_test_output="$(docker run --rm "${image_tag}")"
configured_user="$(docker image inspect --format '{{.Config.User}}' "${image_tag}")"

[[ "${version_output}" == fastmath-cli\ * ]]
[[ "${self_test_output}" == "fastmath self-test passed: add=30 dot_product=32" ]]
[[ "${configured_user}" == "65532:65532" ]]

echo "${version_output}"
echo "${self_test_output}"
echo "Container verification passed as non-root user ${configured_user}."
