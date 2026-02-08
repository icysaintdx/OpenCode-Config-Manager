# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = [('assets', 'assets'), ('locales', 'locales')]
hiddenimports = ['qfluentwidgets', 'qfluentwidgets.widgets', 'qfluentwidgets.components', 'qfluentwidgets.common', 'qfluentwidgets.window', 'requests', 'urllib3', 'certifi', 'charset_normalizer', 'idna']
datas += collect_data_files('qfluentwidgets')
hiddenimports += collect_submodules('qfluentwidgets')


a = Analysis(
    ['opencode_config_manager_fluent.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow', 'scipy', 'matplotlib', 'pandas', 'numpy', 'PIL', 'IPython', 'jedi', 'zmq', 'lxml', 'cryptography', 'pyarrow', 'numba', 'llvmlite', 'sqlalchemy', 'openpyxl', 'pytest', 'pygments', 'psutil'],
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
    name='OCCM_Dynamic_Lang',
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
