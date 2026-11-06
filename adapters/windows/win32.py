"""
apex/adapters/windows/win32.py
Win32 API Window Discovery, Client Geometry & Coordinate Frame Clamping.
"""
import sys

IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes


class Win32WindowAdapter:
    @staticmethod
    def get_client_size(hwnd):
        if IS_WINDOWS and hwnd and ctypes.windll.user32.IsWindow(hwnd):
            rect = wintypes.RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            return max(100, rect.right - rect.left), max(100, rect.bottom - rect.top)
        return (1280, 720)

    @staticmethod
    def get_client_origin(hwnd):
        if IS_WINDOWS and hwnd and ctypes.windll.user32.IsWindow(hwnd):
            pt = wintypes.POINT(0, 0)
            ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
            return (pt.x, pt.y)
        return (0, 0)
