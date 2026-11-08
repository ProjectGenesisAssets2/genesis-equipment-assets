#!/usr/bin/env python3
"""Project Genesis V044 genuine 65-joint Quaternius-to-Meshy experimental rig.
Use authentic downloaded Meshy model and pre-existing Quaternius Ranger 65-bone
armature. Fit source bones to Meshy A-pose, skin Meshy geometry with actual
individual finger groups, test live deformations and render Cycles+EXR32.
Neither original model is edited. No false approved / Mixamo / playable claim.
"""
import argparse,sys,json,math,hashlib
from pathlib import Path
import bpy
from mathutils import Vector,Quaternion,Matrix

p=argparse.ArgumentParser()
for v in ('meshy','donor','hdri','out'):
 p.add_argument('--'+v,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.meshy)=='0452096d35bb41d992bc3508ee05f9cdc2a6ee34bb472a60c33eb9b22b66f005'
assert sha(a.donor)=='2b8a1358f165fb7a1afa5930c4a3d92a9fff11ea01c63df18d368735fdbb29af'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.donor.resolve()))
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(arms)==1
arm=arms[0];assert len(arm.data.bones)==65,len(arm.data.bones)
# Donor body is discarded; keep precisely its original existing bone hierarchy.
for o in list(bpy.data.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
rest={}
for bone in arm.data.bones:
 rest[bone.name]=(arm.matrix_world@bone.head_local,arm.matrix_world@bone.tail_local,bone.parent.name if bone.parent else None)
assert 'thumb_01_r' in rest and 'index_03_l' in rest
# Imported CC0 rig is normalized to world axes, then bones are refitted to
# actual A-pose of Meshy; parent relationships/65 bone names are unchanged.
arm.matrix_world=Matrix.Identity(4)

before={o.name for o in bpy.data.objects}
bpy.ops.import_scene.gltf(filepath=str(a.meshy.resolve()))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert len(meshes)==1
mesh=meshes[0]
mesh.name='MESHY_WEARY_WARRIOR_ORIGINAL_GEOMETRY_V044'
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.context.view_layer.update()
loz=min((mesh.matrix_world@v.co).z for v in mesh.data.vertices)
mesh.location.z-=loz
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
verts=len(mesh.data.vertices)
assert verts==9277,verts
vcoords=[v.co.copy() for v in mesh.data.vertices]
bounds=[[round(fn(v[k] for v in vcoords),4) for fn in (min,max)] for k in range(3)]
assert 1.95<max(v.z for v in vcoords)<2.06
print('V044_ACTUAL_MESHY_ORIGINAL_BOUNDS',bounds,flush=True)

# Refitted anatomical points (Blender Z-up; body faces -Y).
# +/-X are limbs on each side, arms lowered exactly like Meshy source.
spec={
 'root':((0,0,.93),(0,0,.96)),
 'pelvis':((0,0,.96),(0,0,1.08)),
 'spine_01':((0,0,1.08),(0,0,1.25)),
 'spine_02':((0,0,1.25),(0,0,1.43)),
 'spine_03':((0,0,1.43),(0,0,1.56)),
 'neck_01':((0,0,1.56),(0,0,1.68)),
 'Head':((0,0,1.68),(0,0,1.90))
}
for side,sign in [('l',1),('r',-1)]:
 def v(x,y,z):return(sign*x,y,z)
 spec.update({
  'clavicle_'+side:(v(.07,-.008,1.53),v(.185,-.008,1.50)),
  'upperarm_'+side:(v(.185,-.008,1.50),v(.276,-.018,1.22)),
  'lowerarm_'+side:(v(.276,-.018,1.22),v(.328,-.025,.94)),
  'hand_'+side:(v(.328,-.025,.94),v(.343,-.020,.836)),
  'thigh_'+side:(v(.112,0,.96),v(.118,-.012,.56)),
  'calf_'+side:(v(.118,-.012,.56),v(.128,-.02,.14)),
  'foot_'+side:(v(.128,-.02,.14),v(.128,-.116,.075)),
  'ball_'+side:(v(.128,-.116,.075),v(.128,-.190,.065)),
  'ball_leaf_'+side:(v(.128,-.190,.065),v(.128,-.225,.06)),
 })
# Transfer donor finger chains relative to donor wrist to new Meshy wrist.
# This preserves the proven thumb/index/middle/ring/pinky topology (four nodes
# each), while rotating horizontal T-pose hand bones to vertical A-pose hands.
finger_pos={}
for side in ('l','r'):
 old_wrist,old_palm,_=rest['hand_'+side]
 new_wrist=Vector(spec['hand_'+side][0])
 new_palm=Vector(spec['hand_'+side][1])
 old_axis=old_palm-old_wrist
 assert old_axis.length>.025,('donor hand rest too short',side)
 orientation=old_axis.rotation_difference(new_palm-new_wrist)
 for finger in ('thumb','index','middle','ring','pinky'):
  for idx in range(1,5):
   name=(f'{finger}_{idx:02d}_'+side if idx<=3 else f'{finger}_04_leaf_'+side)
   head,tail,_=rest[name]
   scale=.77
   new_head=new_wrist+orientation@((head-old_wrist)*scale)
   new_tail=new_wrist+orientation@((tail-old_wrist)*scale)
   if (new_tail-new_head).length<.001:new_tail=new_head+Vector((0,0,-.005))
   finger_pos[name]=(new_head,new_tail)
# Avoid zero-length edit bones, preserve hierarchy and original names.
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,b in arm.data.edit_bones.items():
 b.use_connect=False
 h,t=(finger_pos[name] if name in finger_pos else (Vector(v) for v in spec[name]))
 b.head=h;b.tail=t
 if name.endswith('leaf_l') or name.endswith('leaf_r'):b.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
assert len(arm.data.bones)==65

# Bind original Meshy vertices: anatomical regional weights plus geometric
# closest-finger-segment weights. Do not copy donor medieval outfit mesh.
for grp in list(mesh.vertex_groups):mesh.vertex_groups.remove(grp)
groups={n:mesh.vertex_groups.new(name=n) for n in rest if not n.startswith('root')}
finger_names={side:[n for n in finger_pos if n.endswith('_'+side)] for side in ('l','r')}
finger_segments={}
for n,(h,t) in finger_pos.items():
 if '_04_leaf_' not in n: finger_segments[n]=(h,t)
def segment_distance(p,h,t):
 delta=t-h
 u=min(1.,max(0.,(p-h).dot(delta)/max(1e-12,delta.length_squared)))
 return (p-(h+delta*u)).length
def setweights(idx,scores):
 s=sum(scores.values())
 assert s>.00001,(idx,scores)
 for n,val in scores.items():
  if val>1e-5:groups[n].add([idx],val/s,'REPLACE')
finger_counts={'l':0,'r':0}
finger_bones_weighted={'l':set(),'r':set()}
for vertex in mesh.data.vertices:
 v=vertex.co
 x,y,z=v.x,v.y,v.z
 side='l' if x>=0 else 'r'
 absx=abs(x)
 cape=(y>.115 and z<1.65 and absx>.17)
 if cape:
  if z<.97:scores={'pelvis':.6,'spine_01':.4}
  elif z<1.35:scores={'spine_01':.55,'spine_02':.45}
  else:scores={'spine_02':.6,'spine_03':.4}
 elif .66<z<.96 and absx>.275 and y<.115:
  # A mesh glove/hand can use the bone at the nearest finger segment, but
  # only if the segment is actually within the hand neighbourhood.
  nearest=sorted((segment_distance(v,*ends),n) for n,ends in finger_segments.items() if n.endswith('_'+side))
  distance,name=nearest[0]
  if z<.865 and distance<.12:
   strength=min(.92,max(.38,(.12-distance)/.09))
   finger_counts[side]+=1
   finger_bones_weighted[side].add(name)
   scores={'hand_'+side:1-strength,name:strength}
   if len(nearest)>1 and nearest[1][0]<distance+.012:
    second=nearest[1][1]
    scores[name]*=.86
    scores[second]=strength*.14
    finger_bones_weighted[side].add(second)
  else:
   scores={'hand_'+side:1.}
 elif absx>.235 and .90<z<1.58 and y<.135:
  opts=['clavicle_'+side,'upperarm_'+side,'lowerarm_'+side,'hand_'+side]
  distances=sorted((segment_distance(v,arm.data.bones[n].head_local,arm.data.bones[n].tail_local),n) for n in opts)
  weights=[(n,math.exp(-((d/.095)**2))) for d,n in distances[:3]]
  scores=dict(weights)
  if sum(scores.values())<.00001:scores={distances[0][1]:1.}
 elif z<.98 and absx>.072 and y<.13:
  if z<.10:scores={'foot_'+side:.6,'ball_'+side:.4}
  elif z<.22:scores={'calf_'+side:.2,'foot_'+side:.8}
  elif z<.58:scores={'calf_'+side:.85,'thigh_'+side:.15}
  elif z<.90:scores={'thigh_'+side:.94,'pelvis':.06}
  else:scores={'thigh_'+side:.5,'pelvis':.5}
 elif z>1.72 and absx<.24:scores={'Head':1.}
 elif z>1.57:scores={'neck_01':.23,'Head':.77}
 elif z>1.43:scores={'spine_03':1.}
 elif z>1.25:scores={'spine_02':1.}
 elif z>1.08:scores={'spine_01':1.}
 else:scores={'pelvis':1.}
 setweights(vertex.index,scores)
print('V044_MESHY_FINGER_VERTEX_COUNTS',finger_counts,'finger bones with assigned weights', {s:len(v) for s,v in finger_bones_weighted.items()},flush=True)
assert all(c>=30 for c in finger_counts.values()),('Too few mesh vertices influenced by actual finger bones',finger_counts)

# Source geometry and materials are not altered aside from object transform.
mesh.parent=arm
mesh.matrix_parent_inverse=Matrix.Identity(4)
modifier=mesh.modifiers.new('GENESIS_MESHY_V044_REAL_ARMATURE','ARMATURE')
modifier.object=arm
assert len(mesh.data.vertices)==9277
bpy.context.view_layer.update()
# Independent equipment sockets follow actual donor hand bones, not geometry.
sockets=[]
for label,hand in [('GENESIS_SOCKET_WEAPON_R','hand_r'),('GENESIS_SOCKET_SHIELD_L','hand_l')]:
 ob=bpy.data.objects.new(label,None)
 bpy.context.scene.collection.objects.link(ob)
 ob.empty_display_type='PLAIN_AXES'
 ob.empty_display_size=.05
 ob.parent=arm;ob.parent_type='BONE';ob.parent_bone=hand
 sockets.append(ob)
# Export unposed/actual rigged GLB first, without donor outfit.
outpath=a.out/'GENESIS_MESHY_WEARY_WARRIOR_65BONES_V044_EXPERIMENTAL.glb'
bpy.ops.object.select_all(action='DESELECT')
for ob in [arm,mesh]+sockets:ob.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(outpath.resolve()),export_format='GLB',
 use_selection=True,export_animations=False)
