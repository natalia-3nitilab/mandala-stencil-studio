#!/usr/bin/env python3
"""Generate book/index.html (project book, v3) from the real parts and the build manifest."""
import json
import os
import re
import html

import make_v3 as MK
import v3_more as M

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = os.path.join(HERE, "book")
man = json.load(open(os.path.join(HERE, "stl", "manifest.json")))
P = MK.build_all()
FILE = dict(MK.FILES)
checks = man.get("_checks", [])
n_pass, n_all = sum(c["pass"] for c in checks), len(checks)

old = open(os.path.join(BOOK, "index.html")).read()
css = re.search(r"<style>(.*?)</style>", old, re.S).group(1)
css += """
.mixer { display:grid; grid-template-columns: minmax(0, 1fr) minmax(0, 300px); gap: 24px; align-items: start; }
.stage { position: relative; aspect-ratio: 1 / 1; border-radius: 6px; overflow: hidden; box-shadow: var(--shadow); background: var(--mx-bg, #0b0f14); max-width: 100%; }
.stage > div { position: absolute; inset: 0; }
.stage svg { width: 100%; height: 100%; display: block; }
.stage .ln { fill: var(--mx-line, #3fd6d0); } .stage .dw { fill: var(--mx-white, #f4efe2); } .stage .dg { fill: var(--mx-gold, #f2c45a); }
.controls { display: grid; gap: 16px; }
.controls fieldset { border: 1px solid var(--rule); border-radius: 8px; padding: 10px 12px; display: grid; gap: 6px; margin: 0; }
.controls legend { font: 500 .74rem/1 var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); padding: 0 4px; }
.controls label { display: flex; gap: 8px; align-items: center; font-size: .92rem; cursor: pointer; }
.controls .parts-used { font-family: var(--f-mono); font-size: .8rem; color: var(--muted); }
.gallery { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.gallery figure { margin: 0; display: grid; gap: 4px; }
.gallery figcaption { font-size: .78rem; color: var(--muted); }
.pill { font: 500 .72rem/1 var(--f-mono); padding: 4px 7px; border-radius: 999px; background: var(--surface-2); color: var(--muted); }
@media (max-width: 900px) { .gallery { grid-template-columns: repeat(3, minmax(0, 1fr)); } .mixer { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 520px) { .gallery { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
"""


def esc(s):
    return html.escape(str(s))


def placements_text(p):
    pl = getattr(p, "placements", [])
    if not pl:
        return "once"
    kind = getattr(p, "kind", "")
    labs = []
    for l, _, f in pl:
        if l not in labs:
            labs.append(l)
    faces = sorted({f for _, _, f in pl})
    where = "·".join(labs)
    if kind == "wedge":
        return f"{'A then B' if faces == ['A', 'B'] else 'A'} at hub {where if len(labs) < 8 else '1–8'}"
    if kind == "insert":
        if len(pl) == 1:
            return "once"
        return f"{'A then B' if faces == ['A', 'B'] else 'A'} at notch {where}"
    if getattr(p, "role", "") == "corner":
        return "4 corners"
    return "once"


def card(pid):
    p = P[pid]
    m = man.get(pid, {})
    vol = m.get("volume_cm3", 0)
    size = m.get("size_mm", [0, 0, 0])
    mins = int(round(6 + vol * 6, -1)) or 10
    note = getattr(p, "note", "") or ""
    faces = "two faces" if getattr(p, "two_faced", False) else "one face"
    if getattr(p, "role", "") in ("corner", "jig"):
        faces = "prints lips up"
    return f"""<article class="part"><div class="pic"><img src="img3/part_{pid}.svg" alt="{esc(p.name)} drawing" loading="lazy"></div>
<div class="meta"><div class="id"><code>{pid}</code><h3>{esc(p.name)}</h3></div><p>{esc(note)}</p>
<dl><dt>use</dt><dd>{esc(placements_text(p))}</dd><dt>size</dt><dd>{size[0]:.0f} × {size[1]:.0f} mm · {faces}</dd>
<dt>print</dt><dd>~{mins} min · {vol * 1.24:.0f} g</dd><dt>file</dt><dd>{esc(FILE.get(pid, ''))}</dd></dl></div></article>"""


