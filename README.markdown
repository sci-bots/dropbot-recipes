Conda recipe to build [`ragel`][0] package, including:

 - [`ragel.exe`][win-ragel]

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

    conda install -c wheeler-microfluidics ragel


[win-ragel]: https://github.com/eloraiby/ragel-windows
[0]: http://www.colm.net/open-source/ragel/
[1]: https://anaconda.org/wheeler-microfluidics/ragel
[2]: https://anaconda.org/wheeler-microfluidics
