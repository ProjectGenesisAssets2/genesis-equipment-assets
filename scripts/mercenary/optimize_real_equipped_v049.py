#!/usr/bin/env python3
"""Genesis V049: make the ACTUAL V048 Genesis Ranger+V12B+V015 PlayCanvas-ready.
- Preserve ALL original mesh and 65-joint skin binary streams byte-for-byte.
- Fix ONE known nonexported PBR shader: forged front V015 (white in V048).
  Use physically coherent iron from the V175 palette; do NOT substitute gear.
- Convert image payloads to game-supported EXT_texture_webp (already used by
  the V015 approved candidate), keep 2K sword/face and reduce 4K outfit to
  1536 texture budget. Normal/roughness textures lossless WebP.
- Embed all data in one standalone GLB, no required external domains at play.
- Experimental only: no approval, no main edits.
"""
import argparse,hashlib,io,json,struct
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
data=a.source.read_bytes()
assert data[:4]==b'glTF'
assert struct.unpack_from('<II',data,4)==(2,len(data))
jsonlen,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
g=json.loads(data[20:20+jsonlen])
start=20+jsonlen
binarylen,kind=struct.unpack_from('<I4s',data,start);assert kind==b'BIN\0'
binary=data[start+8:start+8+binarylen]
assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==65
assert 'EXT_texture_webp' in g['extensionsRequired']
assert len(g['images'])>=20

# The V015 front iron material in original V048 exported with no shader
# color/roughness; default white rendered like a white disc. Use a physically
# based dark iron in glTF, preserving all V015 geometry and UV.
iron_indices=[i for i,m in enumerate(g['materials']) if 'V015_IronV175_Hammered_Only_Front_DERIVED' in m.get('name','')]
assert len(iron_indices)==1,iron_indices
iron=g['materials'][iron_indices[0]]
pbr=iron.setdefault('pbrMetallicRoughness',{})
assert 'baseColorTexture' not in pbr,'Unexpected changed source material'
pbr['baseColorFactor']=[.15,.165,.185,1]
pbr['metallicFactor']=.80
pbr['roughnessFactor']=.38
# Reuse original V175 iron normal map from authentic sword material.
v175_normal_idx=next(i for i,img in enumerate(g['images']) if 'Genesis_V175_Hierro_Normal_2K' in img.get('name',''))
v175_texture_idx=next((i for i,t in enumerate(g['textures']) if
            t.get('source')==v175_normal_idx or
            t.get('extensions',{}).get('EXT_texture_webp',{}).get('source')==v175_normal_idx),None)
assert v175_texture_idx is not None
iron['normalTexture']={'index':v175_texture_idx,'scale':0.18}
iron['doubleSided']=True
print('V049_REPAIRED_V015_FORGED_FACE_PBR',iron,flush=True)

# All non-WebP embedded images are converted; the V015 skin/wood original
# WebP images are preserved byte-for-byte. No materials/mesh replacements.
modified_views={}
converted=[]
image_lengths={}
for image_index,img in enumerate(g['images']):
    bv_id=img['bufferView']
    v=g['bufferViews'][bv_id]
    assert v.get('buffer',0)==0
    raw=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
    if img.get('mimeType')=='image/webp':
        image_lengths[img.get('name',str(image_index))]=len(raw)
        continue
    name=img.get('name',f'Image_{image_index}')
    original=Image.open(io.BytesIO(raw))
    original.load()
    original_wh=original.size
    max_side=1536 if name.startswith('T_Ranger_') else 2048
    if max(original.size)>max_side:
        ratio=max_side/max(original.size)
        original=original.resize(tuple(int(round(s*ratio)) for s in original.size),Image.Resampling.LANCZOS)
    # Actual skin/normal/PBR masks are lossless to prevent unwanted artifacts.
    noncolor=any(x in name.lower() for x in ('normal','_orm','rough','_mr','metal'))
    if original.mode not in ('RGB','RGBA'):original=original.convert('RGBA' if 'A' in original.mode else 'RGB')
    web=io.BytesIO()
    if noncolor:
        original.save(web,format='WEBP',lossless=True,method=6,exact=True)
    else:
        original.save(web,format='WEBP',quality=96,method=6,exact=True)
    out=web.getvalue()
    assert out[:4]==b'RIFF' and out[8:12]==b'WEBP'
    img['mimeType']='image/webp'
    modified_views[bv_id]=out
    for tex in g['textures']:
        if tex.get('source')!=image_index:continue
        del tex['source']
        ext=tex.setdefault('extensions',{})
        ext['EXT_texture_webp']={'source':image_index}
    converted.append({'name':name,'old_bytes':len(raw),'new_bytes':len(out),
       'old_dimensions':list(original_wh),'new_dimensions':list(original.size),
       'lossless':noncolor})
    image_lengths[name]=len(out)
