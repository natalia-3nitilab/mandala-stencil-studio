"""Stencil system v2 — reversible pieces, one motif per piece, edges draw.

LOCK: straight fins, full height, drop into straight slots in the hub (no layers,
no sandwich). A fin is the same top and bottom, so every piece works face A up or
flipped to face B. Slots are 1.1 mm wide, narrower than a marker tip, so tracing
around the hub stays smooth. Everything drops in and lifts straight up.

Rule for the painter: at each placement, face A -> lift, flip -> face B.
Flipping mirrors the piece about the hub-number line, so face B draws the mirror
image: half arcs and half pearl rows complete each other, slots interleave, and a
motif at +x on face A lands at -x on face B.
"""
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

from geom import *  # noqa
from parts import Part, check_body, sector, radial_text, HUB_ROW1, HUB_ROW2, corner_lips, LIP_D

SLOT_W, SLOT_D, FIN_W, FIN_L = 1.1, 1.6, 0.9, 1.45
EDGE_REL = 0.3
NUMBERS = [(str(k + 1), 45.0 * k) for k in range(8)]
AXES = [n for n in NUMBERS if int(n[0]) % 2 == 1]
DIAGS = [n for n in NUMBERS if int(n[0]) % 2 == 0]


def mirror(g):
    return affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))


def radial_rect(phi, r0, r1, w):
    a = math.radians(phi)
    u = np.array([math.sin(a), math.cos(a)])
    v = np.array([math.cos(a), -math.sin(a)])
    return Polygon([u * r0 + v * w / 2, u * r1 + v * w / 2, u * r1 - v * w / 2, u * r0 - v * w / 2])


def slot(phi):            # in the hub's outer rim
    return radial_rect(phi, R_HUB - SLOT_D, R_HUB + 1.0, SLOT_W)


def fin(phi):             # on a piece, sits in slot(phi)
    return radial_rect(phi, R_HUB - FIN_L, R_HUB + 0.9, FIN_W)


def islot(phi):           # in the hub's inner rim
    return radial_rect(phi, R_CORE - 1.0, R_CORE + 1.4, SLOT_W)


def ifin(phi):            # on an insert
    return radial_rect(phi, R_INS - 0.7, R_CORE + 1.25, FIN_W)


def stack(base, cuts, eng_top=None, eng_bot=None, extra=None, rel=None):
    """Three slabs: undercut/lead-in on BOTH faces, because pieces are reversible."""
    rel = base if rel is None else rel
    full = base if extra is None else unary_union([base, extra])
    relx = rel if extra is None else unary_union([rel, extra])
    bot = relx.difference(cuts.buffer(EDGE_REL, quad_segs=12))
    top = relx.difference(cuts.buffer(EDGE_REL, quad_segs=12))
    if eng_bot is not None and not eng_bot.is_empty:
        bot = bot.difference(eng_bot)
    if eng_top is not None and not eng_top.is_empty:
        top = top.difference(eng_top)
    return [(0.0, EDGE_REL, bot), (EDGE_REL, T - EDGE_REL, full.difference(cuts)), (T - EDGE_REL, T, top)]