assert outpath.stat().st_size>300000
print('V044_EXPORTED_REAL_SKINNED_GLB',outpath.name,outpath.stat().st_size,flush=True)

# Actual Blender deformation QA before animation additions.
deps=bpy.context.evaluated_depsgraph_get()
def evaluated():
 bpy.context.view_layer.update()
 ob=mesh.evaluated_get(deps)
 d=ob.to_mesh()
 try:return [tuple(ob.matrix_world@v.co) for v in d.vertices]
 finally:ob.to_mesh_clear()
rest_pos=evaluated()

# Render with real 32-bit EXR HDRI + physically coherent PBR source textures.
scene=bpy.context.scene
world=bpy.data.worlds.new('GENESIS_MESHY_V044_REAL_EXR_32BIT')
world.use_nodes=True;scene.world=world
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96,('not 32bit/channel HDRI',env.image.depth)
bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.68
ow=nodes.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],ow.inputs['Surface'])
def aim(o,target):o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,power,radius):
 light=bpy.data.lights.new(name,'AREA')
 ob=bpy.data.objects.new(name,light);scene.collection.objects.link(ob)
 ob.location=location;aim(ob,Vector((0,0,1.1)))
 light.energy=power;light.shape='DISK';light.size=radius
area('key',(-2.0,-2.2,3.1),550,2.8)
area('rim',(1.7,1.8,2.6),280,2.4)
bpy.ops.mesh.primitive_plane_add(size=7,location=(0,0,-.028))
floor=bpy.context.object;floor.name='QA_FLOOR_NOT_IN_SOURCE'
mat=bpy.data.materials.new('QA_FLOOR');mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.085,.090,.095,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.87
floor.data.materials.append(mat)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=30
scene.render.resolution_x=650;scene.render.resolution_y=760
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.12
renders=[]
def render(name,view,focus,scale):
 data=bpy.data.cameras.new(name+'Lens')
 cam=bpy.data.objects.new(name+'Camera',data);scene.collection.objects.link(cam)
 cam.location=Vector(focus)+Vector(view).normalized()*4
 aim(cam,Vector(focus));scene.camera=cam
 data.type='ORTHO';data.ortho_scale=scale
 path=a.out/(name+'.png');scene.render.filepath=str(path.resolve())
 bpy.ops.render.render(write_still=True)
 assert path.stat().st_size>45000,('render absent',name)
 renders.append({'file':name+'.png','size':path.stat().st_size})
