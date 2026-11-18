"""Physical parts: hub, inserts, wedge plates, corner plates, centre jig, fit card.

Every part is described as a stack of 2D slabs (z0, z1, shape) in USE orientation
(canvas at z = 0).  Parts with `flip=True` are turned over for printing.
"""
import math
import numpy as np
import manifold3d as m3d
import trimesh
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

from geom import *  # noqa


# ---------------------------------------------------------------------------
class Part:
    def __init__(self, pid, name, role, feats=None, positions=None, order=None, flip=False):
        self.pid, self.name, self.role = pid, name, role
        self.feats = feats or []
        self.positions = positions or [("1", 0.0)]
        self.order = order or [p[0] for p in self.positions]
        self.flip = flip
        self.layers = []       # (z0, z1, shapely geom)
        self.outline = None    # footprint for previews
        self.cuts = None       # openings for previews
        self.engrave = None
        self.cut_override = None  # cut used when computing drawn lines
        self.warnings = []
        self.howto = ""

    # drawn paint for one placement (design frame rotated by deg)
    def drawn_at(self, deg):
        out = []
        cut_all = self.cut_override if self.cut_override is not None else None
        for f in self.feats:
            if f.kind == "hole" and cut_all is not None:
                g = f.drawn(cut_all)
            else:
                g = f.drawn()
            col = DOT_COLOR[f.size] if f.kind == "dot" else f.color
            out.append((col, rot(g, deg)))
        return out

    def solid(self):
        man = None
        for z0, z1, g in self.layers:
            for poly in polys_of(g):
                rings = [np.array(poly.exterior.coords[:-1])] + [np.array(i.coords[:-1]) for i in poly.interiors]
                cs = m3d.CrossSection(rings, fillrule=m3d.FillRule.EvenOdd)
                s = m3d.Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])
                man = s if man is None else man + s
        return man

    def export_stl(self, path):
        man = self.solid()
        if self.flip:  # turn over (rotate 180 about X) so it prints without supports
            man = man.rotate([180, 0, 0])
        bb = man.bounding_box()
        man = man.translate([-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]])
        mesh = man.to_mesh()
        v = np.array(mesh.vert_properties)[:, :3]
        f = np.array(mesh.tri_verts)
        tm = trimesh.Trimesh(vertices=v, faces=f, process=True)
        tm.export(path)
        ext = tm.bounds[1] - tm.bounds[0]
        return {
            "watertight": bool(tm.is_watertight),
            "volume_cm3": round(tm.volume / 1000, 2),
            "size_mm": [round(x, 1) for x in ext],
            "triangles": int(len(f)),
            "genus_ok": man.genus() >= 0,
        }


def check_body(part, body, min_web=0.9):
    ps = polys_of(body)
    big = [p for p in ps if p.area > 0.5]
    if len(big) > 1:
        areas = sorted([round(p.area, 1) for p in big], reverse=True)
        part.warnings.append(f"body splits into {len(big)} pieces: areas {areas[:6]}")
    er = body.buffer(-min_web / 2)
    eps = [p for p in polys_of(er) if p.area > 0.3]
    if len(eps) > len(big):
        part.warnings.append(f"thin web (< {min_web} mm) somewhere: eroded body has {len(eps)} pieces")


def std_layers(outline, cuts, engrave=None, top_extra=None, low_outline=None):
    """Bottom relief / body / top lead-in stack. top_extra = shape added above STEP (teeth/ears)."""
    low = outline if low_outline is None else low_outline
    hi = outline if top_extra is None else unary_union([outline, top_extra])
    if top_extra is not None:      # tiny inset so walls of the two bands never coincide (clean STL)
        low = low.buffer(-0.02, join_style="mitre")
    L = []
    L.append((0.0, RELIEF_H, low.difference(cuts.buffer(RELIEF, quad_segs=12))))
    L.append((RELIEF_H, STEP + 0.1, low.difference(cuts)))
    L.append((STEP + 0.1, T - CHAMF_H, hi.difference(cuts)))
    top = hi.difference(cuts.buffer(CHAMF, quad_segs=12))
    if engrave is not None:
        top = top.difference(engrave)
    L.append((T - CHAMF_H, T, top))
    return L


def vee(phi, r_apex, r_open, half_open):
    """V shape (polygon) pointing to r_apex at angle phi, opening at r_open with half width."""
    a = math.radians(phi)
    u = np.array([math.sin(a), math.cos(a)])
    v = np.array([math.cos(a), -math.sin(a)])
    return Polygon([u * r_apex, u * r_open + v * half_open, u * r_open - v * half_open])


