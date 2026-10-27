"""Revised standalone arrows alpha holder, built from uploaded original v0.4 CAD.
Preserves v0.4 bottom 110 x 114 x 6.4, hole pattern and v0.9 dock interface.
"""
from pathlib import Path
import cadquery as cq
from cadquery import exporters
import trimesh
import json, zipfile, shutil
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

DIR=Path('/mnt/data/ArrowsAlpha_Holder_v041_Strengthened_71p6mm')
(DIR/'STL').mkdir(parents=True,exist_ok=True)
(DIR/'STEP').mkdir(exist_ok=True)
(DIR/'DRAWING').mkdir(exist_ok=True)

B=110.0; D=114.0; FLOOR=6.4
OLD_W=72.6; NEW_W=71.6
GUIDE_HEIGHT=65.0; GUIDE_W=8.0; PHONE_SLOT_D=18.; GUIDE_Y=3.; RECESS=1.5
WALL_H=48.; WALL_T=3.6

def box(w,d,h,x=0,y=0,z=0):
 return cq.Workplane('XY').box(w,d,h).translate((x,y,z)).val()

def vertical_fillet(s,r):
 try:return cq.Workplane(obj=s).edges('|Z').fillet(r).val()
 except Exception as e:
  print('Skipped fillet:',e);return s

def hole(s,x,y,z1,z2,r):
 cylinder=cq.Solid.makeCylinder(r,z2-z1,cq.Vector(x,y,z1),cq.Vector(0,0,1))
 return s.cut(cylinder)

# Exact v0.4 base with identical fasteners, tray dock interface.
base=vertical_fillet(box(B,D,FLOOR,0,0,FLOOR/2),2.)
for x in (-23.,23.):
 for y in (-16.,16.):
  base=hole(base,x,y,-0.1,FLOOR+0.1,2.2)
  base=hole(base,x,y,FLOOR-1.6,FLOOR+0.1,3.65)
for x in (-35.,35.):
 for y in (-36.,36.):base=hole(base,x,y,-.1,FLOOR+.1,2.2)
for x in (-22.,22.):base=hole(base,x,-38.,-.1,FLOOR+.1,2.2)
base=base.cut(box(NEW_W,PHONE_SLOT_D,RECESS,0,GUIDE_Y,FLOOR-RECESS/2))

s=base
for side in (-1,1):
    gx=side*(NEW_W/2+GUIDE_W/2)
    rail=box(GUIDE_W,PHONE_SLOT_D+2.,GUIDE_HEIGHT,gx,GUIDE_Y,FLOOR+GUIDE_HEIGHT/2.)
    s=s.fuse(rail)
    # Reproduce v0.4 front/rear edge retention geometry, at new inner width.
    # 1.1mm inboard of inner side face (not over the main touch display).
    for face in (-1,1):
        tab=box(1.1,3.4,GUIDE_HEIGHT-2.,side*(NEW_W/2-.55),
                GUIDE_Y+face*(PHONE_SLOT_D/2-1.2),FLOOR+(GUIDE_HEIGHT+2)/2)
        s=s.fuse(tab)

    # Reinforcement gussets on the OUTSIDE ONLY. No change to phone-depth clearance.
    # Two triangular vertically extruded webs, growing from phone-side rail to base.
    inner=NEW_W/2
    rail_outer=inner+GUIDE_W
    far_x=52.0 # inside the 55mm original base width
    h_top=40.0 # relative to build plate (orig 65mm side rails)
    coords=[(rail_outer-1.6,FLOOR), (far_x,FLOOR), (far_x,FLOOR+6.0),
            (rail_outer+0.3,FLOOR+h_top), (rail_outer-1.6,FLOOR+h_top)]
    coords=[(side*x,z) for x,z in coords]
    if side<0:coords=list(reversed(coords))
    for ylo,yhi in [(-5.8,-1.3),(7.6,12.1)]:
       # The XZ workplane extrudes toward negative Y.
       rib=(cq.Workplane('XZ', origin=(0,yhi,0)).polyline(coords).close()
            .extrude(yhi-ylo).val())
       s=s.fuse(rib)

# Rear back wall taller; top still far below rear cameras at the top of the 156mm phone.
# Position is unchanged; wall gets +14mm height and +0.6mm depth (outside direction).
rear_y=GUIDE_Y+PHONE_SLOT_D/2+1.0
back=box(NEW_W+2*GUIDE_W,WALL_T,WALL_H,0,rear_y+.3,FLOOR+WALL_H/2)
s=s.fuse(back)

# Two outside corner stabilizers, tucked behind the side guides, reducing shear stress
# on the wall junction. All material is outside the device contact faces.
for side in (-1,1):
   # Small vertical pad on the back wall OUTSIDE edge near its ends.
   x=side*(NEW_W/2+GUIDE_W-2.0)
   s=s.fuse(box(4.0,5.0,39.0,x,rear_y+1.6,FLOOR+39.0/2))

