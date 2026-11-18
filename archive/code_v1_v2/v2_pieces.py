"""All v2 pieces: Kit 01 (20 cm), Kit 02 (30 cm outer), library centres and the Lace ring set.

Every wedge piece is one motif, clicks onto the hub with straight fins, and is used
face A then face B at each placement (unless marked one-faced).
"""
import itertools
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union, linemerge
from shapely import affinity

from geom import *  # noqa
from parts import sector, check_body
import design01 as d1
from v2 import (Piece, Corner, build_hub, build_jig, make_insert, mirror, notch_comb, around, half_plane,
                foot, arm, side_of, comb_points, NUMBERS, AXES, DIAGS, fin, ifin, slot, islot, stack, radial_rect)

IN3 = [("1", 0.0, "A"), ("2", 60.0, "A"), ("3", 120.0, "A")]       # three consecutive inner notches
ONCE = [("1", 0.0, "A")]


def faces(positions):
    return [(l, d, f) for l, d in positions for f in "AB"]


def lens(p0, p1, w):
    return vesica(p0, p1, w)


# ============================================================ Kit 01 ring "Bloom": dome + petal
DOME_R, PEARL_R, SUN_R = 22.0, 25.2, 4.5
DC = (0.0, C1)
RAYS_A = [5.625 + 22.5 * k for k in range(-4, 4)]
PET_PHI, PET_IN, PET_OUT, PET_W = 22.5, 64.0, 93.0, 20.0


def bloom_petal_true():
    return vesica(P(PET_IN, PET_PHI), P(PET_OUT, PET_PHI), PET_W)


def build_dome():
    split = 1.0
    smooth = disk(DOME_R - TIP_R, DC, q=128).intersection(half_plane(DC, 0.0, -1, offset=split))
    comb_disk = disk(PEARL_R, DC, q=128).intersection(half_plane(DC, 0.0, +1, offset=-split))
    pet = bloom_petal_true()
    keep = unary_union([pet, rot(pet, -45), rot(disk(PEARL_R + 1.9, DC, q=96), 45),
                        rot(disk(PEARL_R + 1.9, DC, q=96), -45)]).buffer(2.3)
    pearls = comb_points(DC, PEARL_R, 0.0, 112.5, 3.75,
                         keep=lambda q: rad(q) >= R_HUB + 2.6 and not keep.contains(Point(q)))
    body = unary_union([smooth, comb_disk]).difference(disk(R_HUB + CLR, q=256))
    combs = notch_comb(pearls, DOT_S / 2 + 0.05)
    sun = disk(SUN_R + TIP_R, DC, q=64)
    body = body.difference(combs).difference(sun)
    rays = [LineString([around(DC, 8.6, b), around(DC, 19.2, b)]) for b in RAYS_A]
    slots_ = unary_union([r.buffer(LINE_SLOT / 2, quad_segs=12) for r in rays])
    lines = [(a, "edge") for a in arcs_where(DC, DOME_R, lambda p: rad(p) >= C1 + 0.2)]
    lines += [(a, "edge") for a in arcs_where(DC, SUN_R, lambda p: rad(p) >= R_HUB + 0.9)]
    lines += [(r, "slot") for r in rays]
    return Piece("DM", "Dome", body, slots_, lines, [(q, "S") for q in pearls], fins=[-15.0, 15.0],
                 note="arc on the smooth edge, pearls in the notches, 8 ray slots (16 with face B), sun in the cut-out")


