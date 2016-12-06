Conda recipe to build `clang` package, including:

 - `libclang.dll`
 - `clang` Python bindings

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

    conda install -c wheeler-microfluidics clang


[1]: https://anaconda.org/wheeler-microfluidics/clang
[2]: https://anaconda.org/wheeler-microfluidics
