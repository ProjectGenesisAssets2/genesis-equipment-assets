#!/usr/bin/env python3
"""Actual new Meshy candidate-1 V039 skinned GLB, five actions, read-only Cycles review.
No original mesh modification, no proxies, no claimed equipment attachment."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser()
for k in ('character','hdri','out'):p.add_argument('--'+k,required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
raw=a.character.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='e29d2d0e6e32936b0b1c11df53a40315da9360cea56212e9ea7e76327cf6fc15'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.character.resolve()))
bpy.context.view_layer.update()
meshes=[ob for ob in bpy.data.objects if ob.type=='MESH']
arms=[ob for ob in bpy.data.objects if ob.type=='ARMATURE']
assert len(meshes)==1 and len(arms)==1,(len(meshes),len(arms))
arm=arms[0];assert len(arm.data.bones)==24
names={b.name for b in arm.data.bones}
assert {'RightHand','LeftHand','Hips','LeftFoot','RightFoot'}.issubset(names)
assert arm.data.bones['RightHand'].head_local.x<0 and arm.data.bones['LeftHand'].head_local.x>0
assert len([x for x in bpy.data.actions if x.name.startswith('GENESIS_MESHY_')])==5
mesh=meshes[0]
corners=[mesh.matrix_world@Vector(v) for v in mesh.bound_box]
lo=Vector(tuple(min(v[k] for v in corners) for k in range(3)))
hi=Vector(tuple(max(v[k] for v in corners) for k in range(3)))
center=(lo+hi)/2
assert 1.5<(hi.z-lo.z)<2.5,('height',list(lo),list(hi))
scene=bpy.context.scene
world=bpy.data.worlds.new('GENESIS_CANDIDATE1_32bit_EXR')
scene.world=world;world.use_nodes=True
n=world.node_tree.nodes;n.clear();links=world.node_tree.links
env=n.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(a.hdri.resolve()))
assert env.image.depth>=96
bg=n.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.7
out=n.new('ShaderNodeOutputWorld');links.new(env.outputs['Color'],bg.inputs['Color']);links.new(bg.outputs['Background'],out.inputs['Surface'])
def aim(ob,t):
    ob.rotation_euler=(t-ob.location).to_track_quat('-Z','Y').to_euler()
def lamp(name,offset,power,size):
    d=bpy.data.lights.new(name,'AREA')
    ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob)
    ob.location=center+Vector(offset);aim(ob,center)
    d.energy=power;d.shape='DISK';d.size=size
lamp('key',(-2,-2.3,2.8),780,3)
lamp('rim',(2.3,1.9,2.2),430,2.7)
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,lo.z-.028))
floor=bpy.context.object;floor.name='QA_GROUND_ONLY'
mat=bpy.data.materials.new('QA_GREY');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.06,.065,.071,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
floor.data.materials.append(mat)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.device='CPU'
scene.render.resolution_x=650;scene.render.resolution_y=780
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.1
allactions={ac.name:ac for ac in bpy.data.actions if ac.name.startswith('GENESIS_MESHY_')}
clips=[
 ('GENESIS_MESHY_IDLE_V039',.15,'V039_01_IDLE.png',(.17,-1,.1)),
 ('GENESIS_MESHY_WALK_V039',.33,'V039_02_WALK.png',(.17,-1,.1)),
 ('GENESIS_MESHY_INSPECT_SWORD_V039',.50,'V039_03_INSPECT_SWORD.png',(.17,-1,.1)),
 ('GENESIS_MESHY_INSPECT_SHIELD_V039',.50,'V039_04_INSPECT_SHIELD.png',(.17,-1,.1)),
 ('GENESIS_MESHY_WALK_EQUIPPED_V039',.65,'V039_05_WALK_EQUIPPED_NO_GEAR.png',(.17,-1,.1)),
 ('GENESIS_MESHY_WALK_EQUIPPED_V039',.65,'V039_06_WALK_EQUIPPED_BACK.png',(-.17,1,.1))
]
records=[]
for clip,phase,name,view in clips:
    action=allactions[clip]
    if arm.animation_data is None:arm.animation_data_create()
    arm.animation_data.action=action
    if getattr(action,'slots',None) and len(action.slots):
        arm.animation_data.action_slot=action.slots[0]
    start,end=action.frame_range
    fr=round(start+(end-start)*phase)
    scene.frame_set(fr);bpy.context.view_layer.update()
    # Guard against runaway pose from transferred animation.
    evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    try:
        worldpoints=[mesh.matrix_world@v.co for v in evaluated.vertices]
        minz=min(v.z for v in worldpoints);maxz=max(v.z for v in worldpoints)
        xmax=max(abs(v.x) for v in worldpoints)
        assert minz>-1.2 and maxz<4.0 and xmax<3.0,(clip,minz,maxz,xmax)
    finally:mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    camdata=bpy.data.cameras.new(name+'_Lens');camera=bpy.data.objects.new(name+'_Camera',camdata)
    scene.collection.objects.link(camera);scene.camera=camera
    camera.location=center+Vector(view).normalized()*5.5;aim(camera,center)
    camdata.type='ORTHO';camdata.ortho_scale=2.65
    target=a.out/name;scene.render.filepath=str(target.resolve())
    bpy.ops.render.render(write_still=True)
    assert target.stat().st_size>60000
    records.append({'source_clip':clip,'phase':phase,'frame':fr,'render':name,'bytes':target.stat().st_size,
                    'evaluated_bounds_z_m':[round(minz,4),round(maxz,4)],'max_abs_x_m':round(xmax,4)})
report={'status':'V039_TRUE_CYCLES_FIVE_ACTIONS_RIGGED_NO_EQUIPMENT_NO_APPROVAL',
 'character_sha256':hashlib.sha256(raw).hexdigest(),
 'source':'Meshy candidate1 unrigged CC0, retargeted V029 existing explorer motions',
 'mesh_vertices':len(mesh.data.vertices),'bones':24,'action_count':len(allactions),
 'individual_finger_bones':0,'right_hand_is_x_negative':True,
 'left_hand_is_x_positive':True,'render_engine':'CYCLES',
 'hdri':'studio_small_09_4k.exr','hdri_depth_bits_per_rgb_channel':env.image.depth/3,
 'rendered_clips':records,'sword_equipped':False,'shield_equipped':False,
 'playcanvas_tested':False,'user_approved':False}
(a.out/'V039_VISUAL_QA_REAL_CYCLES.json').write_text(json.dumps(report,indent=2))
print('GENESIS_V039_SIX_REAL_CYCLES_POSES_RENDERED',json.dumps({'names':[v['render'] for v in records], 'bounds':[v['evaluated_bounds_z_m'] for v in records]}),flush=True)
