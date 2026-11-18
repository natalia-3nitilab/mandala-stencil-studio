"""Painting 01 — "Seed Bloom" (20 x 20 cm / 8 x 8 in canvas).

Core   : Flower of Life lens field (insert F1, 3 turns) + lattice dots (insert F2)
Hub    : dotted ring (through the hub) + boundary circles traced on hub edges
Wedges : A = dome arcs + sun arcs + petal outlines
         B = sunburst rays + inner petals + echo arcs
         D = dot trails (small + medium dots)
Corners: K = corner "web" (arcs, ladder ticks, dots)
"""
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

from geom import *  # noqa
from parts import build_hub, build_insert, build_wedge, build_corner, build_jig, build_fit_card

HALF = 100.0          # canvas half size (20 cm); 8 in = 101.6 also fits
RMAX = 98.0           # wedge plates must stay on the canvas at every position
WEDGE_POS = [(str(k + 1), 45.0 * k) for k in range(8)]
WEDGE_ORDER = ["1", "3", "5", "7", "2", "4", "6", "8"]
R_IN_OK = R_HUB + 1.3 + LINE_SLOT / 2   # nearest a channel centre-line may come to the hub

# ---------------------------------------------------------------- core
FOL_R = 12.4


def fol_lattice(r=FOL_R, rmax=60.0):
    a1 = np.array([r, 0.0])
    a2 = np.array([r / 2, r * math.sqrt(3) / 2])
    pts = []
    n = int(rmax / r) + 3
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            p = i * a1 + j * a2
            if np.hypot(*p) <= rmax:
                pts.append(p)
    return pts, a1, a2


def fol_lenses(r=FOL_R, rclip=R_INS):
    pts, a1, a2 = fol_lattice(r, rclip + r)
    out = []
    for A in pts:
        B = A + a1
        C = A + a2
        D = A + a1 - a2
        lens = disk(r, tuple(C), q=96).intersection(disk(r, tuple(D), q=96))
        if lens.intersects(disk(rclip - 0.5)):
            out.append(lens)
    return out


def fol_drawn_all():
    """true FoL arcs (all three turns) clipped to the boundary — used to find boundary dots"""
    ls = []
    for deg in (0, 60, 120):
        for L in fol_lenses():
            ls.append(rot(L.exterior, deg))
    return unary_union(ls)


def core_parts():
    lenses = fol_lenses()
    f1 = [Feat("hole", L, color="line", group="fol") for L in lenses]
    F1 = build_insert("F1", "Flower of Life — lines", f1, [("A", 0.0), ("B", 60.0), ("C", 120.0)], rim=1.1, label="F1")

    pts, _, _ = fol_lattice(FOL_R, 40)
    lim = R_INS - 1.1 - DOT_M / 2
    lat = [p for p in pts if np.hypot(*p) <= lim + 1e-6]
    dots = [Feat("dot", Point(tuple(p)), color="gold", size="M" if np.hypot(*p) > 1 else "M", group="foldots") for p in lat]
    # boundary dots: where FoL arcs meet the boundary circle
    circ = disk(C0, q=256).exterior
    hits = fol_drawn_all().intersection(circ)
    angs = sorted({round(ang(h.coords[0]), 2) for h in parts(hits)})
    merged = []
    for a in angs:
        if merged and abs(a - merged[-1][-1]) < 4.2:
            merged[-1].append(a)
        else:
            merged.append([a])
    if len(merged) > 1 and (merged[0][0] + 360 - merged[-1][-1]) < 4.2:
        merged[0] = merged[-1] + [x + 360 for x in merged[0]]
        merged.pop()
    bdots = []
    for grp in merged:
        a = sum(grp) / len(grp)
        p = P(R_INS - 0.8 - DOT_S / 2 - CHAMF, a)
        if all(np.hypot(p[0] - q[0], p[1] - q[1]) > (DOT_M + DOT_S) / 2 + 0.8 for q in lat):
            bdots.append(Feat("dot", Point(p), color="gold", size="S", group="folbound"))
    F2 = build_insert("F2", "Flower of Life — dots", dots + bdots, [("A", 0.0)], rim=1.1, label="F2", clip_lines=False)
    return F1, F2


# ---------------------------------------------------------------- wedges
DOME_R = 22.0
DOME_C = P(C1, 0.0)
SUN_R = 4.5
PETAL_PHI = 22.5
PETAL_IN, PETAL_OUT, PETAL_W = 66.0, 92.0, 19.0
INNER_OFF = 4.2
ECHO_R = 26.5


