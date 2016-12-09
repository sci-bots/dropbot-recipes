REM Download Windows ragel binary.
"%PYTHON%" -m wget https://github.com/eloraiby/ragel-windows/raw/2e947e9c04e1cb98e99816b3ab4ab2a42926e8ff/ragel.exe
if errorlevel 1 exit 1
REM Copy protoc.exe to ${PREFIX}\Library\bin
copy ragel.exe "%PREFIX%"\Library\bin\ragel.exe
if errorlevel 1 exit 1
