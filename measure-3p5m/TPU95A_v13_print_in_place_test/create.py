"""Print-in-place captive hinge TEST ONLY, TPU95A / 0.8mm nozzle.
Print on edge. Final measuring length is NOT validated.
"""
import cadquery as cq
from cadquery import Vector,exporters
import trimesh
from pathlib import Path
import json,math
ROOT=Path(__file__).parent
W_Z=8.0; TH_Y=1.6
PIN_R=1.55; OUTER_HEAD_R=3.30; INNER_R=2.45; RING_R=4.35
RING_BOTTOM=1.7; RING_TOP=5.55; BOTTOM_CAP_H=0.85
TOP_CONE_START=5.95; TOP_CONE_HEIGHT=1.45; TOP_CAP_THICK=0.60
RAIL_HALF=62.0; RAIL_END=5.1; RAIL_Y_OFFSET=-1.15
def box(l,w,h,x,y,z):
    return cq.Workplane('XY').box(l,w,h).translate((x,y,z)).val()
def ring_side():
    sh=box(RAIL_HALF-RAIL_END,TH_Y,W_Z,-(RAIL_HALF+RAIL_END)/2,RAIL_Y_OFFSET,W_Z/2)
    ann=cq.Workplane('XY').circle(RING_R).circle(INNER_R).extrude(RING_TOP-RING_BOTTOM).translate((0,0,RING_BOTTOM)).val()
    sh=sh.fuse(ann)
    sh=sh.fuse(box(2.7,TH_Y,RING_TOP-RING_BOTTOM,-4.6,-.70,(RING_BOTTOM+RING_TOP)/2))
    for deg in (55,125,235,305):
        a=math.radians(deg);rr=4.75
        sh=sh.fuse(box(1.08,1.08,RING_BOTTOM+.12,rr*math.cos(a),rr*math.sin(a),(RING_BOTTOM+.12)/2))
    return sh.clean()
def pin_side():
    sh=box(RAIL_HALF-RAIL_END,TH_Y,W_Z,(RAIL_HALF+RAIL_END)/2,RAIL_Y_OFFSET,W_Z/2)
    sh=sh.fuse(cq.Workplane('XY').circle(PIN_R).extrude(7.95).val())
    sh=sh.fuse(cq.Workplane('XY').circle(OUTER_HEAD_R).extrude(BOTTOM_CAP_H).val())
    sh=sh.fuse(cq.Solid.makeCone(PIN_R,OUTER_HEAD_R,TOP_CONE_HEIGHT,Vector(0,0,TOP_CONE_START),Vector(0,0,1)))
    sh=sh.fuse(cq.Workplane('XY').workplane(offset=TOP_CONE_START+TOP_CONE_HEIGHT).circle(OUTER_HEAD_R).extrude(TOP_CAP_THICK).val())
    sh=sh.fuse(box(2.65,1.4,BOTTOM_CAP_H,4.20,-.70,BOTTOM_CAP_H/2))
    sh=sh.fuse(box(2.65,1.4,TOP_CAP_THICK,4.20,-.70,TOP_CONE_START+TOP_CONE_HEIGHT+TOP_CAP_THICK/2))
    return sh.clean()
def export_shape(shape,file):
    exporters.export(shape,str(ROOT/file),tolerance=.055,angularTolerance=.20)
    m=trimesh.load_mesh(ROOT/file)
    info=dict(file=file,watertight=m.is_watertight,parts=len(m.split()),triangles=len(m.faces),dimensions=[round(float(x),3) for x in m.extents])
    assert info['watertight'] and max(m.extents)<=220
    return info
L=ring_side();R=pin_side()
assert L.isValid() and R.isValid() and L.intersect(R).Volume()<1e-5
pair=cq.Compound.makeCompound([L,R])
q=[export_shape(pair,'PRINT_FIRST_2_RAILS_CAPTIVE_HINGE_0p8_TPU.stl')]
q.append(export_shape(L.translate(Vector(73,9,0)),'REFERENCE_LEFT_RING_WITH_BREAKAWAY_SUPPORTS.stl'))
q.append(export_shape(R.translate(Vector(73,9,0)),'REFERENCE_RIGHT_HEAD_PIN.stl'))
center=R.fuse(ring_side().translate(Vector(80,0,0))).clean()
third=pin_side().translate(Vector(80,0,0))
assert len(center.Solids())==1 and L.intersect(center).Volume()<1e-5 and center.intersect(third).Volume()<1e-5
q.append(export_shape(cq.Compound.makeCompound([L,center,third]),'SECOND_TEST_3_RAILS_TWO_CAPTIVE_HINGES.stl'))
exporters.export(pair,str(ROOT/'EDITABLE_PIN_AND_RING_IN_PRINT_POSITION.step'),exportType='STEP')
(ROOT/'DESIGN_VALIDATION.json').write_text(json.dumps({'printer':'Adventurer 5M','material':'TPU95A','nozzle_mm':0.8,'experimental':True,'print_in_place':True,'CAD_validation':q,'caveat':'Printed pivot may fuse; cut the tiny sacrificial supports and verify free rotation.'},ensure_ascii=False,indent=2),encoding='utf-8')
print(q)
