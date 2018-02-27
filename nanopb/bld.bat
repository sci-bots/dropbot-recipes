@echo on
set MODULE_DIR=%SP_DIR%\nanopb_generator

REM Patch generator to support Python 3
patch --verbose --binary -l generator/nanopb_generator.py -i "%RECIPE_DIR%\nanopb_generator.py3-support.patch"
if errorlevel 1 exit 1
REM Convert `nanopb_generator.py` to Python module
md "%MODULE_DIR%"
if errorlevel 1 exit 1
copy generator\nanopb_generator.py "%MODULE_DIR%\__main__.py"
if errorlevel 1 exit 1
echo "" > "%MODULE_DIR%\__init__.py"
if errorlevel 1 exit 1

REM Generate nanopb Python protobuf definitions.
set NANO_PROTO_DIR=generator\proto
protoc --python_out=%NANO_PROTO_DIR% --proto_path=%NANO_PROTO_DIR% %NANO_PROTO_DIR%\nanopb.proto
if errorlevel 1 exit 1
protoc --python_out=%NANO_PROTO_DIR% --proto_path=%NANO_PROTO_DIR% %NANO_PROTO_DIR%\plugin.proto
if errorlevel 1 exit 1
xcopy /S /Y /I /Q %NANO_PROTO_DIR% "%MODULE_DIR%\proto"
if errorlevel 1 exit 1

REM Create batch file to run `nanopb_generator` Python module as a script
echo @echo off > "%PREFIX%"\Library\bin\protoc-gen-nanopb.bat
echo python -m nanopb_generator --protoc-plugin >> "%PREFIX%"\Library\bin\protoc-gen-nanopb.bat
if errorlevel 1 exit 1
REM Create batch file to call protoc compiler with `nanopb_generator` plugin
echo @echo off> "%PREFIX%"\Library\bin\nanopb.bat
echo set BIN_DIR=%%~dp0>> "%PREFIX%"\Library\bin\nanopb.bat
echo protoc --plugin=protoc-gen-nanopb="%%BIN_DIR%%protoc-gen-nanopb.bat" %%*>> "%PREFIX%"\Library\bin\nanopb.bat
if errorlevel 1 exit 1

REM Copy nanopb C source and headers to Arduino
setlocal enableextensions
md "%PREFIX%"\Library\include\Arduino\nanopb\src
endlocal
copy "%RECIPE_DIR%"\library.properties "%PREFIX%"\Library\include\Arduino\nanopb
copy "%RECIPE_DIR%"\nanopb.h "%PREFIX%"\Library\include\Arduino\nanopb\src
copy *.h "%PREFIX%"\Library\include\Arduino\nanopb\src
copy *.c "%PREFIX%"\Library\include\Arduino\nanopb\src
copy *.txt "%PREFIX%"\Library\include\Arduino\nanopb\src
copy *.md "%PREFIX%"\Library\include\Arduino\nanopb\src
copy AUTHORS "%PREFIX%"\Library\include\Arduino\nanopb\src
copy BUILD "%PREFIX%"\Library\include\Arduino\nanopb\src
copy CHANGELOG.txt "%PREFIX%"\Library\include\Arduino\nanopb\src
