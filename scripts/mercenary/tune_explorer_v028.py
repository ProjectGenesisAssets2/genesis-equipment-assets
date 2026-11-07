#!/usr/bin/env python3
"""V028: replace theatrical inspection gestures with subtle hand-and-gaze motion.
V027 gait/ground/idle unchanged. Input masters protected. Candidate only.
"""
import argparse,copy,json,hashlib,math,struct
from pathlib import Path

def glb(path):
 raw=path.read_bytes();assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
 j=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+j]);n=struct.unpack_from('<I',raw,20+j)[0]
 return raw,g,raw[28+j:28+j+n]

def mix(a,b,t):
 dot=sum(x*y for x,y in zip(a,b))
 if dot<0:b=[-x for x in b];dot=-dot
 if dot>.9995:z=[a[i]*(1-t)+b[i]*t for i in range(4)]
 else:
  theta=math.acos(min(1,max(-1,dot)));st=math.sin(theta)
  z=[(a[i]*math.sin((1-t)*theta)+b[i]*math.sin(t*theta))/st for i in range(4)]
 d=math.sqrt(sum(x*x for x in z));return [x/d for x in z]
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def blend_envelope(t):
 if t<.14:return 0
 if t<.36:return ease((t-.14)/.22)
 if t<.70:return 1
 if t<.94:return 1-ease((t-.70)/.24)
 return 0

def main():
 ap=argparse.ArgumentParser()
 for n in ('base','original','out'):ap.add_argument('--'+n,required=True,type=Path)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 inputraw,g,oldbin=glb(a.base);sourceraw,source,sbin=glb(a.original)
 assert len(g['animations'])==5 and len(source['animations'])==19
 old=copy.deepcopy(g);ni={n.get('name'):i for i,n in enumerate(g['nodes'])}
 def track(g,action,node,path):
  for ch in action['channels']:
   if ch['target']['node']==node and ch['target']['path']==path:
    return action['samplers'][ch['sampler']]
  raise RuntimeError((action['name'],node,path))
 def sample(g,b,ix):
  ac=g['accessors'][ix];v=g['bufferViews'][ac['bufferView']];k={'VEC4':4,'VEC3':3,'SCALAR':1}[ac['type']]
  off=v.get('byteOffset',0)+ac.get('byteOffset',0);stride=v.get('byteStride',k*4)
  return [list(struct.unpack_from('<'+'f'*k,b,off+j*stride)) for j in range(ac['count'])]
 outdata=bytearray(oldbin)
 def add(rows):
  while len(outdata)%4:outdata.append(0)
  start=len(outdata);data=[float(v) for row in rows for v in row];outdata.extend(struct.pack('<'+'f'*len(data),*data))
  vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(data)*4})
  ix=len(g['accessors']);g['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(rows),'type':'VEC4'})
  return ix
 rest_idle=next(x for x in g['animations'] if x['name']=='GENESIS_MERC_IDLE_V027')
 rules={
  'GENESIS_MERC_INSPECT_SWORD_V027':{'RightShoulder':.40,'RightArm':.58,'RightForeArm':.62,'RightHand':.38,'Spine02':.30}
 }
 for action in g['animations']:
  if action['name'] in rules:
   for bone,weight in rules[action['name']].items():
    node=ni[bone]
    dst=track(g,action,node,'rotation')
    baseline=sample(old,oldbin,track(old,action,node,'rotation')['output'])
    rest=sample(old,oldbin,track(old,rest_idle,node,'rotation')['output'])
    assert len(baseline)==g['accessors'][dst['output']]['count']
    vals=[mix(q,rest[round(i*(len(rest)-1)/(len(baseline)-1))],weight) for i,q in enumerate(baseline)]
    dst['output']=add(vals)
  action['name']=action['name'].replace('V027','V028')
  action.setdefault('extras',{}).update({'version':'v028','purpose':'quiet explorer inspection; not combat','approved':False})
 for p in ('nodes','skins','meshes','materials','images','textures'):
  assert g.get(p)==old.get(p)
 data=bytes(outdata);data+=b'\0'*(-len(data)%4);g['buffers'][0]['byteLength']=len(data)
 j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
 result=b'glTF'+struct.pack('<II',2,20+len(j)+8+len(data))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(data),b'BIN\0')+data
 dest=a.out/'mercenary_explorer_v028.glb';dest.write_bytes(result)
 _,verify,_=glb(dest)
 assert len(verify['animations'])==5 and all('ATTACK' not in x['name'] for x in verify['animations'])
 report={'status':'V028_EXPERIMENTAL_CYCLES_REVIEW_PENDING','source_v027_sha256':hashlib.sha256(inputraw).hexdigest(),
 'source_v023_sha256':hashlib.sha256(sourceraw).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),
 'animations':[x['name'] for x in verify['animations']],'rig_bones':24,
 'changes':'sword inspection closer to body via blend toward source neutral idle; no changes to shield or gait',
 'meshes_unchanged':True,'playcanvas_tested':False,'human_approved':False}
 (a.out/'MERCENARY_EXPLORER_V028_QA.json').write_text(json.dumps(report,indent=2))
 print('V028_PASS',json.dumps(report))
if __name__=='__main__':main()
