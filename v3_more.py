"""v3 Kit 02 (30 cm outer ring), library centres and the Lace ring set."""
import itertools
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union, linemerge

from geom import *  # noqa
from parts import sector
from v3 import (Piece, Corner, build_jig, make_insert, mirror, around, half_plane, foot, arm, side_of, comb,
                notches_at, pockets, NUMBERS, AXES, DIAGS, C1_3, R_INS3, GROOVE_W)

FACES = lambda pos: [(l, d, f) for l, d in pos for f in "AB"]
IN = lambda *ks: [(str(k + 1), 60.0 * k, "A") for k in ks]
INAB = lambda *ks: [(str(k + 1), 60.0 * k, f) for k in ks for f in "AB"]
ONCE = [("1", 0.0, "A")]


def holes_of(dots):
    return unary_union([pockets([q for q, s in dots if s == "S"], "S"), pockets([q for q, s in dots if s == "M"], "M")])


def greedy(cands, existing=(), gap=1.6):
    """keep candidate dots that leave >= gap of plastic to every kept dot (and mirrored ones if given)."""
    out = list(existing)
    for q, s in cands:
        rq = (DOT_M if s == "M" else DOT_S) / 2
        if all(math.dist(q, p) >= rq + (DOT_M if t == "M" else DOT_S) / 2 + gap for p, t in out):
            out.append((q, s))
    return out[len(existing):]


# ============================================================ Kit 02 outer (30 cm)
C2 = 100.0
FAN_PHI, FAN_C = 22.5, P(100.0, 22.5)
GP_BASE, GP_RHO, GP_TIP, GP_MID = 102.0, 17.0, 144.0, 6.5
ST_C, ST_R, HL_R, HL_IN = P(129.0, 0.0), 22.0, 28.8, 24.3


def teardrop(base_r, rho, tip_r):
    return unary_union([disk(rho, P(base_r + rho, 0.0), q=128), Point(P(tip_r, 0.0))]).convex_hull


def gp_true():
    return teardrop(GP_BASE, GP_RHO, GP_TIP)


def kit2_keepout():
    gp, st = gp_true(), disk(HL_R, ST_C, q=96)
    fan = disk(23.4 + 1.6, FAN_C, q=96)
    g = [rot(gp, d) for d in (0, 45, -45, 90, -90)] + [rot(st, d) for d in (0, 45, -45, 90, -90)]
    g += [rot(fan, d) for d in (0, 45, -45)] + [rot(mirror(fan), d) for d in (0, 45, -45)]
    return unary_union(g)


def build_ring_c2():
    split, ov = 1.2, math.degrees(3.0 / C2)
    smooth = sector(92.0, C2 - TIP_R, -22.5 - ov, split)
    combd = sector(92.0, C2 + 3.1, split, 22.5 + ov)
    ko = kit2_keepout().buffer(2.4)
    outer = comb((0, 0), C2 + 3.1, 0.0, 22.5, 4.0, keep=lambda q: not ko.contains(Point(q)))
    tip = [Point(P(95.5, d)) for d in (-22.5, 22.5)]
    inner = [P(96.2, -22.5 * (j + 0.5) / 6) for j in range(6)]
    inner = [q for q in inner if min(t.distance(Point(q)) for t in tip) > 2.8]
    spine = arm([P(R_HUB + 3, 0.0), P(93.0, 0.0)], 10.0)
    body = unary_union([smooth, combd, spine, foot()]).buffer(0.6).buffer(-0.6)       # fillet the inside corners
    body = body.difference(disk(R_HUB + CLR, q=256)).difference(notches_at(outer, DOT_S / 2 + 0.05))
    lines = [(arc((0, 0), C2, -22.5 - ov, 22.5 + ov, step=0.25), "edge")]
    return Piece("RC", "Ring C2", body, pockets(inner, "S"), lines, [(q, "S") for q in outer + inner], [-15.0, 15.0],
                 rows=[inner], note="smooth edge = ring, notches = outer pearls, grooved pockets = inner pearls")


