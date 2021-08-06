# SEEDPOD Ground Risk Model

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4776529.svg)](https://doi.org/10.5281/zenodo.4776529)

Proof of Concept demonstrating modelling of UAS ground risk from open source data sources. This constructs a
spatiotemporal population density map and evaluates the risk posed by a parameterised UAS.

All data processing is performed locally, so performance depends on your machine spec. At least 8GiB of RAM is essential
however.

Developed as part of the [SEEDPOD project](https://cascadeuav.com/seedpod/) funded by the E-Drone project grant
grant ([EP/V002619/1)](https://gow.epsrc.ukri.org/NGBOViewGrant.aspx?GrantRef=EP/V002619/1).

## Disclaimer

***This is intended to provide guidance on overflight risks in terms of risk-to-life (RtL) and is by no means an
extensive or complete picture of the ground risks. While the software is intended to promote safe drone flight, use of
this software does not in itself guarantee safe or legal drone operation. Follow
the [drone code](https://dronesafe.uk/drone-code/).***

## Usage

### UI

A Windows 64-bit installer is provided with each release. This is the easiest option for just using the tool. This works
on its own, however is not able to take advantage of the GPU, causing rather slow risk map generation. For this reason
it is highly recommended to install the [Nvidia CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).

### CLI

A CLI is provided to allow for automation. Currently this requires building your own wheels as local wheel dependencies
cannot be packaged and distributed. The included data files also take the package above the PyPI limit.

See `BUILD.md` for further instructions.

## License

    MIT License
    
    Copyright (c) 2021 Aliaksei Pilko
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.