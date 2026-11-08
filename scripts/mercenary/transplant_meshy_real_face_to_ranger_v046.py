#!/usr/bin/env python3
"""Genesis V046 - REAL Meshy adult face transplant onto original Quaternius Ranger.
Source face: original CC0 MesHy Weary Medieval Warrior GLB actual PBR skin,
not a concept/picture. Keep original verified 65-joint Quaternius Ranger,
hands and outfits. Head source is unrigged: facial mesh weights rigidly to
the existing Head bone. Experimental until visual QA. No main changes.
"""
import argparse,sys,json,hashlib,math
from pathlib import Path
import bpy,bmesh
from mathutils import Matrix,Vector

p=argparse.ArgumentParser()
for x in ('ranger','meshy','hdri','out'):p.add_argument('--'+x,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(a.ranger)=='fc1baff512c38a59660f7240b0da9e4a2bd19d038ccd055357b3635572fed7b4'
assert sha(a.meshy)=='0452096d35bb41d992bc3508ee05f9cdc2a6ee34bb472a60c33eb9b22b66f005'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.ranger.resolve()))
ranger_meshes=[o for o in bpy.data.objects if o.type=='MESH']
ranger_names=[o.name for o in ranger_meshes]
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(arms)==1 and len(arms[0].data.bones)==65
arm=arms[0]
assert {'Head','neck_01','hand_l','hand_r','thumb_01_r','thumb_01_l'}<=set(x.name for x in arm.data.bones)
old_face=next((o for o in ranger_meshes if o.name.startswith('GENESIS_V045_BASE_MALE_REAL_FACE_AND_NECK')),None)
assert old_face
old_eyes=next((o for o in ranger_meshes if o.name.startswith('GENESIS_V045_BASE_MALE_EYES')),None)
old_brows=next((o for o in ranger_meshes if o.name.startswith('GENESIS_V045_BASE_MALE_EYEBROWS')),None)
assert old_eyes and old_brows

def bounds_world(obj):
 co=[obj.matrix_world@v.co for v in obj.data.vertices]
 return Vector([min(v[i] for v in co) for i in range(3)]),Vector([max(v[i] for v in co) for i in range(3)])
old_lo,old_hi=bounds_world(old_face)
print('V046_ORIGINAL_RANGER_HEAD_BOUNDS',list(old_lo),list(old_hi),flush=True)
# Hide original fake looking eyeballs/brows; keep only original facial mesh as a
# lower-priority backing at first, to be inspected in the actual render.
for o in [old_eyes,old_brows]:
 bpy.data.objects.remove(o,do_unlink=True)
# Original skull backing may show through cropped source face; hide it during
# frontal visual review, retain in Blender only as a diagnostic if desired.
old_face.hide_render=True
old_face.hide_viewport=True

bpy.ops.import_scene.gltf(filepath=str(a.meshy.resolve()))
sources=[o for o in bpy.data.objects if o.type=='MESH' and o not in ranger_meshes]
assert len(sources)==1
src=sources[0]
assert len(src.data.vertices)==9277
bpy.ops.object.select_all(action='DESELECT');src.select_set(True)
bpy.context.view_layer.objects.active=src
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
minz=min(v.co.z for v in src.data.vertices)
src.location.z-=minz
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
assert 1.95<max(v.co.z for v in src.data.vertices)<2.06
source_bounds=bounds_world(src)
print('V046_SOURCE_MESHY_BOUNDS',*[list(x) for x in source_bounds],flush=True)

# Retain original source PBR mesh polygons strictly from face-front region.
# Original meshes use Blender axes Z-up, toward -Y (same as Ranger).
bm=bmesh.new();bm.from_mesh(src.data)
bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
before_faces=len(bm.faces)
crop=dict(xmax=.138,zlo=1.665,zhi=1.948,ylo=-.265,yhi=-.050)
drop=[]
for f in bm.faces:
 ok=all(abs(v.co.x)<crop['xmax']
        and crop['zlo']<v.co.z<crop['zhi']
        and crop['ylo']<v.co.y<crop['yhi'] for v in f.verts)
 if not ok:drop.append(f)
