# `conda-env-exec`

# Motivation

As of `conda>=4.4`, new Windows Conda environments no longer contain
`Scripts\activate.bat` or `Scripts\conda.bat`.

The `Scripts\activate.bat` script could previously be used to, for example,
execute various commands in scripts within the activated environment.

[`conda-wrappers`][conda-wrappers] helps somewhat for executing, e.g.,
`python`, `ipython`, `jupyter`, etc.

However, it is also sometimes useful to execute `conda` commands from within an
environment, e.g., to install new packages into the environment, without having
to explicitly add the root Conda environment to the path.

# Solution

This package creates a batch script calling the `conda` executable that was
used during the installation of this package in the `Scripts` directory of the
Conda environment.  A wrapped version of the created `conda.bat` is also
created (using [`conda-wrappers`][conda-wrappers]) in the
`Scripts/wrapper/conda` directory, which is equivalent to running `conda` in
the activated environment.

For example, after installing this package in an environment named `my-env`,
`conda` commands could be run as follows:

```sh
$ C:\Users\me\Miniconda2\envs\my-env\Scripts\wrappers\conda\conda.bat install ...
```

# See also

 - [`conda/conda/issues/7126`: "With conda being a shell function in 4.4+,
   what's the suggested way to use conda via scripts when an environment isn't
   explicitly activated by the user
   beforehand?"](https://github.com/conda/conda/issues/7126)
 - `conda` gitter messages:
   - [April 20, 2018 4:49 PM](https://gitter.im/conda/conda?at=5ada526027c509a77433792c)
   - [April 20, 2018 5:02 PM](https://gitter.im/conda/conda?at=5ada557d15c9b031141b0187)


[conda-wrappers]: https://anaconda.org/conda-forge/conda-wrappers
