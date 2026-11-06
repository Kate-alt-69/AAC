"""
apex/adapters/linux/wayland.py
Linux Wayland Backend (XDG RemoteDesktop Portal & libei permission-aware input).
"""

class LinuxWaylandPortalAdapter:
    backend_name = "LINUX_WAYLAND_PORTAL"

    @staticmethod
    def get_capabilities():
        return {
            "background_input": False,
            "portal_permission_required": True,
            "input_backend": "org.freedesktop.portal.RemoteDesktop / libei",
            "frame_capture": "org.freedesktop.portal.ScreenCast + PipeWire",
            "requires_foreground": True
        }
