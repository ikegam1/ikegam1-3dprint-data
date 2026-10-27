"""ArrowsAlpha drop cup v1.1: angled inward 6.5 deg, below-floor bearing triangle gussets,
wide custom saddle matching center v0.9 6-mm front slab; all mm. For PETG & AD5M.
No load rating inferred from CAD or mesh validation.
"""
from pathlib import Path
import numpy as np, math, json, zipfile, shutil
import cadquery as cq
from cadquery import exporters
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path('/mnt/data/ArrowsAlpha_CUP_v11_INWARD_TILT_BOTTOM_BRACED')
STL=ROOT/'01_PRINT_STL'; STEP=ROOT/'02_EDITABLE_STEP'; PICS=ROOT/'03_ACTUAL_STL_RENDER'; REPORT=ROOT/'04_VERIFY'
for p in (STL,STEP,PICS,REPORT):p.mkdir(parents=True,exist_ok=True)
CENTER=cq.importers.importStep('/mnt/data/01_CENTER_V09_70mm_GRIP_110x114_PHONE_DOCK.step').val()

# Drawing coordinate system matches original v0.9 center STEP:
# center deck at z=9..15, front y=-81, clear through y=-60.5 beneath phone front fence.
# cup base is slightly FORWARD of the rim -> upper bottle leans inward toward y=0.
TILT=6.5
CUPY=-108.0; BASEZ=-111.0; CUP_H=70.0
R_OUT=45.0; R_IN=40.5; FLOOR=4.5
CLAMP_W=113.; CLAMP_YMIN=-94.0; CLAMP_YMAX=-59.0
DECK_FRONT=-81.0; DECK_TOP=15.; DECK_BOTTOM=9.
CLAMP_TOP_UNDER=15.34; CLAMP_BOTTOM_UPPER=8.60; CLEARANCE=0.34


