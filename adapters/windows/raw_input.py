"""
apex/adapters/windows/raw_input.py
Windows Raw Input & High-Frequency Hardware Cursor Polling.
"""
import sys

IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes


class RawInputReader:
    @staticmethod
    def get_cursor_pos():
        if IS_WINDOWS:
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return (pt.x, pt.y)
        return (0, 0)
