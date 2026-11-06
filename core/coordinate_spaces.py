"""
apex/core/coordinate_spaces.py
Explicit Coordinate Frame System (Never guesses coordinate types!).
Supports:
  1. SCREEN            - Physical desktop coordinates (px)
  2. WINDOW_CLIENT     - Position relative to target application's client area (px)
  3. WINDOW_NORMALIZED - Resolution-independent relative coordinates U, V in [0.0, 1.0]
  4. ELEMENT_RELATIVE  - Position relative to a recognized UIA / DOM semantic element
"""

class CoordinateSpace:
    SCREEN = "SCREEN"
    WINDOW_CLIENT = "WINDOW_CLIENT"
    WINDOW_NORMALIZED = "WINDOW_NORMALIZED"
    ELEMENT_RELATIVE = "ELEMENT_RELATIVE"

    ALL_SPACES = (SCREEN, WINDOW_CLIENT, WINDOW_NORMALIZED, ELEMENT_RELATIVE)

    @classmethod
    def validate(cls, space):
        if space not in cls.ALL_SPACES:
            raise ValueError(f"Explicit coordinate_space required! Got invalid: {space}")
        return space


class CoordinateConverter:
    """Explicit conversion between SCREEN, WINDOW_CLIENT, WINDOW_NORMALIZED, and ELEMENT_RELATIVE."""
    @staticmethod
    def screen_to_client(screen_x, screen_y, origin_x, origin_y, width, height, clamp=True):
        cx = int(screen_x) - int(origin_x)
        cy = int(screen_y) - int(origin_y)
        if clamp:
            w, h = max(1, int(width)), max(1, int(height))
            cx = max(0, min(cx, w - 1))
            cy = max(0, min(cy, h - 1))
        return cx, cy

    @staticmethod
    def client_to_screen(client_x, client_y, origin_x, origin_y, width, height, clamp=True):
        w, h = max(1, int(width)), max(1, int(height))
        cx, cy = int(client_x), int(client_y)
        if clamp:
            cx = max(0, min(cx, w - 1))
            cy = max(0, min(cy, h - 1))
        return int(origin_x) + cx, int(origin_y) + cy

    @staticmethod
    def client_to_normalized(client_x, client_y, width, height):
        w = max(1, int(width))
        h = max(1, int(height))
        u = max(0.0, min(1.0, float(client_x) / float(w)))
        v = max(0.0, min(1.0, float(client_y) / float(h)))
        return round(u, 5), round(v, 5)

    @staticmethod
    def normalized_to_client(u, v, current_width, current_height):
        w = max(1, int(current_width))
        h = max(1, int(current_height))
        cx = int(round(max(0.0, min(1.0, float(u))) * w))
        cy = int(round(max(0.0, min(1.0, float(v))) * h))
        return max(0, min(cx, w - 1)), max(0, min(cy, h - 1))

    @staticmethod
    def element_to_client(rel_u, rel_v, elem_rect):
        """Resolves ELEMENT_RELATIVE (u, v) inside an element bounding box (x, y, w, h)."""
        ex, ey, ew, eh = elem_rect
        cx = int(ex) + int(round(float(rel_u) * max(1, int(ew))))
        cy = int(ey) + int(round(float(rel_v) * max(1, int(eh))))
        return cx, cy
