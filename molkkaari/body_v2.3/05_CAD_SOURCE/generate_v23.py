"""Molkkaari v2.3 - printable body & storage channel, 4 bars and 3 removable pin bridges.
For Flashforge Adventurer 5M (220 mm bed), PETG. Model in mm. No print tests.
"""
import os, math, json, zipfile, shutil, io
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh
from cadquery import exporters
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon as MPolygon

ROOT=Path('/mnt/data/Molkkaari_v2_3_4bars_engraved_storage')
D_BODY=ROOT/'01_BODY_STL_ONE_EACH'
D_BRIDGES=ROOT/'02_CONNECTORS_STL_ONE_EACH'
D_RULER=ROOT/'03_3500mm_RULER_STL'
D_TEST=ROOT/'04_TEST_FIRST'
D_CAD=ROOT/'05_CAD_SOURCE'
D_IMG=ROOT/'06_GUIDE_IMAGES'
for d in [D_BODY,D_BRIDGES,D_RULER,D_TEST,D_CAD,D_IMG]:d.mkdir(parents=True, exist_ok=True)
BARNAMES=['01_LEFT_WING','02_CENTER_LEFT','03_CENTER_RIGHT','04_RIGHT_WING']
L=240.; WIDTH=18.; HEIGHT=33.; WALL=2.2; ROOF=2.4
GAP=40/3 # mm, overall path length of 4x240 + 3x13.333 = 1000
PIN_HOLE=4.15; PEG=3.65; PLATE_T=2.2; PEG_L=6.0
ANGLES=[45.,0.,0.,-45.]
PITCH=3500/18
validation=[]

def box(l,w,h,xc,yc,zc):
 return cq.Workplane('XY').box(l,w,h).translate((xc,yc,zc)).val()

def export_stl(shape,path,bed=True):
 exporters.export(shape,str(path),exportType='STL',tolerance=0.06,angularTolerance=0.23)
 m=trimesh.load(str(path),force='mesh'); bb=m.bounds; size=m.extents
 record={'name':path.name,'closed_mesh':bool(m.is_watertight),'components':len(m.split()),'size_mm':[round(float(v),2) for v in size],'volume_mm3':round(float(abs(m.volume)),1),'fits_AD5M':bool((size<=220.01).all()),'bbox_min':[round(float(v),2) for v in bb[0]]}
 if not m.is_watertight or abs(m.volume)<1: raise RuntimeError('Bad STL '+str(record))
 if bed and ((bb[0] < -0.01).any() or (bb[1]>220.01).any()):raise RuntimeError('Out of bed '+str(record)+str(bb))
 validation.append(record);print(record)
 return m

def make_bar(i):
 # Outer solid 240 x 18 x 33; underside cavity. Only full-width end webs where sockets are present.
 body=box(L,WIDTH,HEIGHT,L/2,0,HEIGHT/2)
 if i==0: x1,x2=6.,213.  # no socket at the start; two sockets near the right end
 elif i==3: x1,x2=27.,234. # no socket at the end
 else: x1,x2=27.,213.
 channel=box(x2-x1, WIDTH-2*WALL, HEIGHT-ROOF+0.4,(x1+x2)/2,0,(HEIGHT-ROOF-0.4)/2)
 body=body.cut(channel)
 # Right and/or left end sockets: vertical THRU holes; no unsupported roofs/bridging over blind holes.
 holes=[]
 if i>0:holes += [(10.,0.),(21.,0.)]
 if i<3:holes += [(219.,0.),(230.,0.)]
 for x,y in holes:
  # square bores run top-to-bottom through solid end walls; 0 bridging above them.
  body=body.cut(box(PIN_HOLE,PIN_HOLE,HEIGHT+2,x,y,HEIGHT/2))
 # Shallow tapered retaining ridges inside the storage channel.
 # Their overhang grows gradually from the sidewall, avoiding a free-standing cantilever.
 # Clearance/retention must be checked with a short real PETG sample.
 if i==0:
  for x in (39.,166.):
   for side in (-1,1):
    yz=[(side*7.2,10.5),(side*7.2,2.5),(side*3.0,2.5),(side*6.9,9.7)]
    if side<0:yz=yz[::-1]
    ridge=cq.Workplane('YZ').polyline(yz).close().extrude(5.5).translate((x-2.75,0,0)).val()
    body=body.fuse(ridge)
 # External front wall lettering, at y=-9. CAD plane XZ has normal -Y.
 # Font size 17mm, recess .7mm through front face, retaining at least 1.5mm wall.
 try:
  textshape=(cq.Workplane('XZ',origin=(L/2,-WIDTH/2+0.72,17.5))
    .text('Mölkky',17.,1.0,font='DejaVu Sans',kind='bold',halign='center',valign='center',combine=True)
    .val())
  body=body.cut(textshape)
 except Exception as err:
  print('ERROR during unicode text generation:',err);raise
 return body.clean(),(x1,x2)

