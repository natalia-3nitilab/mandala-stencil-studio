# Mandala Stencil Studio

3D-printed stencils for painting precise sacred-geometry mandalas with acrylic markers. No compass, no pencil drafting: every stencil clicks onto one hub at the canvas centre, so every line and every dot lands where it should.

![Kit 01 Seed Bloom, simulated painting](preview/P1_turquoise.png)

**Status:** Phase 0 (calibration) and Phase 1 (Kit 01 "Seed Bloom", 20 × 20 cm) are designed and generated. All STLs are checked closed solids, and a virtual assembly test passes (22/22). They have not been test-printed or painted yet. Phase 2 (30 × 30 cm "Turquoise Bloom") is in progress.

## How the system works
- **Hub (H1):** a 108 mm ring held at the canvas centre with a little removable putty. It has 48 outer notches (one every 7.5°) and 6 inner notches.
- **Wedge plates (A1, B1, D1):** two teeth click into the hub's outer notches. Each plate is used at 8 positions: 1-3-5-7, then 2-4-6-8.
- **Inserts (F1, F2):** drop inside the hub and key into its inner notches. F1 traced at 3 consecutive notches gives the full Flower of Life.
- **Corner plate (K1):** two lips hook onto a canvas corner.
- **Three kinds of opening:** channels you glide along, openings you trace around the inside wall, and dot holes. Every opening is offset by the marker tip radius.
- **Bridges hide under dots:** closed curves keep a 1 mm bridge, placed exactly where a later plate puts a big dot.
- **Colour rule:** lines are colour 1, small holes are colour 2, big holes are colour 3.

## Kit 01 "Seed Bloom": print order
| # | File | Part | Used |
|---|------|------|------|
| 0 | `stl/00_T0_fit_card.stl` | Fit Card: test your markers first | once |
| 1 | `stl/01_J20_centre_jig_20cm_8in.stl` | Centre Jig (prints lips up, flip to use) | once |
| 2 | `stl/02_H1_hub.stl` | Hub: everything clicks onto it | stays on |
| 3 | `stl/03_F1_flower_of_life_lines.stl` | Flower of Life lines | 3 turns |
| 4 | `stl/04_F2_flower_of_life_dots.stl` | Flower of Life dots | 1× |
| 5 | `stl/05_A1_plate_A_domes_petals.stl` | Plate A: domes, sun arcs, petals | 8× |
| 6 | `stl/06_B1_plate_B_rays_inner_petals.stl` | Plate B: rays, echo arcs, inner petals | 8× |
| 7 | `stl/07_D1_plate_D_dots.stl` | Plate D: dot trails + bridge dots | 8× |
| 8 | `stl/08_K1_corner_web.stl` | Corner web (prints lips up, flip to use) | 4 corners |

PLA or PETG · 0.4 mm nozzle · 0.2 mm layers · 100 % infill · no supports · no brim · about 82 g and 5 hours.

## Painting Seed Bloom
1. Putty in the 3 hub pockets. Put the jig on a canvas corner, drop the hub in the jig ring with number 6 on the tooth, press it down, lift the jig.
2. Put F1 in the hub, ear in any inner notch. Trace the bead chains, then move to the next notch clockwise, twice.
3. Trace inside the hub, then around the outside of the hub.
4. Plate A: point the ▼ at a hub number and click both teeth in. Do positions 1-3-5-7, then 2-4-6-8.
5. Plate B, the same way. Wait about 10 minutes.
6. Dots: hub holes, F2, then plate D ×8. Big holes take the big marker, small holes the fine marker.
7. Put corner plate K1 on each corner.
8. Peel the hub off, touch up, let it cure 24 h, then spray varnish.

The full illustrated guide is in [`book/index.html`](book/index.html) (open it locally in a browser).

## Your markers are a different size?
Print the Fit Card, find your sizes, then rebuild everything:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install shapely numpy manifold3d trimesh matplotlib
python3 make_kit.py --line 2.0 --dot-s 2.4 --dot-m 3.2   # STLs + fit check
python3 guide_assets.py                                  # previews + instruction frames
```

Defaults: 1.8 mm line channel (PC-3M class), 2.2 mm small-dot hole, 3.0 mm big-dot hole (PC-5M class).

## Code
- `geom.py`: marker profile, plate settings, hub dimensions, geometry helpers
- `parts.py`: hub, inserts, wedge plates, corner plates, centre jig, fit card (2D slabs extruded with manifold3d)
- `design01.py`: the Seed Bloom design (radii, petals, rays, dot layout)
- `make_kit.py`: builds the STLs and runs the virtual fit check
- `guide_assets.py`, `render.py`: simulated paintings and step-by-step frames

## Roadmap
- **Phase 0, Calibrate:** Fit Card and your marker profile. *Done.*
- **Phase 1, Kit 01 "Seed Bloom" (20 cm):** core system and the first full kit. *Done, waiting for a test print.*
- **Phase 2, Kit 02 "Turquoise Bloom" (30 cm / 12 in):** outer plates on the same hub. *In progress.*
- **Phase 3, Library:** Seed of Life, Metatron's Cube and Sri Yantra-style inserts, plus 6-, 12- and 16-fold rings.
- **Phase 4, Kits:** numbered parts, instruction cards, wear tests, beginner testing, packaging.

Copyright © 2026 natalia-3nitilab. All rights reserved. No open-source license is granted yet.
