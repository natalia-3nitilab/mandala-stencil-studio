# Mandala Stencil Studio

3D-printed stencils for precise sacred-geometry mandalas in acrylic marker, with no compass and no pencil. Every piece locks onto one hub, does one motif, works on both faces, and draws with its edges, its openings and its grooved dot rows.

| Kit 01 "Seed Bloom", 20 cm | Kit 02 "Turquoise Bloom", 30 cm |
|---|---|
| ![Kit 01](preview/k1_turquoise.png) | ![Kit 02](preview/k2_turquoise.png) |

**Status: v3.** 37 STL files, all closed solids. **130/130 automatic checks pass.** For every piece on both faces, they cover: seated with zero overlap, a clear straight path down and up, locked against turning and sliding, walls of at least 1.6 mm, every intended line fully painted, and no dot on another element's paint. Nothing has been test-printed yet.

## How v3 works
- **Lock:** solid 90° V-teeth (1.8 mm deep, 3.6 mm wide, full height) drop into V-notches in the hub. The hub has a notch every 7.5° outside and 6 inside. There are no thin fins and no layers.
- **Both faces:** a tooth is the same top and bottom, so every piece also works flipped. Face B draws the mirror image: the other half of an arc, rays between rays, the petal on the other side of the number.
- **Lanes:** the hub's notched edges are never traced. The ring around the hub is traced in a 2.6 mm gap between the hub and the ring piece. A centre's border is traced in a 2.4 mm gap between the insert and the hub. Tabs sit at uneven angles, so face A and face B close the circle.
- **Edges and openings draw.** The Flower of Life is the classic 19 circles, every one a whole round opening.
- **Dots are a line with pockets:** through-holes linked by a 0.6 mm groove on each face. Glide the tip along the groove and press at each pocket.
- **Printing:** flat on either face, no supports. Jigs and corner pieces print lips up.

## Files (print order)

**Calibrate + system**

| File | Part | Faces |
|---|---|---|
| `stl/00_T0_fit_card.stl` | Fit Card | A |
| `stl/01_H3_hub.stl` | Hub | A |
| `stl/02_J20_jig_20cm_8in.stl` | Centre jig 20 cm / 8 in | A |
| `stl/03_J30_jig_30cm_12in.stl` | Centre jig 30 cm / 12 in | A |

**Kit 01 Seed Bloom, 20 cm**

| File | Part | Faces |
|---|---|---|
| `stl/10_FA_flower_corners.stl` | Flower of Life: outer corners | A+B |
| `stl/11_FB_flower_inner_ring.stl` | Flower of Life: inner ring | A+B |
| `stl/12_FC_flower_sides.stl` | Flower of Life: outer sides | A |
| `stl/13_FD_flower_centre_border.stl` | Flower of Life: centre + border | A+B |
| `stl/14_FE_flower_dots.stl` | Flower of Life: dots | A |
| `stl/30_R1_hub_ring.stl` | Hub ring | A+B |
| `stl/31_DM_dome.stl` | Dome | A+B |
| `stl/32_PT_petal.stl` | Petal | A+B |
| `stl/37_K1_corner_20cm.stl` | Corner web 20 cm | A |

**Kit 02 Turquoise Bloom, 30 cm (adds to Kit 01)**

| File | Part | Faces |
|---|---|---|
| `stl/40_RC_ring_c2.stl` | Ring C2 | A+B |
| `stl/41_FN_fan.stl` | Rainbow fan | A+B |
| `stl/42_GP_great_petal.stl` | Great petal | A+B |
| `stl/43_GH_petal_heart.stl` | Petal heart | A+B |
| `stl/44_ST_star_disc.stl` | Star disc | A+B |
| `stl/45_HL_halo.stl` | Halo | A+B |
| `stl/46_K2_corner_30cm.stl` | Corner fan 30 cm | A |

**Library centres**

| File | Part | Faces |
|---|---|---|
| `stl/15_B0_border_ring.stl` | Border ring | A+B |
| `stl/16_SF_sunflower.stl` | Sunflower | A |
| `stl/17_MK1_merkaba_lines.stl` | Merkaba lines | A+B |
| `stl/18_MK2_merkaba_dots.stl` | Merkaba dots | A |
| `stl/19_SE1_seed_petals.stl` | Seed of Life: petals | A+B |
| `stl/20_SE2_seed_centre_border.stl` | Seed of Life: centre + border | A+B |
| `stl/21_SE3_seed_dots.stl` | Seed of Life: dots | A |
| `stl/22_MT1_metatron_circles_a.stl` | Metatron: centre + outer circles | A+B |
| `stl/23_MT2_metatron_circles_b.stl` | Metatron: inner circles | A+B |
| `stl/24_MT3_metatron_lines_a.stl` | Metatron lines 0/60/120 | A+B |
| `stl/25_MT4_metatron_lines_b.stl` | Metatron lines 30/90/150 | A |
| `stl/26_MT5_metatron_lines_c.stl` | Metatron lines 19/41 | A+B |
| `stl/27_MT6_metatron_dots.stl` | Metatron dots | A |

**Library Lace ring set, 20 cm**

| File | Part | Faces |
|---|---|---|
| `stl/33_AR_arch.stl` | Arch | A+B |
| `stl/34_LT_lotus.stl` | Lotus petal | A+B |
| `stl/35_OR_outer_ring.stl` | Outer ring | A+B |
| `stl/36_OP_outer_petal.stl` | Outer petal | A+B |

PLA or PETG, 0.4 nozzle, 0.2 mm layers, 100% infill, no supports. Print the hub and one dome first to check the lock.

## Recipes
Choose any centre (Flower of Life, Sunflower, Merkaba, Seed of Life, Metatron's Cube) with either ring set (Bloom or Lace), plus corners. That makes 10 recipes; all are rendered in `book/img3/r_*.svg`. The project book (`book/index.html`) has a mixer to try any combination.

## Build
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install shapely numpy manifold3d trimesh matplotlib
python3 make_v3.py                                   # every STL + all checks
python3 make_v3.py --line 2.0 --dot-s 2.4 --dot-m 3.2  # your marker sizes (from the Fit Card)
python3 render_v3.py && python3 book_v3.py           # previews + project book
```

## Code
- `v3.py`: the system (hub, V-lock, lanes, grooves, reversible pieces, inserts, jigs, corner pieces)
- `v3_kit1.py`: Kit 01 designs. `v3_more.py`: Kit 02, library centres, Lace ring set
- `v3_check.py`: fit, path, wall, line and overlap checks. `make_v3.py`: builds everything
- `geom.py`, `parts.py`, `render.py`: shared geometry, text, rendering
- `archive/`: v1 plates and the v2 prototype (they don't fit the v3 hub)

## Roadmap
- Phase 0–3: calibrate, Kit 01, Kit 02 and the library are designed and generated (v3).
- Phase 4: test prints, wear tests, beginner tests, instruction cards, packaging.
- Next: Ukrainian stitching stencils, then a mandala that combines the Flower of Life with Ukrainian stitching.

Copyright © 2026 natalia-3nitilab. All rights reserved. No open-source license is granted yet.
