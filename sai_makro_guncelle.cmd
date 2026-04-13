@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for /f "delims=" %%i in ('wsl.exe wslpath "%SCRIPT_DIR%"') do set "WSL_DIR=%%i"
wsl.exe bash -lc "cd '%WSL_DIR%' && python3 makro.py guncelle %*"
