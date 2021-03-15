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
import sklearn
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

block_cipher = None

one_dir_mode = True

binaries = []
if sys.platform.startswith('win'):
    qt_plugins_path = os.path.join(PySide2.__path__[0], "plugins")
    binaries = [
        # (os.path.join(sys.base_prefix, "Library", "bin", "spatialindex_c-64.dll"), '.'),
        # (os.path.join(sys.base_prefix, "Library", "bin", "mkl_intel_thread.dll"), '.'),  # LAPACK etc. routines
        (os.path.join(rtree.__path__[0], 'lib'), 'rtree/lib'),
        (os.path.join(PySide2.__path__[0], "plugins"), 'PySide2')
    ]
elif sys.platform.startswith('linux'):
    qt_plugins_path = os.path.join(PySide2.__path__[0], "Qt", "plugins", "platforms")
    binaries = [
        (os.path.join(sys.base_prefix, "lib", "libspatialindex_c.so"), '.'),
        # (os.path.join(PySide2.__path__[0], "Qt", "plugins", "platforms"), '.')
    ]

upx = False  # UPX does not play with anything Qt
upx_exclude = [
    'PySide2',
    'shiboken2',
    'qwindows.dll'
]

a = Analysis(['seedpod_ground_risk/main.py'],
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
                 ('static_data/tra0307.ods', 'static_data'),
                 ("seedpod_ground_risk/ui_resources/cascade_splash.png", "ui_resources"),
                 ("README.md", '.'),
                 (os.path.join(pyviz_comms.comm_path, "notebook.js"), "pyviz_comms"),
                 (panel.__path__[0], "panel"),
                 (sklearn.utils.__path__[0], "sklearn/utils"),
                 (datashader.__path__[0], "datashader"),
                 (distributed.__path__[0], "distributed"),
                 (os.path.join(fiona.__path__[0], "*.pyd"), "fiona"),  # Geospatial primitives
                 # Geopandas requires access to its data dir
                 (os.path.join(geopandas.__path__[0], "datasets"), "geopandas/datasets"),
                 (shiboken2.__path__[0], "shiboken2"),  # C++ bindings
             ],
             hiddenimports=[
                 "uu",  # Binary data en/decode over ASCII sockets
                 "json",
                 "spatialpandas",
                 "pyproj.datadir",  # CRS projection data
                 "llvmlite.binding",  # Numba C bindings
                 "pyexpat",  # XML parsing
                 "numba.cuda",  # CUDA routines
                 "pyarrow.compute",  # native routines
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[
                 "PySide2.Qt3DCore",
                 "PySide2.Qt3DInput",
                 "PySide2.Qt3DAnimation",
                 "PySide2.Qt3DExtras",
                 "PySide2.Qt3DLogic",
                 "PySide2.Qt3DRender",
                 "PySide2.QtQuick",
                 "PySide2.QtMultimedia",
                 "Pyside2.QtCharts",
                 "PySide2.QtDataVisualization",
                 "PySide2.QtLocation",
                 "PySide2.QtTextToSpeech",
                 "PySide2.QtSql",
                 "PySide2.QtSerialPort",
                 "PySide2.QtSensors",
                 "PySide2.QtScript"
                 "PyQt5",
                 "PyQt4",
                 "tkinter",
                 # "pydoc",
                 "pdb",
                 "IPython",
                 "jupyter",
                 "coverage"
             ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

if one_dir_mode:
    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='SEEDPOD Ground Risk',
              debug=True,
              bootloader_ignore_signals=False,
              strip=False,
              upx=upx,
              upx_exclude=upx_exclude,
              console=True)
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=upx,
                   upx_exclude=upx_exclude,
                   name='SEEDPOD Ground Risk')
else:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              exclude_binaries=False,
              name='SEEDPOD Ground Risk',
              debug=True,
              bootloader_ignore_signals=False,
              strip=False,
              upx=upx,
              upx_exclude=upx_exclude,
              console=True)
