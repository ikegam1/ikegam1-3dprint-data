"""PETG removable top-down joint stabilizers for authentic wooden Molkkaari frames.

Print with roof on build plate (STL opening faces upward); after printing,
flip the part and lower it over the wooden joint. Units: millimeters.
Requires cadquery, shapely, numpy, trimesh, matplotlib for preview.
"""
from pathlib import Path
import math, os, json, zipfile
import cadquery as cq
from shapely.geometry import LineString, Polygon
from shapely.affinity import translate as geo_translate
import trimesh
import numpy as np

ROOT=Path('/mnt/data/Molkkaari_Original_JointCovers_PETG')
ROOT.mkdir(exist_ok=True)
WALL=2.0            # Wall and roof thickness
LENGTH=50.0         # Distance outward from virtual hinge intersection on each member
RELIEF_LENGTH=8.0   # Hinge pocket extends 8 mm each way
RELIEF_EXTRA=1.3    # Additional clearance for hinge tape near junction

# nominal thickness / outer height / clearance over nominal wood thickness
SIZES={
  'Tactic_18mm': {'nominal_w':18.,'height':33.,'clearances':[0.6,1.2]},
  'Other_17mm': {'nominal_w':17.,'height':30.,'clearances':[0.6,1.2]},
}

def make_path(turn_deg):
    # Incoming member x negative, outgoing member rotated clockwise by turn_deg.
    a=math.radians(turn_deg)
    return [(-LENGTH, 0.0), (0.0, 0.0), (LENGTH*math.cos(a), -LENGTH*math.sin(a))]

def extend_line(path, extra):
    x0,y0=path[0]; x1,y1=path[1]; x2,y2=path[2]
    ux=x1-x0; uy=y1-y0; d=math.hypot(ux,uy); ux/=d; uy/=d
    vx=x2-x1; vy=y2-y1; d=math.hypot(vx,vy); vx/=d; vy/=d
    return [(x0-ux*extra,y0-uy*extra),path[1],(x2+vx*extra,y2+vy*extra)]

def hinge_path(path):
    x0,y0=path[0]; x1,y1=path[1]; x2,y2=path[2]
    p0=(x1+(x0-x1)*RELIEF_LENGTH/LENGTH,y1+(y0-y1)*RELIEF_LENGTH/LENGTH)
    p2=(x1+(x2-x1)*RELIEF_LENGTH/LENGTH,y1+(y2-y1)*RELIEF_LENGTH/LENGTH)
    return [p0, path[1], p2]

def prism_from_polygon(shape,h,z=0):
    assert shape.geom_type=='Polygon', shape.geom_type
    pts=list(shape.exterior.coords)[:-1]
    return cq.Workplane('XY').workplane(offset=z).polyline(pts).close().extrude(h)

def make_cover(turn_deg, wood_w=18., cap_h=33., clearance=0.6):
    assert turn_deg in (0,45)
    path=make_path(turn_deg)
    inner_w=wood_w+clearance
    # continuous U-channel: ceiling 2 mm, side walls 2 mm, open ends.
    outside=LineString(path).buffer(inner_w/2+WALL, cap_style='flat', join_style='mitre')
    inside=LineString(extend_line(path,3)).buffer(inner_w/2, cap_style='flat', join_style='mitre')
    # create roof in print position 0-2 mm, and full side walls reaching 33 mm
    full=prism_from_polygon(outside,cap_h)
    full=full.cut(prism_from_polygon(inside,cap_h-WALL+1,z=WALL))
    # local 1.3mm sidewall recess for original fabric hinge without reducing roof thickness
    relief=LineString(hinge_path(path)).buffer(inner_w/2+RELIEF_EXTRA, cap_style='flat',join_style='mitre')
    full=full.cut(prism_from_polygon(relief,cap_h-WALL+1,z=WALL))
    solid=full.combine().val()
    return solid

def export_solid(solid, directory, name):
    directory.mkdir(parents=True, exist_ok=True)
    p=directory/(name+'.stl')
    cq.exporters.export(solid, str(p), exportType='STL', tolerance=.08, angularTolerance=.12)
    return p

