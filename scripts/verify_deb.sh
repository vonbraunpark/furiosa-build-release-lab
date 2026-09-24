#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
package_path="$(find "${project_root}/dist/deb" -maxdepth 1 -name 'fastmath_*.deb' -print | sort | tail -n 1)"
consumer_build="$(mktemp -d)"
package_name="fastmath"

if [[ -z "${package_path}" ]]; then
  echo "No fastmath .deb found under ${project_root}/dist/deb" >&2
  exit 1
fi

if [[ "$(id -u)" -eq 0 ]]; then
  elevate=()
elif command -v sudo >/dev/null 2>&1; then
  elevate=(sudo)
else
  echo "Root privileges or sudo are required for package verification." >&2
  exit 1
fi

cleanup() {
  "${elevate[@]}" dpkg --remove "${package_name}" >/dev/null 2>&1 || true
  rm -rf "${consumer_build}"
}
trap cleanup EXIT

"${elevate[@]}" dpkg --install "${package_path}"
dpkg-query --show --showformat='${Package} ${Version} ${Architecture}\n' "${package_name}"
dpkg-query --listfiles "${package_name}"

test -f /usr/include/fastmath/fastmath.hpp
test -f /usr/lib/x86_64-linux-gnu/libfastmath.so.0.1.0 || test -f /usr/lib/libfastmath.so.0.1.0

cmake -S "${project_root}/tests/consumer" -B "${consumer_build}" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${consumer_build}" --parallel
"${consumer_build}/fastmath_consumer"

"${elevate[@]}" dpkg --remove "${package_name}"
package_state="$(dpkg-query --show --showformat='${db:Status-Abbrev}' "${package_name}" 2>/dev/null || true)"
if [[ "${package_state}" == ii* ]]; then
  echo "Package is still installed after removal." >&2
  exit 1
fi

trap - EXIT
rm -rf "${consumer_build}"
echo "DEB install, consumer build, runtime, and removal verification passed."
