#!/usr/bin/env python3
"""Genesis original Meshy candidate 1: real Cycles visual inspection only.
No edits to the source mesh, no fabricated rig or sockets, no concepts.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--hdri',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
src=a.source.read_bytes();assert src[:4]==b'glTF'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=='MESH']
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(meshes)==1 and len(arms)==0, ('unexpected source mesh/rig counts',len(meshes),len(arms))
corners=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector((min(v.x for v in corners),min(v.y for v in corners),min(v.z for v in corners)))
hi=Vector((max(v.x for v in corners),max(v.y for v in corners),max(v.z for v in corners)))
center=(lo+hi)*.5;dims=hi-lo
assert 1.4<dims.z<2.5, ('wrong height after glTF import',tuple(dims))
scene=bpy.context.scene
world=bpy.data.worlds.new('Genesis_Original_Weary_Warrior_32bit_EXR')
scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96
bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.70
o=nodes.new('ShaderNodeOutputWorld');links.new(env.outputs['Color'],bg.inputs['Color']);links.new(bg.outputs['Background'],o.inputs['Surface'])
def point_at(ob,pt):
    ob.rotation_euler=(pt-ob.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,energy,size):
    data=bpy.data.lights.new(name,'AREA');obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj);obj.location=Vector(loc);point_at(obj,center)
    data.energy=energy;data.shape='DISK';data.size=size
light('Softbox_key',center+Vector((-2.0,-2.3,2.5)),600,3.5)
light('Softbox_rim',center+Vector((1.7,2.1,1.8)),350,2.5)
bpy.ops.mesh.primitive_plane_add(size=8,location=(center.x,center.y,lo.z-.025))
floor=bpy.context.object;floor.name='QA_ground_not_part_of_source'
material=bpy.data.materials.new('QA_ground');material.use_nodes=True
material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.08,.08,.09,1)
material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.84
floor.data.materials.append(material)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.device='CPU'
scene.render.resolution_x=720;scene.render.resolution_y=900
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=0
renders=[]
def render(filename,direction,focus=None,ortho=2.6,distance=3.0):
    target=focus if focus is not None else center
    camd=bpy.data.cameras.new(filename+'_lens')
    cam=bpy.data.objects.new(filename+'_camera',camd);scene.collection.objects.link(cam)
    cam.location=target+Vector(direction).normalized()*distance;point_at(cam,target)
    camd.type='ORTHO';camd.ortho_scale=ortho
    scene.camera=cam;scene.render.filepath=str((a.out/filename).resolve())
    bpy.ops.render.render(write_still=True)
    dst=a.out/filename;assert dst.stat().st_size>50000
    renders.append({'file':filename,'bytes':dst.stat().st_size,'camera_position':list(cam.location),'focus':list(target)})
render('MESHY_CANDIDATE1_01_front.png',(0,-1,.15),ortho=2.65)
render('MESHY_CANDIDATE1_02_three_quarter.png',(1,-1,.18),ortho=2.65)
render('MESHY_CANDIDATE1_03_back.png',(0,1,.18),ortho=2.65)
# The unrigged source does not encode anatomical sides; mark visual sides rather than inventing hands.
render('MESHY_CANDIDATE1_04_hand_Xnegative.png',(-.3,-1,.12),focus=center+Vector((-dims.x*.36,0,.10)),ortho=.78,distance=1.45)
render('MESHY_CANDIDATE1_05_hand_Xpositive.png',(.3,-1,.12),focus=center+Vector((dims.x*.36,0,.10)),ortho=.78,distance=1.45)
report={'status':'GENESIS_CANDIDATE1_UNRIGGED_SOURCE_RENDERED_NOT_APPROVED',
        'sha256':hashlib.sha256(src).hexdigest(),
        'blender_version':bpy.app.version_string,'engine':'CYCLES',
        'source_meshes':len(meshes),'source_armatures':len(arms),
        'real_size_m':list(dims),'hdri_source':a.hdri.name,
        'hdri_bits_per_rgb_channel':env.image.depth//3,
        'renders':renders,'source_modified':False,
        'left_right_hands_verified':False,'finger_grip_tested':False,
        'V12B_equipped':False,'V015_equipped':False,'human_approved':False}
(a.out/'MESHY_CANDIDATE1_VISUAL_QA.json').write_text(json.dumps(report,indent=2))
print('GENESIS_CANDIDATE1_ACTUAL_CYCLES_RENDER_PASS',json.dumps(report),flush=True)
