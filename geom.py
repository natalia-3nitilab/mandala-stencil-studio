"""Geometry core for the Sacred Geometry Marker Stencil system.

All dimensions in millimetres. Angles (phi) are in degrees measured CLOCKWISE
from "up" (12 o'clock), which is how hub positions are numbered on the canvas.
"""
import math
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon, LineString, MultiLineString, GeometryCollection, box
from shapely.ops import unary_union
from shapely import affinity

# ============================================================================
# 1. MARKER PROFILE  — change these after printing the Fit Card (Phase 0)
# ============================================================================
LINE_SLOT = 1.8      # channel width your FINE line marker glides in (PC-3M class)
DOT_S = 2.2          # small dot hole  (fine marker tip, PC-3M class)
DOT_M = 3.0          # medium dot hole (medium marker tip, PC-5M class)
TIP_R = LINE_SLOT / 2  # tracing offset: centre of the tip sits this far from a wall

# drawn sizes, only used for the painting previews
LINE_W = 1.2
DOT_DRAWN = {"S": 1.9, "M": 2.7}
DOT_COLOR = {"S": "white", "M": "gold"}   # rule for painters: big holes = colour 3, small holes = colour 2

# ============================================================================
# 2. PLATE / PRINT SETTINGS
# ============================================================================
T = 2.0              # plate thickness
STEP = 0.8           # smooth contact band height (index teeth/notches sit above it)
RELIEF, RELIEF_H = 0.25, 0.4   # under-cut on the canvas side so wet paint isn't touched
CHAMF, CHAMF_H = 0.35, 0.4     # lead-in on the marker side
ENGRAVE_H = CHAMF_H            # label engraving depth (same slab)
BRIDGE = 1.0         # width of a bridge across a channel (always hidden under a dot later)

# ============================================================================
# 3. SYSTEM DIMENSIONS (shared by every kit)
# ============================================================================
R_CORE = 40.0        # hub inner edge = Flower-of-Life boundary circle (traced)
R_HUB = 54.0         # hub outer edge (wedges register here; traced for ring C1)
CLR = 0.12           # sliding clearance
N_NOTCH = 48         # outer index notches -> 7.5 deg steps (6/8/12/16/24-fold ready)
NOTCH_D = 1.5        # notch depth (90 deg V)
R_INS = R_CORE - 0.15  # insert disc radius
C0 = R_CORE - TIP_R  # centre-line of the traced FoL boundary circle
C1 = R_HUB + TIP_R   # centre-line of the circle traced around the hub


# ---------------------------------------------------------------------------
# basic helpers
# ---------------------------------------------------------------------------
def P(r, phi):
    a = math.radians(phi)
    return (r * math.sin(a), r * math.cos(a))


def ang(p):
    return math.degrees(math.atan2(p[0], p[1]))


def rad(p):
    return math.hypot(p[0], p[1])


def disk(r, c=(0.0, 0.0), q=64):
    return Point(c).buffer(r, quad_segs=q)


def annulus(r0, r1, q=128):
    return disk(r1, q=q).difference(disk(r0, q=q))


def sector(r0, r1, phi0, phi1, step=0.5):
    n = max(3, int(abs(phi1 - phi0) / step) + 1)
    outer = [P(r1, p) for p in np.linspace(phi0, phi1, n)]
    inner = [P(r0, p) for p in np.linspace(phi1, phi0, n)]
    return Polygon(outer + inner)


def rot(g, deg):
    """rotate geometry CLOCKWISE by deg around canvas centre"""
    return affinity.rotate(g, -deg, origin=(0, 0))


