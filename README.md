# ikegam1 3D print data

3D printing files and drawings (STL / STEP / PNG / CAD source), primarily designed for **Flashforge Adventurer 5M**.

## Projects and versions

| Project | Directory | Status |
|---|---|---|
| Live stream tray | [livestream-tray/center-and-side-trays/v0.9/](livestream-tray/center-and-side-trays/v0.9/) | Prototype: PETG fit and load unverified |
| arrows alpha phone holder | [livestream-tray/phone-holder/v0.4.1-reinforced/](livestream-tray/phone-holder/v0.4.1-reinforced/) | Reinforced prototype, 71.6 mm slot; confirm actual fit |
| Drink holder | [livestream-tray/drink-holder/v1.3-backshift-half-under-table/](livestream-tray/drink-holder/v1.3-backshift-half-under-table/) | **Newest v1.3:** cup shifted approximately half under the table; 500 mL bottle CAD clearance checked. PETG load-bearing and stability **not physically validated** |
| Indoor Kubb | [kubb/70x70x150-closed-light/](kubb/70x70x150-closed-light/) | Closed 70×70×150 mm model with low slicer infill |
| PETG slippers | [footwear/petg-slippers-27cm/](footwear/petg-slippers-27cm/) | Early prototype, requires compatible hardware; PETG can be hard and slippery |
| Mölkky trophy (おおみそCUP) | [molkky_trophy/](molkky_trophy/) | Print data for 4 trophies (2026-10-27) plus a 1/3-scale fit test; not yet test-printed |
| Mölkkaari | [molkkaari/](molkkaari/) | Body, 3.5 m measuring rule prototypes, angle covers for wooden frames, legacy center extension adapters; STL, design sources, assembly images and instructions. Prototypes |
| 3.5 m measuring rule (new joint system) | [measure-3p5m/](measure-3p5m/) | Prototype record (v13 etc.); **under physical testing, not a finished design** |

**Previous drink holder versions:** [v1.1-inward-tilt](livestream-tray/drink-holder/v1.1-inward-tilt/); retained for reference, v1.3 is current.\n\n**Former designs:** [archive/older-unverified-revisions/](archive/older-unverified-revisions/) — retained for comparison only; several are superseded due to fit, stability, or strength problems.

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

- [**3.5m測定具 v14：18節一体型・直線位置ロック（設計・印刷設定）**](measure-3p5m/TPU95A_v14_onepiece_straightlock/README.md) — TPU95A／0.8mmノズル。フルサイズのCADデータは作成済みですが、嵌合・3.5m精度・収納は実機未検証。

- [**3.5m測定具 v15：真の鎖式連結（試験モデル）**](measure-3p5m/TPU95A_v15_free_chain/REQUIREMENTS.md) — 閉環が立体的に絡む方式。2節・3節のCAD試験完了、**3.5m完成版と実機印刷は未完了**。v14の直線ロック方式は採用見送り。

- [**測定具 v15.1：鎖ジョイントのサポート除去改善（2リンク試験）**](measure-3p5m/TPU95A_v15_easy_release_test/README.md) — 自動サポートOFF・外付けの切除柱式。実機での成功は未確認。

- [**測定具 v16：鎖式26節・根元リング／先端錨（CAD候補と印刷設定）**](measure-3p5m/TPU95A_v16_chain_ring_anchor/README.md) — STL生成済み、3.5m校正・収納・可動性は未検証。2節試験から。

- [**測定具 v17：PETG／0.8mm・根元の四角リング（内寸24×39mm）＋鎖式**](measure-3p5m/PETG_v17_square_root_chain/README.md) — 試験用STL・26節CADモデル作成。3.5m実測とサポート除去は未検証。

- [**測定具 v18：PETG・0.4mm／八角形の鎖ジョイント試験**](measure-3p5m/PETG_v18_faceted_chain_test/README.md) — 2節のSTLを作成。支柱の除去・可動性は実機未検証。

- [**測定具 v19：PETG・0.4mm／成功した八角形ジョイントで26節の本体**](measure-3p5m/PETG_v19_faceted_full/README.md) — 根元24×39mm角リング＋錨。STL生成・形状検証済み、実際の3.5m長さは未校正。

- [**測定具 v20：PETG・0.4mm／首折れ対策の幅広補強（実寸2節から試験）**](measure-3p5m/PETG_v20_reinforced_necks/README.md) — v19の破断写真を受けて再設計。2節・3節試験STLと26節候補を作成。**耐久性は実機未確認。**

- [**測定具 v21：PETG・0.4mm／さらに太いジョイント＋中央へ向かって薄くなる板**](measure-3p5m/PETG_v21_reinforced_graded_flex/README.md) — 端2.8mm／中央1.5mm、実寸2節試験から。26節の強度と3.5m精度は未検証。

- [**測定具 v22：三角穴を板端に一体化した鎖式連結（CAD検討用・印刷非推奨）**](measure-3p5m/PETG_v22_integrated_triangle_eyes_CONCEPT/README.md) — 45°／90°の2枚の立体連結を確認。強度・サポート・3.5m配置は未検証。

- [**測定具 v22.1：上面視90°で2枚を配置し、三角穴で一体連結する修正版CAD**](measure-3p5m/PETG_v22_1_planview_90deg_triangle_eyes/README.md) — 旧v22の角度解釈を訂正。2枚の幾何検証済み、**サポート未完成・印刷非推奨**。

- [**測定具 v22.2：薄い平板に直接三角穴・穴の周囲のみ補強（CAD検討版）**](measure-3p5m/PETG_v22_2_flat_plate_triangle_holes/README.md) — 90°はベッド上の板同士の配置角。2枚の立体連結はCAD確認済み、サポート未設計のため印刷非推奨。

- [**測定具 v22.3：薄板の三角穴＋内蔵サポート20か所（PETG／0.4mm・2枚試験）**](measure-3p5m/PETG_v22_3_flat_triangle_supports_built_in/README.md) — スライサーのサポートOFFでテストできる構成。支柱除去は実機未検証。
