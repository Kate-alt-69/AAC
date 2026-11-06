#!/usr/bin/env python3
import os, sys, subprocess, shutil

def build_executable():
    sep = ";" if sys.platform.startswith("win") else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--windowed",
        "--name", "ApexAutoClicker",
        "--add-data", f"apex{sep}apex",
        "--hidden-import", "apex.core.coordinate_spaces",
        "--hidden-import", "apex.core.geometry",
        "--hidden-import", "apex.core.event_model",
        "--hidden-import", "apex.core.target_registry",
        "--hidden-import", "apex.core.application_state",
        "--hidden-import", "apex.core.capability_registry",
        "--hidden-import", "apex.core.runtime_coordinator",
        "--hidden-import", "apex.core.input_router",
        "--hidden-import", "apex.core.action_scheduler",
        "--hidden-import", "apex.core.safety_manager",
        "--hidden-import", "apex.recording.event_capture",
        "--hidden-import", "apex.recording.target_attribution",
        "--hidden-import", "apex.recording.gesture_recognizer",
        "--hidden-import", "apex.recording.trajectory_recorder",
        "--hidden-import", "apex.recording.session_recorder",
        "--hidden-import", "apex.adapters.base",
        "--hidden-import", "apex.adapters.browsers.adaptive_scroll",
        "--hidden-import", "apex.adapters.custom.application_bridge",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.ImageGrab",
        "--hidden-import", "PIL.ImageTk",
        "apex_autoclicker.py"
    ]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        exe_name = "ApexAutoClicker.exe" if sys.platform.startswith("win") else "ApexAutoClicker"
        dist_p = os.path.join("dist", exe_name)
        if os.path.exists(dist_p):
            shutil.copy2(dist_p, exe_name)
            print("BUILD SUCCESSFUL:", os.path.abspath(exe_name))

if __name__ == "__main__":
    build_executable()
