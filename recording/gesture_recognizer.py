"""
apex/recording/gesture_recognizer.py
Recognizes higher-level gestures (Click, Double Click, Press & Hold, Click-n-Drag, Glide, Scroll)
while preserving the underlying raw recorded events.
"""
import math


class GestureRecognizer:
    @staticmethod
    def classify_mouse_press_release(sx, sy, ex, ey, duration_sec, moved_during_press=False):
        dist = math.hypot(ex - sx, ey - sy)
        if (moved_during_press and dist > 10) or dist > 15:
            return "Click-n-Drag (Move while Holding)"
        if duration_sec >= 0.25:
            return "Press & Hold"
        return "Click"