def build_petal():
    pet = bloom_petal_true()
    body_p = pet.buffer(-TIP_R, join_style="mitre", mitre_limit=4)
    inner_true = pet.buffer(-6.2, join_style="mitre", mitre_limit=4)
    inner_hole = inner_true.buffer(TIP_R, join_style="mitre", mitre_limit=3)
    ring = pet.buffer(-3.1, join_style="mitre", mitre_limit=4).exterior
    tips = [Point(P(PET_IN, PET_PHI)), Point(P(PET_OUT, PET_PHI))]
    n = int(ring.length / 3.6)
    pearls = []
    for i in range(n):
        q = ring.interpolate((i + 0.5) * ring.length / n).coords[0]
        if side_of(q, (0, 0), PET_PHI) > 0.6 and min(t.distance(Point(q)) for t in tips) > 4.0:
            pearls.append(q)
    attach = pet.exterior.interpolate(pet.exterior.project(Point(P(PET_IN + 5.0, PET_PHI - 4.0)))).coords[0]
    a = arm([P(R_HUB + 4.0, 10.0), P(R_HUB + 9.0, 12.5), attach], 4.6)
    body = unary_union([body_p, a, foot()]).difference(disk(R_HUB + CLR, q=256))
    cuts = unary_union([inner_hole, notch_comb(pearls, DOT_S / 2)])
    lines = [(pet.exterior, "edge"), (inner_true.exterior, "hole")]
    return Piece("PT", "Petal", body, cuts, lines, [(q, "S") for q in pearls], fins=[-15.0, 15.0],
                 note="outline on the edge, inner petal in the opening; face B closes the gap at the arm")


def build_k1():
    chans = [arc((0, 0), r, 0, 90, step=0.4) for r in (14.0, 21.0, 28.0)]
    chans += [LineString([P(14 + 2.8, 9.0 * k), P(21 - 2.8, 9.0 * k)]) for k in range(1, 10)]
    dots = [(P(24.5, 90.0 * (k + 0.5) / 10), "S") for k in range(10)]
    dots += [(P(31.5, 90.0 * (k + 0.5) / 13), "S") for k in range(13)]
    dots += [(P(7.0, 45.0), "M")]
    return Corner("K1", "Corner web 20 cm", 100.0, 35.0, chans, dots, 40.0, "K1")


# ============================================================ centres
def build_fol():
    lenses = d1.fol_lenses()
    holes = unary_union([L.buffer(TIP_R, join_style="mitre", mitre_limit=3.0) for L in lenses])
    F1 = make_insert("F1", "Flower of Life lines", holes, [(L.exterior, "hole") for L in lenses], [], IN3)
    _, F2v1 = d1.core_parts()
    dots = [(f.geom.coords[0], f.size) for f in F2v1.feats]
    F2 = make_insert("F2", "Flower of Life dots", Polygon(), [], dots, ONCE)
    return F1, F2


def build_sunflower():
    golden = 137.50776
    have, dots = [], []
    n = 1
    while True:
        r = 2.15 * math.sqrt(n)
        if r > R_INS - 1.2 - DOT_M / 2:
            break
        a = math.radians(n * golden)
        size = "S" if r < 22 else "M"
        q = (r * math.cos(a), r * math.sin(a))
        need = (DOT_M if size == "M" else DOT_S) / 2
        if all(math.dist(q, h) >= need + hs + 0.75 for h, hs in have):
            dots.append((q, size))
            have.append((q, need))
        n += 1
    dots.append(((0.0, 0.0), "M"))
    return make_insert("SF", "Sunflower", Polygon(), [], dots, ONCE)


def tri(R, rot_deg=0.0):
    return Polygon([P(R, rot_deg + 120 * k) for k in range(3)])


