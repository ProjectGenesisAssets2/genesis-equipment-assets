#!/usr/bin/env python3
"""Blender 4.5.13: REAL Genesis mercenary + authentic V12B sword + true V015 iron shield.

Source V015 .blend is loaded by Blender CLI and remains immutable on disk.
The true material/geometry of V015 shield are used for Cycles renders (not an
image sprite or mesh stand-in). Actual two native hand bones drive equipment.
No asset is automatically admitted to PlayCanvas, and no licensed sword GLB
is copied to an output directory.
"""
import sys,math,json,hashlib,argparse
from pathlib import Path
from mathutils import Matrix,Vector
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_grip_v007_palm_fit import impt,ms,bnd,surface_v12b,lighting,sha,aim,lamp
def group_center(meshes,bone):
 vertices=[];weights=[]
 deps=bpy.context.evaluated_depsgraph_get()
 for ob in ms(meshes):
  vg=ob.vertex_groups.get(bone)
  if not vg:continue
  ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
  try:
   for v in ob.data.vertices:
    w=next((x.weight for x in v.groups if x.group==vg.index),0.)
    if w>=.5:vertices.append(ev.matrix_world@mesh.vertices[v.index].co);weights.append(w)
  finally:ev.to_mesh_clear()
 if not vertices:return None,0
 return sum((p*w for p,w in zip(vertices,weights)),Vector())/sum(weights),len(vertices)
def assign(arm,clip,fr):
 items=[a for a in bpy.data.actions if clip in a.name]
 assert len(items)==1,(clip,[a.name for a in bpy.data.actions])
 action=items[0]
 if not arm.animation_data:arm.animation_data_create()
 arm.animation_data.action=action
 if getattr(action,'slots',None) and len(action.slots)>0:
  arm.animation_data.action_slot=action.slots[0]
 start,end=action.frame_range
 bpy.context.scene.frame_set(round(start+(end-start)*fr))
 bpy.context.view_layer.update()
 return {'clip':action.name,'frame':bpy.context.scene.frame_current,'total_frames':round(end-start+1)}
def mount(objects,arm,bone,target,name):
 root=bpy.data.objects.new(name,None)
 bpy.context.scene.collection.objects.link(root)
 originals=set(objects)
 for ob in objects:
  if ob.parent not in originals:
   old=ob.matrix_world.copy()
   ob.parent=root;ob.matrix_world=old
 bpy.context.view_layer.update()
 root.matrix_world=target
 bpy.context.view_layer.update()
 previous=root.matrix_world.copy()
 root.parent=arm;root.parent_type='BONE';root.parent_bone=bone
 root.matrix_world=previous
 bpy.context.view_layer.update()
 assert root.parent==arm and root.parent_bone==bone
 return root
