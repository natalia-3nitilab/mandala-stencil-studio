#!/usr/bin/env python3
"""Build the stencil kits: STL files, previews and a fit + paint-overlap check.

    python3 make_kit.py                 # both kits, default marker profile
    python3 make_kit.py --kit 1         # only Kit 01 Seed Bloom (20 cm)
    python3 make_kit.py --line 2.0 --dot-s 2.4 --dot-m 3.2   # after the Fit Card test

Kit 02 Turquoise Bloom (30 cm) reuses H1 F1 F2 A1 B1 D1 from Kit 01 and adds files 10-17.
Needs: pip install shapely numpy manifold3d trimesh matplotlib
"""
import argparse
import json
import math
import os
import sys
import time
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("--kit", default="all", choices=["1", "2", "all"])
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

import design01  # noqa: E402
import design02  # noqa: E402
from geom import rot  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402
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
    "J30": "10_J30_centre_jig_30cm_12in.stl",
    "E1": "11_E1_plate_E_rainbow_fans.stl",
    "D2": "12_D2_plate_D2_ring_border_dots.stl",
    "P2": "13_P2_plate_P2_great_petals.stl",
    "P3": "14_P3_plate_P3_petal_dots.stl",
    "S1": "15_S1_plate_S1_star_circles.stl",
    "S2": "16_S2_plate_S2_echo_star_field.stl",
    "K2": "17_K2_corner_fan_30cm.stl",
}
KIT2_NEW = ["J30", "E1", "D2", "P2", "P3", "S1", "S2", "K2"]

t0 = time.time()
kit1 = design01.build_kit() if args.kit in ("1", "all") else None
kit2 = design02.build_kit() if args.kit in ("2", "all") else None

report = {}
todo = []
if kit1:
    todo += [(pid, kit1[pid]) for pid in kit1]
if kit2:
    todo += [(pid, kit2[pid]) for pid in KIT2_NEW]
for pid, part in todo:
    info = part.export_stl(os.path.join(OUT, FILES[pid]))
    info.update(file=FILES[pid], name=part.name, warnings=part.warnings,
                positions=[p[0] for p in part.positions], order=part.order)
    report[pid] = info
    flag = "OK " if info["watertight"] and not part.warnings else "!! "
    print(f"{flag}{pid:4s} {part.name:34s} {[float(x) for x in info['size_mm']]} mm  {info['volume_cm3']} cm3  {part.warnings}")


# ------------------------------------------------------------------ fit check
def vol(m):
    return 0.0 if m.is_empty() else m.volume()


def placed(part, deg, inward=0.0):
    m = part.solid()
    if inward:
        m = m.translate([0, -inward, 0])      # push towards the hub in the plate's own frame
    return m.rotate([0, 0, -deg]) if deg else m


checks = []


def wedge_checks(kit, pids):
    hub = kit["H1"].solid()
    for pid in pids:
        part = kit[pid]
        for lab, deg in part.positions[:2]:
            clash = vol(hub ^ placed(part, deg))
            seated = vol(hub ^ placed(part, deg, 0.35)) > 0.0005
            checks.append((f"{pid} at hub {lab}", clash < 1e-4 and seated, f"overlap {clash:.4f} mm3, seated={seated}"))
        off = vol(hub ^ placed(part, part.positions[0][1] + 3.75))
        checks.append((f"{pid} half-notch off", off > 0.001, f"blocked, overlap {off:.3f} mm3"))


def jig_checks(kit, jid):
    hub = kit["H1"].solid()
    J = kit[jid]
    j = J.solid().translate([-J.half, -J.half, 0])
    checks.append((f"{jid} around hub", vol(hub ^ j) < 1e-4, f"overlap {vol(hub ^ j):.4f} mm3"))
    jo = j.rotate([0, 0, -3.75])
    checks.append((f"{jid} tooth keys the hub", vol(hub ^ jo) > 0.001, f"half-notch turn blocked, overlap {vol(hub ^ jo):.3f} mm3"))


