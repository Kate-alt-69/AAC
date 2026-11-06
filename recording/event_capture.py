"""
apex/recording/event_capture.py
Physical Input Stream observer: timestamps real mouse & keyboard events and filters sensitive fields.
"""
from apex.core.application_state import ApplicationStateProfile


class PhysicalEventCapture:
    @staticmethod
    def sanitize_key_if_sensitive(key_str, window_title="", element_name=""):
        if ApplicationStateProfile.is_sensitive_context(window_title, element_name):
            return "[REDACTED]"
        return key_str
