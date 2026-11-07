#!/usr/bin/env python3
"""Actual Blender Cycles HDRI32 explorer QA, never concepts. V024 experimental."""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_grip_v007_palm_fit import impt, ms, bnd, surface_v12b, lighting, sha, aim, lamp, centroid_for_group, attach_to_socket
from qa_natural_dual_real_v023 import assign

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
 arms=[o for o in person if o.type=='ARMATURE'];assert len(arms)==1
 arm=arms[0];assert len(arm.data.bones)==24
 expected=['GENESIS_MERC_IDLE_V024','GENESIS_MERC_WALK_V024','GENESIS_MERC_INSPECT_SWORD_V024','GENESIS_MERC_INSPECT_SHIELD_V024','GENESIS_MERC_WALK_EQUIPPED_V024']
 assert len(bpy.data.actions)>=5
 for n in expected:assert len([x for x in bpy.data.actions if n in x.name])==1,n
 assign(arm,expected[0],0)
 native={}
 for name,bone in (('GENESIS_SOCKET_WEAPON_R','RightHand'),('GENESIS_SOCKET_SHIELD_L','LeftHand')):
  anchor=bpy.data.objects.get(name);assert anchor,(name,'missing socket')
  pos=arm.matrix_world@arm.pose.bones[bone].matrix@Matrix.Translation((0,6,0))
  anchor.parent=None;anchor.matrix_world=pos
  bpy.context.view_layer.update();world=anchor.matrix_world.copy()
  anchor.parent=arm;anchor.parent_type='BONE';anchor.parent_bone=bone
  anchor.matrix_world=world;bpy.context.view_layer.update();native[name]=anchor
 shield=impt(a.shield);shmesh=ms(shield)
 sh_lo,sh_hi=bnd(shmesh);dims=sh_hi-sh_lo
 assert .60<max(dims.x,dims.z)<.72
 left_palm,n=centroid_for_group(ms(person),'LeftHand');assert left_palm and n>40
 shield_target=Matrix.Translation(left_palm+Vector((.145,-.205,.035)))@Matrix.Rotation(math.radians(9),4,'Z')
 shieldroot=attach_to_socket(shield,shield_target,native['GENESIS_SOCKET_SHIELD_L'])
 sword=impt(a.sword);surface=surface_v12b(sword)
 iron=[o for o in ms(sword) if any(m and 'Iron_Blade_V175' in m.name for m in o.data.materials)];assert iron
 src0,src1=bnd(sword);extent=src1-src0
 axis=max(range(3),key=lambda i:extent[i]);up_axis=Vector(tuple(int(i==axis) for i in range(3)))
 grip=(src0+src1)*.5;grip[axis]=src0[axis]+.175*extent[axis]
 i0,i1=bnd(iron);ext=i1-i0;cross=[i for i in range(3) if i!=axis]
 face=Vector(tuple(int(i==min(cross,key=lambda n:ext[n])) for i in range(3)))
 scale=.8925/extent[axis]
 right_palm,n=centroid_for_group(ms(person),'RightHand');assert right_palm and n>=50
 hand=right_palm+Vector((-.013,-.013,-.003))
 anchor=native['GENESIS_SOCKET_WEAPON_R'];side=1 if anchor.matrix_world.translation.x>0 else -1
 desired=Vector((.17*side,-.18,-.969)).normalized();q=up_axis.rotation_difference(desired)
 frontal=Vector((.20,-1,.16));project=(frontal-desired*frontal.dot(desired)).normalized()
 projected=(q@face-desired*(q@face).dot(desired)).normalized()
 rotation=(projected.rotation_difference(project)@q).to_matrix().to_4x4()
 sword_target=Matrix.Translation(hand)@rotation@Matrix.Scale(scale,4)@Matrix.Translation(-grip)
 swordroot=attach_to_socket(sword,sword_target,anchor)
 assert swordroot.parent==anchor and shieldroot.parent==native['GENESIS_SOCKET_SHIELD_L']

 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=38
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.22
 hdr=lighting(a.hdri)
 center=Vector((0,0,1.08));blade=(bnd(iron)[0]+bnd(iron)[1])*.5
 lamp('V024_KEY',center+Vector((-2.1,-2.4,2.6)),center,102,2.8,3.0)
 lamp('V024_RIM',center+Vector((1.8,1.3,1.9)),center,58,2.0,2.7)
 lamp('V024_SWORD_REFLECTION',blade+Vector((-.75,-1,1)),blade,88,1.5,2.0)
 bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.035))
 floor=bpy.context.object;floor.name='QA_GROUND_ONLY'
 mat=bpy.data.materials.new('QA_FLOOR');mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.05,.053,.058,1)
 bs.inputs['Roughness'].default_value=.89;floor.data.materials.append(mat)
 poses=[]
 def render(label,clip,phase,has_sword,has_shield,camdir=(.68,-1,.16)):
  pose=assign(arm,clip,phase)
  for m in ms(sword):m.hide_render=not has_sword
  for m in ms(shield):m.hide_render=not has_shield
  assert all(m.hide_render== (not has_sword) for m in ms(sword))
  assert all(m.hide_render== (not has_shield) for m in ms(shield))
  cam_data=bpy.data.cameras.new('V024_CAM_'+label);cam=bpy.data.objects.new('V024_CAM_'+label,cam_data)
  scene.collection.objects.link(cam);scene.camera=cam;cam.location=center+Vector(camdir).normalized()*5.5
  aim(cam,center);cam_data.type='ORTHO';cam_data.ortho_scale=2.5
  scene.render.resolution_x=900;scene.render.resolution_y=1080
  target=a.out/(label+'.png');scene.render.filepath=str(target.resolve())
  bpy.ops.render.render(write_still=True);assert target.stat().st_size>50000,target
  poses.append({'file':target.name,'sha256':sha(target),'bytes':target.stat().st_size,'clip':clip,'phase':phase,
    'sword_visible':has_sword,'shield_visible':has_shield,'rigged_character':True,'real_Cycles':True})

 render('V024_01_idle_sin_equipo',expected[0],.0,False,False)
 render('V024_02_caminar_sin_equipo',expected[1],.25,False,False)
 render('V024_03_inspeccionar_espada',expected[2],.54,True,False)
 render('V024_04_inspeccionar_escudo',expected[3],.54,False,True)
 render('V024_05_caminar_equipado_paso1',expected[4],.25,True,True)
 render('V024_06_caminar_equipado_paso2',expected[4],.75,True,True)
 report={'status':'V024_CYCLES32_REAL_POSE_REVIEW_PENDING_HUMAN_APPROVAL',
  'character_sha256':sha(a.character),'sword_sha256':sha(a.sword),'shield_sha256':sha(a.shield),
  'hdri':hdr,'bones':len(arm.data.bones),'clips':expected,'sword_surface':surface,
  'weapon_socket':anchor.name,'shield_socket':native['GENESIS_SOCKET_SHIELD_L'].name,
  'weapon_parent_correct':swordroot.parent==anchor,
  'shield_parent_correct':shieldroot.parent==native['GENESIS_SOCKET_SHIELD_L'],
  'playcanvas_tested':False,'human_approved':False,'renders':poses}
 (a.out/'MERCENARY_EXPLORER_V024_RENDER_QA.json').write_text(json.dumps(report,indent=2))
 print('V024_EXPLORER_CYCLES_RENDER_OK',json.dumps({'renders':len(poses),'rig':24,'actions':len(bpy.data.actions)}),flush=True)
if __name__=='__main__':main()
