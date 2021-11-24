import os

import numpy as np
from Cython.Build import cythonize
from setuptools import setup, find_packages

####
# setup.py is used over a static setup.cfg as dynamic determination of local wheel dependencies is required.
###

ext_options = {"compiler_directives": {"profile": False, 'language_level': 2, 'cdivision': True}, "annotate": True,
               "gdb_debug": False}
# ext_options = {"compiler_directives": {"profile": False}, "annotate": True, "gdb_debug": False}

extern_path = 'file:///' + os.path.join(os.getcwd(), 'extern', ) + os.sep

requirements = ['altgraph==0.17',
                'attrs==20.3.0',
                'bokeh==2.3.1',
                f'Cartopy @ {extern_path}Cartopy-0.19.0.post1-cp38-cp38-win_amd64.whl',
                'certifi==2020.12.5',
                'chardet==4.0.0',
                'click==7.1.2',
                'click-plugins==1.1.1',
                'cligj==0.7.1',
                'cloudpickle==1.6.0',
                'colorama==0.4.4',
                'colorcet==2.0.6',
                'commonmark==0.9.1',
                'cycler==0.10.0',
                'dask==2021.4.0',
                'datashader==0.12.1',
                'datashape==0.5.2',
                'defusedxml==0.7.1',
                'dill==0.3.3',
                'distributed==2021.4.0',
                f'fastparquet @ {extern_path}fastparquet-0.6.3-cp38-cp38-win_amd64.whl',
                f'Fiona @ {extern_path}Fiona-1.8.19-cp38-cp38-win_amd64.whl',
                'fsspec==2021.4.0',
                'future==0.18.2',
                f'GDAL @ {extern_path}GDAL-3.2.3-cp38-cp38-win_amd64.whl',
                f'rasterio @ {extern_path}rasterio-1.2.3-cp38-cp38-win_amd64.whl',
                'geopandas==0.9.0',
                'geoviews==1.9.1',
                'HeapDict==1.0.1',
                'holoviews==1.14.3',
                'import-profiler==0.0.3',
                'Jinja2==2.11.3',
                'kiwisolver==1.3.1',
                'llvmlite==0.36.0',
                'locket==0.2.1',
                'Markdown==3.3.4',
                'MarkupSafe==1.1.1',
                'matplotlib==3.4.1',
                'msgpack==1.0.2',
                'multipledispatch==0.6.0',
                'multiprocess==0.70.11.1',
                'munch==2.5.0',
                'numba==0.53.1',
                'numpy==1.20.2',
                'odfpy==1.4.1',
                'packaging==20.9',
                'pandas==1.2.4',
                'panel==0.11.3',
                'param==1.10.1',
                'partd==1.2.0',
                'pathos==0.2.7',
                'pefile==2019.4.18',
                'Pillow==8.2.0',
                'pox==0.2.9',
                'ppft==1.6.6.3',
                'psutil==5.8.0',
                'pyarrow==3.0.0',
                'pyct==0.4.8',
                'pygeos==0.8',
                'Pygments==2.8.1',
                'pyinstaller @ https://github.com/pyinstaller/pyinstaller/tarball/develop',
                'pyinstaller-hooks-contrib==2021.1',
                'pyparsing==2.4.7',
                f'pyproj @ {extern_path}pyproj-3.0.1-cp38-cp38-win_amd64.whl',
                'pyshp==2.1.3',
                'PySide2==5.15.2',
                'python-dateutil==2.8.1',
                'pytz==2021.1',
                'pyviz-comms==2.0.1',
                'pywin32-ctypes==0.2.0',
                'PyYAML==5.4.1',
                'requests==2.25.1',
                'retrying==1.3.3',
                'rich==10.1.0',
                f'Rtree @ {extern_path}Rtree-0.9.7-cp38-cp38-win_amd64.whl',
                'scipy==1.6.2',
                'Shapely==1.7.1',
                'shiboken2==5.15.2',
                'six==1.15.0',
                'sortedcontainers==2.3.0',
                'spatialpandas==0.3.6',
                'tabulate==0.8.9',
                'tblib==1.7.0',
                'thrift==0.13.0',
                'toolz==0.11.1',
                'topojson==1.0',
                'tornado==6.1',
                'tqdm==4.60.0',
                'typing-extensions==3.7.4.3',
                'urllib3==1.26.4',
                'xarray==0.17.0',
                'zict==2.0.0',
                'casex~=1.0.5',
                'scikit-learn~=0.24.1',
                'scikit-image~=0.18.1']


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='seedpod-ground-risk',
    version='0.14.0',
    author='Aliaksei Pilko',
    author_email='a.pilko@southampton.ac.uk',
    description='UAS ground risk analysis and path planning',
    long_description=readme(),
    url='https://github.com/aliaksei135/seedpod_ground_risk',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Operating System :: OS Independent',
        'Environment :: GPU :: NVIDIA CUDA',
        'Intended Audience :: Science/Research',
    ],
    project_urls={
        'Source': 'https://github.com/aliaksei135/seedpod_ground_risk',
        'Tracker': 'https://github.com/aliaksei135/seedpod_ground_risk/issues',
    },
    packages=find_packages(exclude=['seedpod_ground_risk.ui_resources.*']),
    scripts=['seedpod_ground_risk/cli/spgr.py'],
    package_data={
        'seedpod_ground_risk': ['extern/*', 'static_data/*']
    },
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'spgr = seedpod_ground_risk.cli.spgr:main',
        ],
    },
    include_dirs=[np.get_include()],
    ext_modules=cythonize('seedpod_ground_risk/**/*.pyx', **ext_options),
    zip_safe=False,
)
