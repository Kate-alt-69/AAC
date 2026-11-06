@echo off
title Apex Auto-Clicker v11.0 - Modular .EXE Builder
color 0B
python -m pip install --upgrade pip
python -m pip install pynput pillow pyinstaller
python build_exe.py
pause
