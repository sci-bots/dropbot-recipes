REM Copy protoc.exe to ${PREFIX}\Library\bin
copy bin\protoc.exe "%PREFIX%"\Library\bin\protoc.exe
if errorlevel 1 exit 1
xcopy /S /Y /I /Q include\google "%PREFIX%"\Library\include\google
if errorlevel 1 exit 1
