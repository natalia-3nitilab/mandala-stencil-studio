# Mandala Stencil Studio

3D-printed stencils for painting precise sacred-geometry mandalas with acrylic markers. No compass, no pencil drafting: every stencil clicks onto one hub at the canvas centre, so every line and every dot lands where it should.

| Kit 01 "Seed Bloom", 20 cm | Kit 02 "Turquoise Bloom", 30 cm |
|---|---|
| ![Kit 01 Seed Bloom, simulated painting](preview/P1_turquoise.png) | ![Kit 02 Turquoise Bloom, simulated painting](preview/P2_turquoise.png) |

**Status:** Phase 0 (calibration), Phase 1 (Kit 01 "Seed Bloom", 20 × 20 cm) and Phase 2 (Kit 02 "Turquoise Bloom", 30 × 30 cm) are designed and generated. All 17 STLs are checked closed solids. A virtual assembly and paint-overlap test passes 41/41. Nothing has been test-printed or painted yet. A v2 prototype (below) reworks the system after the first review.

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

## v2 prototype: reversible, one motif per piece, edges draw
After the first review the system was rethought. Prototype files are in `stl/v2/`:

| File | Part |
|------|------|
| `stl/v2/v2_01_H2_hub_reversible.stl` | Hub v2: index notches in the middle of the thickness |
| `stl/v2/v2_02_DM_dome_piece.stl` | Dome piece: edge = arc, notched edge = pearls, 8 slots → 16 rays |
| `stl/v2/v2_03_PT_petal_piece.stl` | Petal piece: edge = petal, opening = inner petal, half the pearls per face |
| `stl/v2/v2_04_F1_flower_of_life_lines.stl` | Flower of Life lines, flippable |
| `stl/v2/v2_05_F2_flower_of_life_dots.stl` | Flower of Life dots, flippable |
| `stl/v2/v2_06_SF_sunflower_core.stl` | Sunflower core: 222 dots on golden-angle spirals |

- **Locks on both faces:** teeth and notches sit in the middle band (z 0.6–1.4 mm), so a piece clicks in face A up or flipped to face B. Flipping mirrors the piece about the hub number.
- **One motif per piece**, and the **outer edge is a drawing guide**: trace around the piece.
- **Face A + face B complete each other:** half arc + half pearls per face, interleaved rays, the petal arm on opposite flanks.
- **Rule for every piece:** at each hub number, face A, flip, face B.

Fit check: `python3 v2_check.py` (36/36 pass). Previews: `python3 v2_render.py`. v1 plates do not fit the v2 hub.

![v2 prototype painting](preview/v2_painting_fol.png)

## Kit 02 "Turquoise Bloom" (30 × 30 cm / 12 × 12 in)
Reuses H1, F1, F2, A1, B1 and D1 from Kit 01 for the centre and adds:

| # | File | Part | Used |
|---|------|------|------|
| 10 | `stl/10_J30_centre_jig_30cm_12in.stl` | Centre Jig 30 cm / 12 in (202 mm, prints lips up) | once |
| 11 | `stl/11_E1_plate_E_rainbow_fans.stl` | Rainbow fans on ring C2 | 8× |
| 12 | `stl/12_D2_plate_D2_ring_border_dots.stl` | Ring C2 + fan dots + border dots | 8× |
| 13 | `stl/13_P2_plate_P2_great_petals.stl` | Great teardrop petals | positions 1 3 5 7 |
| 14 | `stl/14_P3_plate_P3_petal_dots.stl` | Petal dots + bridge dots | positions 1 3 5 7 |
| 15 | `stl/15_S1_plate_S1_star_circles.stl` | Star circles + rim dots | positions 2 4 6 8 |
| 16 | `stl/16_S2_plate_S2_echo_star_field.stl` | Echo circle + star field | positions 2 4 6 8 |
| 17 | `stl/17_K2_corner_fan_30cm.stl` | Corner fan (prints lips up) | 4 corners |

About 87 g and 6 hours of printing. Every plate fits a 180 mm bed except J30. Without J30, measure instead: the hub's outer edge sits 96 mm from each canvas edge (98 mm on 12 in).

Order: hub with J30 → Seed Bloom lines (F1, hub circles, A, B) → E1 → P2 → S1 → S2 → centre dots (hub, F2, D1) → D2 (glide ring C2 first) → P3 → K2. About 1,700 dots and 4 to 4½ hours.

## Your markers are a different size?
Print the Fit Card, find your sizes, then rebuild everything:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install shapely numpy manifold3d trimesh matplotlib
python3 make_kit.py --line 2.0 --dot-s 2.4 --dot-m 3.2   # both kits: STLs + fit and overlap check
python3 guide_assets.py                                  # previews + instruction frames
```

Defaults: 1.8 mm line channel (PC-3M class), 2.2 mm small-dot hole, 3.0 mm big-dot hole (PC-5M class).

## Code
- `geom.py`: marker profile, plate settings, hub dimensions, geometry helpers
- `parts.py`: hub, inserts, wedge plates, corner plates, centre jig, fit card (2D slabs extruded with manifold3d)
- `design01.py`: the Seed Bloom design (radii, petals, rays, dot layout)
- `design02.py`: the Turquoise Bloom outer ring (fans, great petals, star circles, corners)
- `make_kit.py`: builds the STLs and runs the virtual fit check and the paint-overlap check
- `guide_assets.py`, `render.py`: simulated paintings and step-by-step frames

## Roadmap
- **Phase 0, Calibrate:** Fit Card and your marker profile. *Done.*
- **Phase 1, Kit 01 "Seed Bloom" (20 cm):** core system and the first full kit. *Done, waiting for a test print.*
- **Phase 2, Kit 02 "Turquoise Bloom" (30 cm / 12 in):** outer plates on the same hub. *Done, waiting for a test print.*
- **Phase 3, Library:** Seed of Life, Metatron's Cube and Sri Yantra-style inserts, plus 6-, 12- and 16-fold rings.
- **Phase 4, Kits:** numbered parts, instruction cards, wear tests, beginner testing, packaging.

Copyright © 2026 natalia-3nitilab. All rights reserved. No open-source license is granted yet.
