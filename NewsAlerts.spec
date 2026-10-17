# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect tzdata for zoneinfo on Windows
tzdata_datas = collect_data_files('tzdata')

# Collect bottle data/assets if any
bottle_datas = collect_data_files('bottle')

# Collect pywebview and pythonnet data/submodules
webview_datas = collect_data_files('webview')
webview_submodules = collect_submodules('webview')

datas = [
    ('web', 'web'),
] + tzdata_datas + bottle_datas + webview_datas

# Hidden imports that dynamic loaders or reflection might miss
hiddenimports = [
    'zoneinfo',
    'tzdata',
    'bottle',
    'clr_loader',
    'pythonnet',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
] + webview_submodules

a = Analysis(
    ['run_app.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['secrets'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NewsAlerts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
