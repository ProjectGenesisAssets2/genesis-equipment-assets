#!/usr/bin/env python3
"""Read-only GLB anatomy and game-compatibility audit for Meshy candidate #1.

Usage:
    python scripts/mercenary/audit_weary_warrior_candidate1.py exported_original.glb --out /tmp/report.json

No asset modifications, no armature/socket fabrication, no false "ready" claim.
The original mesh, hands and inventory attachments still require visual Cycles QA.
"""
import argparse, hashlib, json, re, struct
from pathlib import Path

def audit(p):
    data=p.read_bytes()
    if len(data)<20 or data[:4]!=b'glTF':
        raise ValueError("Not a binary glTF/GLB. Export the official model as GLB.")
    version,total=struct.unpack_from("<II",data,4)
    if version!=2 or total!=len(data):
        raise ValueError("Invalid GLB v2 header/length")
    jlen,chunk_type=struct.unpack_from("<I4s",data,12)
    if chunk_type!=b"JSON":
        raise ValueError("GLB JSON chunk missing")
    doc=json.loads(data[20:20+jlen].decode("utf-8"))
    nodes=doc.get("nodes",[])
    mesh=doc.get("meshes",[])
    skins=doc.get("skins",[])
    animations=doc.get("animations",[])
    names=[n.get("name","") for n in nodes]
    parent={}
    for i,n in enumerate(nodes):
        for ch in n.get("children",[]):
            if ch in parent: raise ValueError(f"Node {ch} has more than one parent")
            parent[ch]=i
    def chain(node_id):
        out=[]
        while node_id in parent:
            node_id=parent[node_id]
            out.append(names[node_id])
        return out
    bones=sorted(set(k for skin in skins for k in skin.get("joints",[])))
    bone_names=[names[i] for i in bones]
    def guess_hand(side):
        return [str(i)+":"+name for i,name in enumerate(names)
            if re.search(r'(?i)(mixamorig[:_])?(left|right)[\W_]*(hand|wrist)|'
                r'(hand|wrist)[._ -]?(l|r)$',name)
            and (("left" in name.lower() or name.lower().endswith(('.l','_l','-l')))
                if side=="left" else ("right" in name.lower() or name.lower().endswith(('.r','_r','-r'))))]
    r=guess_hand("right");l=guess_hand("left")
    fingers=[name for name in bone_names if any(t in name.lower() for t in
      ("thumb","index","middle","ring","pinky","finger","metacarp"))]
    geom=[]
    nvertices=0;ntriangles=0
    for mid,m in enumerate(mesh):
        for prim in m.get("primitives",[]):
            pos=prim.get("attributes",{}).get("POSITION")
            if pos is None:continue
            ac=doc["accessors"][pos];v=ac["count"];nvertices+=v
            ix=prim.get("indices")
            mode=prim.get("mode",4)
            tri=(doc["accessors"][ix]["count"]//3 if ix is not None else v//3) if mode==4 else None
            if tri is not None:ntriangles+=tri
            geom.append({"mesh":m.get("name",str(mid)),
                         "primitive_vertices":v,"triangles_if_mode4":tri,
                         "is_skinned":any(k.startswith("JOINTS_") for k in prim.get("attributes",{}))})
    texture_links={x.get('source') for x in doc.get('textures',[]) if 'source' in x}
    equipment_nodes=[name for name in names if re.search(r'(?i)sword|shield|scabbard|weapon|equip|hilt|blade',name)]
    report={
      "candidate":"Meshy 01969c2e-f1bb-7898-a9dd-c2104e943510 (CC0 per public listing)",
      "input_filename":p.name,"glb_sha256":hashlib.sha256(data).hexdigest(),
      "file_size_bytes":len(data),"glb_version":version,
      "node_count":len(nodes),"mesh_count":len(mesh),"skin_count":len(skins),
      "joint_count_per_skin":[len(x.get('joints',[])) for x in skins],
      "animation_names":[a.get('name',str(i)) for i,a in enumerate(animations)],
      "right_hand_nodes":r,"left_hand_nodes":l,
      "finger_bones":fingers,"finger_bones_count":len(fingers),
      "right_hand_verified":bool(r),"left_hand_verified":bool(l),
      "equipment_named_nodes":equipment_nodes,
      "total_vertices_across_primitives":nvertices,
      "estimated_triangles":ntriangles,
      "mesh_primitives":geom,
      "material_count":len(doc.get('materials',[])),
      "texture_count":len(doc.get('textures',[])),
      "image_count":len(doc.get('images',[])),
      "primitive_modes_nontriangles":sum(1 for m in mesh for pr in m.get('primitives',[]) if pr.get('mode',4)!=4),
      "has_skinned_mesh":any(x['is_skinned'] for x in geom),
      "evidence_stage":"ORIGINAL_GLB_STATIC_AUDIT_ONLY",
      "sword_V12B_compatible":None,"shield_V015_compatible":None,
      "fingers_grip_verified":False,"handedness_pose_verified":False,
      "visual_Cycles32_tested":False,"playcanvas_tested":False,"user_approved":False,
      "next_step":"Render genuine source from front/back; detect right/left anatomical axes; align V12B/V015 inventory assets to actual bones and validate real grip over walk/inspection."
    }
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("original_glb",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.original_glb)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__": main()
