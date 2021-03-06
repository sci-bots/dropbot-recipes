# DropBot driver dependency Conda recipes

This repository contains Conda build recipes for all `dropbot` driver
dependencies.  **Pre-built `win-32`/`win-64` Conda packages for Python 2.7 and
Python 3.6 are available on the [`dropbot` Anaconda][dropbot-conda] channel.**

The packages are split into two types, based on whether or not they are
platform-dependent (i.e., Windows, Linux, MacOS).  Platform-dependent packages typically
either include a compile C-extension component, or write files to `include`,
`bin`, etc. since the Conda `include`, `bin`, etc. paths differ based on
architecture.

For example, on Windows, the path is:

    <conda prefix>/Library/include

On Linux, the path is:

    <conda prefix>/include

-------------------------------------------------

# Build

1. Install `conda-build`:

       conda install -n root conda-build -c conda-forge

2. Build DropBot dependencies (Windows Powershell or Bash). Note that you will  need to install [this package](https://github.com/BCSharp/PSCondaEnvs) to use conda with Powershell:

       conda build --croot C:\bld -c dropbot -c sci-bots -c conda-forge --skip-existing -m variants.yaml $(cat bootstrap-build-order.txt)

## Notes

**Step _(2)_ uses:**

 - `$(cat bootstrap-build-order.txt)` to build recipes in dependency order,
   such that each recipe will only be built after all dependency packages have
   been built.
 - `-m variants.yaml` to build against both Python 2.7 _and_ Python 3.6 (in
   recipes that use [`{{ python }}` variant tag][variants]).
 - `--croot C:\bld` to shorten the file path length of the build environment to
   avoid _"filename too long"_ or _"file does not exist"_ type errors.

   This is a [known issue](https://github.com/conda/conda-build#gotchasfaq).

-------------------------------------------------

# Packages

## DropBot `noarch` dependencies

The following `dropbot` driver dependencies may be built as `noarch` and are compatible 
across platforms (i.e., Windows, Linux, MacOS) and Python versions:

    json-tricks/meta.yaml
    onoff/meta.yaml
    paho-mqtt/meta.yaml
    platformio/click/meta.yaml
    platformio/platform-atmelavr/meta.yaml
    platformio/platform-teensy/meta.yaml
    platformio/platformio-core/meta.yaml
    python-clang/meta.yaml
    si-prefix/meta.yaml
    wheezy.routing/meta.yaml
    _source/arduino-helpers/.conda-recipe/meta.yaml
    _source/asyncserial.py27/conda/asyncserial/meta.yaml **
    _source/asyncserial.py3/conda/asyncserial/meta.yaml **
    _source/clang-helpers/.conda-recipe/meta.yaml
    _source/conda-helpers/.conda-recipe/meta.yaml
    _source/logging-helpers/.conda-recipe/meta.yaml
    _source/mqtt-messages-python/.conda-recipe/meta.yaml
    _source/nanopb-helpers/.conda-recipe/meta.yaml
    _source/or-event/.conda-recipe/meta.yaml
    _source/pandas-helpers/.conda-recipe/meta.yaml
    _source/serial-device/.conda-recipe/meta.yaml

__**__: `asyncserial` has a different version for Python 2.7 and Python 3.5+,
but both versions are compatible across platforms (i.e., Windows, Linux,
MacOS).

## DropBot platform-specific dependencies

The following `dropbot` driver dependencies must be built for each platform and
Python version:

    arduino/fast-digital/meta.yaml
    arduino/linked-list/meta.yaml
    arduino/slow-soft-i2c-master/meta.yaml
    arduino/slow-soft-wire/meta.yaml
    clang/meta.yaml
    matplotlib/meta.yaml
    nanopb/meta.yaml
    ntfsutils/meta.yaml
    path_helpers/meta.yaml
    platformio/framework-arduinoavr/meta.yaml
    platformio/framework-arduinoteensy/meta.yaml
    platformio/tool-avrdude/meta.yaml
    platformio/tool-scons/meta.yaml
    platformio/tool-teensy/meta.yaml
    platformio/toolchain-atmelavr/meta.yaml
    platformio/toolchain-gccarmnoneeabi/meta.yaml
    protoc/meta.yaml
    ragel/meta.yaml
    _source/arduino-memory/.conda-recipe/meta.yaml
    _source/arduino-rpc/.conda-recipe/meta.yaml
    _source/base-node/.conda-recipe/meta.yaml
    _source/base-node-rpc/.conda-recipe/meta.yaml
    _source/c-array-defs/.conda-recipe/meta.yaml
    _source/nadamq/.conda-recipe/meta.yaml
    _source/teensy-minimal-rpc/.conda-recipe/meta.yaml


-------------------------------------------------------------------

# Notes

## Add existing recipe repo

The following commands can be used to graft an existing recipe git
repo to a subdirectory of this repo:

```sh
git remote add temp ...other recipe...
git fetch --all
git branch --no-track '"feat(<recipe package name>)"' temp/master
git remote rm temp

git merge -s ours --no-commit '"feat(<recipe package name>)"' --allow-unrelated-histories
git read-tree -u --prefix=<recipe package name> '"feat(<recipe package name>)"'

git commit
```

Example message to append to the merge commit:

    Add `<recipe package name>` recipe.

-------------------------------------------------

## Switch package to architecture specific



```markdown
fix(conda): do not build as noarch

Do not build as `noarch` package since the Conda `include` path differs
based on architecture.

For example, on Windows, the path is:

    <conda prefix>/Library/include

On Linux, the path is:

    <conda prefix>/include
```


[dropbot-conda]: https://anaconda.org/dropbot/
[variants]: https://conda.io/docs/user-guide/tasks/build-packages/variants.html
