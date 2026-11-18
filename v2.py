"""Stencil system v2 — reversible, one motif per piece, edges draw lines.

Rethink of v1, after feedback:
  1. REVERSIBLE: the hub's index notches sit in the MIDDLE of its thickness
     (z 0.6-1.4) and every piece's teeth sit in the same band, so a piece clicks
     in face A up OR flipped to face B. Flipping mirrors the piece about the hub
     number line, so face B draws the mirror image.
  2. ONE MOTIF PER PIECE: the dome piece only makes domes, the petal piece only
     makes petals.
  3. EDGES DRAW: a piece's outer contour is a drawing guide. Trace around the
     outside of the dome piece -> the dome arc. No channel, no bridge, no island.
  4. A + B COMPLETE EACH OTHER: what one face cannot reach, the other face does.
       - dome: face A traces the left half of the arc and drops pearls on the
         right; face B (mirror) does the opposite; rays interleave, so 8 slots
         give a 16-ray sunburst.
       - petal: the arm that holds it to the hub blocks a bit of the outline on
         one flank; face B's arm is on the other flank, so the outline closes.
         Pearls inside the petal are split the same way.
  5. DOTS: pearl combs (notches in an edge: push the tip into each notch),
     split across faces so no dot is ever made twice, and a golden-angle
     sunflower field as a core.

Rule for the painter, the same for every piece:
    at each hub number: face A -> lift, flip -> face B.
"""
import math
import numpy as np
import manifold3d as m3d
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity

from geom import *  # noqa
from parts import Part, check_body, outer_notch, outer_tooth, inner_notch, inner_ear, radial_text, sector

Z_LO, Z_HI = 0.6, 1.4       # index band, symmetric about mid-thickness (T = 2.0)
EDGE_REL = 0.3             # undercut + lead-in, the same on both faces


def mirror(g):
    """face B = face A flipped over about the hub-number line (x -> -x)."""
    return affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))


# ---------------------------------------------------------------- hub v2
def build_hub_v2():
    from parts import HUB_ROW1, HUB_ROW2
    part = Part("H2", "Hub v2 (reversible lock)", "hub")
    row1 = [Feat("dot", Point(P(HUB_ROW1, 3.75 + 7.5 * k)), size="M", group="hubdots") for k in range(48)]
    row2 = [Feat("dot", Point(P(HUB_ROW2, 3.75 + 7.5 * k)), size="S", group="hubdots2") for k in range(48)]
    part.feats = row1 + row2
    ring = annulus(R_CORE, R_HUB, q=256)
    inset = annulus(R_CORE + 0.02, R_HUB - 0.02, q=256)
    dcut = unary_union([f.cut() for f in part.feats])
    notches = unary_union([outer_notch(7.5 * k) for k in range(N_NOTCH)])
    inotch = unary_union([inner_notch(60 * k) for k in range(6)])
    pockets = unary_union([sector(46.75, 48.35, ph - 6.5, ph + 6.5).buffer(0.3).buffer(-0.3) for ph in (22.5, 142.5, 262.5)])
    engr = unary_union([radial_text(str(k + 1), HUB_ROW2, 45 * k, 2.4) for k in range(8)])
    band = ring.difference(notches).difference(inotch)
    part.layers = [
        (0.0, EDGE_REL, inset.difference(dcut.buffer(EDGE_REL)).difference(pockets)),
        (EDGE_REL, Z_LO, inset.difference(dcut)),
        (Z_LO, Z_HI, band.difference(dcut)),
        (Z_HI, T - EDGE_REL, inset.difference(dcut)),
        (T - EDGE_REL, T, inset.difference(dcut.buffer(EDGE_REL)).difference(engr)),
    ]
    part.outline = ring
    part.cuts = dcut
    part.engrave = engr
    part.notches = notches
    check_body(part, ring.difference(dcut))
    return part


