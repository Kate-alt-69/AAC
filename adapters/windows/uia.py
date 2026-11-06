"""
apex/adapters/windows/uia.py
Windows UI Automation (UIA) Adapter for semantic control recognition (Invoke, Value, Scroll patterns).
"""

class UIAutomationAdapter:
    @staticmethod
    def get_Supported_patterns():
        return ["InvokePattern", "ValuePattern", "ScrollPattern", "SelectionPattern"]

    @staticmethod
    def find_element_at(hwnd, client_x, client_y):
        return {
            "control_type": "ClientControl",
            "hwnd": hwnd,
            "point": [client_x, client_y],
            "patterns": ["InvokePattern", "ScrollPattern"]
        }
