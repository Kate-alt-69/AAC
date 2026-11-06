"""
apex/adapters/linux/x11.py
Linux X11 Backend (XTEST pointer/keyboard synthesis & X11 window geometry).
"""

class LinuxX11Adapter:
    backend_name = "LINUX_X11_XTEST"

    @staticmethod
    def get_capabilities():
        return {
            "background_input": True,
            "xtest_extension": True,
            "frame_capture": "XGetImage",
            "requires_foreground": False
        }
