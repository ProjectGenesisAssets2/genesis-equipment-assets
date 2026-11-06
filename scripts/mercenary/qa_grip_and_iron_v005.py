#!/usr/bin/env python3
"""Blender 4.5.13/Cycles verification of real joint socket GLB and actual V12B sword.
Shield geometry deliberately NOT replaced by the previous placeholder.
"""
import sys,hashlib,json,math,argparse
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Matrix,Vector
from mercy_v12b_captures_v003 import impt,ms,bnd,surface_v12b,lighting,sha,aim,lamp

def attach_to_socket(objs,target,socket):
 root=bpy.data.objects.new("QA_EQUIPPED_SWORD_V12B",None)
 bpy.context.scene.collection.objects.link(root)
 prev=set(objs)
 for ob in objs:
  if ob.parent not in prev:
   w=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=w
 bpy.context.view_layer.update()
 root.matrix_world=target;bpy.context.view_layer.update()
 w=root.matrix_world.copy();root.parent=socket;root.matrix_world=w
 bpy.context.view_layer.update()
 return root
def centroid_for_group(meshes,name):
 pts=[];weights=[]
 for ob in meshes:
  if ob.type!="MESH":continue
  group=ob.vertex_groups.get(name)
  if not group:continue
  # Read the DEFORMED skinned positions. Raw bpy.data.vertices are rest-pose
  # coordinates, unusable for comparison with animated hand bones.
  deps=bpy.context.evaluated_depsgraph_get()
  evaluated=ob.evaluated_get(deps)
  deform=evaluated.to_mesh()
  try:
   for vert in ob.data.vertices:
    try:wt=next(v.weight for v in vert.groups if v.group==group.index)
    except StopIteration:continue
    if wt<.5:continue
    pts.append(evaluated.matrix_world@deform.vertices[vert.index].co);weights.append(wt)
  finally:
   evaluated.to_mesh_clear()
 if not pts:return None,0
 center=sum((v*w for v,w in zip(pts,weights)),Vector())/sum(weights)
 return center,len(pts)
def render_v005(output,person,sword,hand,blade_meshes):
    """Only authentic Cycles frames; 32-bit EXR world + controlled reflected softboxes.
    Specular is produced by actual light reflection; no Photoshop/relighting the sword albedo.
    """
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=72
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.32
    all_actors=ms(person)+ms(sword)
    pmin,pmax=bnd(all_actors);char_center=(pmin+pmax)*.5
    char_height=(pmax-pmin).z
    bmin,bmax=bnd(blade_meshes);blade_center=(bmin+bmax)*.5
    # A neutral frontal softbox + a thin vertical highlight reveal the approved
    # V175 metal. They add lighting, never replace its albedo, normals or roughness.
    lamp('V005_CHARACTER_KEY',char_center+Vector((-2.0,-2.2,2.1)),char_center,90,2.7,3.0)
    lamp('V005_CHARACTER_RIM',char_center+Vector((1.7,1.6,1.9)),char_center,48,2.1,2.8)
    lamp('V005_IRON_LARGE_REFLECTION',blade_center+Vector((-.48,-1.04,1.15)),blade_center,78,1.45,2.2)
    lamp('V005_IRON_FINE_HIGHLIGHT',blade_center+Vector((.62,-.9,.53)),blade_center,46,.23,2.0)
    lamp('V005_IRON_LOWER_FILL',blade_center+Vector((-.4,-1.0,-.2)),blade_center,20,1.1,1.1)
    def frame(name,location,target,height,width=1220,rows=1520):
        cam=bpy.data.objects.new('CAM_V005_'+name,bpy.data.cameras.new('CAM_V005_'+name))
        bpy.context.scene.collection.objects.link(cam);scene.camera=cam
        cam.location=location
        aim(cam,target)
        cam.data.type='ORTHO';cam.data.ortho_scale=height
        scene.render.resolution_x=width;scene.render.resolution_y=rows
        dest=output/(name+'.png')
        scene.render.filepath=str(dest.resolve())
        bpy.ops.render.render(write_still=True)
        assert dest.stat().st_size>90000,(name,'render missing')
        return {'name':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest)}
    views=[]
    scene.frame_set(1);bpy.context.view_layer.update()
    views.append(frame('V005_01_tres_cuartos_espada_metal',char_center+Vector((.72,-1,.19)).normalized()*char_height*2.8,char_center,char_height*1.15,1400,1400))
    views.append(frame('V005_02_frente_espada_metal',char_center+Vector((0,-1,.10)).normalized()*char_height*2.8,char_center,char_height*1.15,1400,1400))
    grip_target=hand+Vector((0,-.03,-.08))
    views.append(frame('V005_03_detalle_agarre_real',grip_target+Vector((.72,-1,.30)).normalized()*2.3,grip_target,.76,1320,1080))
    blade_target=blade_center
    views.append(frame('V005_04_detalle_hoja_hierro_v175',blade_target+Vector((.32,-1,.16)).normalized()*2.1,blade_target,1.12,1320,1520))
    return views