def build_merkaba():
    Ro, Rm, Ri = 36.5, 25.0, 13.0
    outer_hole = tri(Ro).buffer(TIP_R, join_style="mitre", mitre_limit=3)
    island = tri(Rm).buffer(-TIP_R, join_style="mitre", mitre_limit=3)
    inner_hole = tri(Ri).buffer(TIP_R, join_style="mitre", mitre_limit=3)
    bridge = box(-9.4, -Ro / 2 - 2.5, -6.8, -Rm / 2 + 1.5)          # off-axis: face B covers it
    cuts = unary_union([outer_hole.difference(island).difference(bridge), inner_hole])
    lines = [(tri(Ro).exterior, "hole"), (tri(Rm).exterior, "hole"), (tri(Ri).exterior, "hole")]
    pl = [("1", 0.0, "A"), ("1", 0.0, "B"), ("2", 60.0, "A"), ("2", 60.0, "B")]
    MK1 = make_insert("MK1", "Merkaba lines", cuts, lines, [], pl, two_faced=True)
    # dots: every vertex, every crossing of same-size up/down triangles, and the centre
    segs = []
    for R in (Ro, Rm, Ri):
        for d in (0.0, 60.0):
            segs.append(tri(R, d).exterior)
    pts = [((0.0, 0.0), "M")]
    for R in (Ro, Rm, Ri):
        for d in (0.0, 60.0):
            for k in range(3):
                pts.append((P(R, d + 120 * k), "M" if R == Ro else "S"))
    for R in (Ro, Rm, Ri):
        x = tri(R, 0).exterior.intersection(tri(R, 60).exterior)
        for g in parts(x):
            pts.append((g.coords[0], "S"))
    dots = []
    for p, s in pts:
        need = (DOT_M if s == "M" else DOT_S) / 2
        if rad(p) + need > R_INS - 0.9:
            continue
        if all(math.dist(p, q) >= need + (DOT_M if t == "M" else DOT_S) / 2 + 0.8 for q, t in dots):
            dots.append((p, s))
    MK2 = make_insert("MK2", "Merkaba dots", Polygon(), [], dots, ONCE)
    return MK1, MK2


SEED_R = 18.7


def seed_nodes():
    A = [P(SEED_R, 90 - 60 * k) for k in range(6)]
    return A


def build_seed():
    A = seed_nodes()
    twin = unary_union([disk(SEED_R + TIP_R, A[0], q=128), disk(SEED_R + TIP_R, A[3], q=128)])
    SE1 = make_insert("SE1", "Seed of Life circles", twin,
                      [(disk(SEED_R, A[0], q=128).exterior, "hole"), (disk(SEED_R, A[3], q=128).exterior, "hole")], [], IN3)
    centre = disk(SEED_R + TIP_R, q=128)
    outer = [(P(SEED_R * math.sqrt(3), 60 * k), "M") for k in range(6)]
    tips = [(P(2 * SEED_R, 90 - 60 * k), "S") for k in range(6)]
    SE2 = make_insert("SE2", "Seed of Life centre", centre, [(disk(SEED_R, q=128).exterior, "hole")], outer + tips, ONCE)
    dots = [((0.0, 0.0), "M")] + [(a, "M") for a in A] + [(P(SEED_R / 2, 90 - 60 * k), "S") for k in range(6)]
    for k in range(6):
        a, b = np.array(A[k]), np.array(A[(k + 1) % 6])
        dots += [(tuple(a + b / 2), "S"), (tuple(b + a / 2), "S")]
    SE3 = make_insert("SE3", "Seed of Life dots", Polygon(), [], dots, ONCE)
    return SE1, SE2, SE3


MT_D, MT_RHO = 15.0, 7.5


def mt_nodes():
    O = [(0.0, 0.0)]
    A = [P(MT_D, 90 - 60 * k) for k in range(6)]
    B = [P(2 * MT_D, 90 - 60 * k) for k in range(6)]
    return O, A, B


def mt_lines(direction_deg):
    """All Metatron lines (centre-to-centre) running in one exact direction (math degrees), merged."""
    O, A, B = mt_nodes()
    nodes = O + A + B
    segs = []
    for p, q in itertools.combinations(nodes, 2):
        v = np.array(q) - np.array(p)
        a = math.degrees(math.atan2(v[1], v[0])) % 180
        if abs(((a - direction_deg + 90) % 180) - 90) < 0.05:
            segs.append(LineString([p, q]))
    merged = linemerge(unary_union(segs))
    return lines_of(merged)


