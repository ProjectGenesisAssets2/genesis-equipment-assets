#!/usr/bin/env python3
import json,struct,sys,hashlib,math
from pathlib import Path
p=Path(sys.argv[1]);data=p.read_bytes()
assert hashlib.sha256(data).hexdigest()=="e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b"
j=None;buf=None;i=12
while i<len(data):
 n,t=struct.unpack_from('<II',data,i);i+=8;d=data[i:i+n];i+=n
 if t==0x4e4f534a:j=json.loads(d)
 if t==0x004e4942:buf=d
def acc(k):
 a=j['accessors'][k];b=j['bufferViews'][a['bufferView']]
 fm={5126:'f',5123:'H',5125:'I',5121:'B'}[a['componentType']]
 n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 fmt='<'+fm*n;step=b.get('byteStride',struct.calcsize(fmt));start=b.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from(fmt,buf,start+o*step) for o in range(a['count'])]
verts=[];faces=[];materials=[]
for mi,m in enumerate(j['meshes']):
 for pr in m['primitives']:
  if 'POSITION' not in pr['attributes']:continue
  vv=acc(pr['attributes']['POSITION']);ids=[a[0] for a in acc(pr['indices'])] if 'indices' in pr else list(range(len(vv)))
  k=len(verts);verts.extend(vv)
  for f in range(0,len(ids),3):
   if f+2<len(ids):faces.append([k+ids[f],k+ids[f+1],k+ids[f+2],pr.get('material',0)])
print('GLB_V03',len(verts),len(faces),'MATERIALS',len(j.get('materials',[])))
# Select an area-weighted representative geometry subset, without publishing the full licensed source.
def area(f):
 a,b,c=[verts[k] for k in f[:3]]
 u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
 return math.sqrt(sum((u[(i+1)%3]*v[(i+2)%3]-u[(i+2)%3]*v[(i+1)%3])**2 for i in range(3)))/2
ordered=sorted(range(len(faces)),key=lambda i:area(faces[i]),reverse=True)
selected=sorted(ordered[:min(450,len(ordered))])
used=sorted(set(n for i in selected for n in faces[i][:3]))
remap={x:i for i,x in enumerate(used)}
preview={'v':[[round(float(t),4) for t in verts[k]] for k in used],'f':[[remap[q] for q in faces[k][:3]]+[faces[k][3]] for k in selected]}
print('GENESIS_PREVIEW_BEGIN')
print(json.dumps(preview,separators=(',',':')))
print('GENESIS_PREVIEW_END')
