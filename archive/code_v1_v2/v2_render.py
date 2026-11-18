"""v2 prototype previews: painting, anchored A/B frames, lock detail and cross-section."""
import os
from shapely.geometry import box, Point
from shapely.ops import unary_union
from shapely import affinity

import design01 as d1
import v2
from geom import rot, disk, C0, C1, LINE_W, R_HUB, polys_of
from guide_assets import frame, layers_svg_body, overlay_body, PALETTES, OUT
from render import geom_d, svg_doc, png_from_layers, PALETTE

H = 100.0
NUM = [45.0 * k for k in range(8)]
TEETH = "#f2c45a"


def ring(r):
    return disk(r + LINE_W / 2, q=256).difference(disk(r - LINE_W / 2, q=256))


def core_layers(kind="fol"):
    if kind == "fol":
        F1, F2 = d1.core_parts()
        L = []
        for _, deg in F1.positions:
            L += F1.drawn_at(deg)
        L += F2.drawn_at(0)
    else:
        sf = v2.build_sunflower()
        L = sf.drawn_at(0)
    return L


def build():
    hub = v2.build_hub_v2()
    dm, pt = v2.build_dome(), v2.build_petal()
    return hub, dm, pt


def painting(hub, dm, pt, core="fol", upto=None):
    L = core_layers(core) + [("line", ring(C0)), ("line", ring(C1))]
    for f in hub.feats:
        L.append(("gold" if f.size == "M" else "white", f.drawn()))
    for pc in (dm, pt):
        for deg in NUM:
            for face in ("A", "B"):
                if upto and not upto(pc.pid, deg, face):
                    continue
                L += pc.painted(deg, face)
    return L


def overlays(hub, pc, deg, face):
    tint = "rgba(226,232,240,0.70)" if face == "A" else "rgba(170,205,240,0.72)"
    hub_g = hub.outline.difference(hub.cuts)
    teeth = pc.teeth_geom()
    teeth = rot(v2.mirror(teeth) if face == "B" else teeth, deg)
    return [(hub_g, "rgba(226,232,240,0.62)", "#ffffff"),
            (pc.placed_outline(deg, face), tint, "#ffffff"),
            (teeth, TEETH, "#000000")]


def svg_frame(name, L, ovs, labels=(), s=2.6, half=H):
    p = PALETTES["turquoise"]
    body = layers_svg_body(L, p, s, half)
    for g, fill, stroke in ovs:
        body += f'<path d="{geom_d(g.simplify(0.03), s, -half, half)}" fill="{fill}" stroke="{stroke}" stroke-width="0.8" fill-rule="evenodd"/>'
    for x, y, t, sz in labels:
        X, Y = (x + half) * s, (half - y) * s
        body += (f'<text x="{X:.1f}" y="{Y:.1f}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="{sz}" '
                 f'font-weight="700" fill="#ffffff" text-anchor="middle" dominant-baseline="central">{t}</text>')
    svg = svg_doc(2 * half * s, 2 * half * s, body, p["bg"])
    open(os.path.join(OUT, name + ".svg"), "w").write(svg)


def lock_detail(hub, dm):
    """Zoomed top view at hub number 1: dome piece face A clicked in, teeth in gold."""
    s, x0, x1, y0, y1 = 9.0, -26.0, 26.0, 40.0, 80.0
    W, Hh = (x1 - x0) * s, (y1 - y0) * s
    def d(g):
        return geom_d(g, s, x0, y1)
    win = box(x0, y0, x1, y1)
    hub_g = hub.outline.difference(hub.cuts).intersection(win)
    notch = hub.outline.intersection(hub.notches).intersection(win)
    pc = dm.outline.difference(dm.cuts_).intersection(win)
    teeth = dm.teeth_geom().intersection(win)
    body = (f'<path d="{d(hub_g)}" fill="#cfd5dc" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'
            f'<path d="{d(notch)}" fill="none" stroke="#5b6573" stroke-width="1" stroke-dasharray="4 3"/>'
            f'<path d="{d(pc)}" fill="#e7ebef" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'
            f'<path d="{d(teeth)}" fill="{TEETH}" stroke="#7a5a00" stroke-width="1"/>')
    def label(x, y, t, anchor="middle"):
        X, Y = (x - x0) * s, (y1 - y) * s
        return (f'<text x="{X:.0f}" y="{Y:.0f}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="15" '
                f'font-weight="600" fill="#1d2329" text-anchor="{anchor}">{t}</text>')
    body += label(0, 44.5, "hub") + label(-13.8, 49.0, "tooth", "middle") + label(13.8, 49.0, "tooth", "middle")
    body += label(0, 73.5, "dome piece, face A")
    return svg_doc(W, Hh, body, "#f4f6f8")


