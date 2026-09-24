#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 OWNER/REPO RELEASE_TAG REPORT_FILE" >&2
  exit 2
}

[[ $# -eq 3 ]] || usage

repository="$1"
tag="$2"
report_file="$3"
work_dir="$(mktemp -d)"
assets_dir="${work_dir}/release-assets"
trap 'rm -rf -- "${work_dir}"' EXIT

for command_name in docker gh python3 sha256sum; do
  command -v "${command_name}" >/dev/null || {
    echo "${command_name} is required" >&2
    exit 1
  }
done

[[ "${repository}" =~ ^[^/]+/[^/]+$ ]] || usage
[[ "${tag}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.-]+)?$ ]] || usage

release_body="$(gh release view "${tag}" --repo "${repository}" --json body --jq .body)"
image_reference="$(
  printf '%s\n' "${release_body}" |
    sed -n 's/.*Immutable digest: `\([^`]*@sha256:[0-9a-f]\{64\}\)`.*/\1/p' |
    head -n 1
)"
[[ -n "${image_reference}" ]] || {
  echo "release notes do not contain an immutable container digest" >&2
  exit 1
}

mkdir -p "${assets_dir}"
gh release download "${tag}" --repo "${repository}" --dir "${assets_dir}"
"$(dirname "$0")/verify_release.sh" all \
  "${repository}" "${tag}" "${assets_dir}" "${image_reference}"

python3 - "${assets_dir}" <<'PY'
import json
import sys
from pathlib import Path

assets = Path(sys.argv[1])
sboms = list(assets.glob("*.spdx.json"))
if len(sboms) != 1:
    raise SystemExit(f"expected one SPDX JSON SBOM, found {len(sboms)}")
document = json.loads(sboms[0].read_text(encoding="utf-8"))
if document.get("spdxVersion") != "SPDX-2.3":
    raise SystemExit("SBOM is not SPDX-2.3")
for field in ("SPDXID", "creationInfo", "documentNamespace"):
    if field not in document:
        raise SystemExit(f"SBOM is missing {field}")
print("sbom-structure: OK")
PY

docker pull "${image_reference}"
docker run --rm "${image_reference}" --version
docker run --rm "${image_reference}"

mkdir -p "$(dirname "${report_file}")"
cat >"${report_file}" <<EOF
# Disaster recovery verification

- Repository: ${repository}
- Release: ${tag}
- Container: ${image_reference}
- Verified at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Release and asset integrity: PASS
- SHA256 checksums: PASS
- Provenance and SBOM attestations: PASS
- SPDX 2.3 structure: PASS
- Container pull and smoke tests: PASS
EOF

echo "disaster-recovery-verification: PASS"
