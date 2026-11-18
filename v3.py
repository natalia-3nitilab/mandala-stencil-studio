"""Stencil system v3 — robust and printable.

LOCK      Solid 90-degree V-teeth (1.8 mm deep, 3.6 mm wide) drop into V-notches in the hub.
          Full height, no layers, no thin fins. The same top and bottom, so every piece
          also works flipped (face B = mirror image).
LANES     The hub's notched edges are never traced. The ring circle around the hub is traced
          in a 2.6 mm lane between the hub and the ring piece's inner edge; the boundary
          circle of a centre is traced in a 2.4 mm lane between the insert and the hub.
          Pieces that bridge a lane do it with tabs at uneven angles: face A's tabs and face
          B's tabs never cover the same spot, so A + B close the circle.
GROOVES   Dot rows are "a line with pockets": through-holes linked by a shallow groove
          (1.3 wide, 0.6 deep) on each face. Glide the tip along the groove, press at each hole.
WALLS     Every wall at least 1.6 mm (4 lines of a 0.4 nozzle). Checked automatically.
PRINT     Everything prints flat, no supports. Jigs and corner pieces print lips up.
"""
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

from geom import *  # noqa
from parts import Part, sector, radial_text, corner_lips, LIP_D, vee

MIN_WALL = 1.6
EDGE_REL = 0.3
GROOVE_W, GROOVE_D = 1.3, 0.6
NOTCH_D, INOTCH_D = 1.8, 1.6
LANE_OUT = 2.6                  # hub rim -> ring piece inner edge
LANE_IN = 2.4                   # insert edge -> hub inner wall
R_INS3 = R_CORE - LANE_IN       # 37.6 insert radius
C0_3 = R_INS3 + TIP_R           # 38.5 centre boundary circle
R_LANE = R_HUB + LANE_OUT       # 56.6 ring piece inner edge
C1_3 = R_LANE - TIP_R           # 55.7 ring circle around the hub
HUB_ROW1_3, HUB_ROW2_3 = 44.6, 49.0
NUMBERS = [(str(k + 1), 45.0 * k) for k in range(8)]
AXES = [n for n in NUMBERS if int(n[0]) % 2 == 1]
DIAGS = [n for n in NUMBERS if int(n[0]) % 2 == 0]


def mirror(g):
    return affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))


def notch(phi):
    return vee(phi, R_HUB - NOTCH_D, R_HUB + 1.5, NOTCH_D + 1.5)


def tooth(phi, base=R_HUB + 0.9):
    t = vee(phi, R_HUB - NOTCH_D + 0.17, base, (base - (R_HUB - NOTCH_D + 0.17)) - 0.17)
    return t.difference(disk(R_HUB - NOTCH_D + 0.45, q=256))     # blunt tip, easy to print


def inotch(phi):
    return vee(phi, R_CORE + INOTCH_D, R_CORE - 1.5, INOTCH_D + 1.5)


def itooth(phi):
    apex = R_CORE + INOTCH_D - 0.17
    base = R_CORE - 0.6
    t = vee(phi, apex, base, (apex - base) - 0.17)
    return t.intersection(disk(R_CORE + INOTCH_D - 0.45, q=256))


def radial_rect(phi, r0, r1, w):
    a = math.radians(phi)
    u = np.array([math.sin(a), math.cos(a)])
    v = np.array([math.cos(a), -math.sin(a)])
    return Polygon([u * r0 + v * w / 2, u * r1 + v * w / 2, u * r1 - v * w / 2, u * r0 - v * w / 2])


def grooves(rows):
    """rows: lists of pocket centres; returns the groove geometry linking consecutive pockets."""
    g = []
    for row in rows:
        if len(row) >= 2:
            g.append(LineString(row).buffer(GROOVE_W / 2, cap_style="round", quad_segs=8))
    return unary_union(g) if g else Polygon()


def min_wall_ok(body, w=MIN_WALL):
    """True if every part of `body` survives an erosion of w/2 (no wall thinner than w)."""
    big = [p for p in polys_of(body) if p.area > 0.5]
    er = [p for p in polys_of(body.buffer(-w / 2 + 0.01)) if p.area > 0.05]
    return len(er) <= len(big), len(er), len(big)


