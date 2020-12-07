import os
import sys

import PySide2
from cx_Freeze import setup, Executable

qt_plugins_path = os.path.join(PySide2.__path__[0], "Qt", "plugins")

base = None
if sys.platform == "win32":
    base = "Win32GUI"

options = {
    "build_exe": {
        # "build_exe": "dist",
        "optimize": 0,
        "include_files": [
            os.path.join(qt_plugins_path, "platforms"),  # additional plugins needed by qt at runtime
            "static_data/2018-MRDB-minimal.dbf",
            "static_data/2018-MRDB-minimal.prj",
            "static_data/2018-MRDB-minimal.shp",
            "static_data/2018-MRDB-minimal.shx",
            "static_data/DATA_SOURCES.md",
            "static_data/density.csv",
            "static_data/dft_traffic_counts_aadf.csv",
            "static_data/england_wa_2011_clipped.dbf",
            "static_data/england_wa_2011_clipped.prj",
            "static_data/england_wa_2011_clipped.shp",
            "static_data/england_wa_2011_clipped.shx",
            "static_data/test_path.json",
            "static_data/timed_tfc.parq.res20.7z",
            "static_data/tra0307.ods"
        ],
        "packages": [
            "PySide2",
        ],
        "zip_include_packages": [
            "PySide2",
            "PySide2.QtWebEngineCore",
            "PySide2.QtWebEngineWidgets",
            "shiboken2",
            "encodings",
            "pyviz_comms"
        ],  # reduce size of packages that are used
        "excludes": [
            "tkinter",
            "unittest",
            "email",
            "http",
            "xml",
            "pydoc",
            "pdb",
        ],  # exclude packages that are not really needed
    }
}

executables = [Executable("seedpod_ground_risk/main.py", base=base, targetName='SEEDPOD Ground Risk')]

setup(
    name="SEEDPOD Ground Risk",
    version="0.1a",
    description="Ground Risk-to-Life model proof of concept for SEEDPOD",
    options=options,
    executables=executables,
)