def build_metatron():
    O, A, B = mt_nodes()
    circ = lambda c: disk(MT_RHO + TIP_R, c, q=96)
    ring = lambda c: disk(MT_RHO, c, q=96).exterior
    MT1 = make_insert("MT1", "Metatron circles: centre + outer", unary_union([circ(c) for c in O + B]),
                      [(ring(c), "hole") for c in O + B], [(a, "M") for a in A], ONCE)
    MT2 = make_insert("MT2", "Metatron circles: inner ring", unary_union([circ(A[k]) for k in (0, 2, 4)]),
                      [(ring(A[k]), "hole") for k in (0, 2, 4)], [], [("1", 0.0, "A"), ("1", 0.0, "B")], two_faced=True)
    out = [MT1, MT2]
    fams = [("MT3", "Metatron lines 0/60/120", 60.0, [("1", 0.0, "A"), ("1", 0.0, "B"), ("2", 60.0, "A")], True),
            ("MT4", "Metatron lines 30/90/150", 90.0, IN3, False),
            ("MT5", "Metatron lines 19/41 deg", math.degrees(math.atan2(math.sqrt(3), 5)), faces([("1", 0.0), ("2", 60.0), ("3", 120.0)]), True)]
    for pid, name, ang_, pl, two in fams:
        ls = mt_lines(ang_)
        for a_, b_ in itertools.combinations(ls, 2):
            assert a_.distance(b_) >= LINE_SLOT + 0.8 or a_.intersects(b_), f"{pid}: lines too close"
        holes = unary_union([l.buffer(LINE_SLOT / 2, quad_segs=12) for l in ls])
        out.append(make_insert(pid, name, holes, [(l, "slot") for l in ls], [], pl, two_faced=two))
    dots = [((0.0, 0.0), "M")] + [(b, "M") for b in B]
    dots += [(P(MT_D / 2, 90 - 60 * k), "S") for k in range(6)]
    dots += [(tuple((np.array(A[k]) + np.array(A[(k + 1) % 6])) / 2), "S") for k in range(6)]
    dots += [(P(1.5 * MT_D, 90 - 60 * k), "S") for k in range(6)]
    out.append(make_insert("MT6", "Metatron dots", Polygon(), [], dots, ONCE))
    return out


# ============================================================ Lace ring set (20 cm, 16-fold)
LACE_PHI = 11.25
OR_R = 77.5


def lt_true():
    return vesica(P(64.5, LACE_PHI), P(75.0, LACE_PHI), 8.0)


def op_true():
    return vesica(P(81.5, LACE_PHI), P(95.0, LACE_PHI), 9.0)


def build_arch():
    ac = P(C1, LACE_PHI)
    body = disk(8.0 - TIP_R, ac, q=96).difference(disk(R_HUB + CLR, q=256))
    band = sector(R_HUB + CLR, 55.6, -21.0, 26.0)
    notch = disk(4.0 + TIP_R, ac, q=64)
    body = unary_union([body, band]).difference(notch)
    lines = [(a, "edge") for a in arcs_where(ac, 8.0, lambda p: rad(p) >= C1 + 0.2)]
    lines += [(a, "edge") for a in arcs_where(ac, 4.0, lambda p: rad(p) >= R_HUB + 0.9)]
    return Piece("AR", "Arch", body, Polygon(), lines, [], fins=[-15.0, 22.5],
                 note="double arch standing on the hub circle; face B makes the mirror arch")


def build_lotus():
    lt = lt_true()
    hole = lt.buffer(TIP_R, join_style="mitre", mitre_limit=3)
    local = lt.buffer(TIP_R + 3.4)
    body = unary_union([local, arm([P(R_HUB + 3, 0.0), P(63.0, 6.0), P(67.0, LACE_PHI - 1.0)], 7.0), foot()])
    body = body.difference(disk(R_HUB + CLR, q=256))
    return Piece("LT", "Lotus petal", body, hole, [(lt.exterior, "hole")], [], fins=[-15.0, 15.0])