def main():
    summary=[]; exported=[]; models={}
    for group,info in SIZES.items():
        for clear in info['clearances']:
            inner_w=info['nominal_w']+clear
            if clear<1: sizekey='TIGHT'
            else: sizekey='EASY'
            sub=ROOT/group/sizekey
            code=f'{inner_w:.1f}mm'
            for angle, filelabel in [(0,'CENTER_180deg_x1'),(45,'CORNER_45deg_x2')]:
                name=f'MOLKKAARI_{filelabel}_{code}_H{int(info["height"])}_PETG'
                solid=make_cover(angle, info['nominal_w'], info['height'], clear)
                file=export_solid(solid,sub,name)
                mesh=trimesh.load_mesh(file,process=True)
                bounds=mesh.bounds
                valid=mesh.is_watertight and mesh.is_winding_consistent and mesh.body_count==1
                assert valid, (name, mesh.is_watertight,mesh.is_winding_consistent,mesh.body_count)
                assert abs(bounds[1,2]-info['height'])<.01, bounds
                dims=mesh.extents
                assert max(dims[:2])<220, (name,dims)
                summary.append({'file':str(file.relative_to(ROOT)), 'angle':angle,'wood_width':info['nominal_w'], 'clearance':clear,'inner_width':round(inner_w,2), 'height':info['height'], 'size_xyz':np.round(dims,2).tolist(),'volume_cm3':round(mesh.volume/1000,2),'watertight':valid})
                models[(group,sizekey,angle)]=solid
                exported.append(file)
            # Test short 25 mm straight U-slot, same cross-section as the real design.
            test_name=f'FIT_TEST_{code}_H{int(info["height"])}_print_first'
            test_path=[(-15.,0),(0.,0),(15.,0)]
            test_out=LineString(test_path).buffer(inner_w/2+WALL,cap_style='flat',join_style='mitre')
            test_in=LineString(extend_line(test_path,3)).buffer(inner_w/2,cap_style='flat',join_style='mitre')
            coupon=prism_from_polygon(test_out,info['height']).cut(prism_from_polygon(test_in,info['height']-WALL+1,z=WALL)).val()
            test_file=export_solid(coupon,sub,test_name)
            tm=trimesh.load_mesh(test_file)
            assert tm.is_watertight and tm.is_winding_consistent and tm.body_count==1
            exported.append(test_file)
    # Single plate with three part instances for recommended 18mm wood / tight slot.
    # Each part is in its designed support-free printing orientation, roof touching print bed.
    chosen=models[('Tactic_18mm','TIGHT',0)]
    corner=models[('Tactic_18mm','TIGHT',45)]
    platepieces=[]
    for solid,x,y in [(chosen,110,42),(corner,56,126),(corner,162,126)]:
        translated=solid.translate((x,y,0))
        platepieces.append(translated)
    assembly=cq.Assembly(name='MOLKKAARI_FullSet_18.6mm')
    for i,solid in enumerate(platepieces):
        assembly.add(solid,name=('Straight' if i==0 else f'Corner_{i}'))
    combined=cq.Compound.makeCompound(platepieces)
    oneplate=ROOT/'MOLKKAARI_TACTIC_18mm_3PIECES_220mm_plate.stl'
    cq.exporters.export(combined,str(oneplate),exportType='STL',tolerance=.08,angularTolerance=.12)
    mm=trimesh.load_mesh(oneplate,process=True)
    assert mm.is_watertight and mm.body_count==3
    assert mm.bounds[0,0]>3 and mm.bounds[0,1]>3 and mm.bounds[1,0]<217 and mm.bounds[1,1]<217, mm.bounds
    summary.append({'file':oneplate.name,'count':3,'size_xyz':np.round(mm.extents,2).tolist(),'bounds':np.round(mm.bounds,2).tolist(),'watertight':True})
    # export editable STEP of recommended pair (works even if other dimensions need adjustment)
    for angle,label in [(0,'CENTER_180deg'),(45,'CORNER_45deg')]:
        p=ROOT/f'EDITABLE_TACTIC_18mm_{label}.step'
        cq.exporters.export(models[('Tactic_18mm','TIGHT',angle)],str(p))
        exported.append(p)
    (ROOT/'geometry_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary,models

if __name__=='__main__':
    sm, models=main()
    for m in sm:
        print(m['file'], 'size:',m['size_xyz'], 'watertight:',m['watertight'])