def paint_overlaps(name, kit, layer_pids, corner_pid, corner_fn, intended):
    items = []
    for pid in layer_pids:
        part = kit[pid]
        for lab, deg in part.positions:
            for f in part.feats:
                g = f.drawn(part.cut_override if (f.kind == "hole" and part.cut_override is not None) else None)
                items.append((pid, f.group, f.kind, rot(g, deg)))
    part = kit[corner_pid]
    for lab, deg in part.positions:
        for f in part.feats:
            items.append((corner_pid, f.group, f.kind, corner_fn(f.drawn(), deg)))
    tree = STRtree([it[3] for it in items])
    bad = Counter()
    for i, (pid, grp, kind, g) in enumerate(items):
        if kind != "dot":
            continue
        for j in tree.query(g):
            if j == i:
                continue
            pj, gj, _, hj = items[j]
            key = (pid, grp, pj, gj)
            if key in intended or (pj, gj, pid, grp) in intended:
                continue
            if g.intersection(hj).area > 0.05:
                bad[key] += 1
    n = sum(bad.values())
    checks.append((f"{name} dots clear of other paint", n == 0, f"{n} unintended overlaps {dict(bad) if n else ''}"))


INTENDED = {("S1", "echobridge", "S2", "echo"), ("D1", "apex", "A1", "dome"),
            ("E1", "fancentre", "D2", "C2"), ("P3", "petbridge", "P2", "petal_out")}

if not args.no_check:
    if kit1:
        wedge_checks(kit1, ["A1", "B1", "D1"])
        hub = kit1["H1"].solid()
        for pid in ("F1", "F2"):
            for deg in (0, 60, 120):
                f = placed(kit1[pid], deg)
                checks.append((f"{pid} in hub @{deg}", vol(hub ^ f) < 1e-4, f"overlap {vol(hub ^ f):.4f} mm3"))
            f = placed(kit1[pid], 30)
            checks.append((f"{pid} ear between notches", vol(hub ^ f) > 0.001, f"blocked, overlap {vol(hub ^ f):.3f} mm3"))
        jig_checks(kit1, "J20")
        paint_overlaps("Kit 01", kit1, ["H1", "F2", "D1", "A1", "B1"], "K1", design01.corner_to_canvas, INTENDED)
    if kit2:
        wedge_checks(kit2, ["E1", "D2", "P2", "P3", "S1", "S2"])
        jig_checks(kit2, "J30")
        paint_overlaps("Kit 02", kit2, ["H1", "F2", "D1", "A1", "B1", "E1", "D2", "P2", "P3", "S1", "S2"], "K2",
                       design02.corner_to_canvas, INTENDED)
    for name, ok, msg in checks:
        print(("PASS " if ok else "FAIL ") + f"{name:30s} {msg}")

# ------------------------------------------------------------------ previews
if kit1:
    L = design01.painting_layers(kit1)
    png_from_layers(os.path.join(PREV, "painting01.png"), L, design01.HALF, px=2000)
    with open(os.path.join(PREV, "painting01.svg"), "w") as fh:
        fh.write(painting_svg(L, design01.HALF, scale=3.0))
    for pid, part in kit1.items():
        with open(os.path.join(PREV, f"plate_{pid}.svg"), "w") as fh:
            fh.write(plate_svg(part))
if kit2:
    L = design02.painting_layers(kit2)
    png_from_layers(os.path.join(PREV, "painting02.png"), L, design02.HALF, px=2400)
    for pid in KIT2_NEW:
        with open(os.path.join(PREV, f"plate_{pid}.svg"), "w") as fh:
            fh.write(plate_svg(kit2[pid]))

manifest_path = os.path.join(OUT, "manifest.json")
old = {}
if os.path.exists(manifest_path):
    try:
        old = json.load(open(manifest_path))
    except Exception:
        old = {}
old.update(report)
old["_checks"] = [{"name": n, "pass": bool(ok), "detail": m} for n, ok, m in checks]
old["_profile"] = {"LINE_SLOT": geom.LINE_SLOT, "DOT_S": geom.DOT_S, "DOT_M": geom.DOT_M, "T": geom.T}
with open(manifest_path, "w") as fh:
    json.dump(old, fh, indent=1)
print(f"done in {time.time() - t0:.1f}s -> {OUT}")
if any(not ok for _, ok, _ in checks):
    sys.exit(1)
