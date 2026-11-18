"""v3 Kit 01 "Seed Bloom" (20 x 20 cm / 8 x 8 in).

Centre  FA FB FC FD  the classic 19-circle Flower of Life, every circle a whole round opening
        FE           dots on all 37 crossing points, linked by grooves along the lattice rows
        FD           also traces the boundary circle in the lane (face A + face B close it)
Ring    R1           the circle around the hub, traced in the lane
        DM           dome: arc on the edge, pearl comb, 8 ray slots -> 16 rays with face B
        PT           petal: outline on the edge, inner petal opening, pearl row with groove
Corner  K1           corner web, hooks the canvas corner
"""
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union

from geom import *  # noqa
from parts import sector
from v3 import (Piece, Corner, build_hub, build_jig, make_insert, mirror, around, half_plane, foot, arm, side_of,
                comb, notches_at, pockets, lane_tabs, tooth, grooves, NUMBERS, AXES, DIAGS, R_LANE, C1_3, C0_3,
                R_INS3, MIN_WALL)

HALF = 100.0
IN = lambda *ks: [(str(k + 1), 60.0 * k, "A") for k in ks]


# ============================================================ Flower of Life, 19 circles
FOL_R3 = 11.5


def lattice(n):
    """hex lattice point at ring/axial coords -> canvas (one lattice direction is horizontal)."""
    pts = []
    a1 = np.array([FOL_R3, 0.0])
    a2 = np.array([FOL_R3 / 2, FOL_R3 * math.sqrt(3) / 2])
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            k = -i - j
            if max(abs(i), abs(j), abs(k)) <= n:
                pts.append(tuple(i * a1 + j * a2))
    return pts


def fol_centres():
    r = FOL_R3
    ring1 = [P(r, 90 - 60 * k) for k in range(6)]
    corners = [P(2 * r, 90 - 60 * k) for k in range(6)]
    mids = [P(r * math.sqrt(3), 60 - 60 * k) for k in range(6)]
    return ring1, corners, mids


def circle_insert(pid, name, centres, placements, two_faced=False, lane=False):
    holes = unary_union([disk(FOL_R3 + TIP_R, c, q=128) for c in centres])
    lines = [(disk(FOL_R3, c, q=128).exterior, "hole") for c in centres]
    return make_insert(pid, name, holes, lines, [], [], placements, two_faced=two_faced, lane=lane)


def build_fol():
    ring1, corners, mids = fol_centres()
    FA = circle_insert("FA", "Flower of Life: outer corners", [corners[0], corners[2], corners[4]],
                       [("1", 0.0, "A"), ("1", 0.0, "B")], two_faced=True)
    FB = circle_insert("FB", "Flower of Life: inner ring", [ring1[0]],
                       [(str(k + 1), 60.0 * k, f) for k in range(3) for f in "AB"], two_faced=True)
    FC = circle_insert("FC", "Flower of Life: outer sides", [mids[0], mids[2], mids[4]], IN(0, 1))
    FD = circle_insert("FD", "Flower of Life: centre + border", [(0.0, 0.0)], [("1", 0.0, "A"), ("1", 0.0, "B")],
                       two_faced=True, lane=True)
    pts = lattice(3)
    pts = [p for p in pts if rad(p) <= 3 * FOL_R3 + 0.01]
    dots = [(p, "S" if rad(p) > 2 * FOL_R3 + 0.01 else "M") for p in pts]
    rows = {}
    for p in pts:
        rows.setdefault(round(p[1], 2), []).append(p)
    rows = [sorted(v) for v in rows.values() if len(v) >= 2]
    FE = make_insert("FE", "Flower of Life: dots", Polygon(), [], dots, rows, [("1", 0.0, "A")])
    return [FA, FB, FC, FD, FE]


# ============================================================ ring around the hub (traced in the lane)
def build_ring1():
    ov = math.degrees(3.0 / C1_3)
    band = sector(R_LANE, R_LANE + 6.5, -22.5 - ov - 2, 22.5 + ov + 2)
    tabs = lane_tabs([-15.0, 7.5], R_HUB + CLR, R_LANE + 1.0, 5.0)
    line = arc((0, 0), C1_3, -22.5 - ov, 22.5 + ov, step=0.25)
    return Piece("R1", "Hub ring", band, Polygon(), [(line, "lane")], [], [-15.0, 7.5], tabs=tabs,
                 note="trace the circle in the gap between hub and piece; face B fills the two tab gaps")


# ============================================================ dome
DOME_R, PEARL_R, SUN_R = 22.0, 25.2, 4.5
DC = (0.0, C1_3)
RAYS_A = [5.625 + 22.5 * k for k in range(-4, 4)]
PET_PHI = 22.5


def petal_true():
    return vesica(P(65.5, PET_PHI), P(94.0, PET_PHI), 20.0)


