#!/usr/bin/env python3
"""v3 previews: paintings, recipe gallery, mixer layers, anchored step frames, part drawings."""
import os
from shapely.geometry import Point, box
from shapely.ops import unary_union
from shapely import affinity

import make_v3 as MK
import v3_more as M
from v3 import mirror, R_HUB, R_CORE
from geom import rot, polys_of, DOT_DRAWN
from render import geom_d, svg_doc, png_from_layers, PALETTE

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "book", "img3")
PNG = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PNG, exist_ok=True)

PAL = {"turquoise": dict(bg="#0b0f14", line="#3fd6d0", gold="#f2c45a", white="#f4efe2"),
       "moonlight": dict(bg="#121a3d", line="#f1ece0", gold="#f2c45a", white="#8fe3ff"),
       "rose": dict(bg="#140c16", line="#ff7aa8", gold="#ffd27a", white="#c9b6ff")}
TEETH, PIECE_A, PIECE_B = "#f2c45a", "rgba(226,232,240,0.74)", "rgba(170,205,240,0.76)"


def simp(g):
    return g.simplify(0.03, preserve_topology=True)


def layers_of(P, pids, which=None):
    L = []
    for pid in pids:
        p = P[pid]
        if getattr(p, "kind", "") == "hub":
            for q, s in p.dots:
                L.append(("gold" if s == "M" else "white", Point(q).buffer(DOT_DRAWN[s] / 2, quad_segs=12)))
            continue
        w = which.get(pid) if which else None
        if which is not None and pid in which and w == "none":
            continue
        L += p.all_painted(w)
    return L


def body_paths(L, pal, s, half, classed=False):
    by = {}
    for c, g in L:
        by.setdefault(c, []).append(g)
    out = []
    for c in ("line", "white", "gold"):
        if c in by:
            d = geom_d(simp(unary_union(by[c])), s, -half, half)
            if classed:
                cls = {"line": "ln", "white": "dw", "gold": "dg"}[c]
                out.append(f'<path class="{cls}" d="{d}" fill-rule="evenodd"/>')
            else:
                out.append(f'<path d="{d}" fill="{pal[c]}" fill-rule="evenodd"/>')
    return "".join(out)


def save(name, svg):
    with open(os.path.join(OUT, name + ".svg"), "w") as fh:
        fh.write(svg)


def painting(name, P, pids, half, pal="turquoise", s=2.6, png=True):
    L = layers_of(P, pids)
    p = PAL[pal]
    save(name, svg_doc(2 * half * s, 2 * half * s, body_paths(L, p, s, half), p["bg"]))
    if png:
        PALETTE.update(p)
        png_from_layers(os.path.join(PNG, name + ".png"), L, half, px=2000 if half > 120 else 1800)
        PALETTE.update(PAL["turquoise"])


def frame(name, P, pids, half, overlays=(), which=None, labels=(), s=2.4):
    L = layers_of(P, pids, which)
    p = PAL["turquoise"]
    body = body_paths(L, p, s, half)
    for g, fill, stroke in overlays:
        body += f'<path d="{geom_d(simp(g), s, -half, half)}" fill="{fill}" stroke="{stroke}" stroke-width="0.8" fill-rule="evenodd"/>'
    for x, y, t, sz in labels:
        X, Y = (x + half) * s, (half - y) * s
        body += (f'<text x="{X:.1f}" y="{Y:.1f}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="{sz}" '
                 f'font-weight="700" fill="#ffffff" text-anchor="middle" dominant-baseline="central">{t}</text>')
    save(name, svg_doc(2 * half * s, 2 * half * s, body, p["bg"]))


def hub_ov(P):
    h = P["H3"]
    return (h.outline.difference(h.cuts), "rgba(226,232,240,0.55)", "#ffffff")


def piece_ov(P, pid, deg, face):
    p = P[pid]
    if getattr(p, "kind", "") == "corner" or p.role == "corner":
        return [(p.placed_outline(deg), PIECE_A, "#ffffff")]
    return [(p.placed_outline(deg, face), PIECE_A if face == "A" else PIECE_B, "#ffffff"),
            (p.placed_teeth(deg, face), TEETH, "#000000")]


