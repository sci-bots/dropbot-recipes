@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Remove "." characters from package version, e.g., "3.9.0" -> "390".
set RELEASE=%PKG_VERSION:.=%
REM Remove trailing zero from release number, e.g., "390" -> "39".
set RELEASE=%RELEASE:~0,-1%

set OUTPUT_DIR=%SP_DIR%\clang

REM Download clang release from here.
curl -L -o clang-release.zip https://github.com/llvm-mirror/clang/archive/release_%RELEASE%.zip
if errorlevel 1 exit 1
"%PREFIX%\Library\usr\lib\p7zip\7z.exe" x clang-release.zip "*/bindings/python" -r -y
if errorlevel 1 exit 1

mkdir "%OUTPUT_DIR%"
if errorlevel 1 exit 1
copy clang-release_%RELEASE%\bindings\python\clang "%OUTPUT_DIR%"
if errorlevel 1 exit 1

endlocal
