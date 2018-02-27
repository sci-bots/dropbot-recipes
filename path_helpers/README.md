Conda recipe to build `path_helpers` package.

Build
=====

Install `conda-build`:

    conda install conda-build

Build recipe:

    conda build . -c sci-bots -m variants.yaml


Install
=======

The pre-built package may be installed from the [`sci-bots`][2] channel using:

    conda install -c sci-bots path_helpers


[1]: https://anaconda.org/sci-bots/path-helpers
[2]: https://anaconda.org/sci-bots