def outer_notch(phi):      # cut into hub rim
    return vee(phi, R_HUB - NOTCH_D, R_HUB + 1.0, NOTCH_D + 1.0)


def outer_tooth(phi):      # on wedge / jig, fits outer_notch
    apex = R_HUB - NOTCH_D + 0.2
    base = R_HUB + 0.9
    return vee(phi, apex, base, (base - apex) - 0.18)


INNER_NOTCH_D = 1.2


def inner_notch(phi):      # cut into hub inner edge
    return vee(phi, R_CORE + INNER_NOTCH_D, R_CORE - 1.0, INNER_NOTCH_D + 1.0)


def inner_ear(phi):        # on inserts
    apex = R_CORE + INNER_NOTCH_D - 0.2
    base = R_INS - 0.7
    return vee(phi, apex, base, (base - apex) - 0.18)


def radial_text(s, r, phi, h):
    g = text_poly(s, h)
    g = affinity.rotate(g, -phi, origin=(0, 0))
    x, y = P(r, phi)
    return affinity.translate(g, x, y)


# ---------------------------------------------------------------------------
# HUB
# ---------------------------------------------------------------------------
HUB_ROW1, HUB_ROW2 = 44.4, 50.2


def build_hub():
    part = Part("H1", "Hub (anchor ring)", "hub")
    row1 = [Feat("dot", Point(P(HUB_ROW1, 3.75 + 7.5 * k)), color="gold", size="M", group="hubdots") for k in range(48)]
    row2 = [Feat("dot", Point(P(HUB_ROW2, 3.75 + 7.5 * k)), color="white", size="S", group="hubdots2") for k in range(48)]
    dots = row1 + row2
    part.feats = dots
    ring = annulus(R_CORE, R_HUB, q=256)
    dcut = unary_union([f.cut() for f in dots])
    notches = unary_union([outer_notch(7.5 * k) for k in range(N_NOTCH)])
    inotch = unary_union([inner_notch(60 * k) for k in range(6)])
    pockets = unary_union([sector(46.75, 48.35, ph - 6.5, ph + 6.5).buffer(0.3).buffer(-0.3) for ph in (22.5, 142.5, 262.5)])
    eng = [radial_text(str(k + 1), HUB_ROW2, 45 * k, 2.4) for k in range(8)]
    engr = unary_union(eng)
    hi = ring.difference(notches).difference(inotch)
    lowring = annulus(R_CORE + 0.02, R_HUB - 0.02, q=256)   # tiny inset -> clean STL topology
    part.layers = [
        (0.0, RELIEF_H, lowring.difference(dcut.buffer(RELIEF)).difference(pockets)),
        (RELIEF_H, STEP, lowring.difference(dcut)),
        (STEP, T - CHAMF_H, hi.difference(dcut)),
        (T - CHAMF_H, T, hi.difference(dcut.buffer(CHAMF)).difference(engr)),
    ]
    part.outline = ring.difference(notches).difference(inotch)
    part.cuts = dcut
    part.engrave = engr
    part.pockets = pockets
    check_body(part, ring.difference(dcut))
    free = hi.difference(dcut.buffer(CHAMF + 0.3))
    for g in parts(engr):
        if not free.contains(g):
            part.warnings.append("hub number collides with a dot hole")
            break
    part.howto = "Stick to the canvas centre with the Centre Jig. Everything else clicks onto it."
    return part


# ---------------------------------------------------------------------------
# INSERTS (sit inside the hub, key into the A/B/C notches)
# ---------------------------------------------------------------------------
def build_insert(pid, name, feats, positions, rim=0.9, label=None, clip_lines=True):
    part = Part(pid, name, "insert", feats, positions)
    disc = disk(R_INS, q=256)
    lcuts = unary_union([f.cut() for f in feats if f.kind != "dot"])
    if clip_lines and not lcuts.is_empty:
        lcuts = lcuts.intersection(disk(R_INS - rim, q=256))
    dcuts = unary_union([f.cut() for f in feats if f.kind == "dot"])
    cuts = unary_union([lcuts, dcuts])
    part.cut_override = lcuts
    body = disc.difference(cuts)
    check_body(part, body)
    ear = inner_ear(0.0)
    engr = None
    if label:
        lab = text_poly(label, 3.2)
        engr = place_label(body, cuts, lab, prefer=(0, R_INS - 6))
        if engr is None:
            part.warnings.append("no room for label")
    part.layers = std_layers(disc, cuts, engr, top_extra=ear)
    part.outline = unary_union([disc, ear])
    part.cuts = cuts
    part.engrave = engr
    return part


