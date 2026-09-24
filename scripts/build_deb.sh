#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${project_root}/build/deb"
package_dir="${project_root}/dist/deb"

cmake -S "${project_root}" -B "${build_dir}" \
  -DFASTMATH_BUILD_PYTHON=OFF \
  -DFASTMATH_BUILD_TESTS=ON \
  -DFASTMATH_BUILD_NATIVE_PACKAGE=ON \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr
cmake --build "${build_dir}" --parallel
ctest --test-dir "${build_dir}" --output-on-failure

mkdir -p "${package_dir}"
find "${package_dir}" -maxdepth 1 -name '*.deb' -delete
cpack --config "${build_dir}/CPackConfig.cmake" -B "${package_dir}"

find "${package_dir}" -maxdepth 1 -name '*.deb' -print