def build_fan():
    fc = FAN_C
    smooth = disk(20.0 - TIP_R, fc, q=128).intersection(half_plane(fc, FAN_PHI, -1, offset=1.2))
    combd = disk(23.4, fc, q=128).intersection(half_plane(fc, FAN_PHI, +1, offset=-1.2)).difference(disk(101.5, q=256))
    low = disk(20.0 - TIP_R, fc, q=128).intersection(disk(101.5, q=256))
    ko = unary_union([rot(gp_true(), d) for d in (0, 45)] + [rot(disk(HL_R, ST_C, q=96), d) for d in (0, 45)]).buffer(2.0)
    crown = [q for q in comb(fc, 23.4, FAN_PHI, FAN_PHI + 105, 4.8) if rad(q) >= 104.0 and not ko.contains(Point(q))]
    body = unary_union([smooth, combd, low, arm([P(R_HUB + 3, 6.0), P(84.0, 18.5)], 8.0), foot()])
    body = body.difference(disk(R_HUB + CLR, q=256)).difference(notches_at(crown, DOT_M / 2 + 0.05))
    body = body.buffer(-0.8).buffer(0.8).difference(disk(R_HUB + CLR, q=256))   # drop slivers left by the comb
    arcs_ = []
    for r in (7.0, 12.0):
        arcs_ += arcs_where(fc, r, lambda p: rad(p) >= C2)
    slots = unary_union([a.buffer(LINE_SLOT / 2, quad_segs=12) for a in arcs_])
    row = [q for q in comb(fc, 16.0, FAN_PHI, FAN_PHI + 100, 4.0, inset=0.0) if rad(q) >= C2 + 2.8]
    lines = [(a, "edge") for a in arcs_where(fc, 20.0, lambda p: rad(p) >= C2)] + [(a, "hole") for a in arcs_]
    return Piece("FN", "Rainbow fan", body, unary_union([slots, pockets(row, "S")]), lines,
                 [(q, "S") for q in row] + [(q, "M") for q in crown], [-15.0, 15.0], rows=[row],
                 note="edge = outer arc, slots = inner arcs, grooved pockets + crown notches = dots")


def half_ring(shape, offset, spacing):
    ring = shape.buffer(-offset, join_style="mitre", mitre_limit=4).exterior
    cw = ring.intersection(box(0.0, -500, 500, 500))
    ln = max(lines_of(linemerge(cw) if cw.geom_type != "LineString" else cw), key=lambda l: l.length)
    n = max(1, int(round(ln.length / spacing)))
    pts = [ln.interpolate((i + 0.5) * ln.length / n).coords[0] for i in range(n)]
    return sorted(pts, key=lambda q: -q[1])


def build_great_petal():
    gp = gp_true()
    bc = P(GP_BASE + GP_RHO, 0.0)
    pearls = [q for q in half_ring(gp, 3.6, 4.0) if q[0] > 1.6]
    a = arm([P(R_HUB + 4, -14.0), P(96.0, -7.0), around(bc, GP_RHO - 4.5, 212.0)], 7.0)
    body = unary_union([gp.buffer(-TIP_R, join_style="mitre", mitre_limit=4), a, foot(29.0)]).difference(disk(R_HUB + CLR, q=256))
    return Piece("GP", "Great petal", body, pockets(pearls, "S"), [(gp.exterior, "edge")], [(q, "S") for q in pearls],
                 [-22.5, 22.5], rows=[pearls], placements=FACES(AXES), note="edge = outline, grooved pockets = pearls")


def build_petal_heart():
    gp = gp_true()
    bc = P(GP_BASE + GP_RHO, 0.0)
    mid = gp.buffer(-GP_MID, join_style="mitre", mitre_limit=4)
    inner = gp.buffer(-13.4, join_style="mitre", mitre_limit=4)
    pearls = [q for q in half_ring(gp, 9.95, 4.0) if q[0] > 1.6]
    a = arm([P(R_HUB + 4, -14.0), P(96.0, -7.0), around(bc, GP_RHO - GP_MID - 4.0, 212.0)], 6.0)
    body = unary_union([mid.buffer(-TIP_R, join_style="mitre", mitre_limit=4), a, foot(29.0)]).difference(disk(R_HUB + CLR, q=256))
    holes = unary_union([inner.buffer(TIP_R, join_style="mitre", mitre_limit=3), pockets(pearls, "S")])
    return Piece("GH", "Petal heart", body, holes, [(mid.exterior, "edge"), (inner.exterior, "hole")],
                 [(q, "S") for q in pearls], [-22.5, 22.5], rows=[pearls], placements=FACES(AXES))


