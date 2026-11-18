"""Painting 02 — "Turquoise Bloom" (30 x 30 cm / 12 x 12 in canvas).

Centre : the whole Seed Bloom (H1, F1, F2, A1, B1, D1) — no reprint
Outer  : E1 = rainbow fans sitting on ring C2 (8 positions)
         D2 = ring C2 + fan dot rows + border dots (8 positions)
         P2 = great teardrop petals on the 4 axes, two outlines (positions 1 3 5 7)
         P3 = great petal dots: band row, inner row, heart, bridge dots (1 3 5 7)
         S1 = star circles on the 4 diagonals + echo bridge dots + rim dots (2 4 6 8)
         S2 = echo circle + star field (2 4 6 8)
Corner : K2 = large corner fan (4 corners)
Jig    : J30 = centre jig for 30 cm and 12 in
"""
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

from geom import *  # noqa
from parts import build_wedge, build_corner, build_jig
import design01 as d1

HALF = 150.0
EDGE = 148.0                       # plates keep 2 mm inside the canvas edge
WEDGE_POS = d1.WEDGE_POS
WEDGE_ORDER = d1.WEDGE_ORDER
AXIS_POS = [("1", 0.0), ("3", 90.0), ("5", 180.0), ("7", 270.0)]
DIAG_POS = [("2", 45.0), ("4", 135.0), ("6", 225.0), ("8", 315.0)]

C2 = 100.0                         # border ring around Seed Bloom
FAN_PHI, FAN_RADII = 22.5, (8.0, 13.0, 18.0)
FAN_C = P(C2, FAN_PHI)
PET_BASE, PET_RHO, PET_TIP, PET_MID = 102.0, 17.0, 144.0, 5.0
STAR_C, STAR_R, STAR_ECHO = P(129.0, 0.0), 22.0, 26.5


def canvas_clip(positions, half=HALF, margin=2.0):
    """Region (in the plate's own frame) that stays on the canvas at every listed position."""
    sq = box(-half + margin, -half + margin, half - margin, half - margin)
    g = None
    for _, deg in positions:
        r = rot(sq, -deg)
        g = r if g is None else g.intersection(r)
    return g


def teardrop(base_r, rho, tip_r, phi=0.0):
    c = P(base_r + rho, phi)
    return unary_union([disk(rho, c, q=96), Point(P(tip_r, phi))]).convex_hull


def great_petal():
    return teardrop(PET_BASE, PET_RHO, PET_TIP)


# ---------------------------------------------------------------- E1 fans
def layer_E1():
    f = []
    for r in FAN_RADII:
        for a in arcs_where(FAN_C, r, lambda p: rad(p) >= C2):
            f.append(Feat("chan", a, color="line", group="fan"))
    f.append(Feat("dot", Point(FAN_C), size="M", group="fancentre"))
    return f


# ---------------------------------------------------------------- D2 ring + dots
def keepouts():
    """Outer features (any position) in the D2/E1 frame, to keep border dots clear of them."""
    pet = [rot(great_petal(), a) for a in (0, 90, -90)]
    star = [rot(disk(STAR_ECHO, STAR_C), a) for a in (45, -45, 135)]
    fans = [rot(disk(FAN_RADII[-1] + 4.6, FAN_C), a) for a in (0, 45, -45)]
    return unary_union(pet + star + fans)


def layer_D2():
    f = []
    ov = math.degrees(3.0 / C2)
    f.append(Feat("chan", arc((0, 0), C2, -ov, 45 + ov, step=0.25), color="line", group="C2"))
    clear_c2 = lambda p: abs(rad(p) - C2) > LINE_SLOT / 2 + 1.0 + DOT_S / 2
    # fan dot rows (between the arcs)
    for r, sp in ((10.5, 3.3), (15.5, 3.7)):
        for a in arcs_where(FAN_C, r, lambda p: rad(p) >= C2 + 2.6):
            f += d1.dots_along(a, sp, "S", "white", "fanrow")
    # crown row just outside the biggest fan arc
    for a in arcs_where(FAN_C, 21.2, lambda p: rad(p) >= C2 + 3.0):
        f += d1.dots_along(a, 4.6, "M", "gold", "fancrown")
    ko = keepouts().buffer(2.4)
    # border dots just outside C2, between the big shapes
    for a in arcs_where((0, 0), C2 + 3.1, lambda p: 0.0 <= ang(p) < 45.0 and not ko.contains(Point(p))):
        f += d1.dots_along(a, 3.6, "S", "white", "c2out")
    # inner border dots just inside C2 (skip the Seed Bloom petal tips at 22.5)
    tip = Point(P(95.0, 22.5))
    n_in = int(round(math.radians(45) * (C2 - 2.9) / 4.2))
    for k in range(n_in):            # evenly spaced in [0, 45) so neighbouring positions never double up
        q = Point(P(C2 - 2.9, 45.0 * (k + 0.5) / n_in))
        if tip.distance(q) >= 4.5:
            f.append(Feat("dot", q, size="S", group="c2in"))
    return f


