"""
apex/core/application_state.py
Application State Profiles & Checkpoints with automatic sensitive/password field redaction.
"""

class ApplicationStateProfile:
    SENSITIVE_KEYWORDS = ("password", "passcode", "secret", "token", "cvv", "pin", "ssn", "bank", "login", "auth")

    def __init__(self, profile_id="notepad", executable="notepad.exe", window_class="Notepad",
                 title="Untitled - Notepad", client_size=(1280, 720), dpi_scale=1.0,
                 adapter_type="WIN32_UIA_ADAPTER", capabilities=None):
        self.profile_id = profile_id
        self.executable = executable
        self.window_class = window_class
        self.title = title
        self.client_size = tuple(client_size)
        self.dpi_scale = float(dpi_scale)
        self.adapter_type = adapter_type
        self.capabilities = capabilities or {}
        self.scroll_ratio = 0.0
        self.focused_element = None
        self.visual_anchors = []

    @classmethod
    def is_sensitive_context(cls, title="", element_name=""):
        text = f"{title} {element_name}".lower()
        return any(k in text for k in cls.SENSITIVE_KEYWORDS)

    def create_checkpoint(self, cursor_vertex=None, scroll_ratio=0.0):
        safe_title = "[REDACTED SENSITIVE WINDOW]" if self.is_sensitive_context(self.title) else self.title
        return {
            "profile_id": self.profile_id,
            "executable": self.executable,
            "window_class": self.window_class,
            "title": safe_title,
            "client_size": list(self.client_size),
            "dpi_scale": self.dpi_scale,
            "adapter_type": self.adapter_type,
            "scroll_ratio": round(float(scroll_ratio), 4),
            "cursor_vertex": cursor_vertex or [0.5, 0.5],
            "capabilities": self.capabilities
        }