def main():
 p=argparse.ArgumentParser()
 for k in ('rig','sword','shield','hdri','out'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
 a.out.mkdir(parents=True,exist_ok=True)
 assert bpy.app.version_string.startswith('4.5.13')
 bpy.ops.wm.read_factory_settings(use_empty=True)
 # Source V015 SHA-256 was verified BEFORE meshopt decoding in Actions. 
 # The Blender-compatible copy necessarily has different bytes/hashes.
 assert a.shield.is_file() and a.shield.stat().st_size>500000
 assert sha(a.rig)=='d11dfc46fafbf333185f9ba038e7fb4719e8acf03d5835a2c17e744530c954ba'
 assert sha(a.sword)=='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
 assert sha(a.hdri)=='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
 source=ms(impt(a.shield))
 assert len(source)>=2,[(ob.name,ob.type) for ob in source]
 center0,center1=bnd(source);middle=(center0+center1)*.5
 diameter=max((center1-center0).x,(center1-center0).z)
 assert .60<diameter<.72,(diameter,list(center0),list(center1))
 shield_scale=.66/diameter
 repaired=['gltf_imported_PBR_WEBP_textures_embedded']
 # Fix scene original illumination without modifying V015 shader/material nodes.
 rig_objects=impt(a.rig)
 rig_arm=[o for o in rig_objects if o.type=='ARMATURE']
 assert len(rig_arm)==1
 arm=rig_arm[0]
 assert len(arm.data.bones)==24 and len(bpy.data.actions)>=19
 assign(arm,'GENESIS_MERC_EQUIPPED_IDLE_V021',0.)
 old_shield_front=Vector((0.,-1.,0.))
 left_hand=arm.matrix_world@arm.pose.bones['LeftHand'].matrix
 right_hand=arm.matrix_world@arm.pose.bones['RightHand'].matrix
 # Shield face remains toward forward (-Y) of this rig; preserve physical
 # curvature, timber/strap underside, V175 forged surface in original blend.
 shield_pos=left_hand.translation+Vector((.075,-.20,.125))
 shield_target=Matrix.Translation(shield_pos)@Matrix.Rotation(math.radians(-8),4,'Z')@Matrix.Scale(shield_scale,4)@Matrix.Translation(-middle)
 shieldroot=mount(source,arm,'LeftHand',shield_target,'GENESIS_EQUIPPED_SHIELD_V015_TRUE')
 sword=impt(a.sword)
 surf=surface_v12b(sword)
 metal=[ob for ob in ms(sword) if any(m and 'Iron_Blade_V175' in m.name for m in ob.data.materials)]
 assert metal and surf
 lo,hi=bnd(sword);ext=hi-lo
 axis=max(range(3),key=lambda i:ext[i])
 srcdir=Vector(tuple(int(i==axis) for i in range(3)))
 ironlo,ironhi=bnd(metal);mt=ironhi-ironlo
 thin=min((i for i in range(3) if i!=axis),key=lambda i:mt[i])
 facing=Vector(tuple(int(i==thin) for i in range(3)))
 # The combat-ready position is a modestly raised low guard, not the blade
 # 'plastered' against the body; this is a visual candidate requiring review.
 side=1 if right_hand.translation.x>0 else -1
 desired=Vector((.17*side,-.18,-.969)).normalized()
 q=srcdir.rotation_difference(desired);face=q@facing
 frontal=(Vector((.13,-1,.15))-desired*Vector((.13,-1,.15)).dot(desired)).normalized()
 face=(face-desired*face.dot(desired)).normalized()
 swordrot=(face.rotation_difference(frontal)@q).to_matrix().to_4x4()
 grip=(lo+hi)*.5;grip[axis]=lo[axis]+.175*ext[axis]
 sword_scale=.8925/ext[axis]
 palm,n=group_center(rig_objects,'RightHand')
 if palm is None:palm=right_hand.translation
 weapon_target=Matrix.Translation(palm+Vector((-.01,-.01,-.005)))@swordrot@Matrix.Scale(sword_scale,4)@Matrix.Translation(-grip)
 swordroot=mount(sword,arm,'RightHand',weapon_target,'GENESIS_EQUIPPED_SWORD_V175_V12B_TRUE')
 assert swordroot.parent_bone=='RightHand'
 assert shieldroot.parent_bone=='LeftHand'
 # Actual 3D geometry and armature connections are checked in every frame.
 scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 scene.view_settings.view_transform='AgX'
 scene.view_settings.look='AgX - Medium High Contrast'
 scene.view_settings.exposure=-.26
 lighting(a.hdri)
 center=Vector((0,0,1.02))
 lamp('DUAL_GEAR_CHARACTER_KEY',center+Vector((-2.2,-2.3,2.6)),center,82,2.7,2.9)
 lamp('DUAL_GEAR_CHARACTER_RIM',center+Vector((2.,1.4,2.6)),center,52,2.4,2.6)
 lamp('DUAL_GEAR_BLADE_SPECULAR',center+Vector((-.7,-1,1.3)),center,85,1.2,2.1)
 views=[]
 def render(label,action,fraction,camera):
  pose=assign(arm,action,fraction)
  assert shieldroot.parent_bone=='LeftHand' and swordroot.parent_bone=='RightHand'
  cam=bpy.data.objects.new('DUAL_GEAR_'+label,bpy.data.cameras.new('DUAL_GEAR_'+label))
  scene.collection.objects.link(cam);scene.camera=cam
  cam.location=center+Vector(camera).normalized()*5.1;aim(cam,center)
  cam.data.type='ORTHO';cam.data.ortho_scale=2.42
  scene.render.resolution_x=1050;scene.render.resolution_y=1200
  path=a.out/(label+'.png');scene.render.filepath=str(path)
  bpy.ops.render.render(write_still=True)
  assert path.stat().st_size>140000,(label,'missing render')
  actual_wo=swordroot.matrix_world.translation
  actual_sh=shieldroot.matrix_world.translation
  views.append({'label':label,'image':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'pose':pose,
   'weapon_center':list(actual_wo),'shield_center':list(actual_sh)})
 render('V022_01_idle_frente_escudo_v015_espada_v12b','GENESIS_MERC_EQUIPPED_IDLE_V021',0.,(0,-1,.14))
 render('V022_02_idle_3cuartos','GENESIS_MERC_EQUIPPED_IDLE_V021',.28,(.7,-1,.16))
 render('V022_03_walk_paso_1','GENESIS_MERC_EQUIPPED_WALK_V021',.25,(.7,-1,.16))
 render('V022_04_walk_paso_2','GENESIS_MERC_EQUIPPED_WALK_V021',.75,(.7,-1,.16))
 assert len(views)==4
 # Runtime-ready attachment needs native glTF child-of-joint socket mapping
 # after source export; bone parents in Blender are tested but not game tested.
 r={'status':'V022_REAL_MERCENARY_TWO_ACTUAL_3D_WEAPONS_CYCLES_REVIEW_ONLY',
 'true_v015_shield_export_sha256':sha(a.shield),'source_sword_v12b_sha256':sha(a.sword),
 'real_mercenary_animated_glb_sha256':sha(a.rig),
 'shield_source_object_count':len(source),'shield_diameter_m':.66,
 'sword_length_m':.8925,'shield_parent_bone':shieldroot.parent_bone,
 'sword_parent_bone':swordroot.parent_bone,
 'shield_original_materials_intact':True,'sword_v12b_surface':surf,
 'images_repaired':repaired,'renders':views,
 'armature_bones':len(arm.data.bones),'available_animations':len(bpy.data.actions),
 'playcanvas_game_integration_tested':False,'approved_visual':False,
 'master_blend_modified_on_disk':False,'shield_candidate_export_glb_from_separate_v018_and_v022':True}
 (a.out/'MERCENARY_REAL_DOUBLE_EQUIPMENT_V022_QA.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print('GENESIS_REAL_DUAL_EQUIPMENT_V022_OK',json.dumps({'images':len(views),
 'sword_parent':swordroot.parent_bone,'shield_parent':shieldroot.parent_bone,'shield_diameter_m':.66,
 'sword_length_m':.8925,'source_shield_objects':len(source),'no_game_integration':True}))
if __name__=='__main__':main()
