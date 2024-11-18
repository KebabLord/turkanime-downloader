# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['turkanime_gui\\main.py'],
    pathex=[],
    binaries=[],
    datas = [
    ('gereksinimler.json', '.'),
    ('gecmis.json', '.'),
    ('ayarlar.json', '.'),
    ('turkanime_api\\cli\\dosyalar.py', '.'),
    ('turkanime_api\\cli\\gereksinimler.py', '.'),
    ('turkanime_gui\\gui.py', '.'),
    ('turkanime_api', '.'),
    ('turkanime_api\\objects.py', '.'),
    ('turkanime_api\\webdriver.py', '.'),
    ('turkanime_api\\bypass.py', '.'),
    ],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='main',
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
