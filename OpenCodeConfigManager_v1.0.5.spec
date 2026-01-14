# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['opencode_config_manager_fluent.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],  # 如果后续还报 win32 相关错误，可能需要在这里添加 'win32com.shell'
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 删除了 'win32com'
    excludes=['torch', 'scipy', 'pandas', 'matplotlib', 'numpy', 'PIL', 'IPython', 'jedi', 'zmq', 'lxml', 'cryptography', 'pyarrow', 'numba', 'llvmlite', 'sqlalchemy', 'openpyxl', 'pytest', 'pygments', 'psutil'], 
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
    name='OpenCodeConfigManager_v1.0.5',
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
    icon=['assets\\icon.ico'],
)