def build_outer_ring():
    split = 1.0
    ov = math.degrees(3.0 / OR_R)
    smooth = sector(71.5, OR_R - TIP_R, -22.5 - ov, split)
    comb = sector(71.5, OR_R + 3.0, split, 22.5 + ov)
    keep = unary_union([op_true(), mirror(op_true()), rot(op_true(), 45), rot(mirror(op_true()), -45)]).buffer(1.9)
    pearls = comb_points((0, 0), OR_R + 3.0, 0.0, 22.5, 3.4, keep=lambda q: not keep.contains(Point(q)))
    # a pearl exactly at each outer-petal base
    pearls = [q for q in pearls if abs(ang(q)) > 2.2]
    spine = arm([P(R_HUB + 3, 0.0), P(72.5, 0.0)], 9.0)
    body = unary_union([smooth, comb, spine, foot()]).difference(disk(R_HUB + CLR, q=256)).difference(notch_comb(pearls, DOT_S / 2 + 0.05))
    lines = [(arc((0, 0), OR_R, -22.5 - ov, 22.5 + ov, step=0.25), "edge")]
    return Piece("OR", "Outer ring", body, Polygon(), lines, [(q, "S") for q in pearls], fins=[-15.0, 15.0],
                 note="ring on the smooth edge, pearls in the notches; face B does the other half")


def build_outer_petal():
    op = op_true()
    hole = op.buffer(TIP_R, join_style="mitre", mitre_limit=3)
    local = op.buffer(TIP_R + 3.4)
    body = unary_union([local, arm([P(R_HUB + 3, 0.0), P(72.0, 3.0), P(83.0, LACE_PHI - 1.0)], 7.0), foot()])
    body = body.difference(disk(R_HUB + CLR, q=256))
    return Piece("OP", "Outer petal", body, hole, [(op.exterior, "hole")], [], fins=[-15.0, 15.0])


# ============================================================ Kit 02 outer (30 cm)
C2 = 100.0
FAN_PHI, FAN_C = 22.5, P(100.0, 22.5)
GP_BASE, GP_RHO, GP_TIP, GP_MID = 102.0, 17.0, 144.0, 6.0
ST_C, ST_R, HL_R, HL_IN = P(129.0, 0.0), 22.0, 28.5, 24.25


def teardrop(base_r, rho, tip_r):
    return unary_union([disk(rho, P(base_r + rho, 0.0), q=128), Point(P(tip_r, 0.0))]).convex_hull


def gp_true():
    return teardrop(GP_BASE, GP_RHO, GP_TIP)


def kit2_keepout():
    """outer motifs in any piece's frame (great petals on one parity, stars on the other)."""
    gp = gp_true()
    st = disk(HL_R, ST_C, q=96)
    fan = disk(21.2 + 1.4, FAN_C, q=96)
    g = []
    for d in (0, 45, -45, 90, -90):
        g += [rot(gp, d), rot(st, d)]
    for d in (0, 45, -45):
        g += [rot(fan, d), rot(mirror(fan), d)]
    return unary_union(g)


def build_ring_c2():
    split = 1.0
    ov = math.degrees(3.0 / C2)
    smooth = sector(93.0, C2 - TIP_R, -22.5 - ov, split)
    comb = sector(93.0, C2 + 3.1, split, 22.5 + ov)
    ko = kit2_keepout().buffer(2.4)
    outer = comb_points((0, 0), C2 + 3.1, 0.0, 22.5, 3.6, keep=lambda q: not ko.contains(Point(q)))
    tip = [Point(P(95.0, d)) for d in (-22.5, 22.5)]
    inner = comb_points((0, 0), 96.8 + 0.25, 0.0, -22.5, 4.0, keep=lambda q: min(t.distance(Point(q)) for t in tip) > 2.5)
    spine = arm([P(R_HUB + 3, 0.0), P(94.0, 0.0)], 10.0)
    body = unary_union([smooth, comb, spine, foot()]).difference(disk(R_HUB + CLR, q=256)).difference(notch_comb(outer, DOT_S / 2 + 0.05))
    holes = notch_comb(inner, DOT_S / 2)
    lines = [(arc((0, 0), C2, -22.5 - ov, 22.5 + ov, step=0.25), "edge")]
    return Piece("RC", "Ring C2", body, holes, lines, [(q, "S") for q in outer + inner], fins=[-15.0, 15.0],
                 note="ring C2 on the smooth edge; pearls outside in the notches and inside in the holes")