def petal():
    return vesica(P(PETAL_IN, PETAL_PHI), P(PETAL_OUT, PETAL_PHI), PETAL_W)


def petal_m():  # mirrored petal on the other side of the dome (phi = -22.5)
    return vesica(P(PETAL_IN, -PETAL_PHI), P(PETAL_OUT, -PETAL_PHI), PETAL_W)


def layer_A():
    f = []
    for a in arcs_where(DOME_C, DOME_R, lambda p: rad(p) >= R_IN_OK):
        f.append(Feat("chan", a, color="line", bridges=[P(C1 + DOME_R, 0.0)], group="dome"))
    for a in arcs_where(DOME_C, SUN_R, lambda p: rad(p) >= R_IN_OK):
        f.append(Feat("chan", a, color="line", group="sun"))
    f.append(Feat("hole", petal(), color="line", group="petal"))
    return f


def layer_B():
    f = []
    # sunburst rays inside the dome
    for k in range(7):
        d = -67.5 + 22.5 * k
        s, e = 8.2, DOME_R - 1.9
        p0 = (DOME_C[0] + s * math.sin(math.radians(d)), DOME_C[1] + s * math.cos(math.radians(d)))
        p1 = (DOME_C[0] + e * math.sin(math.radians(d)), DOME_C[1] + e * math.cos(math.radians(d)))
        f.append(Feat("chan", LineString([p0, p1]), color="line", group="ray"))
    # inner petal
    ip = petal().buffer(-INNER_OFF, join_style="mitre", mitre_limit=5)
    f.append(Feat("hole", ip, color="line", group="petal_in"))
    # echo arc around the dome, stopping short of the petals
    keep_out = unary_union([petal(), petal_m()]).buffer(2.6)
    for a in arcs_where(DOME_C, ECHO_R, lambda p: rad(p) >= 63.0 and not keep_out.contains(Point(p))):
        if a.length > 8:
            f.append(Feat("chan", a, color="line", group="echo"))
    return f


def dots_along(line, spacing, size, color, group, skip=lambda p: False, phase=0.5):
    L = line.length
    n = max(1, int(L / spacing))
    sp = L / n
    out = []
    for i in range(n + (0 if line.is_ring else 1)):
        d = (i + phase) * sp if line.is_ring else i * sp
        if d > L:
            break
        p = line.interpolate(d).coords[0]
        if not skip(p):
            out.append(Feat("dot", Point(p), color=color, size=size, group=group))
    return out


def layer_D():
    f = []
    # bridge dot on the dome apex + sun centre dot
    f.append(Feat("dot", Point(P(C1 + DOME_R, 0.0)), color="gold", size="M", group="apex"))
    f.append(Feat("dot", Point(P(R_HUB + 2.6, 0.0)), color="gold", size="M", group="suncentre"))
    # dot trail just outside the dome arc, between dome and echo
    mid = (DOME_R + ECHO_R) / 2
    keep_out = unary_union([petal(), petal_m()]).buffer(2.4)
    apex = Point(P(C1 + DOME_R, 0.0))
    for a in arcs_where(DOME_C, mid, lambda p: rad(p) >= R_HUB + 3.2 and not keep_out.contains(Point(p))):
        f += dots_along(a, 3.7, "S", "gold", "dometrail", skip=lambda p: apex.distance(Point(p)) < 3.0)
    # dots in the petal band (between outer and inner petal)
    band = petal().buffer(-INNER_OFF / 2, join_style="mitre", mitre_limit=5).exterior
    tips = [Point(P(PETAL_IN, PETAL_PHI)), Point(P(PETAL_OUT, PETAL_PHI))]
    f += dots_along(band, 3.6, "S", "white", "petalband", skip=lambda p: min(t.distance(Point(p)) for t in tips) < 4.2)
    # petal tip trail (outward)
    for i, r in enumerate([PETAL_OUT + 3.0]):
        f.append(Feat("dot", Point(P(r, PETAL_PHI)), color="gold", size="M", group="tiptrail"))
    # ray-tip dots (between the rays, just inside the dome)
    for k in range(6):
        dd = -56.25 + 22.5 * k
        q = (DOME_C[0] + 17.6 * math.sin(math.radians(dd)), DOME_C[1] + 17.6 * math.cos(math.radians(dd)))
        f.append(Feat("dot", Point(q), color="white", size="S", group="raytips"))
    # crown above each dome, beyond the echo arc
    pk = unary_union([petal(), petal_m()]).buffer(2.6)
    for phi, r, sz in [(0, 86.0, "M"), (-5.6, 85.2, "S"), (5.6, 85.2, "S"), (-10.8, 83.2, "S"), (10.8, 83.2, "S")]:
        q = P(r, phi)
        if not pk.contains(Point(q)):
            f.append(Feat("dot", Point(q), color="gold" if sz == "M" else "white", size=sz, group="crown"))
    # petal heart: a short line of dots along the petal axis
    for r in np.linspace(PETAL_IN + 9.5, PETAL_OUT - 9.5, 4):
        f.append(Feat("dot", Point(P(r, PETAL_PHI)), color="gold", size="S", group="heart"))
    return f