# ---------------------------------------------------------------- P2 / P3 great petals
def layer_P2():
    pet = great_petal()
    outer = LineString(pet.exterior.coords)
    tipbridge = box(-0.6, PET_TIP - 3.2, 0.6, PET_TIP + 2.0)
    f = [Feat("chan", outer, color="line", bridges=[P(PET_BASE, 0.0), tipbridge], group="petal_out"),
         Feat("hole", pet.buffer(-PET_MID, join_style="mitre", mitre_limit=5), color="line", group="petal_mid")]
    return f


def layer_P3():
    pet = great_petal()
    f = []
    ends = [Point(P(PET_BASE, 0)), Point(P(PET_TIP, 0))]
    f.append(Feat("dot", ends[0], size="M", group="petbridge"))
    f.append(Feat("dot", ends[1], size="M", group="petbridge"))
    band = pet.buffer(-PET_MID / 2, join_style="mitre", mitre_limit=5).exterior
    f += d1.dots_along(band, 3.7, "S", "white", "petband",
                       skip=lambda p: min(e.distance(Point(p)) for e in ends) < 4.6)
    inner = pet.buffer(-PET_MID - 3.0, join_style="mitre", mitre_limit=5)
    itip = Point(max(inner.exterior.coords, key=lambda q: q[1]))
    f += d1.dots_along(inner.exterior, 4.6, "M", "gold", "petinner",
                       skip=lambda p: itip.distance(Point(p)) < 3.0)
    heart = P(PET_BASE + PET_RHO, 0.0)
    f.append(Feat("dot", Point(heart), size="M", group="petheart"))
    for dr in (-6.5, 6.0, 10.5, 14.5):
        f.append(Feat("dot", Point(P(PET_BASE + PET_RHO + dr, 0.0)), size="S", group="petheart"))
    for dx in (-6.0, 6.0):
        f.append(Feat("dot", Point(heart[0] + dx, heart[1]), size="S", group="petheart"))
    return f


# ---------------------------------------------------------------- S1 / S2 star circles
ECHO_BRIDGE_ANGLES = (45.0, 135.0, 225.0, 315.0)


def around(c, r, a):
    return (c[0] + r * math.sin(math.radians(a)), c[1] + r * math.cos(math.radians(a)))


def layer_S1():
    f = [Feat("hole", disk(STAR_R, STAR_C, q=128), color="line", group="star")]
    bpts = [around(STAR_C, STAR_ECHO, a) for a in ECHO_BRIDGE_ANGLES]
    for b in bpts:
        f.append(Feat("dot", Point(b), size="M", group="echobridge"))
    rr = (STAR_R + STAR_ECHO) / 2
    n = int(round(2 * math.pi * rr / 4.0))
    for k in range(n):               # closed ring of dots, evenly spaced
        q = around(STAR_C, rr, 360.0 * (k + 0.5) / n)
        if min(math.dist(q, b) for b in bpts) >= 3.6:
            f.append(Feat("dot", Point(q), size="S", group="starrim"))
    return f


def sparkle(c, centre="M", arm=3.6):
    out = [Feat("dot", Point(c), size=centre, group="sparkle")]
    for dx, dy in ((0, arm), (0, -arm), (arm, 0), (-arm, 0)):
        out.append(Feat("dot", Point(c[0] + dx, c[1] + dy), size="S", group="sparkle"))
    return out


def layer_S2():
    echo = LineString([around(STAR_C, STAR_ECHO, a) for a in np.linspace(0, 360, 1441)])
    f = [Feat("chan", echo, color="line", bridges=[around(STAR_C, STAR_ECHO, a) for a in ECHO_BRIDGE_ANGLES], group="echo")]
    cx, cy = STAR_C
    f += sparkle((cx, cy), "M", 3.8)
    for sx in (-1, 1):
        f += sparkle((cx + sx * 10.5, cy + 7.5), "S", 3.3)
        f += sparkle((cx + sx * 9.0, cy - 10.0), "S", 3.3)
    f += sparkle((cx, cy + 14.0), "S", 3.3)
    f += sparkle((cx, cy - 15.5), "S", 3.3)
    singles = [(-16.5, -1.5), (16.5, -1.5), (-6.0, 17.5), (6.0, 17.5), (-15.5, 9.5 + 3.5), (15.5, 13.0),
               (-4.5, 4.5), (4.5, 4.5), (-15.0, -10.5), (15.0, -10.5), (0.0, 7.6)]
    have = [f_.geom for f_ in f if f_.kind == "dot"]
    for dx, dy in singles:
        q = Point(cx + dx, cy + dy)
        if math.hypot(dx, dy) <= 19.0 and all(q.distance(h) >= DOT_M / 2 + DOT_S / 2 + 0.8 for h in have):
            f.append(Feat("dot", q, size="S", group="single"))
            have.append(q)
    return f


