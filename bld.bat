REM Download Windows (32-bit) binary.
"%PYTHON%" -m wget http://llvm.org/releases/3.9.0/LLVM-3.9.0-win32.exe
if errorlevel 1 exit 1
REM Extract $_OUTDIR\bin\libclang.dll from LZMA archive.
"%PREFIX%"\Library\usr\lib\p7zip\7z e LLVM-3.9.0-win32.exe libclang.dll -y -r
if errorlevel 1 exit 1
REM Copy libclang.dll to ${PREFIX}\Library\bin\libclang.dll.
copy libclang.dll "%PREFIX%"\Library\bin\libclang.dll
if errorlevel 1 exit 1
REM Download clang release from here.
"%PYTHON%" -m wget -o clang-release.zip https://github.com/llvm-mirror/clang/archive/release_39.zip
if errorlevel 1 exit 1
REM Copy bindings/python/clang to ${PREFIX}\Lib\site-packages\clang.
"%PREFIX%"\Library\usr\lib\p7zip\7z x clang-release.zip "*/bindings/python" -r -y
if errorlevel 1 exit 1
mkdir "%PREFIX%"\Lib\site-packages\clang
if errorlevel 1 exit 1
copy clang-release_39\bindings\python\clang "%PREFIX%"\Lib\site-packages\clang
if errorlevel 1 exit 1
