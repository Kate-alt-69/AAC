"""Stable identity and coordinate mapping for one target HWND.

This module does not inject code into the target process. It binds automation to a
captured top-level window identity and refuses to continue if that HWND is
destroyed, reused by another thread/process, or resized to an unusable client.
"""
from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass

IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    _user32.IsWindow.argtypes = [wintypes.HWND]
    _user32.IsWindow.restype = wintypes.BOOL
    _user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    _user32.GetAncestor.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetClientRect.restype = wintypes.BOOL
    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.GetWindowTextLengthW.restype = ctypes.c_int
    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetWindowTextW.restype = ctypes.c_int
    _user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetClassNameW.restype = ctypes.c_int
    _user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    _user32.ClientToScreen.restype = wintypes.BOOL
    _user32.ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    _user32.ScreenToClient.restype = wintypes.BOOL
    _user32.ChildWindowFromPointEx.argtypes = [wintypes.HWND, wintypes.POINT, wintypes.UINT]
    _user32.ChildWindowFromPointEx.restype = wintypes.HWND
    _user32.GetForegroundWindow.argtypes = []
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.IsIconic.argtypes = [wintypes.HWND]
    _user32.IsIconic.restype = wintypes.BOOL
    _user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    _user32.GetSystemMetrics.restype = ctypes.c_int
    _user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _user32.SetForegroundWindow.restype = wintypes.BOOL
    _user32.BringWindowToTop.argtypes = [wintypes.HWND]
    _user32.BringWindowToTop.restype = wintypes.BOOL
    _user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.ShowWindow.restype = wintypes.BOOL
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    _kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL


class TargetWindowError(RuntimeError):
    """The locked target window is no longer a valid automation target."""


@dataclass(frozen=True)
class WindowTargetSnapshot:
    hwnd: int
    process_id: int
    thread_id: int
    title: str
    class_name: str
    executable: str
    client_width: int
    client_height: int