render('V044_01_ORIGINAL_MESHY_WITH_DONOR_RIG',(.22,-1,.16),(0,0,1.03),2.60)
render('V044_02_THREE_QUARTER',(.8,-1,.17),(0,0,1.03),2.60)
render('V044_03_RIGHT_HAND_OPEN',(.4,-1,.15),(-.32,0,.81),.62)
render('V044_04_LEFT_HAND_OPEN',(-.4,-1,.15),(.32,0,.81),.62)

# Flex real donor finger chains and measure deformation of native Meshy mesh.
testbones=[]
for s in ('l','r'):
 for finger in ('thumb','index','middle','ring','pinky'):
  for k in (1,2,3):
   bone=arm.pose.bones[f'{finger}_{k:02d}_{s}']
   bone.rotation_mode='QUATERNION'
   angle=math.radians(24 if k==1 else 18)
   bone.rotation_quaternion=Quaternion((1,0,0),angle)
   testbones.append(bone.name)
deformed=evaluated()
movement={}
for side,sgn in [('l',1),('r',-1)]:
 moved=[math.dist(x,y) for src,dst,x,y in []]
 displaced=[]
 for orig,p1,p2 in zip(vcoords,rest_pos,deformed):
  if orig.x*sgn>.25 and .63<orig.z<.94:
   displaced.append(math.dist(p1,p2))
 movement[side]={
  'vertices_moved_over_2mm':sum(x>.002 for x in displaced),
  'max_displacement_m':round(max(displaced or [0.]),5),
  'mean_displacement_m':round(sum(displaced)/max(1,len(displaced)),6),
  'vertices_in_hand_region':len(displaced)}