def thin_spots(body, w=MIN_WALL):
    """Area of material that disappears with an opening of w (thin walls / slivers)."""
    opened = body.buffer(-w / 2 + 0.01).buffer(w / 2 - 0.01)
    return body.difference(opened)


# ============================================================ hub
def build_hub():
    p = Part("H3", "Hub", "hub")
    p.kind = "hub"
    r1 = [P(HUB_ROW1_3, 3.75 + 7.5 * k) for k in range(48)]
    r2 = [P(HUB_ROW2_3, 3.75 + 7.5 * k) for k in range(48)]
    p.dots = [(q, "M") for q in r1] + [(q, "S") for q in r2]
    ring = annulus(R_CORE, R_HUB, q=256)
    notches = unary_union([notch(7.5 * k) for k in range(48)] + [inotch(60.0 * k) for k in range(6)])
    body = ring.difference(notches)
    holes = unary_union([Point(q).buffer((DOT_M if s == "M" else DOT_S) / 2, quad_segs=24) for q, s in p.dots])
    gr = grooves([r1 + [r1[0]], r2 + [r2[0]]])
    pockets = unary_union([sector(46.4, 47.4, ph - 6.5, ph + 6.5).buffer(0.3).buffer(-0.3) for ph in (22.5, 142.5, 262.5)])
    eng = unary_union([radial_text(str(k + 1), 50.9, 45 * k, 2.0) for k in range(8)])
    ins = lambda g, i: g.buffer(-0.01 * i, join_style="mitre") if i else g     # every slab its own inset -> clean STL
    p.layers = [
        (0.0, EDGE_REL, ins(body, 1).difference(holes.buffer(EDGE_REL)).difference(pockets)),
        (EDGE_REL, T - GROOVE_D, body.difference(holes)),
        (T - GROOVE_D, T - EDGE_REL, ins(body, 2).difference(holes.buffer(0.02)).difference(gr)),
        (T - EDGE_REL, T, ins(body, 3).difference(holes.buffer(EDGE_REL + 0.01)).difference(gr.buffer(0.01)).difference(eng)),
    ]
    p.outline, p.cuts, p.engrave, p.notches, p.body = body, holes, eng, notches, body
    p.grooves = gr
    p.placements = [("-", 0.0, "A")]
    p.lines = []
    return p


