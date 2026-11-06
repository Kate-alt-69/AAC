@echo off
setlocal
cd /d "%~dp0"
title Apex Auto-Clicker v1.1
py -3 apex_autoclicker.py
if errorlevel 1 pause
