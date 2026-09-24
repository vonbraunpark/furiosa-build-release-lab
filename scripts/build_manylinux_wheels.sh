#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON:-python3}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to build manylinux wheels locally." >&2
  exit 1
fi

cd "${project_root}"
"${python_bin}" -m cibuildwheel --platform linux --output-dir wheelhouse

