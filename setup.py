import os

from setuptools import setup, find_packages
import platform
import pkg_resources

####
# setup.py is used over a static setup.cfg as dynamic determination of local wheel dependencies is required.
###

extern_local_path = 'file:///../extern/'
extern_full_path = 'file:///' + os.path.join(os.getcwd(), 'extern', ) + os.sep

if platform.system() == 'Windows':
    requirements_file = os.path.join(os.getcwd(), 'requirements.txt')
else:
    requirements_file = os.path.join(os.getcwd(), 'requirements-linux.txt')

with open(requirements_file) as _requirements_file:
    requirements = [
        str(package).replace(extern_local_path, extern_full_path)
        for package in
        pkg_resources.parse_requirements(_requirements_file.read())
    ]

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='seedpod-ground-risk',
    version='0.15.0',
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
)
