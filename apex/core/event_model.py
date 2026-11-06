"""
apex/core/event_model.py
Dynamic Interaction Event Schema & Backward-Compatible Macro Migration Engine.
"""
from apex.core.coordinate_spaces import CoordinateSpace
from apex.core.geometry import Vertex2D, Vector2D


class InteractionEvent:
    """
    Represents a single context-aware interaction event with:
      - timestamp
      - target (profile, runtime window reference, recorded dimensions)
      - interaction (category: MOUSE/KEYBOARD/LOGIC, type: CLICK/DRAG/MOVE/SCROLL/KEY_HOLD)
      - coordinate_space (WINDOW_NORMALIZED, WINDOW_CLIENT, SCREEN, ELEMENT_RELATIVE)
      - vertices (start: [u0, v0], end: [u1, v1])
      - vector (du, dv, dx, dy)
      - duration_ms
      - raw_events (preserves underlying raw hardware events!)
    """
    SCHEMA_VERSION = "11.0"

    def __init__(self, timestamp, target_info, category, action_type,
                 start_vertex: Vertex2D, end_vertex: Vertex2D = None,
                 duration_ms=50, coordinate_space=CoordinateSpace.WINDOW_NORMALIZED,
                 data=None, raw_events=None):
        self.timestamp = round(float(timestamp), 5)
        self.target = target_info or {"profile": "desktop", "window": "root", "recorded_dimensions": [1280, 720]}
        self.category = category
        self.action_type = action_type
        self.coordinate_space = CoordinateSpace.validate(coordinate_space)
        self.start_vertex = start_vertex
        self.end_vertex = end_vertex or start_vertex
        self.vector = Vector2D.between(self.start_vertex, self.end_vertex)
        self.duration_ms = int(round(duration_ms))
        self.data = dict(data or {})
        self.raw_events = list(raw_events or [])

        # Keep legacy keys synced for backward compatibility
        self.data.setdefault("x", self.start_vertex.x)
        self.data.setdefault("y", self.start_vertex.y)
        if end_vertex:
            self.data.setdefault("end_x", self.end_vertex.x)
            self.data.setdefault("end_y", self.end_vertex.y)

    def to_dict(self):
        return {
            "schema_version": self.SCHEMA_VERSION,
            "time": self.timestamp,
            "timestamp": self.timestamp,
            "type": self.action_type,
            "target": self.target,
            "interaction": {
                "category": self.category,
                "type": self.action_type
            },
            "coordinate_space": self.coordinate_space,
            "vertices": {
                "start": self.start_vertex.to_list(),
                "end": self.end_vertex.to_list()
            },
            "vector": {
                "dx": self.vector.du,
                "dy": self.vector.dv,
                "du": self.vector.du,
                "dv": self.vector.dv,
                "px_dx": self.vector.dx,
                "px_dy": self.vector.dy
            },
            "duration_ms": self.duration_ms,
            "data": self.data,
            "raw_events": self.raw_events
        }

    @classmethod
    def migrate_legacy_dict(cls, raw_dict, default_dims=(1280, 720)):
        """Migrates v7.0 - v10.5 macro event dictionaries to the v11.0 schema without data loss."""
        if "vertices" in raw_dict and "coordinate_space" in raw_dict:
            return raw_dict
        t = raw_dict.get("time", raw_dict.get("timestamp", 0.0))
        atype = raw_dict.get("type", "MOUSE_MOVE")
        d = raw_dict.get("data", {})
        w, h = default_dims
        v0 = Vertex2D.from_client(d.get("x", 0), d.get("y", 0), w, h)
        v1 = Vertex2D.from_client(d.get("end_x", d.get("x", 0)), d.get("end_y", d.get("y", 0)), w, h)
        cat = "MOUSE" if "MOUSE" in atype else ("KEYBOARD" if "KEY" in atype else "LOGIC")
        dur_ms = int(float(d.get("duration", d.get("seconds", 0.05))) * 1000)
        evt = cls(
            timestamp=t,
            target_info=raw_dict.get("target", {"profile": "legacy_macro", "window": "runtime-window-reference", "recorded_dimensions": [w, h]}),
            category=cat,
            action_type=atype,
            start_vertex=v0,
            end_vertex=v1,
            duration_ms=dur_ms,
            data=d
        )
        return evt.to_dict()