def part_sheet(p):
    """Face A drawing (and face B mirrored beside it when the part is two-faced)."""
    g = p.outline.difference(p.cuts) if p.cuts is not None and not p.cuts.is_empty else p.outline
    gr = getattr(p, "grooves", None)
    tg = p.teeth_geom() if hasattr(p, "teeth_geom") else None
    items = [(g, "#e7ebef", "#5b6573")]
    if gr is not None and not gr.is_empty:
        items.append((gr.intersection(g.buffer(0.01)), "#aeb8c4", "none"))
    if tg is not None and not tg.is_empty:
        items.append((tg, TEETH, "#7a5a00"))
    if p.engrave is not None and not p.engrave.is_empty:
        items.append((p.engrave, "#5b6573", "none"))
    shapes = [items]
    if getattr(p, "two_faced", False):
        b = [(mirror(x), ("#cfe0f2" if c == "#e7ebef" else c), sc) for x, c, sc in items if c != "#5b6573"]
        if getattr(p, "engrave_b", None) is not None and not p.engrave_b.is_empty:
            b.append((mirror(p.engrave_b), "#5b6573", "none"))
        shapes.append(b)
    allg = unary_union([x for grp in shapes for x, _, _ in grp])
    minx, miny, maxx, maxy = allg.bounds
    w = maxx - minx
    gap = 10
    s = 4.0
    W = (w * len(shapes) + gap * (len(shapes) - 1) + 8) * s
    H = (maxy - miny + 8) * s
    body = ""
    for i, grp in enumerate(shapes):
        dx = -minx + 4 + i * (w + gap)
        for x, c, sc in grp:
            x2 = affinity.translate(x, dx, 0)
            body += f'<path d="{geom_d(x2, s, 0, maxy + 4)}" fill="{c}" stroke="{sc}" stroke-width="1" fill-rule="evenodd"/>'
    return svg_doc(W, H, body)


