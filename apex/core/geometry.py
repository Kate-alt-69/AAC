"""
apex/core/geometry.py
Geometric primitives: Vertex2D P0=(u0,v0), Vector2D dP=P1-P0, and Trajectory curves.
"""
import math
import random
from apex.core.coordinate_spaces import CoordinateSpace, CoordinateConverter


class Vertex2D:
    """A recorded point P0 = (u0, v0) with explicit coordinate space."""
    def __init__(self, u=0.0, v=0.0, x=0, y=0, space=CoordinateSpace.WINDOW_NORMALIZED):
        self.space = CoordinateSpace.validate(space)
        self.u = round(float(u), 5)
        self.v = round(float(v), 5)
        self.x = int(x)
        self.y = int(y)

    @classmethod
    def from_client(cls, cx, cy, width, height):
        u, v = CoordinateConverter.client_to_normalized(cx, cy, width, height)
        return cls(u=u, v=v, x=int(cx), y=int(cy), space=CoordinateSpace.WINDOW_NORMALIZED)

    def resolve_to_client(self, current_width, current_height, elem_rect=None):
        if self.space == CoordinateSpace.ELEMENT_RELATIVE and elem_rect:
            return CoordinateConverter.element_to_client(self.u, self.v, elem_rect)
        if self.space == CoordinateSpace.WINDOW_NORMALIZED or (0.0 <= self.u <= 1.0 and (self.u > 0 or self.v > 0)):
            return CoordinateConverter.normalized_to_client(self.u, self.v, current_width, current_height)
        w, h = max(1, int(current_width)), max(1, int(current_height))
        return max(0, min(self.x, w - 1)), max(0, min(self.y, h - 1))

    def to_list(self):
        return [self.u, self.v]

    def to_dict(self):
        return {"u": self.u, "v": self.v, "x": self.x, "y": self.y, "space": self.space}


class Vector2D:
    """Movement displacement dP = P1 - P0."""
    def __init__(self, du=0.0, dv=0.0, dx=0, dy=0):
        self.du = round(float(du), 5)
        self.dv = round(float(dv), 5)
        self.dx = int(dx)
        self.dy = int(dy)

    @classmethod
    def between(cls, start_v: Vertex2D, end_v: Vertex2D):
        return cls(
            du=end_v.u - start_v.u,
            dv=end_v.v - start_v.v,
            dx=end_v.x - start_v.x,
            dy=end_v.y - start_v.y
        )

    def to_dict(self):
        return {"du": self.du, "dv": self.dv, "dx": self.dx, "dy": self.dy}


class TrajectoryGeometry:
    """Biomechanical Bézier, Bresenham, and Cubic Ease path generators."""
    @staticmethod
    def bresenham_line(x0, y0, x1, y1):
        points = []
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = int(x0), int(y0)
        while True:
            points.append((cx, cy))
            if cx == int(x1) and cy == int(y1):
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
        return points

    @staticmethod
    def cubic_ease_interpolate(x0, y0, x1, y1, steps=20):
        points = []
        for i in range(steps + 1):
            t = i / float(max(1, steps))
            ease_t = 3 * (t ** 2) - 2 * (t ** 3)
            px = round(x0 + (x1 - x0) * ease_t)
            py = round(y0 + (y1 - y0) * ease_t)
            points.append((int(px), int(py)))
        return points

    @staticmethod
    def human_bezier_curve(x0, y0, x1, y1, steps=25, jitter_mag=2.0):
        points = []
        dx, dy = x1 - x0, y1 - y0
        dist = math.hypot(dx, dy)
        arc = random.uniform(-0.15, 0.15) * dist
        c1x = x0 + dx * 0.25 - dy * arc * 0.005
        c1y = y0 + dy * 0.25 + dx * arc * 0.005
        c2x = x0 + dx * 0.75 - dy * arc * 0.003
        c2y = y0 + dy * 0.75 + dx * arc * 0.003
        for i in range(steps + 1):
            t = i / float(max(1, steps))
            t_ease = t * t * (3.0 - 2.0 * t)
            u = 1.0 - t_ease
            bx = (u**3)*x0 + 3*(u**2)*t_ease*c1x + 3*u*(t_ease**2)*c2x + (t_ease**3)*x1
            by = (u**3)*y0 + 3*(u**2)*t_ease*c1y + 3*u*(t_ease**2)*c2y + (t_ease**3)*y1
            if 0 < i < steps:
                bx += random.uniform(-jitter_mag, jitter_mag) * math.sin(t * math.pi)
                by += random.uniform(-jitter_mag, jitter_mag) * math.sin(t * math.pi)
            points.append((int(round(bx)), int(round(by))))
        return points