def build_star_disc():
    sc = ST_C
    field, rows = [], []

    def mirrored(lst):
        return [((2 * sc[0] - q[0], q[1]), s) for q, s in lst]
    for cx, cy, s in ((6.0, 2.0, "M"), (12.5, 10.5, "S"), (10.0, -10.0, "S"), (4.5, 14.5, "S"), (5.0, -15.5, "S")):
        c = (sc[0] + cx, sc[1] + cy)
        arm4 = [(c[0], c[1] + 4.0), (c[0], c[1] - 4.0), (c[0] + 4.0, c[1]), (c[0] - 4.0, c[1])]
        cand = [(c, s)] + [(q, "S") for q in arm4]
        cand = [(q, t) for q, t in cand if q[0] - sc[0] >= (DOT_M if t == "M" else DOT_S) / 2 + 0.85 and math.dist(q, sc) <= ST_R - 3.0]
        kept = greedy(cand, field + mirrored(field))
        field += kept
        kq = [q for q, _ in kept]
        if c in kq:
            for q in kq:
                if q != c:
                    rows.append([c, q])
    a = arm([P(R_HUB + 4, -14.0), P(103.0, -9.0), around(sc, ST_R - 4.5, 205.0)], 7.0)
    body = unary_union([disk(ST_R - TIP_R, sc, q=128), a, foot(29.0)]).difference(disk(R_HUB + CLR, q=256))
    return Piece("ST", "Star disc", body, holes_of(field), [(disk(ST_R, sc, q=128).exterior, "edge")], field,
                 [-22.5, 22.5], rows=rows, placements=FACES(DIAGS), note="edge = circle, sparkles = pockets on cross grooves")


def build_halo():
    sc = ST_C
    pearls = comb(sc, HL_IN, 0.0, 180.0, 4.2, inset=-0.25)
    a = arm([P(R_HUB + 4, -14.0), P(99.0, -12.0), around(sc, HL_R - 2.0, 200.0)], 7.0)
    ring_ = disk(HL_R - TIP_R, sc, q=160).difference(disk(HL_IN, sc, q=160))
    body = unary_union([ring_, a, foot(29.0)]).difference(disk(R_HUB + CLR, q=256)).difference(disk(HL_IN, sc, q=160))
    body = body.difference(notches_at(pearls, DOT_S / 2 + 0.05))
    return Piece("HL", "Halo", body, Polygon(), [(disk(HL_R, sc, q=160).exterior, "edge")], [(q, "S") for q in pearls],
                 [-22.5, 22.5], placements=FACES(DIAGS), note="outer edge = echo circle, inner notches = pearls")


def build_k2():
    radii = [16.0, 24.0, 32.0, 40.0]
    chans = [arc((0, 0), r, 0, 90, step=0.4) for r in radii]
    rows, sizes = [], []
    for r, s in ((20.0, "S"), (28.0, "M"), (36.0, "S"), (43.75, "S")):
        n = int(math.radians(90) * r / (4.0 if s == "S" else 4.8))
        rows.append([P(r, 90.0 * (k + 0.5) / n) for k in range(n)])
        sizes.append(s)
    return Corner("K2", "Corner fan 30 cm", 150.0, 47.5, chans, rows, sizes, 54.0, "K2", seed=P(8.0, 45.0))


