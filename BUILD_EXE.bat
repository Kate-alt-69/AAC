@echo off
setlocal
cd /d "%~dp0"
title Apex Auto-Clicker v1.1 - Build App and Installers
py -3 build.py --target all %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Build failed with exit code %RESULT%.
pause
exit /b %RESULT%
