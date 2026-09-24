#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${PYTHON:-python3}"
wheel_path="$(find "${project_root}/dist" -maxdepth 1 -name '*.whl' -print | sort | tail -n 1)"

if [[ -z "${wheel_path}" ]]; then
  echo "No wheel found under ${project_root}/dist" >&2
  exit 1
fi

verify_dir="$(mktemp -d)"
trap 'rm -rf "${verify_dir}"' EXIT

"${python_bin}" -m venv "${verify_dir}/venv"
"${verify_dir}/venv/bin/python" -m pip install --quiet "${wheel_path}"
cd "${verify_dir}"
"${verify_dir}/venv/bin/python" -m unittest discover \
  -s "${project_root}/tests/python" -p 'test_*.py' -v

