#!/usr/bin/env python3
"""Inject true glTF child-of-joint sockets into the *original* CC0 mercenary GLB.
No Blender bone-parent exporter offsets, no geometry/material/animation edits.
Keep weapon/shield independent GLBs; switch equipment in PlayCanvas at runtime.
"""
import argparse,copy,hashlib,json,struct
from pathlib import Path

SOCKETS=(
 ("RightHand","GENESIS_SOCKET_WEAPON_R",[0.0,6.0,0.0],"weapon","right"),
 ("LeftHand","GENESIS_SOCKET_SHIELD_L",[0.0,6.0,0.0],"shield","left"),
)
def digest(b):return hashlib.sha256(b).hexdigest()
def parse_glb(b):
 assert b[:4]==b"glTF" and struct.unpack_from("<II",b,4)==(2,len(b))
 n,k=struct.unpack_from("<I4s",b,12);assert k==b"JSON"
 return json.loads(b[20:20+n]),b[20+n:]
def save_glb(j,tail):
 raw=json.dumps(j,ensure_ascii=False,separators=(",",":")).encode()
 raw+=b" "*((-len(raw))%4)
 return b"glTF"+struct.pack("<II",2,20+len(raw)+len(tail))+struct.pack("<I4s",len(raw),b"JSON")+raw+tail
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 original=a.source.read_bytes()
 j,tail=parse_glb(original);before=copy.deepcopy(j)
 assert len(j.get("skins",[]))==1
 assert len(j.get("animations",[]))==10
 assert len(j.get("meshes",[]))>=1
 names={n.get("name"):i for i,n in enumerate(j["nodes"])}
 assert all(b in names for b,_,_,_,_ in SOCKETS)
 assert all(s not in names for _,s,_,_,_ in SOCKETS)
 skin_joints=set(j["skins"][0]["joints"])
 for bone,name,translation,slot,hand in SOCKETS:
  parent=names[bone];assert parent in skin_joints,(bone,"not a skin joint")
  node={"name":name,"translation":translation,"rotation":[0,0,0,1],
        "scale":[1,1,1],
        "extras":{"genesis_socket_version":4,"parent_joint":bone,"hand":hand,
                  "slot":slot,"space":"glTF joint-local","not_equipment_mesh":True}}
  child=len(j["nodes"]);j["nodes"].append(node)
  j["nodes"][parent].setdefault("children",[]).append(child)
 for field in ("meshes","materials","textures","images","skins","animations","accessors","bufferViews","buffers"):
  assert j.get(field)==before.get(field),("critical glTF content changed",field)
 b=save_glb(j,tail);pout=a.out/"mercenary_meshy_cc0_rig_sockets_v004.glb";pout.write_bytes(b)
 check,bin2=parse_glb(b)
 assert bin2==tail and len(check["animations"])==10
 for bone,name,local,_,_ in SOCKETS:
  parent=next(n for n in check["nodes"] if n.get("name")==bone)
  assert any(check["nodes"][id].get("name")==name for id in parent["children"])
  assert next(n for n in check["nodes"] if n.get("name")==name)["translation"]==local
 report={"status":"EXPERIMENTAL_AVATAR_SOCKET_GLTF_V004","not_integrated":True,
   "source_sha256":digest(original),"output_sha256":digest(b),
   "source_bytes":len(original),"output_bytes":len(b),
   "mesh_and_animation_buffers_unmodified_sha256":digest(tail),
   "skin_count":len(j["skins"]),"clip_count":len(j["animations"]),
   "clip_names":[x.get("name") for x in j["animations"]],
   "sockets":[{"parent_bone":bone,"name":name,"translation_joint_local":p,"usage":slot} for bone,name,p,slot,_ in SOCKETS],
   "sword":"V03 V175 V12B - geometry separate; source rights preserved",
   "shield":"approved shield separate: no provisional shield treated as final",
   "in_game":False,"approved_avatar":False}
 (a.out/"rig_integrity_v004.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
 print("GENESIS_SOCKET_RIG_V004",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
