"""Klasifikasi geometris empat jari dan stabilisasi berdasarkan waktu."""
import math
import config


def classify(points, width, height):
    try:
        angles = []
        for a, b, c in ((5, 6, 7), (9, 10, 11), (13, 14, 15), (17, 18, 19)):
            u = ((points[a].x-points[b].x)*width, (points[a].y-points[b].y)*height)
            v = ((points[c].x-points[b].x)*width, (points[c].y-points[b].y)*height)
            denominator = math.hypot(*u)*math.hypot(*v)
            if not math.isfinite(denominator) or denominator <= 1e-9:
                return 'unknown'
            cosine = sum(x*y for x,y in zip(u,v))/denominator
            if not math.isfinite(cosine):
                return 'unknown'
            angles.append(math.degrees(math.acos(max(-1,min(1,cosine)))))
        return 'open' if min(angles)>=config.OPEN_ANGLE else 'fist' if max(angles)<=config.FIST_ANGLE else 'neutral'
    except (IndexError, AttributeError, TypeError):
        return 'unknown'


class GestureState:
    def __init__(self):
        self.kind = 'unknown'
        self.duration = 0.
        self.armed = True

    def update(self, kind, dt):
        self.duration = self.duration + dt if kind == self.kind else 0.
        self.kind = kind
        if kind == 'unknown':
            self.duration = 0.
        if kind in ('open', 'neutral') and self.duration >= config.FIST_HOLD:
            self.armed = True
        event = kind == 'fist' and self.duration >= config.FIST_HOLD and self.armed
        if event:
            self.armed = False
        return {'kind': kind, 'duration': self.duration, 'fist': event}
