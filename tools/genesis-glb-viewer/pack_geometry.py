#!/usr/bin/env python3
"""Pack exact GLB triangle data into small gzip/base64 text for offline inline canvas.
Mesh fragments are recovered from the source GLB (not procedurally created).
Multiple copies of grip wraps/guard ends reference the same geometry plus translation.
"""
import base64,gzip,hashlib,json,struct,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
file=root/'assets/playcanvas/swords/provisional_v001/genesis_sword_provisional_v001.glb'
data=file.read_bytes()
assert data[:4]==b'glTF'
assert hashlib.sha256(data).hexdigest()=='210d41cc2bc96d03862029d983af9ffcf71d093fd2e662ecb85a479db928d4ad'
cursor=12; gltf=None; blob=None
while cursor<len(data):
    size,tag=struct.unpack_from('<II',data,cursor);cursor+=8
    chunk=data[cursor:cursor+size];cursor+=size
    if tag==0x4e4f534a:gltf=json.loads(chunk)
    if tag==0x004e4942:blob=chunk
assert gltf and blob
def accessor(i):
    a=gltf['accessors'][i];v=gltf['bufferViews'][a['bufferView']]
    cc={'SCALAR':1,'VEC3':3}[a['type']]
    fmt={5126:'f',5123:'H',5125:'I'}[a['componentType']]
    width=struct.calcsize(fmt)
    stride=v.get('byteStride',width*cc)
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from('<'+fmt*cc,blob,start+j*stride) for j in range(a['count'])]
ids=[0,1,2,4,5,13,14,15]
chunks=[]
counts=[]
for mesh_id in ids:
    verts=[];tris=[]
    for p in gltf['meshes'][mesh_id]['primitives']:
        local=accessor(p['attributes']['POSITION'])
        idx=[n[0] for n in accessor(p['indices'])]
        off=len(verts); verts+=local
        assert p.get('mode',4)==4
        tris.extend((off+idx[k],off+idx[k+1],off+idx[k+2],p['material']) for k in range(0,len(idx),3))
    chunk=bytearray(struct.pack('<HH',len(verts),len(tris)))
    for v in verts:
        chunk.extend(struct.pack('<hhh',*[round(x*10000) for x in v]))
    for a,b,c,mat in tris:
        chunk.extend(struct.pack('<HHHB',a,b,c,mat))
    chunks.append(chunk);counts.append([mesh_id,len(verts),len(tris)])
raw=b''.join(chunks)
mapping={0:0,1:1,2:2,3:2,4:3,5:4,6:4,7:4,8:4,9:4,10:4,11:4,12:4,13:5,14:6,15:7}
nodes=[[mapping[i],*[round(x*10000) for x in n.get('translation',[0,0,0])]] for i,n in enumerate(gltf['nodes'])]
compressed=gzip.compress(raw,compresslevel=9,mtime=0)
out=root/'tools/genesis-glb-viewer'
(out/'sword-payload-gzip.b64').write_text(base64.b64encode(compressed).decode('ascii'),encoding='ascii')
(out/'sword-payload-meta.json').write_text(json.dumps({'source_sha256':hashlib.sha256(data).hexdigest(),'meshes':counts,'instances':nodes,'triangle_count':3324,'raw_bytes':len(raw),'compressed_bytes':len(compressed),'algorithm':'gzip'},indent=2),encoding='utf8')
print('SOURCE_VERIFIED',len(data),'PACKED',len(raw),'GZIP',len(compressed),'BASE64',len(base64.b64encode(compressed)))
