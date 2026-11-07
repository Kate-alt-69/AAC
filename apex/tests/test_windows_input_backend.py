"""Focused tests for target-HWND input ownership."""
import unittest
from unittest.mock import patch

from apex.adapters.windows.input_backends import (
    InputDispatchReceipt,
    WindowMessageInputBackend,
)
from apex.adapters.windows.target_session import TargetWindowError


class FakeTargetSession:
    hwnd = 1

    def __init__(self):
        self.focus = 101
        self.allowed = {1, 101, 102}

    def validate(self):
        return 200, 100

    def validate_input_target(self, hwnd):
        target = int(hwnd)
        if target not in self.allowed:
            raise TargetWindowError("input target escaped locked window")
        return target

    def clamp_point(self, x, y):
        return max(0, min(int(x), 199)), max(0, min(int(y), 99))

    def child_at_client_point(self, x, y):
        if int(x) < 50:
            return 101, int(x), int(y)
        return 102, int(x) - 50, int(y)

    def client_to_screen(self, x, y):
        return int(x) + 1000, int(y) + 2000

    def screen_to_client(self, hwnd, x, y):
        if int(hwnd) == 102:
            return int(x) - 1050, int(y) - 2000
        return int(x) - 1000, int(y) - 2000

    def point_for_target(self, hwnd, x, y):
        self.validate_input_target(hwnd)
        sx, sy = self.client_to_screen(x, y)
        return self.screen_to_client(hwnd, sx, sy)

    def focused_control(self):
        return self.focus

    @staticmethod
    def pack_client_lparam(x, y):
        return ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)

    @staticmethod
    def pack_screen_lparam(x, y):
        return ((int(y) & 0xFFFF) << 16) | (int(x) & 0xFFFF)

    @staticmethod
    def pack_wheel_wparam(delta, key_state=0):
        return ((int(delta) & 0xFFFF) << 16) | (int(key_state) & 0xFFFF)


class TestWindowMessageInputBackend(unittest.TestCase):
    def make_backend(self):
        session = FakeTargetSession()
        backend = WindowMessageInputBackend(session)
        calls = []

        def record(hwnd, msg, wparam, lparam):
            session.validate_input_target(hwnd)
            calls.append((hwnd, msg, wparam, lparam))
            return InputDispatchReceipt(
                route=WindowMessageInputBackend.ROUTE,
                status="QUEUED_UNVERIFIED",
                target_hwnd=int(hwnd),
                message="test receipt",
            )

        backend._post = record
        return session, backend, calls

    def test_drag_keeps_original_child_until_button_up(self):
        _session, backend, calls = self.make_backend()

        backend.button_down(10, 20, "left")
        backend.mouse_move(75, 25)
        backend.button_up(90, 30, "left")

        self.assertEqual([item[0] for item in calls], [101, 101, 101])
        self.assertEqual([item[1] for item in calls], [
            backend.WM_LBUTTONDOWN, backend.WM_MOUSEMOVE, backend.WM_LBUTTONUP
        ])
        self.assertFalse(backend.mouse_capture_targets)

    def test_key_up_uses_original_focused_child(self):
        session, backend, calls = self.make_backend()

        backend.key_down(0x41, 0x1E)
        session.focus = 102
        backend.key_up(0x41, 0x1E)

        self.assertEqual([item[0] for item in calls], [101, 101])
        self.assertEqual([item[1] for item in calls], [backend.WM_KEYDOWN, backend.WM_KEYUP])
        self.assertFalse(backend.pressed_keys)

    def test_scroll_targets_child_under_virtual_pointer(self):
        session, backend, calls = self.make_backend()
        session.focus = 101

        backend.scroll(80, 40, dy=-1)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], 102)
        self.assertEqual(calls[0][1], backend.WM_MOUSEWHEEL)

    def test_release_all_releases_original_press_targets(self):
        session, backend, calls = self.make_backend()

        backend.button_down(10, 20, "left")
        backend.key_down(0x41, 0x1E)
        session.focus = 102
        backend.mouse_move(75, 25)
        with patch("apex.adapters.windows.input_backends.IS_WINDOWS", True):
            backend.release_all()

        self.assertEqual(calls[-2][0], 101)
        self.assertEqual(calls[-2][1], backend.WM_LBUTTONUP)
        self.assertEqual(calls[-1][0], 101)
        self.assertEqual(calls[-1][1], backend.WM_KEYUP)
        self.assertFalse(backend.pressed_buttons)
        self.assertFalse(backend.pressed_keys)

    def test_key_up_keeps_recorded_scan_code(self):
        _session, backend, calls = self.make_backend()

        backend.key_down(0x41, 0x1E)
        backend.key_up(0x41, 0x30)

        down_scan = (calls[0][3] >> 16) & 0xFF
        up_scan = (calls[1][3] >> 16) & 0xFF
        self.assertEqual(down_scan, 0x1E)
        self.assertEqual(up_scan, 0x1E)

    def test_non_windows_cleanup_clears_virtual_press_ownership(self):
        _session, backend, _calls = self.make_backend()
        backend.pressed_buttons.add("left")
        backend.mouse_capture_targets["left"] = 101
        backend.pressed_keys[0x41] = (0x1E, 0, 101)

        with patch("apex.adapters.windows.input_backends.IS_WINDOWS", False):
            backend.release_all()

        self.assertFalse(backend.pressed_buttons)
        self.assertFalse(backend.mouse_capture_targets)
        self.assertFalse(backend.pressed_keys)

    def test_foreign_child_is_rejected(self):
        _session, backend, _calls = self.make_backend()
        with self.assertRaises(TargetWindowError):
            backend._validate_target(999)


if __name__ == "__main__":
    unittest.main()
