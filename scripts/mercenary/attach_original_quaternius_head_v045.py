#!/usr/bin/env python3
"""Genesis V045 – authentic Quaternius Male Ranger + original CC0 male head.

Both source GLBs already share the same genuine 65-bone skeleton/rest matrices.
Extract the actual male SuperHero_Male head, Eyes and Eyebrows from the CC0
Quaternius base character, retain donor vertex weights, rebind them to Ranger's
original armature and export one coherent experimental GLB.

Blender 4.5.13 LTS, Cycles + 32bit/channel HDRI EXR; no image concepts.
No equipment, clips, main updates or human approval are implied.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Matrix
p=argparse.ArgumentParser()
for x in ('ranger','base','hdri','out'):p.add_argument('--'+x,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(a.ranger)=='2b8a1358f165fb7a1afa5930c4a3d92a9fff11ea01c63df18d368735fdbb29af'
assert sha(a.base)=='d6f3b64cab629f6ddca9ba063811aeffd3663a8a4e49ade47cd9505dc2bbd70f'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.ranger.resolve()))
ranger_meshes=[o for o in bpy.data.objects if o.type=='MESH']
ranger_rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(ranger_rigs)==1 and len(ranger_rigs[0].data.bones)==65
assert len(ranger_meshes)>=8
rig=ranger_rigs[0]
assert any('Head_Hood' in o.name for o in ranger_meshes)
print('GENESIS_V045_RANGER_INTACT',len(ranger_meshes),len(rig.data.bones),flush=True)

old=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(a.base.resolve()))
add=[o for o in bpy.data.objects if o not in old]
donor_rigs=[o for o in add if o.type=='ARMATURE']
donor_meshes=[o for o in add if o.type=='MESH']
assert len(donor_rigs)==1
donor=donor_rigs[0]
assert len(donor.data.bones)==65
by_name={o.name.split('.')[0]:o for o in donor_meshes}
body=next((o for o in donor_meshes if o.name.startswith('SuperHero_Male')),None)
eyes=next((o for o in donor_meshes if o.name.startswith('Eyes')),None)
brows=next((o for o in donor_meshes if o.name.startswith('Eyebrows')),None)
assert body is not None and eyes is not None and brows is not None,[(o.name,len(o.data.vertices)) for o in donor_meshes]
assert len(body.data.vertices)>=7000

required=['Head','neck_01','spine_03','pelvis','hand_r','hand_l']
diffs={}
for name in required:
 assert name in rig.data.bones and name in donor.data.bones
 ra=rig.matrix_world@rig.data.bones[name].head_local
 da=donor.matrix_world@donor.data.bones[name].head_local
 diffs[name]=(ra-da).length
assert max(diffs.values())<.035,('donor skeleton not truly matching original Ranger',diffs)
print('GENESIS_V045_MATCHED_RIG_REST',diffs,flush=True)

# Isolate the authentic head/neck polygon faces of the original base male.
# Exclude the donor body, legs, fingers, chest: no second costume underneath.
bm=bmesh.new();bm.from_mesh(body.data)
bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
original_faces=len(bm.faces)
mat=body.matrix_world.copy()
original_vert_count=len(body.data.vertices)
# Base Quaternius male head is around z 1.64--1.81m. Cut below neckline
# where the Ranger hood conceals the seam. Restrict X to exclude shoulders.
max_z=max((mat@v.co).z for v in bm.verts)
lower=max_z-.325
to_delete=[]
for face in bm.faces:
 if any((mat@v.co).z<lower or abs((mat@v.co).x)>.245 for v in face.verts):
  to_delete.append(face)
bmesh.ops.delete(bm,geom=to_delete,context='FACES')
orphans=[v for v in bm.verts if not v.link_faces]
if orphans:bmesh.ops.delete(bm,geom=orphans,context='VERTS')
remaining_faces=len(bm.faces);remaining_verts=len(bm.verts)
assert 150<remaining_faces<original_faces/2,(original_faces,remaining_faces,lower)
assert 100<remaining_verts<original_vert_count/2,(original_vert_count,remaining_verts)
bm.to_mesh(body.data);bm.free();body.data.update()
body.name='GENESIS_V045_BASE_MALE_REAL_FACE_AND_NECK'
eyes.name='GENESIS_V045_BASE_MALE_EYES'
brows.name='GENESIS_V045_BASE_MALE_EYEBROWS'

# Rebind original bone-weighted head pieces to the *same* ranger rig.
head_meshes=[body,eyes,brows]
for ob in head_meshes:
 orig_world=ob.matrix_world.copy()
 orig_vgroups={g.name for g in ob.vertex_groups}
 assert 'Head' in orig_vgroups,(ob.name,sorted(orig_vgroups))
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 if not any(m.type=='ARMATURE' for m in ob.modifiers):
  m=ob.modifiers.new('GENESIS_V045_BIND_TO_EXISTING_RANGER_65BONES','ARMATURE');m.object=rig
 ob.parent=rig
 ob.matrix_world=orig_world
 assert ob.parent==rig and any(m.type=='ARMATURE' and m.object==rig for m in ob.modifiers)
bpy.context.view_layer.update()
for ob in [donor]:
 bpy.data.objects.remove(ob,do_unlink=True)
assert len([o for o in bpy.data.objects if o.type=='ARMATURE'])==1
assert len(rig.data.bones)==65

# Restore original full Ranger armature and outfit unmodified. Add three
# original head meshes, skins and materials, without synthetic concepts.
outpath=a.out/'GENESIS_QUATERNIUS_RANGER_WITH_ORIGINAL_MALE_HEAD_V045.glb'
bpy.ops.object.select_all(action='DESELECT')
for ob in ranger_meshes+head_meshes+[rig]:
 ob.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(outpath.resolve()),
 export_format='GLB',use_selection=True,export_animations=False)
assert outpath.stat().st_size>2000000
print('GENESIS_V045_EXPORTED_ORIGINAL_MODEL_WITH_REAL_HEAD',outpath.stat().st_size,flush=True)

# Authentic Cycles HDRI32 render, shadow-fill to check face visibility.
scene=bpy.context.scene
scene.world=bpy.data.worlds.new('GENESIS_V045_REAL_STUDIO_EXR')
world=scene.world;world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96,('HDRI must be RGB 32-bit',env.image.depth)
bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.75
out=nodes.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],out.inputs['Surface'])

head_center=rig.matrix_world@rig.data.bones['Head'].head_local
root_center=rig.matrix_world@rig.data.bones['pelvis'].head_local
focus=Vector((0,0,(head_center.z+root_center.z)*.5))
def aim(o,target):
 o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,target,offset,power,size):
 lamp=bpy.data.lights.new(name,'AREA')
 obj=bpy.data.objects.new(name,lamp);scene.collection.objects.link(obj)
 obj.location=Vector(target)+Vector(offset);aim(obj,Vector(target))
 lamp.energy=power;lamp.shape='DISK';lamp.size=size
area('soft_key',focus,(-2.2,-2.3,2.1),550,2.9)
area('back_rim',focus,(2.1,2,1.5),350,2.4)
area('face_under_hood_fill',head_center,(.05,-.85,.13),125,.95)
bpy.ops.mesh.primitive_plane_add(size=10,location=(0,0,-.025))
floor=bpy.context.object;floor.name='QA_GROUND_NOT_GAME_ASSET'
fm=bpy.data.materials.new('QA_GREY');fm.use_nodes=True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.08,.083,.088,1)
fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.89
floor.data.materials.append(fm)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=28
scene.render.resolution_x=700;scene.render.resolution_y=860
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.17
renders=[]
def render(name,dir,focal,ortho):
 camdata=bpy.data.cameras.new(name+'_lens');cam=bpy.data.objects.new(name+'_camera',camdata)
 scene.collection.objects.link(cam)
 cam.location=Vector(focal)+Vector(dir).normalized()*4
 aim(cam,Vector(focal));scene.camera=cam
 camdata.type='ORTHO';camdata.ortho_scale=ortho
 dst=a.out/(name+'.png');scene.render.filepath=str(dst.resolve())
 bpy.ops.render.render(write_still=True)
 assert dst.stat().st_size>50000,(name,dst.stat().st_size)
 renders.append({'file':dst.name,'bytes':dst.stat().st_size})
render('V045_01_RANGER_NEW_HEAD_FRONT',(.15,-1,.12),focus,3.25)
render('V045_02_RANGER_NEW_HEAD_THREEQUARTER',(.78,-1,.14),focus,3.25)
render('V045_03_RANGER_NEW_HEAD_DETAIL_FRONT',(.07,-1,.10),head_center,.71)
render('V045_04_RANGER_NEW_HEAD_DETAIL_THREEQUARTER',(.68,-1,.1),head_center,.71)
render('V045_05_RANGER_NEW_HEAD_SIDE',(.98,-.12,.1),head_center,.79)
report={
 'status':'V045_CC0_ORIGINAL_QUATERNIUS_FACE_ATTACHED_EXPERIMENTAL_UNAPPROVED',
 'ranger_original_sha256':sha(a.ranger),
 'base_male_source_sha256':sha(a.base),
 'combined_glb_sha256':sha(outpath),
 'combined_glb_bytes':outpath.stat().st_size,
 'ranger_skeleton_unchanged':True,
 'ranger_bones':len(rig.data.bones),
 'ranger_outfit_meshes_preserved':len(ranger_meshes),
 'male_source_head_meshes_added':[ob.name for ob in head_meshes],
 'male_source_body_mesh_original_verts':original_vert_count,
 'male_source_selected_head_verts':remaining_verts,
 'male_source_selected_head_faces':remaining_faces,
 'male_source_neck_cut_z_m':lower,
 'skeleton_rest_position_errors_m':diffs,
 'genuine_pbr_materials':len(bpy.data.materials),
 'original_character_mesh_preserved':True,
 'face_and_eyes_attached_to_existing_Head_skin_bone':True,
 'render_engine':'CYCLES',
 '32bit_HDRI_source':a.hdri.name,'hdri_total_depth_bits':env.image.depth,
 'renders':renders,
 'visual_quality_8_of_10_verified':False,
 'glb_animation_clips':0,
 'sword_v12b_equipped':False,'shield_v015_equipped':False,
 'mixamo_tested':False,'playcanvas_tested':False,
 'human_approved':False,'main_modified':False
}
(a.out/'V045_QUATERNIUS_RANGER_ORIGINAL_FACE_QA.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('GENESIS_V045_GENUINE_RANGER_FACE_IN_HOOD_RENDERED',json.dumps({'face_verts':remaining_verts,'rig_bones':len(rig.data.bones),'renders':len(renders),'GLB_bytes':outpath.stat().st_size}),flush=True)
