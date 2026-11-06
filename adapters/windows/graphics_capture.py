"""
apex/adapters/windows/graphics_capture.py
Windows Graphics Capture (WGC) & PrintWindow PW_RENDERFULLCONTENT frame observation pipeline.
"""

class WindowsGraphicsCaptureAdapter:
    PW_RENDERFULLCONTENT = 0x00000002

    @staticmethod
    def describe_pipeline():
        return "Windows Graphics Capture / PrintWindow(PW_RENDERFULLCONTENT)"
