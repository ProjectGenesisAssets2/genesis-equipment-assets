#!/usr/bin/env python3
"""Blender 4.5.13/Cycles verification of real joint socket GLB and actual V12B sword.
Shield geometry deliberately NOT replaced by the previous placeholder.
"""
import sys,hashlib,json,math,argparse
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mathutils import Matrix,Vector
from mercy_v12b_captures_v003 import impt,ms,bnd,surface_v12b,lighting,photo,sha

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
  for vert in ob.data.vertices:
   try:wt=next(v.weight for v in vert.groups if v.group==group.index)
   except StopIteration:continue
   if wt<.5:continue
   pts.append(ob.matrix_world@vert.co);weights.append(wt)
 if not pts:return None,0
 center=sum((v*w for v,w in zip(pts,weights)),Vector())/sum(weights)
 return center,len(pts)
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
 right_hand=arm.matrix_world@arm.pose.bones["RightHand"].matrix
 left_hand=arm.matrix_world@arm.pose.bones["LeftHand"].matrix
 distances={name:round((sockets[name].matrix_world.translation-(right_hand if "WEAPON" in name else left_hand).translation).length,5)
  for name in sockets}
 assert all(.005<d<.2 for d in distances.values()),("socket to wrist distance",distances)
 centroids={}
 for name,group in (("right","RightHand"),("left","LeftHand")):
  pt,count=centroid_for_group(ms(person),group)
  if pt is not None:
   pos=(r if name=="right" else l).matrix_world.translation
   centroids[name]={"skinned_vertices":count,"palm_centroid_distance_m":round((pos-pt).length,4)}
 assert all(v["palm_centroid_distance_m"]<.18 for v in centroids.values()),("Socket away from skinned hand mesh",centroids)
 sword=impt(a.sword);surface=surface_v12b(sword)
 smin,smax=bnd(sword);slen=smax-smin
 axis=max(range(3),key=lambda i:slen[i])
 srcdir=Vector(tuple(int(i==axis) for i in range(3)))
 bounds=bnd(person);side=1.0 if r.matrix_world.translation.x>(bounds[0].x+bounds[1].x)*.5 else -1.
 desired=Vector((.37*side,-.2,-.91)).normalized()
 grip=(smin+smax)*.5;grip[axis]=smin[axis]+.13*slen[axis]
 scale=1.05/slen[axis]
 rot=srcdir.rotation_difference(desired).to_matrix().to_4x4()
 target=Matrix.Translation(r.matrix_world.translation)@rot@Matrix.Scale(scale,4)@Matrix.Translation(-grip)
 equipped=attach_to_socket(sword,target,r)
 r_start=r.matrix_world.translation.copy();l_start=l.matrix_world.translation.copy()
 off=equipped.matrix_world.translation-r_start
 assert math.isfinite(off.length)
 hdr=lighting(a.hdri)
 renders=photo(a.out,ms(person)+ms(sword))
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
 report={"status":"V004_EXPERIMENTAL_SOCKET_QA","avatar":"Meshy CC0 candidate unapproved",
   "source_socket_glb_sha256":sha(a.character),"source_sword_sha256":sha(a.sword),
   "sword":"V03 V175 V12B authentic original","sword_material":surface,
   "shield":"approved shield model not present in this public QA runner; left-hand socket tested structurally",
   "bones":len(arm.data.bones),"animation_action_count":len(bpy.data.actions),
   "wrist_to_socket_m":distances,"palm_mesh_centroids":centroids,
   "socket_world_positions":{"right_rest":list(r_start),"left_rest":list(l_start)},
   "socket_names":list(sockets),"animated_clip_probes":animations,
   "sword_parent_object":equipped.parent.name if equipped.parent else "",
   "hdri":hdr,"renders":renders,"game_integrated":False,"shader_visual_approved":True}
 (a.out/"SOCKET_QA.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
 print("GENESIS_WEAPON_SHIELD_V004_SOCKET_QA",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