# ============================================================ hub
def build_hub():
    part = Part("H2", "Hub", "hub")
    row1 = [Feat("dot", Point(P(HUB_ROW1, 3.75 + 7.5 * k)), size="M") for k in range(48)]
    row2 = [Feat("dot", Point(P(HUB_ROW2, 3.75 + 7.5 * k)), size="S") for k in range(48)]
    part.feats = row1 + row2
    ring = annulus(R_CORE, R_HUB, q=256)
    dcut = unary_union([f.cut() for f in part.feats])
    slot_list = [slot(7.5 * k) for k in range(48)] + [islot(60.0 * k) for k in range(6)]
    slots = unary_union(slot_list)
    lead = unary_union([s.buffer(0.3, join_style="mitre") for s in slot_list])
    pockets = unary_union([sector(46.75, 48.35, ph - 6.5, ph + 6.5).buffer(0.3).buffer(-0.3) for ph in (22.5, 142.5, 262.5)])
    engr = unary_union([radial_text(str(k + 1), HUB_ROW2, 45 * k, 2.4) for k in range(8)])
    body = ring.difference(slots)
    part.layers = [
        (0.0, EDGE_REL, body.difference(dcut.buffer(EDGE_REL)).difference(pockets)),
        (EDGE_REL, T - EDGE_REL, body.difference(dcut)),
        (T - EDGE_REL, T, ring.difference(lead).difference(dcut.buffer(EDGE_REL)).difference(engr)),
    ]
    part.outline, part.cuts, part.engrave, part.slots = body, dcut, engr, slots
    check_body(part, body.difference(dcut))
    part.placements = [("-", 0.0, "A")]
    return part


# ============================================================ reversible piece / insert
class Piece(Part):
    """kind 'wedge' clicks onto the hub rim, 'insert' drops inside the hub.
    lines: (true geometry, 'edge'|'slot'|'hole'); dots: (point, 'S'|'M').
    placements: (hub label, rotation deg clockwise, face)."""

    def __init__(self, pid, name, body, cuts, lines, dots, fins, kind="wedge", placements=None,
                 label=None, two_faced=True, note=""):
        super().__init__(pid, name, kind)
        self.body, self.cuts_, self.lines, self.dots = body, cuts, list(lines), list(dots)
        self.fins_at = list(fins)
        self.kind, self.two_faced, self.note = kind, two_faced, note
        if placements is None:
            placements = [(l, d, f) for l, d in NUMBERS for f in (("A", "B") if two_faced else ("A",))]
        self.placements = placements
        self.positions = sorted({(l, d) for l, d, _ in placements}, key=lambda x: x[1])
        self.cuts = cuts
        fg = self.fin_geom()
        self.outline = unary_union([body, fg])
        check_body(self, body.difference(cuts))
        lab = label or pid
        free = body.difference(cuts.buffer(1.3)).buffer(-0.9)
        if kind == "wedge":
            free = free.difference(disk(R_HUB + 3.0, q=128))
        self.engrave = self._place(free, text_poly(lab + (" A" if two_faced else ""), 3.4))
        if two_faced:
            self.engrave_b = self._place(free.difference(self.engrave.buffer(1.0)), mirror(text_poly(lab + " B", 3.4)))
        else:
            self.engrave_b = Polygon()
        if kind == "wedge":
            rel = unary_union([body.buffer(-EDGE_REL, join_style="mitre"), body.intersection(disk(R_HUB + 2.5, q=256))])
        else:
            rel = body.buffer(-0.02)
        self.layers = stack(body, cuts, self.engrave, self.engrave_b, extra=fg, rel=rel)

    def fin_geom(self):
        if self.kind == "wedge":
            return unary_union([fin(p) for p in self.fins_at])
        return unary_union([ifin(p) for p in self.fins_at])

    def _place(self, free, lab):
        from shapely.prepared import prep
        if free.is_empty:
            self.warnings.append("no room for label")
            return Polygon()
        fp = prep(free)
        minx, miny, maxx, maxy = free.bounds
        hull = lab.convex_hull
        best = None
        for y in np.arange(miny, maxy, 0.8):
            for x in np.arange(minx, maxx, 0.8):
                if not fp.contains(Point(x, y)):
                    continue
                if fp.contains(affinity.translate(hull, x, y)):
                    score = abs(x) + 0.25 * abs(y)
                    if best is None or score < best[0]:
                        best = (score, (x, y))
        if best is None:
            self.warnings.append("no room for label")
            return Polygon()
        return affinity.translate(lab, *best[1])

    def painted_a(self):
        out = []
        blocked = self.outline.buffer(TIP_R - 0.06, quad_segs=16)
        reach = self.cuts_.buffer(-TIP_R + 0.06, quad_segs=16).buffer(0.05)
        for g, kind in self.lines:
            ln = g.difference(blocked) if kind == "edge" else g.intersection(reach)
            for l in lines_of(ln):
                out.append(("line", l.buffer(LINE_W / 2, quad_segs=8)))
        for p, size in self.dots:
            out.append(("gold" if size == "M" else "white", Point(p).buffer(DOT_DRAWN[size] / 2, quad_segs=16)))
        return out

    def painted(self, deg, face="A"):
        out = self.painted_a()
        if face == "B":
            out = [(c, mirror(g)) for c, g in out]
        return [(c, rot(g, deg)) for c, g in out]

    def all_painted(self, which=None):
        L = []
        for lab, deg, face in self.placements:
            if which is None or (lab, face) in which:
                L += self.painted(deg, face)
        return L

    def placed_outline(self, deg, face="A"):
        g = self.outline.difference(self.cuts_)
        return rot(mirror(g) if face == "B" else g, deg)

    def placed_fins(self, deg, face="A"):
        g = self.fin_geom()
        return rot(mirror(g) if face == "B" else g, deg)

    def solid_face(self, face="A"):
        m = self.solid()
        if face == "B":
            m = m.rotate([0, 180, 0]).translate([0, 0, T])
        return m