def build_dome():
    split = 1.2
    smooth = disk(DOME_R - TIP_R, DC, q=128).intersection(half_plane(DC, 0.0, -1, offset=split))
    combd = disk(PEARL_R, DC, q=128).intersection(half_plane(DC, 0.0, +1, offset=-split))
    pet = petal_true()
    keep = unary_union([pet, rot(pet, -45), rot(disk(PEARL_R + 1.9, DC, q=96), 45),
                        rot(disk(PEARL_R + 1.9, DC, q=96), -45)]).buffer(2.3)
    pearls = comb(DC, PEARL_R, 0.0, 112.5, 4.0, keep=lambda q: rad(q) >= R_HUB + 3.0 and not keep.contains(Point(q)))
    body = unary_union([smooth, combd]).difference(disk(R_HUB + CLR, q=256))
    sun = disk(SUN_R + TIP_R, DC, q=64)
    body = body.difference(notches_at(pearls, DOT_S / 2 + 0.05)).difference(sun)
    rays = [LineString([around(DC, 9.0, b), around(DC, 18.4, b)]) for b in RAYS_A]
    slots = unary_union([r.buffer(LINE_SLOT / 2, quad_segs=12) for r in rays])
    lines = [(a, "edge") for a in arcs_where(DC, DOME_R, lambda p: rad(p) >= C1_3 + 0.2)]
    lines += [(a, "edge") for a in arcs_where(DC, SUN_R, lambda p: rad(p) >= R_HUB + 1.4)]
    lines += [(r, "hole") for r in rays]
    return Piece("DM", "Dome", body, slots, lines, [(q, "S") for q in pearls], [-15.0, 15.0],
                 note="smooth edge = arc, notches = pearls, 8 slots = rays (16 with face B), cut-out = sun")


# ============================================================ petal
def build_petal():
    pet = petal_true()
    body_p = pet.buffer(-TIP_R, join_style="mitre", mitre_limit=4)
    inner_true = pet.buffer(-7.4, join_style="mitre", mitre_limit=4)
    inner_hole = inner_true.buffer(TIP_R, join_style="mitre", mitre_limit=3)
    ring = pet.buffer(-3.7, join_style="mitre", mitre_limit=4).exterior
    tips = [Point(P(65.5, PET_PHI)), Point(P(94.0, PET_PHI))]
    n = int(ring.length / 4.0)
    pearls = []
    for i in range(n):
        q = ring.interpolate((i + 0.5) * ring.length / n).coords[0]
        if side_of(q, (0, 0), PET_PHI) > 0.8 and min(t.distance(Point(q)) for t in tips) > 5.0:
            pearls.append(q)
    pearls.sort(key=lambda q: rad(q))
    attach = pet.exterior.interpolate(pet.exterior.project(Point(P(71.0, PET_PHI - 4.5)))).coords[0]
    a = arm([P(R_HUB + 4.0, 9.0), P(R_HUB + 10.0, 13.0), attach], 6.0)
    body = unary_union([body_p, a, foot()]).difference(disk(R_HUB + CLR, q=256))
    cuts = unary_union([inner_hole, pockets(pearls, "S")])
    lines = [(pet.exterior, "edge"), (inner_true.exterior, "hole")]
    return Piece("PT", "Petal", body, cuts, lines, [(q, "S") for q in pearls], [-15.0, 15.0], rows=[pearls],
                 note="edge = petal, opening = inner petal, pockets on a groove = pearls; face B closes the arm gap")


# ============================================================ corner
def build_k1():
    radii = [14.0, 21.5, 29.0]
    chans = [arc((0, 0), r, 0, 90, step=0.4) for r in radii]
    rows, sizes = [], []
    for r in (17.75, 25.25, 32.75):
        n = int(math.radians(90) * r / 4.0)
        rows.append([P(r, 90.0 * (k + 0.5) / n) for k in range(n)])
        sizes.append("S")
    return Corner("K1", "Corner web 20 cm", HALF, 36.5, chans, rows, sizes, 40.0, "K1", seed=P(7.0, 45.0))


def build_kit1():
    parts_ = dict(H3=build_hub(), J20=build_jig("J20", "Centre jig 20 cm / 8 in", 100.8, "20cm/8in"))
    for p in build_fol():
        parts_[p.pid] = p
    parts_.update(R1=build_ring1(), DM=build_dome(), PT=build_petal(), K1=build_k1())
    return parts_


ORDER1 = ["FA", "FB", "FC", "FD", "R1", "DM", "PT", "H3", "FE", "K1"]


def painting(parts_, order=ORDER1, which=None):
    L = []
    for pid in order:
        p = parts_[pid]
        if getattr(p, "kind", "") == "hub":
            for q, s in p.dots:
                L.append(("gold" if s == "M" else "white", Point(q).buffer(DOT_DRAWN[s] / 2, quad_segs=16)))
            continue
        L += p.all_painted(which.get(pid) if which and pid in which else None) if not (which and pid in which and which[pid] == "none") else []
    return L
