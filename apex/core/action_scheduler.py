"""
apex/core/action_scheduler.py
High-Precision Zero-Drift Action Scheduler with bounded event queues.
"""
import time


class ActionScheduler:
    @staticmethod
    def wait_until(clock_start, target_offset_sec, speed_mult=1.0, stop_event=None):
        if speed_mult >= 900.0:
            return
        target_time = clock_start + (float(target_offset_sec) / max(0.05, float(speed_mult)))
        while time.perf_counter() < target_time:
            if stop_event and stop_event.is_set():
                break
            rem = target_time - time.perf_counter()
            if rem > 0.003:
                time.sleep(rem * 0.75)