s=s.clean()
if len(s.Solids())!=1:
 raise RuntimeError('CAD part disconnected: '+str(len(s.Solids())))

stl=DIR/'STL'/'ARROWS_ALPHA_HOLDER_v041_REINFORCED_SLOT_71p6mm.stl'
step=DIR/'STEP'/'ARROWS_ALPHA_HOLDER_v041_REINFORCED_SLOT_71p6mm.step'
exporters.export(s,str(stl),exportType='STL',tolerance=0.05,angularTolerance=0.15)
exporters.export(s,str(step),exportType='STEP')
m=trimesh.load(str(stl),force='mesh',process=True)
assert m.is_watertight, 'not watertight'
assert len(m.split())==1,'mesh disconnected'
assert all(m.extents <= 220.01)
assert m.bounds[0][2] >= -.01
assert abs(m.extents[0]-110)<.01 and abs(m.extents[1]-114)<.01

# Compare actual bottom solid to original STEP from the uploaded v0.4 source.
original=cq.importers.importStep('/mnt/data/v04_source_work/03_STEP_SOURCE/CENTRAL_TRAY_PHONE_GUIDES.step').val()
orig_bb=original.BoundingBox()
if not (abs(orig_bb.xlen-110)<.01 and abs(orig_bb.ylen-114)<.01):
 raise RuntimeError('Original base does not match promised footprint')
# Constrain the validation to bottom z 0..4.8mm where the slot change cannot affect material.
bottom_region=box(140,140,4.7,0,0,2.35)
part_0=s.intersect(bottom_region)
orig_0=original.intersect(bottom_region)
missing=orig_0.cut(part_0).Volume()
extra=part_0.cut(orig_0).Volume()
print('BASE_BOTTOM_VOLUME_DIFFERENCE',missing,extra)
assert missing < .01 and extra<.01, 'Base mounting geometry was accidentally changed'

validation={
 'reference':'User-supplied ArrowsAlpha_LiveTray_v04_phone_backwall_PETG.zip',
 'new_holder_file':stl.name,
 'mesh_watertight':bool(m.is_watertight),
 'connected_components':len(m.split()),
 'body_count_in_STEP':len(s.Solids()),
 'print_bbox_xyz_mm':[round(float(x),2) for x in m.extents],
 'fits_adventurer5m_220mm':True,
 'base_original_xyz_mm':[110,114,6.4],
 'base_bottom_difference_volume_mm3':[round(missing,5),round(extra,5)],
 'groove_width_before_mm':OLD_W,
 'groove_width_after_mm':NEW_W,
 'guide_height_unchanged_mm':GUIDE_HEIGHT,
 'side_wall_thickness_before_mm':6.,
 'side_wall_thickness_after_mm':GUIDE_W,
 'rear_wall_height_before_mm':34.,
 'rear_wall_height_after_mm':WALL_H,
 'back_wall_thickness_before_mm':3.,
 'back_wall_thickness_after_mm':WALL_T,
 'external_support_web_count':4,
 'mating_dock':'v0.9 110 x 114 x 6.4 mm sliding receiver nominally unchanged (requires actual physical fit)',
 'printer_material':'AD5M PETG',
 'limitations':['No physical fit/load test performed','71.6mm inner slot is 1.0mm narrower than original 72.6mm and may be too tight for a cased device','The backwall may interfere with very thick/low-positioned card holders and must be checked by slow hand insertion','Snap hooks are PETG and must not be forced','Phone can still be pulled upward, no positive upward lock']}
(DIR/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')

fig,axes=plt.subplots(1,2,figsize=(11,5.5),layout='constrained')
ax=axes[0]
ax.add_patch(Rectangle((-55,-57),110,114,facecolor='#e8ecee',edgecolor='#455a64',linewidth=2))
ax.add_patch(Rectangle((-NEW_W/2,-6),NEW_W,18,facecolor='#e0d3b4',edgecolor='#ac8054',linewidth=1.2))
for side in (-1,1):
 x=side*(NEW_W/2+GUIDE_W/2)
 ax.add_patch(Rectangle((x-GUIDE_W/2,-7),GUIDE_W,20,facecolor='#51859a',edgecolor='#245062'))
ax.add_patch(Rectangle((-(NEW_W+2*GUIDE_W)/2, rear_y+.3-WALL_T/2),NEW_W+2*GUIDE_W,WALL_T,facecolor='#688699',edgecolor='#344b61'))
ax.annotate('',xy=(-NEW_W/2,-17),xytext=(NEW_W/2,-17),arrowprops=dict(arrowstyle='<->',color='#222',lw=1.4))
ax.text(0,-22,'71.6 mm (previously 72.6 mm)',ha='center',fontsize=9)
ax.set_xlim(-59,59);ax.set_ylim(-47,37);ax.set_aspect('equal');ax.set_title('Top — phone slot narrowed by 1 mm',fontsize=11);ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)')
ax=axes[1]
ax.add_patch(Rectangle((-55,0),110,6.4,facecolor='#b3c3d4',edgecolor='#455a64',linewidth=1))
for side in (-1,1):
 x=side*(NEW_W/2)
 ax.add_patch(Rectangle((x if side>0 else x-GUIDE_W,6.4),GUIDE_W,65.,facecolor='#688ba2',edgecolor='#44556c'))
 outer=side*(NEW_W/2+GUIDE_W)
 xx=[outer-side*1.6,side*52.,side*52.,outer+side*.3,outer-side*1.6]
 zz=[6.4,6.4,12.4,46.4,46.4]
 ax.add_patch(Polygon(list(zip(xx,zz)),facecolor='#9dbdc9',alpha=.8,edgecolor='#526b81'))