# ============================================================ library centres (inserts)
def build_sunflower():
    golden = 137.50776
    dots = []
    for n in range(1, 600):
        r = 2.35 * math.sqrt(n)
        if r > R_INS3 - 1.6 - DOT_M / 2:
            break
        a = math.radians(n * golden)
        dots.append(((r * math.cos(a), r * math.sin(a)), "S" if r < 20 else "M", n))
    kept = greedy([(q, s) for q, s, _ in dots], [((0.0, 0.0), "M")])
    kept = [((0.0, 0.0), "M")] + kept
    # grooves along the 21 golden spirals: link each dot to its nearest kept neighbour 21 steps out
    idx = {q: n for q, s, n in dots}
    byn = {idx[q]: q for q, s in kept if q in idx}
    rows = []
    for n, q in byn.items():
        if n + 21 in byn:
            rows.append([q, byn[n + 21]])
    return make_insert("SF", "Sunflower", Polygon(), [], kept, rows, ONCE, note="golden-angle dots on 21 spiral grooves")


def tri(R, rot_deg=0.0):
    return Polygon([P(R, rot_deg + 120 * k) for k in range(3)])


def build_merkaba():
    Ro, Rm, Ri = 34.5, 23.5, 12.0
    outer_hole = tri(Ro).buffer(TIP_R, join_style="mitre", mitre_limit=3)
    island = tri(Rm).buffer(-TIP_R - 0.8, join_style="mitre", mitre_limit=3).buffer(0.8)
    inner_hole = tri(Ri).buffer(TIP_R, join_style="mitre", mitre_limit=3)
    bridge = box(-10.0, -Ro / 2 - 2.5, -7.0, -Rm / 2 + 1.5)
    cuts = unary_union([outer_hole.difference(island).difference(bridge), inner_hole])
    lines = [(tri(R).exterior, "hole") for R in (Ro, Rm, Ri)]
    MK1 = make_insert("MK1", "Merkaba lines", cuts, lines, [], [], INAB(0, 1), two_faced=True, lane=True,
                      note="outer and inner triangles inside the openings, middle triangle around the island")
    cand = [((0.0, 0.0), "M")]
    for R in (Ro, Rm, Ri):
        for d in (0.0, 60.0):
            cand += [(P(R, d + 120 * k), "M" if R == Ro else "S") for k in range(3)]
        x = tri(R, 0).exterior.intersection(tri(R, 60).exterior)
        cand += [(g.coords[0], "S") for g in parts(x)]
    cand = [(q, s) for q, s in cand if rad(q) + (DOT_M if s == "M" else DOT_S) / 2 <= R_INS3 - 1.6]
    dots = greedy(cand)
    rows = []
    for R in (Ro, Rm, Ri):
        ring = [q for q, s in dots if abs(rad(q) - R) < 0.05]
        ring.sort(key=lambda q: ang(q))
        if len(ring) >= 3:
            rows.append(ring + [ring[0]])
    MK2 = make_insert("MK2", "Merkaba dots", Polygon(), [], dots, rows, ONCE)
    return MK1, MK2


SEED_R3 = 17.0


def build_seed():
    A = [P(SEED_R3, 90 - 60 * k) for k in range(6)]
    SE1 = make_insert("SE1", "Seed of Life: petals", disk(SEED_R3 + TIP_R, A[0], q=128),
                      [(disk(SEED_R3, A[0], q=128).exterior, "hole")], [], [], INAB(0, 1, 2), two_faced=True)
    outer = [(P(SEED_R3 * math.sqrt(3), 60 * k), "M") for k in range(6)]
    SE2 = make_insert("SE2", "Seed of Life: centre + border", disk(SEED_R3 + TIP_R, q=128),
                      [(disk(SEED_R3, q=128).exterior, "hole")], [], [], [("1", 0.0, "A"), ("1", 0.0, "B")],
                      two_faced=True, lane=True)
    dots = [((0.0, 0.0), "M")] + [(a, "M") for a in A] + [(P(SEED_R3 / 2, 90 - 60 * k), "S") for k in range(6)] + outer
    for k in range(6):
        a, b = np.array(A[k]), np.array(A[(k + 1) % 6])
        dots += [(tuple(a + b / 2), "S"), (tuple(b + a / 2), "S")]
    dots += [(P(2 * SEED_R3, 90 - 60 * k), "S") for k in range(6)]
    dots = greedy(dots)
    spokes = [[(0.0, 0.0), P(SEED_R3 / 2, 90 - 60 * k), A[k]] for k in range(6)]
    SE3 = make_insert("SE3", "Seed of Life: dots", Polygon(), [], dots, spokes, ONCE)
    return SE1, SE2, SE3


