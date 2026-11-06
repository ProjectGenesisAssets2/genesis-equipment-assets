#!/usr/bin/env python3
"""Inspect actual CC0 Quaternius Sword_Idle, Sword_Attack and walking on Meshy.

Render actual V12B sword in alternate realistic combat grips, with 32-bit HDRI.
No image generated, no shield substitute, no changes to any approved geometry.
"""
import argparse,math,json,sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_grip_v007_palm_fit import (
 impt,ms,bnd,surface_v12b,lighting,sha,aim,lamp,centroid_for_group,attach_to_socket
)
def assign(arm,clip,fraction):
 matches=[x for x in bpy.data.actions if clip in x.name]
 assert len(matches)==1,(clip,[a.name for a in bpy.data.actions])
 a=matches[0]
 if not arm.animation_data:arm.animation_data_create()
 arm.animation_data.action=a
 if getattr(a,'slots',None):
  slots=list(a.slots)
  if slots:arm.animation_data.action_slot=slots[0]
 start,end=a.frame_range
 bpy.context.scene.frame_set(int(round(start+(end-start)*fraction)))
 bpy.context.view_layer.update()
 return {'clip':a.name,'frame':bpy.context.scene.frame_current,'frame_range':[start,end]}
def main():
 p=argparse.ArgumentParser()
 for k in ('character','sword','hdri','preset','out'):p.add_argument('--'+k,required=True,type=Path)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
 preset=json.loads(a.preset.read_text())
 assert sha(a.sword)==preset['source_original']['sha256']
 assert sha(a.hdri)==preset['lighting']['hdri_sha256']
 bpy.ops.wm.read_factory_settings(use_empty=True)
 person=impt(a.character)
 arms=[ob for ob in person if ob.type=='ARMATURE']
 assert len(arms)==1
 arm=arms[0];assert len(arm.data.bones)==24
 assert len(bpy.data.actions)>=15
 active=assign(arm,'GENESIS_CC0_SWORD_IDLE_V012',0)
 native={}
 for name,bone in (('GENESIS_SOCKET_WEAPON_R','RightHand'),('GENESIS_SOCKET_SHIELD_L','LeftHand')):
  anchor=bpy.data.objects.get(name)
  assert anchor
  # Meshy import fix for Blender Cycles QA only, not native GLB rewrite.
  pos=arm.matrix_world@arm.pose.bones[bone].matrix@Matrix.Translation((0,6,0))
  anchor.parent=None;anchor.matrix_world=pos
  bpy.context.view_layer.update()
  world=anchor.matrix_world.copy()
  anchor.parent=arm;anchor.parent_type='BONE';anchor.parent_bone=bone
  anchor.matrix_world=world
  bpy.context.view_layer.update()
  native[name]=anchor
 sword=impt(a.sword)
 surface=surface_v12b(sword)
 iron=[ob for ob in ms(sword) if any(mat and 'Iron_Blade_V175' in mat.name for mat in ob.data.materials)]
 assert iron
 src0,src1=bnd(sword)
 ext=src1-src0;axis=max(range(3),key=lambda i:ext[i])
 up_axis=Vector(tuple(int(i==axis) for i in range(3)))
 grip=(src0+src1)*.5;grip[axis]=src0[axis]+.175*ext[axis]
 il,ih=bnd(iron);sz=ih-il
 cross=[i for i in range(3) if i!=axis]
 face=Vector(tuple(int(i==min(cross,key=lambda n:sz[n])) for i in range(3)))
 scale=.8925/ext[axis]
 anchor=native['GENESIS_SOCKET_WEAPON_R']
 side=1 if anchor.matrix_world.translation.x>0 else -1
 palm,n=centroid_for_group(ms(person),'RightHand')
 assert palm is not None and n>=50
 hand=palm+Vector((-.013,-.013,-.003))
 def calculate_mount(direction):
  desired=Vector(direction).normalized()
  q=up_axis.rotation_difference(desired)
  existing=q@face
  frontal=Vector((.20,-1,.16))
  projected=(frontal-desired*frontal.dot(desired)).normalized()
  existing=(existing-desired*existing.dot(desired)).normalized()
  rotation=(existing.rotation_difference(projected)@q).to_matrix().to_4x4()
  return Matrix.Translation(hand)@rotation@Matrix.Scale(scale,4)@Matrix.Translation(-grip)
 profiles={
  'rest_lowered':(.11*side,-.06,-.992),
  'combat_forward':(.18*side,-.68,.71),
  'combat_midguard':(.22*side,-.91,.34)}
 first=calculate_mount(profiles['rest_lowered'])
 equipped=attach_to_socket(sword,first,anchor)
 scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=30
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG'
 scene.view_settings.view_transform='AgX'
 scene.view_settings.look='AgX - Medium High Contrast'
 scene.view_settings.exposure=-.22
 hdr=lighting(a.hdri)
 both=ms(person)+ms(sword)
 lo,hi=bnd(both)
 center=Vector((0,0,1.08))
 blade_mid=(bnd(iron)[0]+bnd(iron)[1])*.5
 lamp('V012_KEY',center+Vector((-2.1,-2.4,2.6)),center,102,2.8,3.0)
 lamp('V012_RIM',center+Vector((1.8,1.3,1.9)),center,58,2.0,2.7)
 lamp('V012_SWORD_REFLECTION',blade_mid+Vector((-.75,-1,1)),blade_mid,88,1.5,2.0)
 bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.035))
 floor=bpy.context.object;floor.name='QA_GROUND_ONLY'
 mat=bpy.data.materials.new('QA_GROUND_MAT');mat.diffuse_color=(.035,.035,.038,1.)
 mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(.050,.053,.058,1.0)
 bs.inputs['Roughness'].default_value=.89
 floor.data.materials.append(mat)
 frames=[]
 def render(label,clip,fraction,variant,view,scale_cam=2.50):
  # Set socket transform at SOURCE idle pose, store correct relative transform
  # for every subsequent animation frame. The equipment follows RightHand.
  assign(arm,'GENESIS_CC0_SWORD_IDLE_V012',0)
  target=calculate_mount(profiles[variant])
  equipped.matrix_world=target
  bpy.context.view_layer.update()
  socket_local=anchor.matrix_world.inverted()@equipped.matrix_world
  pose=assign(arm,clip,fraction)
  cam_data=bpy.data.cameras.new('V012_CAMERA_'+label)
  cam=bpy.data.objects.new('V012_CAMERA_'+label,cam_data)
  scene.collection.objects.link(cam);scene.camera=cam
  cam.location=center+Vector(view).normalized()*5.5
  aim(cam,center)
  cam_data.type='ORTHO';cam_data.ortho_scale=scale_cam
  scene.render.resolution_x=1100
  scene.render.resolution_y=1350
  dest=a.out/(label+'.png');scene.render.filepath=str(dest.resolve())
  bpy.ops.render.render(write_still=True)
  assert dest.stat().st_size>120000,(label,'real Cycles render missing')
  frames.append({'image':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest),
   'clip':pose['clip'],'frame':pose['frame'],'sword_variant':variant,
   'source_weapon_socket':anchor.name,
   'sword_world_tip_direction':list(profiles[variant]),
   'socket_relative_matrix':[list(row) for row in socket_local]})
 render('V012_01_original_cc0_sword_idle_lowered','GENESIS_CC0_SWORD_IDLE_V012',0,'rest_lowered',(.5,-1,.12))
 render('V012_02_cc0_sword_idle_combat_forward','GENESIS_CC0_SWORD_IDLE_V012',0,'combat_forward',(.50,-1,.12))
 render('V012_03_cc0_sword_idle_combat_midguard','GENESIS_CC0_SWORD_IDLE_V012',0,'combat_midguard',(.5,-1,.12))
 render('V012_04_cc0_walk_sword_guard','GENESIS_CC0_WALK_SWORD_GUARD_V012',.25,'combat_forward',(.75,-1,.15))
 render('V012_05_cc0_walk_sword_guard_step2','GENESIS_CC0_WALK_SWORD_GUARD_V012',.75,'combat_forward',(.75,-1,.15))
 render('V012_06_cc0_sword_attack','GENESIS_CC0_SWORD_ATTACK_V012',.47,'combat_forward',(.70,-1,.16))
 report={'status':'V012_CC0_QUATERNIUS_REAL_CYCLES_POSE_QA_PENDING_HUMAN_VISUAL_APPROVAL',
 'target_original_bones':24,'total_actions':len(bpy.data.actions),
 'real_cc0_animation_clips':['Sword_Idle','Walk_Loop','Sword_Attack','Jog_Fwd_Loop'],
 'authentic_original_sword_sha256':sha(a.sword),'metal_v175_v12b':surface,
 'sword_length_m':.8925,'hdri':hdr,
 'sword_attached_to_real_bone_socket':equipped.parent==anchor,
 'no_placeholder_shield':True,'approved_shield_model_mounted':False,
 'game_tested':False,'human_visual_approved':False,
 'renders':frames}
 (a.out/'POSE_QA_CC0_V012.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('GENESIS_CC0_QUATERNIUS_REAL_RENDERS_V012',json.dumps({'images':len(frames),
   'bones':24,'actions':len(bpy.data.actions),'authentic_sword':sha(a.sword)}),flush=True)
if __name__=='__main__':main()
