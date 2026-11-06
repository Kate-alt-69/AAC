"""
apex/recording/target_attribution.py
Per-event dynamic target window attribution (identifies which window received each interaction).
"""
from apex.core.capability_registry import CapabilityRegistry


class TargetAttributor:
    @staticmethod
    def attribute(hwnd, title, class_name, client_size=(1280, 720)):
        profile = CapabilityRegistry.inspect(hwnd, title, class_name, client_size)
        return {
            "profile": profile.profile_id,
            "window": f"hwnd_{hwnd}" if hwnd else "runtime-window-reference",
            "title": profile.title,
            "class_name": profile.window_class,
            "adapter": profile.adapter_type,
            "recorded_dimensions": list(client_size)
        }, profile
