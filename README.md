# DropBot driver dependency Conda recipes

This repository contains Conda build recipes for all `dropbot` driver
dependencies.

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

2. Build DropBot **`noarch` dependencies** (use `grep` to find recipes containing
   `noarch`):
   - Windows Powershell:

         conda build -c cfobel -c conda-forge --skip-existing $(grep noarch $(cmd /C dir /s/b meta.yaml) -l)
   - Bash:

         conda build -c cfobel -c conda-forge --skip-existing $(grep noarch $(find -name meta.yaml) -l)

3. Build DropBot **platform-specific dependencies** (use `grep` to find recipes
   which do not contain `noarch`):
   - Windows Powershell:

         conda build -c cfobel -c conda-forge --skip-existing $(grep noarch $(cmd /C dir /s/b meta.yaml) -L)
   - Bash:

         conda build -c cfobel -c conda-forge --skip-existing $(grep noarch $(find -name meta.yaml) -L)

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

    git remote add temp ...other recipe...
    git fetch --all
    git branch --no-track '"feat(<recipe package name>)"' temp/master
    git remote rm temp

    git merge -s ours --no-commit '"feat(<recipe package name>)"' --allow-unrelated-histories
    git read-tree -u --prefix=<recipe package name> '"feat(<recipe package name>)"'

    git commit

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

