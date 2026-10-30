"""v1.3 center-shifted CUP redesign based on v1.2 source: true printable CAD for AD5M PETG.
All geometry millimeters. Cup approximates half underside placement; outward 15-deg lean is
necessary for in/out bottle clearance with fixed center tray at original cup height.
"""
from pathlib import Path
import cadquery as cq, numpy as np, math, json, zipfile, shutil
from cadquery import exporters
import trimesh
from cadquery import Vector

ROOT=Path('/mnt/data/ArrowsAlpha_Cup_v13_BACKSHIFT_TESTED')
STL=ROOT/'STL'; STEP=ROOT/'STEP'; CHECK=ROOT/'inspection'
for d in (STL,STEP,CHECK):d.mkdir(parents=True,exist_ok=True)
def box(a,b,c,x=0,y=0,z=0):return cq.Workplane('XY').box(a,b,c).translate((x,y,z)).val()
def cyl(r,h,z=0):return cq.Workplane('XY').circle(r).extrude(h).translate((0,0,z)).val()
def ann(ro,ri,z,h):return cyl(ro,h,z).cut(cyl(ri,h+2,z-1))
def yzpoly(P,x,w):return cq.Workplane('YZ',origin=(x,0,0)).polyline(P).close().extrude(w).val()
def combine(items):
 s=items[0]
 for x in items[1:]:s=s.fuse(x)
 return s.clean()
TILT=15.0; TH=math.radians(TILT); CY=-76.0; CZ=-171.0
RO=46.5; RI=41.5; H=76.0

def tow(obj):return obj.rotate((0,0,0),(1,0,0),TILT).translate((0,CY,CZ))
# Retain mesh structural concept of the user's successful print; slightly smaller circle.
mesh=[ann(RO,RI,z,h) for z,h in [(0,6),(24,5),(48,5),(69,7)]]
for i in range(12):
 a=i*2*math.pi/12
 r=(RO+RI)/2
 mesh.append(box(5.5,5.5,H,r*math.cos(a),r*math.sin(a),H/2))
for p in (-23,0,23):
 mesh.append(box(7.0,86,5.2,p,0,2.6));mesh.append(box(86,7.0,5.2,0,p,2.6))
cage=combine(mesh).intersect(cyl(RO,H)).cut(cyl(RI,H-5.5+1,5.5)).clean()
cup=tow(cage)
# Re-use exact dimensions of tested v1.2 high-strength saddle.
TOP=box(113,35,5,0,-76.5,17.84)
BOT=box(113,35,5,0,-76.5,6.10)
BRIDGE=box(113,13.4,16.8,0,-87.6,12.0)
UNDER=box(113,14.0,9,0,-87.3,-.5)
# Lowered brace struts wrap the back of cup; upper shoulder remains near established mount.
# Wide side plates x+-26..+-40, and center spine x+-11. These run *behind* cup, and
# are trimmed by cylindrical bottle-clearance boring, preventing internal snagging.
side_profile=[(-94.3,7),(-75.7,7),(-69,-23),(-57,-74),(-43,-124),(-29,-176),
              (-53,-176),(-64,-133),(-79,-75),(-92,-20)]
sideplates=[yzpoly(side_profile,-41,14),yzpoly(side_profile,27,14)]
# Center spine along rear center y: from saddle down to floor and rear of cage.
center_profile=[(-94.3,6),(-67,6),(-54,-42),(-40,-106),(-24,-177),
                (-52,-177),(-64,-127),(-78,-72),(-91,-20)]
