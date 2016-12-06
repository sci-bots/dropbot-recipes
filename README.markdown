Conda recipe to build `protoc` package, including:

 - `protoc.exe`
 - Google protobuf headers

**Note** Windows 32-bit build only.

Build
=====

Install `conda-build`:

    conda install conda-build

Build recipe:

    conda build .


Install
=======

The [Windows 32-bit build][1] may be installed from the
[`wheeler-microfluidics`][2] channel using:

    conda install -c wheeler-microfluidics protoc


[1]: https://anaconda.org/wheeler-microfluidics/protoc
[2]: https://anaconda.org/wheeler-microfluidics
