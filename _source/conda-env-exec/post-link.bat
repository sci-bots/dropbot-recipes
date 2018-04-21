REM Create `Scripts\conda.bat` if no conda command exists in `Scripts`.
@echo off
set CONDA_PATHS=where /F conda
for /f "delims=" %%a in ('where /F conda') do set "CONDA_EXE=%%a"&goto :stop
:stop
mkdir "%PREFIX%\Scripts"
set ENV_CONDA_EXE=%PREFIX%\Scripts\conda.bat
if exist "%PREFIX%\Scripts\conda.exe" (
  goto :skip
)
if exist "%PREFIX%\Scripts\conda.bat" (
  goto :skip
)
if not exist "%ENV_CONDA_EXE%" (
    echo @echo off > "%ENV_CONDA_EXE%"
    echo %CONDA_EXE% %%* >> "%ENV_CONDA_EXE%"
)
:skip
REM Create wrapped `conda`.
call "%PREFIX%\Scripts\.conda-wrappers-post-link.bat"
