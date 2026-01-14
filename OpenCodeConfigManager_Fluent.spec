# -*- mode: python ; coding: utf-8 -*-
# OpenCode Config Manager Fluent 版本构建配置
# 基于 PyQt5 + QFluentWidgets
# 使用方法: pyinstaller OpenCodeConfigManager_Fluent.spec --noconfirm

VERSION = '1.0.0'

# 收集 qfluentwidgets 资源
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

qfluentwidgets_datas = collect_data_files('qfluentwidgets')
qfluentwidgets_hiddenimports = collect_submodules('qfluentwidgets')

a = Analysis(
    ['opencode_config_manager_fluent_v1.0.0.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.ico', 'assets'),
        ('assets/icon.png', 'assets'),
        ('assets/logo.png', 'assets'),
        ('assets/logo.ico', 'assets'),
        ('assets/logo1.png', 'assets'),
    ] + qfluentwidgets_datas,
    hiddenimports=qfluentwidgets_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'tensorflow',
        'scipy',
        'matplotlib',
        'pandas',
        'numpy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'OpenCodeConfigManager_v{VERSION}',
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
    icon=['assets/icon.ico'],
)
