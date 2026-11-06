"""
apex/adapters/base.py
Base Adapter Contract for the Apex Application Compatibility Layer (AACL).
Macro Studio communicates with the Runtime, and the Runtime communicates with these adapters.
"""

class BaseApplicationAdapter:
    adapter_name = "BASE_ADAPTER"

    def get_capabilities(self):
        return {
            "background_input": False,
            "uia_scroll_pattern": False,
            "adaptive_scroll": False,
            "requires_foreground": True
        }

    def send_mouse_click(self, hwnd, client_x, client_y, button="left", hold_sec=0.04):
        raise NotImplementedError

    def send_mouse_drag(self, hwnd, start_xy, end_xy, button="left", duration_sec=0.4):
        raise NotImplementedError

    def send_key_hold(self, hwnd, key_str, duration_sec=0.1, modifiers=None):
        raise NotImplementedError

    def send_scroll(self, hwnd, client_x, client_y, dx=0, dy=-2):
        raise NotImplementedError