def build_fan():
    fc = FAN_C
    smooth = disk(18.0 - TIP_R, fc, q=128).intersection(half_plane(fc, FAN_PHI, -1, offset=1.2))
    comb = disk(21.2, fc, q=128).intersection(half_plane(fc, FAN_PHI, +1, offset=-1.2)).difference(disk(101.5, q=256))
    low = disk(18.0 - TIP_R, fc, q=128).intersection(disk(101.5, q=256))
    ko = unary_union([rot(gp_true(), d) for d in (0, 45)] + [rot(disk(HL_R, ST_C, q=96), d) for d in (0, 45)]).buffer(2.0)
    crown = [q for q in comb_points(fc, 21.2, FAN_PHI, FAN_PHI + 105, 4.4) if rad(q) >= 103.6 and not ko.contains(Point(q))]
    body = unary_union([smooth, comb, low, arm([P(R_HUB + 3, 6.0), P(84.0, 18.5)], 8.0), foot()])
    body = body.difference(disk(R_HUB + CLR, q=256)).difference(notch_comb(crown, DOT_S / 2 + 0.05))
    arcs_ = []
    for r in (8.0, 13.0):
        arcs_ += arcs_where(fc, r, lambda p: rad(p) >= C2)
    slots_ = unary_union([a.buffer(LINE_SLOT / 2, quad_segs=12) for a in arcs_])
    rows = []
    for r, sp in ((10.5, 3.3), (15.5, 3.7)):
        rows += [q for q in comb_points(fc, r, FAN_PHI, FAN_PHI + 100, sp, inset=0.0) if rad(q) >= C2 + 2.6]
    holes = unary_union([slots_, notch_comb(rows, DOT_S / 2)])
    lines = [(a, "edge") for a in arcs_where(fc, 18.0, lambda p: rad(p) >= C2)] + [(a, "slot") for a in arcs_]
    return Piece("FN", "Rainbow fan", body, holes, lines, [(q, "S") for q in rows] + [(q, "M") for q in crown],
                 fins=[-15.0, 15.0], note="outer arc on the edge, two inner arcs in slots, dots between")


def half_ring_pearls(shape_true, offset, spacing):
    """Pearls along shape offset inward, on the clockwise half only, symmetric about the axis."""
    ring = shape_true.buffer(-offset, join_style="mitre", mitre_limit=4).exterior
    cw = ring.intersection(box(0.0, -500, 500, 500))
    ln = linemerge(cw) if cw.geom_type != "LineString" else cw
    ln = max(lines_of(ln), key=lambda l: l.length)
    n = max(1, int(round(ln.length / spacing)))
    return [ln.interpolate((i + 0.5) * ln.length / n).coords[0] for i in range(n)]


def build_great_petal():
    gp = gp_true()
    bc = P(GP_BASE + GP_RHO, 0.0)
    body_p = gp.buffer(-TIP_R, join_style="mitre", mitre_limit=4)
    pearls = [q for q in half_ring_pearls(gp, 3.0, 3.7) if q[0] > 1.0]
    attach = around(bc, GP_RHO - 4.0, 212.0)
    a = arm([P(R_HUB + 4, -14.0), P(96.0, -7.0), attach], 7.0)
    body = unary_union([body_p, a, foot(28.0)]).difference(disk(R_HUB + CLR, q=256))
    return Piece("GP", "Great petal", body, notch_comb(pearls, DOT_S / 2), [(gp.exterior, "edge")],
                 [(q, "S") for q in pearls], fins=[-22.5, 22.5], placements=faces(AXES),
                 note="outline on the edge; face B closes the gap at the arm")


