"""
apex/recording/trajectory_recorder.py
Records high-frequency cursor movement paths with sub-pixel jitter suppression.
"""
import math


class TrajectoryRecorder:
    def __init__(self, jitter_threshold_px=2.0):
        self.jitter_threshold_px = float(jitter_threshold_px)
        self.points = []

    def add_sample(self, x, y, timestamp):
        if not self.points:
            self.points.append((int(x), int(y), float(timestamp)))
            return True
        lx, ly, _ = self.points[-1]
        if math.hypot(x - lx, y - ly) >= self.jitter_threshold_px:
            self.points.append((int(x), int(y), float(timestamp)))
            return True
        return False