def notch_comb(centres, r):
    return unary_union([Point(c).buffer(r, quad_segs=16) for c in centres])


def around(c, r, a):
    return (c[0] + r * math.sin(math.radians(a)), c[1] + r * math.cos(math.radians(a)))


def half_plane(c, axis_deg, side, offset=0.0, size=400.0):
    """Half plane bounded by the line through c in direction axis_deg (clockwise from up).
    side=+1 keeps the clockwise side; the boundary is moved `offset` mm into the other side."""
    a = math.radians(axis_deg)
    u = np.array([math.sin(a), math.cos(a)])
    n = np.array([u[1], -u[0]]) * side
    o = np.array(c) - n * offset
    return Polygon([o - u * size, o + u * size, o + u * size + n * size, o - u * size + n * size])


def foot(span=21.0, depth=7.0):
    return sector(R_HUB + CLR, R_HUB + depth, -span, span)


def arm(points, w):
    return LineString(points).buffer(w / 2, quad_segs=8)


def side_of(q, c, axis_deg):
    a = math.radians(axis_deg)
    u = (math.sin(a), math.cos(a))
    return u[1] * (q[0] - c[0]) - u[0] * (q[1] - c[1])      # >0 clockwise side


def comb_points(c, r, a0, a1, spacing, keep=lambda q: True, inset=0.25):
    out = []
    n = max(1, int(abs(math.radians(a1 - a0)) * r / spacing))
    for j in range(n):
        a = a0 + (a1 - a0) * (j + 0.5) / n
        q = around(c, r - inset, a)
        if keep(q):
            out.append(q)
    return out


def make_insert(pid, name, holes, lines, dots, placements, label=None, two_faced=False, rim=1.1, clip=True):
    disc = disk(R_INS, q=256)
    cuts = holes
    if clip and not holes.is_empty:
        cuts = holes.intersection(disk(R_INS - rim, q=256))
    dcut = unary_union([Point(p).buffer((DOT_S if s == "S" else DOT_M) / 2, quad_segs=24) for p, s in dots]) if dots else Polygon()
    cuts = unary_union([cuts, dcut])
    return Piece(pid, name, disc, cuts, lines, dots, fins=[0.0], kind="insert",
                 placements=placements, label=label, two_faced=two_faced)


