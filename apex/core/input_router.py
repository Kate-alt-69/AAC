"""
Target-window-first input route selection.

WINDOW_MESSAGES is target-HWND scoped and best-effort.
FOREGROUND_SENDINPUT is a guarded shared desktop input stream, never background
or isolated input. It is selected for targets expected to consume Raw Input,
DirectInput, or modern foreground-only input.
"""
from apex.core.capability_registry import CapabilityRegistry


class InputRouter:
    MODE_TARGET_SESSION = "TARGET_SESSION"
    MODE_DESKTOP = "DESKTOP_MODE"

    ROUTE_WINDOW_MESSAGES = "WINDOW_MESSAGES"
    ROUTE_FOREGROUND_SENDINPUT = "FOREGROUND_SENDINPUT"

    def __init__(self):
        self.mode = self.MODE_TARGET_SESSION
        self.last_routing_warning = None

    def select_route(
        self,
        hwnd,
        title="",
        class_name="",
        client_size=(1280, 720),
        executable="",
        force_foreground=False,
    ):
        profile = CapabilityRegistry.inspect(
            hwnd, title, class_name, client_size, executable=executable
        )
        caps = profile.capabilities

        if self.mode == self.MODE_DESKTOP or force_foreground:
            route = self.ROUTE_FOREGROUND_SENDINPUT
        elif caps.get("requires_foreground") or not caps.get("window_message_input"):
            route = self.ROUTE_FOREGROUND_SENDINPUT
        else:
            route = self.ROUTE_WINDOW_MESSAGES

        if route == self.ROUTE_WINDOW_MESSAGES:
            self.last_routing_warning = (
                "Target-HWND messages are queued without moving the physical cursor. "
                "The application may ignore them; delivery is not acknowledged."
            )
        else:
            self.last_routing_warning = (
                f"'{profile.title}' requires foreground input. Apex will revalidate the "
                "locked HWND before every SendInput call; the physical desktop cursor/input "
                "stream is shared and cannot remain isolated in the background."
            )
        return route, profile
