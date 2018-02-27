Conda recipe to build `clang` package, including:

 - `libclang.dll` (Windows only)
 - `libclang.so` (Linux only)

**Note** Windows 32-bit build and Linux build only.

Build
=====

Install `conda-build`:

    conda install conda-build

Build recipe:

    conda build .


Install
=======

The [Windows 32-bit or Linux 32-bit build][1] may be installed from the
[`sci-bots`][2] channel using:

    conda install -c sci-bots clang


See also
========

 - [`python-clang`][3]: Clang Python bindings


[1]: https://anaconda.org/sci-bots/clang
[2]: https://anaconda.org/sci-bots
[3]: https://anaconda.org/sci-bots/python-clang