def grid(pids):
    return '<div class="parts">' + "".join(card(p) for p in pids) + "</div>"


def step(img, title, items, alt):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<div class="step"><div class="canvas"><img src="img3/{img}.svg" alt="{esc(alt)}" loading="lazy" width="480" height="480"></div><h3>{title}</h3><ul>{lis}</ul></div>'


K1 = ["H3", "J20", "FA", "FB", "FC", "FD", "FE", "R1", "DM", "PT", "K1"]
K2 = ["J30", "RC", "FN", "GP", "GH", "ST", "HL", "K2"]
CORE_PARTS = ["B0", "SF", "MK1", "MK2", "SE1", "SE2", "SE3", "MT1", "MT2", "MT3", "MT4", "MT5", "MT6"]
LACE = ["AR", "LT", "OR", "OP"]
vol_k1 = sum(man[p]["volume_cm3"] for p in K1 if p in man)
vol_k2 = sum(man[p]["volume_cm3"] for p in K2 if p in man)
vol_lib = sum(man[p]["volume_cm3"] for p in CORE_PARTS + LACE if p in man)

steps1 = "".join([
    step("k1_s01_hub", "Centre the hub", ["A rice grain of putty in each of the 3 pockets under the hub.",
         "Hook the jig on a canvas corner. Drop the hub in with number 6 on the jig’s tooth. Press, lift the jig."], "Jig holding the hub at the canvas centre"),
    step("k1_s02_fa", "Flower of Life: FA", ["Drop FA in: its two teeth go into two inner notches, the bump sits opposite.",
         "Trace inside the 3 circles. Lift, flip to face B at the same notch: 3 more."], "Insert FA in the hub with its teeth in gold"),
    step("k1_s03_fb", "Inner ring: FB", ["One circle per face. Face A then B at notches 1, 2 and 3 gives all six."], "Insert FB at notch 2"),
    step("k1_s04_fd", "Sides FC, centre FD", ["FC: face A at notches 1 and 2.",
         "FD: trace the centre circle, then the border in the gap between the insert and the hub. Flip, trace the border again to close the tab gaps."], "Insert FD tracing the border in the lane"),
    step("k1_s05_ring", "Hub ring: R1", ["At each number: face A, trace the circle in the gap between hub and piece. Flip, face B.",
         "The tabs never cover the same spot on both faces, so the circle closes."], "Ring piece R1 at number 3"),
    step("k1_s06_domeA", "Dome, face A", ["Smooth edge = arc. Notches = pearls. 8 slots = rays. Cut-out = sun."], "Dome piece face A at number 1"),
    step("k1_s07_domeB", "Dome, face B", ["Same number, flipped: the other half of the arc and pearls, and 8 rays between the first 8."], "Dome piece face B at number 1"),
    step("k1_s08_petal", "Petals", ["Face A draws the petal right of the number, face B the one on the left.",
         "Edge = petal, opening = inner petal, grooved pockets = pearls."], "Petal piece face B at number 1"),
    step("k1_s09_dots", "Dots", ["Hub: glide each groove, press at every hole (big holes = big marker).", "FE: the Flower of Life crossings, along the lattice grooves."], "Dot insert FE in the hub"),
    step("k1_s10_corner", "Corners", ["Hook K1’s lips on each corner. Arcs in the channels, dots along the grooves."], "Corner piece on the top-right corner"),
    step("k1_s11_done", "Finish", ["Peel the hub off slowly. Touch up, cure 24 h, spray varnish."], "Finished Seed Bloom"),
])
steps2 = "".join([
    step("k2_s01_ring", "Ring C2: RC", ["After the Seed Bloom centre (with J30): smooth edge = ring, notches = outer pearls, grooved pockets = inner pearls."], "Ring piece RC"),
    step("k2_s02_fan", "Rainbow fans: FN", ["Edge = outer arc, slots = inner arcs, grooved pockets and crown notches = dots."], "Fan piece FN"),
    step("k2_s03_petal", "Great petals: GP", ["Only at 1, 3, 5, 7. Edge = outline; face B closes the gap at the arm."], "Great petal GP at number 3"),
    step("k2_s04_heart", "Petal hearts: GH", ["Same numbers. Edge = middle teardrop, opening = inner teardrop."], "Petal heart GH"),
    step("k2_s05_star", "Star discs: ST", ["Only at 2, 4, 6, 8. Edge = circle, sparkles = pockets on cross grooves."], "Star disc ST at number 2"),
    step("k2_s06_halo", "Halos: HL", ["Same numbers. Outer edge = echo circle, inner notches = pearls."], "Halo HL at number 4"),
    step("k2_s07_corner", "Corners: K2", ["Hook on each corner."], "Corner K2"),
])

