#!/usr/bin/env python3
"""Project Genesis — V048 MERCENARY IN THE DEMO: sword V12B & shield V015.
Deliberate pragmatic STATIC EQUIPMENT DISPLAY (not animation/hand-grip claim):
One original Quaternius 65-bone Ranger+head, rest arms lowered, with two real Genesis items
placed by anatomical hand coordinates and baked into a single GLB. No generic
sword/shield replacements, no edits to originals, no main integration.
Render front/three-quarter/back/hands in Cycles with 32-bit EXR HDRI.
"""
import argparse,bpy,hashlib,json,math,sys,struct
from pathlib import Path
from mathutils import Matrix,Vector

ap=argparse.ArgumentParser()
for arg in ('ranger','sword','shield','hdri','preset','out'):
    ap.add_argument('--'+arg,type=Path,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
preset=json.loads(a.preset.read_text())
assert preset['id']=='Genesis_Espada_V03_Hierro_V175_V12B'
assert sha(a.sword)==preset['source_original']['sha256'],('sword must be authentic approved V12B',sha(a.sword))
assert sha(a.hdri)==preset['lighting']['hdri_sha256']
assert len(a.ranger.read_bytes())>30000000
assert len(a.shield.read_bytes())>3000000
bpy.ops.wm.read_factory_settings(use_empty=True)

def import_file(path):
    old=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    add=[o for o in bpy.data.objects if o not in old]
    assert any(o.type=='MESH' for o in add)
    bpy.context.view_layer.update()
    return add
def meshes(objects):return [o for o in objects if o.type=='MESH']
def bounds(objects):
    pts=[ob.matrix_world@Vector(v) for ob in meshes(objects) for v in ob.bound_box]
    assert pts
    return Vector(tuple(min(v[i] for v in pts) for i in range(3))),Vector(tuple(max(v[i] for v in pts) for i in range(3)))
def stage_group(objs,name,world_matrix):
    root=bpy.data.objects.new(name,None)
    bpy.context.scene.collection.objects.link(root)
    src=set(objs)
    for ob in objs:
        if ob.parent not in src:
            mat=ob.matrix_world.copy()
            ob.parent=root
            ob.matrix_world=mat
    root.matrix_world=world_matrix
    bpy.context.view_layer.update()
    return root

person=import_file(a.ranger)
body=meshes(person)
rigs=[o for o in person if o.type=='ARMATURE']
assert len(rigs)==1
rig=rigs[0]
assert len(rig.data.bones)==65
assert all(n in rig.pose.bones for n in ('hand_r','hand_l','Head','pelvis'))
# V045b has a visible original Quaternius male head. Reject headless old V043.
assert any('GENESIS_V045_BASE_MALE_REAL_FACE_AND_NECK' in x.name for x in body)
assert any('Male_Ranger_Head_Hood' in x.name for x in body)

# V048: make a simple permanent medieval exhibition rest stance.
# The original free Ranger arrives with horizontal T-pose arms. Rotate its
# existing 65-bone shoulder chains down, bake original skin deformation into
# the SAME meshes, then apply the new posture as skeleton rest pose.
# No new bones, no generic body, no animation dependency in the final GLB.
arm_rest_before={side:(rig.matrix_world@rig.pose.bones['hand_'+side].matrix).translation.copy() for side in ('l','r')}
pose_info={}
for side in ('l','r'):
    pb=rig.pose.bones['upperarm_'+side]
    base=pb.matrix.copy()
    pivot=base.translation.copy()
    options=[]
    for factor in (1,-1):
        q=__import__('mathutils').Quaternion((0,1,0),math.radians(61*factor))
        pb.matrix=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)@base
        bpy.context.view_layer.update()
        pos=(rig.matrix_world@rig.pose.bones['hand_'+side].matrix).translation.copy()
        options.append((pos.z,factor,pos.copy()))
    best=min(options,key=lambda x:x[0])
    q=__import__('mathutils').Quaternion((0,1,0),math.radians(61*best[1]))
    pb.matrix=Matrix.Translation(pivot)@q.to_matrix().to_4x4()@Matrix.Translation(-pivot)@base
    bpy.context.view_layer.update()
    drop=arm_rest_before[side].z-(rig.matrix_world@rig.pose.bones['hand_'+side].matrix).translation.z
    assert .14<drop<.9,(side,drop,options)
    pose_info[side]={'selected_sign':best[1],'wrist_drop_m':round(drop,3)}
