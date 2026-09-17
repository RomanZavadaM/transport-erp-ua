#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "TransportERP-UA.app потрібно збирати безпосередньо на macOS." >&2
    exit 1
fi

app_version="$(tr -d '\r\n' < PREVIEW_VERSION.txt)"
app_revision="$(tr -d '\r\n' < PREVIEW_REVISION.txt)"
app_version_safe="${app_version//./_}"
app_arch="$(uname -m)"
app_python="${TRANSPORT_ERP_MACOS_PYTHON:-python3}"
app_venv="${TRANSPORT_ERP_MACOS_VENV:-.venv-macos}"
bundle_dir="TransportERP-UA_v${app_version_safe}_TEST_${app_revision}_macOS_${app_arch}"
bundle_zip="${bundle_dir}_Portable.zip"

pushd frontend >/dev/null
npm install
npm run lint
npm run typecheck
npm run build
popd >/dev/null

"${app_python}" -m venv "${app_venv}"
"${app_venv}/bin/python" -m pip install --upgrade pip
"${app_venv}/bin/python" -m pip install -e './backend[desktop,dev]' 'pyinstaller>=6.10,<7.0'
pushd backend >/dev/null
"../${app_venv}/bin/python" -m ruff check .
"../${app_venv}/bin/python" -m mypy
"../${app_venv}/bin/python" -m pytest -q
popd >/dev/null

rm -rf 'dist/TransportERP-UA.app' 'dist/TransportERP-UA'
"${app_venv}/bin/python" -m PyInstaller --noconfirm --clean TransportERP_macos.spec

app_bundle='dist/TransportERP-UA.app'
app_executable='dist/TransportERP-UA.app/Contents/MacOS/TransportERP-UA'
[[ -x "${app_executable}" ]]
if find "${app_bundle}" -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -print -quit | grep -q .; then
    echo "У TransportERP-UA.app неочікувано знайдено базу даних." >&2
    exit 1
fi
file "${app_executable}" | grep -q "${app_arch}"
codesign --force --deep --sign - "${app_bundle}"
codesign --verify --deep --strict "${app_bundle}"
TRANSPORT_ERP_SMOKE_TEST_ONLY=1 "${app_executable}"

rm -rf "${bundle_dir}" "${bundle_zip}"
mkdir "${bundle_dir}"
mv "${app_bundle}" "${bundle_dir}/TransportERP-UA.app"
printf '%s\n' \
  "TransportERP-UA v${app_version} TEST ${app_revision}" \
  'Business data are stored outside this application bundle.' \
  'Persistent data: ~/Library/Application Support/TransportERP-UA' \
  'This testing build is ad-hoc signed and not notarized.' \
  > "${bundle_dir}/README-START.txt"
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "${bundle_dir}" "${bundle_zip}"
shasum -a 256 "${bundle_zip}" > "SHA256SUMS_v${app_version_safe}_TEST_${app_revision}_macOS_${app_arch}.txt"
echo "Готово: ${bundle_zip}"
