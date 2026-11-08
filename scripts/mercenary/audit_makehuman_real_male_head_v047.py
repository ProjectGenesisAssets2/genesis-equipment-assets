#!/usr/bin/env python3
"""Genesis V047: inspect real CC0 MakeHuman male base with human facial features.
No change to approved Ranger yet; genuine Blender/Cycles visual admission test.
"""
import bpy,sys,argparse,json,hashlib
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser()
for x in ('source','hdri','out'):p.add_argument('--'+x,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
raw=a.source.read_bytes();assert raw[:4]==b'glTF'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(arms)==1 and len(meshes)>=2,(len(arms),len(meshes))
arm=arms[0]
names={x.name for x in arm.data.bones}
assert 'head' in names and 'neck_01' in names
body=sorted(meshes,key=lambda x:len(x.data.vertices),reverse=True)[0]
shape_names=[key.name for key in body.data.shape_keys.key_blocks] if body.data.shape_keys else []
print('V047_REAL_SOURCE_MESHES',json.dumps([{ 'name':x.name,'verts':len(x.data.vertices),'materials':[m.name for m in x.data.materials if m],'shape_keys':len(x.data.shape_keys.key_blocks) if x.data.shape_keys else 0} for x in meshes]),flush=True)
print('V047_REAL_SOURCE_SHAPE_KEYS',shape_names,flush=True)
print('V047_REAL_SOURCE_RIG_BONES',len(names),sorted(names),flush=True)
# Reference head bone physical location; original MakeHuman CC0 base with facial
# expressions and eyes. No simulation, no generated pictures.
head=(arm.matrix_world@arm.data.bones['head'].head_local)
head+=Vector((0,0,.13))
print('V047_REFERENCE_HEAD_LOCATION',list(head),flush=True)

scene=bpy.context.scene
world=bpy.data.worlds.new('GENESIS_V047_STUDIO_HDRI_EXR_32BIT')
world.use_nodes=True;scene.world=world
n=world.node_tree.nodes;n.clear();links=world.node_tree.links
tex=n.new('ShaderNodeTexEnvironment')
tex.image=bpy.data.images.load(str(a.hdri.resolve()))
assert tex.image.depth>=96
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.67
out=n.new('ShaderNodeOutputWorld')
links.new(tex.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],out.inputs['Surface'])
def aim(cam,pt):
 cam.rotation_euler=(pt-cam.location).to_track_quat('-Z','Y').to_euler()
def lamp(name,offset,power,size):
 d=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,d)
 scene.collection.objects.link(ob);ob.location=head+Vector(offset)
 aim(ob,head);d.energy=power;d.shape='DISK';d.size=size
lamp('V047_KEY',(-1.4,-1.5,1.4),250,2.0)
lamp('V047_RIM',(1.3,1.2,1.2),150,1.7)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24
scene.render.resolution_x=700;scene.render.resolution_y=830
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.06
renders=[]
def capture(nam,dir,sc):
 data=bpy.data.cameras.new(nam+'_lens');cam=bpy.data.objects.new(nam+'_cam',data)
 scene.collection.objects.link(cam);cam.location=head+Vector(dir).normalized()*3.2
 aim(cam,head);data.type='ORTHO';data.ortho_scale=sc
 scene.camera=cam;path=a.out/(nam+'.png');scene.render.filepath=str(path.resolve())
 bpy.ops.render.render(write_still=True)
 assert path.stat().st_size>40000
 renders.append(path.name)
capture('V047_01_MAKEHUMAN_ADULT_BASE_FRONT',(.10,-1,.07),.75)
capture('V047_02_MAKEHUMAN_ADULT_BASE_THREEQUARTER',(.7,-1,.10),.80)
# If the shipped source contains aged morphs, preview the original morph itself
# with skin + eyes. Do not fake aging by recoloring a childlike face.
aged=[]
for name in shape_names:
 if 'old' in name.lower() or ('age' in name.lower() and not any(y in name.lower() for y in ['young','baby','child'])):
  aged.append(name)
if aged:
 chosen=next((x for x in aged if 'old' in x.lower()),aged[0])
 key=body.data.shape_keys.key_blocks.get(chosen)
 key.value=.72
 bpy.context.view_layer.update()
 print('V047_ACTUAL_AGE_MORPH_USED',chosen,.72,flush=True)
 capture('V047_03_MAKEHUMAN_SOURCE_OLDER_FACE',(.10,-1,.07),.75)
else:print('V047_NO_AGE_MORPH_AVAILABLE',flush=True)
qa={'source':'kblood/CharacterCreator output/base_body.glb',
 'license':'CC0-1.0 (generated output, LICENSE-NOTES.md)',
 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'actual_mesh_count':len(meshes),'bone_count':len(arm.data.bones),
 'body_mesh':body.name,'body_verts':len(body.data.vertices),
 'shape_keys_count':len(shape_names),'possible_age_morphs':aged,
 'meshes':[{'name':x.name,'verts':len(x.data.vertices),'materials':[m.name for m in x.data.materials if m]} for x in meshes],
 'real_Cycles_32bit_hdr_renders':renders,'hdri':a.hdri.name,
 'converted_to_ranger':False,'visual_approved':False,'main_modified':False}
(a.out/'V047_MAKEHUMAN_SOURCE_REAL_PREVIEW_QA.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False))
print('V047_MAKEHUMAN_REAL_CC0_HEAD_PREVIEW_COMPLETE',qa['source_sha256'],renders,flush=True)