print('V044_ACTUAL_MESHY_65BONE_FINGER_MOVEMENT',movement,flush=True)
render('V044_05_RIGHT_HAND_BENT',(.4,-1,.15),(-.32,0,.81),.62)
render('V044_06_LEFT_HAND_BENT',(-.4,-1,.15),(.32,0,.81),.62)
# Flagging no visual approval is mandatory even if numeric tests pass.
pass_deformation=all(q['vertices_moved_over_2mm']>=15 and .003<q['max_displacement_m']<.30 for q in movement.values())
report={
 'status':'V044_EXPERIMENTAL_RETARGET_BONE_HIERARCHY_AND_FINGER_WEIGHT_TEST',
 'original_meshy_sha256':sha(a.meshy),
 'original_donor_rig_sha256':sha(a.donor),
 'exported_glb_sha256':sha(outpath),
 'source_mesh_vertices':verts,'donor_real_bones':65,
 'donor_original_finger_bone_chains_per_hand':20,
 'target_weighted_finger_vertices':finger_counts,
 'finger_pose_test_bones':testbones,
 'source_model_geometry_preserved':True,
 'source_model_texture_preserved':True,
 'original_donor_medieval_outfit_not_used':True,
 'mesh_weights_created_for_new_geometry':True,
 'digit_deformation_measurements':movement,
 'finger_deformation_numeric_pass':pass_deformation,
 'render_engine':'CYCLES','hdri':a.hdri.name,'hdr_bits_total':env.image.depth,
 'renders':renders,
 'visual_quality_8of10_verified':False,
 'finger_grasp_verified':False,
 'V12B_sword_attached':False,'V015_shield_attached':False,
 'animations_applied':False,'Mixamo_tested':False,
 'PlayCanvas_tested':False,'user_approved':False,'main_modified':False
}
(a.out/'V044_MESHY_DONOR_FINGERS_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
assert pass_deformation,('V044 REJECT: no credible finger deformation',movement)
print('V044_REAL_FINGER_RIG_EXPERIMENTAL_GEOMETRIC_PASS_NOT_VISUALLY_APPROVED',json.dumps({'movement':movement,'GLB':outpath.name,'renders':len(renders)}),flush=True)
