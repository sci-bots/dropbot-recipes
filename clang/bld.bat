@echo off
setlocal ENABLEDELAYEDEXPANSION

set URL=http://llvm.org/releases/%PKG_VERSION%/LLVM-%PKG_VERSION%-win32.exe

echo %URL%

REM Download Windows (32-bit) binary.
curl -L -o LLVM-%PKG_VERSION%-win32.exe %URL%
if errorlevel 1 exit 1
REM Extract $_OUTDIR\bin\libclang.dll from LZMA archive.
%PREFIX%\Library\usr\lib\p7zip\7z.exe e LLVM-%PKG_VERSION%-win32.exe libclang.dll -y -r
if errorlevel 1 exit 1
REM Copy libclang.dll to ${PREFIX}\Library\bin\libclang.dll.
copy libclang.dll "%PREFIX%"\Library\bin\libclang.dll
if errorlevel 1 exit 1

endlocal
