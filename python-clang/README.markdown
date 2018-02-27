Conda recipe to build the `python-clang` package, i.e., `clang` Python
bindings.

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

    conda install -c sci-bots python-clang


See also
========

 - [`clang`][3]: Compiled Clang shared library.


[1]: https://anaconda.org/sci-bots/clang
[2]: https://anaconda.org/sci-bots