class TargetWindowSession:
    """A stable, revalidated handle to one top-level application window."""

    GA_ROOT = 2
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    CWP_SKIPINVISIBLE = 0x0001
    CWP_SKIPDISABLED = 0x0002
    CWP_SKIPTRANSPARENT = 0x0004

    def __init__(self, snapshot: WindowTargetSnapshot):
        self.snapshot = snapshot
        self.hwnd = int(snapshot.hwnd)

    @staticmethod
    def clamp_client_point(x: int, y: int, width: int, height: int) -> tuple[int, int]:
        """Clamp a point to a half-open client rectangle."""
        return (
            max(0, min(int(x), max(0, int(width) - 1))),
            max(0, min(int(y), max(0, int(height) - 1))),
        )

    @staticmethod
    def resolve_normalized_point(u: float, v: float, width: int, height: int) -> tuple[int, int]:
        """Resolve a normalized [0, 1] vertex against current client dimensions."""
        w, h = max(1, int(width)), max(1, int(height))
        nx = max(0.0, min(1.0, float(u)))
        ny = max(0.0, min(1.0, float(v)))
        return round(nx * (w - 1)), round(ny * (h - 1))

    @staticmethod
    def pack_client_lparam(x: int, y: int) -> int:
        """Pack signed 16-bit client coordinates for WM_MOUSE* messages."""
        return ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)

    @staticmethod
    def pack_screen_lparam(x: int, y: int) -> int:
        """Pack signed screen coordinates for WM_MOUSEWHEEL / WM_MOUSEHWHEEL."""
        return ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)

    @staticmethod
    def pack_wheel_wparam(delta: int, key_state: int = 0) -> int:
        """Pack button/modifier state and signed wheel delta."""
        return ((int(delta) & 0xFFFF) << 16) | (int(key_state) & 0xFFFF)

    @classmethod
    def capture(cls, hwnd: int) -> "TargetWindowSession":
        if not IS_WINDOWS:
            raise TargetWindowError("Target-window Win32 input is only available on Windows.")
        if not hwnd:
            raise TargetWindowError("No target window is selected.")

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        candidate = int(hwnd)
        if not user32.IsWindow(candidate):
            raise TargetWindowError("The selected target window no longer exists.")

        root = int(user32.GetAncestor(candidate, cls.GA_ROOT) or candidate)
        pid = ctypes.c_ulong(0)
        tid = int(user32.GetWindowThreadProcessId(root, ctypes.byref(pid)))
        if not tid or not pid.value:
            raise TargetWindowError("Windows could not identify the target process/thread.")

        rect = wintypes.RECT()
        if not user32.GetClientRect(root, ctypes.byref(rect)):
            raise TargetWindowError("Windows could not read the target client rectangle.")
        width, height = int(rect.right - rect.left), int(rect.bottom - rect.top)
        if width < 1 or height < 1:
            raise TargetWindowError("The target window has no usable client area (it may be minimized).")

        title_len = int(user32.GetWindowTextLengthW(root))
        title_buf = ctypes.create_unicode_buffer(max(1, min(title_len + 1, 4096)))
        user32.GetWindowTextW(root, title_buf, len(title_buf))
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(root, class_buf, len(class_buf))

        executable = ""
        process = kernel32.OpenProcess(cls.PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if process:
            try:
                size = ctypes.c_ulong(32768)
                path_buf = ctypes.create_unicode_buffer(size.value)
                if kernel32.QueryFullProcessImageNameW(process, 0, path_buf, ctypes.byref(size)):
                    executable = path_buf.value
            finally:
                kernel32.CloseHandle(process)

        snapshot = WindowTargetSnapshot(
            hwnd=root,
            process_id=int(pid.value),
            thread_id=tid,
            title=title_buf.value,
            class_name=class_buf.value,
            executable=executable,
            client_width=width,
            client_height=height,
        )
        return cls(snapshot)

    def validate(self) -> tuple[int, int]:
        """Revalidate HWND identity and return its current client dimensions."""
        if not IS_WINDOWS:
            raise TargetWindowError("Target-window Win32 input is only available on Windows.")
        user32 = ctypes.windll.user32
        if not user32.IsWindow(self.hwnd):
            raise TargetWindowError("The locked target window was closed.")
        root = int(user32.GetAncestor(self.hwnd, self.GA_ROOT) or self.hwnd)
        if root != self.hwnd:
            raise TargetWindowError("The locked target HWND is no longer the same top-level window.")

        pid = ctypes.c_ulong(0)
        tid = int(user32.GetWindowThreadProcessId(self.hwnd, ctypes.byref(pid)))
        if int(pid.value) != self.snapshot.process_id or tid != self.snapshot.thread_id:
            raise TargetWindowError("The locked HWND was reused or now belongs to a different process/thread.")

        rect = wintypes.RECT()
        if not user32.GetClientRect(self.hwnd, ctypes.byref(rect)):
            raise TargetWindowError("The target client rectangle is unavailable.")
        width, height = int(rect.right - rect.left), int(rect.bottom - rect.top)
        if width < 1 or height < 1 or user32.IsIconic(self.hwnd):
            raise TargetWindowError("The target window is minimized or has no usable client area.")
        return width, height

    def validate_input_target(self, hwnd: int) -> int:
        """Ensure a message recipient is the locked top-level HWND or its child."""
        self.validate()
        target = int(hwnd or 0)
        user32 = ctypes.windll.user32
        if not target or not user32.IsWindow(target):
            raise TargetWindowError("The selected target control no longer exists.")
        root = int(user32.GetAncestor(target, self.GA_ROOT) or target)
        if root != self.hwnd:
            raise TargetWindowError(
                "Refusing input because the recipient is outside the locked target window."
            )
        return target

    def point_for_target(self, hwnd: int, client_x: int, client_y: int) -> tuple[int, int]:
        """Map a point in the root client area into a pinned child HWND's coordinates."""
        target = self.validate_input_target(hwnd)
        cx, cy = self.clamp_point(client_x, client_y)
        if target == self.hwnd:
            return cx, cy
        sx, sy = self.client_to_screen(cx, cy)
        return self.screen_to_client(target, sx, sy)

    def get_client_size(self) -> tuple[int, int]:
        return self.validate()

    def clamp_point(self, x: int, y: int) -> tuple[int, int]:
        width, height = self.validate()
        return self.clamp_client_point(x, y, width, height)

    def normalized_point(self, u: float, v: float) -> tuple[int, int]:
        width, height = self.validate()
        return self.resolve_normalized_point(u, v, width, height)

    def client_to_screen(self, x: int, y: int) -> tuple[int, int]:
        self.validate()
        point = wintypes.POINT(int(x), int(y))
        if not ctypes.windll.user32.ClientToScreen(self.hwnd, ctypes.byref(point)):
            raise TargetWindowError("ClientToScreen failed for the locked target.")
        return int(point.x), int(point.y)

    def screen_to_client(self, hwnd: int, x: int, y: int) -> tuple[int, int]:
        point = wintypes.POINT(int(x), int(y))
        if not ctypes.windll.user32.ScreenToClient(int(hwnd), ctypes.byref(point)):
            raise TargetWindowError("ScreenToClient failed while resolving a target child control.")
        return int(point.x), int(point.y)

    def child_at_client_point(self, x: int, y: int) -> tuple[int, int, int]:
        """Return deepest visible child HWND and coordinates relative to that child."""
        self.validate()
        cx, cy = self.clamp_point(x, y)
        sx, sy = self.client_to_screen(cx, cy)
        current = self.hwnd
        user32 = ctypes.windll.user32

        for _ in range(16):
            parent_x, parent_y = self.screen_to_client(current, sx, sy)
            pt = wintypes.POINT(parent_x, parent_y)
            child = int(user32.ChildWindowFromPointEx(
                current,
                pt,
                self.CWP_SKIPINVISIBLE | self.CWP_SKIPDISABLED | self.CWP_SKIPTRANSPARENT,
            ) or 0)
            if not child or child == current:
                break
            child_root = int(user32.GetAncestor(child, self.GA_ROOT) or child)
            if child_root != self.hwnd:
                break
            current = child

        target_x, target_y = self.screen_to_client(current, sx, sy)
        return current, target_x, target_y

    def focused_control(self) -> int:
        """Return the focused control owned by the target GUI thread, else its root."""
        self.validate()
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long),
            ]

        class GUITHREADINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong), ("flags", ctypes.c_ulong),
                ("hwndActive", ctypes.wintypes.HWND), ("hwndFocus", ctypes.wintypes.HWND),
                ("hwndCapture", ctypes.wintypes.HWND), ("hwndMenuOwner", ctypes.wintypes.HWND),
                ("hwndMoveSize", ctypes.wintypes.HWND), ("hwndCaret", ctypes.wintypes.HWND),
                ("rcCaret", RECT),
            ]

        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        user32 = ctypes.windll.user32
        user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
        user32.GetGUIThreadInfo.restype = wintypes.BOOL
        if user32.GetGUIThreadInfo(self.snapshot.thread_id, ctypes.byref(info)):
            focused = int(info.hwndFocus or 0)
            if focused and ctypes.windll.user32.IsWindow(focused):
                root = int(ctypes.windll.user32.GetAncestor(focused, self.GA_ROOT) or focused)
                if root == self.hwnd:
                    return focused
        return self.hwnd

    def is_foreground(self) -> bool:
        self.validate()
        foreground = int(ctypes.windll.user32.GetForegroundWindow() or 0)
        if not foreground:
            return False
        root = int(ctypes.windll.user32.GetAncestor(foreground, self.GA_ROOT) or foreground)
        return root == self.hwnd

    def activate(self) -> bool:
        """Request foreground activation, then verify it actually succeeded."""
        self.validate()
        user32 = ctypes.windll.user32
        if user32.IsIconic(self.hwnd):
            user32.ShowWindow(self.hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(self.hwnd)
        user32.SetForegroundWindow(self.hwnd)
        return self.is_foreground()

    def require_foreground(self) -> None:
        if not self.is_foreground():
            raise TargetWindowError(
                "This application requires foreground system input. The locked target is not currently foreground."
            )