def box(x,y,z,cx,cy,cz):return cq.Workplane('XY').box(x,y,z).translate((cx,cy,cz)).val()
def yzpoly(p,x1,xthick):return cq.Workplane('YZ',origin=(x1,0,0)).polyline(p).close().extrude(xthick).val()
def cylinder(r,h,x=0,y=0,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((x,y,z)).val()
def fuse(*objs):
    b=objs[0]
    for j in objs[1:]:b=b.fuse(j)
    return b

def tilt_cup_obj(s):return s.rotate((0,0,0),(1,0,0),-TILT).translate((0,CUPY,BASEZ))

# 4.5mm thick rim wall and enclosed 4.5mm load-bearing floor.
# Floor has 5 drain holes (no large delicate lattice crossing beneath heavy bottle).
uncut_outer=cylinder(R_OUT,CUP_H)
inner=cylinder(R_IN,CUP_H-FLOOR+2,z=FLOOR)
cuplocal=uncut_outer.cut(inner)
for x,y in [(0,0),(-18,-14),(-18,14),(18,-14),(18,14)]:
    cuplocal=cuplocal.cut(cylinder(4.0,FLOOR+1,x,y,-.5))
cuplocal=cuplocal.clean()
cupr=tilt_cup_obj(cuplocal)

# Wide U-shaped saddle: sandwich v0.9 tray's 6mm front edge.
# upper shelf at z15.34..20.34, lower shelf z3.6..8.60,
# front y=-94..-81 is full-depth reinforced return; rearward contact length 22mm.
clip_depth=CLAMP_YMAX-CLAMP_YMIN
middle_y=(CLAMP_YMAX+CLAMP_YMIN)/2
TOP=box(CLAMP_W,clip_depth,5.0,0,middle_y,17.84)
BOTTOM=box(CLAMP_W,clip_depth,5.0,0,middle_y,6.10)
FRONT_BRIDGE=box(CLAMP_W,13.3,17.0,0,-87.65,11.90) # y -94.3..-81, z3.4..20.4
saddle=fuse(TOP,BOTTOM,FRONT_BRIDGE)

# Strong load path:
# - two fully solid tapered 9-mm-thick side gussets form an underside strut to cup base
# - a third central back spine runs below floor and completes a triangular support
# - all three meet a full-width, full-depth transverse beam at the U throat.
# Each fusible rib is deliberately solid, not an airy pillar that breaks on support removal.
left_right=[]
for x0 in (-47.5,38.5):
    # x-range 38..49 intersects cup outer wall near side in XY; at bottom the leg reaches under floor.
    points=[(-96.5,8.6),(-59.0,8.6),(-64.0,-16.0),(-84.0,-78.0),(-97.0,-113.0),(-125.0,-114.5),(-114.0,-97.0),(-109.0,-49.0),(-100.0,-13.0)]
    rib=yzpoly(points,x0,9.0)
    left_right.append(rib)
# Center web behind cup lower back with large toe supporting cup from below.
# Shape is slightly forward-leaning to avoid extending toward phone dock above the slab.
center_spine=yzpoly([(-94.0,11),(-60.0,11),(-58.0,-30),(-63.0,-84),(-92.0,-117.5),(-124.0,-117.5),(-112.0,-107),(-85.0,-78),(-84.0,-32)],-8.0,16.0)
# Underfloor triangular transverse ledge; supports the cup from below and binds all three webs.
floor_strut=box(98,27,5.5,0,-108.0,-114.4)
# Transverse load distributor under the clip, wide and thick, attached to the side ribs.
clip_stiffener=box(111,16,9,0,-86,1.0)
# Outer horizontal reinforcement at the front edge of tray, below lower plate.
# Wide support strip carries shear along almost the full 113-mm saddle.
sill=box(113,13.5,5.2,0,-87.35,1.55)
shape=fuse(cupr,saddle, *left_right,center_spine, floor_strut,clip_stiffener,sill)
# Remove any rib/wedge geometry protruding into the vessel interior; keep 5mm floor intact.
inner_global=tilt_cup_obj(inner)
shape=shape.cut(inner_global)
# Remove any geometry from the tray plate insertion volume. Clip's returns are at y <= -81.0.
# Clearance applies everywhere behind tray front edge.
slot=box(130,90,CLAMP_TOP_UNDER-CLAMP_BOTTOM_UPPER,0,-36.0,(CLAMP_TOP_UNDER+CLAMP_BOTTOM_UPPER)/2)
shape=shape.cut(slot)
shape=shape.clean()
# A crucial printability check: the extra gussets must NOT protrude below the tilted
# bottle cup floor in the print orientation. Trim them flush to that floor plane,
# ensuring the full cup floor, not two skinny gusset tips, is what touches the bed.
print_floor_z=CUPY*math.sin(math.radians(TILT))+BASEZ*math.cos(math.radians(TILT))
rotated=shape.rotate((0,0,0),(1,0,0),TILT)
rotated=rotated.cut(box(400,400,150,0,0,print_floor_z+0.02-75)).clean()
shape=rotated.rotate((0,0,0),(1,0,0),-TILT).clean()
# For load sharing, mating plane must be planar and remain inside x+-56.5.

# Testing precise STEP assembly state and insertion from front along +Y direction.
vol=shape.intersect(CENTER).Volume()
progress=[]
for dy in np.linspace(-60,0,31):
    collision=shape.translate((0,float(dy),0)).intersect(CENTER).Volume()
    progress.append({'insertion_shift_mm':round(float(dy),2),'intersection_volume_mm3':round(float(collision),6)})
assert vol<0.05,(vol,'assembly fit');assert max(q['intersection_volume_mm3'] for q in progress)<0.05,'insertion clash'

if len(shape.Solids())!=1 or not shape.isValid():
    raise RuntimeError(f'not a valid single solid: {len(shape.Solids())} solids, valid {shape.isValid()}')

NAME='CUP_v11_6p5DEG_INWARD_113mm_SADDLE_SUPPORTS_500ml'
exporters.export(shape,str(STEP/(NAME+'.step')),exportType='STEP')
# print with angled bottom plane flattened; rotate entire assembly by +6.5 deg, then translate into build area.
pr=shape.rotate((0,0,0),(1,0,0),TILT)
bb=pr.BoundingBox()
pr=pr.translate((110-(bb.xmin+bb.xmax)/2,110-(bb.ymin+bb.ymax)/2,-bb.zmin))
exporters.export(pr,str(STL/(NAME+'_AD5M_PRINT.stl')),exportType='STL',tolerance=.065,angularTolerance=.23)
m=trimesh.load(str(STL/(NAME+'_AD5M_PRINT.stl')),force='mesh')
print('render mesh size:',m.extents, 'mass g theoretical',m.volume*1.27/1000,'connected meshes:',len(m.split()),'watertight?',m.is_watertight)
assert m.is_watertight and len(m.split())==1, 'bad STL solid component'
assert np.all(m.extents<=220) and (m.bounds[0]>=-0.01).all() and (m.bounds[1]<=220).all(), m.bounds

# Exact mesh render (NOT conceptual/generative). Main 3/4 view + detail underside/top; plot with true triangulated STL.
mm=trimesh.load(str(STL/(NAME+'_AD5M_PRINT.stl')),force='mesh')
# reverse print rotation to common assembly axes and center for clearer multi views
v0=shape # use STEP geometry tessellation: assembled at true origin, no overlaid drawn geometry
vis=trimesh.Trimesh(vertices=np.array(m.vertices),faces=np.array(m.faces),process=False)
V=np.array(vis.vertices) - np.mean(m.bounds,axis=0)
F=np.array(vis.faces)
# downsample surface triangles for plotting only; final printable STL is full quality
ix=np.linspace(0,len(F)-1,min(16000,len(F)),dtype=int)
faces=F[ix]
fig=plt.figure(figsize=(14,9.2),facecolor='white')
for idx,(elev,azim,label) in enumerate([(22,-62,'Print STL — 3/4 view'),(-18,-40,'Print STL — underside'),(18,138,'Print STL — clamp side'),(72,-72,'Print STL — top view')],start=1):
    ax=fig.add_subplot(2,2,idx,projection='3d')
    coll=Poly3DCollection(V[faces],facecolor='#e4a39b',edgecolor='none',alpha=1)
    ax.add_collection3d(coll)
    lo=V.min(0);hi=V.max(0)
    cen=(lo+hi)/2;mx=max(hi-lo)*.62
    ax.set_xlim(cen[0]-mx,cen[0]+mx);ax.set_ylim(cen[1]-mx,cen[1]+mx);ax.set_zlim(cen[2]-mx,cen[2]+mx)
    ax.view_init(elev=elev,azim=azim);ax.set_box_aspect((1,1,1));ax.set_axis_off();ax.set_title(label,fontsize=13)
fig.suptitle('v1.1 REAL printed STL mesh — not an AI concept rendering',fontsize=16)
fig.tight_layout(rect=[0,0,1,.96])
fig.savefig(PICS/'01_REAL_STL_MULTIVIEW.png',dpi=135,bbox_inches='tight');plt.close(fig)

# Real-fit cross-section schematic (not a photo): actual top and bottom clamp Z
fig,ax=plt.subplots(figsize=(10,4.3))
ax.add_patch(Rectangle((-81,DECK_BOTTOM),22,DECK_TOP-DECK_BOTTOM,fc='#a3a6b1',edgecolor='#656773',lw=1.5))
ax.add_patch(Rectangle((CLAMP_YMIN,CLAMP_TOP_UNDER),clip_depth,5,fc='#dd8c82',ec='#76352b',lw=1.5))
ax.add_patch(Rectangle((CLAMP_YMIN,3.6),clip_depth,5,fc='#dd8c82',ec='#76352b',lw=1.5))
ax.add_patch(Rectangle((-94.3,3.4),13.3,17,fc='#c87065',ec='#76352b',lw=1.5))
ax.annotate('v0.9 center slab: 6mm',xy=(-71,12),xytext=(-32,34),arrowprops=dict(arrowstyle='->'),fontsize=12)
ax.annotate('Wide top clamp: 113mm total span',xy=(-73,18.5),xytext=(-116,38),arrowprops=dict(arrowstyle='->'),fontsize=12)
ax.annotate('Wide lower shelf supports from below',xy=(-70,5.9),xytext=(-27,-18),arrowprops=dict(arrowstyle='->'),fontsize=12)
ax.set_xlim(-140,10);ax.set_ylim(-25,45);ax.set_aspect('equal');ax.axis('off');fig.tight_layout()
fig.savefig(PICS/'02_CLAMP_CROSS_SECTION.png',dpi=165,bbox_inches='tight');plt.close(fig)

report={
  'version':'v1.1','compatible_center_step':'01_CENTER_V09_70mm_GRIP_110x114_PHONE_DOCK.step',
  'tray_front_y_mm':DECK_FRONT,'tray_plate_z_mm':[DECK_BOTTOM,DECK_TOP],
  'clip_width_mm':CLAMP_W,'clip_rear_y_mm':CLAMP_YMAX,'plate_contact_length_mm':CLAMP_YMAX-DECK_FRONT,
  'clip_gap_mm':CLAMP_TOP_UNDER-CLAMP_BOTTOM_UPPER,'nominal_plate_clearance_each_mm':round((CLAMP_TOP_UNDER-CLAMP_BOTTOM_UPPER-6)/2,3),
  'cup_inward_tilt_deg':TILT,'cup_base_cy_mm':CUPY,'cup_rim_cy_approx_mm':round(CUPY+CUP_H*math.sin(math.radians(TILT)),2),
  'cup_inner_diameter_mm':R_IN*2,'cup_outer_diameter_mm':R_OUT*2,
  'cup_height_mm':CUP_H,'cup_floor_mm':FLOOR,'print_floor_plane_trim_applied':True,'nominal_bottle_volume_ml':500,
  'loaded_torque_example_Nm_approx':round(0.75*9.81*0.1,2),
  'solid_component_count':len(shape.Solids()),'valid_step_solid':shape.isValid(),
  'mesh_watertight':bool(m.is_watertight),'mesh_connected_count':len(m.split()),
  'AD5M_print_extent_xyz_mm':[round(float(v),2) for v in m.extents],
  'cad_center_intersection_mm3':round(float(vol),8),
  'assembly_slide_positions_checked':len(progress),'max_slide_collision_mm3':max(q['intersection_volume_mm3'] for q in progress),
  'mesh_volume_mm3':round(float(m.volume),1),'theoretical_PETG_mass_g':round(float(m.volume*1.27/1000),1),
  'warnings':['Designed for v0.9 center tray only; different printed center may not fit.',
    '6.5-degree inward inclination is modeled, it is NOT a hinge or a predictable elastic movement under 500ml load.',
    'No bolt/no positive latch. Friction and saddle geometry still need physical slide-off/load tests.',
    '500ml filled bottle is a design load case, not a certified or simulated safe rated load.',
    'PETG layers are anisotropic, so load and repeated jolting can cause failure.',
    'Use slicer supports only where explicitly needed under U saddle; remove carefully.',
    'Tripod tip-over stability depends on leg spread and other mounted gear.']}
(REPORT/'geometry_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
(REPORT/'slide_insertion_collision_samples.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
(ROOT/'README_印刷と取り付け.md').write_text('''# ドリンクホルダー v1.1（500mlボトル想定、PETG）

**v0.9中央テーブル専用**。他バージョンの中央には無加工で適合するとは限りません。

## 改良内容
- 内径81mm（一般的な500mlペットボトルの外径70mm前後を想定）。以前の83mmから少し縮小。
- カップの上側が三脚の中心に近づく**固定約6.5°の傾斜**。重さで曲がる可動式ではなく、最初から傾けた構造です。
- カップ底を全面4.5mm厚の底板（排水穴5つあり）で支持。前モデルの破断しやすい細い格子ではありません。
- カップ底部から中央テーブルの下面へ**左右2枚＋中央1枚の大きな三角補強板**を接続。
- 取り付け部分は幅113mmで、v0.9の厚さ6mmの中央テーブル前縁を、上面と下面から挟みます。
- 取り付け側の金具やネジ、別体ピンは使いません。

## プリントファイル
`01_PRINT_STL/CUP_v11_6p5DEG_INWARD_113mm_SADDLE_SUPPORTS_500ml_AD5M_PRINT.stl` を1個。
`02_EDITABLE_STEP`には装着時姿勢のCADを同梱。
`03_ACTUAL_STL_RENDER`の画像は実際のSTLから描画したもので、AI生成の完成予想図ではありません。

## 印刷
Flashforge Adventurer 5M / PETG。STLはビルドプレート内へ配置し、傾いたカップ底面を平らに接地する向きで保存しました。
0.4mmノズルの場合、積層0.20mm／壁4周／インフィル25〜35%／ノズル235〜245°C（材料優先）／ベッド75〜85°Cを初期目安にしてください。
カップ底面側から印刷。上部のU字型サドルに一部サポートが必要になる場合があります。サポートをONにする場合は、**取り付け溝の内部に除去困難なサポートが生成されないか、スライサープレビューで必ず確認**してください。

## 組み立て
中央テーブルの**手前側の前縁**から水平に差し込みます。サドルが中央テーブルの上下に掛かり、約22mm奥へ差し込まれます。無理に叩き込まないでください。

## 安全上の注意
500ml飲料を載せる前提の形ですが、CAE強度解析や実物の500ml静荷重・振動・傾け試験はまだしていません。
**耐荷重500gを保証したデータではありません。** 特にプラスチックの積層方向、印刷欠陥、三脚の重心に左右されます。
中央テーブルを水平にした状態で、まず空ボトル→少量の水→500mlの順に確認し、変形・カタつき・脱落・三脚の転倒兆候があればすぐ中止してください。安全な平面で足を十分広げ、スマホ等が損傷しない状態で行ってください。
取り付けには**完全な抜け止めロックはありません**。外れる方向に引っ張られる運用や移動中の使用は避けてください。
''',encoding='utf-8')
shutil.copy(__file__,ROOT/'generate_v11.py')
Z=Path('/mnt/data/ArrowsAlpha_CUP_v11_500ml_INWARD_ANGLE_WIDE_BRACE.zip')
with zipfile.ZipFile(Z,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for f in ROOT.rglob('*'):
        if f.is_file():z.write(f,arcname=str(f.relative_to(ROOT)))
print('created',Z,Z.stat().st_size)
