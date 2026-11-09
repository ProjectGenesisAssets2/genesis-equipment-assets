#!/usr/bin/env python3
"""True Blender Cycles preview from V050 GLB for Project Genesis 4-T WebGL fallback.
Not a concept. The validated GLB, its 65-bone rig and original materials remain untouched.
"""
import argparse, pathlib, json, hashlib, math
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--glb',required=True);p.add_argument('--hdri',required=True);p.add_argument('--out',required=True)
a=p.parse_args(__import__('sys').argv[__import__('sys').argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
assert len(meshes)>=10,len(meshes)
corners=[]
for o in meshes:
 for c in o.bound_box: corners.append(o.matrix_world@Vector(c))
mn=Vector((min(v[i] for v in corners) for i in range(3)))
mx=Vector((max(v[i] for v in corners) for i in range(3)))
center=(mn+mx)*.5;height=mx.z-mn.z;width=max(mx.x-mn.x,mx.y-mn.y)
assert 1.0<height<5.0,(height,width)
scene=bpy.context.scene;scene.render.engine='CYCLES'
scene.cycles.samples=72
scene.render.resolution_x=820;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Studio small EXR 4k 32bpc')
scene.world=world;world.use_nodes=True;nt=world.node_tree;nt.nodes.clear()
out=nt.nodes.new('ShaderNodeOutputWorld');bg=nt.nodes.new('ShaderNodeBackground');tex=nt.nodes.new('ShaderNodeTexEnvironment')
tex.image=bpy.data.images.load(a.hdri);assert tex.image.depth>=96,tex.image.depth
bg.inputs['Strength'].default_value=.9
nt.links.new(tex.outputs['Color'],bg.inputs['Color']);nt.links.new(bg.outputs['Background'],out.inputs['Surface'])
cam_data=bpy.data.cameras.new('V050 4-T actual GLB front camera');camera=bpy.data.objects.new('V050_Camera',cam_data);scene.collection.objects.link(camera);scene.camera=camera
target=Vector((center.x,center.y,center.z+.04*height))
camera.location=Vector((center.x+2.7*height,center.y-6.7*height,center.z+.7*height))
direction=target-camera.location;camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO';cam_data.ortho_scale=max(height*1.29,width*1.12/(820/900))
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.filepath=a.out;pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True)
bpy.ops.render.render(write_still=True)
img=bpy.data.images.load(a.out)
assert img.size[0]==820 and img.size[1]==900
qa={"status":"EXPERIMENTAL_REAL_BLENDER_CYCLES_V050_GLTF_NOT_OWNER_APPROVED",
    "glb_sha256":hashlib.sha256(pathlib.Path(a.glb).read_bytes()).hexdigest(),
    "render_sha256":hashlib.sha256(pathlib.Path(a.out).read_bytes()).hexdigest(),
    "hdr_format":"32-bit EXR per channel","renderer":"Blender 4.5.13 LTS Cycles",
    "image_pixels":[820,900],"mesh_count":len(meshes),"height_m":round(height,4),
    "in_game_tested":False}
pathlib.Path(a.out).with_suffix('.json').write_text(json.dumps(qa,indent=2))
print('GENESIS V050 EXACT-GLB CYCLES RENDER',json.dumps(qa))
