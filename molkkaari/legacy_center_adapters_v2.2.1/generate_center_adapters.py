"""v2.2.1 center extension adapters, compatible with 02_center_left male and 04_center_right female.
Print only one length. Geometry intentionally copies exact mating feature dimensions from generate_v22.py.
"""
from pathlib import Path
import math, zipfile, json, shutil
import cadquery as cq
import trimesh
from cadquery import exporters
from shapely.geometry import LineString
from shapely.geometry.polygon import orient

OUT=Path('/mnt/data/molkkaari_v2_2_1_center_adapters')
OUT.mkdir(exist_ok=True)
STLS=OUT/'STL_この中から1個だけ印刷'; STLS.mkdir(exist_ok=True)
ED=OUT/'CAD_STEP_編集用'; ED.mkdir(exist_ok=True)
LENGTHS=(40,60,80,100)
W=18.0; H=33.0; TOP=27.0
TONGUE_END=22.0; RECEIVER_END=24.5
HOLE_CENTERS=(6.4,16.9); PIN_LEN=4.5; HOLE_LEN=5.2
PIN_BOT=19.85; HOLE_FLOOR=19.2
DATA=[]

def b(x,y,z,cx,cy,cz): return cq.Workplane('XY').box(x,y,z).translate((cx,cy,cz)).val()
def poly(points,z0,ht): return cq.Workplane('XY').polyline(points).close().extrude(ht).translate((0,0,z0)).val()

def make_bar(L):
    # middle/straight v2.2.1 bar: same end geometries as original 03_center_middle.
    base=b(L,W,H,L/2,0,H/2)
    # female receiver: same precise rectangular trench cut and two rectangular sockets
    top_cut=b(38.5,W+10,H-TOP+1.5,(RECEIVER_END-14)/2,0,(H+TOP)/2+.75)
    base=base.cut(top_cut)
    for xpos in HOLE_CENTERS:
        hole=b(HOLE_LEN,13.2,TOP-HOLE_FLOOR+0.03,xpos,0,(TOP+HOLE_FLOOR)/2+0.015)
        base=base.cut(hole)
    # male flange from original: flattened LineString 18mm wide and 22mm long
    outer=list(orient(LineString([(L-12,0),(L,0),(L+TONGUE_END,0)]).buffer(W/2,cap_style=2,join_style=2,resolution=8),sign=1).exterior.coords)[:-1]
    flange=poly(outer,TOP,H-TOP)
    for t in HOLE_CENTERS:
        corners=[(L+t+u,v) for u,v in [(-PIN_LEN/2,-6.3),(PIN_LEN/2,-6.3),(PIN_LEN/2,6.3),(-PIN_LEN/2,6.3)]]
        flange=flange.fuse(poly(corners,PIN_BOT,TOP-PIN_BOT))
    base=base.fuse(flange).clean()
    # hollow ground-facing cavity on longer spacers; short 40mm piece stays solid for strength
    if L>=60:
        xa=31.5; xb=L-19.5
        if xb>xa+5:
            # match v2.2.1 dimensions: 13.7mm internal width and 2.2mm roof
            cut=b(xb-xa,13.7,31.0,(xa+xb)/2,0,15.3)
            base=base.cut(cut).clean()
    return base

def orient_print(s):
    # roof down, open cavity up, same as v2.2.1 body; no unsupported long roof spans
    s=s.rotate((0,0,0),(1,0,0),180)
    # leave bar horizontal aligned X for straightforward placement (rather than diagonally on bed)
    bb=s.BoundingBox()
    return s.translate((110-(bb.xmin+bb.xmax)/2,110-(bb.ymin+bb.ymax)/2,-bb.zmin))

for L in LENGTHS:
    cad=make_bar(L)
    shape=orient_print(cad)
    nm=f'CENTER_JOIN_v221_{L}mm_PRINT_ONE.stl'
    path=STLS/nm
    exporters.export(shape,str(path),exportType='STL',tolerance=0.045,angularTolerance=0.2)
    exporters.export(cad,str(ED/f'CENTER_JOIN_v221_{L}mm.step'),exportType='STEP')
    m=trimesh.load(path,force='mesh')
    bb=m.bounds
    assert m.is_watertight and m.volume>0
    assert bb.min()>=-1e-4 and all(bb[1]<220.001),bb
    d={'adapter_length_mm':L,'total_expected_path_mm':920+L,'mesh_watertight':bool(m.is_watertight),'print_extents_xyz_mm':[round(float(z),2) for z in m.extents],'watertight_components':len(m.split()),'volume_mm3':round(float(m.volume))}
    DATA.append(d)

