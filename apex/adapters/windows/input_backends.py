"""
apex/adapters/windows/input_backends.py
Windows Input Backends:
  1. TargetSessionMessageBackend (ChildWindowFromPointEx + PostMessageW for Notepad/Win32)
  2. ForegroundSendInputBackend  (Hardware mouse_event / SendInput for Desktop Mode & DirectX Games)
"""
import sys

IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    import ctypes


class WindowsInputBackends:
    @staticmethod
    def make_lparam(cx, cy):
        return ((int(cy) & 0xFFFF) << 16) | (int(cx) & 0xFFFF)

    @staticmethod
    def hardware_click(button="left"):
        if IS_WINDOWS:
            flags = 0x0002 | 0x0004 if button == "left" else (0x0008 | 0x0010 if button == "right" else 0x0020 | 0x0040)
            ctypes.windll.user32.mouse_event(flags, 0, 0, 0, 0)
            return True
        return False
