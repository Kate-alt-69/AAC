"""
apex/runtime/virtual_cursor.py
Stream 4 (Virtual Feedback Stream): Virtual Cursor state machine (HOVER, DOWN, DRAG, SCROLL).
"""

class VirtualCursorState:
    def __init__(self):
        self.u = 0.5
        self.v = 0.5
        self.client_x = 100
        self.client_y = 100
        self.state = "HOVER"
        self.active_key_badge = ""
        self.drag_trail = []

    def update(self, cx, cy, width, height, state=None, key_badge=None):
        self.client_x = int(cx)
        self.client_y = int(cy)
        self.u = round(float(cx) / float(max(1, width)), 5)
        self.v = round(float(cy) / float(max(1, height)), 5)
        if state is not None:
            self.state = state
        if key_badge is not None:
            self.active_key_badge = key_badge