MT_RHO = 6.9
MT_D = 2 * MT_RHO


def mt_nodes():
    return [(0.0, 0.0)], [P(MT_D, 90 - 60 * k) for k in range(6)], [P(2 * MT_D, 90 - 60 * k) for k in range(6)]


def mt_lines(direction_deg):
    O, A, B = mt_nodes()
    segs = []
    for p, q in itertools.combinations(O + A + B, 2):
        v = np.array(q) - np.array(p)
        a = math.degrees(math.atan2(v[1], v[0])) % 180
        if abs(((a - direction_deg + 90) % 180) - 90) < 0.05:
            segs.append(LineString([p, q]))
    return lines_of(linemerge(unary_union(segs)))


def build_metatron():
    O, A, B = mt_nodes()
    circ = lambda c: disk(MT_RHO + TIP_R, c, q=96)
    ring = lambda c: disk(MT_RHO, c, q=96).exterior
    out = [make_insert("MT1", "Metatron: centre + outer circles", unary_union([circ(c) for c in O + B]),
                       [(ring(c), "hole") for c in O + B], [], [], [("1", 0.0, "A"), ("1", 0.0, "B")],
                       two_faced=True, lane=True),
           make_insert("MT2", "Metatron: inner circles", unary_union([circ(A[k]) for k in (0, 2, 4)]),
                       [(ring(A[k]), "hole") for k in (0, 2, 4)], [], [], [("1", 0.0, "A"), ("1", 0.0, "B")], two_faced=True)]
    fams = [("MT3", "Metatron lines 0/60/120", 60.0, [("1", 0.0, "A"), ("1", 0.0, "B"), ("2", 60.0, "A")], True),
            ("MT4", "Metatron lines 30/90/150", 90.0, IN(0, 1, 2), False),
            ("MT5", "Metatron lines 19/41", math.degrees(math.atan2(math.sqrt(3), 5)), INAB(0, 1, 2), True)]
    for pid, name, a_, pl, two in fams:
        ls = mt_lines(a_)
        holes = unary_union([l.buffer(LINE_SLOT / 2, quad_segs=12) for l in ls])
        out.append(make_insert(pid, name, holes, [(l, "hole") for l in ls], [], [], pl, two_faced=two))
    dots = [((0.0, 0.0), "M")] + [(b, "M") for b in B] + [(a, "M") for a in A] + [(P(MT_D / 2, 90 - 60 * k), "S") for k in range(6)]
    dots += [(P(1.5 * MT_D, 90 - 60 * k), "S") for k in range(6)]
    dots = greedy(dots)
    rows = [[(0.0, 0.0), P(MT_D / 2, 90 - 60 * k), A[k], P(1.5 * MT_D, 90 - 60 * k), B[k]] for k in range(6)]
    out.append(make_insert("MT6", "Metatron dots", Polygon(), [], dots, rows, ONCE))
    return out


# ============================================================ Lace ring set (20 cm, 16-fold)
LACE_PHI, OR_R = 11.25, 77.5


def lt_true():
    return vesica(P(65.5, LACE_PHI), P(75.0, LACE_PHI), 8.0)


def op_true():
    return vesica(P(81.5, LACE_PHI), P(95.0, LACE_PHI), 9.0)


def build_arch():
    """Arches stand on a base circle that the piece's own band edge draws: no gaps at the feet."""
    ac = P(C1_3, LACE_PHI)
    base_r = 56.8 + TIP_R
    body = unary_union([disk(8.0 - TIP_R, ac, q=96), sector(R_HUB + CLR, 56.8, -24.0, 26.0)])
    body = body.difference(disk(R_HUB + CLR, q=256)).difference(disk(4.0 + TIP_R, ac, q=64))
    lines = [(a, "edge") for a in arcs_where(ac, 8.0, lambda p: rad(p) >= base_r - 0.3)]
    lines += [(a, "edge") for a in arcs_where(ac, 4.0, lambda p: rad(p) >= C1_3 + 0.6)]
    lines += [(arc((0, 0), base_r, -23.0, 25.0, step=0.25), "edge")]
    return Piece("AR", "Arch", body, Polygon(), lines, [], [-15.0, 22.5],
                 note="band edge = base circle, round edge = arch, cut-out = inner arch")


