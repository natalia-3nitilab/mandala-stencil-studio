"""v3 checks: fit (both faces), straight-down insertion path, angular lock, seating,
minimum walls, paint overlaps, and closed STL solids."""
import math
from collections import Counter
from shapely.strtree import STRtree
from shapely.geometry import Point

from v3 import T, MIN_WALL, thin_spots
from geom import polys_of


def vol(m):
    return 0.0 if m.is_empty() else m.volume()


def fit_checks(hub, pieces, jigs=()):
    H = hub.solid()
    res = []
    for p in pieces:
        if not hasattr(p, "solid_face") or p.kind not in ("wedge", "insert"):
            continue
        faces = ("A", "B") if p.two_faced else ("A",)
        lab, deg, _ = p.placements[0]
        for f in faces:
            base = p.solid_face(f)
            m = base.rotate([0, 0, -deg]) if deg else base
            ov = vol(H ^ m)
            path = max(vol(H ^ m.translate([0, 0, dz])) for dz in (0.3, 0.7, 1.1, 1.5, 1.9, 2.3))
            lock = min(vol(H ^ m.rotate([0, 0, s])) for s in (-1.0, 1.0))
            if p.kind == "wedge":
                pushed = base.translate([0, -0.35, 0])
                seat = vol(H ^ (pushed.rotate([0, 0, -deg]) if deg else pushed))
            else:
                seat = min(vol(H ^ (base.translate([dx, 0, 0]).rotate([0, 0, -deg]) if deg else base.translate([dx, 0, 0])))
                           for dx in (-0.35, 0.35))
            ok = ov < 1e-4 and path < 1e-4 and lock > 1e-3 and seat > 1e-4
            res.append((f"{p.pid} face {f}", ok,
                        f"seated overlap {ov:.4f} | in/out path {path:.4f} | turn 1deg {lock:.3f} | push {seat:.3f}"))
    for J in jigs:
        j = J.solid().translate([-J.half, -J.half, 0])
        ov = vol(H ^ j)
        path = max(vol(H ^ j.translate([0, 0, dz])) for dz in (0.5, 1.0, 1.5, 2.5, 3.5))
        key = vol(H ^ j.rotate([0, 0, -3.75]))
        res.append((f"{J.pid} on hub", ov < 1e-4 and path < 1e-4 and key > 1e-3,
                    f"overlap {ov:.4f} | path {path:.4f} | keyed {key:.3f}"))
    return res


def wall_checks(pieces):
    res = []
    for p in pieces:
        bad = [w for w in p.warnings if "thin" in w]
        res.append((f"{p.pid} walls >= {MIN_WALL} mm", not bad, "; ".join(bad) or "ok"))
    return res


def overlap_check(name, painted_items, allowed=()):
    """painted_items: list of (pid, kind, geom) with kind 'dot' or 'line'."""
    tree = STRtree([g for _, _, g in painted_items])
    bad = Counter()
    for i, (pid, kind, g) in enumerate(painted_items):
        if kind != "dot":
            continue
        for j in tree.query(g):
            if j == i:
                continue
            pj, kj, h = painted_items[j]
            if (pid, pj) in allowed or (pj, pid) in allowed:
                continue
            if g.intersection(h).area > 0.05:
                bad[(pid, pj, kj)] += 1
    n = sum(bad.values())
    return (f"{name}: dots clear of other paint", n == 0, f"{n} overlaps {dict(bad) if n else ''}")


def painted_items(parts_, pids):
    items = []
    for pid in pids:
        p = parts_[pid]
        if getattr(p, "kind", "") == "hub":
            from geom import DOT_DRAWN
            for q, s in p.dots:
                items.append((pid, "dot", Point(q).buffer(DOT_DRAWN[s] / 2)))
            continue
        for lab, deg, face in p.placements:
            for c, g in p.painted(deg, face):
                items.append((pid, "dot" if c in ("gold", "white") else "line", g))
    return items


def line_coverage(p, min_gap=0.4):
    """Every intended line of a piece, over all its placements, must end up painted."""
    from shapely.ops import unary_union
    from v3 import mirror
    from geom import rot, lines_of
    true, paint = [], []
    for lab, deg, face in p.placements:
        for g, kind in p.lines:
            gg = mirror(g) if face == "B" else g
            if hasattr(p, "half"):
                from shapely import affinity
                gg = affinity.translate(g, -p.half, -p.half)
            true.append(rot(gg, deg))
        paint += [g for c, g in p.painted(deg, face) if c == "line"]
    if not true:
        return (f"{p.pid} lines complete", True, "no lines")
    T = unary_union(true)
    miss = T.difference(unary_union(paint).buffer(0.05))
    gaps = [l for l in lines_of(miss) if l.length > min_gap]
    worst = max((l.length for l in gaps), default=0.0)
    return (f"{p.pid} lines complete", not gaps, f"{len(gaps)} gaps, longest {worst:.2f} mm" if gaps else "every line closed")
