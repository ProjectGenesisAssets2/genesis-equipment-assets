#!/usr/bin/env python3
"""V026: replace theatrical inspection gestures with subtle hand-and-gaze motion.
V025 gait/ground/idle unchanged. Input masters protected. Candidate only.
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
 original_idle=next(x for x in source['animations'] if x['name']=='GENESIS_MERC_EQUIPPED_IDLE_V023')
 donor=next(x for x in source['animations'] if x['name']=='Agree_Gesture')
 rules={
  'GENESIS_MERC_INSPECT_SWORD_V025':{'RightArm':.10,'RightForeArm':.13,'RightHand':.06,'Head':.14},
  'GENESIS_MERC_INSPECT_SHIELD_V025':{'LeftArm':.08,'LeftForeArm':.09,'LeftHand':.05,'Head':.12}
 }
 for action in g['animations']:
  if action['name'] in rules:
   for bone,weight in rules[action['name']].items():
    node=ni[bone]
    dst=track(g,action,node,'rotation');baseline=sample(source,sbin,track(source,original_idle,node,'rotation')['output'])
    d=track(source,donor,node,'rotation');keys=sample(source,sbin,d['output'])
    target=keys[max(0,min(len(keys)-1,int(len(keys)*.25)))]
    assert len(baseline)==g['accessors'][dst['output']]['count']
    vals=[mix(q,target,weight*blend_envelope(i/(len(baseline)-1))) for i,q in enumerate(baseline)]
    dst['output']=add(vals)
  action['name']=action['name'].replace('V025','V026')
  action.setdefault('extras',{}).update({'version':'v026','purpose':'quiet explorer inspection; not combat','approved':False})
 for p in ('nodes','skins','meshes','materials','images','textures'):
  assert g.get(p)==old.get(p)
 data=bytes(outdata);data+=b'\0'*(-len(data)%4);g['buffers'][0]['byteLength']=len(data)
 j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*(-len(j)%4)
 result=b'glTF'+struct.pack('<II',2,20+len(j)+8+len(data))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(data),b'BIN\0')+data
 dest=a.out/'mercenary_explorer_v026.glb';dest.write_bytes(result)
 _,verify,_=glb(dest)
 assert len(verify['animations'])==5 and all('ATTACK' not in x['name'] for x in verify['animations'])
 report={'status':'V026_EXPERIMENTAL_CYCLES_REVIEW_PENDING','source_v025_sha256':hashlib.sha256(inputraw).hexdigest(),
 'source_v023_sha256':hashlib.sha256(sourceraw).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),
 'animations':[x['name'] for x in verify['animations']],'rig_bones':24,
 'changes':'subtle chest-height inspection gestures; retain grounded V025 gait and relaxed idle',
 'meshes_unchanged':True,'playcanvas_tested':False,'human_approved':False}
 (a.out/'MERCENARY_EXPLORER_V026_QA.json').write_text(json.dumps(report,indent=2))
 print('V026_PASS',json.dumps(report))
if __name__=='__main__':main()
