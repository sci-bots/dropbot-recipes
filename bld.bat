REM Download Windows (32-bit) binary.
"%PYTHON%" -m wget https://github.com/google/protobuf/releases/download/v3.1.0/protoc-3.1.0-win32.zip
if errorlevel 1 exit 1
REM Extract $_OUTDIR\bin\libclang.dll from LZMA archive.
"%PREFIX%"\Library\bin\7za x protoc-3.1.0-win32.zip -y
if errorlevel 1 exit 1
REM Copy protoc.exe to ${PREFIX}\Library\bin
copy bin\protoc.exe "%PREFIX%"\Library\bin\protoc.exe
if errorlevel 1 exit 1
xcopy /S /Y /I /Q include\google "%PREFIX%"\Library\include\google
if errorlevel 1 exit 1
