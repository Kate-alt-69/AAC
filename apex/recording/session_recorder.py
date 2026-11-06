"""
apex/recording/session_recorder.py
Multi-application session recorder that maintains both raw events and compiled Studio blocks.
"""
import time
from apex.core.runtime_coordinator import RuntimeCoordinator


class SessionRecorder:
    def __init__(self, coordinator: RuntimeCoordinator = None):
        self.coordinator = coordinator or RuntimeCoordinator()
        self.raw_events = []
        self.start_time = 0.0
        self.is_recording = False

    def start(self):
        self.raw_events.clear()
        self.start_time = time.perf_counter()
        self.is_recording = True

    def stop(self):
        self.is_recording = False
        return list(self.raw_events)