# ---------------------------------------------------------------- piece builder
class Piece(Part):
    """A reversible motif piece. `lines` are the TRUE curves the motif wants (local frame,
    hub number on +y); what actually gets painted is computed from what the marker can reach."""

    def __init__(self, pid, name, body, cuts, teeth, lines=(), dots=(), label="", sym=False):
        super().__init__(pid, name, "piece", positions=[(str(k + 1), 45.0 * k) for k in range(8)])
        self.body, self.cuts_, self.teeth = body, cuts, list(teeth)
        self.lines, self.dots, self.sym = list(lines), list(dots), sym
        self.outline = unary_union([body, self.teeth_geom()])
        self.cuts = cuts
        check_body(self, body.difference(cuts))
        # labels: "A" on top, "B" on the underside (mirrored so it reads right when flipped)
        la = text_poly("A", 3.6)
        lb = mirror(text_poly("B", 3.6))
        free = body.difference(cuts.buffer(1.2)).buffer(-1.0)
        self.engrave = self._place(free, la)
        self.engrave_b = self._place(free, lb)
        self._layers()

    def teeth_geom(self):
        return unary_union([outer_tooth(ph) for ph in self.teeth])

    def _place(self, free, lab):
        from shapely.prepared import prep
        fp = prep(free)
        minx, miny, maxx, maxy = free.bounds
        best = None
        for y in np.arange(miny, maxy, 1.0):
            for x in np.arange(minx, maxx, 1.0):
                g = affinity.translate(lab, x, y)
                if fp.contains(g):
                    if best is None or abs(x) + 0.3 * y < best[0]:
                        best = (abs(x) + 0.3 * y, g)
        if best is None:
            self.warnings.append("no room for label")
            return Polygon()
        return best[1]

    def _layers(self):
        body, cuts = self.body, self.cuts_
        near_hub = disk(R_HUB + 2.5, q=256)
        rel = unary_union([body.buffer(-EDGE_REL, join_style="mitre"), body.intersection(near_hub)])
        low = body.buffer(-0.02, join_style="mitre")
        hi = unary_union([body, self.teeth_geom()])
        self.layers = [
            (0.0, EDGE_REL, rel.difference(cuts.buffer(EDGE_REL)).difference(self.engrave_b)),
            (EDGE_REL, Z_LO, low.difference(cuts)),
            (Z_LO, Z_HI, hi.difference(cuts)),
            (Z_HI, T - EDGE_REL, low.difference(cuts)),
            (T - EDGE_REL, T, rel.difference(cuts.buffer(EDGE_REL)).difference(self.engrave)),
        ]

    # what the marker paints with face A (local frame)
    def painted_a(self):
        out = []
        blocked = self.body.buffer(TIP_R - 0.06, quad_segs=16)
        holes_reach = self.cuts_.buffer(-TIP_R + 0.06, quad_segs=16)
        for g, kind in self.lines:
            if kind == "edge":
                ln = g.difference(blocked)
            else:   # inside a hole / slot
                ln = g.intersection(holes_reach.buffer(0.05))
            for l in lines_of(ln):
                out.append(("line", l.buffer(LINE_W / 2, quad_segs=8)))
        for p, size in self.dots:
            out.append(("gold" if size == "M" else "white", Point(p).buffer(DOT_DRAWN[size] / 2, quad_segs=16)))
        return out

    def painted(self, number_deg, face="A"):
        out = self.painted_a()
        if face == "B":
            out = [(c, mirror(g)) for c, g in out]
        return [(c, rot(g, number_deg)) for c, g in out]

    def placed_outline(self, number_deg, face="A"):
        g = self.outline.difference(self.cuts_)
        return rot(mirror(g) if face == "B" else g, number_deg)

    def solid_face(self, face="A"):
        m = self.solid()
        if face == "B":   # turn over about the hub-number line (y axis): x -> -x, z -> 2 - z
            m = m.rotate([0, 180, 0]).translate([0, 0, T])
        return m


def notch_comb(centres, r):
    return unary_union([Point(c).buffer(r, quad_segs=16) for c in centres])


# ---------------------------------------------------------------- DOME piece
PET_PHI, PET_IN, PET_OUT, PET_W = 22.5, 64.0, 93.0, 20.0
DOME_R, PEARL_R, SUN_R = 22.0, 25.2, 4.5
DC = (0.0, C1)
RAYS_A = [5.625 + 22.5 * k for k in range(-4, 4)]      # face B mirrors -> 16 rays


def around(c, r, a):
    return (c[0] + r * math.sin(math.radians(a)), c[1] + r * math.cos(math.radians(a)))


def build_dome():
    split = 2.2                                   # face A traces x <= split, combs x >= split
    smooth = disk(DOME_R - TIP_R, DC, q=128).intersection(box(-60, 0, split, 200))
    comb_disk = disk(PEARL_R, DC, q=128).intersection(box(split, 0, 60, 200))
    # pearls on the comb half (face A), evenly spaced, starting off-axis so A and B never double up
    sp = 3.75 / PEARL_R
    pearls = []
    j = 0
    # keep the pearl string clear of the neighbouring motifs (petals at +-22.5, next domes at +-45)
    pet = vesica(P(PET_IN, PET_PHI), P(PET_OUT, PET_PHI), PET_W)
    keep = unary_union([rot(pet, 0), rot(pet, -45), rot(disk(PEARL_R + 1.9, DC, q=96), 45),
                        rot(disk(PEARL_R + 1.9, DC, q=96), -45)]).buffer(2.3)
    while True:
        a = math.degrees((j + 0.5) * sp) + 3.0
        q = around(DC, PEARL_R - 0.25, a)
        if a > 100 or rad(q) < R_HUB + 2.6:
            break
        if not keep.contains(Point(q)):
            pearls.append(q)
        j += 1
    body = unary_union([smooth, comb_disk]).difference(disk(R_HUB + CLR, q=256))
    combs = notch_comb(pearls, DOT_S / 2 + 0.05)
    sun = disk(SUN_R + TIP_R, DC, q=64)
    slots = unary_union([LineString([around(DC, 8.6, b), around(DC, 19.2, b)]).buffer(LINE_SLOT / 2, quad_segs=12) for b in RAYS_A])
    cuts = unary_union([combs, sun, slots])
    body = body.difference(combs).difference(sun)
    cuts_inside = slots
    true_arc = [a for a in arcs_where(DC, DOME_R, lambda p: rad(p) >= C1 + 0.2)]
    true_sun = arcs_where(DC, SUN_R, lambda p: rad(p) >= R_HUB + 0.9)
    rays = [LineString([around(DC, 8.6, b), around(DC, 19.2, b)]) for b in RAYS_A]
    lines = [(a, "edge") for a in true_arc] + [(s, "edge") for s in true_sun] + [(r, "slot") for r in rays]
    pc = Piece("DM", "Dome piece", body, cuts_inside, teeth=[-15.0, 15.0], lines=lines,
               dots=[(q, "S") for q in pearls], label="DM")
    pc.combs = combs
    return pc


