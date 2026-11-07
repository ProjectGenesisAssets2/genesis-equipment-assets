#!/usr/bin/env python3
"""Select a genuinely already-rigged medieval male source with finger joints
from Quaternius official free Standard ZIP, never manufacture a new armature.
This is strictly a read-only/source-extraction QA; no approval or main changes.
"""
import json,zipfile,hashlib,re,struct,os
from pathlib import Path,PurePosixPath
from urllib.parse import unquote
root=Path('/tmp/genesis_v041')
archive=root/'quaternius_fantasy_standard.zip'
out=Path('output/mercenary_finger_rig_v041')
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
 score=(10 if 'knight' in lower else 0)+(9 if 'warrior' in lower else 0)+(8 if 'soldier' in lower else 0)+(7 if 'guard' in lower else 0)+(4 if 'male' in lower else 0)+(2 if 'fullbody' in lower else 0)
 candidates.append({'file':name,'node_count':len(g.get('nodes',[])),
 'mesh_count':len(g.get('meshes',[])), 'skinned_joints':len(joints),
 'finger_bones_left':fingers_l,'finger_bones_right':fingers_r,'score':score,
 'format':PurePosixPath(name).suffix.lower(),'gltf':g})
print('V041_OFFICIAL_STANDARD_MODEL_COUNT',len(candidates))
for c in sorted(candidates,key=lambda x:-x['score'])[:35]:
 print('V041_CANDIDATE',c['file'],'joints',c['skinned_joints'],
       'digits',len(c['finger_bones_left']),len(c['finger_bones_right']),'score',c['score'])
winners=[c for c in candidates if c['score']>=7 and len(c['finger_bones_left'])>=10 and len(c['finger_bones_right'])>=10]
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
  joined=(base/PurePosixPath(unquote(u))).as_posix()
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
 report['selected_original']=best['file']
 report['selected_file_count']=len(selected)
 report['missing_linked_resources']=[u.get('uri') for u in g.get('buffers',[])+g.get('images',[]) if u.get('uri') and not (base/PurePosixPath(unquote(u.get('uri','')))).as_posix() in selected]
 print('V041_SELECTED_SOURCE',best['file'],'files',len(selected))
else:
 print('V041_NO_PRE-RIGGED_MEDIEVAL_DIGITS_VERIFIED_IN_OFFICIAL_STANDARD')
(out/'V041_OFFICIAL_RIG_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
