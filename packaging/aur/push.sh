#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VARS_FILE="${1:-${SCRIPT_DIR}/vars.env}"

if [ -f "${VARS_FILE}" ]; then
    # shellcheck disable=SC1090
    . "${VARS_FILE}"
fi

AUR_PKGNAME="tinypedal"
AUR_SSH_USER="${AUR_SSH_USER:-aur}"
AUR_GIT_URL="${AUR_GIT_URL:-ssh://${AUR_SSH_USER}@aur.archlinux.org/${AUR_PKGNAME}.git}"
AUR_REPO_DIR="${AUR_REPO_DIR:-${SCRIPT_DIR}/aur-repo}"
AUR_OUT_DIR="${AUR_OUT_DIR:-${SCRIPT_DIR}/out}"

if [ ! -d "${AUR_OUT_DIR}" ]; then
    echo "Missing ${AUR_OUT_DIR}. Run render.sh first." >&2
    exit 1
fi

if [ ! -d "${AUR_REPO_DIR}/.git" ]; then
    git clone "${AUR_GIT_URL}" "${AUR_REPO_DIR}"
fi

cp "${AUR_OUT_DIR}/PKGBUILD" "${AUR_OUT_DIR}/.SRCINFO" "${AUR_OUT_DIR}/tinypedal.install" "${AUR_REPO_DIR}/"

cd "${AUR_REPO_DIR}"
git status -sb

if [ "${AUR_AUTO_COMMIT:-0}" = "1" ]; then
    PKGVER="$(awk -F= '/^pkgver=/{print $2}' PKGBUILD | head -n1)"
    git add PKGBUILD .SRCINFO tinypedal.install
    git commit -m "Update to v${PKGVER:-unknown}"
fi

echo "Ready to push: (cd ${AUR_REPO_DIR} && git push)"
