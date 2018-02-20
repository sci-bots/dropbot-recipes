@echo off
:: Make `LinkedList` directory (and parent directories, if necessary).
setlocal enableextensions
md "%PREFIX%"\Library\include\Arduino\LinkedList
endlocal

:: Copy library source files into Arduino library directory.
xcopy /S /Y /I /Q "%SRC_DIR%" "%PREFIX%"\Library\include\Arduino\LinkedList
del "%PREFIX%"\Library\include\Arduino\LinkedList\bld.bat
if errorlevel 1 exit 1
