#!/usr/bin/env python3
"""Genesis V045b – authentic Quaternius Ranger + male base original head,
reuse ORIGINAL Ranger skin PBR atlas (it contains face, eyes, ears, lips).

This stage corrects real head materials only. Do not modify donor geometry,
65-joint skin, approved game, or invent any model/texture/concept.
"""
import argparse,json,hashlib,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser()
for x in ('combined','hdri','out'):p.add_argument('--'+x,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
raw=a.combined.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='24cd5e08ce919950a2325bd02177cec50f184d236b8d67bcbbf2c8921589d76e'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.combined.resolve()))
armatures=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(armatures)==1 and len(armatures[0].data.bones)==65
arm=armatures[0]
meshes=[o for o in bpy.data.objects if o.type=='MESH']
head_objs={}
for key in ('GENESIS_V045_BASE_MALE_EYEBROWS','GENESIS_V045_BASE_MALE_EYES',
            'GENESIS_V045_BASE_MALE_REAL_FACE_AND_NECK'):
 ob=next((o for o in meshes if o.name.startswith(key)),None)
 assert ob is not None,key
 head_objs[key]=ob

# Reuse existing original Quaternius PBR skin atlas which is visibly present on
# ranger's exposed forearm/hands; don't invent a JPG/PNG for environment light.
skin=next((m for m in bpy.data.materials if m.name.startswith('MI_Regular_Male')),None)
assert skin and skin.use_nodes
textures=[n.image.name for n in skin.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
assert textures and any('Male' in t for t in textures),textures
for ob in head_objs.values():
 ob.data.materials.clear()
 ob.data.materials.append(skin)
assert len(bpy.data.objects)>10
# This is the real Quaternius skin UV; report all UV maps to diagnose mismatches.
for key,ob in head_objs.items():
 print('V045b_HEAD_UV',key,len(ob.data.vertices),[uv.name for uv in ob.data.uv_layers],flush=True)

# Real exported asset, skin PBR linked to all three actual source head meshes.
path=a.out/'GENESIS_QUATERNIUS_RANGER_MALE_FACE_PBR_V045B.glb'
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes+[arm]:ob.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(path.resolve()),export_format='GLB',
 use_selection=True,export_animations=False)
assert path.stat().st_size>2000000
print('V045B_EXPORTED_PBR_SKIN_FACE_ASSET',path.stat().st_size,flush=True)

scene=bpy.context.scene
world=bpy.data.worlds.new('GENESIS_V045b_REAL_32BIT_EXR')
scene.world=world;world.use_nodes=True
n=world.node_tree.nodes;n.clear();links=world.node_tree.links
env=n.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.75
ow=n.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],ow.inputs['Surface'])
headpos=arm.matrix_world@arm.data.bones['Head'].head_local
pelvis=arm.matrix_world@arm.data.bones['pelvis'].head_local
middle=(headpos+pelvis)*.5
def aim(o,target):o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,target,offset,power,size):
 data=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,data)
 scene.collection.objects.link(o);o.location=Vector(target)+Vector(offset)
 aim(o,Vector(target));data.energy=power;data.shape='DISK';data.size=size
light('GENESIS_KEY',middle,(-2.2,-2.2,2.2),520,2.8)
light('GENESIS_RIM',middle,(2.2,1.8,1.8),300,2.2)
light('GENESIS_FACE_FILL',headpos,(.07,-1,.17),125,.8)
bpy.ops.mesh.primitive_plane_add(size=10,location=(0,0,-.03))
floor=bpy.context.object;floor.name='QA_FLOOR_NOT_EXPORTED'
mat=bpy.data.materials.new('QA_DARK_FLOOR');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.08,.083,.089,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.89
floor.data.materials.append(mat)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=34
scene.render.resolution_x=760;scene.render.resolution_y=900
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.23
recs=[]
def capture(label,direction,target,scale):
 camdata=bpy.data.cameras.new(label+'_lens')
 cam=bpy.data.objects.new(label+'_camera',camdata)
 scene.collection.objects.link(cam)
 cam.location=target+Vector(direction).normalized()*4
 aim(cam,target);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=scale
 output=a.out/(label+'.png');scene.render.filepath=str(output.resolve())
 bpy.ops.render.render(write_still=True)
 assert output.stat().st_size>55000
 recs.append({'file':output.name,'bytes':output.stat().st_size})
capture('V045B_01_ACTUAL_FACE_ATLAS_FRONT',(.08,-1,.1),headpos,.74)
capture('V045B_02_ACTUAL_FACE_ATLAS_THREE_QUARTER',(.7,-1,.1),headpos,.78)
capture('V045B_03_RANGER_COMPLETE_WITH_PBR_FACE',(.15,-1,.13),middle,3.27)
qa={'status':'V045B_ORIGINAL_RANGER_FACE_REUSE_EXISTING_PBR_SKIN_ATLAS_UNAPPROVED',
 'base_combined_sha256':hashlib.sha256(raw).hexdigest(),
 'output_glb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'output_glb_bytes':path.stat().st_size,
 'original_armature_bones':len(arm.data.bones),
 'original_head_geometry_modified':False,
 'original_ranger_geometry_modified':False,
 'source_pbr_material_used':skin.name,
 'source_pbr_atlas_images':textures,
 'head_meshes':[{'name':k,'verts':len(v.data.vertices),'uvs':[x.name for x in v.data.uv_layers]} for k,v in head_objs.items()],
 'HDRI':a.hdri.name,'HDRI_total_bits':env.image.depth,
 'renders':recs,'engine':'CYCLES',
 'face_visual_review_approved':False,'sword_v12b_equipped':False,
 'shield_v015_equipped':False,'mixamo_tested':False,
 'playcanvas_tested':False,'human_approved':False,'main_modified':False}
(a.out/'V045B_ORIGINAL_SKIN_ATLAS_QA.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False))
print('V045B_HEAD_MALE_REAL_SKIN_ATLAS_RENDERED',json.dumps({'material':skin.name,'renders':len(recs),'bones':65,'glb_bytes':path.stat().st_size}),flush=True)
