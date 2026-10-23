# -*- mode: python ; coding: utf-8 -*-
"""Starter PyInstaller spec for a portable Windows BlurGPT GUI.

Usage (on a Windows machine with the project deps):
    pyinstaller blurGPT.spec

This produces dist/BlurGPT/ (onedir) by default. Switch to onefile by
changing the EXE(...) call if desired. Models and ffmpeg are expected
beside the executable at runtime (see core/paths.py and docs/packaging.md).
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Uncomment and adjust if you want to embed the model (large):
        # ('models/blurGPT.pt', 'models'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'torch',
        'ultralytics',
        'cv2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BlurGPT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # windowed GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BlurGPT',
)
