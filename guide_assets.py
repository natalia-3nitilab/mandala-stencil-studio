#!/usr/bin/env python3
"""Painting variants + step-by-step instruction frames (SVG + PNG) for Kit 01."""
import os
import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity

import design01 as d
from geom import P, rot, disk, polys_of, R_HUB
from render import geom_d, svg_doc, png_from_layers, PALETTE

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview", "guide")
os.makedirs(OUT, exist_ok=True)
H = d.HALF

PALETTES = {
    "turquoise": dict(bg="#0b0f14", line="#3fd6d0", gold="#f2c45a", white="#f4efe2"),
    "moonlight": dict(bg="#121a3d", line="#f1ece0", gold="#f2c45a", white="#8fe3ff"),
    "rose": dict(bg="#140c16", line="#ff7aa8", gold="#ffd27a", white="#c9b6ff"),
}


def simp(g):
    return g.simplify(0.03, preserve_topology=True)


def layers_svg_body(layers, pal, s, half):
    by = {}
    for c, g in layers:
        by.setdefault(c, []).append(g)
    out = []
    for c in ["line", "white", "gold"]:
        if c in by:
            g = simp(unary_union(by[c]))
            out.append(f'<path d="{geom_d(g, s, -half, half)}" fill="{pal[c]}" fill-rule="evenodd"/>')
    return "".join(out)


def overlay_body(g, s, half, fill="rgba(226,232,240,0.62)", stroke="#ffffff"):
    return f'<path d="{geom_d(simp(g), s, -half, half)}" fill="{fill}" stroke="{stroke}" stroke-width="0.8" fill-rule="evenodd"/>'


def text(x, y, s, half, t, size=13, fill="#ffffff", weight=700):
    X, Y = (x + half) * s, (half - y) * s
    return (f'<text x="{X:.1f}" y="{Y:.1f}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="middle" dominant-baseline="central">{t}</text>')


def frame(name, layers, overlays=(), labels=(), pal="turquoise", s=2.6, half=H):
    p = PALETTES[pal]
    W = 2 * half * s
    body = layers_svg_body(layers, p, s, half)
    for g in overlays:
        body += overlay_body(g, s, half)
    for (x, y, t, sz) in labels:
        body += text(x, y, s, half, t, sz)
    svg = svg_doc(W, W, body, p["bg"])
    with open(os.path.join(OUT, name + ".svg"), "w") as fh:
        fh.write(svg)
    return svg


def plate_body(part):
    return part.outline.difference(part.cuts) if part.cuts is not None and not part.cuts.is_empty else part.outline


def placed(part, deg):
    return rot(plate_body(part), deg)


def main():
    kit = d.build_kit()
    hub = plate_body(kit["H1"])
    ALL = ("F1", "C", "A1", "B1", "H1", "F2", "D1", "K1")

    # ---- painting variants
    variants = {
        "P1_turquoise": (ALL, "turquoise"),
        "P1_moonlight": (ALL, "moonlight"),
        "P1_lotus_rose": (("F1", "C", "A1", "H1", "F2", "D1"), "rose"),
    }
    for name, (inc, pal) in variants.items():
        L = d.painting_layers(kit, include=inc)
        frame(name, L, pal=pal, s=3.0)
        PALETTE.update(PALETTES[pal])
        PALETTE["bg"] = PALETTES[pal]["bg"]
        png_from_layers(os.path.join(HERE, "preview", name + ".png"), L, H, px=1800)
    PALETTE.update(PALETTES["turquoise"])

    # ---- step frames
    J = kit["J20"]
    jig = affinity.translate(J.outline, -J.half, -J.half)
    canvas_edge = box(-H, -H, H, H).exterior.buffer(0.6)
    f = []
    f.append(frame("s1_hub", [("line", canvas_edge)], [jig, hub],
                   [(-H * 0.55, -H * 0.55 - 12, "jig", 12), (0, 0, "hub", 14)]))
    L = d.painting_layers(kit, include=("F1",), positions={"F1": ["A"]})
    f.append(frame("s2_fol_A", L, [hub, rot(plate_body(kit["F1"]), 60)], [(0, -47, "next notch →", 11)]))
    L = d.painting_layers(kit, include=("F1",))
    f.append(frame("s3_circles", L, [hub], [(0, 0, "", 1)]))
    L = d.painting_layers(kit, include=("F1", "C", "A1"), positions={"A1": ["1", "3", "5"]})
    labs = [(P(96, 45 * k)[0], P(96, 45 * k)[1], str(k + 1), 12) for k in range(8)]
    f.append(frame("s4_plateA", L, [hub, placed(kit["A1"], 45 * 6)], labs))
    L = d.painting_layers(kit, include=("F1", "C", "A1", "B1"), positions={"B1": ["1", "3"]})
    f.append(frame("s5_plateB", L, [hub, placed(kit["B1"], 45 * 4)], labs))
    L = d.painting_layers(kit, include=("F1", "C", "A1", "B1", "H1"))
    f.append(frame("s6_dots_core", L, [rot(plate_body(kit["F2"]), 0), hub]))
    L = d.painting_layers(kit, include=("F1", "C", "A1", "B1", "H1", "F2", "D1"), positions={"D1": ["1", "3", "5", "7"]})
    f.append(frame("s7_plateD", L, [placed(kit["D1"], 45)], labs))
    L = d.painting_layers(kit, include=("F1", "C", "A1", "B1", "H1", "F2", "D1", "K1"), positions={"K1": ["BL", "TL"]})
    K = kit["K1"]
    kp = d.corner_to_canvas(plate_body(K), 180)
    f.append(frame("s8_corners", L, [kp]))
    L = d.painting_layers(kit, include=ALL)
    f.append(frame("s9_done", L))

    # ---- system diagram: hub + insert + plate A in place (top view), light on dark
    diag = [hub, rot(plate_body(kit["F1"]), 0), placed(kit["A1"], 0)]
    frame("system", [], diag, [], s=3.2, half=H)
    print("ok", len(f), "frames ->", OUT)


if __name__ == "__main__":
    main()