# ---------------------------------------------------------------- PETAL piece


def build_petal():
    pet = vesica(P(PET_IN, PET_PHI), P(PET_OUT, PET_PHI), PET_W)
    body_p = pet.buffer(-TIP_R, join_style="mitre", mitre_limit=4)
    inner_true = pet.buffer(-6.2, join_style="mitre", mitre_limit=4)
    inner_hole = inner_true.buffer(TIP_R, join_style="mitre", mitre_limit=3)
    # pearl ring inside the petal: face A gets the outer flank (away from the hub number)
    ring = pet.buffer(-3.1, join_style="mitre", mitre_limit=4).exterior
    axis_u = np.array(P(1, PET_PHI))
    n = int(ring.length / 3.6)
    pearls = []
    tips = [Point(P(PET_IN, PET_PHI)), Point(P(PET_OUT, PET_PHI))]
    for i in range(n):
        q = ring.interpolate((i + 0.5) * ring.length / n).coords[0]
        side = axis_u[0] * q[1] - axis_u[1] * q[0]         # >0: clockwise of the petal axis
        if side < -0.6 and min(t.distance(Point(q)) for t in tips) > 4.0:
            pearls.append(q)
    # arm: from a foot on the hub (teeth symmetric about the number line) to the petal's inner flank
    foot = sector(R_HUB + CLR, R_HUB + 7.0, -21.0, 21.0)
    attach = pet.exterior.interpolate(pet.exterior.project(Point(P(PET_IN + 5.0, PET_PHI - 4.0)))).coords[0]
    arm = LineString([P(R_HUB + 4.0, 10.0), P(R_HUB + 9.0, 12.5), attach]).buffer(2.3, quad_segs=8)
    body = unary_union([body_p, arm, foot]).difference(disk(R_HUB + CLR, q=256))
    dots = notch_comb(pearls, DOT_S / 2)
    cuts = unary_union([inner_hole, dots])
    lines = [(pet.exterior, "edge"), (inner_true.exterior, "hole")]
    pc = Piece("PT", "Petal piece", body, cuts, teeth=[-15.0, 15.0], lines=lines,
               dots=[(q, "S") for q in pearls], label="PT")
    return pc


# ---------------------------------------------------------------- SUNFLOWER core (dots only)
def build_sunflower():
    from parts import build_insert
    golden = 137.50776
    c = 2.15
    feats = []
    have = []
    n = 1
    while True:
        r = c * math.sqrt(n)
        if r > R_INS - 1.2 - DOT_M / 2:
            break
        a = n * golden
        size = "S" if r < 22 else "M"
        q = Point(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
        need = (DOT_M if size == "M" else DOT_S) / 2
        if all(q.distance(h) >= need + hs + 0.75 for h, hs in have):
            feats.append(Feat("dot", q, size=size, group="sunflower"))
            have.append((q, need))
        n += 1
    feats.append(Feat("dot", Point(0, 0), size="M", group="sunflower"))
    return build_insert("SF", "Sunflower core (golden angle)", feats, [("A", 0.0)], rim=1.1, label="SF", clip_lines=False)


def insert_v2(part):
    """Re-layer a v1 insert so its ear sits in the middle band (reversible, fits hub v2)."""
    disc = disk(R_INS, q=256)
    ear = inner_ear(0.0)
    cuts = part.cuts
    low = disc.buffer(-0.02)
    engr = part.engrave if part.engrave is not None else Polygon()
    part.layers = [
        (0.0, EDGE_REL, low.difference(cuts.buffer(EDGE_REL))),
        (EDGE_REL, Z_LO, low.difference(cuts)),
        (Z_LO, Z_HI, unary_union([disc, ear]).difference(cuts)),
        (Z_HI, T - EDGE_REL, low.difference(cuts)),
        (T - EDGE_REL, T, low.difference(cuts.buffer(EDGE_REL)).difference(engr)),
    ]
    return part
