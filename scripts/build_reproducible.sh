#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 OUTPUT_DIR" >&2
  exit 2
}

[[ $# -eq 1 ]] || usage

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="$1"
work_dir="$(mktemp -d)"
trap 'rm -rf -- "${work_dir}"' EXIT

for command_name in cmake cpack ctest python3 sha256sum tar; do
  command -v "${command_name}" >/dev/null || {
    echo "${command_name} is required" >&2
    exit 1
  }
done

mkdir -p "${output_dir}"
if find "${output_dir}" -mindepth 1 -print -quit | grep -q .; then
  echo "output directory must be empty: ${output_dir}" >&2
  exit 1
fi

source_date_epoch="$(git -C "${project_root}" log -1 --pretty=%ct 2>/dev/null || true)"
source_date_epoch="${source_date_epoch:-1700000000}"

copy_source() {
  local destination="$1"
  mkdir -p "${destination}"
  tar \
    --exclude=.git \
    --exclude=.venv \
    --exclude=build \
    --exclude=dist \
    --exclude=wheelhouse \
    --exclude='__pycache__' \
    -C "${project_root}" -cf - . | tar -C "${destination}" -xf -
}

build_once() {
  local label="$1"
  local source_dir="${work_dir}/${label}/source"
  local build_dir="${work_dir}/${label}/build"
  local artifact_dir="${work_dir}/${label}/artifacts"
  local package_dir="${work_dir}/${label}/packages"
  copy_source "${source_dir}"
  mkdir -p "${artifact_dir}" "${package_dir}"

  SOURCE_DATE_EPOCH="${source_date_epoch}" \
  PYTHONHASHSEED=0 TZ=UTC LC_ALL=C.UTF-8 \
    python3 -m build --wheel --no-isolation --outdir "${artifact_dir}" "${source_dir}"

  SOURCE_DATE_EPOCH="${source_date_epoch}" TZ=UTC LC_ALL=C.UTF-8 \
    cmake -S "${source_dir}" -B "${build_dir}" \
      -DFASTMATH_BUILD_PYTHON=OFF \
      -DFASTMATH_BUILD_TESTS=ON \
      -DFASTMATH_BUILD_NATIVE_PACKAGE=ON \
      -DFASTMATH_REPRODUCIBLE=ON \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/usr
  SOURCE_DATE_EPOCH="${source_date_epoch}" cmake --build "${build_dir}" --parallel 2
  ctest --test-dir "${build_dir}" --output-on-failure
  SOURCE_DATE_EPOCH="${source_date_epoch}" TZ=UTC LC_ALL=C.UTF-8 \
    cpack --config "${build_dir}/CPackConfig.cmake" -B "${package_dir}"
  cp "${package_dir}"/*.deb "${artifact_dir}/"
}

build_once build-a
build_once build-b
cp -a "${work_dir}/build-a/artifacts" "${output_dir}/build-a"
cp -a "${work_dir}/build-b/artifacts" "${output_dir}/build-b"

set +e
python3 "${project_root}/scripts/compare_reproducible_builds.py" \
  "${output_dir}/build-a" "${output_dir}/build-b" \
  --json-report "${output_dir}/reproducibility.json" \
  --markdown-report "${output_dir}/reproducibility.md"
comparison_status=$?
set -e

if [[ ${comparison_status} -ne 0 ]] && command -v diffoscope >/dev/null; then
  diffoscope \
    --text "${output_dir}/diffoscope.txt" \
    --html "${output_dir}/diffoscope.html" \
    "${output_dir}/build-a" "${output_dir}/build-b" || true
fi

exit "${comparison_status}"
