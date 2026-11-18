"""Fit check for the v2 reversible system: every piece, both faces."""
import math
import v2
import design01 as d1

def vol(m):
    return 0.0 if m.is_empty() else m.volume()

def run():
    hub = v2.build_hub_v2()
    H = hub.solid()
    pieces = [v2.build_dome(), v2.build_petal()]
    F1, F2 = d1.core_parts()
    inserts = [v2.insert_v2(F1), v2.insert_v2(F2), v2.insert_v2(v2.build_sunflower())]
    res = []
    for pc in pieces:
        for face in ("A", "B"):
            base = pc.solid_face(face)
            for deg in (0.0, 45.0):
                m = base.rotate([0, 0, -deg]) if deg else base
                ux, uy = math.sin(math.radians(deg)), math.cos(math.radians(deg))
                pushed = base.translate([0, -0.35, 0]).rotate([0, 0, -deg]) if deg else base.translate([0, -0.35, 0])
                ov, seat = vol(H ^ m), vol(H ^ pushed) > 5e-4
                res.append((f"{pc.pid} face {face} at {deg:.0f}", ov < 1e-4 and seat, f"overlap {ov:.4f}, seated={seat}"))
            off = vol(H ^ base.rotate([0, 0, -3.75]))
            res.append((f"{pc.pid} face {face} half-notch off", off > 1e-3, f"blocked {off:.3f} mm3"))
    for ins in inserts:
        for face in ("A", "B"):
            m0 = ins.solid()
            if face == "B":
                m0 = m0.rotate([0, 180, 0]).translate([0, 0, v2.T])
            for deg in (0, 60, 120):
                ov = vol(H ^ m0.rotate([0, 0, -deg]))
                res.append((f"{ins.pid} face {face} @{deg}", ov < 1e-4, f"overlap {ov:.4f}"))
            off = vol(H ^ m0.rotate([0, 0, -30]))
            res.append((f"{ins.pid} face {face} between notches", off > 1e-3, f"blocked {off:.3f}"))
    return res, hub, pieces, inserts

if __name__ == "__main__":
    res, *_ = run()
    for n, ok, m in res:
        print(("PASS " if ok else "FAIL ") + f"{n:30s} {m}")
    print(sum(ok for _, ok, _ in res), "/", len(res))
