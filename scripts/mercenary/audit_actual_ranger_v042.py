#!/usr/bin/env python3
"""Verify official, originally rigged Quaternius CC0 male Ranger with real
skinning to both sets of fingers. Extract original glTF and its dependencies,
never edit rig/mesh, never approve or integrate the game automatically.
"""
import json,zipfile,hashlib,struct,posixpath,re
from pathlib import Path,PurePosixPath
from urllib.parse import unquote
from collections import Counter

arc=Path('/tmp/genesis_v041/quaternius_fantasy_standard.zip')
dest=Path('output/mercenary_ranger_v042')
dest.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(arc) as z:
    files=z.namelist()
    sources=[f for f in files if f.endswith('/Outfits/Male_Ranger.gltf') and 'glTF' in f]
    assert len(sources)==1,sources
    name=sources[0]
    g=json.loads(z.read(name))
    assert len(g.get('skins',[]))==1,'No original skin in official Male_Ranger'
    joints=g['skins'][0]['joints']
    assert len(joints)==65,len(joints)
    bone_names=[g['nodes'][i].get('name','') for i in joints]
    left=[(i,n) for i,n in enumerate(bone_names) if n.endswith('_l') and any(x in n.lower() for x in ('thumb','index','middle','ring','pinky'))]
    right=[(i,n) for i,n in enumerate(bone_names) if n.endswith('_r') and any(x in n.lower() for x in ('thumb','index','middle','ring','pinky'))]
    print('V042_RIG_JOINTS',len(joints),'LEFT_DIGIT_JOINTS',len(left),'RIGHT_DIGIT_JOINTS',len(right),flush=True)
    assert len(left)>=15 and len(right)>=15,(left,right)
    base=posixpath.dirname(name)
    dependencies={}
    for item in g.get('buffers',[])+g.get('images',[]):
        uri=item.get('uri')
        if not uri or uri.startswith('data:'):continue
        path=posixpath.normpath(posixpath.join(base,unquote(uri)))
        assert not path.startswith('../'),'unsafe path'
        if path not in files:
            hits=[file for file in files if file.endswith('/'+posixpath.basename(path))]
            assert len(hits)==1,(uri,'missing or ambiguous linked resource')
            # Preserve expected referenced folder relative to the original GLTF.
            dependencies[path]=z.read(hits[0])
        else:dependencies[path]=z.read(path)
    blobs=[]
    for item in g['buffers']:
        uri=item.get('uri','')
        assert uri and not uri.startswith('data:'),'unexpected buffer'
        key=posixpath.normpath(posixpath.join(base,unquote(uri)))
        blobs.append(dependencies[key])
    def accessor(index):
        acc=g['accessors'][index]
        assert 'sparse' not in acc and 'bufferView' in acc,'unsupported sparse accessor'
        v=g['bufferViews'][acc['bufferView']]
        types={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
        codes={5121:'B',5123:'H',5125:'I',5126:'f'}
        cols=types[acc['type']];fmt='<'+codes[acc['componentType']]*cols
        width=struct.calcsize(fmt)
        offset=v.get('byteOffset',0)+acc.get('byteOffset',0)
        stride=v.get('byteStride',width)
        buf=blobs[v.get('buffer',0)]
        rows=[struct.unpack_from(fmt,buf,offset+i*stride) for i in range(acc['count'])]
        if acc.get('normalized') and acc['componentType'] in (5121,5123):
            div={5121:255,5123:65535}[acc['componentType']]
            rows=[tuple(c/div for c in row) for row in rows]
        return rows
    left_ids=set(j for j,_ in left)
    right_ids=set(j for j,_ in right)
    weighted={'left':0,'right':0};maxweights={'left':0.0,'right':0.0};verts=0;mesh_prims=0
    for node in g['nodes']:
        if 'mesh' not in node or 'skin' not in node:continue
        assert node['skin']==0
        for prim in g['meshes'][node['mesh']]['primitives']:
            attrs=prim.get('attributes',{})
            if not {'JOINTS_0','WEIGHTS_0'}<=attrs.keys():continue
            inds=accessor(attrs['JOINTS_0']);w=accessor(attrs['WEIGHTS_0'])
            assert len(inds)==len(w)
            mesh_prims+=1;verts+=len(inds)
            for j0,w0 in zip(inds,w):
                for side,indices in (('left',left_ids),('right',right_ids)):
                    weight=sum(float(v) for k,v in zip(j0,w0) if int(k) in indices)
                    maxweights[side]=max(maxweights[side],weight)
                    if weight>.05:weighted[side]+=1
    print('V042_WEIGHTED_FINGERS',weighted,'MAX_WEIGHTS',maxweights,'CHECKED_VERTICES',verts,flush=True)
    assert verts>1000 and mesh_prims>=1
    valid=weighted['left']>=25 and weighted['right']>=25
    target=dest/'source'
    for fname,data in {name:z.read(name),**dependencies}.items():
        o=target/fname;o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(data)
    report={
        'status':'ORIGINAL_FINGER_RIG_SKIN_QA_PASS' if valid else 'REJECT_UNWEIGHTED_FINGERS',
        'character':'Quaternius Modular Character Outfits - Fantasy / Male Ranger Standard',
        'source_publisher':'https://quaternius.itch.io/modular-character-outfits-fantasy',
        'source_license':'CC0 as advertised by publisher, Standard free download',
        'zip_sha256':hashlib.sha256(arc.read_bytes()).hexdigest(),
        'gltf_sha256':hashlib.sha256(z.read(name)).hexdigest(),
        'source_path':name,'extracted_source_files':[name,*dependencies],
        'bone_count':len(joints),
        'left_finger_bone_names':[n for _,n in left],
        'right_finger_bone_names':[n for _,n in right],
        'left_weighted_vertices':weighted['left'],
        'right_weighted_vertices':weighted['right'],
        'checked_vertices':verts,
        'max_finger_weights':maxweights,
        'finger_skinning_verified':valid,
        'visual_reviewed':False,'original_model_modified':False,
        'mixamo_tested':False,'human_approved':False,'playcanvas_tested':False
    }
    (dest/'V042_ORIGINAL_MALE_RANGER_FINGER_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if not valid:raise RuntimeError('The Ranger has finger joint names but NOT verified nonzero deformation weights; do not approve')
    print('V042_REAL_MALE_RANGER_FINGERS_PASS',json.dumps({'source':name,'bones':len(joints),'skin_weighted_vertices':weighted,'source_files':len(dependencies)+1}),flush=True)