# ============================================================ piece / insert
class Piece(Part):
    """A reversible stencil piece.

    body      solid outline (without teeth)
    cuts      through-openings: tracing holes, slots, dot pockets
    lines     (true geometry, 'edge' | 'hole' | 'lane') — what the marker should paint
    dots      (point, 'S'|'M') — every pocket
    rows      lists of pocket centres linked by grooves
    teeth     outer V-teeth angles (wedge) or inner V-teeth angles (insert)
    bumps     plain contact tabs (insert) — angles
    """

    def __init__(self, pid, name, body, cuts, lines, dots, teeth, kind="wedge", rows=(), bumps=(),
                 placements=None, two_faced=True, label=None, note="", tabs=None):
        super().__init__(pid, name, kind)
        self.kind, self.two_faced, self.note = kind, two_faced, note
        self.teeth_at, self.bumps_at = list(teeth), list(bumps)
        self.tabs = tabs if tabs is not None else Polygon()
        self.body0 = body
        tg = self.teeth_geom()
        self.body = unary_union([body, self.tabs])
        self.outline = unary_union([self.body, tg])
        self.cuts_ = cuts
        self.cuts = cuts
        self.lines, self.dots, self.rows = list(lines), list(dots), [list(r) for r in rows]
        if placements is None:
            placements = [(l, d, f) for l, d in NUMBERS for f in (("A", "B") if two_faced else ("A",))]
        self.placements = placements
        self.positions = sorted({(l, d) for l, d, _ in placements}, key=lambda x: x[1])
        self.grooves = grooves(self.rows)
        # walls
        thin = thin_spots(self.body.difference(cuts))
        bad = [g for g in polys_of(thin) if g.area > 0.35]
        if bad:
            self.warnings.append(f"thin wall: {len(bad)} spot(s), largest {max(g.area for g in bad):.2f} mm2")
        # labels
        lab = label or pid
        free = self.body.difference(cuts.buffer(1.6)).difference(self.grooves.buffer(1.0)).buffer(-1.0)
        if kind == "wedge":
            free = free.difference(disk(R_HUB + 3.5, q=128))
        self.engrave = Polygon()
        for h in (3.4, 2.6, 2.0):
            g = self._place(free, text_poly(lab + (" A" if two_faced else ""), h), quiet=True)
            if not g.is_empty:
                self.engrave = g
                break
        self.engrave_b = Polygon()
        if two_faced:
            fb = free.difference(self.engrave.buffer(1.2)).difference(mirror(self.engrave).buffer(1.2))
            for h in (3.4, 2.6, 2.0):
                g = self._place(fb, mirror(text_poly(lab + " B", h)), quiet=True)
                if not g.is_empty:
                    self.engrave_b = g
                    break
        if self.engrave.is_empty or (two_faced and self.engrave_b.is_empty):
            self.warnings.append("label: no room")
        self._layers(tg)

    def teeth_geom(self):
        if self.kind == "wedge":
            return unary_union([tooth(a) for a in self.teeth_at]) if self.teeth_at else Polygon()
        g = [itooth(a) for a in self.teeth_at]
        return unary_union(g) if g else Polygon()

    def _place(self, free, lab, quiet=False):
        from shapely.prepared import prep
        if free.is_empty:
            return Polygon()
        fp = prep(free)
        minx, miny, maxx, maxy = free.bounds
        hull = lab.convex_hull
        best = None
        for y in np.arange(miny, maxy, 0.8):
            for x in np.arange(minx, maxx, 0.8):
                if fp.contains(Point(x, y)) and fp.contains(affinity.translate(hull, x, y)):
                    s = abs(x) + 0.25 * abs(y)
                    if best is None or s < best[0]:
                        best = (s, (x, y))
        if best is None:
            return Polygon()
        return affinity.translate(lab, *best[1])

    def _layers(self, tg):
        """Adjacent slabs never share a wall (0.01 mm offsets), so the STL is a clean closed solid."""
        body, cuts, gr = self.outline, self.cuts_, self.grooves
        ins = lambda g, i: g.buffer(-0.01 * i, join_style="mitre") if i else g
        grow = lambda g, i: g.buffer(0.01 * i, quad_segs=12) if i and not g.is_empty else g
        if self.kind == "wedge":
            keep = unary_union([self.body.intersection(disk(R_HUB + 2.5, q=256)), tg])
        else:
            keep = unary_union([self.tabs, tg])
        def rel(i):
            return unary_union([self.body.buffer(-EDGE_REL - 0.01 * i, join_style="mitre"), ins(keep, i)])
        lead = lambda i: cuts.buffer(EDGE_REL + 0.01 * i, quad_segs=12)
        gb = gr if self.two_faced else Polygon()
        L = [(0.0, EDGE_REL, rel(1).difference(lead(1)).difference(grow(gb, 1)).difference(self.engrave_b))]
        if self.two_faced:
            L.append((EDGE_REL, GROOVE_D, ins(body, 2).difference(grow(cuts, 2)).difference(grow(gb, 2))))
            L.append((GROOVE_D, T - GROOVE_D, body.difference(cuts)))
        else:
            L.append((EDGE_REL, T - GROOVE_D, body.difference(cuts)))
        L.append((T - GROOVE_D, T - EDGE_REL, ins(body, 3).difference(grow(cuts, 3)).difference(grow(gr, 3))))
        L.append((T - EDGE_REL, T, rel(4).difference(lead(4)).difference(grow(gr, 4)).difference(self.engrave)))
        self.layers = L

    # ---- painting
    def painted_a(self):
        out = []
        blocked = self.outline.buffer(TIP_R - 0.06, quad_segs=16)
        reach = self.cuts_.buffer(-TIP_R + 0.06, quad_segs=16).buffer(0.05)
        for g, kind in self.lines:
            if kind in ("edge", "lane"):
                ln = g.difference(blocked)
            else:
                ln = g.intersection(reach)
            for l in lines_of(ln):
                out.append(("line", l.buffer(LINE_W / 2, quad_segs=8)))
        for q, s in self.dots:
            out.append(("gold" if s == "M" else "white", Point(q).buffer(DOT_DRAWN[s] / 2, quad_segs=16)))
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

    def placed_teeth(self, deg, face="A"):
        g = self.teeth_geom()
        return rot(mirror(g) if face == "B" else g, deg)

    def solid_face(self, face="A"):
        m = self.solid()
        if face == "B":
            m = m.rotate([0, 180, 0]).translate([0, 0, T])
        return m


