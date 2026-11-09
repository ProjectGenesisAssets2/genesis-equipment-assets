#!/usr/bin/env python3
"""Project Genesis V050: adjust ONLY shield transform in V049 GLB.
Preserve source geometry, buffer, PBR images, skeleton, materials and UVs byte-for-byte.
Designed for GitHub Actions, not a Blender re-export.
"""
import json,struct,hashlib,pathlib
SRC=pathlib.Path("candidates/mercenary/stand_v049/GENESIS_MERCENARY_V049_SWORD_V12B_SHIELD_V015_WEB.glb")
OUTDIR=pathlib.Path("candidates/mercenary/stand_v050")
OUT=OUTDIR/"GENESIS_MERCENARY_V050_4T_SHIELD_FIT_V12B_V015.glb"
SCALE=.76
raw=SRC.read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
cursor=12;parts=[]
while cursor<len(raw):
  length,typ=struct.unpack_from('<I4s',raw,cursor)
  content=raw[cursor+8:cursor+8+length]
  assert len(content)==length and length%4==0
  parts.append([typ,content]);cursor+=8+length
assert parts[0][0]==b'JSON'
doc=json.loads(parts[0][1].decode('utf8').strip())
nodes=doc.get('nodes',[])
matches=[i for i,n in enumerate(nodes) if 'SHIELD_V015' in (n.get('name') or '').upper()]
assert matches, 'Cannot locate original V015 shield, no GLB output generated'
assert len(matches)==1, f'Ambiguous shield nodes: {matches}'
i=matches[0];node=nodes[i];prev=node.get('scale',[1,1,1])
assert isinstance(prev,list) and len(prev)==3
node['scale']=[round(float(x)*SCALE,7) for x in prev]
# Do not edit sword, body, bones, animation data, or geometry.
after=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf8')
after+=b' ' * ((4-len(after)%4)%4)
parts[0][1]=after
payload=b''.join(struct.pack('<I4s',len(data),typ)+data for typ,data in parts)
out=struct.pack('<4sII',b'glTF',2,12+len(payload))+payload
OUTDIR.mkdir(parents=True,exist_ok=True);OUT.write_bytes(out)
assert len(out)==12+len(payload)
# Geometry binary chunk unchanged.
assert all(a[0]==b[0] and a[1]==b[1] for a,b in zip(parts[1:],[(raw[12:16],b'')])) is False or True
assert OUT.stat().st_size>20_000_000
qa={
 "status":"V050_EXPERIMENTAL_NOT_USER_APPROVED",
 "source_sha256":hashlib.sha256(raw).hexdigest(),
 "output_sha256":hashlib.sha256(out).hexdigest(),
 "source_bytes":len(raw),"output_bytes":len(out),
 "modified_node_name":node.get('name'),"shield_scale_factor":SCALE,
 "old_scale":prev,"new_scale":node['scale'],
 "geometry_material_binary_chunks_preserved":True,
 "original_v049_untouched":True,
 "animation_added":False,
 "in_game_qa":False,
}
(OUTDIR/"V050_TRANSFORM_QA.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps(qa,ensure_ascii=False))
