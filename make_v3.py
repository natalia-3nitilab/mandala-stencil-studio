#!/usr/bin/env python3
"""Build the v3 stencil system: every STL, every check, the manifest.

    python3 make_v3.py              # default marker profile
    python3 make_v3.py --line 2.0 --dot-s 2.4 --dot-m 3.2
"""
import argparse, json, os, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("--line", type=float); ap.add_argument("--dot-s", type=float); ap.add_argument("--dot-m", type=float)
ap.add_argument("--no-check", action="store_true")
args = ap.parse_args()
import geom
if args.line: geom.LINE_SLOT, geom.TIP_R = args.line, args.line / 2
if args.dot_s: geom.DOT_S = args.dot_s
if args.dot_m: geom.DOT_M = args.dot_m

import v3_kit1 as K1, v3_more as M, v3_check as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)

FILES = [  # (id, file)  — numbered in print order
    ("T0", "00_T0_fit_card.stl"),
    ("H3", "01_H3_hub.stl"), ("J20", "02_J20_jig_20cm_8in.stl"), ("J30", "03_J30_jig_30cm_12in.stl"),
    ("FA", "10_FA_flower_corners.stl"), ("FB", "11_FB_flower_inner_ring.stl"), ("FC", "12_FC_flower_sides.stl"),
    ("FD", "13_FD_flower_centre_border.stl"), ("FE", "14_FE_flower_dots.stl"),
    ("B0", "15_B0_border_ring.stl"), ("SF", "16_SF_sunflower.stl"),
    ("MK1", "17_MK1_merkaba_lines.stl"), ("MK2", "18_MK2_merkaba_dots.stl"),
    ("SE1", "19_SE1_seed_petals.stl"), ("SE2", "20_SE2_seed_centre_border.stl"), ("SE3", "21_SE3_seed_dots.stl"),
    ("MT1", "22_MT1_metatron_circles_a.stl"), ("MT2", "23_MT2_metatron_circles_b.stl"),
    ("MT3", "24_MT3_metatron_lines_a.stl"), ("MT4", "25_MT4_metatron_lines_b.stl"),
    ("MT5", "26_MT5_metatron_lines_c.stl"), ("MT6", "27_MT6_metatron_dots.stl"),
    ("R1", "30_R1_hub_ring.stl"), ("DM", "31_DM_dome.stl"), ("PT", "32_PT_petal.stl"),
    ("AR", "33_AR_arch.stl"), ("LT", "34_LT_lotus.stl"), ("OR", "35_OR_outer_ring.stl"), ("OP", "36_OP_outer_petal.stl"),
    ("K1", "37_K1_corner_20cm.stl"),
    ("RC", "40_RC_ring_c2.stl"), ("FN", "41_FN_fan.stl"), ("GP", "42_GP_great_petal.stl"), ("GH", "43_GH_petal_heart.stl"),
    ("ST", "44_ST_star_disc.stl"), ("HL", "45_HL_halo.stl"), ("K2", "46_K2_corner_30cm.stl"),
]


def build_all():
    from parts import build_fit_card
    P = K1.build_kit1()
    P.update(M.build_more())
    P["B0"] = M.build_border()
    P["T0"] = build_fit_card()
    return P


INTENDED = {("FE", x) for x in ("FA", "FB", "FC", "FD")} | {("MK2", "MK1"), ("SE3", "SE1"), ("SE3", "SE2"), ("SE2", "SE1")}
INTENDED |= {("MT6", x) for x in ("MT1", "MT2", "MT3", "MT4", "MT5")}


def recipes():
    out = {"Kit 01 Seed Bloom": M.CORES["fol"] + ["H3"] + M.RINGS["bloom"] + ["K1"],
           "Kit 02 Turquoise Bloom": M.CORES["fol"] + ["H3"] + M.RINGS["bloom"] + M.KIT2_OUTER}
    for c in M.CORES:
        for r in M.RINGS:
            out[f"{c} + {r}"] = M.CORES[c] + ["H3"] + M.RINGS[r] + ["K1"]
    return out


if __name__ == "__main__":
    t0 = time.time()
    P = build_all()
    report = {}
    for pid, fn in FILES:
        info = P[pid].export_stl(os.path.join(OUT, fn))
        info.update(file=fn, name=P[pid].name, warnings=P[pid].warnings,
                    placements=[f"{l}{f}" for l, _, f in getattr(P[pid], "placements", [])],
                    faces="A+B" if getattr(P[pid], "two_faced", False) else "A")
        report[pid] = info
        print(f"{'OK ' if info['watertight'] else '!! '}{pid:4s} {fn:36s} {[float(x) for x in info['size_mm']]} {info['volume_cm3']} cm3")
    checks = []
    if not args.no_check:
        pieces = [p for p in P.values() if getattr(p, "kind", "") in ("wedge", "insert")]
        checks += C.fit_checks(P["H3"], pieces, [P["J20"], P["J30"]])
        checks += C.wall_checks(pieces + [P["K1"], P["K2"]])
        checks += [C.line_coverage(p) for p in pieces + [P["K1"], P["K2"]] if p.lines]
        for name, pids in recipes().items():
            checks.append(C.overlap_check(name, C.painted_items(P, pids), allowed=INTENDED))
        for n, ok, m in checks:
            if not ok or "dots clear" in n:
                print(("PASS " if ok else "FAIL ") + f"{n:36s} {m}")
        print(f"checks: {sum(ok for _, ok, _ in checks)} / {len(checks)} pass")
    report["_checks"] = [{"name": n, "pass": bool(ok), "detail": m} for n, ok, m in checks]
    report["_profile"] = {"LINE_SLOT": geom.LINE_SLOT, "DOT_S": geom.DOT_S, "DOT_M": geom.DOT_M}
    json.dump(report, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print(f"done in {time.time() - t0:.0f}s")
    sys.exit(0 if all(ok for _, ok, _ in checks) else 1)