# ============================================================ helpers for designs
def around(c, r, a):
    return (c[0] + r * math.sin(math.radians(a)), c[1] + r * math.cos(math.radians(a)))


def half_plane(c, axis_deg, side, offset=0.0, size=400.0):
    a = math.radians(axis_deg)
    u = np.array([math.sin(a), math.cos(a)])
    n = np.array([u[1], -u[0]]) * side
    o = np.array(c) - n * offset
    return Polygon([o - u * size, o + u * size, o + u * size + n * size, o - u * size + n * size])


def foot(span=22.0, depth=7.5):
    return sector(R_HUB + CLR, R_HUB + depth, -span, span)


def arm(points, w):
    return LineString(points).buffer(w / 2, quad_segs=8)


def side_of(q, c, axis_deg):
    a = math.radians(axis_deg)
    u = (math.sin(a), math.cos(a))
    return u[1] * (q[0] - c[0]) - u[0] * (q[1] - c[1])


def comb(c, r, a0, a1, spacing, keep=lambda q: True, inset=0.25):
    """Pocket centres for a notch comb on an edge of radius r around c (half-open, symmetric)."""
    n = max(1, int(abs(math.radians(a1 - a0)) * r / spacing))
    out = []
    for j in range(n):
        a = a0 + (a1 - a0) * (j + 0.5) / n
        q = around(c, r - inset, a)
        if keep(q):
            out.append(q)
    return out


def notches_at(pts, r):
    return unary_union([Point(q).buffer(r, quad_segs=16) for q in pts]) if pts else Polygon()


def pockets(pts, size="S"):
    d = DOT_S if size == "S" else DOT_M
    return unary_union([Point(q).buffer(d / 2, quad_segs=24) for q in pts]) if pts else Polygon()


def lane_tabs(angles, r_in, r_out, width=5.0):
    """tabs that bridge a lane (wedge: hub rim -> ring piece)."""
    return unary_union([radial_rect(a, r_in, r_out, width) for a in angles]) if angles else Polygon()


# ============================================================ inserts (drop inside the hub)
INS_TEETH = [60.0, 120.0]       # V-teeth into inner notches (uneven, so face B uses 240/300)
INS_BUMP = [270.0]              # a plain contact tab opposite, so the insert can't drift


def insert_tabs():
    t = [radial_rect(a, R_INS3 - 1.0, R_CORE - 0.55, 5.0) for a in INS_TEETH]
    t += [radial_rect(a, R_INS3 - 1.0, R_CORE - CLR, 4.0) for a in INS_BUMP]
    return unary_union(t)


def make_insert(pid, name, holes, lines, dots, rows, placements, two_faced=False, lane=False, label=None, note=""):
    disc = disk(R_INS3, q=256)
    cuts = unary_union([holes, pockets([q for q, s in dots if s == "S"], "S"), pockets([q for q, s in dots if s == "M"], "M")])
    lines = list(lines)
    if lane:
        lines.append((disk(C0_3, q=256).exterior, "lane"))
    return Piece(pid, name, disc, cuts, lines, dots, INS_TEETH, kind="insert", rows=rows, bumps=INS_BUMP,
                 placements=placements, two_faced=two_faced, label=label, note=note, tabs=insert_tabs())


