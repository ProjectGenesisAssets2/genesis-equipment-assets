#!/usr/bin/env python3
"""Select a genuinely already-rigged medieval male source with finger joints
from Quaternius official free Standard ZIP, never manufacture a new armature.
This is strictly a read-only/source-extraction QA; no approval or main changes.
"""
import json,zipfile,hashlib,re,struct,os,posixpath,base64
from pathlib import Path,PurePosixPath
from urllib.parse import unquote
root=Path('/tmp/genesis_v041')
archive=root/'quaternius_fantasy_standard.zip'
out=Path('output/mercenary_ranger_v042')
out.mkdir(parents=True,exist_ok=True)
assert archive.exists() and zipfile.is_zipfile(archive)
z=zipfile.ZipFile(archive)
allnames=set(z.namelist())
candidates=[]
def scene(name):
 try:
  blob=z.read(name)
  if name.lower().endswith('.glb'):
   if blob[:4]!=b'glTF':return None
   size=struct.unpack_from('<I',blob,12)[0]
   return json.loads(blob[20:20+size])
  return json.loads(blob)
 except Exception:return None
for name in sorted(allnames):
 if not name.lower().endswith(('.gltf','.glb')):continue
 g=scene(name)
 if not isinstance(g,dict) or not g.get('skins'):continue
 joints=[g['nodes'][j].get('name','') for skin in g['skins'] for j in skin.get('joints',[])]
 fingers_l=sorted({n for n in joints if re.search(r'(?i)(thumb|index|middle|ring|pinky).*_l$',n)})
 fingers_r=sorted({n for n in joints if re.search(r'(?i)(thumb|index|middle|ring|pinky).*_r$',n)})
 lower=name.lower()
 score=(18 if 'ranger' in lower else 0)+(12 if 'knight' in lower else 0)+(10 if 'warrior' in lower else 0)+(8 if 'guard' in lower else 0)+(8 if 'male' in lower else 0)-(10 if 'female' in lower else 0)+(24 if '/outfits/' in lower else 0)-(10 if '/modular parts/' in lower else 0)
 candidates.append({'file':name,'node_count':len(g.get('nodes',[])),
 'mesh_count':len(g.get('meshes',[])), 'skinned_joints':len(joints),
 'finger_bones_left':fingers_l,'finger_bones_right':fingers_r,'score':score,
 'format':PurePosixPath(name).suffix.lower(),'gltf':g})
print('V042_OFFICIAL_STANDARD_MODEL_COUNT',len(candidates))
for c in sorted(candidates,key=lambda x:-x['score'])[:35]:
 print('V042_CANDIDATE',c['file'],'joints',c['skinned_joints'],
       'digits',len(c['finger_bones_left']),len(c['finger_bones_right']),'score',c['score'])
winners=[c for c in candidates if c['score']>=35 and len(c['finger_bones_left'])>=10 and len(c['finger_bones_right'])>=10]
report={'source_url':'https://quaternius.itch.io/modular-character-outfits-fantasy',
 'source_license':'CC0 1.0, free Standard pack, publisher',
 'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
 'model_entries':len(candidates),
 'qualified_medieval_models':[{k:v for k,v in c.items() if k!='gltf'} for c in sorted(winners,key=lambda x:-x['score'])[:15]],
 'matches_required':['pre-rigged skeleton','separate anatomical thumb and fingers, left and right','medieval outfit keyword'],
 'visual_verified':False,'skin_influence_verified':False,'animation_tested':False,'approved':False}