def main():
    P = MK.build_all()
    K1PIDS = M.CORES["fol"] + ["H3"] + M.RINGS["bloom"] + ["K1"]
    K2PIDS = M.CORES["fol"] + ["H3"] + M.RINGS["bloom"] + M.KIT2_OUTER
    painting("k1_turquoise", P, K1PIDS, 100.0)
    painting("k1_moonlight", P, K1PIDS, 100.0, "moonlight")
    painting("k2_turquoise", P, K2PIDS, 150.0, s=2.0)
    painting("k2_rose", P, K2PIDS, 150.0, "rose", s=2.0)
    for c in M.CORES:
        for r in M.RINGS:
            painting(f"r_{c}_{r}", P, M.CORES[c] + ["H3"] + M.RINGS[r] + ["K1"], 100.0, s=1.6, png=False)

    # ---- mixer layers (colours from CSS classes)
    def layer(name, pids, half=100.0, s=1.8):
        L = layers_of(P, pids)
        save("mx_" + name, svg_doc(2 * half * s, 2 * half * s, body_paths(L, None, s, half, classed=True)))
    for c in M.CORES:
        layer("core_" + c, M.CORES[c])
    for r in M.RINGS:
        layer("ring_" + r, M.RINGS[r])
    layer("hub", ["H3"])
    layer("corner", ["K1"])

    # ---- Kit 01 step frames (hub + piece + gold teeth in every frame that uses the hub)
    H = 100.0
    J = P["J20"]
    jig = affinity.translate(J.outline, -J.half, -J.half)
    edge = box(-H, -H, H, H).exterior.buffer(0.6)
    frame("k1_s01_hub", P, [], H, [(edge, "#2a3a44", "none"), (jig, PIECE_A, "#ffffff"), hub_ov(P)])
    centre = ["FA", "FB", "FC", "FD"]
    frame("k1_s02_fa", P, ["FA"], H, [hub_ov(P)] + piece_ov(P, "FA", 0.0, "B"), which={"FA": {("1", "A")}})
    frame("k1_s03_fb", P, ["FA", "FB"], H, [hub_ov(P)] + piece_ov(P, "FB", 60.0, "A"),
          which={"FB": {("1", "A"), ("1", "B")}})
    frame("k1_s04_fd", P, ["FA", "FB", "FC", "FD"], H, [hub_ov(P)] + piece_ov(P, "FD", 0.0, "A"), which={"FD": {("1", "A")}})
    labs = [(*__import__("geom").P(95, 45 * k), str(k + 1), 12) for k in range(8)]
    frame("k1_s05_ring", P, centre + ["R1"], H, [hub_ov(P)] + piece_ov(P, "R1", 90.0, "A"),
          which={"R1": {("1", "A"), ("1", "B"), ("2", "A"), ("2", "B")}}, labels=labs)
    frame("k1_s06_domeA", P, centre + ["R1", "DM"], H, [hub_ov(P)] + piece_ov(P, "DM", 0.0, "A"),
          which={"DM": {("1", "A")}}, labels=labs)
    frame("k1_s07_domeB", P, centre + ["R1", "DM"], H, [hub_ov(P)] + piece_ov(P, "DM", 0.0, "B"),
          which={"DM": {("1", "A"), ("1", "B")}}, labels=labs)
    frame("k1_s08_petal", P, centre + ["R1", "DM", "PT"], H, [hub_ov(P)] + piece_ov(P, "PT", 0.0, "B"),
          which={"PT": {("1", "A"), ("1", "B"), ("8", "A"), ("8", "B")}}, labels=labs)
    frame("k1_s09_dots", P, centre + ["R1", "DM", "PT", "H3"], H, [hub_ov(P)] + piece_ov(P, "FE", 0.0, "A"))
    frame("k1_s10_corner", P, centre + ["R1", "DM", "PT", "H3", "FE", "K1"], H, piece_ov(P, "K1", 180.0, "A"),
          which={"K1": {("BL", "A"), ("TL", "A")}})
    frame("k1_s11_done", P, K1PIDS, H)

    # ---- Kit 02 frames
    H2 = 150.0
    base = M.CORES["fol"] + ["H3"] + M.RINGS["bloom"] + ["FE"]
    labs2 = [(*__import__("geom").P(142, 45 * k), str(k + 1), 13) for k in range(8)]
    for name, extra, pid, deg, face, which in [
        ("k2_s01_ring", [], "RC", 45.0, "A", {"RC": {("1", "A"), ("1", "B")}}),
        ("k2_s02_fan", ["RC"], "FN", 90.0, "B", {"FN": {("1", "A"), ("1", "B"), ("2", "A"), ("2", "B")}}),
        ("k2_s03_petal", ["RC", "FN"], "GP", 90.0, "A", {"GP": {("1", "A"), ("1", "B")}}),
        ("k2_s04_heart", ["RC", "FN", "GP"], "GH", 0.0, "B", {"GH": {("1", "A")}}),
        ("k2_s05_star", ["RC", "FN", "GP", "GH"], "ST", 45.0, "A", {"ST": "none"}),
        ("k2_s06_halo", ["RC", "FN", "GP", "GH", "ST"], "HL", 135.0, "B", {"HL": {("2", "A"), ("2", "B"), ("4", "A")}}),
    ]:
        frame(name, P, base + extra + [pid], H2, [hub_ov(P)] + piece_ov(P, pid, deg, face), which=which, labels=labs2, s=1.8)
    frame("k2_s07_corner", P, base + ["RC", "FN", "GP", "GH", "ST", "HL", "K2"], H2, piece_ov(P, "K2", 180.0, "A"),
          which={"K2": {("BL", "A"), ("TL", "A")}}, s=1.8)

    # ---- part drawings
    for pid, _ in MK.FILES:
        if pid in ("T0",):
            continue
        p = P[pid]
        if getattr(p, "role", "") == "jig" or pid.startswith("J"):
            g = p.outline
            minx, miny, maxx, maxy = g.bounds
            s = 2.0
            save("part_" + pid, svg_doc((maxx - minx + 8) * s, (maxy - miny + 8) * s,
                 f'<path d="{geom_d(g, s, minx - 4, maxy + 4)}" fill="#e7ebef" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'))
            continue
        save("part_" + pid, part_sheet(p))
    print("v3 previews ok ->", OUT)


