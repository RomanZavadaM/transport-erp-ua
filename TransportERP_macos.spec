# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')

a = Analysis(
    ['backend/src/transport_erp/desktop.py'],
    pathex=['backend/src'],
    binaries=webview_binaries,
    datas=[('frontend/out', 'frontend')] + webview_datas,
    hiddenimports=webview_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TransportERP-UA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='TransportERP-UA',
)

app = BUNDLE(
    coll,
    name='TransportERP-UA.app',
    icon=None,
    bundle_identifier='ua.transport.erp',
    version='0.2',
    info_plist={
        'CFBundleDisplayName': 'TransportERP-UA',
        'CFBundleName': 'TransportERP-UA',
        'LSApplicationCategoryType': 'public.app-category.business',
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
    },
)
