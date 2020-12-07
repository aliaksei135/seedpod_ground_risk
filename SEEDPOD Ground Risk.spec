# -*- mode: python ; coding: utf-8 -*-

import os
import sys

import panel
import pyviz_comms
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

block_cipher = None

a = Analysis(['seedpod_ground_risk/main.py'],
             pathex=['/home/aliaksei/PycharmProjects/seedpod_gr_app'],
             binaries=[(os.path.join(sys.base_prefix, "lib", "libspatialindex_c.so"), '.')],
             datas=[('static_data/2018-MRDB-minimal.dbf', ' static_data'),
                    ('static_data/2018-MRDB-minimal.prj', ' static_data'),
                    ('static_data/2018-MRDB-minimal.shp', ' static_data'),
                    ('static_data/2018-MRDB-minimal.shx', ' static_data'),
                    ('static_data/DATA_SOURCES.md', ' static_data'), ('static_data/density.csv', ' static_data'),
                    ('static_data/dft_traffic_counts_aadf.csv', ' static_data'),
                    ('static_data/england_wa_2011_clipped.dbf', ' static_data'),
                    ('static_data/england_wa_2011_clipped.prj', ' static_data'),
                    ('static_data/england_wa_2011_clipped.shp', ' static_data'),
                    ('static_data/england_wa_2011_clipped.shx', ' static_data'),
                    ('static_data/test_path.json', ' static_data'),
                    ('static_data/timed_tfc.parq.res20.7z', ' static_data'),
                    ('static_data/tra0307.ods', ' static_data'),
                    (os.path.join(pyviz_comms.comm_path, "notebook.js"), "pyviz_comms"),
                    (os.path.join(panel.__path__[0], "package.json"), "panel")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='SEEDPOD Ground Risk',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='SEEDPOD Ground Risk')
