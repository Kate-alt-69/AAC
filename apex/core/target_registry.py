"""
apex/core/target_registry.py
Tracks runtime window references, application identities, and active target sessions.
"""

class TargetRegistry:
    def __init__(self):
        self._targets = {}
        self._active_session_id = None

    def register_target(self, window_handle, title, class_name="", executable="", client_size=(1280, 720), profile_id="default"):
        ref_id = f"win_{window_handle}" if window_handle else f"prof_{profile_id}"
        entry = {
            "reference_id": ref_id,
            "hwnd": window_handle,
            "title": title or "Target Application",
            "class_name": class_name,
            "executable": executable,
            "client_size": list(client_size),
            "profile_id": profile_id
        }
        self._targets[ref_id] = entry
        self._active_session_id = ref_id
        return entry

    def get_active_target(self):
        if self._active_session_id and self._active_session_id in self._targets:
            return self._targets[self._active_session_id]
        return None

    def list_targets(self):
        return list(self._targets.values())
