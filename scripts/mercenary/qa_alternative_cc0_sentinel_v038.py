#!/usr/bin/env python3
"""Project Genesis V038: inspect ACTUAL alternative CC0 rigged sentinel in Cycles.
This is candidate QA only: no original mercenary edits, no main integration.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser()
for v in ('character','hdri','out'):p.add_argument('--'+v,required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
assert a.character.stat().st_size>100000 and a.hdri.suffix.lower()=='.exr'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.character.resolve()))
bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=='MESH']
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert meshes and arms,('candidate has no skinned animation',len(meshes),len(arms))
points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
lo=Vector((min(v.x for v in points),min(v.y for v in points),min(v.z for v in points)))
hi=Vector((max(v.x for v in points),max(v.y for v in points),max(v.z for v in points)))
size=hi-lo;scale=max(size);assert .25<size.z<6.,('unexpected meter scale',list(size))
center=(lo+hi)*.5;frame_size=max(size.z*1.18,size.x*1.4)
actions=list(bpy.data.actions)
print('V038_GLTF_IMPORTED',json.dumps({'meshes':len(meshes),'arms':len(arms),'actions':[x.name for x in actions],
'object_names':[x.name for x in meshes[:45]],'bones':[b.name for b in arms[0].data.bones[:120]],'bounds_m':[list(lo),list(hi)]}),flush=True)

world=bpy.data.worlds.new('Genesis_V038_REAL_32bit_HDRI')
bpy.context.scene.world=world;world.use_nodes=True
wn=world.node_tree.nodes;wl=world.node_tree.links
wn.clear()
tex=wn.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert tex.image.depth>=96,('HDRI not float 32bit per RGB channel',tex.image.depth)
bg=wn.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.65
out=wn.new('ShaderNodeOutputWorld');wl.new(tex.outputs['Color'],bg.inputs['Color']);wl.new(bg.outputs['Background'],out.inputs['Surface'])

def point(ob,t):
    vec=t-ob.location;ob.rotation_euler=vec.to_track_quat('-Z','Y').to_euler()

def area(name,offset,power,length):
    lamp=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,lamp)
    bpy.context.scene.collection.objects.link(ob)
    ob.location=center+Vector(offset)*size.z
    point(ob,center);lamp.energy=power;lamp.shape='DISK';lamp.size=length;return ob
area('V038_KEY_LIGHT',(-1.3,-1.3,1.1),800,2.4)
area('V038_RIM',(1.0,.9,.9),500,1.9)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=28
scene.render.resolution_x=650;scene.render.resolution_y=780
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.2
bpy.ops.mesh.primitive_plane_add(size=max(6,scale*10),location=(center.x,center.y,lo.z-.03))
floor=bpy.context.object;floor.name='V038_QA_GROUND_ONLY'
mat=bpy.data.materials.new('V038_QA_GROUND_MATERIAL');mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.055,.060,.065,1.)
bsdf.inputs['Roughness'].default_value=.84;floor.data.materials.append(mat)
allbones={b.name:b for arm in arms for b in arm.pose.bones}
def right_hand_target():
    for name,bone in allbones.items():
        normalized=''.join(ch.lower() for ch in name if ch.isalpha())
        if 'righthand' in normalized or normalized in ('handr','rhand'):
            arm=next(a for a in arms if bone.name in a.pose.bones)
            return (arm.matrix_world@arm.pose.bones[bone.name].matrix).translation,bone.name
    return center+Vector((size.x*.18,0,size.z*.04)),None
def set_clip(kind,phase):
    matches=[ac for ac in actions if kind in ac.name.lower()]
    if not matches:return {'action':None,'frame':None}
    ac=matches[0]
    arm=arms[0]
    if arm.animation_data is None:arm.animation_data_create()
    arm.animation_data.action=ac
    if getattr(ac,'slots',None):
        slots=list(ac.slots)
        if slots:arm.animation_data.action_slot=slots[0]
    start,end=ac.frame_range;frame=round(start+(end-start)*phase)
    scene.frame_set(frame);bpy.context.view_layer.update()
    return {'action':ac.name,'frame':frame}
def render(name,clip,phase,direction,detail=False):
    assigned=set_clip(clip,phase)
    hand,handbone=right_hand_target()
    target=hand if detail else center
    cam_data=bpy.data.cameras.new(name+'_camera')
    cam=bpy.data.objects.new(name+'_camera',cam_data)
    bpy.context.scene.collection.objects.link(cam);scene.camera=cam
    cam.location=target+Vector(direction).normalized()*(size.z*(1.3 if detail else 2.8))
    point(cam,target);cam_data.type='ORTHO';cam_data.ortho_scale=(size.z*.42 if detail else frame_size)
    dest=a.out/(name+'.png');scene.render.filepath=str(dest.resolve())
    bpy.ops.render.render(write_still=True)
    assert dest.stat().st_size>60000,('render missing',name)
    return {'file':dest.name,'size':dest.stat().st_size,'clip':assigned,'hand_bone':handbone,'hand_focus_world':list(hand),'camera':list(cam.location),'detail':detail}
renders=[]
renders.append(render('V038_01_idle_front','idle',.10,(.25,-1,.16)))
renders.append(render('V038_02_idle_back','idle',.10,(-.28,1,.18)))
renders.append(render('V038_03_walk_step','walk',.30,(.35,-1,.17)))
renders.append(render('V038_04_sword_hand_detail','idle',.10,(.32,-1,.12),True))
renders.append(render('V038_05_sword_hand_reverse','idle',.10,(-.32,1,.12),True))
report={'status':'V038_ALTERNATIVE_CC0_CHARACTER_REAL_CYCLES_VISUAL_REVIEW_REQUIRED',
  'source_url':'https://www.autosprite.io/free-3d-models/t1-sentinel',
  'license_claim':'CC0 on publisher page, candidate not approved',
  'source_sha256':hashlib.sha256(a.character.read_bytes()).hexdigest(),
  'source_bytes':a.character.stat().st_size,'source_not_edited':True,
  'blender_version':bpy.app.version_string,'engine':'CYCLES',
  'hdri':a.hdri.name,'hdri_depth_bits':tex.image.depth,
  'meshes':len(meshes),'armatures':len(arms),'bones':[b.name for b in arms[0].data.bones],
  'actions':[ac.name for ac in actions],'mesh_object_names':[o.name for o in meshes],
  'material_count':len(bpy.data.materials),'character_bounds_m':[list(lo),list(hi)],
  'equipment_can_be_separated':None,'game_tested':False,'finger_grip_visual_approved':False,
  'renders':renders}
(a.out/'V038_CANDIDATE_CYCLES_QA.json').write_text(json.dumps(report,indent=2))
print('V038_ALTERNATE_REAL_CYCLES_RENDER_QA',json.dumps({'images':len(renders),'bones':len(report['bones']),'actions':report['actions'],'source_sha256':report['source_sha256']}),flush=True)
