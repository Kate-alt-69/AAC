@echo off
setlocal
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "TARGET=all"
set "FORMAT=all"
set "CLEAN="
:parse
if "%~1"=="" goto run
if /I "%~1"=="--target" (set "TARGET=%~2" & shift & shift & goto parse)
if /I "%~1"=="--installer-format" (set "FORMAT=%~2" & shift & shift & goto parse)
if /I "%~1"=="--clean" (set "CLEAN=--clean" & shift & goto parse)
echo Unknown argument: %~1
exit /b 2
:run
pushd "%ROOT%"
if not defined APEX_PYTHON set "APEX_PYTHON=python"
"%APEX_PYTHON%" build_backend.py --platform windows --target "%TARGET%" --installer-format "%FORMAT%" %CLEAN%
set "RESULT=%ERRORLEVEL%"
popd
exit /b %RESULT%
