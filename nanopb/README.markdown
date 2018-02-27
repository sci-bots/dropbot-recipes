Conda recipe to build `nanopb` package, including:

 - `nanopb.bat` command to compile [protocol buffer][1] messages using
   [nanopb][2].
     * For example:

            nanopb --nanopb_out=. simple.proto
 - `nanopb` Arduino library, located at:

        $PREFIX/Library/include/Arduino/nanopb

**Note** Windows 32-bit build only.

Build
=====

Install `conda-build`:

    conda install conda-build

Build recipe:

    conda build .


Install
=======

The [Windows 32-bit build][3] may be installed from the
[`wheeler-microfluidics`][4] channel using:

    conda install -c wheeler-microfluidics nanopb


[1]: https://developers.google.com/protocol-buffers/
[2]: https://koti.kapsi.fi/~jpa/nanopb/
[3]: https://anaconda.org/wheeler-microfluidics/nanopb
[4]: https://anaconda.org/wheeler-microfluidics