def circle_pts(c, rho, n=720):
    return [(c[0] + rho * math.sin(t), c[1] + rho * math.cos(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def arcs_where(c, rho, keep, n=1440):
    """Return the arcs (LineStrings) of circle(c, rho) whose points satisfy keep(p)."""
    pts = circle_pts(c, rho, n)
    ok = [keep(p) for p in pts]
    if all(ok):
        return [LineString(pts + [pts[0]])]
    if not any(ok):
        return []
    # rotate so we start at a False
    s = ok.index(False)
    pts = pts[s:] + pts[:s]
    ok = ok[s:] + ok[:s]
    runs, cur = [], []
    for p, k in zip(pts, ok):
        if k:
            cur.append(p)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [LineString(r) for r in runs if len(r) >= 2]


def arc(c, rho, phi0, phi1, step=0.5):
    n = max(2, int(abs(phi1 - phi0) / step) + 1)
    return LineString([(c[0] + rho * math.sin(math.radians(p)), c[1] + rho * math.cos(math.radians(p)))
                       for p in np.linspace(phi0, phi1, n)])


def vesica(p0, p1, w):
    """Pointed lens/petal with tips p0, p1 and maximum width w."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    u = (p1 - p0) / L
    n = np.array([-u[1], u[0]])
    R = ((L / 2) ** 2 + (w / 2) ** 2) / w
    mid = (p0 + p1) / 2
    c1 = mid + n * (R - w / 2)
    c2 = mid - n * (R - w / 2)
    return disk(R, tuple(c1), q=128).intersection(disk(R, tuple(c2), q=128))


def parts(g):
    if g is None or g.is_empty:
        return []
    if hasattr(g, "geoms"):
        out = []
        for x in g.geoms:
            out += parts(x)
        return out
    return [g]


def lines_of(g):
    return [x for x in parts(g) if x.geom_type in ("LineString", "LinearRing") and x.length > 0.05]


def polys_of(g):
    return [x for x in parts(g) if x.geom_type == "Polygon" and x.area > 1e-6]


# ---------------------------------------------------------------------------
# Features: what a stencil lets you draw
# ---------------------------------------------------------------------------
class Feat:
    """kind: 'chan' = channel the tip glides in (geom = centre-line)
             'hole' = opening you trace around the inside wall of (geom = true outline polygon)
             'dot'  = dot hole (geom = Point, size 'S' or 'M')
    """

    def __init__(self, kind, geom, color="line", size="S", bridges=(), group=""):
        self.kind, self.geom, self.color, self.size = kind, geom, color, size
        self.bridges = list(bridges)
        self.group = group

    def rotated(self, deg):
        br = [rot(b, deg) if hasattr(b, "geom_type") else rot(Point(b), deg).coords[0] for b in self.bridges]
        f = Feat(self.kind, rot(self.geom, deg), self.color, self.size, br, self.group)
        return f

    def cut(self):
        if self.kind == "chan":
            g = self.geom.buffer(LINE_SLOT / 2, quad_segs=24)
            for b in self.bridges:   # a point -> bridge across the path; a polygon -> used as is
                g = g.difference(b if hasattr(b, "geom_type") else bridge_poly(self.geom, b))
            return g
        if self.kind == "hole":
            return self.geom.buffer(TIP_R, join_style="mitre", mitre_limit=3.0)
        if self.kind == "dot":
            d = DOT_S if self.size == "S" else DOT_M
            return self.geom.buffer(d / 2, quad_segs=24)
        raise ValueError(self.kind)

    def drawn(self, cut=None):
        """Geometry that ends up as paint (as a polygon) for the preview."""
        cut = self.cut() if cut is None else cut
        if self.kind == "dot":
            return self.geom.buffer(DOT_DRAWN[self.size] / 2, quad_segs=16)
        reach = cut.buffer(-TIP_R + 0.03, quad_segs=16)
        if self.kind == "chan":
            path = self.geom
        else:
            path = self.geom.exterior
        ln = path.intersection(reach.buffer(0.04))
        return unary_union([l.buffer(LINE_W / 2, quad_segs=8) for l in lines_of(ln)])


def bridge_poly(path, p):
    d = path.project(Point(p))
    a = np.array(path.interpolate(max(0, d - 0.3)).coords[0])
    b = np.array(path.interpolate(min(path.length, d + 0.3)).coords[0])
    t = b - a
    t = t / np.linalg.norm(t)
    n = np.array([-t[1], t[0]])
    c = np.array(path.interpolate(d).coords[0])
    hw, hl = LINE_SLOT, BRIDGE / 2
    pts = [c + t * hl + n * hw, c - t * hl + n * hw, c - t * hl - n * hw, c + t * hl - n * hw]
    return Polygon(pts)


# ---------------------------------------------------------------------------
# Text engraving
# ---------------------------------------------------------------------------
def text_poly(s, h=4.0, weight="bold"):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), s, size=h, prop=FontProperties(family="DejaVu Sans", weight=weight))
    g = Polygon()
    for ring in tp.to_polygons(closed_only=True):
        if len(ring) >= 3:
            g = g.symmetric_difference(Polygon(ring).buffer(0))
    minx, miny, maxx, maxy = g.bounds
    return affinity.translate(g, -(minx + maxx) / 2, -(miny + maxy) / 2)


def arrow_poly(h=5.0, w=4.0):
    """Arrow pointing DOWN (towards the hub when the plate points up)."""
    return Polygon([(-w / 2, h / 2), (w / 2, h / 2), (0, -h / 2)])


def place_label(body, avoid, label_geom, prefer, max_r=None, search=None):
    """Find a spot inside body (away from avoid) for label_geom, nearest to `prefer`."""
    from shapely.prepared import prep
    free = body.buffer(-1.0).difference(avoid.buffer(1.2)).simplify(0.05)
    fp = prep(free)
    hull = label_geom.convex_hull.simplify(0.05)
    if search is None:
        minx, miny, maxx, maxy = body.bounds
        xs = np.arange(minx, maxx, 1.5)
        ys = np.arange(miny, maxy, 1.5)
        search = [(x, y) for x in xs for y in ys]
    search = sorted(search, key=lambda q: (q[0] - prefer[0]) ** 2 + (q[1] - prefer[1]) ** 2)
    for q in search:
        if not fp.contains(Point(q)):
            continue
        if fp.contains(affinity.translate(hull, q[0], q[1])):
            return affinity.translate(label_geom, q[0], q[1])
    return None
