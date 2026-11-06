"""
apex/runtime/feedback_renderer.py
Renders Virtual Cursor, click animations, trajectories, and active key badges.
"""

class FeedbackRenderer:
    @staticmethod
    def get_cursor_color(state):
        return "#10893E" if state == "HOVER" else ("#E81123" if state == "DOWN" else "#FFB900")
