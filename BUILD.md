# Building

The build process should be fairly familiar. The instructions provided are for Windows x64.

1. Ensure you have the required dependencies:
    - Python 3.8 *ONLY*
    - [Nvidia CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

   Only Python 3.8 can be used currently, as the local dependencies are built for 3.8 Windows x64. They are provided by
   Christoph Gohlke [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/).

2. Create and activate a virtual environment to install into, any should do. Here we use `virtualenv`:

```commandline
python3 -m venv spgr

.\spgr\Scripts\activate.bat
```

3. Clone the repository

```commandline
git clone https://github.com/aliaksei135/seedpod_ground_risk.git
```

4. Install requirements

```commandline
cd seedpod_ground_risk

pip install -r requirements.txt
```

This is enough to run and develop on.

# Packaging

There are 2 available packaging formats: Installer or wheel. The former is what is distributed, while the latter is
required for use of the CLI for instance.

When packaging don't forget to check versions in both `setup.py` and `make_installer.iss` and ensure they match!

### Installer

The installer uses `PyInstaller` to extract all the dependencies and `InnoSetup` to create a Windows installer package
out of them.

1. Ensure you have installed `InnoSetup` [here](https://jrsoftware.org/isdl.php).

2. Inside the root repository directory with the virtualenv active:

```commandline
python -O -m PyInstaller --noconfirm "SEEDPOD Ground Risk.spec"
```

We run `python` with the first level optimise flag `-O` to slim down some now unnecessary debug code. *Do not use second
level optimisation `-OO`, as this removes some docstrings that break dependencies.*

3. Open `make_installer.iss` in InnoSetup and run the packaging process. This can take a while, but should output an
   installer in the `Output` folder.

### Wheel

1. Inside the root repository directory with the virtualenv active. Ensure you have up to date build tools:

```commandline
pip install --upgrade build
```

2. Build the wheel as usual:

```commandline
python -m build
```

The `.whl` file will be built in `dist`. You can install this as required:

```commandline
pip install <.whl file>
```

then import the module:

```python
import seedpod_ground_risk # Import entire module
import seedpod_ground_risk.cli # Only the CLI
```