"""Arrows Alpha Live Tray v0.9: compatibility fix for printed FULL v0.3/v0.4 phone holder.
Assumes base plate 110x114x6.4 mm (not the 96x65mm short test slice).
New 136mm center width to accommodate accessible side loading rails; shift v0.8.1 side trays
outward by 13mm each. Keep underside 70x52x12mm clamp body and 3mm/5mm relief.
No bolts, nuts or standalone small test items. PETG, Adventurer 5M.
"""
from pathlib import Path
import math,shutil,json,zipfile
import cadquery as cq
import numpy as np
import trimesh
from cadquery import exporters
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path('/mnt/data/ArrowsAlpha_LiveTray_v09_FULL_110x114_phone_mount')
STL=ROOT/'01_STL_印刷用';STEP=ROOT/'02_STEP_編集用';IMG=ROOT/'03_寸法図'
for d in [ROOT,STL,STEP,IMG]:d.mkdir(exist_ok=True,parents=True)
W=136.0; DEP=162.0; base_z=9.0; slab_top=15.0
phone_w=110.;phone_d=114.;phone_t=6.4
phone_y=6.0
metadata=[]
def box(w,d,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,d,h).translate((x,y,z)).val()
def add(s,t):return s.fuse(t)
def export(s,path):
    exporters.export(s,str(STEP/(path+'.step')),exportType='STEP')
    b=s.BoundingBox(); t=s.translate((110-(b.xmin+b.xmax)/2,110-(b.ymin+b.ymax)/2,-b.zmin))
    exporters.export(t,str(STL/(path+'.stl')),exportType='STL',tolerance=.06,angularTolerance=.22)
    m=trimesh.load(str(STL/(path+'.stl')),force='mesh')
    n=len(m.split(only_watertight=False))
    datum={'filename':path+'.stl','bbox_mm':[round(float(a),2) for a in m.extents], 'watertight':bool(m.is_watertight),'connected_components':n,'volume_mm3':round(float(m.volume),1),'fits_220':bool(np.all(m.extents<=220.001))}
    metadata.append(datum)
    if not m.is_watertight or n!=1 or m.volume<0 or not datum['fits_220']: raise RuntimeError(datum)
    print('ok',datum)
    return s

# Central plate and unchanged tested 70mm lower grip geometry.
center=box(W,DEP,6,0,0,12)
blade=box(70,52,12,0,0,3)
try:blade=cq.Workplane(obj=blade).edges('|Z').fillet(1.2).val()
except Exception: pass
center=add(center,blade)
# Relief exactly preserves v0.8 shape: near deck 5mm height, 3mm cut from each side.
for side in (-1,1):center=center.cut(box(4.2,53,5,side*34.1,0,6.5))

# Functional T rails: v0.8 rail features translated 13mm outward on each side, to match new seam x=68.
for side in (-1,1):
    stem=box(6.5,135,4.8,side*70.0,2,11.3)
    head=box(9.0,135,3.2,side*73.0,2,14.0)
    center=add(center,stem)
    center=add(center,head)

# Full-sized printed phone unit (older actual 110x114x6.4mm main base).
# The L rail only captures outermost sides, leaving the phone holder side towers (x +-42) completely clear.
# Original printed phone part enters from back (+Y), to a shallow front stop.
for side in (-1,1):
    # Side wall outside the old phone base: inner surface x +/-55.55, 0.55mm per side clearance.
    wall=box(3.2,116,9.4,side*57.15,phone_y,19.7) # x inner=55.55; z15..24.4
    center=add(center,wall)
    # Lip engages ~2.25mm of the top of the base plate. Clearance above 6.4mm plate = .55mm.
    # Upper lips extend slightly into the vertical sidewall for a fully connected continuous solid.
    lip=box(2.75,105,2.4,side*54.70,phone_y-2.0,23.15) # z21.95..24.35; x from53.325..56.075
    center=add(center,lip)
# Only a front fence; open at the back for insertion; prevent motion towards user (-Y).
# Final seated phone plate bounds y=-51..+63, front stop back-facing surface at y=-52.3.
stop=box(114,3.4,6.5,0,-54.0,18.25) # y -55.7 to -52.3; z 15..21.5
center=add(center,stop)
center=center.clean()
export(center,'01_CENTER_V09_70mm_GRIP_110x114_PHONE_DOCK')