# ============================================================ centring jig
def build_jig(pid, name, half, label, wall=5.0, open_far=False):
    part = Part(pid, name, "jig", flip=True)
    cx = cy = half
    ring_in = R_HUB + 0.25
    ring = annulus(ring_in, ring_in + wall)
    if open_far:   # C-shaped cradle (200 deg) still traps the hub, and fits a 210 mm bed
        ring = ring.difference(sector(0, ring_in + wall + 5, 45 - 80, 45 + 80)).buffer(1.0).buffer(-1.0)
    ring = affinity.translate(ring, cx, cy)
    d = np.array([1, 1]) / math.sqrt(2)
    n = np.array([-1, 1]) / math.sqrt(2)
    p1 = np.array([cx, cy]) - d * (ring_in + 3)
    beam = Polygon([n * 9, p1 + n * 9, p1 - n * 9, -n * 9])
    corner = box(0, 0, 34, 34).difference(Point(34, 34).buffer(22))
    L = 40
    lips = corner_lips(L)
    plate = unary_union([ring, beam, corner, box(0, 0, L, 6), box(0, 0, 6, L), lips])
    plate = plate.difference(affinity.translate(disk(ring_in), cx, cy))
    key = affinity.translate(fin(225.0), cx, cy)            # a fin that drops into hub slot "6"
    TJ = 3.0
    lab = affinity.translate(affinity.rotate(text_poly(label, 4.0), 45, origin=(0, 0)), cx * 0.45, cy * 0.45)
    lab2 = affinity.translate(affinity.rotate(text_poly("hub 6", 3.0), 45, origin=(0, 0)), *(np.array([cx, cy]) - d * (ring_in + 9)))
    engr = unary_union([lab, lab2])
    body = unary_union([plate, key])
    part.layers = [(0.0, TJ - 0.5, body), (TJ - 0.5, TJ, body.difference(engr)), (-LIP_D, 0.0, lips)]
    part.outline, part.cuts, part.engrave, part.half = body, Polygon(), engr, half
    return part


# ============================================================ corner piece (hooks a canvas corner; one face)
class Corner(Part):
    def __init__(self, pid, name, half, edge_r, chans, dots, L, label):
        super().__init__(pid, name, "corner", flip=True)
        self.half = half
        lips = corner_lips(L).intersection(box(-3, -3, edge_r - TIP_R, edge_r - TIP_R))
        plate = disk(edge_r - TIP_R, q=256).intersection(box(0, 0, L, L))
        cuts = unary_union([c.buffer(LINE_SLOT / 2, quad_segs=16) for c in chans] +
                           [Point(p).buffer((DOT_S if s == "S" else DOT_M) / 2, quad_segs=16) for p, s in dots])
        cuts = cuts.intersection(box(0, 0, L + 5, L + 5))
        self.body = unary_union([plate, lips])
        self.cuts_ = cuts
        self.lines = [(arc((0, 0), edge_r, 0, 90, step=0.4), "edge")] + [(c, "slot") for c in chans]
        self.dots = list(dots)
        self.outline, self.cuts = self.body, cuts
        check_body(self, self.body.difference(cuts))
        from geom import place_label
        self.engrave = place_label(self.body, cuts, text_poly(label, 3.6), prefer=(edge_r * 0.3, edge_r * 0.3)) or Polygon()
        rel = unary_union([self.body.buffer(-EDGE_REL, join_style="mitre"), lips])
        self.layers = stack(self.body, cuts, self.engrave, None, rel=rel) + [(-LIP_D, 0.0, lips)]
        self.positions = [("BL", 0.0), ("TL", 90.0), ("TR", 180.0), ("BR", 270.0)]
        self.placements = [(l, d, "A") for l, d in self.positions]
        self.two_faced = False

    def fin_geom(self):
        return Polygon()

    def painted_a(self):
        return Piece.painted_a(self)

    def painted(self, deg, face="A"):
        return [(c, rot(affinity.translate(g, -self.half, -self.half), deg)) for c, g in self.painted_a()]

    def all_painted(self, which=None):
        L = []
        for lab, deg, face in self.placements:
            if which is None or (lab, face) in which:
                L += self.painted(deg, face)
        return L

    def placed_outline(self, deg, face="A"):
        return rot(affinity.translate(self.outline.difference(self.cuts_), -self.half, -self.half), deg)
