"""Molkkaari v11.1: 4 PETG-only modules (6+5+5+5), integrated connectors.
Unverified prototype. No detached connectors. The full length 3500mm is NOMINAL.
A printed side-edge rail: large planar strip on its 1.4-mm-thick edge.
"""
from pathlib import Path
import cadquery as cq
from cadquery import Vector as V
import numpy as np, json, trimesh
ROOT=Path(__file__).resolve().parents[1]
DPRO=ROOT/'01_PRODUCTION_STL'; DTEST=ROOT/'02_FIRST_TEST_STL'; DCAD=ROOT/'03_CAD'
for p in [DPRO,DTEST,DCAD]:p.mkdir(exist_ok=True,parents=True)
P=3500/21 # 21 reference pitches = 3,500 mm
W=11.5; T=1.4; BZ=4.4 # main strip occupies z=4.4..5.8 in its assembled orientation
R=1.65; JH=5.8; ZC=2.9
INNER_EAR=2.05; OUTER_EAR=5.75

def b(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def cy_y(r,x,y0,y1,z):return cq.Solid.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))
def cone_y(r0,r1,x,y0,y1,z):return cq.Solid.makeCone(r0,r1,y1-y0,V(x,y0,z),V(0,1,0))
def cy_z(r,x,y,z0,z1):return cq.Solid.makeCylinder(r,z1-z0,V(x,y,z0),V(0,0,1))
def ramp(coords,w=W,ym=0):return cq.Workplane('XZ').polyline(coords).close().extrude(w/2,both=True).translate((0,ym,0)).val()
def polygon(points,height):return cq.Workplane('XY').polyline(points).close().extrude(height).val()
def union(*ss):
 s=ss[0]
 for o in ss[1:]:s=s.fuse(o)
 return s.clean()
def locate_hinge(s,side):
 # local hinge has strap in 0..1.4 and jaw in 0..5.
 # up: strap 4.4..5.8, joint centre 6.9
 # down: reflected strap 4.4..5.8, joint centre 3.3
 if side=='TOP':return s.translate(V(0,0,BZ))
 if side=='BOTTOM':return s.mirror('XY').translate(V(0,0,BZ+T))
 raise ValueError(side)

def female_hinge(side,hole=R):
 # Wide, fully supported eyelets. Open diagonal keyways allow side/upper insertion
 # of a constant-diameter cylinder WITHOUT bending either arm. The closed hole
 # on the left (-x) bears load when the measurement strip is pulled straight.
 s=union(b(-5.4,21.0,-OUTER_EAR,-INNER_EAR,0,JH),b(-5.4,21.0,INNER_EAR,OUTER_EAR,0,JH),
  b(13,35,-OUTER_EAR,-INNER_EAR,0,T),b(13,35,INNER_EAR,OUTER_EAR,0,T))
 # Diagonal travel channel from the pivot to TOP edge; width ~3.05 for
 # diameter 2.70 male peg. No forced snap, no protruding heads.
 # Polygon is widened to guarantee there is an entry from outside at z>5.
 path=[(-.58,4.26),(.58,1.54),(8.0,4.65),(6.55,7.60)]
 for y in (-OUTER_EAR-.2,INNER_EAR-.2):
  s=s.cut(cy_y(hole,0,y,y+(OUTER_EAR-INNER_EAR)+.4,ZC))
  slit=cq.Workplane('XZ').polyline(path).close().extrude((OUTER_EAR-INNER_EAR)+.4).val()
  bb=slit.BoundingBox()
  # Workplane XZ extrudes toward -y. Put y extent precisely across this ear.
  slit=slit.translate(V(0, y-bb.ymin, 0))
  s=s.cut(slit)
 return locate_hinge(s.clean(),side)

