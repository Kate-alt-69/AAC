"""Target-bound Windows input routes.

Window-message routing is isolated to the captured HWND but is best-effort:
PostMessage success means the message was queued, not that the app processed it.
Foreground SendInput is used only after the target HWND is verified as foreground.
It enters the shared desktop input stream and is not background isolation.
"""
from __future__ import annotations

import ctypes
import sys
import time
from dataclasses import dataclass
from typing import Optional

from apex.adapters.windows.target_session import (
    IS_WINDOWS,
    TargetWindowError,
    TargetWindowSession,
)

if IS_WINDOWS:
    from ctypes import wintypes


@dataclass(frozen=True)
class InputDispatchReceipt:
    route: str
    status: str
    target_hwnd: int
    message: str


class WindowMessageInputBackend:
    """Best-effort background route for applications that process standard HWND messages."""

    ROUTE = "WINDOW_MESSAGES"
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_CHAR = 0x0102
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105
    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MOUSEWHEEL = 0x020A
    WM_MOUSEHWHEEL = 0x020E

    MK_LBUTTON = 0x0001
    MK_RBUTTON = 0x0002
    MK_MBUTTON = 0x0010

    def __init__(self, session: TargetWindowSession):
        self.session = session
        self.pressed_buttons: set[str] = set()
        self.pressed_keys: dict[int, tuple[int, int]] = {}
        self.last_client_point = (0, 0)

    def _post(self, hwnd: int, msg: int, wparam: int, lparam: int) -> InputDispatchReceipt:
        if not IS_WINDOWS:
            raise TargetWindowError("Win32 window-message input is only available on Windows.")
        self.session.validate()
        ctypes.set_last_error(0)
        ok = ctypes.windll.user32.PostMessageW(
            int(hwnd), int(msg), int(wparam), int(lparam)
        )
        if not ok:
            error = int(ctypes.windll.kernel32.GetLastError())
            reason = ctypes.FormatError(error).strip() if error else "PostMessageW returned FALSE"
            raise TargetWindowError(
                f"Windows rejected target message 0x{msg:04X} for HWND {int(hwnd)}: {reason}"
            )
        return InputDispatchReceipt(
            route=self.ROUTE,
            status="QUEUED_UNVERIFIED",
            target_hwnd=int(hwnd),
            message=f"WM 0x{msg:04X} queued; target application processing is not acknowledged.",
        )

    def mouse_move(self, x: int, y: int, button_held: Optional[str] = None) -> InputDispatchReceipt:
        target, tx, ty = self.session.child_at_client_point(x, y)
        self.last_client_point = self.session.clamp_point(x, y)
        key_state = self.MK_LBUTTON if button_held == "left" else (
            self.MK_RBUTTON if button_held == "right" else (
                self.MK_MBUTTON if button_held == "middle" else 0
            )
        )
        return self._post(target, self.WM_MOUSEMOVE, key_state, self.session.pack_client_lparam(tx, ty))

    def button_down(self, x: int, y: int, button: str = "left") -> InputDispatchReceipt:
        target, tx, ty = self.session.child_at_client_point(x, y)
        messages = {
            "left": (self.WM_LBUTTONDOWN, self.MK_LBUTTON),
            "right": (self.WM_RBUTTONDOWN, self.MK_RBUTTON),
            "middle": (self.WM_MBUTTONDOWN, self.MK_MBUTTON),
        }
        msg, state = messages.get(button, messages["left"])
        receipt = self._post(target, msg, state, self.session.pack_client_lparam(tx, ty))
        self.pressed_buttons.add(button)
        self.last_client_point = self.session.clamp_point(x, y)
        return receipt

    def button_up(self, x: int, y: int, button: str = "left") -> InputDispatchReceipt:
        target, tx, ty = self.session.child_at_client_point(x, y)
        messages = {
            "left": (self.WM_LBUTTONUP, 0),
            "right": (self.WM_RBUTTONUP, 0),
            "middle": (self.WM_MBUTTONUP, 0),
        }
        msg, state = messages.get(button, messages["left"])
        receipt = self._post(target, msg, state, self.session.pack_client_lparam(tx, ty))
        self.pressed_buttons.discard(button)
        self.last_client_point = self.session.clamp_point(x, y)
        return receipt

    def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> list[InputDispatchReceipt]:
        sx, sy = self.session.client_to_screen(x, y)
        target = self.session.focused_control()
        receipts = []
        if dy:
            delta = int(round(float(dy) * 120))
            wparam = self.session.pack_wheel_wparam(delta)
            receipts.append(self._post(target, self.WM_MOUSEWHEEL, wparam, self.session.pack_screen_lparam(sx, sy)))
        if dx:
            delta = int(round(float(dx) * 120))
            wparam = self.session.pack_wheel_wparam(delta)
            receipts.append(self._post(target, self.WM_MOUSEHWHEEL, wparam, self.session.pack_screen_lparam(sx, sy)))
        return receipts

    def key_down(self, vk: int, scan: int = 0, *, system: bool = False, extended: bool = False,
                 char: Optional[str] = None) -> InputDispatchReceipt:
        target = self.session.focused_control()
        lparam = 1 | ((int(scan) & 0xFF) << 16)
        if extended:
            lparam |= 1 << 24
        if system:
            lparam |= 1 << 29
        shift_state = (
            (int(ctypes.windll.user32.VkKeyScanW(ord(char))) >> 8) & 0x01
            if IS_WINDOWS and char and len(char) == 1 else 0
        )
        auto_shift = bool(shift_state and 0x10 not in self.pressed_keys)
        if auto_shift:
            shift_scan = int(ctypes.windll.user32.MapVirtualKeyW(0x10, 0))
            self._post(target, self.WM_KEYDOWN, 0x10, 1 | ((shift_scan & 0xFF) << 16))
        receipt = self._post(target, self.WM_SYSKEYDOWN if system else self.WM_KEYDOWN, int(vk), lparam)
        if char and len(char) == 1 and not system:
            self._post(target, self.WM_CHAR, ord(char), lparam)
        if auto_shift:
            shift_scan = int(ctypes.windll.user32.MapVirtualKeyW(0x10, 0))
            shift_up = 1 | ((shift_scan & 0xFF) << 16) | (1 << 30) | (1 << 31)
            self._post(target, self.WM_KEYUP, 0x10, shift_up)
        self.pressed_keys[int(vk)] = (int(scan), 1 if extended else 0)
        return receipt

    def key_up(self, vk: int, scan: int = 0, *, system: bool = False, extended: bool = False) -> InputDispatchReceipt:
        target = self.session.focused_control()
        lparam = 1 | ((int(scan) & 0xFF) << 16) | (1 << 30) | (1 << 31)
        if extended:
            lparam |= 1 << 24
        if system:
            lparam |= 1 << 29
        receipt = self._post(target, self.WM_SYSKEYUP if system else self.WM_KEYUP, int(vk), lparam)
        self.pressed_keys.pop(int(vk), None)
        return receipt

    def key_hold(self, vk: int, scan: int = 0, duration: float = 0.1, stop_event=None,
                 *, system: bool = False, extended: bool = False, char: Optional[str] = None) -> None:
        self.key_down(vk, scan, system=system, extended=extended, char=char)
        deadline = time.perf_counter() + max(0.01, float(duration))
        try:
            while time.perf_counter() < deadline:
                if stop_event is not None and stop_event.is_set():
                    break
                time.sleep(min(0.025, max(0.001, deadline - time.perf_counter())))
        finally:
            self.key_up(vk, scan, system=system, extended=extended)

    def release_all(self) -> None:
        """Best-effort release of keys/buttons owned by this backend."""
        if not IS_WINDOWS:
            self.pressed_buttons.clear()
            self.pressed_keys.clear()
            return
        try:
            x, y = self.last_client_point
            for button in tuple(self.pressed_buttons):
                try:
                    self.button_up(x, y, button)
                except Exception:
                    self.pressed_buttons.discard(button)
            for vk, (scan, extended) in tuple(self.pressed_keys.items()):
                try:
                    self.key_up(vk, scan, extended=bool(extended))
                except Exception:
                    self.pressed_keys.pop(vk, None)
        except Exception:
            self.pressed_buttons.clear()
            self.pressed_keys.clear()


