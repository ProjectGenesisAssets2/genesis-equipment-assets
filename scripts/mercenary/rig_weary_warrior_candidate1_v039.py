#!/usr/bin/env python3
"""Project Genesis | candidate 1 actual skeleton+skin+five borrowed explorer clips.

Inputs: downloaded original Meshy CC0 Weary Warrior GLB (unrigged);
prior real V029 24-bone rig with five working motion clips.
Output: new isolated experimental GLB. Never change the original or main.
Blender 4.5.13 LTS. Visual rigging QA required; nothing auto-approved.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector

P=argparse.ArgumentParser()
for arg in ('character','motion_source','out'): P.add_argument('--'+arg,type=Path,required=True)
a=P.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
original=a.character.read_bytes()
assert original[:4]==b'glTF'
sha=hashlib.sha256(original).hexdigest()
assert sha=='0452096d35bb41d992bc3508ee05f9cdc2a6ee34bb472a60c33eb9b22b66f005',sha
old_sha=hashlib.sha256(a.motion_source.read_bytes()).hexdigest()
assert old_sha=='694c5d9de518de6a702e5d0ee2d801e203daffa04807f394437663cae4ef94aa',old_sha

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.character.resolve()))
meshes=[x for x in bpy.data.objects if x.type=='MESH']
assert len(meshes)==1
mesh=meshes[0]
assert len([x for x in bpy.data.objects if x.type=='ARMATURE'])==0
source_materials=[m.name for m in mesh.data.materials if m]
# Quantized source has tiny object scale: apply, then bring the 2m body from [-1..1] to [0..2].
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
minz=min((mesh.matrix_world@v.co).z for v in mesh.data.vertices)
mesh.location.z-=minz
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
verts=len(mesh.data.vertices)
assert 8500<verts<11000,(verts,'source mesh unexpectedly changed')
bb=[mesh.matrix_world@Vector(c) for c in mesh.bound_box]
low=Vector([min(v[k] for v in bb) for k in range(3)])
high=Vector([max(v[k] for v in bb) for k in range(3)])
dimensions=high-low
assert 1.9<dimensions.z<2.1 and dimensions.x<1.0,tuple(dimensions)
mesh.name='GENESIS_CANDIDATE1_WEARY_WARRIOR_ORIGINAL_PBR_MESH'

# Names correspond to anatomical sides, NOT mirrored screen sides.
# RightHand has X negative; LeftHand has X positive.
bones=[
 ('Hips',None,(0,0,.96),(0,0,1.09)),
 ('Spine','Hips',(0,0,1.09),(0,0,1.26)),
 ('Spine01','Spine',(0,0,1.26),(0,0,1.42)),
 ('Spine02','Spine01',(0,0,1.42),(0,0,1.56)),
 ('neck','Spine02',(0,0,1.56),(0,0,1.67)),
 ('Head','neck',(0,0,1.67),(0,0,1.84)),
 ('head_end','Head',(0,0,1.84),(0,0,1.96)),
 ('headfront','Head',(0,-.04,1.74),(0,-.12,1.74)),
 ('RightShoulder','Spine02',(-.075,0,1.55),(-.19,0,1.53)),
 ('RightArm','RightShoulder',(-.19,0,1.53),(-.285,0,1.215)),
 ('RightForeArm','RightArm',(-.285,0,1.215),(-.33,0,.91)),
 ('RightHand','RightForeArm',(-.33,0,.91),(-.338,0,.815)),
 ('LeftShoulder','Spine02',(.075,0,1.55),(.19,0,1.53)),
 ('LeftArm','LeftShoulder',(.19,0,1.53),(.285,0,1.215)),
 ('LeftForeArm','LeftArm',(.285,0,1.215),(.33,0,.91)),
 ('LeftHand','LeftForeArm',(.33,0,.91),(.338,0,.815)),
 ('RightUpLeg','Hips',(-.115,0,.99),(-.12,0,.58)),
 ('RightLeg','RightUpLeg',(-.12,0,.58),(-.13,0,.14)),
 ('RightFoot','RightLeg',(-.13,0,.14),(-.13,-.09,.08)),
 ('RightToeBase','RightFoot',(-.13,-.09,.08),(-.13,-.20,.07)),
 ('LeftUpLeg','Hips',(.115,0,.99),(.12,0,.58)),
 ('LeftLeg','LeftUpLeg',(.12,0,.58),(.13,0,.14)),
 ('LeftFoot','LeftLeg',(.13,0,.14),(.13,-.09,.08)),
 ('LeftToeBase','LeftFoot',(.13,-.09,.08),(.13,-.20,.07)),
]
assert len(bones)==24
armdata=bpy.data.armatures.new('GENESIS_WEARY_WARRIOR_24_BONES')
arm=bpy.data.objects.new('GENESIS_WEARY_WARRIOR_RIG_V039',armdata)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,par,h,t in bones:
    b=armdata.edit_bones.new(name)
    b.head=h;b.tail=t;b.use_deform=(name not in ('head_end','headfront'))
for name,par,h,t in bones:
    if par:armdata.edit_bones[name].parent=armdata.edit_bones[par]
bpy.ops.object.mode_set(mode='OBJECT')
assert len(armdata.bones)==24
ni={n:b for n,b in bones[:0]} if False else {b.name:b for b in armdata.bones}
assert ni['RightHand'].head_local.x<0 and ni['LeftHand'].head_local.x>0

# Blender's geometric heat weights preserve the original mesh/UV/materials.
# If a source has disconnected hanging cape pieces and heat weights fail,
# use explicit local field weighting rather than claim a failed bind as valid.
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True);arm.select_set(True)
bpy.context.view_layer.objects.active=arm
auto_result='unattempted'
try:
    bpy.ops.object.parent_set(type='ARMATURE_AUTO',keep_transform=True)
    auto_result='AUTO_BONE_HEAT'
except RuntimeError as ex:
    print('BONE_HEAT_FAILURE',str(ex),flush=True)
    auto_result='FALLBACK_DISTANCE_BASED_SKIN'

deform_groups={x.name:mesh.vertex_groups.get(x.name) for x in armdata.bones if x.use_deform}
auto_valid=all(v is not None for k,v in deform_groups.items() if k in ('Hips','Spine','LeftHand','RightHand','LeftLeg','RightLeg'))
if not auto_valid:
    auto_result='FALLBACK_DISTANCE_BASED_SKIN'
if auto_result=='FALLBACK_DISTANCE_BASED_SKIN':
    for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
    bpy.context.view_layer.objects.active=mesh
    mesh.parent=arm;mesh.matrix_parent_inverse=arm.matrix_world.inverted()
    for bone in armdata.bones:
        if bone.use_deform:mesh.vertex_groups.new(name=bone.name)
    groups={x.name:mesh.vertex_groups[x.name] for x in armdata.bones if x.use_deform}
    for v in mesh.data.vertices:
        co=v.co
        x,y,z=co.x,co.y,co.z
        side='Right' if x<0 else 'Left'
        ax=abs(x)
        scores={}
        # Cape behind the actor is anchored to torso rather than knotted to legs.
        cape=y>.15 and z>.16 and z<1.65 and ax>.17
        if cape:
            scores={'Spine':.23,'Spine01':.32,'Spine02':.45}
        elif z>=1.68 and ax<.27:
            scores={'Head':1.}
        elif ax>.225 and z>.78 and z<1.57:
            if z<.94:scores={side+'Hand':1.}
            elif z<1.24:
                t=(z-.94)/.30
                scores={side+'ForeArm':1.-.35*t,side+'Arm':.35*t}
            else:
                t=(z-1.24)/.33
                scores={side+'Arm':1.-.18*t,side+'Shoulder':.18*t}
        elif z<.98:
            if z<.13:scores={side+'Foot':.65,side+'ToeBase':.35}
            elif z<.22:scores={side+'Leg':.25,side+'Foot':.75}
            elif z<.62:
                t=(z-.22)/.40
                scores={side+'Leg':1.-.2*t,side+'UpLeg':.2*t}
            else:
                t=(z-.62)/.36
                scores={side+'UpLeg':.9, 'Hips':.1*t}
        elif z<1.22:scores={'Hips':.65,'Spine':.35}
        elif z<1.43:scores={'Spine':.5,'Spine01':.5}
        else:scores={'Spine01':.25,'Spine02':.75}
        norm=sum(scores.values())
        for name,weight in scores.items():groups[name].add([v.index],weight/norm,'REPLACE')
else:
    # Heat weights can leave a few loose cape vertices. Ensure every vertex
    # has at least one valid joint influence, with minimally invasive fallback.
    hips=mesh.vertex_groups.get('Hips')
    assert hips is not None
    missing=[]
    for v in mesh.data.vertices:
        if not v.groups:missing.append(v.index)
    for idx in missing:hips.add([idx],1.0,'REPLACE')

# Ensure all present vertices belong to at least one group.
if not mesh.parent:mesh.parent=arm
if not any(m.type=='ARMATURE' and m.object==arm for m in mesh.modifiers):
    modifier=mesh.modifiers.new('GENESIS_V039_SKIN','ARMATURE');modifier.object=arm
assert mesh.parent==arm
groupnames={g.name for g in mesh.vertex_groups}
assert {'Hips','RightHand','LeftHand','LeftUpLeg','RightUpLeg'}.issubset(groupnames)
weighted=sum(bool(v.groups) for v in mesh.data.vertices)
assert weighted==verts,(weighted,verts,'unweighted source vertices')
# Attachable sockets are empties children of exact anatomical wrist bones.
sockets=[]
for name,bone in [('GENESIS_SOCKET_WEAPON_R','RightHand'),('GENESIS_SOCKET_SHIELD_L','LeftHand')]:
    obj=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type='PLAIN_AXES';obj.empty_display_size=.035
    obj.parent=arm;obj.parent_type='BONE';obj.parent_bone=bone
    obj.location=(0,0,0)
    sockets.append(obj)
assert sockets[0].parent_bone=='RightHand' and sockets[1].parent_bone=='LeftHand'

# Import archived original V029 ONLY as animation reference. It will be
# removed after motion capture. Geometry and PBR stay from NEW Meshy candidate.
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(a.motion_source.resolve()))
source_objects=set(bpy.data.objects)-before
src_arms=[ob for ob in source_objects if ob.type=='ARMATURE']
assert len(src_arms)==1
src_arm=src_arms[0]
src_bones=set(pb.name for pb in src_arm.pose.bones)
assert all(n in src_bones for n,_,_,_ in bones)
clips=[
 ('GENESIS_MERC_IDLE_V029','GENESIS_MESHY_IDLE_V039',24),
 ('GENESIS_MERC_WALK_V029','GENESIS_MESHY_WALK_V039',32),
 ('GENESIS_MERC_INSPECT_SWORD_V029','GENESIS_MESHY_INSPECT_SWORD_V039',34),
 ('GENESIS_MERC_INSPECT_SHIELD_V029','GENESIS_MESHY_INSPECT_SHIELD_V039',34),
 ('GENESIS_MERC_WALK_EQUIPPED_V029','GENESIS_MESHY_WALK_EQUIPPED_V039',32),
]
source_actions={}
for orig,renamed,n in clips:
    matches=[ac for ac in bpy.data.actions if ac.name==orig]
    assert len(matches)==1,(orig,[ac.name for ac in bpy.data.actions])
    source_actions[orig]=matches[0]
arm.animation_data_create()
if src_arm.animation_data is None:src_arm.animation_data_create()
original_rest={n:(src_arm.matrix_world@src_arm.pose.bones[n].bone.matrix_local).to_quaternion() for n,_,_,_ in bones}
target_rest={n:(arm.matrix_world@arm.pose.bones[n].bone.matrix_local).to_quaternion() for n,_,_,_ in bones}
parents={n:p for n,p,_,_ in bones}
scene=bpy.context.scene
clip_report=[]
for original_clip,outname,samples in clips:
    ac=source_actions[original_clip]
    src_arm.animation_data.action=ac
    if getattr(ac,'slots',None) and len(ac.slots):
        src_arm.animation_data.action_slot=ac.slots[0]
    # New action stored only for target armature, old animation action is not copied.
    out_act=bpy.data.actions.new(outname)
    arm.animation_data.action=out_act
    start,end=ac.frame_range
    for idx in range(samples+1):
        fraction=idx/samples
        scene.frame_set(int(round(start+(end-start)*fraction)))
        bpy.context.view_layer.update()
        desired={}
        for name,_,_,_ in bones:
            pb=src_arm.pose.bones[name]
            world_pose=(src_arm.matrix_world@pb.matrix).to_quaternion()
            relative=world_pose@original_rest[name].inverted()
            desired[name]=relative@target_rest[name]
        for name,parent,_,_ in bones:
            pb=arm.pose.bones[name];pb.rotation_mode='QUATERNION'
            if parent:
                restrel=target_rest[parent].inverted()@target_rest[name]
                q=restrel.inverted()@desired[parent].inverted()@desired[name]
            else:
                q=target_rest[name].inverted()@desired[name]
            pb.rotation_quaternion=q.normalized()
            pb.keyframe_insert(data_path='rotation_quaternion',frame=idx+1,group=name)
        # Small root breathing / gait grounding, not combat or fake attack.
        if original_clip.endswith(('WALK_V029','WALK_EQUIPPED_V029')):
            phase=2*math.pi*fraction
            pb=arm.pose.bones['Hips']
            pb.location=(0,0,.012*abs(math.sin(phase)))
            pb.keyframe_insert(data_path='location',frame=idx+1,group='Hips')
    clip_report.append({'name':outname,'source':original_clip,'samples':samples+1,
        'reference_frame_range':[round(start,2),round(end,2)]})
    print('V039_RETARGETED_REAL_CLIP',outname,samples+1,flush=True)
# Remove old source objects+actions. They must not enter new exported character.
for ob in list(source_objects):bpy.data.objects.remove(ob,do_unlink=True)
for src_action in source_actions.values():
    if src_action.name in bpy.data.actions:bpy.data.actions.remove(src_action,do_unlink=True)
assert sum(1 for o in bpy.data.objects if o.type=='MESH')==1
assert sum(1 for o in bpy.data.objects if o.type=='ARMATURE')==1
assert len([x for x in bpy.data.actions if x.name.startswith('GENESIS_MESHY_')])==5
newaction=next(x for x in bpy.data.actions if x.name=='GENESIS_MESHY_IDLE_V039')
arm.animation_data.action=newaction
if getattr(newaction,'slots',None) and len(newaction.slots):
    arm.animation_data.action_slot=newaction.slots[0]
scene.frame_set(1)
bpy.context.view_layer.update()

outpath=a.out/'GENESIS_MESHY_CANDIDATE1_RIGGED_ANIMATED_V039.glb'
bpy.ops.object.select_all(action='DESELECT')
for ob in [mesh,arm]+sockets:ob.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(outpath.resolve()),export_format='GLB',use_selection=True,
                           export_animations=True,export_animation_mode='ACTIONS',
                           export_force_sampling=True)
assert outpath.exists() and outpath.stat().st_size>100000

report={
 'status':'V039_REAL_GLB_RIGGED_FIVE_CLIPS_EXPERIMENTAL_NOT_APPROVED',
 'source_model_sha256':sha,'source_motion_sha256':old_sha,
 'output_sha256':hashlib.sha256(outpath.read_bytes()).hexdigest(),
 'model_original_preserved':True,'mesh_source':'actual Meshy CC0 Weary Warrior candidate #1',
 'mesh_vertices':verts,'source_materials':source_materials,
 'actual_skin_weighting':auto_result,'weighted_vertices':weighted,
 'skin_bones':len(armdata.bones),'finger_joints':0,
 'anatomical_right_hand':'RightHand X negative',
 'anatomical_left_hand':'LeftHand X positive',
 'weapon_socket':'GENESIS_SOCKET_WEAPON_R',
 'shield_socket':'GENESIS_SOCKET_SHIELD_L',
 'gltf_clips':clip_report,
 'preview_quality_verified':False,'weapons_attached_tested':False,
 'playcanvas_tested':False,'human_approved':False,
 'geometry_and_texture_untouched_except_transform_scale_bake':True,
}
(a.out/'GENESIS_MESHY_CANDIDATE1_RIG_V039_QA.json').write_text(json.dumps(report,indent=2))
print('GENESIS_MESHY_RIGGED_V039_EXPORTED',json.dumps(report),flush=True)