mid=yzpoly(center_profile,-11,22)
# Two short triangular floor supports for bending moment; underneath cage rim, not fragile posts.
# Adjacent rib overlap in X is intentional. The lattice itself is preserved.
underfloor=box(85,15,7.5,0,-70,-172)
# Cut below print bottom plane so it rests on broad base when tilted.
part=combine([cup,TOP,BOT,BRIDGE,UNDER,*sideplates,mid,underfloor])
# Bottle-safe bore along the 15 degree CAGE axis.
part=part.cut(tow(cyl(RI,400,5.5))).clean()
# Keep actual deck slab 6 mm unobstructed within clip gap.
part=part.cut(box(140,95,6.74,0,-33.5,11.97)).clean()
# Test actual complete surrogate including cap (80 diameter, 220 high)
tray=combine([box(136,162,6,0,0,12),box(114,3.4,6.5,0,-54,18.25)])
body=cyl(40,160)
shoulder=cq.Solid.makeCone(40,15.5,30,Vector(0,0,160),Vector(0,0,1))
bottle=combine([body,shoulder,cyl(15.5,16,190),cyl(17,14,206)])
# Contact-length and area ring overlap: estimate projection of basket along y into y>-81.
ring_pts=[]
for z in [0,19,38,57,76]:
 y=CY-z*math.sin(TH)
 theta=np.linspace(0,2*math.pi,4000,endpoint=False)
 ys=y+RO*np.sin(theta)
 ring_pts.append({'local_z_mm':z,'ring_center_y_mm':round(y,3), 'fraction_ring_circumference_below_table_percent':round(float(np.mean(ys>-81)*100),1)})
# Mass center via bottle volume if user wishes - model only, not finite-element model.
old_mass_y=-146+110*math.sin(math.radians(6.5))
new_mass_y=CY-110*math.sin(TH)
fit=[]
for h in range(0,221,5):
 b=tow(bottle.translate((0,0,5.6+h)))
 v1=b.intersect(tray).Volume();v2=b.intersect(part).Volume()
 fit.append({'lift_mm':h,'bottle_vs_tray_mm3':round(float(v1),4),'bottle_vs_holder_mm3':round(float(v2),4)})
clip=[]
for dy in range(-60,1,3):
 v=part.translate((0,dy,0)).intersect(tray).Volume()
 clip.append((dy,round(float(v),4)))
print('part valid',part.isValid(),'solids',len(part.Solids()),'vol',part.Volume())
print('bottle max collisions',max(x['bottle_vs_tray_mm3'] for x in fit),max(x['bottle_vs_holder_mm3'] for x in fit))
print('tray max clashes',max(y for x,y in clip))
print('cup coverage at heights',ring_pts)
assert part.isValid() and len(part.Solids())==1
assert max(x['bottle_vs_tray_mm3'] for x in fit)<.05
assert max(x['bottle_vs_holder_mm3'] for x in fit)<.05
assert max(x[1] for x in clip)<.05
# print orient 15deg opposite cup lean, full cup grate rests flat on plate.
pr=part.rotate((0,0,0),(1,0,0),-TILT)
# broad CUP floor reference plane, parts not allowed below build plate.
print_z=-CY*math.sin(TH)+CZ*math.cos(TH)
# clip any dangling bottom sub-mm geometry below cup floor plane
pr=pr.cut(box(440,440,150,0,0,print_z+0.01-75)).clean()
assert pr.isValid() and len(pr.Solids())==1
part=pr.rotate((0,0,0),(1,0,0),TILT).clean()
FN='CUP_v13_500ml_HALF_UNDER_TABLE_BACKSHIFT_MESH'
exporters.export(part,str(STEP/(FN+'.step')),exportType='STEP')
bb=pr.BoundingBox()
for_print=pr.translate((110-(bb.xmin+bb.xmax)/2,110-(bb.ymin+bb.ymax)/2,-bb.zmin))
exporters.export(for_print,str(STL/(FN+'_AD5M_PETG.stl')),exportType='STL',tolerance=.05,angularTolerance=.17)
m=trimesh.load(next(STL.glob('*.stl')),force='mesh')
print('mesh',m.extents,'solid?',m.is_watertight,'components',len(m.split()),'volume',m.volume)
assert m.is_watertight and len(m.split())==1 and (m.extents<=220.001).all()
rep={'assembly_cad':'center v0.9 slab 136x162x6mm; phone front stop at y=-54,z15..21.5',
     'saddle_connection_same_as_v12':True,'cup_height_unchanged_mm':76,'cup_base_z_mm':CZ,
     'cup_inner_diameter_mm':RI*2,'cup_outer_diameter_mm':RO*2,
     'tilt_direction':'outward (toward front), needed for bottle/tray clearance while moving basket underneath',
     'tilt_deg':TILT,'cup_bottom_center_y_mm':CY,
     'cup_rim_center_y_mm':round(CY-H*math.sin(TH),1),
     'ring_percent_under_center_table':ring_pts,
     'est_bottle_cg_y_old_v12_mm':round(old_mass_y,1),'est_bottle_cg_y_new_v13_mm':round(new_mass_y,1),
     'bottle_cg_shift_inward_mm':round(new_mass_y-old_mass_y,1),
     'bottle_model_diameter_mm':80,'bottle_model_height_mm':220,
     'bottle_insertion_step_mm':5,'bottle_lift_test_max_mm':220,
     'bottle_max_tray_intersection_mm3':max(x['bottle_vs_tray_mm3'] for x in fit),
     'bottle_max_holder_intersection_mm3':max(x['bottle_vs_holder_mm3'] for x in fit),
     'saddle_fit_tray_max_intersection_mm3':max(x[1] for x in clip),
     'stl_single_component':len(m.split())==1,'stl_watertight':bool(m.is_watertight),
     'print_bbox_xyz_mm':[round(float(a),2) for a in m.extents],
     'theoretical_PETG_mass_g':round(float(m.volume*1.27/1000),1),
     'cautions':['Actual PETG 500g load strength, shaking and tripod tipping not certified',
      'When cup is partly under table, at max realistic bottle diameter, angled 15deg OUTWARD rather than inward is necessary to preserve straight insertion. This is a geometry compromise.',
      'Saddle has no positive slip-out latch',
      'Physical PETG print-fit and removal of support untested.']}