def male_hinge(side,a=P):
 # Two straight short pivot barrels integrated with heavy solid forks.
 # Older v11's conical mushroom tips snapped off during support removal / assembly.
 # No spherical caps, no tiny neck, no PETG deflection to insert.
 # Outer pin face lies on the printing bed in the standard edge-down layout.
 left_arm=union(b(a-35,a-20,-1.83,-.14,0,2.4), b(a-19,a+1.4,-1.83,-.14,0,JH),
   ramp([(a-39,0),(a-39,T),(a-19,2.5),(a-10,JH),(a+1.4,JH),(a+1.4,0)],1.69,(-1.83-.14)/2))
 right_arm=union(b(a-35,a-20,.14,1.83,0,2.4), b(a-19,a+1.4,.14,1.83,0,JH),
   ramp([(a-39,0),(a-39,T),(a-19,2.5),(a-10,JH),(a+1.4,JH),(a+1.4,0)],1.69,(.14+1.83)/2))
 g1=polygon([(a-42,-W/2),(a-22,-1.83),(a-42,-1.83)],2.8)
 g2=polygon([(a-42,W/2),(a-22,1.83),(a-42,1.83)],2.8)
 pin_r=1.35
 s=union(left_arm,right_arm,g1,g2,
  cy_y(pin_r,a,-5.75,-1.83,ZC),
  cy_y(pin_r,a,1.83,5.64,ZC))
 return locate_hinge(s,side)

def male_quick(side,a=P):
 # integrated mushroom for keyhole link; no flexing required
 s=union(b(a-34,a+3.0,-W/2,W/2,0,T),
     cy_z(1.15,a,0,T,3.85),cy_z(2.15,a,0,3.85,4.90))
 return locate_hinge(s,side)

def female_quick(side):
 # keyhole mouth x=+9, seating x=0, slides out by pushing modules together 9mm.
 pad=b(-4.8,15.0,-5.35,5.35,1.60,3.45)
 slot=b(0,9,-1.36,1.36,1.40,3.95)
 slot=union(slot,cy_z(1.36,0,0,1.40,3.95),cy_z(2.38,9,0,1.40,3.95))
 pad=pad.cut(slot)
 tapered=ramp([(13.5,1.50),(13.5,3.45),(33,T),(33,0),(26,0)])
 return locate_hinge(union(pad,tapered),side)

def rail(kind,hole=R):
 left,right=kind.split('_')
 x0=0 if left=='START' else (20 if left in ('TOP','BOTTOM') else 19)
 x1=P if right=='END' else (P-25 if right in ('TOP','BOTTOM') else P-19)
 s=b(x0,x1,-W/2,W/2,BZ,BZ+T)
 if left in ('TOP','BOTTOM'):s=s.fuse(female_hinge(left,hole))
 if right in ('TOP','BOTTOM'):s=s.fuse(male_hinge(right))
 if left in ('QLOW','QHIGH'):s=s.fuse(female_quick('BOTTOM' if left=='QLOW' else 'TOP'))
 if right in ('QLOW','QHIGH'):s=s.fuse(male_quick('BOTTOM' if right=='QLOW' else 'TOP'))
 return s.clean()

def print_orientation(s):
 # Unlike previous long bridge failures, print on the 194mm x 1.4mm strip EDGE.
 # X direction stays ~194mm on bed. Transverse hinge bores print vertically.
 # Side-face of main strap y=-5.75 is now the flat bed-contacting face.
 s=s.rotate((0,0,0),(1,0,0),90)
 bnd=s.BoundingBox()
 s=s.translate(V(110-(bnd.xmin+bnd.xmax)/2,110-(bnd.ymin+bnd.ymax)/2,-bnd.zmin))
 return s

def save(name,s,folder,step=False,expected=1):
 file=folder/(name+'.stl');cq.exporters.export(s,str(file),exportType='STL',tolerance=.052,angularTolerance=.13)
 m=trimesh.load(file,force='mesh',process=True)
 assert m.is_watertight,(name,'open mesh')
 assert len(m.split(only_watertight=False))==expected,(name,'wrong component count')
 assert all(m.extents<220.01),(name,'does not fit 220')
 assert m.bounds[0,2] > -0.01 and m.bounds[0,0]>=0 and m.bounds[0,1]>=0,(name,'off bed')
 assert m.bounds[1,0]<=220.01 and m.bounds[1,1]<=220.01,(name,'off bed')
 if step:cq.exporters.export(s,str(DCAD/(name+'.step')),exportType='STEP')
 return {'parts':expected,'xyz_extent_mm':np.round(m.extents,2).tolist(),'watertight':bool(m.is_watertight),'faces':len(m.faces)}

