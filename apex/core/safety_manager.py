"""
apex/core/safety_manager.py
Runtime Safety Manager: Tracks held keys & mouse buttons and guarantees emergency release on stop/error.
"""

class SafetyManager:
    def __init__(self):
        self.held_keys = set()
        self.held_buttons = set()

    def track_key_down(self, key_str):
        self.held_keys.add(str(key_str))

    def track_key_up(self, key_str):
        self.held_keys.discard(str(key_str))

    def track_button_down(self, button_str):
        self.held_buttons.add(str(button_str))

    def track_button_up(self, button_str):
        self.held_buttons.discard(str(button_str))

    def emergency_release_all(self, release_key_fn=None, release_btn_fn=None):
        released_k = list(self.held_keys)
        released_b = list(self.held_buttons)
        for k in released_k:
            try:
                if release_key_fn:
                    release_key_fn(k)
            except Exception:
                pass
        self.held_keys.clear()
        for b in released_b:
            try:
                if release_btn_fn:
                    release_btn_fn(b)
            except Exception:
                pass
        self.held_buttons.clear()
        return released_k, released_b