# Import validated v0.8.1 side-table model. Shape itself unchanged, position moved by +-13mm.
zpath=Path('/mnt/data/v081_stepextract')
side_shapes={}
for side,nm in [(-1,'LEFT'),(1,'RIGHT')]:
    old=cq.importers.importStep(str(zpath/f'02_{nm}_TABLE_V081_REAR_ENTRY.step')).val()
    new=old.translate(cq.Vector(side*13,0,0)).clean()
    side_shapes[nm]=new
    export(new,f'02_{nm}_TABLE_V09_REAR_ENTRY')

# Keep cup bracket shape of v0.8, which geometrically engages the unchanged slab z9..15 at center front y=-81.
with zipfile.ZipFile('/mnt/data/ArrowsAlpha_LiveTray_v081_center_compatible_checked.zip') as z:
    cup_file=ROOT/'cup_old.step'
    cup_file.write_bytes(z.read('STEP/03_CUP.step'))
cup=cq.importers.importStep(str(cup_file)).val()
export(cup,'03_CUP_V09_SHAPE_UNCHANGED_EMPTY_ONLY')
cup_file.unlink()

# Source main v0.3/v0.4 FULL phone holder for precise assembly checks.
with zipfile.ZipFile('/mnt/data/ArrowsAlpha_LiveTray_v04_phone_backwall_PETG.zip') as z:
    f=ROOT/'phone_old.step'
    f.write_bytes(z.read('03_STEP_SOURCE/CENTRAL_TRAY_PHONE_GUIDES.step'))
phone=cq.importers.importStep(str(f)).val()
f.unlink()
assert round(phone.BoundingBox().xlen,3)==110
assert round(phone.BoundingBox().ylen,3)==114
assert abs(phone.BoundingBox().zlen-71.4)<.01
# Approximate actual loaded state: bottom of printed base rests on z15, x centered, y shifted 6.
# Phone from CAD v04 has bottom z=0 and 65mm guides in z=6.4..71.4.
PHONE_FINAL=phone.translate(cq.Vector(0,phone_y,15.0))
# CAD volumetric collisions at fully seated position + simulated motion into from back +Y.
position_check=[]
for mm in [0,1,5,10,20,30,40,50,60,80,100,120,140,160,180]:
    placed=PHONE_FINAL.translate(cq.Vector(0,mm,0))
    overlap=center.intersect(placed).Volume()
    position_check.append({'from_final_rearward_mm':mm,'intersection_volume_mm3':round(float(overlap),6)})
    if overlap>0.2:raise RuntimeError('PHONE COLLISION '+str(position_check[-1]))
print('phone slide',position_check)

# Verify v0.9 left and right side trays do not collide when assembled with center; check multiple slide positions.
side_tests={}
for side,nm in [(-1,'LEFT'),(1,'RIGHT')]:
    tab=side_shapes[nm]
    info=[]
    for dy in [-160,-140,-100,-80,-60,-40,-20,-10,-5,-2,0]:
        # Side tray insertion from front -> slides to back, final at y=0, during insertion is y<0.
        shifted=tab.translate(cq.Vector(0,dy,0))
        v=center.intersect(shifted).Volume()
        info.append([dy,round(float(v),6)])
        if v>0.2:raise RuntimeError('SIDE COLLISION '+nm+' '+str(info[-1]))
    side_tests[nm]=info
print('side tests',side_tests)
# Loaded phone and side tray should also not collide
for nm,tab in side_shapes.items():
    v=PHONE_FINAL.intersect(tab).Volume()
    if v>0.2:raise RuntimeError('PHONE VS SIDE '+nm+' '+str(v))

# Source v0.8 grip exact solid profile verified by bounding and mesh difference in grip zone
source=cq.importers.importStep(str(zpath/'01_CENTER_V08.step')).val()
region=box(100,80,26,0,0,0) # cuts up through z13: only grip underneath and central slab bottom.
# Test exact z<=9 to avoid slab width different after widening
region=box(100,80,13,0,0,2.5) # z -4..9
oldgrip=source.intersect(region).clean();newgrip=center.intersect(region).clean()
vold=oldgrip.Volume();vnew=newgrip.Volume();vcommon=oldgrip.intersect(newgrip).Volume()
grip_delta=round(float(vold+vnew-2*vcommon),8)
if grip_delta>0.005:raise RuntimeError('70mm GRIP ALTERED '+str(grip_delta))

