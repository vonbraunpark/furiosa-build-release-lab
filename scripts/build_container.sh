#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_tag="${IMAGE_TAG:-furiosa-build-release-lab:local}"
repository_url="${REPOSITORY_URL:-https://github.com/local/furiosa-build-release-lab}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to build the container image locally." >&2
  exit 1
fi

commit_sha="$(git -C "${project_root}" rev-parse --verify HEAD 2>/dev/null || printf 'unknown')"

docker build \
  --build-arg "REPOSITORY_URL=${repository_url}" \
  --build-arg "VCS_REF=${commit_sha}" \
  --tag "${image_tag}" \
  "${project_root}"

echo "Built ${image_tag} from ${commit_sha}."