if winners:
 best=sorted(winners,key=lambda x:(-x['score'],len(x['file'])))[0]
 entry=best['file']; base=PurePosixPath(entry).parent
 selected={entry}
 g=best['gltf']
 for item in g.get('buffers',[])+g.get('images',[]):
  u=item.get('uri','')
  if not u or u.startswith('data:'):continue
  joined=posixpath.normpath((base/PurePosixPath(unquote(u))).as_posix())
  if '..' in PurePosixPath(joined).parts:continue
  if joined in allnames:selected.add(joined)
  else:
   # Some Quaternius files reference parent-level Textures directory.
   match=[n for n in allnames if n.lower().endswith('/'+PurePosixPath(u).name.lower())]
   if len(match)==1:selected.add(match[0])
 dest=out/'verified_source'
 for name in sorted(selected):
  f=dest/name
  f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(name))

 # Verify actual weighted right/left finger influences, not just bone names.
 try:
  buffers=[]
  for item in g.get('buffers',[]):
   uri=item.get('uri','')
   if uri.startswith('data:'):rawbuf=base64.b64decode(uri.split(',',1)[1])
   else:
    full=posixpath.normpath((base/PurePosixPath(unquote(uri))).as_posix())
    rawbuf=z.read(full)
   buffers.append(rawbuf)
  def rows(accessor_id):
   a0=g['accessors'][accessor_id]
   if 'bufferView' not in a0:raise ValueError('No bufferView in joint accessor')
   v=g['bufferViews'][a0['bufferView']]
   nc={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a0['type']]
   ct=a0['componentType'];c={5121:'B',5123:'H',5125:'I',5126:'f'}[ct]
   step=struct.calcsize('<'+c*nc);offset=v.get('byteOffset',0)+a0.get('byteOffset',0)
   stride=v.get('byteStride',step)
   buf=buffers[v.get('buffer',0)];fmt='<'+c*nc
   result=[struct.unpack_from(fmt,buf,offset+i*stride) for i in range(a0['count'])]
   if a0.get('normalized') and ct in (5121,5123):
    divider={5121:255,5123:65535}[ct]
    result=[tuple(n/divider for n in row) for row in result]
   return result
  hit={'left':0,'right':0}
  checked=0
  for node in g['nodes']:
   if 'mesh' not in node or 'skin' not in node:continue
   skin=g['skins'][node['skin']]
   srcnames=[g['nodes'][ix].get('name','') for ix in skin['joints']]
   selectors={'left':{i for i,n in enumerate(srcnames) if re.search(r'(?i)(thumb|index|middle|ring|pinky).*_l
 report['selected_file_count']=len(selected)
 report['missing_linked_resources']=[u.get('uri') for u in g.get('buffers',[])+g.get('images',[]) if u.get('uri') and not (base/PurePosixPath(unquote(u.get('uri','')))).as_posix() in selected]
 print('V042_SELECTED_SOURCE',best['file'],'files',len(selected))
else:
 print('V042_NO_RANGER_WITH_REAL_DIGITS_VERIFIED_IN_OFFICIAL_STANDARD')
(out/'V042_OFFICIAL_RIG_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
,n)},
              'right':{i for i,n in enumerate(srcnames) if re.search(r'(?i)(thumb|index|middle|ring|pinky).*_r
 report['selected_file_count']=len(selected)
 report['missing_linked_resources']=[u.get('uri') for u in g.get('buffers',[])+g.get('images',[]) if u.get('uri') and not (base/PurePosixPath(unquote(u.get('uri','')))).as_posix() in selected]
 print('V042_SELECTED_SOURCE',best['file'],'files',len(selected))
else:
 print('V042_NO_RANGER_WITH_REAL_DIGITS_VERIFIED_IN_OFFICIAL_STANDARD')
(out/'V042_OFFICIAL_RIG_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
,n)}}
   for primitive in g['meshes'][node['mesh']].get('primitives',[]):
    attrs=primitive.get('attributes',{})
    if 'JOINTS_0' not in attrs or 'WEIGHTS_0' not in attrs:continue
    js=rows(attrs['JOINTS_0']);ws=rows(attrs['WEIGHTS_0'])
    if len(js)!=len(ws):raise ValueError('JOINTS weights count mismatch')
    checked+=len(js)
    for j0,w0 in zip(js,ws):
     for side,inds in selectors.items():
      if sum(weight for joint,weight in zip(j0,w0) if int(joint) in inds)>0.05:
       hit[side]+=1
  report['actual_finger_skinned_vertices']=hit
  report['skinned_vertices_checked']=checked
  report['skin_influence_verified']=hit['left']>25 and hit['right']>25
  print('V042_ACTUAL_DIGIT_WEIGHTS',hit,'checked',checked,'pass',report['skin_influence_verified'])
 except Exception as ex:
  report['weight_audit_error']=str(ex)
  report['skin_influence_verified']=False
 report['selected_original']=best['file']
 report['selected_file_count']=len(selected)
 report['missing_linked_resources']=[u.get('uri') for u in g.get('buffers',[])+g.get('images',[]) if u.get('uri') and not (base/PurePosixPath(unquote(u.get('uri','')))).as_posix() in selected]
 print('V042_SELECTED_SOURCE',best['file'],'files',len(selected))
else:
 print('V042_NO_RANGER_WITH_REAL_DIGITS_VERIFIED_IN_OFFICIAL_STANDARD')
(out/'V042_OFFICIAL_RIG_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