# ---------------------------------------------------------------------------
# WEDGE PLATES (click onto the hub's outer notches)
# ---------------------------------------------------------------------------
def wedge_outline(cuts, teeth, rmax, margin=4.0, clip=None):
    pcs = [cuts.buffer(margin, quad_segs=8)]
    for ph in teeth:
        pcs.append(sector(R_HUB, R_HUB + 14, ph - 7, ph + 7))
    hull = unary_union(pcs).convex_hull
    hull = hull.intersection(disk(rmax, q=256))
    if clip is not None:
        hull = hull.intersection(clip)
    return hull.difference(disk(R_HUB + CLR, q=256))


def build_wedge(pid, name, feats, teeth, rmax, positions, order, label=None, clip=None):
    part = Part(pid, name, "wedge", feats, positions, order)
    cuts = unary_union([f.cut() for f in feats])
    outline = wedge_outline(cuts, teeth, rmax, clip=clip)
    body = outline.difference(cuts)
    check_body(part, body)
    tee = unary_union([outer_tooth(ph) for ph in teeth])
    eng = []
    if label:
        lab = text_poly(label, 5.0)
        arrow = arrow_poly(5.0, 4.0)
        combo = unary_union([affinity.translate(lab, 0, 3.6), affinity.translate(arrow, 0, -3.4)])
        g = place_label(body, cuts, combo, prefer=(0, R_HUB + 10),
                        search=[(0, y) for y in np.arange(R_HUB + 6, rmax, 0.5)])
        if g is None:
            g = place_label(body, cuts, combo, prefer=(0, R_HUB + 10))
        if g is None:
            part.warnings.append("no room for label")
        else:
            eng.append(g)
    engr = unary_union(eng) if eng else None
    part.layers = std_layers(outline, cuts, engr, top_extra=tee)
    part.outline = unary_union([outline, tee])
    part.cuts = cuts
    part.engrave = engr
    return part


# ---------------------------------------------------------------------------
# CORNER PLATES (hook onto a canvas corner with two lips) — printed upside down
# ---------------------------------------------------------------------------
LIP_T, LIP_D, LIP_RELIEF = 2.4, 3.5, 9.0


def corner_lips(L):
    a = box(-LIP_T, LIP_RELIEF, 0, L)
    b = box(LIP_RELIEF, -LIP_T, L, 0)
    return unary_union([a, b])


def build_corner(pid, name, feats, half, L, positions, order, label=None):
    """feats are given in CORNER coordinates: canvas corner at (0,0), canvas in +x,+y."""
    part = Part(pid, name, "corner", feats, positions, order, flip=True)
    cuts = unary_union([f.cut() for f in feats]).intersection(box(0.0, 0.0, L + 5, L + 5))
    plate = unary_union([cuts.buffer(4.0), box(0, 0, 14, 14)]).convex_hull.intersection(box(0, 0, L, L))
    lips = corner_lips(L)
    outline = unary_union([plate, lips.intersection(box(-LIP_T, -LIP_T, plate.bounds[2], plate.bounds[3]))])
    body = outline.difference(cuts)
    check_body(part, body)
    engr = None
    if label:
        lab = text_poly(label, 4.0)
        engr = place_label(body, cuts, lab, prefer=(6, 6))
    lip_shape = lips.intersection(box(-LIP_T, -LIP_T, plate.bounds[2], plate.bounds[3]))
    part.layers = std_layers(outline, cuts, engr) + [(-LIP_D, 0.0, lip_shape)]
    part.outline = outline
    part.cuts = cuts
    part.engrave = engr
    part.half = half
    return part