print('V048_EXHIBITION_STANCE_HAND_DROPS',pose_info,flush=True)
bpy.ops.object.select_all(action='DESELECT')
baked_objects=[]
for ob in body:
    bpy.context.view_layer.objects.active=ob
    ob.select_set(True)
    source_modifiers=[m for m in ob.modifiers if m.type=='ARMATURE' and m.object==rig]
    if not source_modifiers:
        print('V048_SOURCE_UNSKINNED_ACCESSORY_PRESERVED',ob.name,flush=True)
        ob.select_set(False)
        continue
    baked_objects.append(ob)
    for mod in source_modifiers:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.select_set(False)
# Mesh positions now carry the intended stance. Update original bone rests;
# restore existing bone vertex groups so a later animation remains possible.
bpy.context.view_layer.objects.active=rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
for ob in baked_objects:
    modifier=ob.modifiers.new('GENESIS_V048_GUARD_STANCE_SKIN','ARMATURE')
    modifier.object=rig
bpy.context.view_layer.update()
arm_rest_after={side:(rig.matrix_world@rig.pose.bones['hand_'+side].matrix).translation.copy() for side in ('l','r')}
assert all(arm_rest_after[s].z<arm_rest_before[s].z-.14 for s in ('l','r'))
assert len(rig.data.bones)==65
print('V048_POSE_BAKED_INTO_ORIGINAL_65_BONE_REST', {s:list(arm_rest_after[s]) for s in ('l','r')},flush=True)

body_bounds=bounds(body)
body_width=body_bounds[1].x-body_bounds[0].x
body_height=body_bounds[1].z-body_bounds[0].z
assert 1.5<body_height<3.5
print('V048_BODY_REAL_BOUNDS',list(body_bounds[0]),list(body_bounds[1]),flush=True)

# Scale only giant ranger body atlas images to 2K game-compatible, leaving
# ORIGINAL sword V12B and shield V015 PBR exactly as approved.
person_images=set(bpy.data.images)
resizes=[]
for im in person_images:
    if not im.has_data:continue
    width,height=im.size
    if max(width,height)>2048:
        ratio=2048/max(width,height)
        new_size=(int(round(width*ratio)),int(round(height*ratio)))
        if min(new_size)>0:
            im.scale(*new_size)
            im.pack()
            resizes.append({'name':im.name,'from':[width,height],'to':list(new_size)})
print('V048_RANGER_ONLY_ATLAS_RESIZES',resizes,flush=True)

sword=import_file(a.sword)
sword_meshes=meshes(sword)
assert len(sword_meshes)>=1
assert sum(len(ob.data.polygons) for ob in sword_meshes)>600
assert any('Iron_Blade_V175' in m.name for ob in sword_meshes for m in ob.data.materials if m)
shield=import_file(a.shield)
shield_meshes=meshes(shield)
assert len(shield_meshes)>=1
assert sum(len(ob.data.polygons) for ob in shield_meshes)>500
print('V048_APPROVED_EQUIPMENT_SOURCE_NAMES',
 [ob.name for ob in sword_meshes],[ob.name for ob in shield_meshes],flush=True)

hand_r=(rig.matrix_world@rig.pose.bones['hand_r'].matrix).translation.copy()
hand_l=(rig.matrix_world@rig.pose.bones['hand_l'].matrix).translation.copy()
assert math.isfinite(hand_r.x+hand_l.x)
assert .1<(hand_r-hand_l).length<2.5
print('V048_REAL_HAND_WORLD_COORDS',list(hand_r),list(hand_l),flush=True)
# Use the actual right/left HAND coordinates and each source mesh bounds,
# rather than positioning 3D weapons by eye with unsupported arbitrary scale.
smin,smax=bounds(sword)
sex=smax-smin
saxis=max(range(3),key=lambda i:sex[i])
slength=sex[saxis]
assert slength>.15
# Original approved sword orientation and grip fraction from V007.
sdir=Vector(tuple(int(j==saxis) for j in range(3)))
side_r=1 if hand_r.x>0 else -1
sword_dir=Vector((side_r*.21,-.11,.97)).normalized()
srot=sdir.rotation_difference(sword_dir)
grip=(smin+smax)*.5
grip[saxis]=smin[saxis]+.175*slength
scale_sword=.86/slength
# Sword straight upright, near the wrist, steel blade outside the face.
grip_position=hand_r+Vector((side_r*.03,-.052,.015))
sword_matrix=Matrix.Translation(grip_position)@srot.to_matrix().to_4x4()@Matrix.Scale(scale_sword,4)@Matrix.Translation(-grip)
sword_root=stage_group(sword,'GENESIS_V048_APPROVED_SWORD_V12B_IN_RIGHT_HAND_STATIC',sword_matrix)
assert (sword_root.matrix_world@grip-grip_position).length<.002

