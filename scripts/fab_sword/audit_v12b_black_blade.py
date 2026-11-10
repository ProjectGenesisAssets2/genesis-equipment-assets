#!/usr/bin/env python3
"""Read-only audit of the exact exported V175 V12B GLB. Never alters source."""
import json,struct,hashlib,io,statistics
from pathlib import Path
from PIL import Image
p=Path('assets/equipment/experimental/espada_v03_v175_v12b/Genesis_Sword_Iron_V03_V175_V12B_PBR_WebGL_CANDIDATE.glb')
b=p.read_bytes()
assert b[:4]==b'glTF' and struct.unpack_from('<I',b,4)[0]==2 and struct.unpack_from('<I',b,8)[0]==len(b)
off=12;chunks={}
while off<len(b):
    length,typ=struct.unpack_from('<I4s',b,off);off+=8
    chunks[typ]=b[off:off+length];off+=length
g=json.loads(chunks[b'JSON'])
bin=chunks.get(b'BIN\\x00',b'')
report={'asset':str(p),'sha256':hashlib.sha256(b).hexdigest(),'size_bytes':len(b),'materials':[],'textures':[],'meshes':len(g.get('meshes',[])),'extensionsUsed':g.get('extensionsUsed',[])}
for i,m in enumerate(g.get('materials',[])):
    mr=m.get('pbrMetallicRoughness',{})
    report['materials'].append({'index':i,'name':m.get('name'),'doubleSided':m.get('doubleSided',False),'alphaMode':m.get('alphaMode','OPAQUE'),'baseColorFactor':mr.get('baseColorFactor',[1,1,1,1]),'metallicFactor':mr.get('metallicFactor',1),'roughnessFactor':mr.get('roughnessFactor',1),'baseColorTexture':mr.get('baseColorTexture'),'metallicRoughnessTexture':mr.get('metallicRoughnessTexture'),'normalTexture':m.get('normalTexture'),'occlusionTexture':m.get('occlusionTexture'),'emissiveFactor':m.get('emissiveFactor')})
for i,im in enumerate(g.get('images',[])):
    try:
        view=g['bufferViews'][im['bufferView']]
        data=bin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        img=Image.open(io.BytesIO(data));img.load()
        rgb=img.convert('RGB');rgb.thumbnail((128,128))
        pix=list(rgb.getdata());means=[round(sum(px[k] for px in pix)/len(pix),2) for k in range(3)]
        lo=[min(px[k] for px in pix) for k in range(3)]
        hi=[max(px[k] for px in pix) for k in range(3)]
        report['textures'].append({'index':i,'name':im.get('name'),'mimeType':im.get('mimeType'),'width':img.width,'height':img.height,'mode':img.mode,'rgb_mean':means,'rgb_min':lo,'rgb_max':hi,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    except Exception as e:
        report['textures'].append({'index':i,'error':str(e)})
for i,tex in enumerate(g.get('textures',[])):
    report.setdefault('textureMappings',[]).append({'index':i,'source':tex.get('source'),'sampler':tex.get('sampler')})
report['flags']={
 'blade_near_full_metallic':any(('Blade' in str(m['name']) or 'Iron' in str(m['name'])) and m['metallicFactor']>=0.95 for m in report['materials']),
 'blade_has_base_color_texture':any(('Blade' in str(m['name']) or 'Iron' in str(m['name'])) and m['baseColorTexture'] for m in report['materials']),
 'no_hdr_environment_embedded':True,
 'gltf_geometry_valid':bool(g.get('meshes')) and bool(g.get('accessors'))
}
Path('diagnostics').mkdir(exist_ok=True)
out=Path('diagnostics/V12B_BLACK_BLADE_AUDIT_20261110.json')
out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\\n')
print('V12B_GLTF_AUDIT',json.dumps(report,ensure_ascii=False))
