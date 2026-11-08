#!/usr/bin/env python3
"""Genesis V046 inspect genuine CC0 Vitruvian photoreal male head as a
replacement candidate for Quaternius V045b wax-like head.
Preserve existing Quaternius 65-bone rig; do not attach unvalidated donor.
Cycles, HDRI EXR32, actual model only; no generated imagery.
"""
import argparse,bpy,sys,hashlib,json,math
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser()
for k in ('head','hdri','out'):p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
raw=a.head.read_bytes()
assert raw[:4]==b'glTF' and len(raw)>1000000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.head.resolve()))
obs=[o for o in bpy.data.objects if o.type=='MESH']
assert obs
counts={o.name:len(o.data.vertices) for o in obs}
allpoints=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
lo=Vector(tuple(min(v[i] for v in allpoints) for i in range(3)))
hi=Vector(tuple(max(v[i] for v in allpoints) for i in range(3)))
dims=hi-lo
center=(hi+lo)/2
assert min(dims)>0.025 and max(dims)<3.0,(lo,hi,dims)
print('V046_REAL_CC0_HUMAN_HEAD',counts,'bbox_m',list(dims),'materials',[m.name for m in bpy.data.materials],flush=True)
world=bpy.data.worlds.new('GENESIS_V046_REAL_32BIT_EXR')
bpy.context.scene.world=world;world.use_nodes=True
n=world.node_tree.nodes;n.clear();links=world.node_tree.links
env=n.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.82
ow=n.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color']);links.new(bg.outputs['Background'],ow.inputs['Surface'])
def look(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
for name,off,power,size in [('key',(-1.1,-1.1,1.4),340,2.4),('fill',(1.4,-.4,.5),190,2),('rim',(1,1,1.5),260,2)]:
 data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(ob)
 ob.location=center+Vector(off);look(ob,center);data.energy=power;data.size=size
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.samples=28;sc.cycles.device='CPU'
sc.render.resolution_x=670;sc.render.resolution_y=820;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.view_settings.exposure=-.12
pictures=[]
for name,offset in [('V046_HUMAN_FACE_FRONT',(0,-1,.05)),('V046_HUMAN_FACE_THREE_QUARTER',(.75,-1,.13)),('V046_HUMAN_FACE_SIDE',(1,-.05,.15))]:
 camera_data=bpy.data.cameras.new(name+'Lens');camera=bpy.data.objects.new(name+'Cam',camera_data)
 sc.collection.objects.link(camera);sc.camera=camera
 camera.location=center+Vector(offset).normalized()*3.7;look(camera,center)
 camera_data.type='ORTHO';camera_data.ortho_scale=max(dims)*1.4
 path=a.out/(name+'.png');sc.render.filepath=str(path.resolve())
 bpy.ops.render.render(write_still=True)
 assert path.stat().st_size>45000
 pictures.append(path.name)
result={
 'status':'V046_REAL_CC0_HUMAN_HEAD_VISUAL_CANDIDATE_UNAPPROVED',
 'source':'ibrews/VitruvianGodot godot_project/vitruvian_head.glb',
 'source_sha256':hashlib.sha256(raw).hexdigest(),
 'size_bytes':len(raw),'mesh_names_and_vertices':counts,
 'bounds_m':list(dims),'blender_version':bpy.app.version_string,
 'materials':[m.name for m in bpy.data.materials],
 'textures':[i.name for i in bpy.data.images],
 'existing_Quaternius_rig_65_bones_untouched':True,
 'fit_to_original_Ranger_tested':False,
 'rebind_original_Head_tested':False,
 'original_head_replacement_done':False,
 'renders':pictures,'HDRI_total_channel_bits':env.image.depth,
 'Cycles':True,'human_approved':False,'main_modified':False
}
(a.out/'V046_PHOTOREAL_HEAD_SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2))
print('V046_REAL_CC0_HUMAN_HEAD_THREE_CYCLES_RENDERS',json.dumps({'names':pictures,'bounds_m':list(dims)}),flush=True)
