# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['dcr_python/src/ui/fim_loader.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('dcr_python/src/report-template.xlsx', 'src/'),
        ('dcr_python/src/ui/logo.png', 'src/ui/'),
        ('dcr_python/src/ui/logo.ico', 'src/ui/'),
    ],
    hiddenimports=[
        'pandas', 
        'openpyxl', 
        'PyQt5',
        'numpy',
        'dateutil',
        'pytz',
        'PIL'
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
    name='DataFerns-Analyser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='dcr_python/src/ui/logo.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DataFerns-Analyser',
)
