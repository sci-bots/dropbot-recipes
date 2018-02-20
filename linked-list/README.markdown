Conda recipe to build Conda package for [Arduino `LinkedList`][1].

Build
=====

Install `conda-build`:

    conda install conda-build

Build recipe:

    conda build .


Install
=======

Install [pre-built package][2] from the [`wheeler-microfluidics`][3] channel
using:

    conda install -c wheeler-microfluidics arduino-linked-list


[1]: https://github.com/ivanseidel/LinkedList
[2]: https://anaconda.org/wheeler-microfluidics/arduino-linked-list
[3]: https://anaconda.org/wheeler-microfluidics
