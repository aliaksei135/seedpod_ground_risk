import os
import sys

import PySide2
import distributed
import fiona
import geopandas
import panel
import pyviz_comms
import shiboken2
from cx_Freeze import setup, Executable

qt_plugins_path = os.path.join(PySide2.__path__[0], "plugins")

base = None
# Remove cmd prompt window on win32
# if sys.platform == "win32":
#     base = "Win32GUI"

options = {
    "build_exe": {
        "optimize": 1,  # do not use optimise 2, this removes docstrings, causing build to fail
        "include_files": [
            PySide2.__path__[0],  # additional plugins needed by qt at runtime
            os.path.join(sys.base_prefix, "Library", "bin", "mkl_intel_thread.dll"),  # LAPACK etc. routines
            shiboken2.__path__[0],  # C++ bindings
            distributed.__path__[0],
            fiona.__path__[0],  # Geospatial primitives
            geopandas.__path__[0],  # Geopandas requires access to its data dir
            os.path.join(pyviz_comms.comm_path, "notebook.js"),
            panel.__path__[0],
            tuple(["static_data/2018-MRDB-minimal.dbf"] * 2),
            tuple(["static_data/2018-MRDB-minimal.prj"] * 2),
            tuple(["static_data/2018-MRDB-minimal.shp"] * 2),
            tuple(["static_data/2018-MRDB-minimal.shx"] * 2),
            tuple(["static_data/DATA_SOURCES.md"] * 2),
            tuple(["static_data/density.csv"] * 2),
            tuple(["static_data/dft_traffic_counts_aadf.csv"] * 2),
            tuple(["static_data/england_wa_2011_clipped.dbf"] * 2),
            tuple(["static_data/england_wa_2011_clipped.prj"] * 2),
            tuple(["static_data/england_wa_2011_clipped.shp"] * 2),
            tuple(["static_data/england_wa_2011_clipped.shx"] * 2),
            tuple(["static_data/test_path.json"] * 2),
            tuple(["static_data/timed_tfc.parq.res20.7z"] * 2),
            tuple(["static_data/tra0307.ods"] * 2),
            "README.md",
            ("seedpod_ground_risk/ui_resources/cascade_splash.png", "ui_resources/cascade_splash.png")
        ],
        "packages": [
            "PySide2",
            "shiboken2",
            "uu",
            "json",
            "pyproj.datadir",  # CRS projection data
            "llvmlite.binding",
            "pyexpat",
            "numba.cuda",  # CUDA routines
            "pyarrow.compute"  # native routines
        ],
        "zip_include_packages": [
            "PySide2",
            "PySide2.QtWebEngineCore",
            "PySide2.QtWebEngineWidgets",
            "shiboken2",
            "encodings",
        ],  # reduce size of packages that are used
        "excludes": [
            "tkinter",
            "pydoc",
            "pdb",
            "IPython",
            "jupyter"
        ],  # exclude packages that are not really needed
    }
}

executables = [Executable("seedpod_ground_risk/main.py", base=base, targetName='SEEDPOD Ground Risk')]

setup(
    name="SEEDPOD Ground Risk",
    version="0.1.0",
    author="Aliaksei Pilko <A.Pilko@soton.ac.uk>",
    description="Ground Risk-to-Life model proof of concept for SEEDPOD",
    options=options,
    executables=executables,
)