# Fit verification for phone plate within dock; genuine geometric boundaries
bounds={'phone_plate_x_mm':110,'phone_plate_y_mm':114,'phone_plate_thickness_mm':6.4,
'dock_side_inner_clear_mm':111.1,'dock_side_clearance_each_mm':0.55,
'dock_lip_bottom_z_mm':21.95,'phone_plate_top_z_mm':21.4,'dock_vertical_clearance_mm':0.55,
'dock_entry_direction':'rear (+Y) toward front (-Y)','grip_profile_difference_mm3':grip_delta,
'center_width_mm':W,'assembled_total_width_mm':W+2*115,'side_module_offset_vs_v081_mm':13,
'clamp_jaw_width_mm':70,'clamp_root_relief_5mm_by_3mm':'unchanged',
'phone_sides_65mm':'keep printed, no reprint',
'phone_base_center_full':'110 x 114mm previously printed v0.3/v0.4',
'cup_load':'not validated; do not use with a filled drink'}

# Top down plan and side clip schematic, no photos/graphics fakes
plt.rcParams['font.family']='DejaVu Sans'
fig,axs=plt.subplots(2,1,figsize=(13,10),gridspec_kw={'height_ratios':[1.2,1]})
ax=axs[0]
for x,w,color,name in [(-125.5,115,'#cfdde1','LEFT'),(0,136,'#e2e8ed','CENTER'),(125.5,115,'#cfdde1','RIGHT')]:
    ax.add_patch(Rectangle((x-w/2,-81),w,162,facecolor=color,edgecolor='#384b54',linewidth=1.7))
    ax.text(x,2,name,ha='center',va='center',fontsize=12)
ax.add_patch(Rectangle((-55,phone_y-57),110,114,fill=False,ec='#2172a4',lw=2.5))
for side in (-1,1):
    x=side*57.15
    ax.add_patch(Rectangle((x-1.6,phone_y-58),3.2,116,fc='#2172a4',ec='#20506d'))
ax.text(0,27,'110 x 114 mm printed holder base',ha='center',color='#175c80',fontsize=10)
ax.add_patch(Rectangle((-35,-26),70,52,fill=False,ec='#bf7e2e',lw=2.5))
ax.set_aspect('equal');ax.axis('off');ax.set_xlim(-196,196);ax.set_ylim(-96,96)
ax.set_title('v0.9  |  assembly top view  |  366 mm overall width',fontsize=15)
ax=axs[1]
ax.add_patch(Rectangle((-68,9),136,6,fc='#d4dce0',ec='#384b54',lw=1.7))
ax.add_patch(Rectangle((-35,-3),70,12,fc='#e5c9a2',ec='#816237',lw=1.5))
ax.add_patch(Rectangle((-55,15),110,6.4,fc='#96c7dc',ec='#2172a4',lw=1.8))
for x in [-57.15,57.15]:
    ax.add_patch(Rectangle((x-1.6,15),3.2,9.4,fc='#2172a4'))
for x in [-54.70,54.70]:ax.add_patch(Rectangle((x-1.375,21.95),2.75,2.4,fc='#2172a4'))
ax.set_xlim(-90,90);ax.set_ylim(-8,30);ax.set_aspect('equal');ax.axis('off')
ax.text(0,26,'Cross-section (front view): printed phone plate is captured by both L-lips',ha='center',fontsize=10)
fig.tight_layout()
fig.savefig(IMG/'01_V09_HOLDER_FIT_AND_TOPVIEW.png',dpi=165,bbox_inches='tight');plt.close(fig)

