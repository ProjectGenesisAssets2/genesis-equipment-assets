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
 for k in ('character','sword','shield','hdri','preset','out'):p.add_argument('--'+k,required=True,type=Path)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
 preset=json.loads(a.preset.read_text())
 assert sha(a.sword)==preset['source_original']['sha256']
 assert sha(a.shield)=='a169a827b70621ec21eeaa894b3cf10eebfacc0eb1ed5bb575d9ff8f275a6ec2'
 assert sha(a.hdri)==preset['lighting']['hdri_sha256']
 bpy.ops.wm.read_factory_settings(use_empty=True)
 person=impt(a.character)
 arms=[ob for ob in person if ob.type=='ARMATURE']
 assert len(arms)==1
 arm=arms[0];assert len(arm.data.bones)==24
 assert len(bpy.data.actions)>=19
 active=assign(arm,'GENESIS_MERC_EQUIPPED_IDLE_V021',0)
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
 # Exactly the V015 hand-made shield source, 15 mesh components, reduced 2K WebP
 # for WebGL but NO geometry substitution. Parent to the real LEFT HAND socket.
 shield=impt(a.shield)
 shmesh=ms(shield)
 assert len(shmesh)>=2,('V015 authentic shield geometry missing',len(shmesh))
 low,high=bnd(shmesh)
 dims=high-low
 assert .60<max(dims.x,dims.z)<.72,(dims,'shield must be 66 cm')
 assert dims.y<.20,(dims,'shield must face forward/back, not sideways')
 left_palm,left_verts=centroid_for_group(ms(person),'LeftHand')
 assert left_palm is not None and left_verts>40
 # Native idle real hand is at waist (no face-covering Quaternius guard).
 # Real shield centre sits forward and slightly outward of that hand.
 shield_center=left_palm+Vector((.145,-.205,.035))
 shield_target=Matrix.Translation(shield_center)@Matrix.Rotation(math.radians(9),4,'Z')
 shieldroot=attach_to_socket(shield,shield_target,native['GENESIS_SOCKET_SHIELD_L'])
 assert shieldroot.parent==native['GENESIS_SOCKET_SHIELD_L']
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
  'rest_lowered':(.17*side,-.18,-.969),
  'combat_forward':(.22*side,-.35,-.91),
  'combat_midguard':(.18*side,-.52,-.84)}
 first=calculate_mount(profiles['rest_lowered'])
 equipped=attach_to_socket(sword,first,anchor)
 scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=34
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format='PNG'
 scene.view_settings.view_transform='AgX'
 scene.view_settings.look='AgX - Medium High Contrast'
 scene.view_settings.exposure=-.22
 hdr=lighting(a.hdri)
 both=ms(person)+ms(sword)+ms(shield)
 lo,hi=bnd(both)
 center=Vector((0,0,1.08))
 blade_mid=(bnd(iron)[0]+bnd(iron)[1])*.5
 lamp('V022_KEY',center+Vector((-2.1,-2.4,2.6)),center,102,2.8,3.0)
 lamp('V022_RIM',center+Vector((1.8,1.3,1.9)),center,58,2.0,2.7)
 lamp('V022_SWORD_REFLECTION',blade_mid+Vector((-.75,-1,1)),blade_mid,88,1.5,2.0)
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
  assign(arm,'GENESIS_MERC_EQUIPPED_IDLE_V021',0)
  target=calculate_mount(profiles[variant])
  equipped.matrix_world=target
  bpy.context.view_layer.update()
  socket_local=anchor.matrix_world.inverted()@equipped.matrix_world
  pose=assign(arm,clip,fraction)
  assert shieldroot.parent==native['GENESIS_SOCKET_SHIELD_L']
  assert equipped.parent==native['GENESIS_SOCKET_WEAPON_R']
  measured_shield=(bnd(shmesh)[0]+bnd(shmesh)[1])*.5
  face_head=(arm.matrix_world@arm.pose.bones['Head'].matrix).translation
  head_delta=face_head.z-measured_shield.z
  assert head_delta>.22,('SHIELD COVERS FACE',label,head_delta)
  cam_data=bpy.data.cameras.new('V022_CAMERA_'+label)
  cam=bpy.data.objects.new('V022_CAMERA_'+label,cam_data)
  scene.collection.objects.link(cam);scene.camera=cam
  cam.location=center+Vector(view).normalized()*5.5
  aim(cam,center)
  cam_data.type='ORTHO';cam_data.ortho_scale=scale_cam
  scene.render.resolution_x=1080
  scene.render.resolution_y=1280
  dest=a.out/(label+'.png');scene.render.filepath=str(dest.resolve())
  bpy.ops.render.render(write_still=True)
  assert dest.stat().st_size>120000,(label,'real Cycles render missing')
  frames.append({'image':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest),
   'clip':pose['clip'],'frame':pose['frame'],'sword_variant':variant,
   'source_weapon_socket':anchor.name,
   'shield_head_vertical_clearance_m':round(head_delta,3),
   'shield_center_world':list(measured_shield),
   'sword_world_tip_direction':list(profiles[variant]),
   'socket_relative_matrix':[list(row) for row in socket_local]})
 render('V022_01_idle_real_mercenary_sword_down','GENESIS_MERC_EQUIPPED_IDLE_V021',0,'rest_lowered',(.50,-1,.12))
 render('V022_02_idle_34_real_mercenary_sword','GENESIS_MERC_EQUIPPED_IDLE_V021',.48,'rest_lowered',(.66,-1,.14))
 render('V022_03_walk_step_025','GENESIS_MERC_EQUIPPED_WALK_V021',.25,'rest_lowered',(.75,-1,.15))
 render('V022_04_walk_step_075','GENESIS_MERC_EQUIPPED_WALK_V021',.75,'rest_lowered',(.75,-1,.15))
 render('V022_05_sword_attack','GENESIS_MERC_EQUIPPED_ATTACK_V021',.47,'rest_lowered',(.70,-1,.16))
 render('V022_06_shield_block_unarmed_left','GENESIS_MERC_EQUIPPED_BLOCK_V021',.53,'rest_lowered',(.70,-1,.16))
 report={'status':'V022_CC0_QUATERNIUS_REAL_CYCLES_POSE_QA_PENDING_HUMAN_VISUAL_APPROVAL',
 'target_original_bones':24,'total_actions':len(bpy.data.actions),
 'real_cc0_animation_clips':['Meshy original Idle_02','Quaternius Walk_Loop','Quaternius Sword_Attack'],
 'authentic_original_sword_sha256':sha(a.sword),'metal_v175_v12b':surface,
 'sword_length_m':.8925,'hdri':hdr,
 'sword_attached_to_real_bone_socket':equipped.parent==anchor,
 'no_placeholder_shield':True,'approved_shield_model_mounted':True,
 'shield_v015_optimization_kept_15_real_parts':True,
 'shield_gltf_draw_mesh_groups':len(shmesh),
 'shield_glb_verified_sha256':sha(a.shield),
 'shield_attached_to_real_left_hand_socket':shieldroot.parent==native['GENESIS_SOCKET_SHIELD_L'],
 'game_tested':False,'human_visual_approved':False,
 'renders':frames}
 (a.out/'POSE_QA_DUAL_NATURAL_V022.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('GENESIS_NATURAL_TRUE_DUAL_EQUIPMENT_CYCLES_V022',json.dumps({'images':len(frames),
   'bones':24,'actions':len(bpy.data.actions),'authentic_sword':sha(a.sword)}),flush=True)
if __name__=='__main__':main()