(CHECK/'fit_results.json').write_text(json.dumps(rep,indent=2,ensure_ascii=False),encoding='utf-8')
(CHECK/'bottle_insertion_5mm.json').write_text(json.dumps(fit,indent=2,ensure_ascii=False),encoding='utf-8')
(CHECK/'saddle_slide_3mm.json').write_text(json.dumps(clip,indent=2),encoding='utf-8')
shutil.copyfile(__file__,ROOT/'generate_v13.py')
(ROOT/'README_印刷前に確認.md').write_text(f'''# カップホルダーv1.3：テーブル下へ大幅移動

今回の修正：中央テーブルv0.9の前縁はY=-81mmです。カップの下部中心をY={CY}mm、上部リング中心をY={CY-H*math.sin(TH):.1f}mmとし、底部は概ね半分をテーブル下へ移しました。従来v1.2では下部中心Y=-146mmでした。カップ底部の高さZ={CZ}mmは旧版と同じです。

**重要：** テーブルと干渉せず500mlペットボトルを出し入れするため、カップは**15°前方（外側）へ傾斜**しています。以前の6.5°内向きでは「半分をテーブル下」かつ「同じ高さ」ではボトルがテーブルにぶつかります。今回、カップ/ボトルの重心は概ね旧版よりテーブル側へ約{new_mass_y-old_mass_y:.0f}mm近付きますが、傾斜自体は外向きです。

- カップ内径：83mm（旧85mm）。外径93mm、網形状のまま。
- 接続：v1.2と同じ113mm幅のU字サドル（v0.9テーブル厚6mm用）。ネジや小さな別体パーツなし。
- 500ml想定モデル：直径80mm、高さ220mm。着座〜220mm引き上げの間を5mm刻みでCAD照合し、ボトル/テーブル/保持部の干渉ゼロ。
- v0.9中央天板模擬体との差し込み経路を検査済み。実物での嵌合/耐荷重は未検証。
- STL：`STL/{FN}_AD5M_PETG.stl` だけ印刷すればよい。STEPと生成Pythonも同梱。
- Flashforge Adventurer 5M 0.4mmノズル PETG、0.2mm積層、外周4〜5周、ブリム4〜6mm。カップ底が接地する向きに調整済み。
- U字サドルの突き出しにはサポートが必要になる場合があります。スライサーのレイヤープレビューで確認し、取り外し時は薄い部位に力を掛けないこと。
- 保持力・固定クリップの抜け止め・飲料入り500g静荷重・三脚の転倒は未検証。初回は安全な場所で空ボトルから。
''',encoding='utf8')
ZIP=Path('/mnt/data/ArrowsAlpha_CUP_v13_BACKSHIFT_HALF_UNDER_TABLE.zip')
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(ROOT))
print('SUCCESS',ZIP,ZIP.stat().st_size)