ax.add_patch(Rectangle((-43,6.4),86,48,fill=False,edgecolor='#cb7a46',linewidth=2,linestyle='--'))
ax.text(0,55.3,'Rear wall 48mm',color='#a65023',ha='center',fontsize=10)
ax.set_xlim(-57,57);ax.set_ylim(-2,79);ax.set_aspect('equal');ax.set_title('Front — reinforced side guides / 48mm back wall',fontsize=11);ax.set_xlabel('X (mm)');ax.set_ylabel('Z (mm)')
fig.suptitle('arrows alpha holder v0.4.1 | strengthened, v0.4 base mounting pattern unchanged',fontsize=12)
fig.savefig(DIR/'DRAWING'/'comparison_top_front.png',dpi=155)
plt.close(fig)

readme='''# arrows alpha ホルダー・補強版 v0.4.1（v0.4交換用）

**このZIPはスマホ保持部だけの修正版です。** 利用者からアップロードされた `ArrowsAlpha_LiveTray_v04_phone_backwall_PETG.zip` 内の元STEP/CADを基準に作りました。三脚用トレーの70mm取り付け部や左右テーブル、ドリンクホルダーは変更していません。

## 修正点

- スマホ溝の左右内幅 **72.6→71.6mm（1mm狭く）**。前後の深さ18mmは変更なし。
- スマホ側面の左右ガイド **6→8mm厚**、高さは65mmを維持。
- 左右ガイドの**外側に4本の三角補強リブを一体化**。荷重がかかりやすい付け根を補強。
- 背面の低い横壁 **高さ34→48mm、厚さ3.0→3.6mm**。背面カメラ周辺の上部は開けてあります。
- 前側左右の小さな保持ツメ・背面のカードホルダーがある前提は維持。前面中央は開放して画面を塞がない設計。
- **底板の横110mm×奥行114mm×厚さ6.4mm、底面と固定穴位置は完全維持。** v0.9中央トレーの差し込みドックに利用する前提。

## 重要な注意

**スマホ本体の公称幅約72mmより溝71.6mmが狭くなる場合があります。** 元のv0.4の実機フィットが緩かったためご指定の通り1mm狭くしましたが、PETGには十分なしなやかさがありません。無理に押し込むと、スマホ傷・ガイド破損の恐れがあります。入れた時の抵抗が強ければ中止し、溝幅を0.5mm戻すなど再調整してください。製造誤差・ケースの有無も影響します。

背面カードホルダーの厚さは不明です。**背面壁が高くなったため、カードホルダーに当たらないか**も確認してください。上からゆっくり差し込み、画面・カメラ・ボタンを覆ったり圧迫したりしないか確認してください。

## 印刷

- `STL/ARROWS_ALPHA_HOLDER_v041_REINFORCED_SLOT_71p6mm.stl` を**1個だけ印刷**。
- Flashforge Adventurer 5M・PETG、0.4mmノズル、積層0.20mm、壁4周、インフィル15～20%を初期値に。
- 底板をビルドプレートに載せ、ガイドが上を向く元データ通りの印刷向き。外寸110×114mm、高さ71.4mm。
- サポートは基本OFFを検討できますが、段差状の小さな前面ツメ／角部が急な張り出しになっていないかスライスプレビューで確認してください。
- 原データと異なり外側リブが立ち上がるため、造形中の変形・干渉にも注意。

## 互換性と検証

- オリジナルv0.4のSTEPから低い底板断面を比較し、ネジ穴を含め、**底板底面の形状差ゼロ**であることをCAD上で検査。
- STLメッシュは閉じていること、**連続した1つの立体**であること、220mm造形範囲内であることを検査。
- **印刷済みv0.9のドックとの実物嵌合や、スマホの保持強度は未検証です。** 

`STEP/` にはCAD再編集用STEPも同梱しています。
'''
(DIR/'README_変更内容と印刷.md').write_text(readme,encoding='utf8')
shutil.copy(__file__,DIR/'generate_holder_v041.py')
zipf=Path('/mnt/data/ArrowsAlpha_Holder_v041_Reinforced_1mm_narrow.zip')
with zipfile.ZipFile(zipf,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in DIR.rglob('*'):
  if f.is_file():z.write(f,arcname=f.relative_to(DIR))
print(json.dumps(validation,ensure_ascii=False,indent=2))
print('RESULT',zipf,zipf.stat().st_size)
