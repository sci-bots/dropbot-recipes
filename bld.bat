REM Download Windows ragel binary.
"%PYTHON%" -m wget https://www.colm.net/files/ragel/ragel-6.9-w32bin.zip
if errorlevel 1 exit 1
"%PREFIX%"\Library\bin\7za e ragel-6.9-w32bin.zip ragel.exe -r -y
if errorlevel 1 exit 1
REM Copy ragel.exe to ${PREFIX}\Library\bin
copy ragel.exe "%PREFIX%"\Library\bin\ragel.exe
if errorlevel 1 exit 1