COUNT={'START_TOP':1,'TOP_BOTTOM':8,'BOTTOM_TOP':5,'TOP_QLOW':1,'QLOW_TOP':1,'BOTTOM_QHIGH':2,'QHIGH_TOP':2,'BOTTOM_END':1}
raw={};checks={}
for kind,count in COUNT.items():
 sh=rail(kind);raw[kind]=sh
 name='V111_'+kind+'_PRINT_'+str(count)+'X'
 checks[name]=save(name,print_orientation(sh),DPRO,step=True)

# realistic two-piece short-end trial coupons, each printed on its side
trial_left=rail('START_TOP').intersect(b(P-65,P+8,-7,7,0,11)).clean()
trial_right=rail('TOP_END').intersect(b(-8,65,-7,7,0,11)).clean()
trial_left=print_orientation(trial_left).translate(V(-40,0,0))
trial_right=print_orientation(trial_right).translate(V(40,0,0))
checks['HINGE_TEST']=save('TEST1_NEW_SLIDE_HINGE_TWO_PIECES_EDGE_DOWN',cq.Compound.makeCompound([trial_left,trial_right]),DTEST,expected=2)
# A second pair is essential: bottom-facing male and female have a different hinge axis.
trial_bottom_left=rail('TOP_BOTTOM').intersect(b(P-65,P+8,-7,7,0,11)).clean()
trial_bottom_right=rail('BOTTOM_END').intersect(b(-8,65,-7,7,0,11)).clean()
trial_bottom_left=print_orientation(trial_bottom_left).translate(V(-40,0,0))
trial_bottom_right=print_orientation(trial_bottom_right).translate(V(40,0,0))
checks['HINGE_BOTTOM_TEST']=save('TEST1B_BOTTOM_SLIDE_HINGE_TWO_PIECES_EDGE_DOWN',cq.Compound.makeCompound([trial_bottom_left,trial_bottom_right]),DTEST,expected=2)
for side,kt,st in [('LOW','TOP_QLOW','QLOW_TOP'),('HIGH','BOTTOM_QHIGH','QHIGH_TOP')]:
 quick_l=rail(kt).intersect(b(P-65,P+8,-7,7,0,11)).clean()
 quick_r=rail(st).intersect(b(-8,65,-7,7,0,11)).clean()
 quick_l=print_orientation(quick_l).translate(V(-40,0,0))
 quick_r=print_orientation(quick_r).translate(V(40,0,0))
 checks['QUICK_TEST_'+side]=save('TEST2_QUICK_'+side+'_TWO_PIECES_EDGE_DOWN',cq.Compound.makeCompound([quick_l,quick_r]),DTEST,expected=2)

# v2.3 PETG body cavity fit gauge (sample, no separate part required for the product)
stor=b(0,45,-5.8,5.8,0,26.0)
checks['FIT_SAMPLE']=save('TEST3_STORAGE_FIT_GAUGE_45x11p6x26',stor.translate(V(10,10,0)),DTEST)

# Geometric test: keyhole link at x0 aligned with mushroom, no interference when fully seated.
qvol={}
for side in ('TOP','BOTTOM'):
 v=male_quick(side,P).translate(V(-P,0,0)).intersect(female_quick(side)).Volume()
 assert v<.05,('quick link unintentional collision',side,v)
 qvol[side]=v