def wedge_parts():
    A = build_wedge("A1", "Plate A — domes + petals", layer_A(), teeth=[-30.0, 30.0], rmax=RMAX,
                    positions=WEDGE_POS, order=WEDGE_ORDER, label="A")
    B = build_wedge("B1", "Plate B — rays + inner petals", layer_B(), teeth=[-30.0, 30.0], rmax=RMAX,
                    positions=WEDGE_POS, order=WEDGE_ORDER, label="B")
    D = build_wedge("D1", "Plate D — dot trails", layer_D(), teeth=[-30.0, 30.0], rmax=RMAX,
                    positions=WEDGE_POS, order=WEDGE_ORDER, label="D")
    return A, B, D


# ---------------------------------------------------------------- corners
def corner_feats():
    f = []
    radii = [14.0, 21.0, 28.0, 35.0]
    keep = lambda p: p[0] >= 0 and p[1] >= 0
    for r in radii:
        a = arc((0, 0), r, 0, 90, step=0.5)
        f.append(Feat("chan", a, color="line", group="carc"))
    # ladder ticks between 14 and 21
    for k in range(1, 10):
        phi = 9.0 * k
        p0, p1 = P(14 + 2.9, phi), P(21 - 2.9, phi)
        f.append(Feat("chan", LineString([p0, p1]), color="line", group="ctick"))
    # dot rows between 21-28 (small) and 28-35 (small)
    for r, n, col in [(24.5, 10, "gold"), (31.5, 13, "white")]:
        for k in range(n):
            phi = 90.0 * (k + 0.5) / n
            f.append(Feat("dot", Point(P(r, phi)), color=col, size="S", group="cdots"))
    # corner seed dot + outer accents
    f.append(Feat("dot", Point(P(7.0, 45.0)), color="gold", size="M", group="cseed"))
    for phi in (22.5, 45.0, 67.5):
        f.append(Feat("dot", Point(P(39.5, phi)), color="gold", size="M", group="caccent"))
    return f


def corner_part():
    feats = corner_feats()
    positions = [("BL", 0.0), ("TL", 90.0), ("TR", 180.0), ("BR", 270.0)]
    return build_corner("K1", "Corner web", feats, HALF, 46.0, positions, [p[0] for p in positions], label="K")


def corner_to_canvas(g, deg):
    """corner coords (corner at 0,0) -> canvas coords for the corner reached by rotating deg clockwise
    from bottom-left."""
    from shapely import affinity as af
    g = af.translate(g, -HALF, -HALF)
    return rot(g, deg)


# ---------------------------------------------------------------- kit
def build_kit():
    hub = build_hub()
    F1, F2 = core_parts()
    A, B, D = wedge_parts()
    K = corner_part()
    J = build_jig("J20", "Centre Jig 20 cm / 8 in", 100.8, "20cm/8in")
    T0 = build_fit_card()
    return dict(T0=T0, J20=J, H1=hub, F1=F1, F2=F2, A1=A, B1=B, D1=D, K1=K)


def ring_line(r):
    return disk(r + LINE_W / 2, q=256).difference(disk(r - LINE_W / 2, q=256))


def painting_layers(kit, include=("F1", "C", "A1", "B1", "H1", "F2", "D1", "K1"), positions=None):
    """(color, geom) list for the painting. include = which steps; positions = {pid: [labels]} to limit."""
    L = []
    for pid in include:
        if pid == "C":
            L.append(("line", ring_line(C0)))
            L.append(("line", ring_line(C1)))
            continue
        part = kit[pid]
        for lab, deg in part.positions:
            if positions and pid in positions and lab not in positions[pid]:
                continue
            if pid == "K1":
                for c, g in part.drawn_at(0):
                    L.append((c, corner_to_canvas(g, deg)))
            else:
                L += part.drawn_at(deg)
    return L
