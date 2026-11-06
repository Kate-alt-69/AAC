"""
apex/adapters/browsers/adaptive_scroll.py
Dynamic Webpage & Container Scrolling Engine.
Computes normalized scroll progress:
    H_scroll = scrollHeight
    H_visible = clientHeight
    P = scrollTop / max(1, H_scroll - H_visible)
Recalculates scroll distance when viewport height, zoom, or lazy-loaded content changes!
"""

class AdaptiveScrollEngine:
    @staticmethod
    def calculate_scroll_ratio(scroll_top, scroll_height, client_height):
        scrollable_span = max(1, int(scroll_height) - int(client_height))
        return round(max(0.0, min(1.0, float(scroll_top) / float(scrollable_span))), 4)

    @staticmethod
    def resolve_target_scroll_top(target_ratio, current_scroll_height, current_client_height):
        scrollable_span = max(1, int(current_scroll_height) - int(current_client_height))
        return int(round(max(0.0, min(1.0, float(target_ratio))) * scrollable_span))

    @staticmethod
    def compute_adaptive_wheel_notches(recorded_dy, recorded_win_h, current_win_h):
        rec_h = max(100, int(recorded_win_h or 720))
        cur_h = max(100, int(current_win_h or 720))
        scaled = int(round(float(recorded_dy) * (float(cur_h) / float(rec_h))))
        if scaled == 0 and recorded_dy != 0:
            return 1 if recorded_dy > 0 else -1
        return scaled
