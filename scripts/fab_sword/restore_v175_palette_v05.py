#!/usr/bin/env python3
"""Restore the V175-derived color palette on Genesis sword's blade.
Builds a new V05 GLB from local authorized V03 and V04 assets, never
modifying either input and never altering geometry / UVs / original hilt.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

def load(path):
    raw=path.read_bytes()
    if struct.unpack_from('<4sII',raw,0)!=(b'glTF',2,len(raw)):
        raise ValueError('Not a GLB 2.0')
    cursor=12; chunks={}
    while cursor<len(raw):
        n,tag=struct.unpack_from('<I4s',raw,cursor);cursor+=8
        chunks[tag]=raw[cursor:cursor+n];cursor+=n
    if cursor!=len(raw): raise ValueError('Corrupted GLB')
    return json.loads(chunks[b'JSON']),bytearray(chunks[b'BIN\x00'])

def get_image(doc,blob,index):
    image=doc['images'][doc['textures'][index]['source']]
    view=doc['bufferViews'][image['bufferView']]
    start=view.get('byteOffset',0)
    return bytes(blob[start:start+view['byteLength']]),image['mimeType']

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--v03',type=Path,required=True)
    parser.add_argument('--v04',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    old,oldbin=load(args.v03)
    doc,blob=load(args.v04)
    if len(doc['meshes'])!=1 or len(doc['meshes'][0]['primitives'])!=2:
        raise ValueError('Unexpected model topology')
    primitives=doc['meshes'][0]['primitives']
    counts=[doc['accessors'][p['indices']]['count'] for p in primitives]
    if counts != [6156,294] or [p['material'] for p in primitives]!=[0,1]:
        raise ValueError('Expected original Genesis isolated blade')
    blade=doc['materials'][1]
    source_tex=old['materials'][1]['pbrMetallicRoughness']['baseColorTexture']['index']
    png,mime=get_image(old,oldbin,source_tex)
    while len(blob)%4:blob.append(0)
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(png)})
    blob.extend(png)
    doc['images'].append({'bufferView':len(doc['bufferViews'])-1,'mimeType':mime,'name':'V175_IronPalette_V05'})
    doc['textures'].append({'source':len(doc['images'])-1})
    blade['name']='Genesis_V175_IronBlade_PBR_V05_PaletteRestored'
    blade['pbrMetallicRoughness']['baseColorTexture']={'index':len(doc['textures'])-1}
    blade['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,1]
    # Keep V04 metallicRoughnessTexture and normalTexture intact.
    blade['pbrMetallicRoughness']['roughnessFactor']=1
    blade['pbrMetallicRoughness']['metallicFactor']=1
    doc['buffers'][0]['byteLength']=len(blob)
    meta=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf8')
    meta+=b' '*(-len(meta)%4)
    b=bytes(blob);b+=b'\x00'*(-len(b)%4)
    raw=(struct.pack('<4sII',b'glTF',2,28+len(meta)+len(b))+
         struct.pack('<I4s',len(meta),b'JSON')+meta+
         struct.pack('<I4s',len(b),b'BIN\x00')+b)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(raw)
    print('V05 SHA256',hashlib.sha256(raw).hexdigest(),'triangles',sum(counts)//3)

if __name__=='__main__':
    main()
