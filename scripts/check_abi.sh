#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 OUTPUT_DIR [BASELINE_GIT_REF]" >&2
  exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="$1"
baseline_ref="${2:-}"
work_dir="$(mktemp -d)"
trap 'rm -rf -- "${work_dir}"' EXIT

for command_name in abidiff abidw cmake diff git nm tar; do
  command -v "${command_name}" >/dev/null || {
    echo "${command_name} is required" >&2
    exit 1
  }
done

mkdir -p "${output_dir}"

build_library() {
  local source_dir="$1"
  local build_dir="$2"
  cmake -S "${source_dir}" -B "${build_dir}" \
    -DFASTMATH_BUILD_PYTHON=OFF \
    -DFASTMATH_BUILD_TESTS=OFF \
    -DFASTMATH_BUILD_NATIVE_PACKAGE=ON \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo >&2
  cmake --build "${build_dir}" --target fastmath_shared --parallel 2 >&2
  find "${build_dir}" -type f -name 'libfastmath.so.*.*.*' -print -quit
}

current_library="$(build_library "${project_root}" "${work_dir}/current-build")"
[[ -f "${current_library}" ]] || {
  echo "current shared library was not produced" >&2
  exit 1
}
abidw --out-file "${output_dir}/current.abi.xml" "${current_library}"

if [[ -z "${baseline_ref}" ]]; then
  nm -D --defined-only "${current_library}" |
    awk '$2 == "T" {print $3}' | LC_ALL=C sort >"${output_dir}/current.symbols"
  if ! diff -u \
    "${project_root}/abi/fastmath-0.1.0.symbols" \
    "${output_dir}/current.symbols" >"${output_dir}/abi-diff.txt"; then
    echo "bootstrap ABI symbol baseline: FAIL" >&2
    exit 1
  fi
  cat >"${output_dir}/abi-report.md" <<EOF
# ABI stability report

- Mode: bootstrap symbol baseline
- Baseline: abi/fastmath-0.1.0.symbols
- Result: PASS
- Exported API symbols: 2

After the first release, CI compares the current ELF ABI against the latest
version tag with Libabigail.
EOF
  echo "abi-stability: PASS (bootstrap baseline)"
  exit 0
fi

baseline_source="${work_dir}/baseline-source"
mkdir -p "${baseline_source}"
git -C "${project_root}" archive "${baseline_ref}" | tar -C "${baseline_source}" -xf -
baseline_library="$(build_library "${baseline_source}" "${work_dir}/baseline-build")"
[[ -f "${baseline_library}" ]] || {
  echo "baseline shared library was not produced" >&2
  exit 1
}
abidw --out-file "${output_dir}/baseline.abi.xml" "${baseline_library}"

set +e
abidiff --no-added-syms "${baseline_library}" "${current_library}" \
  >"${output_dir}/abi-diff.txt" 2>&1
status=$?
set -e

result=PASS
if (( status & 1 || status & 2 || status & 8 )); then
  result=FAIL
fi
cat >"${output_dir}/abi-report.md" <<EOF
# ABI stability report

- Mode: Libabigail binary comparison
- Baseline Git ref: ${baseline_ref}
- abidiff status: ${status}
- Backward-compatible result: ${result}

See `abi-diff.txt` and the XML ABI corpora for detailed evidence.
EOF

echo "abi-stability: ${result}"
[[ "${result}" == PASS ]]
