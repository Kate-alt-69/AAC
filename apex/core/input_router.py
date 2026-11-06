"""
apex/core/input_router.py
Routes resolved automation commands to the appropriate AACL Adapter based on Execution Mode
(TARGET_SESSION vs DESKTOP_MODE) and reports limitations explicitly instead of silently hijacking the cursor.
"""
from apex.core.capability_registry import CapabilityRegistry


class InputRouter:
    MODE_TARGET_SESSION = "TARGET_SESSION"
    MODE_DESKTOP = "DESKTOP_MODE"

    def __init__(self):
        self.mode = self.MODE_TARGET_SESSION
        self.last_routing_warning = None

    def select_route(self, hwnd, title="", class_name="", client_size=(1280, 720)):
        profile = CapabilityRegistry.inspect(hwnd, title, class_name, client_size)
        caps = profile.capabilities

        if self.mode == self.MODE_TARGET_SESSION and caps.get("requires_foreground", False):
            self.last_routing_warning = (
                f"Target '{profile.title}' ({profile.adapter_type}) requires foreground hardware input "
                f"({caps.get('input_backend')}). Using DirectInput hardware synthesis."
            )
            return "FOREGROUND_HARDWARE", profile

        if self.mode == self.MODE_DESKTOP:
            return "DESKTOP_SENDINPUT", profile

        return "ISOLATED_SESSION_ADAPTER", profile
