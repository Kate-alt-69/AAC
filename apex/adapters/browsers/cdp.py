"""
apex/adapters/browsers/cdp.py
Chrome DevTools Protocol (CDP) Adapter for Chromium / Microsoft Edge DOM & Scroll inspection.
"""

class ChromiumCDPAdapter:
    protocol = "CDP_1.3"

    @staticmethod
    def build_scroll_metrics_expression():
        return "({scrollTop: document.scrollingElement.scrollTop, scrollHeight: document.scrollingElement.scrollHeight, clientHeight: document.scrollingElement.clientHeight})"
