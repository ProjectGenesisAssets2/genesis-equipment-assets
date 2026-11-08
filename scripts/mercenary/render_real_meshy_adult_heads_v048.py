#!/usr/bin/env python3
"""Genesis V048: inspect two real CC0 Meshy 3D adult/aged heads, not concepts.
Imported original GLBs in Blender 4.5.13, physical Cycles PBR, EXR HDRI32.
Check actual geometry and render 4 sides for anatomical/facial coverage.
No head is considered approved. Existing Ranger 65 bones untouched.
"""
import bpy,sys,json,argparse,hashlib,math
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser()
for k in ('source','hdri','out','name'):p.add_argument('--'+k,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.out)/a.name;out.mkdir(parents=True,exist_ok=True)
raw=Path(a.source).read_bytes();assert raw[:4]==b'glTF'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(a.source).resolve()))
meshes=[x for x in bpy.data.objects if x.type=='MESH']
assert meshes
allverts=sum(len(x.data.vertices) for x in meshes)
allfaces=sum(len(x.data.polygons) for x in meshes)
assert allverts>=400
corners=[x.matrix_world@Vector(c) for x in meshes for c in x.bound_box]
low=Vector([min(c[i] for c in corners) for i in range(3)])
high=Vector([max(c[i] for c in corners) for i in range(3)])
center=(low+high)*.5;dims=high-low
print('GENESIS_V048_REAL_SOURCE_GEOMETRY',a.name,'verts',allverts,'faces',allfaces,'dims',list(dims),'bounds',list(low),list(high),flush=True)
print('GENESIS_V048_REAL_SOURCE_MATERIALS',a.name,[m.name for m in bpy.data.materials],flush=True)
world=bpy.data.worlds.new('GENESIS_REAL_32BIT_EXR_ADULT_HEAD_V048')
world.use_nodes=True;bpy.context.scene.world=world
n=world.node_tree.nodes;n.clear();links=world.node_tree.links
env=n.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(Path(a.hdri).resolve()),check_existing=True)
assert env.image.depth>=96
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.8
outnode=n.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],outnode.inputs['Surface'])
def aim(ob,t):
 ob.rotation_euler=(t-ob.location).to_track_quat('-Z','Y').to_euler()
def lamp(label,offset,power,size):
 d=bpy.data.lights.new(label,'AREA');o=bpy.data.objects.new(label,d)
 bpy.context.scene.collection.objects.link(o);o.location=center+Vector(offset)
 aim(o,center);d.energy=power;d.shape='DISK';d.size=size
lamp('KEY',(-2,-2.1,2.2),550,3)
lamp('RIM',(2,1.8,1.5),350,2)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=25
scene.render.resolution_x=650;scene.render.resolution_y=750
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.12
renders=[]
views=[('01_front',(0,-1,.07)),('02_threequarter',(.75,-1,.09)),('03_side',(1,-.08,.08)),('04_back',(0,1,.08))]
for label,direction in views:
 data=bpy.data.cameras.new(label+'_lens');camera=bpy.data.objects.new(label+'_cam',data)
 scene.collection.objects.link(camera)
 dist=max(dims)*3
 camera.location=center+Vector(direction).normalized()*dist
 aim(camera,center);data.type='ORTHO';data.ortho_scale=max(dims.z*1.25,dims.x*1.6,.43)
 scene.camera=camera
 filename=f'V048_{a.name}_{label}.png'
 f=out/filename;scene.render.filepath=str(f.resolve())
 bpy.ops.render.render(write_still=True)
 assert f.stat().st_size>20000
 renders.append(filename)
qa={'status':'REAL_3D_HEAD_SOURCE_REVIEW_NOT_APPROVED',
 'source_name':a.name,'source_sha256':hashlib.sha256(raw).hexdigest(),
 'model_glb_bytes':len(raw),'mesh_count':len(meshes),
 'vertices':allverts,'polygons':allfaces,'world_bounds':[list(low),list(high)],
 'dimensions_m':list(dims),'materials':[x.name for x in bpy.data.materials],
 'source_model_not_modified':True,
 'HDRI_32bits_per_channel':env.image.depth/3,
 'render_engine':'CYCLES','rendered_views':renders,
 'actual_face_quality_verified':False,'head_attached_to_Ranger':False,
 'human_approved':False,'PlayCanvas_tested':False,'main_modified':False}
(out/f'V048_{a.name}_SOURCE_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print('GENESIS_V048_REAL_HEAD_RENDER_FINISHED',a.name,json.dumps({'faces':allfaces,'views':len(renders)}),flush=True)