def cross_section():
    """Side view: why the lock works on both faces."""
    s = 34.0
    W, Hh = 760, 300
    def rect(x, z, w, h, fill, stroke="#5b6573"):
        return f'<rect x="{x:.1f}" y="{z:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
    def y(zmm, base):
        return base - zmm * s
    out = []
    for i, (title, base_x) in enumerate((("face A up", 30), ("flipped: face B up", 400))):
        base = 230
        # hub rim: bottom band 0-0.6, top band 1.4-2.0, notch (void) 0.6-1.4 cut back 1.5 mm
        hx = base_x
        out.append(rect(hx, y(2.0, base), 120, 2.0 * s, "#cfd5dc"))
        out.append(rect(hx + 120 - 1.5 * s, y(1.4, base), 1.5 * s, 0.8 * s, "#f4f6f8", "#5b6573"))
        # piece: 2 mm plate starting at the hub edge, tooth 0.6-1.4 reaching into the notch
        px = hx + 120 + 2
        out.append(rect(px, y(2.0, base), 190, 2.0 * s, "#e7ebef" if i == 0 else "#cfe0f2"))
        out.append(rect(px - 1.4 * s, y(1.4, base), 1.4 * s, 0.8 * s, TEETH, "#7a5a00"))
        # canvas
        out.append(f'<line x1="{base_x - 10}" y1="{base}" x2="{base_x + 330}" y2="{base}" stroke="#1d2329" stroke-width="3"/>')
        txt = lambda x, yy, t, size=15, w=600: f'<text x="{x}" y="{yy}" font-family="ui-sans-serif,system-ui,sans-serif" font-size="{size}" font-weight="{w}" fill="#1d2329">{t}</text>'
        out.append(txt(base_x, 40, title, 17, 700))
        out.append(txt(hx + 6, y(2.0, base) - 10, "hub", 14))
        out.append(txt(px + 60, y(2.0, base) - 10, "piece", 14))
        out.append(txt(base_x, base + 28, "canvas", 13, 500))
        out.append(txt(px - 1.4 * s - 6, y(0.6, base) + 34, "tooth in the middle band", 13, 500))
        out.append(txt(px + 100, y(1.0, base) + 5, "A" if i == 0 else "B", 22, 800))
    return svg_doc(W, Hh, "".join(out), "#f4f6f8")


def main():
    hub, dm, pt = build()
    P = PALETTE
    for core, name in (("fol", "v2_painting_fol"), ("sf", "v2_painting_sunflower")):
        L = painting(hub, dm, pt, core)
        frame(name, L, s=3.0)
        png_from_layers(os.path.join(os.path.dirname(OUT), name + ".png"), L, H, px=1800)

    # step frames, every one shows the hub and the gold teeth
    order = []
    done = set()
    def upto_fn(allowed):
        return lambda pid, deg, face: (pid, deg, face) in allowed
    seq = [("DM", 0.0, "A"), ("DM", 0.0, "B")]
    allowed = set()
    L0 = core_layers("fol") + [("line", ring(C0)), ("line", ring(C1))]
    def L_with(allowed):
        L = list(L0)
        for pc in (dm, pt):
            for deg in NUM:
                for face in ("A", "B"):
                    if (pc.pid, deg, face) in allowed:
                        L += pc.painted(deg, face)
        return L
    svg_frame("v2_s1_domeA", L_with({("DM", 0.0, "A")}), overlays(hub, dm, 0.0, "A"))
    svg_frame("v2_s2_domeB", L_with({("DM", 0.0, "A"), ("DM", 0.0, "B")}), overlays(hub, dm, 0.0, "B"))
    all_dm = {("DM", d, f) for d in NUM for f in "AB"}
    svg_frame("v2_s3_domes", L_with(all_dm), [(hub.outline.difference(hub.cuts), "rgba(226,232,240,0.62)", "#ffffff")])
    svg_frame("v2_s4_petalA", L_with(all_dm | {("PT", 0.0, "A")}), overlays(hub, pt, 0.0, "A"))
    svg_frame("v2_s5_petalB", L_with(all_dm | {("PT", 0.0, "A"), ("PT", 45.0, "B")}), overlays(hub, pt, 45.0, "B"))
    svg_frame("v2_s6_done", painting(hub, dm, pt, "fol"), [])
    open(os.path.join(OUT, "v2_lock_detail.svg"), "w").write(lock_detail(hub, dm))
    open(os.path.join(OUT, "v2_cross_section.svg"), "w").write(cross_section())
    # piece sheets: face A and face B side by side
    for pc in (dm, pt):
        g = pc.outline.difference(pc.cuts_)
        a = g
        b = affinity.translate(v2.mirror(g), 0, 0)
        minx, miny, maxx, maxy = unary_union([a, b]).bounds
        sh = 70
        a2 = affinity.translate(a, -minx + 4, 0)
        b2 = affinity.translate(b, -minx + 4 + (maxx - minx) + 14, 0)
        ta = affinity.translate(pc.teeth_geom(), -minx + 4, 0)
        tb = affinity.translate(v2.mirror(pc.teeth_geom()), -minx + 4 + (maxx - minx) + 14, 0)
        ea = affinity.translate(pc.engrave, -minx + 4, 0)
        eb = affinity.translate(v2.mirror(pc.engrave_b), -minx + 4 + (maxx - minx) + 14, 0)
        allg = unary_union([a2, b2])
        bx0, by0, bx1, by1 = allg.bounds
        s = 4.0
        W, Hh = (bx1 + 4) * s, (by1 - by0 + 8) * s
        def d(gg):
            return geom_d(gg, s, 0, by1 + 4)
        body = (f'<path d="{d(a2)}" fill="#e7ebef" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'
                f'<path d="{d(b2)}" fill="#cfe0f2" stroke="#5b6573" stroke-width="1" fill-rule="evenodd"/>'
                f'<path d="{d(unary_union([ta, tb]))}" fill="{TEETH}" stroke="#7a5a00" stroke-width="1"/>'
                f'<path d="{d(unary_union([ea, eb]))}" fill="#5b6573"/>')
        open(os.path.join(OUT, f"v2_piece_{pc.pid}.svg"), "w").write(svg_doc(W, Hh, body))
    print("v2 frames ok")


if __name__ == "__main__":
    main()