def build_lotus():
    lt = lt_true()
    body = unary_union([lt.buffer(TIP_R + 3.4), arm([P(R_HUB + 3, 0.0), P(63.0, 6.0), P(67.5, LACE_PHI - 1.0)], 7.0), foot()])
    body = body.difference(disk(R_HUB + CLR, q=256))
    return Piece("LT", "Lotus petal", body, lt.buffer(TIP_R, join_style="mitre", mitre_limit=3), [(lt.exterior, "hole")],
                 [], [-15.0, 15.0])


def build_outer_ring():
    split, ov = 1.2, math.degrees(3.0 / OR_R)
    smooth = sector(71.5, OR_R - TIP_R, -22.5 - ov, split)
    combd = sector(71.5, OR_R + 3.0, split, 22.5 + ov)
    keep = unary_union([op_true(), mirror(op_true()), rot(op_true(), 45), rot(mirror(op_true()), -45)]).buffer(1.9)
    pearls = [q for q in comb((0, 0), OR_R + 3.0, 0.0, 22.5, 4.0, keep=lambda q: not keep.contains(Point(q))) if abs(ang(q)) > 2.4]
    body = unary_union([smooth, combd, arm([P(R_HUB + 3, 0.0), P(70.5, 0.0)], 9.0), foot()]).buffer(0.6).buffer(-0.6)
    body = body.difference(disk(R_HUB + CLR, q=256)).difference(notches_at(pearls, DOT_S / 2 + 0.05))
    return Piece("OR", "Outer ring", body, Polygon(), [(arc((0, 0), OR_R, -22.5 - ov, 22.5 + ov, step=0.25), "edge")],
                 [(q, "S") for q in pearls], [-15.0, 15.0], note="smooth edge = ring, notches = pearls")


def build_outer_petal():
    op = op_true()
    body = unary_union([op.buffer(TIP_R + 3.4), arm([P(R_HUB + 3, 0.0), P(72.0, 3.0), P(83.0, LACE_PHI - 1.0)], 7.0), foot()])
    body = body.difference(disk(R_HUB + CLR, q=256))
    return Piece("OP", "Outer petal", body, op.buffer(TIP_R, join_style="mitre", mitre_limit=3), [(op.exterior, "hole")],
                 [], [-15.0, 15.0])


def build_more():
    out = dict(J30=build_jig("J30", "Centre jig 30 cm / 12 in", 151.2, "30cm/12in", wall=5.0, open_far=True),
               RC=build_ring_c2(), FN=build_fan(), GP=build_great_petal(), GH=build_petal_heart(), ST=build_star_disc(),
               HL=build_halo(), K2=build_k2(), SF=build_sunflower())
    for p in build_merkaba() + build_seed() + tuple(build_metatron()):
        out[p.pid] = p
    out.update(AR=build_arch(), LT=build_lotus(), OR=build_outer_ring(), OP=build_outer_petal())
    return out


CORES = {"fol": ["FA", "FB", "FC", "FD", "FE"], "sunflower": ["FD", "SF"], "merkaba": ["MK1", "MK2"],
         "seed": ["SE1", "SE2", "SE3"], "metatron": ["MT1", "MT2", "MT3", "MT4", "MT5", "MT6"]}
RINGS = {"bloom": ["R1", "DM", "PT"], "lace": ["R1", "AR", "LT", "OR", "OP"]}
KIT2_OUTER = ["RC", "FN", "GP", "GH", "ST", "HL", "K2"]


def build_border():
    """plain insert that only traces the boundary circle in the lane (for dot-only centres)."""
    return make_insert("B0", "Border ring", Polygon(), [], [], [], [("1", 0.0, "A"), ("1", 0.0, "B")],
                       two_faced=True, lane=True, note="trace the circle in the gap; face B closes the tab gaps")


CORES["sunflower"] = ["B0", "SF"]