report={'basis':'physical photos of printed tall 65mm phone holder and v0.3/v0.4 full-size CAD geometry, not short test plate',
'files':metadata,'phone_sliding_cad_collision_test':position_check,
'side_sliding_cad_collision_test':side_tests,'verified_dimensions':bounds,
'limitations':['Visual identification from photos assumed original 110x114mm full phone holder base: confirm with ruler before reprinting.',
'Geometric CAD fit does not guarantee PETG slide-fit tolerance or snap strength.',
'The phone unit can slide out backward if tilted: currently no positive retention latch.',
'All solids are watertight and single mesh; printability requires slicer-preview support settings.',
'Loaded drink can tip the tripod; no liquid use or load rating established.']}
(ROOT/'dimensional_compatibility_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(__file__,ROOT/'generate_v09.py')
readme='''# ライブ配信用トレー v0.9 — 印刷済みのarrows alpha保持部に適合するための改修

## 今回見つかった問題
v0.8 / v0.8.1は「幅96mm × 奥行65mm の短い試験片」を上面に取り付ける前提でした。
実際に印刷された写真の65mm高ガイド+背面壁付きスマホ保持部は、v0.3/v0.4の実物CADに一致しており、**底板110mm×114mm、厚さ6.4mm**のタイプです。そのためv0.8はそのまま使えません。

## 今回の修正
1. 中央天板を136mm幅に変更（旧110mm）。背面からスライドする**110×114×6.4mm保持部専用の差し込みドック**。左右に0.55mmずつ、上面にも0.55mm余裕を設計。
2. 持ち上がりを抑える左右のL字押さえ（各約2mm掛かり）。前面側に位置決めストッパー。印刷済みarrows alpha保持部は**変更・再印刷不要**。
3. 三脚ホルダー側で実物フィットした**70mm幅・12mm厚・テーブル寄りの5mm×左右3mm逃げ溝**はv0.8から変更せず。（CADで一致を検証）
4. 左右テーブルは、v0.8.1の試験済みの雌型溝は一切変更せず、位置だけ外側へ各13mm移動。90×140mmのテンキーが収まる内側面積を維持。
5. ドリンクホルダーは旧v0.8と同じ形状のまま収録。**飲み物入りでの使用は安全性未検証につき禁止**。

## STL印刷部品
- `01_STL_印刷用/01_CENTER_V09_70mm_GRIP_110x114_PHONE_DOCK.stl` — 中央テーブル（新規に印刷）
- `01_STL_印刷用/02_RIGHT_TABLE_V09_REAR_ENTRY.stl` — 右テーブル（新規に印刷）
- `01_STL_印刷用/02_LEFT_TABLE_V09_REAR_ENTRY.stl` — 左テーブル（新規に印刷）
- `01_STL_印刷用/03_CUP_V09_SHAPE_UNCHANGED_EMPTY_ONLY.stl` — ドリンクホルダー（旧形状。荷重不可）

印刷済みのスマホ保持部と、すでにホルダーに挟めた70mm固定プレートの小試験片は再印刷不要です。ただし本番では70mm固定部は中央テーブルと一体です。

## 印刷・組み立て
- 中央トレーを最初に印刷する。底面には70mmホルダー差し込みブレードが一体になっており、その周囲の天板が浮いているので**ビルドプレートからのサポートをON**にする。サポートが長い側面レールとL字キャプチャまで付着して取れない箇所がないかスライスプレビューで確認。
- 印刷済みスマホ保持部を、中央テーブルの**奥側（+Y）から手前に**平行にスライドさせ、短い前方ストッパーに当たるまで挿入する。ぐっと押し込んだり、立てたまま無理に縦にはめない。
- 左右テーブルは中央のT字レールへ、v0.8.1と同じ**奥側の開口から**スライドして接続。スライドに抵抗が強い場合は中断し、サポートやバリを確認する。
- ネジ、ナット、独立ジョイントは不要。ただし**中央スマホ保持部と左右テーブルに積極的な脱落防止ロックはありません**。傾けるとずり抜ける可能性があります。
- PETG／0.4mmノズル／0.20mm積層／外壁3-4周／ノズル235-245℃・ベッド75-85℃（フィラメントメーカー優先）。インフィル密度10-15%程度から見積もり、スライサー表示の必要フィラメント量に**余裕のある残量**を用意する。

## 印刷前に確認してほしい寸法（たった1か所）
印刷済みスマホ保持部の**底板の横幅が約110mm、奥行が約114mm**か、定規で確認してください。もし違えば、中央テーブルを印刷せず寸法を教えてください。写真からの機種識別なので、この確認が最後の確証です。

## 免責
実機嵌合・耐荷重・PETGの反り・長期使用強度は未検証です。CAD上で干渉ゼロを確認しましたが、スライサーによるサポート必要箇所、積層強度は別のチェックが必要です。転倒を防ぐため、三脚は床面で十分に脚を広げ、平らな場所で空の部品から組み立ててください。
'''
(ROOT/'README_v09_印刷順と注意.md').write_text(readme,encoding='utf-8')
ZIP='/mnt/data/ArrowsAlpha_LiveTray_v09_printed_phone_holder_compatible.zip'
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
    for f in ROOT.rglob('*'):
        if f.is_file():z.write(f,arcname=f.relative_to(ROOT))
print('SUCCESS',ZIP)