def print_orientation(shape):
 # Roof broad outside top face is directly on build plate. U channel is OPEN UP during printing.
 # Rotate about X to flip top & bottom, then 45 degrees in XY to fit 240mm into 220x220 bed.
 s=shape.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),-45)
 bb=s.BoundingBox()
 s=s.translate((110-(bb.xmin+bb.xmax)/2,110-(bb.ymin+bb.ymax)/2,-bb.zmin))
 return s

BODIES=[];CAVITIES=[]
for i,name in enumerate(BARNAMES):
 b,chan=make_bar(i);BODIES.append(b);CAVITIES.append(chan)
 export_stl(print_orientation(b),D_BODY/(f'AD5M_{name}_ROOF_DOWN.stl'))
 exporters.export(b,str(D_CAD/(name+'.step')),exportType='STEP')

# Assembly geometry / rigid-body placement: connectors conform to both bars' socket locations.
def direction(a):return np.array([math.cos(math.radians(a)),math.sin(math.radians(a))])
def rotate_2d(xy,a):
 a=math.radians(a);return np.array([math.cos(a)*xy[0]-math.sin(a)*xy[1],math.sin(a)*xy[0]+math.cos(a)*xy[1]])
starts=[np.array([0.,0.])]
for i in range(3):
 previous_end=starts[i]+L*direction(ANGLES[i])
 bisector=direction((ANGLES[i]+ANGLES[i+1])/2)
 starts.append(previous_end+GAP*bisector)

def coord(i,x,y=0.):return starts[i]+rotate_2d([x,y],ANGLES[i])

# Cross-section plate outline computed as convex hull of circles around socket points,
# avoiding unsupported overhangs. Full cap is 2.2mm, sits on top at z=33..35.2.
# Pins grow from the plate toward the ground; print upside down with plate on bed.
def bridge(j):
  left,right=j,j+1
  pts=[coord(left,219),coord(left,230),coord(right,10),coord(right,21)]
  footprint=unary_union([Point(float(x),float(y)).buffer(5.,resolution=16) for x,y in pts]+[LineString([tuple(pts[i]),tuple(pts[i+1])]).buffer(4.6,cap_style=1) for i in (0,1,2)]).convex_hull
  coords=list(footprint.exterior.coords)
  plate=cq.Workplane('XY').polyline(coords).close().extrude(PLATE_T).translate((0,0,HEIGHT)).val()
  for k,(x,y) in enumerate(pts):
   a=ANGLES[left if k<2 else right]
   peg=box(PEG,PEG,PEG_L,float(x),float(y),HEIGHT-PEG_L/2)
   peg=peg.rotate((x,y,0),(x,y,1),a)
   plate=plate.fuse(peg)
  return plate.clean(),pts

BRIDGES=[]
for j,name in enumerate(['A_LEFT_45DEG','B_CENTER_STRAIGHT','C_RIGHT_45DEG']):
 join,pts=bridge(j); BRIDGES.append(join)
 # print with plate on bed, pegs upright; flip z
 oriented=join.rotate((0,0,0),(1,0,0),180)
 bb=oriented.BoundingBox()
 oriented=oriented.translate((110-(bb.xmin+bb.xmax)/2,110-(bb.ymin+bb.ymax)/2,-bb.zmin))
 export_stl(oriented,D_BRIDGES/(f'AD5M_JOIN_{name}.stl'))
 exporters.export(join,str(D_CAD/(f'JOIN_{name}.step')),exportType='STEP')

