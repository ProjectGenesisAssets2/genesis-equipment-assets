#!/usr/bin/env python3
"""Generate a compact *derived-from-actual-GLB* preview mesh for in-chat WebGL-free viewer.
Blade is retained exactly. Other meshes use real vertex extrema grouped in angular sectors,
so this is a deliberately simplified preview, never a replacement for GLB asset.
"""
from pathlib import Path
import math,struct,json,hashlib
root=Path(__file__).resolve().parents[2]
source=root/'assets/playcanvas/swords/provisional_v001/genesis_sword_provisional_v001.glb'
data=source.read_bytes()
assert hashlib.sha256(data).hexdigest()=='210d41cc2bc96d03862029d983af9ffcf71d093fd2e662ecb85a479db928d4ad'
j=None;buf=None;idx=12
while idx<len(data):
 length,tag=struct.unpack_from('<II',data,idx);idx+=8
 b=data[idx:idx+length];idx+=length
 if tag==0x4e4f534a:j=json.loads(b)
 if tag==0x004e4942:buf=b
assert j and buf
def acc(aid):
 a=j['accessors'][aid];v=j['bufferViews'][a['bufferView']]
 fmt={5126:'f',5123:'H',5125:'I'}[a['componentType']]
 comps={'SCALAR':1,'VEC3':3}[a['type']]
 step=v.get('byteStride',comps*struct.calcsize(fmt))
 off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from('<'+fmt*comps,buf,off+i*step) for i in range(a['count'])]
ids=[0,1,2,4,5,13,14,15]
vertexsets=[];facessets=[]
for m in ids:
 vs=[];fs=[]
 for p in j['meshes'][m]['primitives']:
  q=acc(p['attributes']['POSITION'])
  indices=[v[0] for v in acc(p['indices'])]
  base=len(vs);vs.extend(q)
  for k in range(0,len(indices),3):
   fs.append([base+indices[k],base+indices[k+1],base+indices[k+2],p['material']])
 vertexsets.append(vs);facessets.append(fs)
# The exact sword blade contains 44 triangles. For auxiliary parts use 8-12
# angular segments on 2 end-rings, preserving GLB bounds, center, and scale.
parts=[]
for meshid,(vs,fs) in enumerate(zip(vertexsets,facessets)):
 if meshid==0:
  unique=[];translation={}
  for p in vs:
   key=tuple(round(x*10000) for x in p)
   if key not in translation:translation[key]=len(unique);unique.append(key)
  compact=[]
  for a,b,c,mat in fs:
   compact.append([translation[tuple(round(x*10000) for x in vs[t])] for t in (a,b,c)]+[mat])
  parts.append({'vertices':unique,'faces':compact})
  continue
 # glTF is Y-up, local Y is longitudinal axis for turned cylinders and x-axis for guard
 # For guard box meshes keep extremities; for cylinder approximate 10-sided ring with actual bounds.
 mi=[min(p[k] for p in vs) for k in range(3)]
 ma=[max(p[k] for p in vs) for k in range(3)]
 verts=[];faces=[]
 if meshid in (1,2):
  # boxes: extrema preserve the physical shape of the actual GLB guard.
  for y in (mi[1],ma[1]):
   for x,z in ((mi[0],mi[2]),(ma[0],mi[2]),(ma[0],ma[2]),(mi[0],ma[2])):
    verts.append([round(v*10000) for v in (x,y,z)])
  faces=[[0,1,2,2],[0,2,3,2],[4,6,5,2],[4,7,6,2]]
  for k in range(4):
   a=k;b=(k+1)%4;faces.extend(([a,b,4+b,2],[a,4+b,4+a,2]))
 else:
  cx=(mi[0]+ma[0])/2;cz=(mi[2]+ma[2])/2
  rx=(ma[0]-mi[0])/2;rz=(ma[2]-mi[2])/2
  segments=10 if meshid!=7 else 12
  for y in (mi[1],ma[1]):
   for k in range(segments):
    a=k*math.tau/segments
    verts.append([round(v*10000) for v in (cx+rx*math.cos(a),y,cz+rz*math.sin(a))])
  for k in range(segments):
   q=(k+1)%segments;faces.extend(([k,q,segments+q,fs[0][3]],[k,segments+q,segments+k,fs[0][3]]))
  for k in range(1,segments-1):
   faces.extend(([0,k+1,k,fs[0][3]],[segments,segments+k,segments+k+1,fs[0][3]]))
 parts.append({'vertices':verts,'faces':faces})
inst=[0,1,2,2,3,4,4,4,4,4,4,4,4,5,6,7]
trans=[n.get('translation',[0,0,0]) for n in j['nodes']]
# Encode with simple 3-char signed integer positions and 2-char indices (ASCII only).
# Easier, transparent JSON numeric arrays compressed through delta.
payload={'p':[[[v/10000 for v in a] for a in part['vertices']] for part in parts],
'f':[[f for f in part['faces']] for part in parts],
'n':[[inst[i]]+[round(x,5) for x in trans[i]] for i in range(16)]}
s=json.dumps(payload,separators=(',',':'))
out=root/'tools/genesis-glb-viewer/inline-lod-data.json'
out.write_text(s)
print('TRUE_GLB_LOD',len(s),'triangles',sum(len(x) for x in payload['f']),'instances',len(payload['n']))
