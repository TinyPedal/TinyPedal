#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VARS_FILE="${1:-${SCRIPT_DIR}/vars.env}"

if [ -f "${VARS_FILE}" ]; then
    # shellcheck disable=SC1090
    . "${VARS_FILE}"
fi

REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

if git -C "${REPO_ROOT}" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "${REPO_ROOT}" submodule update --init --recursive
fi

# Prefer the highest semver tag in the repo, not the nearest tag on HEAD.
TAG="$(git -C "${REPO_ROOT}" tag --list 'v*' --sort=-version:refname | head -n1 || true)"
if [ -z "${TAG}" ]; then
    TAG="$(git -C "${REPO_ROOT}" describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [ -z "${TAG}" ]; then
    echo "Error: could not detect a git tag. Set AUR_PKGVER manually." >&2
    exit 1
fi
AUR_PKGVER="${AUR_PKGVER:-${TAG#v}}"

render_file() {
    local input="$1"
    local output="$2"

    awk \
        -v PKGVER="${AUR_PKGVER}" \
        '{
            gsub(/{{PKGVER}}/, PKGVER)
            print
        }' "${input}" >"${output}"
}

OUT_DIR="${AUR_OUT_DIR:-${SCRIPT_DIR}/out}"
mkdir -p "${OUT_DIR}"

render_file "${SCRIPT_DIR}/PKGBUILD.in" "${OUT_DIR}/PKGBUILD"
render_file "${SCRIPT_DIR}/.SRCINFO.in" "${OUT_DIR}/.SRCINFO"
render_file "${SCRIPT_DIR}/tinypedal.install.in" "${OUT_DIR}/tinypedal.install"

cat <<EOF
Wrote:
  ${OUT_DIR}/PKGBUILD
  ${OUT_DIR}/.SRCINFO
  ${OUT_DIR}/tinypedal.install

Detected tag: ${TAG}
Rendered pkgver: ${AUR_PKGVER}

Next:
  - Update sha256sums if needed (makepkg -g or updpkgsums).
  - Regenerate .SRCINFO with makepkg --printsrcinfo if you prefer.
EOF