if IS_WINDOWS:
    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class _HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT), ("hi", _HARDWAREINPUT)]

    class _INPUT(ctypes.Structure):
        _anonymous_ = ("payload",)
        _fields_ = [("type", wintypes.DWORD), ("payload", _INPUTUNION)]

    _user32 = ctypes.windll.user32
    _user32.PostMessageW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    ]
    _user32.PostMessageW.restype = wintypes.BOOL
    _user32.SendInput.argtypes = [
        wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int
    ]
    _user32.SendInput.restype = wintypes.UINT
    _user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    _user32.GetSystemMetrics.restype = ctypes.c_int


class ForegroundSendInputBackend:
    """Real input-stream fallback, guarded by a fresh foreground HWND check per event."""

    ROUTE = "FOREGROUND_SENDINPUT"
    INPUT_MOUSE = 0
    INPUT_KEYBOARD = 1
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_HWHEEL = 0x1000
    MOUSEEVENTF_VIRTUALDESK = 0x4000
    MOUSEEVENTF_ABSOLUTE = 0x8000
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002

    def __init__(self, session: TargetWindowSession):
        self.session = session
        self.pressed_buttons: set[str] = set()
        self.pressed_keys: set[int] = set()
        self.shifted_keys: set[int] = set()

    def _send(self, inputs: list) -> InputDispatchReceipt:
        if not IS_WINDOWS:
            raise TargetWindowError("SendInput is only available on Windows.")
        self.session.require_foreground()
        array_type = _INPUT * len(inputs)
        array = array_type(*inputs)
        ctypes.set_last_error(0)
        sent = int(ctypes.windll.user32.SendInput(len(inputs), array, ctypes.sizeof(_INPUT)))
        if sent != len(inputs):
            error = int(ctypes.windll.kernel32.GetLastError())
            reason = ctypes.FormatError(error).strip() if error else "SendInput inserted fewer events than requested (possibly blocked by UIPI)"
            raise TargetWindowError(f"Foreground input was rejected ({sent}/{len(inputs)}): {reason}")
        return InputDispatchReceipt(
            route=self.ROUTE,
            status="INSERTED_IN_SHARED_INPUT_STREAM",
            target_hwnd=self.session.hwnd,
            message="Input inserted into the shared desktop input stream after verifying the target was foreground.",
        )

    def _mouse(self, flags: int, mouse_data: int = 0, x: int = 0, y: int = 0) -> _INPUT:
        item = _INPUT()
        item.type = self.INPUT_MOUSE
        item.mi = _MOUSEINPUT(int(x), int(y), int(mouse_data), int(flags), 0, 0)
        return item

    def _keyboard(self, vk: int, scan: int = 0, flags: int = 0) -> _INPUT:
        item = _INPUT()
        item.type = self.INPUT_KEYBOARD
        item.ki = _KEYBDINPUT(int(vk), int(scan), int(flags), 0, 0)
        return item

    def mouse_move(self, x: int, y: int, button_held: Optional[str] = None) -> InputDispatchReceipt:
        self.session.require_foreground()
        sx, sy = self.session.client_to_screen(x, y)
        user32 = ctypes.windll.user32
        vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
        vw, vh = max(1, user32.GetSystemMetrics(78)), max(1, user32.GetSystemMetrics(79))
        nx = max(0, min(65535, round((sx - vx) * 65535 / max(1, vw - 1))))
        ny = max(0, min(65535, round((sy - vy) * 65535 / max(1, vh - 1))))
        return self._send([self._mouse(
            self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE | self.MOUSEEVENTF_VIRTUALDESK,
            x=nx, y=ny
        )])

    def button_down(self, x: int, y: int, button: str = "left") -> InputDispatchReceipt:
        flags = {
            "left": self.MOUSEEVENTF_LEFTDOWN,
            "right": self.MOUSEEVENTF_RIGHTDOWN,
            "middle": self.MOUSEEVENTF_MIDDLEDOWN,
        }.get(button, self.MOUSEEVENTF_LEFTDOWN)
        receipt = self._send([self._mouse(flags)])
        self.pressed_buttons.add(button)
        return receipt

    def button_up(self, x: int, y: int, button: str = "left") -> InputDispatchReceipt:
        flags = {
            "left": self.MOUSEEVENTF_LEFTUP,
            "right": self.MOUSEEVENTF_RIGHTUP,
            "middle": self.MOUSEEVENTF_MIDDLEUP,
        }.get(button, self.MOUSEEVENTF_LEFTUP)
        receipt = self._send([self._mouse(flags)])
        self.pressed_buttons.discard(button)
        return receipt

    def scroll(self, x: int, y: int, dx: int = 0, dy: int = 0) -> list[InputDispatchReceipt]:
        receipts = []
        if dy:
            receipts.append(self._send([self._mouse(self.MOUSEEVENTF_WHEEL, mouse_data=int(dy * 120))]))
        if dx:
            receipts.append(self._send([self._mouse(self.MOUSEEVENTF_HWHEEL, mouse_data=int(dx * 120))]))
        return receipts

    def key_down(self, vk: int, scan: int = 0, *, system: bool = False, extended: bool = False,
                 char: Optional[str] = None) -> InputDispatchReceipt:
        flags = self.KEYEVENTF_EXTENDEDKEY if extended else 0
        inputs = []
        shift_state = (
            (int(ctypes.windll.user32.VkKeyScanW(ord(char))) >> 8) & 0x01
            if char and len(char) == 1 else 0
        )
        if shift_state and 0x10 not in self.pressed_keys:
            inputs.append(self._keyboard(0x10))
            self.pressed_keys.add(0x10)
            self.shifted_keys.add(int(vk))
        inputs.append(self._keyboard(vk, scan, flags))
        receipt = self._send(inputs)
        self.pressed_keys.add(int(vk))
        return receipt

    def key_up(self, vk: int, scan: int = 0, *, system: bool = False, extended: bool = False) -> InputDispatchReceipt:
        flags = self.KEYEVENTF_KEYUP | (self.KEYEVENTF_EXTENDEDKEY if extended else 0)
        inputs = [self._keyboard(vk, scan, flags)]
        if int(vk) in self.shifted_keys:
            inputs.append(self._keyboard(0x10, flags=self.KEYEVENTF_KEYUP))
            self.shifted_keys.discard(int(vk))
            self.pressed_keys.discard(0x10)
        receipt = self._send(inputs)
        self.pressed_keys.discard(int(vk))
        return receipt

    def key_hold(self, vk: int, scan: int = 0, duration: float = 0.1, stop_event=None,
                 *, system: bool = False, extended: bool = False, char: Optional[str] = None) -> None:
        self.key_down(vk, scan, system=system, extended=extended, char=char)
        deadline = time.perf_counter() + max(0.01, float(duration))
        try:
            while time.perf_counter() < deadline:
                if stop_event is not None and stop_event.is_set():
                    break
                time.sleep(min(0.025, max(0.001, deadline - time.perf_counter())))
        finally:
            self.key_up(vk, scan, system=system, extended=extended)

    def release_all(self) -> None:
        """Release only synthetic input owned by this backend, even after focus changes."""
        if not IS_WINDOWS:
            self.pressed_buttons.clear()
            self.pressed_keys.clear()
            return
        releases = []
        button_flags = {
            "left": self.MOUSEEVENTF_LEFTUP,
            "right": self.MOUSEEVENTF_RIGHTUP,
            "middle": self.MOUSEEVENTF_MIDDLEUP,
        }
        for button in tuple(self.pressed_buttons):
            releases.append(self._mouse(button_flags[button]))
        for vk in tuple(self.pressed_keys):
            releases.append(self._keyboard(vk, flags=self.KEYEVENTF_KEYUP))
        if releases:
            array_type = _INPUT * len(releases)
            array = array_type(*releases)
            ctypes.windll.user32.SendInput(len(releases), array, ctypes.sizeof(_INPUT))
        self.pressed_buttons.clear()
        self.pressed_keys.clear()
        self.shifted_keys.clear()


def create_backend(route: str, session: TargetWindowSession):
    if route == "WINDOW_MESSAGES":
        return WindowMessageInputBackend(session)
    if route == "FOREGROUND_SENDINPUT":
        return ForegroundSendInputBackend(session)
    raise TargetWindowError(f"Unsupported target input route: {route}")
