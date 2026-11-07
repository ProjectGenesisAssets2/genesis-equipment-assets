#!/usr/bin/env python3
"""Project Genesis V043 – original Quaternius CC0 Male Ranger.
Import *existing* 65-joint skinned medieval outfit, export identical source
as a single GLB, and Cycles-render authentic body and digit deformation tests.
No rig generated, no main, no animations added, no human approval implied.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser()
for k in ('source','hdri','out'):ap.add_argument('--'+k,required=True,type=Path)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
src=a.source.read_bytes()
assert a.source.suffix=='.gltf'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
scene=bpy.context.scene
meshes=[ob for ob in bpy.data.objects if ob.type=='MESH']
arms=[ob for ob in bpy.data.objects if ob.type=='ARMATURE']
assert len(arms)==1 and len(meshes)>=5,(len(arms),len(meshes))
arm=arms[0]
named=set(p.name for p in arm.pose.bones)
assert len(arm.data.bones)==65,len(arm.data.bones)
left=[n for n in named if n.endswith('_l') and any(s in n for s in ('index','middle','ring','pinky','thumb'))]
right=[n for n in named if n.endswith('_r') and any(s in n for s in ('index','middle','ring','pinky','thumb'))]
assert len(left)>=15 and len(right)>=15,(left,right)
assert 'hand_r' in named and 'hand_l' in named

# Never apply the posed finger test to the exported original.
bpy.ops.object.select_all(action='DESELECT')
for ob in [arm]+meshes:ob.select_set(True)
bpy.context.view_layer.objects.active=arm
rigged_glb=a.out/'GENESIS_QUATERNIUS_MALE_RANGER_ORIGINAL_RIGGED_V043.glb'
bpy.ops.export_scene.gltf(filepath=str(rigged_glb.resolve()),export_format='GLB',use_selection=True,export_animations=False)
assert rigged_glb.exists() and rigged_glb.stat().st_size>1_000_000

corners=[ob.matrix_world@Vector(b) for ob in meshes for b in ob.bound_box]
lo=Vector([min(c[k] for c in corners) for k in range(3)])
hi=Vector([max(c[k] for c in corners) for k in range(3)])
center=(lo+hi)*.5
size=hi-lo
assert 1.3<size.z<3.5,('out of expected model dimensions after import',list(size))
assert .5<size.x<2.4,('out of expected model width after import',list(size))
print('V043_ACTUAL_CHARACTER_DIMENSIONS',list(size),flush=True)

world=bpy.data.worlds.new('GENESIS_CC0_RANGER_PBR_EXR32')
scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96
bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.75
out=nodes.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],out.inputs['Surface'])
def aim(ob,target):
 ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,offset,power,radius):
 dat=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,dat)
 scene.collection.objects.link(ob);ob.location=center+Vector(offset)
 aim(ob,center);dat.energy=power;dat.shape='DISK';dat.size=radius
area('V043_KEY',(-2,-2.0,2),600,3)
area('V043_RIM',(2,1.5,1.9),380,2.4)
bpy.ops.mesh.primitive_plane_add(size=9,location=(center.x,center.y,lo.z-.023))
floor=bpy.context.object;floor.name='V043_QA_FLOOR_NOT_SOURCE'
mat=bpy.data.materials.new('QA_Stone_Grey');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.10,.105,.11,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.84
floor.data.materials.append(mat)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=26
scene.render.resolution_x=650;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.15
images=[]
def render(name,camdir,target=None,scale=None):
 focus=center if target is None else target
 if scale is None: scale=max(size.z*1.22,size.x*1.5)
 camdata=bpy.data.cameras.new(name+'_Lens')
 cam=bpy.data.objects.new(name+'_Camera',camdata)
 scene.collection.objects.link(cam);scene.camera=cam
 cam.location=focus+Vector(camdir).normalized()*4
 aim(cam,focus);camdata.type='ORTHO';camdata.ortho_scale=scale
 dst=a.out/(name+'.png');scene.render.filepath=str(dst.resolve())
 bpy.ops.render.render(write_still=True)
 assert dst.exists() and dst.stat().st_size>50000,(name,dst.stat().st_size)
 images.append(name+'.png')
render('V043_01_RANGER_FRONT',(.16,-1,.12))
render('V043_02_RANGER_THREEQUARTER',(.82,-1,.18))
render('V043_03_RANGER_BACK',(-.25,1,.12))
bpy.context.view_layer.update()
def hand(name):
 return (arm.matrix_world@arm.pose.bones[name].matrix).translation
right_hand=hand('hand_r');left_hand=hand('hand_l')
render('V043_04_RIGHT_HAND_RELAXED',(.28,-1,.18),right_hand,.62)
render('V043_05_LEFT_HAND_RELAXED',(-.28,-1,.18),left_hand,.62)

def evaluated_positions():
 deps=bpy.context.evaluated_depsgraph_get()
 values={}
 for ob in meshes:
  evalob=ob.evaluated_get(deps)
  m=evalob.to_mesh()
  try:values[ob.name]=[tuple(evalob.matrix_world@v.co) for v in m.vertices]
  finally:evalob.to_mesh_clear()
 return values
before=evaluated_positions()
# Finger test. No glove sculpting or fake rig: bend actual original
# independently-weighted joints. The axis is a *diagnostic* rotation only.
testnames=[]
for side in ('r','l'):
 for finger in ('index','middle','ring','pinky','thumb'):
  for segment in (1,2,3):
   name=f'{finger}_{segment:02d}_{side}'
   if name not in named:continue
   pb=arm.pose.bones[name]
   pb.rotation_mode='XYZ'
   pb.rotation_euler[0]=math.radians(26 if segment==1 else 19)
   testnames.append(name)
assert len(testnames)>=30,len(testnames)
bpy.context.view_layer.update()
after=evaluated_positions()
maxdisp=0.;moved=0
for objname,base in before.items():
 for p0,p1 in zip(base,after[objname]):
  dist=math.dist(p0,p1)
  if dist>.001:moved+=1
  maxdisp=max(maxdisp,dist)
assert moved>=400 and maxdisp>.012,('finger pose not deforming mesh',moved,maxdisp)
render('V043_06_RIGHT_HAND_FINGER_BEND',(.28,-1,.18),right_hand,.62)
render('V043_07_LEFT_HAND_FINGER_BEND',(-.28,-1,.18),left_hand,.62)

qa={'status':'V043_SOURCE_FINGER_RIG_REAL_RENDER_QA_UNAPPROVED',
 'source_gltf_sha256':hashlib.sha256(src).hexdigest(),
 'single_glb_sha256':hashlib.sha256(rigged_glb.read_bytes()).hexdigest(),
 'single_glb_bytes':rigged_glb.stat().st_size,
 'preexisting_skin_bones':len(arm.data.bones),
 'real_finger_bones_left':len(left),'real_finger_bones_right':len(right),
 'finger_joint_tested':testnames,'actual_mesh_vertices_moved_by_finger_preset':moved,
 'max_vertex_displacement_m':round(maxdisp,5),
 'meshes':len(meshes),'PBR_materials':len(bpy.data.materials),
 'size_m':list(size),'renders':images,
 'Cycles':True,'HDRI_source':a.hdri.name,'HDRI_bits_RGB':env.image.depth,
 'source_original_rig_and_geometry':True,
 'sword_V12B_tested':False,'shield_V015_tested':False,
 'animation_tested':False,'Mixamo_tested':False,
 'PlayCanvas_tested':False,'human_approved':False}
(a.out/'V043_MALE_RANGER_REAL_CYCLES_FINGER_QA.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False))
print('V043_REAL_CC0_MEDIEVAL_RANGER_FINGER_DEFORMATION_CYCLES32_PASS',json.dumps({'bones':len(arm.data.bones),'left_fingers':len(left),'right_fingers':len(right),'vertices_moved':moved,'max_displacement_m':maxdisp,'GLB_sha256':qa['single_glb_sha256'],'renders':len(images)}),flush=True)