# 3D articulation check: hinge axes alternate ABOVE/BELOW the strip, avoiding 3rd-on-1st overlap.
# Bundle sequences for four cavities in v2.3 (outer 207mm; inner 186mm).
MODULES={
 'A_LEFT_6':['START_TOP','TOP_BOTTOM','BOTTOM_TOP','TOP_BOTTOM','BOTTOM_TOP','TOP_QLOW'],
 'B_MIDDLE_5':['QLOW_TOP','TOP_BOTTOM','BOTTOM_TOP','TOP_BOTTOM','BOTTOM_QHIGH'],
 'C_MIDDLE_5':['QHIGH_TOP','TOP_BOTTOM','BOTTOM_TOP','TOP_BOTTOM','BOTTOM_QHIGH'],
 'D_RIGHT_5':['QHIGH_TOP','TOP_BOTTOM','BOTTOM_TOP','TOP_BOTTOM','BOTTOM_END']
}
mod_validation={};mod_shapes={}
for mname,seq in MODULES.items():
 folded=[];zoff=0.0; prev_off=0.0
 for i,typ in enumerate(seq):
  if i:
   pivot=(BZ+ZC if i%2 else BZ+T-ZC)
   ps=(-1)**(i-1);ns=(-1)**i
   zoff=ps*pivot+prev_off-ns*pivot
  prev_off=zoff
  sh=raw[typ]
  if i%2:sh=sh.rotate((0,0,0),(0,1,0),180).translate(V(P,0,zoff))
  else:sh=sh.translate(V(0,0,zoff))
  folded.append(sh)
 collisions=[];adjoin_collisions=[]
 for i in range(len(seq)):
  for j in range(i+1,len(seq)):
   vol=folded[i].intersect(folded[j]).Volume()
   if j==i+1:
    if vol>10:
     cb=folded[i].intersect(folded[j]).BoundingBox()
     adjoin_collisions.append((i+1,j+1,round(vol,3),[round(cb.xmin,2),round(cb.xmax,2),round(cb.ymin,2),round(cb.ymax,2),round(cb.zmin,2),round(cb.zmax,2)]))
   elif vol>.05:
    cb=folded[i].intersect(folded[j]).BoundingBox()
    collisions.append((i+1,j+1,round(vol,3),[round(cb.xmin,2),round(cb.xmax,2),round(cb.ymin,2),round(cb.ymax,2),round(cb.zmin,2),round(cb.zmax,2)]))
 assert not collisions,(mname,collisions)
 bb=cq.Compound.makeCompound(folded).BoundingBox()
 dims=[round(bb.xlen,3),round(bb.ylen,3),round(bb.zlen,3)]
 cavity=207. if mname in ('A_LEFT_6','D_RIGHT_5') else 186.
 assert dims[0] < cavity and dims[1]<13.6 and dims[2]<30.6,(mname,dims,'does not fit')
 mod_validation[mname]={'sequence':seq,'folded_cad_bbox_mm':dims,'cavity_length_mm':cavity,
 'nonadjacent_overlap_mm3':collisions,'adjacent_large_interference':adjoin_collisions}
 mod_shapes[mname]=folded
 print('FOLDED',mname,dims,'CAVITY',cavity,'ADJ',adjoin_collisions)

# intermediate-angle solid interference test (joint interference > small snap geometry is unsafe)
angle_check={}
for side,kind_l,kind_r in [('TOP','START_TOP','TOP_END'),('BOTTOM','TOP_BOTTOM','BOTTOM_END')]:
 left_sh=raw[kind_l]; right_sh=raw[kind_r] if kind_r in raw else rail(kind_r)
 pv=BZ+ZC if side=='TOP' else BZ+T-ZC
 data={}
 for ang in (0,30,45,60,90,120,135,150,180):
  adjacent=right_sh.translate(V(P,0,0)).rotate((P,0,pv),(P,1,pv),ang*(-1 if side=='TOP' else 1))
  ci=left_sh.intersect(adjacent);vol=ci.Volume()
  if ang==180:
   if vol>1e-5:
    cb=ci.BoundingBox(); print('180_COLLISION',side,round(vol,5),[round(v,3) for v in [cb.xmin,cb.xmax,cb.ymin,cb.ymax,cb.zmin,cb.zmax]])
   else: print('180_COLLISION',side,'none')
  data[str(ang)]=round(vol,4)
 print('ANGLE_INTERSECTIONS',side,data)
 angle_check[side]=data
records={'printer':'Flashforge Adventurer 5M','material':'PETG only',
'accuracy':'nominal, not physically calibrated','ruler_design_distance_mm':3500,
'section_reference_pitch_mm':P,'module_count':4,'pieces_per_module':[6,5,5,5],
'no_separate_joints':True,'rail_width_mm':W,'rail_thickness_mm':T,
'female_hinge_outer_width_mm':2*OUTER_EAR,'hinge_axis_top_bottom_z_mm':[6.9,3.3],
'body_cavity_reference_mm':{'outer':[207,13.6,30.6],'inner':[186,13.6,30.6]},
'CAD_folded_module_checks':mod_validation,'hinge_angle_interference_mm3':angle_check,'quick_connector_collision_mm3':qvol,
'printer_check':checks,'kinds_counts':COUNT,
'not_physically_tested':['fit and removal','fatigue after folding','hand tolerance on quick keyhole',
'storage retention when lifted (middle bars have no clips)','storage fit in particular printed body','actual measured 3500mm']}
(DCAD/'validation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps(records,ensure_ascii=False,indent=2))