shmin,shmax=bounds(shield)
shext=shmax-shmin
thin=min(range(3),key=lambda i:shext[i])
thick_axis=Vector(tuple(int(i==thin) for i in range(3)))
# Shield's real broad front faces the spectator (-Y), vertical axis is
# projected Z so the original object remains a plausible arm shield.
direction=Vector((0,-1,0))
q0=thick_axis.rotation_difference(direction)
up_axis=max((i for i in range(3) if i!=thin),key=lambda i:shext[i])
u0=q0@Vector(tuple(int(i==up_axis) for i in range(3)))
u_project=(u0-direction*u0.dot(direction)).normalized()
q1=u_project.rotation_difference(Vector((0,0,1)))
# V047 camera accidentally saw the bright inner wood/straps. Show original forged face.
qshield=__import__('mathutils').Quaternion((0,0,1),math.pi)@q1@q0
shield_diameter=max(shext)
shield_scale=.66/shield_diameter
# Place the shield just forward and below the left wrist, visibly separated
# from the body so the approved face is recognizable in the game.
side_l=1 if hand_l.x>0 else -1
shield_center_world=hand_l+Vector((side_l*.06,-.21,-.135))
source_center=(shmin+shmax)*.5
shield_matrix=Matrix.Translation(shield_center_world)@qshield.to_matrix().to_4x4()@Matrix.Scale(shield_scale,4)@Matrix.Translation(-source_center)
shield_root=stage_group(shield,'GENESIS_V048_APPROVED_SHIELD_V015_IN_LEFT_HAND_STATIC',shield_matrix)
assert (shield_root.matrix_world@source_center-shield_center_world).length<.002
bpy.context.view_layer.update()

# Save this exact posed gear as a coherent standalone GLB. Intentionally
# static equipment: hands/rig remain original for a future animation pass,
# but no false claims that held equipment follows hand during animation.
glb=a.out/'GENESIS_MERCENARY_RANGER_V048_REAL_V12B_SWORD_V015_SHIELD_STATIC.glb'
bpy.ops.object.select_all(action='DESELECT')
for o in set(person+sword+shield+[sword_root,shield_root]):
    if o.name in bpy.data.objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(glb.resolve()),export_format='GLB',
                          use_selection=True,export_animations=False,export_image_format='AUTO')
assert glb.stat().st_size>3000000
print('V048_MERCENARY_REAL_EQUIPMENT_GLB',glb.stat().st_size,flush=True)

# Cycles test the actual same asset. EXR32 ensures metal reflects correctly.
scene=bpy.context.scene
world=bpy.data.worlds.new('GENESIS_V048_STUDIO_SMALL_09_EXR32')
scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth==96 and list(env.image.size)==[4096,2048]
bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.70
wo=nodes.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color']);links.new(bg.outputs['Background'],wo.inputs['Surface'])
focus=(body_bounds[0]+body_bounds[1])*.5
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def lamp(name,direction,power,size):
    l=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,l)
    scene.collection.objects.link(ob)
    ob.location=focus+Vector(direction);aim(ob,focus)
    l.energy=power;l.shape='DISK';l.size=size
