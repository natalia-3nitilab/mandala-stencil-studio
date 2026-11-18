#!/usr/bin/env python3
"""Build Kit 01 "Seed Bloom": STL files, previews and a fit check.

    python3 make_kit.py                 # default marker profile
    python3 make_kit.py --line 2.0 --dot-s 2.4 --dot-m 3.2   # after the Fit Card test

Needs: pip install shapely numpy manifold3d trimesh matplotlib
"""
import argparse
import json
import os
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument("--line", type=float, help="channel width for your fine line marker (mm)")
ap.add_argument("--dot-s", type=float, help="small dot hole (mm)")
ap.add_argument("--dot-m", type=float, help="medium dot hole (mm)")
ap.add_argument("--out", default="stl", help="output folder")
ap.add_argument("--no-check", action="store_true")
args = ap.parse_args()

import geom  # noqa: E402
if args.line:
    geom.LINE_SLOT = args.line
    geom.TIP_R = args.line / 2
if args.dot_s:
    geom.DOT_S = args.dot_s
if args.dot_m:
    geom.DOT_M = args.dot_m

import importlib  # noqa: E402
import parts  # noqa: E402
import design01  # noqa: E402
importlib.reload(parts)
importlib.reload(design01)

import numpy as np  # noqa: E402
import manifold3d as m3d  # noqa: E402
from shapely import affinity  # noqa: E402
from render import png_from_layers, painting_svg, plate_svg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, args.out)
PREV = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

FILES = {
    "T0": "00_T0_fit_card.stl",
    "J20": "01_J20_centre_jig_20cm_8in.stl",
    "H1": "02_H1_hub.stl",
    "F1": "03_F1_flower_of_life_lines.stl",
    "F2": "04_F2_flower_of_life_dots.stl",
    "A1": "05_A1_plate_A_domes_petals.stl",
    "B1": "06_B1_plate_B_rays_inner_petals.stl",
    "D1": "07_D1_plate_D_dots.stl",
    "K1": "08_K1_corner_web.stl",
}

t0 = time.time()
kit = design01.build_kit()
report = {}
for pid, part in kit.items():
    info = part.export_stl(os.path.join(OUT, FILES[pid]))
    info["file"] = FILES[pid]
    info["name"] = part.name
    info["warnings"] = part.warnings
    info["positions"] = [p[0] for p in part.positions]
    info["order"] = part.order
    report[pid] = info
    flag = "OK " if info["watertight"] and not part.warnings else "!! "
    print(f"{flag}{pid:4s} {part.name:34s} {info['size_mm']} mm  {info['volume_cm3']} cm3  {part.warnings}")


# ------------------------------------------------------------------ fit check
def solid(part, deg=0.0, dx=0.0, dy=0.0):
    m = part.solid()
    if deg:
        m = m.rotate([0, 0, -deg])
    if dx or dy:
        m = m.translate([dx, dy, 0])
    return m


def vol(m):
    return 0.0 if m.is_empty() else m.volume()


checks = []
if not args.no_check:
    hub = solid(kit["H1"])
    for pid in ("A1", "B1", "D1"):
        for lab, deg in kit[pid].positions[:2]:
            w = solid(kit[pid], deg)
            clash = vol(hub ^ w)
            # pushed 0.35 mm further in must collide -> teeth really sit in the notches
            import math
            ux, uy = math.sin(math.radians(deg)), math.cos(math.radians(deg))
            w2 = solid(kit[pid], deg, -0.35 * ux, -0.35 * uy)
            seated = vol(hub ^ w2) > 0.0005
            checks.append((f"{pid} at hub {lab}", clash < 1e-4, f"overlap {clash:.4f} mm3, seated={seated}"))
            # rotated half a notch -> teeth must hit the hub (no wrong positions)
            w3 = solid(kit[pid], deg + 3.75)
            checks.append((f"{pid} half-notch off", vol(hub ^ w3) > 0.001, f"blocked overlap {vol(hub ^ w3):.3f} mm3"))
    for pid in ("F1", "F2"):
        for deg in (0, 60, 120):
            f = solid(kit[pid], deg)
            checks.append((f"{pid} in hub @{deg}", vol(hub ^ f) < 1e-4, f"overlap {vol(hub ^ f):.4f} mm3"))
        f = solid(kit[pid], 30)
        checks.append((f"{pid} ear between notches", vol(hub ^ f) > 0.001, f"blocked overlap {vol(hub ^ f):.3f} mm3"))
    J = kit["J20"]
    j = solid(J, 0, -J.half, -J.half)
    checks.append(("J20 around hub", vol(hub ^ j) < 1e-4, f"overlap {vol(hub ^ j):.4f} mm3"))
    j_off = J.solid().translate([-J.half, -J.half, 0]).rotate([0, 0, -3.75])
    checks.append(("J20 tooth keys the hub", vol(hub ^ j_off) > 0.001, f"half-notch turn blocked, overlap {vol(hub ^ j_off):.3f} mm3"))
    for name, ok, msg in checks:
        print(("PASS " if ok else "FAIL ") + f"{name:28s} {msg}")

# ------------------------------------------------------------------ previews
L = design01.painting_layers(kit)
png_from_layers(os.path.join(PREV, "painting01.png"), L, design01.HALF, px=2000)
with open(os.path.join(PREV, "painting01.svg"), "w") as fh:
    fh.write(painting_svg(L, design01.HALF, scale=3.0))
for pid, part in kit.items():
    with open(os.path.join(PREV, f"plate_{pid}.svg"), "w") as fh:
        fh.write(plate_svg(part))

report["_checks"] = [{"name": n, "pass": bool(ok), "detail": m} for n, ok, m in checks]
report["_profile"] = {"LINE_SLOT": geom.LINE_SLOT, "DOT_S": geom.DOT_S, "DOT_M": geom.DOT_M, "T": geom.T}
with open(os.path.join(OUT, "kit01_manifest.json"), "w") as fh:
    json.dump(report, fh, indent=1)
print(f"done in {time.time() - t0:.1f}s -> {OUT}")
if any(not ok for _, ok, _ in checks):
    sys.exit(1)
