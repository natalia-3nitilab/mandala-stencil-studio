"""Previews: simulated paintings, plate drawings, step-by-step frames (SVG + PNG)."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity
from geom import polys_of, rot

PALETTE = {
    "bg": "#0b0f14",
    "line": "#3fd6d0",      # turquoise
    "line2": "#7fe9ff",     # light aqua
    "gold": "#f2c45a",
    "white": "#f4efe2",
    "aqua_dot": "#3fd6d0",
    "plate": "#d9dde3",
}


def _ring_d(coords, s, ox, oy):
    pts = list(coords)
    out = "M" + " L".join(f"{(x - ox) * s:.2f},{(oy - y) * s:.2f}" for x, y in pts[:-1]) + " Z"
    return out


def geom_d(g, s=1.0, ox=0.0, oy=0.0):
    ds = []
    for p in polys_of(g):
        ds.append(_ring_d(p.exterior.coords, s, ox, oy))
        for i in p.interiors:
            ds.append(_ring_d(i.coords, s, ox, oy))
    return " ".join(ds)


def svg_doc(w, h, body, bg=None):
    bgr = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}">{bgr}{body}</svg>'


def painting_svg(layers, half, scale=3.0, corner_r=None, title=None):
    """layers: list of (color_key, geom) in canvas coords (centre 0,0). half = canvas half-size mm."""
    s = scale
    W = 2 * half * s
    body = []
    by_color = {}
    for c, g in layers:
        by_color.setdefault(c, []).append(g)
    order = ["line", "line2", "aqua_dot", "white", "gold"]
    for c in order + [k for k in by_color if k not in order]:
        if c not in by_color:
            continue
        g = unary_union(by_color[c])
        body.append(f'<path d="{geom_d(g, s, -half, half)}" fill="{PALETTE.get(c, c)}" fill-rule="evenodd"/>')
    return svg_doc(W, W, "".join(body), PALETTE["bg"])


def png_from_layers(path, layers, half, px=1600, extra=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    fig = plt.figure(figsize=(px / 200, px / 200), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])

    def patch(g, fc, ec="none", alpha=1.0, lw=0.0, z=1):
        for p in polys_of(g):
            verts, codes = [], []
            for ring in [p.exterior] + list(p.interiors):
                cs = list(ring.coords)
                verts += cs
                codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), facecolor=fc, edgecolor=ec, lw=lw, alpha=alpha, zorder=z))

    for c, g in layers:
        patch(g, PALETTE.get(c, c), z=2 if c in ("gold", "white") else 1)
    if extra:
        for g, fc, ec, a in extra:
            patch(g, fc, ec, a, 0.6, z=5)
    fig.savefig(path, facecolor=PALETTE["bg"])
    plt.close(fig)


def plate_svg(part, scale=4.0, pad=4.0, fill="#cfd5dc", stroke="#5b6573"):
    g = part.outline
    minx, miny, maxx, maxy = g.bounds
    minx -= pad
    miny -= pad
    maxx += pad
    maxy += pad
    s = scale
    W, H = (maxx - minx) * s, (maxy - miny) * s
    body = [f'<path d="{geom_d(g.difference(part.cuts) if part.cuts is not None else g, s, minx, maxy)}" fill="{fill}" stroke="{stroke}" stroke-width="1" fill-rule="evenodd"/>']
    if part.engrave is not None and not part.engrave.is_empty:
        body.append(f'<path d="{geom_d(part.engrave, s, minx, maxy)}" fill="{stroke}" fill-rule="evenodd"/>')
    return svg_doc(W, H, "".join(body))