# print tiny socket tests and a connector for pin clearance assessment
# Use real sockets cut out from printed bars, not detached pins only.
for tag,i,xcenter in [('LEFT_45',0,223),('CENTER_180',1,223),('RIGHT_45',2,223)]:
  b=BODIES[i]
  short=b.intersect(box(48.,18.4,33.1,xcenter,0,16.5)).clean()
  export_stl(print_orientation(short),D_TEST/(f'TEST_SOCKET_{tag}.stl'))

# Joint test pairs (real mating ends) for a complete 45-degree and straight connection.
# Slice 40 mm from each adjoining bar, not just one socket end.
for tag,left,right in [('45DEG',0,1),('180DEG',1,2)]:
 left_piece=BODIES[left].intersect(box(42.,18.2,33.2,L-21.,0,16.5)).clean()
 right_piece=BODIES[right].intersect(box(42.,18.2,33.2,21.,0,16.5)).clean()
 export_stl(print_orientation(left_piece),D_TEST/(f'TEST_{tag}_BAR_A_END.stl'))
 export_stl(print_orientation(right_piece),D_TEST/(f'TEST_{tag}_BAR_B_START.stl'))

# Storage retention sample and dummy 18-layer packet; test before relying on friction tabs.
short=BODIES[0].intersect(box(62.,18.2,33.2,45,0,16.5)).clean()
export_stl(print_orientation(short),D_TEST/'TEST_STORAGE_RETENTION_62mm.stl')
export_stl(box(60.,6.5,12.0,30,3.25,6),D_TEST/'TEST_STORAGE_FAKE_BUNDLE_60x6p5x12.stl',bed=False)

# Reuse the 18-section 3.5m measurement tool from v2.2.1, without modifying its calibrated pitch.
# Its fatigue/fit is not verified; test pair print is mandatory before all 18 sections.
from zipfile import ZipFile
src=Path('/mnt/data/molkkaari_v2_2_1_AD5M_PETG_print_orientation_fixed_full.zip')
with ZipFile(src) as z:
 for name,new in [
  ('02_3500mm_MEASURE_STL/PLATE_A_8_MIDDLES_PRINT_TWICE.stl','RULER_8_MIDDLE_PRINT_TWICE.stl'),
  ('02_3500mm_MEASURE_STL/PLATE_B_START_END_PRINT_ONCE.stl','RULER_START_END_PRINT_ONCE.stl')]:
  data=z.read(name);f=D_RULER/new;f.write_bytes(data)
  m=trimesh.load(str(f),force='mesh')
  print('RULER',f.name,m.extents, m.is_watertight)
  if not m.is_watertight or (m.extents > np.array([220,220,220])).any():raise RuntimeError('bad ruler file '+new)
 z.extract('03_FIRST_PRINT_TESTS/TEST_2_RAILS_65mm_PRINT_FIRST.stl',D_TEST)
 shutil.move(str(D_TEST/'03_FIRST_PRINT_TESTS'/'TEST_2_RAILS_65mm_PRINT_FIRST.stl'),D_TEST/'TEST_RULER_2SHORT_RAILS.stl')
 shutil.rmtree(D_TEST/'03_FIRST_PRINT_TESTS')

# Check assembly for bar-bar solid collisions (nominal gap should eliminate).
from shapely import affinity
polys=[]
for i in range(4):
 footprint=Polygon([(0,-WIDTH/2),(L,-WIDTH/2),(L,WIDTH/2),(0,WIDTH/2)])
 footprint=affinity.rotate(footprint,ANGLES[i],origin=(0,0))
 footprint=affinity.translate(footprint,float(starts[i][0]),float(starts[i][1]))
 polys.append(footprint)
for j in range(3):
 area=polys[j].intersection(polys[j+1]).area
 if area>0.001:raise RuntimeError('bar ends collide! '+str((j,area)))