# ============================================================ centring jig (prints lips up)
def build_jig(pid, name, half, label, wall=5.0, open_far=False):
    p = Part(pid, name, "jig", flip=True)
    cx = cy = half
    ring_in = R_HUB + 0.25
    ring = annulus(ring_in, ring_in + wall)
    if open_far:
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
    key = affinity.translate(tooth(225.0, base=R_HUB + 1.2), cx, cy)
    TJ = 3.0
    lab = affinity.translate(affinity.rotate(text_poly(label, 4.0), 45, origin=(0, 0)), cx * 0.45, cy * 0.45)
    lab2 = affinity.translate(affinity.rotate(text_poly("hub 6", 3.0), 45, origin=(0, 0)), *(np.array([cx, cy]) - d * (ring_in + 9)))
    engr = unary_union([lab, lab2])
    body = unary_union([plate, key])
    p.layers = [(0.0, TJ - 0.5, body), (TJ - 0.5, TJ, body.difference(engr)), (-LIP_D, 0.0, lips)]
    p.outline, p.cuts, p.engrave, p.half = body, Polygon(), engr, half
    return p


# ============================================================ corner piece (hooks a canvas corner, prints lips up)
class Corner(Part):
    def __init__(self, pid, name, half, edge_r, chans, rows, sizes, L, label, seed=None):
        super().__init__(pid, name, "corner", flip=True)
        self.half = half
        lips = corner_lips(L).intersection(box(-3, -3, edge_r - TIP_R, edge_r - TIP_R))
        plate = disk(edge_r - TIP_R, q=256).intersection(box(0, 0, L, L))
        dots = []
        for row, s in zip(rows, sizes):
            dots += [(q, s) for q in row]
        if seed:
            dots.append((seed, "M"))
        cuts = unary_union([c.buffer(LINE_SLOT / 2, quad_segs=16) for c in chans] +
                           [Point(q).buffer((DOT_S if s == "S" else DOT_M) / 2, quad_segs=16) for q, s in dots])
        cuts = cuts.intersection(box(0, 0, L + 5, L + 5))
        self.body = unary_union([plate, lips])
        self.cuts_, self.cuts = cuts, cuts
        self.lines = [(arc((0, 0), edge_r, 0, 90, step=0.4), "edge")] + [(c, "hole") for c in chans]
        self.dots, self.rows = dots, rows
        self.outline = self.body
        self.grooves = grooves(rows)
        thin = thin_spots(self.body.difference(cuts))
        bad = [g for g in polys_of(thin) if g.area > 0.35 and g.bounds[0] >= 0 and g.bounds[1] >= 0]
        if bad:
            self.warnings.append(f"thin wall: {len(bad)} spot(s)")
        from geom import place_label
        self.engrave = place_label(self.body, cuts.union(self.grooves), text_poly(label, 3.6), prefer=(edge_r * 0.3, edge_r * 0.3)) or Polygon()
        rel = unary_union([self.body.buffer(-EDGE_REL, join_style="mitre"), lips])
        lead = cuts.buffer(EDGE_REL, quad_segs=12)
        ins = lambda g, i: g.buffer(-0.01 * i, join_style="mitre")
        rel = lambda i: unary_union([self.body.buffer(-EDGE_REL - 0.01 * i, join_style="mitre"), ins(lips, i)])
        self.layers = [
            (0.0, EDGE_REL, rel(1).difference(cuts.buffer(EDGE_REL + 0.01))),
            (EDGE_REL, T - GROOVE_D, self.body.difference(cuts)),
            (T - GROOVE_D, T - EDGE_REL, ins(self.body, 2).difference(cuts.buffer(0.02)).difference(self.grooves)),
            (T - EDGE_REL, T, rel(3).difference(cuts.buffer(EDGE_REL + 0.03)).difference(self.grooves.buffer(0.01)).difference(self.engrave)),
            (-LIP_D, 0.0, ins(lips, 4)),
        ]
        self.positions = [("BL", 0.0), ("TL", 90.0), ("TR", 180.0), ("BR", 270.0)]
        self.placements = [(l, d, "A") for l, d in self.positions]
        self.two_faced = False
        self.teeth_at = []

    def teeth_geom(self):
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