gal = "".join(f'<figure><div class="canvas"><img src="img3/r_{c}_{r}.svg" alt="{c} centre with {r} ring" loading="lazy" width="320" height="320"></div>'
              f'<figcaption>{c.title()} + {r.title()}</figcaption></figure>' for c in M.CORES for r in M.RINGS)

core_names = {"fol": "Flower of Life", "sunflower": "Sunflower", "merkaba": "Merkaba", "seed": "Seed of Life", "metatron": "Metatron’s Cube"}
ring_names = {"bloom": "Bloom (domes + petals)", "lace": "Lace (arches, lotus, ring, petals)"}
pal_vals = {"turquoise": ("#0b0f14", "#3fd6d0", "#f4efe2", "#f2c45a"), "moonlight": ("#121a3d", "#f1ece0", "#8fe3ff", "#f2c45a"),
            "rose": ("#140c16", "#ff7aa8", "#c9b6ff", "#ffd27a"), "gold": ("#101010", "#f2c45a", "#f4efe2", "#3fd6d0")}
mixer_parts = {c: M.CORES[c] for c in M.CORES}
mixer_rings = {r: M.RINGS[r] for r in M.RINGS}

body = f"""<title>Mandala Stencil Studio</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style>

<nav class="bar" aria-label="Sections"><div class="wrap">
<span class="brand">Stencil Studio</span>
<a href="#how">How it works</a><a href="#phases">Phases</a><a href="#print">Printing</a><a href="#kit01">Kit 01</a>
<a href="#kit02">Kit 02</a><a href="#library">Library</a><a href="#mixer">Mixer</a><a href="#rules">Rules</a><a href="#files">Files</a>
</div></nav>

<header class="hero"><div class="wrap">
<div class="copy">
<span class="eyebrow">Sacred geometry · acrylic marker · 3D printed · v3</span>
<h1>Mandala Stencil Studio</h1>
<p class="lede">3D-printed stencils for precise sacred-geometry mandalas in acrylic marker, with no compass and no pencil. Every piece locks onto one hub, does one motif, and draws with its edges, its openings and its grooved dot rows.</p>
<p>v3 is a rework after your review. The lock now uses solid V-teeth. Every wall is at least 1.6 mm. Dots are lines with pockets. Everything prints flat with no supports.</p>
<div class="facts">
<div class="fact"><b>{len(MK.FILES)}</b><span>printable parts across 2 kits and a library</span></div>
<div class="fact"><b>{n_pass}/{n_all}</b><span>fit, path, wall, line and dot checks pass</span></div>
<div class="fact"><b>10</b><span>recipes from 5 centres × 2 rings</span></div>
</div></div>
<figure class="canvas" style="margin:0"><img src="img3/k1_turquoise.svg" alt="Kit 01 Seed Bloom v3: 19-circle Flower of Life, dotted hub band, 16-ray domes, pearl petals, corner webs" width="600" height="600"></figure>
</div></header>

<section id="how"><div class="wrap">
<span class="eyebrow">How it works</span>
<h2>One hub. Every piece locks on, works on both faces, and draws with its edges</h2>
<div class="rules">
<div class="rule"><b>Solid V-teeth</b><p>The hub has a V-notch every 7.5° (48 around the outside, 6 inside). Pieces have full-height V-teeth, 3.6 mm wide. They drop in and lift straight up, can’t turn, and print as plain solid triangles.</p></div>
<div class="rule"><b>Both faces</b><p>A tooth is the same top and bottom, so every piece also works flipped. Face B draws the mirror image: the other half of an arc, rays between rays, the petal on the other side of the number.</p></div>
<div class="rule"><b>Lanes, not notched edges</b><p>The hub’s notched edges are never traced. The ring around the hub is traced in a 2.6 mm gap between the hub and the ring piece. A centre’s border is traced in a 2.4 mm gap between the insert and the hub. Face A and face B tabs never cover the same spot, so both circles close.</p></div>
<div class="rule"><b>Edges and openings draw</b><p>Trace around a piece for its outline, inside an opening for an inner shape. Round holes give perfect circles: the Flower of Life is now the classic 19 circles, every one a whole opening.</p></div>
<div class="rule"><b>Dots: a line with pockets</b><p>Dot holes are linked by a 0.6 mm groove on each face. Glide the tip along the groove and press at each pocket. Edge notches work the same way along a rim.</p></div>
<div class="rule"><b>Strong and printable</b><p>Every wall is at least 1.6 mm (4 nozzle lines), checked automatically. Parts print flat on either face with no supports. Jigs and corner pieces print lips up.</p></div>
</div>
<div class="two">
<figure style="margin:0;display:grid;gap:8px"><img src="img3/v3_lock.svg" alt="Top view: two gold V-teeth of the dome piece sitting in V-notches of the hub" loading="lazy"><figcaption class="muted">Top view at hub number 1: the dome’s two gold V-teeth in the hub notches.</figcaption></figure>
<figure style="margin:0;display:grid;gap:8px"><img src="img3/v3_section.svg" alt="Side views: full-height tooth beside the hub; groove with pockets" loading="lazy"><figcaption class="muted">Side views: a full-height tooth (no layers), and a dot row as a groove with pockets.</figcaption></figure>
</div>
</div></section>

<section id="phases"><div class="wrap">
<span class="eyebrow">The long project</span>
<h2>Phases</h2>
<div class="phases">
<article class="phase"><div class="tag"><b>0</b><span class="chip">Ready to print</span></div><div class="body"><h3>Calibrate</h3><ul><li>Print the Fit Card (T0), test each marker in its channels and holes, and note your sizes.</li><li>Print the hub and one dome piece to feel the lock before printing the rest.</li></ul></div></article>
<article class="phase"><div class="tag"><b>1</b><span class="chip">Ready to print · v3</span></div><div class="body"><h3>Kit 01 “Seed Bloom”, 20 cm</h3><ul><li>Hub, jig, the 19-circle Flower of Life (5 inserts), hub ring, dome, petal, corner.</li></ul></div></article>
<article class="phase"><div class="tag"><b>2</b><span class="chip">Ready to print · v3</span></div><div class="body"><h3>Kit 02 “Turquoise Bloom”, 30 cm</h3><ul><li>Kit 01’s centre plus ring C2, rainbow fans, great petals and hearts, star discs and halos, corner fans.</li></ul></div></article>
<article class="phase"><div class="tag"><b>3</b><span class="chip">Ready to print · v3</span></div><div class="body"><h3>Library</h3><ul><li>Centres: Sunflower, Merkaba, Seed of Life, Metatron’s Cube. A second ring set: Lace.</li><li>10 recipes and a mixer to try any combination.</li></ul></div></article>
<article class="phase"><div class="tag"><b>4</b><span class="chip later">Later</span></div><div class="body"><h3>Kits for other people</h3><ul><li>Test prints, wear tests, beginner tests, instruction cards, packaging.</li></ul></div></article>
<article class="phase"><div class="tag"><b>5</b><span class="chip later">Queued</span></div><div class="body"><h3>Ukrainian stitching</h3><ul><li>Stencils for vyshyvanka-style patterns, then a mandala that combines the Flower of Life with Ukrainian stitching.</li></ul></div></article>
</div></div></section>

<section id="print"><div class="wrap">
<span class="eyebrow">Printing</span>
<h2>Flat, no supports</h2>
<div class="two"><div class="tbl"><table><thead><tr><th>Setting</th><th>Value</th></tr></thead><tbody>
<tr><td>Material</td><td>PLA to start, PETG for pieces you use a lot</td></tr>
<tr><td>Nozzle / layer</td><td class="num">0.4 mm / 0.2 mm</td></tr>
<tr><td>Infill</td><td>100% (2 mm parts)</td></tr><tr><td>Supports / brim</td><td>None / off</td></tr>
<tr><td>Orientation</td><td>As in the files: flat, either face down. J20, J30, K1, K2 print lips up.</td></tr>
<tr><td>Elephant foot compensation</td><td class="num">0.1–0.15 mm</td></tr></tbody></table></div>
<div style="display:grid;gap:10px;align-content:start">
<p>Kit 01: about <b>{vol_k1:.0f} cm³ ({vol_k1 * 1.24:.0f} g)</b>. Kit 02 adds <b>{vol_k2:.0f} cm³</b>. The library adds <b>{vol_lib:.0f} cm³</b>.</p>
<p>Print the hub and one dome first. If the teeth feel tight, lower the flow 2–3%. If loose, raise it.</p>
<p class="muted">Every file is a closed solid. The build script checks every piece on both faces: seated with no overlap, a clear straight path down and up, locked against turning and sliding, walls ≥ 1.6 mm, every line closed, and no dot on another element’s paint.</p>
</div></div></div></section>

<section id="kit01"><div class="wrap">
<span class="eyebrow">Phase 1 · 20 × 20 cm / 8 × 8 in</span>
<h2>Kit 01 · Seed Bloom</h2>
<div class="paintings" style="grid-template-columns:repeat(2,minmax(0,1fr))">
<figure class="painting" style="margin:0"><div class="canvas"><img src="img3/k1_turquoise.svg" alt="Seed Bloom, turquoise" width="560" height="560"></div><h3>Turquoise</h3></figure>
<figure class="painting" style="margin:0"><div class="canvas"><img src="img3/k1_moonlight.svg" alt="Seed Bloom, moonlight" width="560" height="560"></div><h3>Moonlight</h3></figure>
</div>
{grid(K1)}
<h3>Step by step</h3>
<div class="steps">{steps1}</div>
</div></section>

<section id="kit02"><div class="wrap">
<span class="eyebrow">Phase 2 · 30 × 30 cm / 12 × 12 in</span>
<h2>Kit 02 · Turquoise Bloom</h2>
<div class="paintings" style="grid-template-columns:repeat(2,minmax(0,1fr))">
<figure class="painting" style="margin:0"><div class="canvas"><img src="img3/k2_turquoise.svg" alt="Turquoise Bloom 30 cm" width="600" height="600"></div><h3>Turquoise</h3></figure>
<figure class="painting" style="margin:0"><div class="canvas"><img src="img3/k2_rose.svg" alt="Turquoise Bloom in rose" width="600" height="600"></div><h3>Rose</h3></figure>
</div>
<p class="muted">Uses Kit 01’s hub, centre inserts, R1, DM and PT, plus:</p>
{grid(K2)}
<h3>Step by step</h3>
<div class="steps">{steps2}</div>
</div></section>

<section id="library"><div class="wrap">
<span class="eyebrow">Phase 3 · library</span>
<h2>More centres and a second ring set</h2>
<h3>Centres</h3>
{grid(CORE_PARTS)}
<h3>Lace ring set</h3>
{grid(LACE)}
<h3>Recipes</h3>
<div class="gallery">{gal}</div>
</div></section>

<section id="mixer"><div class="wrap">
<span class="eyebrow">Design a kit</span>
<h2>Mixer</h2>
<div class="mixer">
<div class="stage" id="stage"><div data-layer="hub"></div><div data-layer="core"></div><div data-layer="ring"></div><div data-layer="corner"></div></div>
<div class="controls">
<fieldset><legend>Centre</legend>{''.join(f'<label><input type="radio" name="core" value="{c}" {"checked" if c == "fol" else ""}> {core_names[c]}</label>' for c in M.CORES)}</fieldset>
<fieldset><legend>Ring</legend>{''.join(f'<label><input type="radio" name="ring" value="{r}" {"checked" if r == "bloom" else ""}> {ring_names[r]}</label>' for r in M.RINGS)}</fieldset>
<fieldset><legend>Colours</legend>{''.join(f'<label><input type="radio" name="pal" value="{k}" {"checked" if k == "turquoise" else ""}> {k.title()}</label>' for k in pal_vals)}</fieldset>
<fieldset><legend>Corners</legend><label><input type="checkbox" id="corners" checked> Corner webs (K1)</label></fieldset>
<p class="parts-used" id="used"></p>
</div></div></div></section>

<section id="rules"><div class="wrap">
<span class="eyebrow">Alignment and application</span>
<h2>Rules</h2>
<div class="rules">
<div class="rule"><b>Never move the hub</b><p>Everything refers to it. If it shifts, press it back with the jig.</p></div>
<div class="rule"><b>Teeth first, then flat</b><p>Set the teeth in their notches, then lay the piece flat. Lift straight up.</p></div>
<div class="rule"><b>Face A, then flip to face B</b><p>At every placement in the tables. Some pieces are one-faced; their table says “A”.</p></div>
<div class="rule"><b>Edges: light contact all round</b><p>Keep the marker upright and the tip touching the edge or the opening wall.</p></div>
<div class="rule"><b>Lanes: ride the piece, not the hub</b><p>In the gap around the hub, keep the tip against the piece’s edge. The hub side has notches.</p></div>
<div class="rule"><b>Grooves: glide, press, glide</b><p>The tip can’t reach the canvas in the groove, only at the pockets.</p></div>
<div class="rule"><b>Big holes = colour 3, small = colour 2</b><p>The hole size tells you which marker to use.</p></div>
<div class="rule"><b>Prime on scrap, wipe between colours</b><p>A flooded tip runs under the piece. Wipe the piece’s face when you change colour or flip it.</p></div>
</div></div></section>

<section id="files"><div class="wrap">
<span class="eyebrow">Files</span>
<h2>Project folder</h2>
<div class="two"><ul class="files">{''.join(f'<li>stl/{esc(fn)}</li>' for _, fn in MK.FILES)}</ul>
<div style="display:grid;gap:10px;align-content:start">
<p><span class="mono">make_v3.py</span> rebuilds every STL from your marker profile and runs all {n_all} checks.</p>
<p><span class="mono">render_v3.py</span> renders the paintings, recipes, mixer layers, step frames and part drawings.</p>
<p><span class="mono">v3.py</span> is the system (hub, lock, lanes, grooves, pieces). <span class="mono">v3_kit1.py</span> and <span class="mono">v3_more.py</span> are the designs.</p>
<pre>python3 make_v3.py --line 2.0 --dot-s 2.4 --dot-m 3.2</pre>
<p class="muted">Earlier versions (v1 plates, v2 prototype) are kept in <span class="mono">archive/</span>. They do not fit the v3 hub.</p>
</div></div></div></section>

<footer><div class="wrap">Mandala Stencil Studio · v3 · millimetres · hub numbers run clockwise from the top.</div></footer>

<script>
(function () {{
  var PAL = {json.dumps(pal_vals)};
  var CORES = {json.dumps(mixer_parts)};
  var RINGS = {json.dumps(mixer_rings)};
  var cache = {{}};
  function load(name) {{
    if (cache[name]) return cache[name];
    cache[name] = fetch('img3/mx_' + name + '.svg').then(function (r) {{ return r.text(); }}).catch(function () {{ return ''; }});
    return cache[name];
  }}
  function val(n) {{ var e = document.querySelector('input[name="' + n + '"]:checked'); return e ? e.value : null; }}
  function render() {{
    var st = document.getElementById('stage');
    var core = val('core'), ring = val('ring'), pal = PAL[val('pal')];
    st.style.setProperty('--mx-bg', pal[0]); st.style.setProperty('--mx-line', pal[1]);
    st.style.setProperty('--mx-white', pal[2]); st.style.setProperty('--mx-gold', pal[3]);
    var want = {{ hub: 'hub', core: 'core_' + core, ring: 'ring_' + ring, corner: document.getElementById('corners').checked ? 'corner' : '' }};
    Object.keys(want).forEach(function (k) {{
      var el = st.querySelector('[data-layer="' + k + '"]');
      if (!want[k]) {{ el.innerHTML = ''; return; }}
      load(want[k]).then(function (t) {{ el.innerHTML = t; }});
    }});
    var used = CORES[core].concat(['H3'], RINGS[ring], document.getElementById('corners').checked ? ['K1'] : []);
    document.getElementById('used').textContent = 'Parts: ' + used.join(' · ');
  }}
  document.querySelectorAll('.controls input').forEach(function (i) {{ i.addEventListener('change', render); }});
  render();
}})();
</script>
"""
open(os.path.join(BOOK, "index.html"), "w").write(body)
print("book written", len(body))