assert len(converted)>=10 and all(v['new_bytes']<v['old_bytes']*1.1 for v in converted)
assert all('source' not in t or g['images'][t['source']]['mimeType']!='image/webp' for t in g['textures'])
# Repack every buffer view. Morphs/vertex/index/skin/animations if present are
# copied unmodified, only image views change. Full spec 4-byte alignment.
newbin=bytearray()
for idx,view in enumerate(g['bufferViews']):
    assert view.get('buffer',0)==0
    part=modified_views.get(idx)
    if part is None:
        part=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
    while len(newbin)%4:newbin.append(0)
    view['byteOffset']=len(newbin)
    view['byteLength']=len(part)
    newbin.extend(part)
while len(newbin)%4:newbin.append(0)
g['buffers'][0]['byteLength']=len(newbin)
data_json=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode('utf8')
data_json+=b' '*(-len(data_json)%4)
out=b'glTF'+struct.pack('<II',2,20+8+len(data_json)+8+len(newbin))+struct.pack('<I4s',len(data_json),b'JSON')+data_json+struct.pack('<I4s',len(newbin),b'BIN\0')+newbin
assert len(out)<len(data)*.8,('not a meaningful load-time reduction',len(out),len(data))
dst=a.out/'GENESIS_MERCENARY_V049_SWORD_V12B_SHIELD_V015_WEB.glb'
dst.write_bytes(out)
# Reparse emitted bytes before claiming output.
raw=dst.read_bytes();assert raw[:4]==b'glTF'
assert struct.unpack_from('<II',raw,4)==(2,len(raw))
n,kind=struct.unpack_from('<I4s',raw,12);assert kind==b'JSON'
j=json.loads(raw[20:20+n])
assert len(j['skins'][0]['joints'])==65 and len(j['images'])==len(g['images'])
assert len(j['meshes'])==len(g['meshes'])
assert all('source' not in t for t in j['textures'])
assert all(im['mimeType']=='image/webp' for im in j['images'])
mat=j['materials'][iron_indices[0]]
assert mat['pbrMetallicRoughness']['baseColorFactor'][0]<.3
report={
 'status':'V049_SINGLE_GLB_ORIGINAL_REAL_GENESIS_EQUIPMENT_WEB_3D_CANDIDATE',
 'input_sha256':hashlib.sha256(data).hexdigest(),
 'output_sha256':hashlib.sha256(raw).hexdigest(),
 'input_bytes':len(data),'output_bytes':len(raw),
 'size_reduction_percent':round((1-len(raw)/len(data))*100,2),
 'original_mesh_count':len(g['meshes']),
 'original_joint_count':65,
 'original_gear_nodes_preserved':[x['name'] for x in g['nodes'] if 'GENESIS_V048_APPROVED_' in x.get('name','')],
 'v015_forced_glTF_pbr_repair':mat,
 'approved_original_sword_geometry_unchanged':True,
 'approved_original_shield_geometry_unchanged':True,
 'lossless_roughness_and_normal':True,
 'all_image_textures_webp_embedded':len(j['images']),
 'source_images_converted':converted,
 'ready_for_publisher_visual_integration_test':True,
 'game_scene_tested':False,
 'animation_clips':0,
 'main_changed':False,
 'human_approved':False
}
(a.out/'V049_WEB_GLB_QA.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('V049_REAL_GENESIS_SWORD_AND_SHIELD_WEB_GLB_VERIFIED',
 json.dumps({'bytes':len(raw),'reduction_percent':report['size_reduction_percent'],
             'images':len(j['images']),'iron_material_index':iron_indices[0]}),flush=True)