(OUT/'geometry_check.json').write_text(json.dumps(DATA,indent=2,ensure_ascii=False),encoding='utf-8')
readme=f'''# v2.2.1 本体4本用 中央延長ジョイント（PETG／AD5M）

これは **v2.2.1で印刷した 01_left_wing・02_center_left・04_center_right・05_right_wing の4本** を活用するための、中央の直線延長ジョイントです。v2.3用ではありません。ほかの本体の再印刷は不要です。

## 印刷するもの

`STL_この中から1個だけ印刷` 内のSTLを、**長さを選んで1個だけ** 印刷してください。

| 選択するSTL | 延長量（設計上） | 4本の合計長さ（板に沿った経路長） |
|---|---:|---:|
| CENTER_JOIN_v221_40mm_PRINT_ONE.stl | 40mm | 約960mm |
| CENTER_JOIN_v221_60mm_PRINT_ONE.stl | 60mm | 約980mm |
| **CENTER_JOIN_v221_80mm_PRINT_ONE.stl** | **80mm** | **約1000mm** |
| CENTER_JOIN_v221_100mm_PRINT_ONE.stl | 100mm | 約1020mm |

寸法基準は印刷済み4本が1本230mmという元のCAD設計値（合計920mm）です。実際の完成寸法には印刷収縮・合わせ面の隙間などの差が生じます。写真のみでは必要な延長量は厳密に決定できないため、**純正と並べた際に足りない距離を測って選ぶ**のが確実です。最初の候補は80mmです。

## 取り付け位置

`01 左端 → 02 中央左 → （中央延長ジョイント） → 04 中央右 → 05 右端`

既存の02の2本の凸ピンを、延長ジョイントの受け穴に差し込みます。延長ジョイントの反対側の2本の凸ピンを04の受け穴に差し込みます。180度に直線固定されます。

## 印刷方向（STLで設定済み）

平らで広い面がプレート接地、**空洞が上向き**です。STLを「床面に配置」や「自動面合わせ」で向き変更しないでください。長さ40〜100mm＋凸部22mmの短いパーツなので、Adventurer 5M（220×220×220mm）に余裕で収まります。

PETG・0.4mmノズル・積層0.2mm・ノズル240℃前後・ベッド80℃前後・外壁4周・初層20mm/s程度を初期値にしてください。**サポートON（ビルドプレートのみ）**にし、**受け側の段差の下へサポートが生成されているか**スライス後のプレビューで確認してください。過去に失敗した接続部なので、サポートの指定漏れに注意。

## 嵌合・安全

- 穴とピンの寸法はv2.2.1のCADと同じ（ピン長4.5mm、受け穴長5.2mm）。
- このパーツを作っただけで嵌合が保証されるわけではありません。過去印刷済み部材のサポート跡・PETG収縮・バリを確認してください。
- 強く押し込まず、まず手でゆっくり合わせてください。ピンが入らないときは角穴に残ったサポート材を除去します。
- 40mm版は狭い範囲に両ジョイントを持つので中央部を中空にせず、強度を優先しています。
- **印刷済み4本のうち #03 の「中央中間」を使っている場合、組み合わせが異なる可能性があります。**

本体の側面文字や3.5m測定具には変更を加えていません。STL/STEPの形状とプリント範囲はプログラムで検証済み、実機での嵌合・耐久性は未検証です。
'''
(OUT/'README_印刷と取付方法.md').write_text(readme,encoding='utf-8')
shutil.copy('/mnt/data/build_v221_center_adapters.py',OUT/'generate_center_adapters.py')
Z='/mnt/data/molkkaari_v2_2_1_center_joint_only.zip'
with zipfile.ZipFile(Z,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for f in OUT.rglob('*'):
        if f.is_file():z.write(f,arcname=f.relative_to(OUT))
print('ZIP:',Z)
for d in DATA:print(d)