# ---------------------------------------------------------------------------
# CENTRE JIG (per canvas size) — printed upside down
# ---------------------------------------------------------------------------
def build_jig(pid, name, half, label, wall=6.0, open_far=False):
    """half = distance canvas corner -> centre along each axis (mm)."""
    part = Part(pid, name, "jig", flip=True)
    cx = cy = half
    ring_in = R_HUB + 0.25
    ring = annulus(ring_in, ring_in + wall).buffer(0)
    if open_far:   # C-shaped cradle: 200 deg of ring facing the corner still traps the hub
        ring = ring.difference(sector(0, ring_in + wall + 5, 45 - 80, 45 + 80)).buffer(1.0).buffer(-1.0)
    ring = affinity.translate(ring, cx, cy)
    # diagonal beam from corner to ring
    d = np.array([1, 1]) / math.sqrt(2)
    n = np.array([-1, 1]) / math.sqrt(2)
    p0 = np.array([0, 0])
    p1 = np.array([cx, cy]) - d * (ring_in + 3)
    w = 9.0
    beam = Polygon([p0 + n * w, p1 + n * w, p1 - n * w, p0 - n * w])
    corner = box(0, 0, 34, 34).difference(Point(34, 34).buffer(22))
    L = 40
    lips = corner_lips(L)
    plate = unary_union([ring, beam, corner, box(0, 0, L, 6), box(0, 0, 6, L)])
    plate = plate.intersection(box(0, 0, 1e4, 1e4)).difference(affinity.translate(disk(ring_in), cx, cy))
    plate = unary_union([plate, lips])   # lips rise through the full plate thickness
    # tooth that drops into hub notch "6" (bottom-left = towards this corner)
    tooth = affinity.translate(outer_tooth(225.0), cx, cy)
    tooth = tooth.intersection(affinity.translate(disk(ring_in + 2), cx, cy))
    lab = text_poly(label, 4.0)
    lab = affinity.rotate(lab, 45, origin=(0, 0))
    engr = affinity.translate(lab, cx * 0.45, cy * 0.45)
    lab2 = affinity.rotate(text_poly("hub 6", 3.0), 45, origin=(0, 0))
    engr = unary_union([engr, affinity.translate(lab2, *(np.array([cx, cy]) - d * (ring_in + 9)))])
    TJ = 3.0
    part.layers = [
        (0.0, STEP + 0.1, plate.buffer(-0.02, join_style="mitre")),
        (STEP + 0.1, TJ - 0.5, unary_union([plate, tooth])),
        (TJ - 0.5, TJ, unary_union([plate, tooth]).difference(engr)),
        (-LIP_D, 0.0, lips),
    ]
    part.outline = unary_union([plate, lips, tooth])
    part.cuts = Polygon()
    part.engrave = engr
    part.half = half
    part.howto = "Hook the lips over a canvas corner, drop the hub in (number 6 on the tooth), press, lift the jig off."
    return part


# ---------------------------------------------------------------------------
# FIT CARD (Phase 0 calibration)
# ---------------------------------------------------------------------------
def build_fit_card():
    part = Part("T0", "Fit Card", "card")
    W, H = 118.0, 74.0
    plate = box(0, 0, W, H).buffer(3).buffer(-3)
    cuts, eng = [], []
    widths = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6]
    for i, w in enumerate(widths):
        x = 9 + i * 14.0
        cuts.append(LineString([(x, 44), (x, 66)]).buffer(w / 2, quad_segs=12))
        eng.append(affinity.translate(text_poly(f"{w:.1f}", 2.6), x, 39.5))
    holes = [1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.6, 4.0]
    for i, dd in enumerate(holes):
        x = 7 + i * 10.4
        cuts.append(Point(x, 29).buffer(dd / 2, quad_segs=16))
        eng.append(affinity.translate(text_poly(f"{dd:.1f}", 2.2), x, 23.5))
    # tracing test: a circle and a petal to trace inside (offset for a 1.8 slot marker)
    cuts.append(Point(16, 10).buffer(6.0 + 0.9, quad_segs=32))
    cuts.append(vesica((34, 5), (60, 15), 9.0).buffer(0.9, join_style="mitre", mitre_limit=3))
    # an arc channel with a bridge, to try the bridge + dot trick
    a = arc((96, -14), 26, -38, 38)
    ch = a.buffer(0.9, quad_segs=12).difference(bridge_poly(a, a.interpolate(0.5, normalized=True).coords[0]))
    cuts.append(ch)
    eng.append(affinity.translate(text_poly("FIT", 4.0), 70, 8))
    cuts = unary_union(cuts)
    engr = unary_union(eng)
    part.layers = std_layers(plate, cuts, engr)
    part.outline = plate
    part.cuts = cuts
    part.engrave = engr
    check_body(part, plate.difference(cuts))
    return part
