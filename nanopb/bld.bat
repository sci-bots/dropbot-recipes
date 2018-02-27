set NANO_SRC=nanopb-0.3.7
set NANO_SRC_DIR=nanopb

REM Download Windows (32-bit) binary.
"%PYTHON%" -m wget https://koti.kapsi.fi/~jpa/nanopb/download/%NANO_SRC%.tar.gz
if errorlevel 1 exit 1

REM Extract release from ZIP archive.
"%PREFIX%"\Library\bin\7za x %NANO_SRC%.tar.gz -y
"%PREFIX%"\Library\bin\7za x %NANO_SRC%.tar -y
if errorlevel 1 exit 1

REM Convert `nanopb_generator.py` to Python module
md nanopb_generator
if errorlevel 1 exit 1
copy "%NANO_SRC_DIR%"\generator\nanopb_generator.py nanopb_generator\__main__.py
if errorlevel 1 exit 1
echo "" > nanopb_generator\__init__.py
if errorlevel 1 exit 1

REM Generate nanopb Python protobuf definitions.
set NANO_PROTO_DIR="%NANO_SRC_DIR%"\generator\proto
protoc --python_out=%NANO_PROTO_DIR% --proto_path=%NANO_PROTO_DIR% %NANO_PROTO_DIR%\nanopb.proto
if errorlevel 1 exit 1
protoc --python_out=%NANO_PROTO_DIR% --proto_path=%NANO_PROTO_DIR% %NANO_PROTO_DIR%\plugin.proto
if errorlevel 1 exit 1
xcopy /S /Y /I /Q %NANO_PROTO_DIR% nanopb_generator\proto
if errorlevel 1 exit 1

REM Copy `nanopb_generator` Python module to site-packages
xcopy /S /Y /I /Q nanopb_generator "%PREFIX%"\Lib\site-packages\nanopb_generator
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
copy "%NANO_SRC_DIR%"\*.h "%PREFIX%"\Library\include\Arduino\nanopb\src
copy "%NANO_SRC_DIR%"\*.c "%PREFIX%"\Library\include\Arduino\nanopb\src
copy "%NANO_SRC_DIR%"\*.txt "%PREFIX%"\Library\include\Arduino\nanopb\src
copy "%NANO_SRC_DIR%"\*.md "%PREFIX%"\Library\include\Arduino\nanopb\src
copy "%NANO_SRC_DIR%"\AUTHORS "%PREFIX%"\Library\include\Arduino\nanopb\src
copy "%NANO_SRC_DIR%"\BUILD "%PREFIX%"\Library\include\Arduino\nanopb\src
copy "%NANO_SRC_DIR%"\CHANGELOG.txt "%PREFIX%"\Library\include\Arduino\nanopb\src
