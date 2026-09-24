#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${project_root}/build/cpp"

cmake -S "${project_root}" -B "${build_dir}" \
  -DFASTMATH_BUILD_PYTHON=OFF \
  -DFASTMATH_BUILD_TESTS=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${build_dir}" --parallel
ctest --test-dir "${build_dir}" --output-on-failure

