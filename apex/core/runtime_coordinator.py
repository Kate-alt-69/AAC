"""
apex/core/runtime_coordinator.py
Central Coordinator connecting the 4 independent runtime streams:
  1. Physical Input Stream
  2. Application Observation Stream
  3. Automation Execution Stream
  4. Virtual Feedback Stream
"""
from apex.core.coordinate_spaces import CoordinateSpace, CoordinateConverter
from apex.core.geometry import Vertex2D, Vector2D
from apex.core.event_model import InteractionEvent
from apex.core.target_registry import TargetRegistry
from apex.core.capability_registry import CapabilityRegistry
from apex.core.input_router import InputRouter
from apex.core.safety_manager import SafetyManager
from apex.core.action_scheduler import ActionScheduler


class RuntimeCoordinator:
    def __init__(self):
        self.target_registry = TargetRegistry()
        self.input_router = InputRouter()
        self.safety_manager = SafetyManager()
        self.scheduler = ActionScheduler()

    def build_event(self, timestamp, category, action_type, hwnd, title, class_name,
                    client_size, start_cx, start_cy, end_cx=None, end_cy=None,
                    duration_ms=50, extra_data=None):
        w, h = max(1, int(client_size[0])), max(1, int(client_size[1]))
        profile = CapabilityRegistry.inspect(hwnd, title, class_name, (w, h))
        v0 = Vertex2D.from_client(start_cx, start_cy, w, h)
        v1 = Vertex2D.from_client(end_cx if end_cx is not None else start_cx,
                                  end_cy if end_cy is not None else start_cy, w, h)
        target_info = {
            "profile": profile.profile_id,
            "window": f"hwnd_{hwnd}" if hwnd else "runtime-window-reference",
            "title": profile.title,
            "class_name": profile.window_class,
            "adapter": profile.adapter_type,
            "recorded_dimensions": [w, h]
        }
        evt = InteractionEvent(
            timestamp=timestamp,
            target_info=target_info,
            category=category,
            action_type=action_type,
            start_vertex=v0,
            end_vertex=v1,
            duration_ms=duration_ms,
            coordinate_space=CoordinateSpace.WINDOW_NORMALIZED,
            data=extra_data
        )
        return evt.to_dict()

    def resolve_coordinates(self, event_dict, current_width, current_height):
        w, h = max(1, int(current_width)), max(1, int(current_height))
        verts = event_dict.get("vertices")
        if verts and "start" in verts:
            u0, v0 = verts["start"]
            u1, v1 = verts.get("end", [u0, v0])
            sx, sy = CoordinateConverter.normalized_to_client(u0, v0, w, h)
            ex, ey = CoordinateConverter.normalized_to_client(u1, v1, w, h)
            return sx, sy, ex, ey
        d = event_dict.get("data", {})
        return d.get("x", 0), d.get("y", 0), d.get("end_x", d.get("x", 0)), d.get("end_y", d.get("y", 0))