bmesh.ops.delete(bm,geom=drop,context='FACES')
unlinked=[v for v in bm.verts if not v.link_faces]
if unlinked:bmesh.ops.delete(bm,geom=unlinked,context='VERTS')
face_count=len(bm.faces);vert_count=len(bm.verts)
print('V046_SOURCE_FACE_GEOMETRY',face_count,vert_count,'original_faces',before_faces,flush=True)
assert 45<face_count<1400 and 50<vert_count<1900, ('no authentic face geometry in crop',face_count,vert_count)
bm.to_mesh(src.data);bm.free();src.data.update()
src.name='GENESIS_V046_AUTHENTIC_MESHY_MATURE_FACE'
raw_lo,raw_hi=bounds_world(src)
# Target center: old face region minus its bottom-neck area (already removed).
target_center=(old_lo+old_hi)*.5
src_center=(raw_lo+raw_hi)*.5
ref_width=old_hi.x-old_lo.x
source_width=raw_hi.x-raw_lo.x
scale=max(.68,min(1.33,ref_width/max(.001,source_width)*.95))
# Display 2% in front of original nose. Actual nose will vary; original
# Quaternius face backing is excluded from exported asset to avoid wax.
target_center.y=old_lo.y+.020+(raw_hi.y-raw_lo.y)*scale*.5
target_center.z+=.010
src.matrix_world=Matrix.Translation(target_center) @ Matrix.Scale(scale,4) @ Matrix.Translation(-src_center)
print('V046_TRUE_FACE_TRANSFORM',list(target_center),'scale',scale,'source crop',[list(raw_lo),list(raw_hi)],flush=True)

# Attach these genuine PBR face polygons to the original Quaternius skeleton.
# Source has no skin; for one rigid head section, Head is anatomically proper.
for vg in list(src.vertex_groups):src.vertex_groups.remove(vg)
head_group=src.vertex_groups.new(name='Head')
head_group.add(list(range(len(src.data.vertices))),1.0,'REPLACE')
mw=src.matrix_world.copy()
src.parent=arm
src.matrix_world=mw
skin=src.modifiers.new('GENESIS_V046_ORIGINAL_65_BONE_SKIN','ARMATURE')
skin.object=arm
assert src.parent==arm and len(arm.data.bones)==65
assert len([o for o in bpy.data.objects if o.type=='ARMATURE'])==1
# If old face is removed, Meshy nose/cheeks MUST be self-contained. Keep
# diagnostic full-head view so missing portions cannot be silently omitted.
bpy.data.objects.remove(old_face,do_unlink=True)

newpath=a.out/'GENESIS_QUATERNIUS_RANGER_MESHY_MATURE_FACE_V046_EXPERIMENTAL.glb'
bpy.ops.object.select_all(action='DESELECT')
for o in [arm,src]+[bpy.data.objects.get(name) for name in ranger_names if bpy.data.objects.get(name) is not None]:
 o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(newpath.resolve()),export_format='GLB',
 use_selection=True,export_animations=False)
assert newpath.stat().st_size>2000000
print('V046_EXPORTED_REAL_MESHY_FACE_WITH_QUATERNIUS_RANGER_RIG',newpath.stat().st_size,flush=True)