def build_petal_heart():
    gp = gp_true()
    bc = P(GP_BASE + GP_RHO, 0.0)
    mid = gp.buffer(-GP_MID, join_style="mitre", mitre_limit=4)
    inner = gp.buffer(-12.0, join_style="mitre", mitre_limit=4)
    body_p = mid.buffer(-TIP_R, join_style="mitre", mitre_limit=4)
    pearls = [q for q in half_ring_pearls(gp, 9.0, 3.6) if q[0] > 1.0]
    attach = around(bc, GP_RHO - GP_MID - 4.0, 212.0)
    a = arm([P(R_HUB + 4, -14.0), P(96.0, -7.0), attach], 6.0)
    body = unary_union([body_p, a, foot(28.0)]).difference(disk(R_HUB + CLR, q=256))
    holes = unary_union([inner.buffer(TIP_R, join_style="mitre", mitre_limit=3), notch_comb(pearls, DOT_S / 2)])
    return Piece("GH", "Petal heart", body, holes, [(mid.exterior, "edge"), (inner.exterior, "hole")],
                 [(q, "S") for q in pearls], fins=[-22.5, 22.5], placements=faces(AXES))


def build_star_disc():
    sc = ST_C
    body_p = disk(ST_R - TIP_R, sc, q=128)
    field = []

    def add(q, s):
        need = (DOT_M if s == "M" else DOT_S) / 2
        if q[0] - sc[0] < need + 0.45:          # keep the axis free: face B mirrors this half
            return
        if math.dist(q, sc) > ST_R - 2.6:
            return
        allq = field + [((2 * sc[0] - p[0], p[1]), t) for p, t in field]
        if all(math.dist(q, p) >= need + (DOT_M if t == "M" else DOT_S) / 2 + 0.8 for p, t in allq):
            field.append((q, s))
    for cx, cy, s in ((5.0, 2.0, "M"), (12.5, 9.5, "S"), (9.5, -9.5, "S"), (4.0, 14.5, "S"), (4.5, -15.0, "S"), (15.5, -2.5, "S")):
        c = (sc[0] + cx, sc[1] + cy)
        add(c, s)
        for dx, dy in ((0, 3.4), (0, -3.4), (3.4, 0), (-3.4, 0)):
            add((c[0] + dx, c[1] + dy), "S")
    for cx, cy in ((10.0, 1.0), (16.0, 6.0), (14.0, -9.0), (9.0, 16.0), (2.0, 7.5), (2.0, -7.0), (11.5, -15.5)):
        add((sc[0] + cx, sc[1] + cy), "S")
    attach = around(sc, ST_R - 4.0, 205.0)
    a = arm([P(R_HUB + 4, -14.0), P(103.0, -9.0), attach], 7.0)
    body = unary_union([body_p, a, foot(28.0)]).difference(disk(R_HUB + CLR, q=256))
    holes = unary_union([Point(p).buffer((DOT_S if s == "S" else DOT_M) / 2, quad_segs=16) for p, s in field])
    return Piece("ST", "Star disc", body, holes, [(disk(ST_R, sc, q=128).exterior, "edge")], field,
                 fins=[-22.5, 22.5], placements=faces(DIAGS), note="circle on the edge, half the star field per face")