print('path length:',4*L+3*GAP,'footprint span x=',unary_union(polys).bounds[2]-unary_union(polys).bounds[0])

# 2D assembly drawing
fig,ax=plt.subplots(figsize=(11,5.8))
for i,poly in enumerate(polys):
 xy=np.array(poly.exterior.coords)
 ax.add_patch(MPolygon(xy,facecolor='#d9b982',edgecolor='#644b30',lw=1.8))
 c=starts[i]+120*direction(ANGLES[i]);ax.text(c[0],c[1],f'{i+1}',ha='center',va='center',fontsize=11,rotation=ANGLES[i],color='#302313',fontweight='bold')
for j,join in enumerate(BRIDGES):
 pts=[coord(j,219),coord(j,230),coord(j+1,10),coord(j+1,21)]
 outline=unary_union([Point(float(x),float(y)).buffer(5.,resolution=16) for x,y in pts]).convex_hull
 xx,yy=outline.exterior.xy
 ax.plot(xx,yy,color='#1976a1',lw=2.5)
ax.set_aspect('equal');ax.autoscale_view();ax.margins(0.12);ax.axis('off')
ax.set_title('MOLKKAARI v2.3   |   4 bars + 3 drop-in angle connectors',fontsize=16)
ax.text(0.5,-0.06,'Front vertical faces (not shown from above) are engraved Mölkky; path length = 1,000 mm',transform=ax.transAxes,ha='center',fontsize=11)
fig.savefig(D_IMG/'01_assembled_top_view.png',dpi=160,bbox_inches='tight');plt.close(fig)

# side section diagram: lower face is open toward ground after assembly
fig,ax=plt.subplots(figsize=(9,3.8))
from matplotlib.patches import Rectangle
ax.add_patch(Rectangle((-9,0),18,33,color='#dfb779',ec='#573c25',lw=2))
ax.add_patch(Rectangle((-6.8,0),13.6,30.6,color='white',ec='#573c25',lw=1.5))
ax.add_patch(Rectangle((-3.25,4),6.5,14.5,color='#85b4b6',ec='#2c7378',lw=1.5))
ax.plot([-9,9],[0,0],color='#604a38',lw=3)
ax.annotate('Ground-facing OPEN underside',xy=(0,0),xytext=(25,4),arrowprops=dict(arrowstyle='->'),fontsize=11)
ax.annotate('Stored 3.5 m folding strip bundle',xy=(0,10),xytext=(25,19),arrowprops=dict(arrowstyle='->'),fontsize=11)
ax.annotate('2.4 mm top wall',xy=(0,32),xytext=(25,33),arrowprops=dict(arrowstyle='->'),fontsize=11)
ax.set_xlim(-14,120);ax.set_ylim(-8,39);ax.set_aspect('equal');ax.axis('off');ax.set_title('v2.3 OPEN-BOTTOM U-CHANNEL (section)',fontsize=14)
fig.savefig(D_IMG/'02_cavity_cross_section.png',dpi=160,bbox_inches='tight');plt.close(fig)

# Slicer / plate diagram (roof down; top-down 220 mm bed)
fig,ax=plt.subplots(figsize=(6,6))
ax.add_patch(Rectangle((0,0),220,220,fc='#edf2f4',ec='#323232',lw=2))
name=BARNAMES[0];shape=print_orientation(BODIES[0]);bb=shape.BoundingBox()
ax.add_patch(Rectangle((bb.xmin,bb.ymin),bb.xlen,bb.ylen,fc='#a0c7cf',ec='#087b92',alpha=.7))
ax.text(110,17,'220 x 220 mm build plate',ha='center',fontsize=11)
ax.text(110,190,'Bar is diagonal / outer roof face DOWN',ha='center',fontsize=11)
ax.text(110,180,'Hollow channel faces UP while printing',ha='center',fontsize=10)
ax.set_xlim(-5,225);ax.set_ylim(-5,225);ax.axis('off');ax.set_aspect('equal')
fig.savefig(D_IMG/'03_print_orientation.png',dpi=150,bbox_inches='tight');plt.close(fig)