if __name__ == "__main__":
    main()


def diagrams():
    """v3 lock (top view) and side views of the tooth and of a groove with pockets."""
    import make_v3 as MK
    P = MK.build_all()
    hub, r1, dm = P["H3"], P["R1"], P["DM"]
    s, x0, x1, y0, y1 = 9.0, -24.0, 24.0, 46.0, 78.0
    win = box(x0, y0, x1, y1)
    d = lambda g: geom_d(g.intersection(win), s, x0, y1)
    body = (f'<path d="{d(hub.outline.difference(hub.cuts))}" fill="#cfd5dc" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'
            f'<path d="{d(dm.outline.difference(dm.cuts_))}" fill="#e7ebef" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'
            f'<path d="{d(dm.teeth_geom())}" fill="{TEETH}" stroke="#7a5a00" stroke-width="1"/>')
    def t(x, y, txt, size=15, anchor="middle"):
        return (f'<text x="{(x - x0) * s:.0f}" y="{(y1 - y) * s:.0f}" font-family="ui-sans-serif,system-ui,sans-serif" '
                f'font-size="{size}" font-weight="600" fill="#1d2329" text-anchor="{anchor}">{txt}</text>')
    body += t(0, 48.5, "hub: V-notches every 7.5°") + t(-14.5, 51.2, "V-tooth") + t(14.5, 51.2, "V-tooth") + t(0, 73.5, "dome piece")
    save("v3_lock", svg_doc((x1 - x0) * s, (y1 - y0) * s, body, "#f4f6f8"))
    # side views
    W, Hh = 820, 300
    sc = 40.0
    def rect(x, y, w, h, fill, stroke="#5b6573"):
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
    def txt(x, y, s_, size=14, w=600):
        return f'<text x="{x}" y="{y}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="{size}" font-weight="{w}" fill="#1d2329">{s_}</text>'
    base = 200
    out = [txt(20, 34, "Lock: full-height V-tooth, works on both faces", 16, 700)]
    out.append(rect(30, base - 2 * sc, 150, 2 * sc, "#cfd5dc"))
    out.append(rect(180, base - 2 * sc, 2, 2 * sc, "#ffffff", "#ffffff"))
    out.append(rect(182, base - 2 * sc, 160, 2 * sc, "#e7ebef"))
    out.append(f'<polygon points="{180 - 1.8 * sc},{base - 2 * sc} {182},{base - 2 * sc} {182},{base} {180 - 1.8 * sc},{base}" fill="{TEETH}" stroke="#7a5a00" stroke-width="1.3"/>')
    out.append(f'<line x1="20" y1="{base}" x2="360" y2="{base}" stroke="#1d2329" stroke-width="3"/>')
    out += [txt(40, base - 2 * sc - 10, "hub"), txt(240, base - 2 * sc - 10, "piece"), txt(70, base + 26, "tooth = whole 2 mm height"), txt(20, base + 48, "canvas", 13, 500)]
    gx = 440
    out.append(txt(gx, 34, "Dots: a line with pockets", 16, 700))
    out.append(rect(gx, base - 2 * sc, 340, 2 * sc, "#e7ebef"))
    for i, x in enumerate((gx + 40, gx + 150, gx + 260)):
        out.append(rect(x, base - 2 * sc, 2.2 * sc / 2, 2 * sc, "#ffffff"))
    out.append(rect(gx, base - 2 * sc, 340, 0.6 * sc, "#aeb8c4", "none"))
    out.append(rect(gx, base - 0.6 * sc, 340, 0.6 * sc, "#aeb8c4", "none"))
    out.append(f'<line x1="{gx - 10}" y1="{base}" x2="{gx + 350}" y2="{base}" stroke="#1d2329" stroke-width="3"/>')
    out += [txt(gx, base - 2 * sc - 10, "groove 0.6 mm deep on each face"), txt(gx, base + 26, "pocket = hole: the tip reaches the canvas only here"), txt(gx, base + 48, "glide along the groove, press at each pocket", 13, 500)]
    save("v3_section", svg_doc(W, Hh, "".join(out), "#f4f6f8"))


if __name__ == "__main__":
    diagrams()
