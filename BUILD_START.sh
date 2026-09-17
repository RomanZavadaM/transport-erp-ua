#!/usr/bin/env bash
set -euo pipefail

app_version="$(tr -d '\r\n' < PREVIEW_VERSION.txt)"
app_revision="$(tr -d '\r\n' < PREVIEW_REVISION.txt)"
app_version_safe="${app_version//./_}"
package_dir="TransportERP-UA_v${app_version_safe}_TEST_${app_revision}_START"
package_zip="${package_dir}.zip"

python3 -m pip install --upgrade pip
python3 -m pip install -e './backend[desktop,dev]'
pushd backend >/dev/null
python3 -m ruff check .
python3 -m mypy
python3 -m pytest -q
popd >/dev/null

pushd frontend >/dev/null
npm install
npm run lint
npm run typecheck
npm run build
popd >/dev/null

rm -rf "${package_dir}" "${package_zip}"
mkdir -p "${package_dir}/frontend/out"
cp START.bat START_WINDOWS.bat OPEN_DATA_FOLDER.bat README-PYTHON-PREVIEW.txt "${package_dir}/"
cp PREVIEW_VERSION.txt PREVIEW_REVISION.txt CHECKPOINT_CURRENT.md PROJECT_STATE.md RELEASE_CHECKLIST.md "${package_dir}/"
cp -R backend "${package_dir}/backend"
cp -R frontend/out/. "${package_dir}/frontend/out/"

find "${package_dir}" -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' -o -name '.venv' -o -name '.venv-macos' \) -prune -exec rm -rf '{}' + || true
find "${package_dir}" -type f \( -name '*.pyc' -o -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -delete
zip -r "${package_zip}" "${package_dir}" >/dev/null

if unzip -l "${package_zip}" | grep -Eiq '\.(db|sqlite|sqlite3)([[:space:]]|$)|__pycache__|\.pyc([[:space:]]|$)'; then
    echo 'Database or cache unexpectedly bundled in START package' >&2
    exit 1
fi
sha256sum "${package_zip}" > "SHA256SUMS_v${app_version_safe}_TEST_${app_revision}_START.txt"
echo "Готово: ${package_zip}"