scene=bpy.context.scene
scene.world=bpy.data.worlds.new('GENESIS_32BIT_EXR_V046')
w=scene.world;w.use_nodes=True
nd=w.node_tree.nodes;nd.clear();link=w.node_tree.links
env=nd.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96
bg=nd.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.75
ow=nd.new('ShaderNodeOutputWorld')
link.new(env.outputs['Color'],bg.inputs['Color'])
link.new(bg.outputs['Background'],ow.inputs['Surface'])
head_center=Vector(target_center)
pelvis=arm.matrix_world@arm.data.bones['pelvis'].head_local
middle=(head_center+pelvis)*.5
def aim(ob,pt):ob.rotation_euler=(pt-ob.location).to_track_quat('-Z','Y').to_euler()
def lamp(name,target,offset,power,size):
 data=bpy.data.lights.new(name,'AREA');obj=bpy.data.objects.new(name,data)
 scene.collection.objects.link(obj);obj.location=target+Vector(offset)
 aim(obj,target);data.energy=power;data.shape='DISK';data.size=size
lamp('QA_SOFT_KEY',middle,(-2.2,-2.2,2.2),575,2.9)
lamp('QA_RIM',middle,(2.2,2,1.7),340,2.5)
lamp('QA_FACE_SHADOW_FILL',head_center,(.02,-1.0,.16),110,1.0)
bpy.ops.mesh.primitive_plane_add(size=9,location=(0,0,-.04))
floor=bpy.context.object;floor.name='QA_FLOOR_NOT_EXPORTED'
mat=bpy.data.materials.new('QA_GREY');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.075,.080,.085,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
floor.data.materials.append(mat)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=36
scene.render.resolution_x=700;scene.render.resolution_y=880
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.2
renders=[]
def render(name,direction,focus,scale):
 camera_data=bpy.data.cameras.new(name+'_lens')
 cam=bpy.data.objects.new(name+'_camera',camera_data)
 scene.collection.objects.link(cam)
 cam.location=Vector(focus)+Vector(direction).normalized()*5
 aim(cam,Vector(focus));scene.camera=cam
 camera_data.type='ORTHO';camera_data.ortho_scale=scale
 dst=a.out/(name+'.png');scene.render.filepath=str(dst.resolve())
 bpy.ops.render.render(write_still=True)
 assert dst.stat().st_size>45000
 renders.append({'name':name+'.png','size':dst.stat().st_size})
render('V046_01_MESHY_FACE_ON_RANGER_FRONT',(.08,-1,.12),head_center,.81)
render('V046_02_MESHY_FACE_ON_RANGER_THREEQUARTER',(.7,-1,.12),head_center,.86)
render('V046_03_MESHY_FACE_ON_RANGER_FULL',(.14,-1,.15),middle,3.26)
render('V046_04_MESHY_FACE_ON_RANGER_SIDE',(.96,-.25,.09),head_center,.9)
qa={
 'status':'V046_MESHY_REAL_FACE_FIRST_GEOMETRY_FIT_EXPERIMENTAL_UNAPPROVED',
 'original_ranger_sha256':sha(a.ranger),'original_meshy_sha256':sha(a.meshy),
 'output_sha256':sha(newpath),'output_bytes':newpath.stat().st_size,
 'ranger_original_skin_bones':len(arm.data.bones),
 'source_meshy_original_triangles':before_faces,
 'source_face_selected_triangles':face_count,
 'source_face_selected_vertices':vert_count,
 'face_source_PBR_material':[m.name for m in src.data.materials],
 'face_rig_binding':'Head rigid original Ranger bone',
 'original_ranger_clothing_unchanged':True,
 'mesh_original_head_bones_unchanged':True,
 'source_face_crop_limits':crop,'face_fit_scale':scale,'face_fit_target':list(target_center),
 'renders':renders,'render_engine':'CYCLES','EXR_32bit_hdri':a.hdri.name,
 'visual_quality_verified':False,'no_geometry_holes_verified':False,
 'facial_animation_tested':False,'mixamo_tested':False,'sword_v12b_equipped':False,
 'shield_v015_equipped':False,'playcanvas_tested':False,
 'human_approved':False,'main_modified':False}
(a.out/'V046_ADULT_MESHY_FACE_QA.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False))
print('V046_REAL_MESHY_FACE_FITTING_RENDERED',json.dumps({'faces':face_count,'verts':vert_count,'renders':len(renders),'scale':scale}),flush=True)
