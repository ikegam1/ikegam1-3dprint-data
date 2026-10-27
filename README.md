# ikegam1 3D print data

3D printing files and drawings (STL / STEP / PNG / CAD source), primarily designed for **Flashforge Adventurer 5M**.

## Projects and versions

| Project | Directory | Status |
|---|---|---|
| Live stream tray | [livestream-tray/center-and-side-trays/v0.9/](livestream-tray/center-and-side-trays/v0.9/) | Prototype: PETG fit and load unverified |
| arrows alpha phone holder | [livestream-tray/phone-holder/v0.4.1-reinforced/](livestream-tray/phone-holder/v0.4.1-reinforced/) | Reinforced prototype, 71.6 mm slot; confirm actual fit |
| Drink holder | [livestream-tray/drink-holder/v1.1-inward-tilt/](livestream-tray/drink-holder/v1.1-inward-tilt/) | Prototype, inward 6.5° tilt, 500 mL bottle intended, **load test not yet passed** |
| Indoor Kubb | [kubb/70x70x150-closed-light/](kubb/70x70x150-closed-light/) | Closed 70×70×150 mm model with low slicer infill |
| PETG slippers | [footwear/petg-slippers-27cm/](footwear/petg-slippers-27cm/) | Early prototype, requires compatible hardware; PETG can be hard and slippery |
| Mölkky trophy (おおみそCUP) | [molkky_trophy/](molkky_trophy/) | Print data for 4 trophies (2026-10-27) plus a 1/3-scale fit test; not yet test-printed |
| Mölkkaari | [molkkaari/](molkkaari/) | Body, 3.5 m measuring rule prototypes, angle covers for wooden frames, legacy center extension adapters; STL, design sources, assembly images and instructions. Prototypes |
| 3.5 m measuring rule (new joint system) | [measure-3p5m/](measure-3p5m/) | Prototype record (v13 etc.); **under physical testing, not a finished design** |

**Former designs:** [archive/older-unverified-revisions/](archive/older-unverified-revisions/) — retained for comparison only; several are superseded due to fit, stability, or strength problems.

## Important printing notes

- **Files here are experimental designs, not mechanically certified parts.** Verify slicer preview, dimensions, joining methods, print orientation, and real-world strength.
- For the tripod **drink holder**, never assume a 500 mL filled bottle is safe solely from CAD fitting. Attachment may slide off without a positive lock; confirm stability and load capacity before use.
- The phone holder and main tray were revised repeatedly, so use matching version directories. Do not mix earlier v0.7/v0.8 table connectors into v0.9.
- Some legacy slipper designs **require M3 screws**; do not interpret them as screw-free.
- Drawings in current-version folders are CAD/STL-based visualizations, not AI-generated guaranteed print results.
- The rotating joints of the measuring rule broke or failed to connect in earlier versions. Print a short test piece first.
- The Adventurer 5M build volume is 220 × 220 × 220 mm; check orientation, supports and size in the slicer.

## Mölkkaari / 3.5 m measuring rule: print settings (TPU95A)

- [Mölkkaari v3.0 recommended settings](molkkaari/TPU95A_v3_4parts/PRINT_SETTINGS.md) — 4 parts with integrated joints, 0.4 mm nozzle; fit not yet verified on a real print.
- [3.5 m measuring rule v13 test settings](measure-3p5m/TPU95A_v13_print_in_place_test/PRINT_SETTINGS.md) — 0.8 mm nozzle, **2- and 3-segment test only**; not the finished 3.5 m rule.
- [Avoiding mid-print TPU95A jams](docs/TPU95A_STABLE_PRINTING_AD5M.md) — for the Adventurer 5M.
- [Measuring rule v9–v12: known problems](measure-3p5m/previous-prototypes/PRINT_SETTINGS.md) — older versions are not recommended for production prints.

**These designs are prototypes.** Mölkkaari joint strength and the measuring rule's straightness, 3,500 mm accuracy and storage need to be checked on real prints.

Created from prior ChatGPT design artifacts and uploaded to GitHub on 2026-10-27.