def build_halo():
    sc = ST_C
    ring_ = disk(HL_R - TIP_R, sc, q=160).difference(disk(HL_IN, sc, q=160))
    pearls = comb_points(sc, HL_IN, 0.0, 180.0, 3.9, inset=-0.25)
    attach = around(sc, HL_R - 2.0, 200.0)
    a = arm([P(R_HUB + 4, -14.0), P(99.0, -12.0), attach], 7.0)
    body = unary_union([ring_, a, foot(28.0)]).difference(disk(R_HUB + CLR, q=256)).difference(disk(HL_IN, sc, q=160))
    body = body.difference(notch_comb(pearls, DOT_S / 2 + 0.05))
    return Piece("HL", "Halo", body, Polygon(), [(disk(HL_R, sc, q=160).exterior, "edge")], [(q, "S") for q in pearls],
                 fins=[-22.5, 22.5], placements=faces(DIAGS), note="echo circle on the outer edge, pearls in the inner notches")


def build_k2():
    chans = [arc((0, 0), r, 0, 90, step=0.4) for r in (16.0, 23.0, 30.0, 37.0)]
    chans += [LineString([P(16 + 2.8, 7.5 * k), P(23 - 2.8, 7.5 * k)]) for k in range(1, 12)]
    dots = [(P(26.5, 90.0 * (k + 0.5) / 13), "S") for k in range(13)]
    dots += [(P(33.5, 90.0 * (k + 0.5) / 12), "M") for k in range(12)]
    dots += [(P(40.5, 90.0 * (k + 0.5) / 19), "S") for k in range(19)]
    dots += [(P(8.0, 45.0), "M")]
    return Corner("K2", "Corner fan 30 cm", 150.0, 44.0, chans, dots, 50.0, "K2")


# ============================================================ lock test (print first)
def build_lock_test():
    from parts import Part
    seg = sector(R_CORE, R_HUB, -30.0, 30.0)
    seg = seg.difference(unary_union([slot(7.5 * k) for k in range(-3, 4)] + [islot(0.0)]))
    tab = unary_union([sector(R_HUB + CLR, R_HUB + 12.0, -12.0, 12.0), fin(-7.5), fin(7.5)])
    tab = affinity.translate(tab, 0, 3.0)        # printed beside the segment
    ear = unary_union([sector(R_CORE - 9.0, R_INS, -9.0, 9.0), ifin(0.0)])
    ear = affinity.translate(ear, 0, -22.0)
    p = Part("T1", "Lock test", "card")
    g = unary_union([seg, tab, ear])
    p.layers = [(0.0, T, g)]
    p.outline, p.cuts, p.engrave = g, Polygon(), None
    return p


# ============================================================ everything
def build_all():
    hub = build_hub()
    F1, F2 = build_fol()
    MK1, MK2 = build_merkaba()
    SE1, SE2, SE3 = build_seed()
    MT = build_metatron()
    parts_ = dict(
        T1=build_lock_test(), H2=hub,
        J20=build_jig("J20", "Centre jig 20 cm / 8 in", 100.8, "20cm/8in"),
        J30=build_jig("J30", "Centre jig 30 cm / 12 in", 151.2, "30cm/12in", wall=5.0, open_far=True),
        F1=F1, F2=F2, SF=build_sunflower(), MK1=MK1, MK2=MK2, SE1=SE1, SE2=SE2, SE3=SE3,
        DM=build_dome(), PT=build_petal(), AR=build_arch(), LT=build_lotus(), OR=build_outer_ring(), OP=build_outer_petal(),
        K1=build_k1(),
        RC=build_ring_c2(), FN=build_fan(), GP=build_great_petal(), GH=build_petal_heart(), ST=build_star_disc(), HL=build_halo(),
        K2=build_k2(),
    )
    for m in MT:
        parts_[m.pid] = m
    return parts_


CORES = {"fol": ["F1", "F2"], "sunflower": ["SF"], "merkaba": ["MK1", "MK2"], "seed": ["SE1", "SE2", "SE3"],
         "metatron": ["MT1", "MT2", "MT3", "MT4", "MT5", "MT6"]}
RINGS = {"bloom": ["DM", "PT"], "lace": ["AR", "LT", "OR", "OP"]}
KIT2_OUTER = ["RC", "FN", "GP", "GH", "ST", "HL"]