# ---------------------------------------------------------------- K2 corners
def corner2_feats():
    f = []
    radii = [16.0, 23.0, 30.0, 37.0, 44.0]
    for r in radii:
        f.append(Feat("chan", arc((0, 0), r, 0, 90, step=0.4), color="line", group="carc"))
    for k in range(1, 12):
        phi = 7.5 * k
        f.append(Feat("chan", LineString([P(16 + 2.9, phi), P(23 - 2.9, phi)]), color="line", group="ctick"))
    for r, n, sz in [(26.5, 13, "S"), (33.5, 12, "M"), (40.5, 19, "S")]:
        for k in range(n):
            f.append(Feat("dot", Point(P(r, 90.0 * (k + 0.5) / n)), size=sz, group="cdots"))
    f.append(Feat("dot", Point(P(8.0, 45.0)), size="M", group="cseed"))
    for phi in (15.0, 30.0, 45.0, 60.0, 75.0):
        f.append(Feat("dot", Point(P(48.5, phi)), size="M" if phi == 45.0 else "S", group="caccent"))
    return f


def corner_to_canvas(g, deg):
    g = affinity.translate(g, -HALF, -HALF)
    return rot(g, deg)


# ---------------------------------------------------------------- kit
def outer_parts():
    clip8 = canvas_clip(WEDGE_POS)
    clipA = canvas_clip(AXIS_POS)
    clipD = canvas_clip(DIAG_POS)
    E1 = build_wedge("E1", "Plate E — rainbow fans", layer_E1(), teeth=[0.0, 45.0], rmax=EDGE,
                     positions=WEDGE_POS, order=WEDGE_ORDER, label="E1", clip=clip8)
    D2 = build_wedge("D2", "Plate D2 — ring + border dots", layer_D2(), teeth=[0.0, 45.0], rmax=EDGE,
                     positions=WEDGE_POS, order=WEDGE_ORDER, label="D2", clip=clip8)
    P2 = build_wedge("P2", "Plate P2 — great petals", layer_P2(), teeth=[-22.5, 22.5], rmax=EDGE,
                     positions=AXIS_POS, order=[p[0] for p in AXIS_POS], label="P2", clip=clipA)
    P3 = build_wedge("P3", "Plate P3 — petal dots", layer_P3(), teeth=[-22.5, 22.5], rmax=EDGE,
                     positions=AXIS_POS, order=[p[0] for p in AXIS_POS], label="P3", clip=clipA)
    S1 = build_wedge("S1", "Plate S1 — star circles", layer_S1(), teeth=[-22.5, 22.5], rmax=170.0,
                     positions=DIAG_POS, order=[p[0] for p in DIAG_POS], label="S1", clip=clipD)
    S2 = build_wedge("S2", "Plate S2 — echo + star field", layer_S2(), teeth=[-22.5, 22.5], rmax=170.0,
                     positions=DIAG_POS, order=[p[0] for p in DIAG_POS], label="S2", clip=clipD)
    K2 = build_corner("K2", "Corner fan 30 cm", corner2_feats(), HALF, 54.0,
                      [("BL", 0.0), ("TL", 90.0), ("TR", 180.0), ("BR", 270.0)], ["BL", "TL", "TR", "BR"], label="K2")
    J30 = build_jig("J30", "Centre Jig 30 cm / 12 in", 151.2, "30cm/12in", wall=5.0, open_far=True)
    return dict(E1=E1, D2=D2, P2=P2, P3=P3, S1=S1, S2=S2, K2=K2, J30=J30)


def build_kit():
    k1 = d1.build_kit()
    kit = {k: v for k, v in k1.items() if k in ("H1", "F1", "F2", "A1", "B1", "D1")}
    kit.update(outer_parts())
    return kit


CENTRE = ("F1", "C", "A1", "B1", "H1", "F2", "D1")
OUTER = ("E1", "P2", "S1", "S2", "D2", "P3", "K2")


def painting_layers(kit, include=CENTRE + OUTER, positions=None):
    L = d1.painting_layers(kit, include=[i for i in include if i in CENTRE], positions=positions)
    for pid in include:
        if pid in CENTRE:
            continue
        part = kit[pid]
        for lab, deg in part.positions:
            if positions and pid in positions and lab not in positions[pid]:
                continue
            if pid == "K2":
                for c, g in part.drawn_at(0):
                    L.append((c, corner_to_canvas(g, deg)))
            else:
                L += part.drawn_at(deg)
    return L
