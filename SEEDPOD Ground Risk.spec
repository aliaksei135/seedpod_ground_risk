# -*- mode: python ; coding: utf-8 -*-

import os
import sys

import PySide2
import datashader
import distributed
import fiona
import geopandas
import panel
import pyviz_comms
import rtree
import shiboken2
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

block_cipher = None

binaries = []
if sys.platform.startswith('win'):
    qt_plugins_path = os.path.join(PySide2.__path__[0], "plugins")
    binaries = [
        # (os.path.join(sys.base_prefix, "Library", "bin", "spatialindex_c-64.dll"), '.'),
        # (os.path.join(sys.base_prefix, "Library", "bin", "mkl_intel_thread.dll"), '.'),  # LAPACK etc. routines
        (os.path.join(rtree.__path__[0], 'lib'), 'rtree/lib'),
        (os.path.join(PySide2.__path__[0], "plugins"), '.')
    ]
elif sys.platform.startswith('linux'):
    qt_plugins_path = os.path.join(PySide2.__path__[0], "Qt", "plugins", "platforms")
    binaries = [
        (os.path.join(sys.base_prefix, "lib", "libspatialindex_c.so"), '.'),
        # (os.path.join(PySide2.__path__[0], "Qt", "plugins", "platforms"), '.')
    ]

a = Analysis(['seedpod_ground_risk/main.py'],
             # pathex=['/home/aliaksei/PycharmProjects/seedpod_gr_app'],
             binaries=binaries,
             datas=[
                 ('static_data/2018-MRDB-minimal.dbf', 'static_data'),
                 ('static_data/2018-MRDB-minimal.prj', 'static_data'),
                 ('static_data/2018-MRDB-minimal.shp', 'static_data'),
                 ('static_data/2018-MRDB-minimal.shx', 'static_data'),
                 ('static_data/DATA_SOURCES.md', 'static_data'),
                 ('static_data/density.csv', 'static_data'),
                 ('static_data/dft_traffic_counts_aadf.csv', 'static_data'),
                 ('static_data/england_wa_2011_clipped.dbf', 'static_data'),
                 ('static_data/england_wa_2011_clipped.prj', 'static_data'),
                 ('static_data/england_wa_2011_clipped.shp', 'static_data'),
                 ('static_data/england_wa_2011_clipped.shx', 'static_data'),
                 ('static_data/test_path.json', 'static_data'),
                 # ('static_data/timed_tfc.parq.res20.7z', ' static_data'),
                 ('static_data/timed_tfc.parq', 'static_data/timed_tfc.parq'),
                 ('static_data/tra0307.ods', 'static_data'),
                 ("seedpod_ground_risk/ui_resources/cascade_splash.png", "ui_resources"),
                 ("README.md", '.'),
                 (PySide2.__path__[0], "PySide2"),
                 (os.path.join(pyviz_comms.comm_path, "notebook.js"), "pyviz_comms"),
                 (panel.__path__[0], "panel"),
                 (datashader.__path__[0], "datashader"),
                 (distributed.__path__[0], "distributed"),
                 (fiona.__path__[0], "fiona"),  # Geospatial primitives
                 (os.path.join(geopandas.__path__[0], "datasets"), "geopandas/datasets"),
                 # Geopandas requires access to its data dir
                 (shiboken2.__path__[0], "shiboken2"),  # C++ bindings
             ],
             hiddenimports=[
                 "PySide2",  # Qt,
                 "PySide2.QtPrintSupport",
                 "shiboken2",  # PySide2 C++ bindings
                 "uu",  # Binary data en/decode over ASCII sockets
                 "json",
                 "spatialpandas",
                 "pyproj.datadir",  # CRS projection data
                 "llvmlite.binding",  # Numba C bindings
                 "pyexpat",  # XML parsing
                 "numba.cuda",  # CUDA routines
                 "pyarrow.compute",  # native routines
             ],
             # hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[
                 "PyQt5",
                 "PyQt4",
                 "tkinter",
                 "pydoc",
                 "pdb",
                 "IPython",
                 "jupyter"
             ],
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
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='SEEDPOD Ground Risk')
