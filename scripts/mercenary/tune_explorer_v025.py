#!/usr/bin/env python3
"""V025 incremental pose correction of the verified V024 GLB (no source overwrite).
Bring inspections down to chest height and ground the rig 3.5cm. No attacks.
"""
import argparse,copy,hashlib,json,math,struct
from pathlib import Path

def load(p):
 b=p.read_bytes();j=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+j]);z=struct.unpack_from('<I',b,20+j)[0]
 assert b[:4]==b'glTF' and struct.unpack_from('<I',b,8)[0]==len(b)
 return b,g,b[28+j:28+j+z]
def pack(g,bin):
 bin+=b'\0'*(-len(bin)%4);g['buffers'][0]['byteLength']=len(bin)
 j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
 return b'glTF'+struct.pack('<II',2,20+len(j)+8+len(bin))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(bin),b'BIN\0')+bin

def norm(q):
 s=math.sqrt(sum(v*v for v in q));assert s>.5;return [v/s for v in q]
def mix(a,b,t):
 a=norm(a);b=norm(b);dot=sum(x*y for x,y in zip(a,b))
 if dot<0:b=[-x for x in b];dot=-dot
 if dot>.9995:return norm([(1-t)*x+t*y for x,y in zip(a,b)])
 angle=math.acos(max(-1.,min(1.,dot)));d=math.sin(angle)
 return norm([(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/d for x,y in zip(a,b)])
def ease(t):t=max(0.,min(1.,t));return t*t*(3.-2.*t)
def inspect_intensity(p):
 if p<.13:return 0.
 if p<.38:return ease((p-.13)/.25)
 if p<.7:return 1.
 if p<.95:return 1.-ease((p-.7)/.25)
 return 0.

def main():
 ap=argparse.ArgumentParser()
 for n in ('base','original','out'):ap.add_argument('--'+n,required=True,type=Path)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 raw,g,bin=load(a.base);origraw,original,origbin=load(a.original)
 assert len(g['animations'])==5 and len(original['animations'])==19
 before=copy.deepcopy(g)
 ni={n.get('name'):i for i,n in enumerate(g['nodes'])}
 ac_cache={}
 def samples(data,src,ix):
  key=(id(src),ix)
  if key in ac_cache:return ac_cache[key]
  a=src['accessors'][ix];v=src['bufferViews'][a['bufferView']]
  dim={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];assert a['componentType']==5126
  off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',4*dim)
  value=[list(struct.unpack_from('<'+'f'*dim,data,off+stride*i)) for i in range(a['count'])]
  ac_cache[key]=value;return value
 def tracks(anim):return {(x['target']['node'],x['target']['path']):anim['samplers'][x['sampler']] for x in anim['channels']}
 def from_clip(name):return next(v for v in original['animations'] if v['name']==name)
 def donor(name,bone,phase=.25):
  anim=from_clip(name);sm=tracks(anim)[(ni[bone],'rotation')]
  tt=samples(origbin,original,sm['input']);vv=samples(origbin,original,sm['output'])
  t=tt[0][0]+(tt[-1][0]-tt[0][0])*phase
  for j in range(1,len(tt)):
   if tt[j][0]>=t:
    f=(t-tt[j-1][0])/(tt[j][0]-tt[j-1][0]);return mix(vv[j-1],vv[j],f)
  return vv[-1]
 added=bytearray(bin)
 def accessor(rows,typ):
  while len(added)%4:added.append(0)
  off=len(added);flat=[float(v) for row in rows for v in row]
  added.extend(struct.pack('<'+'f'*len(flat),*flat))
  idx=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':4*len(flat)})
  ai=len(g['accessors']);g['accessors'].append({'bufferView':idx,'componentType':5126,'count':len(rows),'type':typ})
  return ai

 for act in g['animations']:
  old_name=act['name'];kind=old_name.replace('GENESIS_MERC_','').replace('_V024','').lower()
  src_tracks=tracks(act)
  if kind=='idle':
   rules={'RightShoulder':('Hand_on_Hip_Gesture',.20),'RightArm':('Hand_on_Hip_Gesture',.60),
    'RightForeArm':('Hand_on_Hip_Gesture',.78),'RightHand':('Hand_on_Hip_Gesture',.20)}
  elif kind=='walk':
   rules={'RightShoulder':('Hand_on_Hip_Gesture',.13),'RightArm':('Hand_on_Hip_Gesture',.43),
    'RightForeArm':('Hand_on_Hip_Gesture',.56),'RightHand':('Hand_on_Hip_Gesture',.16)}
  elif kind=='inspect_sword':
   rules={'RightShoulder':('Agree_Gesture',.15),'RightArm':('Agree_Gesture',.38),
    'RightForeArm':('Agree_Gesture',.43),'RightHand':('Agree_Gesture',.15),
    'Head':('Agree_Gesture',.08)}
  elif kind=='inspect_shield':
   rules={'LeftShoulder':('Agree_Gesture',.14),'LeftArm':('Agree_Gesture',.28),
    'LeftForeArm':('Agree_Gesture',.27),'LeftHand':('Agree_Gesture',.10),
    'Head':('Agree_Gesture',.07),
    'RightShoulder':('Hand_on_Hip_Gesture',.15),'RightArm':('Hand_on_Hip_Gesture',.48),
    'RightForeArm':('Hand_on_Hip_Gesture',.63)}
  elif kind=='walk_equipped':rules={}
  else:raise AssertionError(kind)
  for bone,(source,w) in rules.items():
   idx=ni[bone];key=(idx,'rotation');sm=src_tracks[key]
   orig_values=samples(bin,before,sm['output']);count=len(orig_values)
   if kind.startswith('inspect'):
    start_tracks=tracks(from_clip('GENESIS_MERC_EQUIPPED_IDLE_V023'))
    orig_values=samples(origbin,original,start_tracks[key]['output'])
    assert len(orig_values)==count
   target=donor(source,bone)
   result=[]
   for j,q in enumerate(orig_values):
    phase=j/(count-1)
    amount=w*inspect_intensity(phase) if kind.startswith('inspect') and source=='Agree_Gesture' else w
    if kind.startswith('walk'):amount*=.94+.06*math.sin(math.pi*2*phase)
    result.append(mix(q,target,amount))
   new=accessor(result,'VEC4')
   for ch in act['channels']:
    if (ch['target']['node'],ch['target']['path'])==key:
     act['samplers'][ch['sampler']]['output']=new;break
  hips=(ni['Hips'],'translation');sm=src_tracks[hips]
  value=samples(bin,before,sm['output'])
  new=accessor([[row[0],row[1]-3.5,row[2]] for row in value],'VEC3')
  for ch in act['channels']:
   if (ch['target']['node'],ch['target']['path'])==hips:
    act['samplers'][ch['sampler']]['output']=new;break
  act['name']=old_name.replace('V024','V025')
  act.setdefault('extras',{}).update({'version':'v025','revision':'lower inspections and heel-to-floor','approved':False})

 for field in ('nodes','skins','meshes','materials','images','textures'):
  assert before.get(field)==g.get(field),field
 out=pack(g,bytes(added));path=a.out/'mercenary_explorer_v025.glb';path.write_bytes(out)
 _,check,_=load(path)
 assert len(check['animations'])==5 and all('ATTACK' not in v['name'] for v in check['animations'])
 report={'status':'V025_CANDIDATE_REQUIRES_BLENDER_QA','source_v024_sha256':hashlib.sha256(raw).hexdigest(),
 'source_v023_sha256':hashlib.sha256(origraw).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),
 'actions':[v['name'] for v in g['animations']],'meshes_unchanged':True,'rig_bones':24,
 'hip_ground_adjustment_cm':-3.5,'inspect_sword':'lower chest-height aim','inspect_shield':'subtle shield examination',
 'playcanvas_tested':False,'human_approved':False}
 (a.out/'MERCENARY_EXPLORER_V025_QA.json').write_text(json.dumps(report,indent=2))
 print('V025_GESTURE_AND_FEET_CORRECTION',json.dumps(report))
if __name__=='__main__':main()