# Design metadata and validation
meta={'version':'2.3','date':'2026-10-15','printer':'Flashforge Adventurer 5M','material':'PETG',
'body_bars':4,'bar_nominal_length_mm':L,'body_cross_section_mm':[WIDTH,HEIGHT],
'joiner_count':3,'gap_nominal_mm':GAP,'assembled_path_length_nominal_mm':4*L+3*GAP,
'angles_between_bars_deg':[45,180,45],
'measure_total_length_design_mm':3500,'measure_segments':18,'measure_segment_pitch_mm':PITCH,
'measure_folded_max_nominal_mm':PITCH+1.5,
'bar1_cavity_length_mm':CAVITIES[0][1]-CAVITIES[0][0],
'bar1_cavity_inner_width_mm':WIDTH-2*WALL,'bar1_cavity_inner_height_mm':HEIGHT-ROOF,
'joiner_hole_width_mm':PIN_HOLE,'joiner_peg_width_mm':PEG,
'font':'DejaVu Sans Bold','text':'Mölkky','text_position':'front vertical face of each bar','text_method':'0.7 mm recessed',
'assumptions':['Hinge mechanism of reused 3.5m ruler has not been real-world tested',
'Final assembled path length of 1000 mm is nominal centerline sum incl. gaps and does not equal horizontal projected width',
'Printable joint geometry is new and not compatible with previous v2.2.1 body',
'Printed pin fit requires test on target PETG and machine; no printed fit guarantee']}
(D_CAD/'design_values.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
(D_CAD/'mesh_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy(__file__,D_CAD/'generate_v23.py')

readme=f'''# モルッカーリ v2.3 — 4本構成・前面Mölkky刻印・下面中空・3.5m測定具収納

対象：Flashforge Adventurer 5M（220×220×220mm）、PETG、ノズル0.4mm。

## 今回の変更
- 本体：**4本**、各240mm（5本目は廃止）。正規品に近い形状です。
- ジョイント間に約13.33mmの間隔を3か所確保し、中心線をたどった**設計全長約1000mm**。横幅（左右端間の投影寸法）が1000mmという意味ではありません。
- 4本の**前面**それぞれに、**Mölkky** と0.7mm程度の凹文字を刻印。文字を拡大縮小せず造形してください。
- 各本体は**地面側が開いたコの字型中空**。フタ・キャップなし。左端の板内に3.5m測定具を収納します。
- 旧版で破綻した長いブリッジを避けるため、上面の角穴に別体の**連結ブリッジ3個**を上から差し込む方式を採用。中央180°、左右45°をそれぞれ固定します。
- 上面の角穴は**貫通穴**です。長い空洞にも蓋がないため、屋根全長のブリッジ造形はありません。
- **接着剤不要**。ただし印刷後の嵌合・保持力・測定具の折りたたみは未検証です。

## 本番印刷ファイル（合計10ジョブ）
**本体：4回** `01_BODY_STL_ONE_EACH/` 内4ファイルを各1回ずつ。
**連結部：3回** `02_CONNECTORS_STL_ONE_EACH/` 内 A（45°）、B（180°）、C（45°）を各1回ずつ。
**3.5m測定具：3回**
- `03_3500mm_RULER_STL/RULER_8_MIDDLE_PRINT_TWICE.stl` を2回（中間16本）
- `03_3500mm_RULER_STL/RULER_START_END_PRINT_ONCE.stl` を1回（先端・終端2本）

全てSTLをスライサーへ読み込んだら **サイズ100%** のまま印刷してください。

## 印刷方向（必ず確認）
- 本体：**広い天面をビルドプレートに接地、下面の空洞は上向き**です。STLは斜め配置済み。長手を垂直に立てないでください（240mm > AD5MのZ高さ220mm）。
- ジョイント：**広い平板面をビルドプレートに接地、4本の四角ピンが上向き**。それぞれ小型です。コーナー下面にサポートは原則不要な向きです。
- 測定具：**板を平らに寝かせる**。厚0.6mm、薄肉部0.3mm。印刷速度を落としサポートOFF推奨。

## まず小さいテストで確認
1. `04_TEST_FIRST/TEST_RULER_2SHORT_RAILS.stl`：0.3mm可撓部分、スナップを確認。
2. `04_TEST_FIRST/TEST_180DEG_BAR_A_END.stl` と `TEST_180DEG_BAR_B_START.stl` を印刷し、中央ジョイントの4本のピンが入るか確認。45°用も同様に2本でテストします。
3. `02_CONNECTORS_STL_ONE_EACH/AD5M_JOIN_B_CENTER_STRAIGHT.stl` を1つ印刷し、角穴への入り具合を確認。
4. `04_TEST_FIRST/TEST_STORAGE_RETENTION_62mm.stl` と `TEST_STORAGE_FAKE_BUNDLE_60x6p5x12.stl` で保持具合を先に確認。

## 収納と設置
- 測定具は18本を最初だけ連結し、以後できるだけ接続を維持して蛇腹に折りたたみます。
- 左端本体の空洞：設計長約**{CAVITIES[0][1]-CAVITIES[0][0]:.1f}mm**、内幅**{WIDTH-2*WALL:.1f}mm**、内高**{HEIGHT-ROOF:.1f}mm**。ただし保持リブ部は狭くなります。
- 測定具の1本は約194.4mmピッチで、最大の先端を含めても約196mm。18枚を重ねた厚さの理論下限10.8mmです。**18本全体を連結したまま確実に収納できるかは物理試験が必要**です。
- 収納するときは本体をひっくり返して空洞を上向きにし、束を入れます。抜け防止リブの保持力はPETGとプリンター条件で変わります。
- 地面に置く際には空洞が下向き。角穴を合わせ、薄い平板のついたジョイントを**上から差し込む**だけです。

## 推奨PETGスライサー初期値
- 温度：ノズル235〜245°C・ベッド75〜85°C（フィラメント指定優先）
- 本体：積層ピッチ0.20mm、外周4周、速度40〜60mm/s、ブリム4mmは必要に応じて
- 本体と連結パーツはサポートなしを基本にスライスプレビューで確認。凹文字の小さな上端はサポート不要想定ですが実機未検証。
- 測定具：積層ピッチ0.15mm、初層0.15mm、20〜30mm/s程度、サポートなし、ブリム不要ならOFF
- **測定具の0.3mm部は2層になっていることをスライサーで確認**。

## ご注意
- これはCAD上で形状・造形サイズをチェックした試作です。**実機の印刷と嵌合確認は未実施**。
- 連結ブリッジの角ピン幅{PEG:.2f}mmに対し角穴幅{PIN_HOLE:.2f}mm。軸方向の公差は印刷状態で変わります。テスト印刷を優先してください。
- 3.5m測定具は前版から流用したSTLで、**3,500mmは設計ピッチの合計**です。実際の端から端、ジョイントの遊び、収縮を含めた精度は完成後に巻尺で校正してください。
- 0.3mm厚PETGネックは繰り返し180°折ると白化・破損するおそれがあり、持続使用は保証できません。テストで破損した場合は18本を印刷しないでください。
- v2.2.1の5本とジョイント互換はありません。
'''
(ROOT/'README_まず読んでください.md').write_text(readme,encoding='utf-8')

fullzip=Path('/mnt/data/molkkaari_v2_3_4bars_Molkky_engraved_3500mm.zip')
with zipfile.ZipFile(fullzip,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in ROOT.rglob('*'):
  if f.is_file():z.write(f,arcname=f.relative_to(ROOT))
minzip=Path('/mnt/data/molkkaari_v2_3_ESSENTIAL_STL.zip')
with zipfile.ZipFile(minzip,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for d in (D_BODY,D_BRIDGES,D_RULER):
  for f in d.glob('*.stl'):z.write(f,arcname=str(f.relative_to(ROOT)))
 z.write(ROOT/'README_まず読んでください.md',arcname='README_まず読んでください.md')
print('SUCCESS',fullzip,fullzip.stat().st_size,minzip,minzip.stat().st_size)
