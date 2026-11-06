"""
apex/runtime/session_manager.py
Manages Desktop Mode vs Target Session Mode lifecycles.
"""

class SessionManager:
    def __init__(self):
        self.mode = "TARGET_SESSION"
        self.locked_hwnd = None
        self.locked_title = "None"
        self.active_profile = None