lamp('GENESIS_KEY',(-2,-2,2.1),640,3)
lamp('GENESIS_SWORD_BLADE_SPEC',(1.0,-1.9,1.8),260,.65)
lamp('GENESIS_RIM',(2.2,1.4,1.6),260,2)
lamp('GENESIS_SHIELD_FILL',(-.4,-1.3,.4),125,1.2)
bpy.ops.mesh.primitive_plane_add(size=10,location=(0,0,-.035))
floor=bpy.context.object;floor.name='QA_FLOOR_NOT_IN_EXPORTED_GLB'
m=bpy.data.materials.new('QA_DARK_STONE');m.use_nodes=True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.083,.085,.090,1)
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.87
floor.data.materials.append(m)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.render.resolution_x=840;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.13
renders=[]
def capture(name,view,target,scale):
    c=bpy.data.objects.new(name+'_cam',bpy.data.cameras.new(name+'_lens'))
    scene.collection.objects.link(c)
    c.location=Vector(target)+Vector(view).normalized()*4.9
    aim(c,target);c.data.type='ORTHO';c.data.ortho_scale=scale
    scene.camera=c
    out=a.out/(name+'.png');scene.render.filepath=str(out.resolve())
    bpy.ops.render.render(write_still=True)
    assert out.stat().st_size>62000,(name,out.stat().st_size)
    renders.append({'file':out.name,'bytes':out.stat().st_size})
# Enough framing to show the sword and the shield simultaneously, with at
# least one opposite angle to expose accidental arm/gear intersections.
allmin,allmax=bounds(body+sword_meshes+shield_meshes)
overall_center=(allmin+allmax)/2
overall_center.z=.97  # source includes negative-z helmet/scene bounds; feet stand at world z≈0
overall_height=2.0 # actual standing avatar height, not glTF's negative-z outlier bounds
capture('V048_01_EQUIPPED_FRONT',(0,-1,.10),overall_center,max(2.55,overall_height*1.2))
capture('V048_02_EQUIPPED_THREE_QUARTER',(.65,-1,.17),overall_center,max(3.0,overall_height*1.2))
capture('V048_03_EQUIPPED_BACK',(-.25,1,.12),overall_center,max(3.0,overall_height*1.2))
capture('V048_04_APPROVED_V12B_RIGHT_HAND_DETAIL',(.65,-1,.15),hand_r,.90)
capture('V048_05_APPROVED_V015_LEFT_HAND_DETAIL',(-.65,-1,.15),hand_l,1.05)
qa={
 'status':'V048_TRUE_GENESIS_APPROVED_SWORD_AND_SHIELD_EQUIPPED_STATIC_EXPERIMENTAL',
 'character_source':'V045b original CC0 Quaternius Ranger+male head with existing 65-bone rig',
 'character_source_sha256':sha(a.ranger),
 'approved_sword_source_sha256':sha(a.sword),
 'approved_sword_name':'V03 V175 V12B true material and mesh unchanged',
 'approved_shield_source_sha256':sha(a.shield),
 'approved_shield_name':'V015_PBR2K_NO_MESHOPT original source unchanged',
 'combined_glb_sha256':sha(glb),'combined_glb_bytes':glb.stat().st_size,
 'character_bones':len(rig.data.bones),
 'character_head_present':True,
 'right_hand_world':list(hand_r),'left_hand_world':list(hand_l),
 'right_hand_sword_grip_world':list(grip_position),
 'right_hand_sword_grip_distance_m':round((hand_r-grip_position).length,4),
 'left_hand_shield_center_world':list(shield_center_world),
 'left_hand_shield_center_distance_m':round((hand_l-shield_center_world).length,4),
 'sword_length_m':.86,'shield_longest_dimension_m':.66,
 'character_atlas_downscale_only':resizes,
 'sword_and_shield_source_materials_preserved':True,
 'render_engine':'CYCLES','hdri':a.hdri.name,'hdr_rgb32_total_bits':env.image.depth,
 'renders':renders,
 'equipment_display_mode':'STATIC baked world placement and original 65-bone arms in lowered rest stance. Does not animate.',
 'arm_lowered_rest_pose':pose_info,
 'original_skin_geometry_reposed_only':True,
 'animation_required_for_demo':False,
 'animation_clips':0,'in_world_integration_tested':False,
 'face_quality_approved':False,'human_visual_approved':False,'main_modified':False
}
(a.out/'V048_MERCENARY_GENESIS_SWORD_SHIELD_QA.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False))
print('GENESIS_V048_REAL_APPROVED_SWORD_SHIELD_EQUIPPED_AND_RENDERED',
 json.dumps({'GLB_bytes':glb.stat().st_size,'bones':len(rig.data.bones),'sword_grip_distance':qa['right_hand_sword_grip_distance_m'],
 'shield_hand_distance':qa['left_hand_shield_center_distance_m'],'renders':len(renders)}),flush=True)
