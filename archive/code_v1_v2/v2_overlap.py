import v2, v2_render as R
from shapely.strtree import STRtree
from collections import Counter
from geom import rot
hub, dm, pt = R.build()
items = []
for pc in (dm, pt):
    for deg in R.NUM:
        for face in "AB":
            for c, g in pc.painted(deg, face):
                items.append((pc.pid, face, "dot" if c in ("gold", "white") else "line", g))
for f in hub.feats:
    items.append(("H2", "-", "dot", f.drawn()))
tree = STRtree([i[3] for i in items]); bad = Counter()
for i, (pid, face, kind, g) in enumerate(items):
    if kind != "dot": continue
    for j in tree.query(g):
        if j == i: continue
        if g.intersection(items[j][3]).area > 0.05:
            bad[(pid, items[j][0], items[j][2])] += 1
print("unintended dot overlaps:", dict(bad) or 0)