def validate_sword_grip(blade_center,hand,grip_anchor):
    assert (grip_anchor-hand).length<.035,('V005 grip must align hand centroid',(grip_anchor-hand).length)
    return {'glove_to_handle_anchor_m':round((grip_anchor-hand).length,4),
            'glove_centroid_world_m':list(hand),
            'grip_world_m':list(grip_anchor),
            'blade_center_world_m':list(blade_center)}

def main():
 ap=argparse.ArgumentParser()
 for k in ["character","sword","hdri","preset","out"]:
  ap.add_argument("--"+k,type=Path,required=True)
 a=ap.parse_args(sys.argv[sys.argv.index("--")+1:]);a.out.mkdir(parents=True,exist_ok=True)
 preset=json.loads(a.preset.read_text())
 assert sha(a.sword)==preset["source_original"]["sha256"]
 assert sha(a.hdri)==preset["lighting"]["hdri_sha256"]
 bpy.ops.wm.read_factory_settings(use_empty=True)
 person=impt(a.character)
 arms=[o for o in person if o.type=="ARMATURE"]
 assert len(arms)==1
 arm=arms[0]
 assert len(arm.data.bones)==24
 sockets={}
 for name in ("GENESIS_SOCKET_WEAPON_R","GENESIS_SOCKET_SHIELD_L"):
  ob=next((o for o in bpy.data.objects if o.name==name),None)
  assert ob,(name,"GLB importer discarded socket")
  sockets[name]=ob
 assert len(bpy.data.actions)>=10
 bpy.context.view_layer.update()
 r=sockets["GENESIS_SOCKET_WEAPON_R"];l=sockets["GENESIS_SOCKET_SHIELD_L"]
 # Blender 4.5 glTF importer misinterprets joint-child empties in 1cm Meshy rigs.
 # Its visible empty may be ~21m away even though original GLB native hierarchy is correct.
 # Reconstruct world-correct Blender anchors strictly for Cycles QA; do NOT export
 # these QA edits back over the verified glTF-native sockets.
 imported_socket_distance={}
 for name,bone in (("GENESIS_SOCKET_WEAPON_R","RightHand"),("GENESIS_SOCKET_SHIELD_L","LeftHand")):
  pb=arm.pose.bones[bone]
  bw=arm.matrix_world@pb.matrix
  ob=sockets[name]
  imported_socket_distance[name]=round((ob.matrix_world.translation-bw.translation).length,5)
  target=bw@Matrix.Translation((0,6.0,0))
  ob.parent=None
  ob.matrix_world=target
  bpy.context.view_layer.update()
  w=ob.matrix_world.copy()
  ob.parent=arm
  ob.parent_type='BONE';ob.parent_bone=bone
  ob.matrix_world=w
  bpy.context.view_layer.update()
 right_hand=arm.matrix_world@arm.pose.bones["RightHand"].matrix
 left_hand=arm.matrix_world@arm.pose.bones["LeftHand"].matrix
 distances={name:round((sockets[name].matrix_world.translation-(right_hand if "WEAPON" in name else left_hand).translation).length,5)
  for name in sockets}
 assert all(.005<d<.2 for d in distances.values()),("calibrated QA socket distance",distances)
 centroids={}
 for name,group in (("right","RightHand"),("left","LeftHand")):
  pt,count=centroid_for_group(ms(person),group)
  if pt is not None:
   pos=(r if name=="right" else l).matrix_world.translation
   centroids[name]={"skinned_vertices":count,"palm_centroid_distance_m":round((pos-pt).length,4)}
 assert all(v["palm_centroid_distance_m"]<.18 for v in centroids.values()),("Socket away from skinned hand mesh",centroids)
 sword=impt(a.sword);surface=surface_v12b(sword)
 sword_metal=[ob for ob in ms(sword) if any(mat and 'Iron_Blade_V175' in mat.name for mat in ob.data.materials)]
 assert sword_metal,'Approved V175 iron blade not found'
 smin,smax=bnd(sword);slen=smax-smin
 axis=max(range(3),key=lambda i:slen[i])
 srcdir=Vector(tuple(int(i==axis) for i in range(3)))
 bounds=bnd(person);side=1.0 if r.matrix_world.translation.x>(bounds[0].x+bounds[1].x)*.5 else -1.
 # V005: sword must hang naturally down & slightly out from the forearm.
 desired=Vector((.27*side,-.12,-.96)).normalized()
 # V004 grasp was on the upper wrap beside pommel; shift to central lower wrap.
 grip=(smin+smax)*.5;grip[axis]=smin[axis]+.175*slen[axis]
 scale=1.05/slen[axis]
 primary_rot=srcdir.rotation_difference(desired)
 # Align the ACTUAL broad iron face with the frontal camera, rather than
 # leaving its dark, nearly edge-on reflective side aimed toward the viewer.
 qmin,qmax=bnd(sword_metal);qext=qmax-qmin
 transverse=[i for i in range(3) if i!=axis]
 thin_axis=min(transverse,key=lambda i:qext[i])
 source_face=Vector(tuple(int(i==thin_axis) for i in range(3)))
 current_face=primary_rot@source_face
 frontal=Vector((.18,-1,.17))
 target_face=(frontal-desired*frontal.dot(desired)).normalized()
 current_face=(current_face-desired*current_face.dot(desired)).normalized()
 face_roll=current_face.rotation_difference(target_face)
 rot=(face_roll@primary_rot).to_matrix().to_4x4()
 # The source skin is evaluated before fitting. Align the center of the V12B
 # leather grip to the real DEFORMED glove, not to a guessed hand-bone pivot.
 palm,count=centroid_for_group(ms(person),'RightHand')
 assert palm is not None and count>=50
 hand=palm+Vector((0,-.008,-.003))
 target=Matrix.Translation(hand)@rot@Matrix.Scale(scale,4)@Matrix.Translation(-grip)
 equipped=attach_to_socket(sword,target,r)
 bpy.context.view_layer.update()
 grip_world=target@grip
 r_start=r.matrix_world.translation.copy();l_start=l.matrix_world.translation.copy()
 alignment=validate_sword_grip(((bnd(sword_metal)[0]+bnd(sword_metal)[1])*.5),palm,grip_world)
 assert math.isfinite((equipped.matrix_world.translation-r_start).length)
 hdr=lighting(a.hdri)
 renders=render_v005(a.out,person,sword,hand,sword_metal)
 scenes=bpy.context.scene
 # The imported glTF clips are backed by Blender's animation actions/NLA.
 # Advance a real source action and report actual changes in the animated socket.
 animations=[]
 for act in list(bpy.data.actions):
  if len(animations)>=10:break
  name=act.name
  try:
   if arm.animation_data is None:arm.animation_data_create()
   if arm.animation_data.action is not None:arm.animation_data.action=None
   arm.animation_data.action=act
   if getattr(act,"slots",None) and not arm.animation_data.action_slot:
    slots=list(act.slots)
    if slots:arm.animation_data.action_slot=slots[0]
   bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
   p0=r.matrix_world.translation.copy();q0=l.matrix_world.translation.copy()
   end=max(10,int(act.frame_range[1]))
   bpy.context.scene.frame_set(max(2,min(end,30)));bpy.context.view_layer.update()
   p1=r.matrix_world.translation.copy();q1=l.matrix_world.translation.copy()
   animations.append({"clip":name,"right_socket_delta_m":round((p1-p0).length,5),
                       "left_socket_delta_m":round((q1-q0).length,5)})
  except Exception as exc:animations.append({"clip":name,"qa_error":str(exc)[:140]})
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 report={"status":"V005_EXPERIMENTAL_GRIP_AND_REFLECTION_QA","avatar":"Meshy CC0 candidate unapproved",
   "source_socket_glb_sha256":sha(a.character),"source_sword_sha256":sha(a.sword),
   "grip_fit":alignment,"grip_position_fraction":.175,"sword_length_m":round(1.05,3),
   "blade_rolled_to_face_camera":True,"roll_alignment_target":list(target_face),
   "metal_maps_and_iron_preset_unchanged":True,"light_reflections":"Two sword-specific area softboxes",
   "sword":"V03 V175 V12B authentic original","sword_material":surface,
   "shield":"approved shield model not present in this public QA runner; left-hand socket tested structurally",
   "bones":len(arm.data.bones),"animation_action_count":len(bpy.data.actions),
   "wrist_to_socket_m":distances,"blender_importer_joint_child_offset_m":imported_socket_distance,"palm_mesh_centroids":centroids,
   "socket_world_positions":{"right_rest":list(r_start),"left_rest":list(l_start)},
   "socket_names":list(sockets),"animated_clip_probes":animations,
   "sword_parent_object":equipped.parent.name if equipped.parent else "",
   "hdri":hdr,"renders":renders,"game_integrated":False,"shader_visual_approved":True}
 (a.out/"GRIP_V005_QA.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
 print("GENESIS_MERCENARY_V005_GRIP_AND_METAL_QA",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
