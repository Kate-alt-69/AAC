"""
apex/runtime/observation_stream.py
Stream 2 (Application Observation Stream): Asynchronous bounded frame & geometry observer.
"""
from collections import deque


class ApplicationObservationStream:
    def __init__(self, max_queue_size=4):
        self.frame_queue = deque(maxlen=max_queue_size)
        self.last_dimensions = (1280, 720)

    def push_observation(self, frame_data, dimensions):
        self.last_dimensions = tuple(dimensions)
        self.frame_queue.append({"frame": frame_data, "dimensions": self.last_dimensions})
