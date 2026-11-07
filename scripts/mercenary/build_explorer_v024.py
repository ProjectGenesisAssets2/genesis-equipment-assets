#!/usr/bin/env python3
"""Project Genesis mercenary explorer V024 — no visible combat.
Produce five deliberately scoped glTF clips. Preserves original 3D geometry,
skin, materials, joint sockets. Gear models remain separate inventory assets.
The V023 source is never overwritten.
"""
import argparse, copy, hashlib, json, math, struct
from pathlib import Path

NAMES = {
 'idle': 'GENESIS_MERC_IDLE_V024',
 'walk': 'GENESIS_MERC_WALK_V024',
 'inspect_sword': 'GENESIS_MERC_INSPECT_SWORD_V024',
 'inspect_shield': 'GENESIS_MERC_INSPECT_SHIELD_V024',
 'walk_equipped': 'GENESIS_MERC_WALK_EQUIPPED_V024',
}

def read_glb(p):
 data=p.read_bytes()
 assert data[:4]==b'glTF' and struct.unpack_from('<II',data,4)==(2,len(data)), 'not valid GLB2'
 jlen,jtype=struct.unpack_from('<I4s',data,12)
 assert jtype==b'JSON'
 g=json.loads(data[20:20+jlen]);blen,btype=struct.unpack_from('<I4s',data,20+jlen)
 assert btype==b'BIN\0'
 return data,g,data[28+jlen:28+jlen+blen]

def write_glb(g, data):
 b=data+b'\0'*(-len(data)%4)
 g['buffers'][0]['byteLength']=len(b)
 j=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode('utf-8');j+=b' '*(-len(j)%4)
 return b'glTF'+struct.pack('<II',2,20+len(j)+8+len(b))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(b),b'BIN\0')+b

def qnorm(q):
 mag=math.sqrt(sum(x*x for x in q));assert mag>.5
 return [float(x/mag) for x in q]

def slerp(a,b,t):
 a=qnorm(a);b=qnorm(b);dot=sum(x*y for x,y in zip(a,b))
 if dot<0:b=[-x for x in b];dot=-dot
 if dot>.9995:return qnorm([(1-t)*x+t*y for x,y in zip(a,b)])
 ang=math.acos(min(1,max(-1,dot)));s=math.sin(ang)
 return qnorm([(x*math.sin((1-t)*ang)+y*math.sin(t*ang))/s for x,y in zip(a,b)])

def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)

def intensity(p):
 if p<.13:return 0.
 if p<.38:return smooth((p-.13)/.25)
 if p<.70:return 1.
 if p<.95:return 1.-smooth((p-.70)/.25)
 return 0.

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--source',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 raw,g,original_bin=read_glb(a.source)
 old=copy.deepcopy(g)
 assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==24
 assert len(g['animations'])==19, 'use verified V023 19 clip source only'
 ni={n.get('name'):i for i,n in enumerate(g['nodes'])}
 assert all(n in ni for n in ['RightArm','RightForeArm','RightHand','LeftArm','LeftForeArm','LeftHand','Head','GENESIS_SOCKET_WEAPON_R','GENESIS_SOCKET_SHIELD_L'])
 assert ni['GENESIS_SOCKET_WEAPON_R'] in g['nodes'][ni['RightHand']].get('children',[])
 assert ni['GENESIS_SOCKET_SHIELD_L'] in g['nodes'][ni['LeftHand']].get('children',[])
 source_actions={x['name']:x for x in old['animations']}
 for n in ('Idle_02','GENESIS_MERC_EQUIPPED_WALK_V023','GENESIS_MERC_EQUIPPED_IDLE_V023','Agree_Gesture'):
  assert n in source_actions
 cache={}
 def values(ix):
  if ix in cache:return cache[ix]
  ac=g['accessors'][ix];view=g['bufferViews'][ac['bufferView']]
  assert ac['componentType']==5126
  dims={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']]
  offset=view.get('byteOffset',0)+ac.get('byteOffset',0)
  stride=view.get('byteStride',dims*4)
  fmt='<'+dims*'f'
  rows=[list(struct.unpack_from(fmt,original_bin,offset+i*stride)) for i in range(ac['count'])]
  cache[ix]=rows;return rows
 def channels(a):
  return {(ch['target']['node'],ch['target']['path']):a['samplers'][ch['sampler']] for ch in a['channels']}
 def sampled_key(sm,phase):
  ts=values(sm['input']);vs=values(sm['output']);assert len(ts)==len(vs)
  target=ts[0][0]+(ts[-1][0]-ts[0][0])*max(0.,min(1.,phase))
  for i in range(1,len(ts)):
   if ts[i][0]>=target:
    f=(target-ts[i-1][0])/max(1e-9,ts[i][0]-ts[i-1][0])
    return slerp(vs[i-1],vs[i],f)
  return qnorm(vs[-1])

 newbin=bytearray(original_bin)
 def accessor(vals,typ):
  while len(newbin)%4:newbin.append(0)
  offset=len(newbin);flat=[float(x) for v in vals for x in v]
  newbin.extend(struct.pack('<'+'f'*len(flat),*flat))
  bv=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':4*len(flat)})
  ai=len(g['accessors']);g['accessors'].append({'bufferView':bv,'componentType':5126,'count':len(vals),'type':typ})
  return ai

 output=[]
 def cloned(source,name,loop=True):
  r=copy.deepcopy(source_actions[source]);r['name']=name
  r['extras']={'project':'Genesis','version':'v024','intent':'non-combat explorer','loop':loop,'source':source,'approved':False}
  return r

 output.append(cloned('Idle_02',NAMES['idle']))
 output.append(cloned('GENESIS_MERC_EQUIPPED_WALK_V023',NAMES['walk']))

 idle=source_actions['GENESIS_MERC_EQUIPPED_IDLE_V023']
 agree=channels(source_actions['Agree_Gesture'])
 for which in ('sword','shield'):
  name=NAMES['inspect_'+which]
  r=cloned('GENESIS_MERC_EQUIPPED_IDLE_V023',name,True)
  target_parts=({
    'RightShoulder':.40,'RightArm':.70,'RightForeArm':.82,'RightHand':.42,
    'Spine02':.10,'Head':.14
   } if which=='sword' else {
    'LeftShoulder':.42,'LeftArm':.72,'LeftForeArm':.80,'LeftHand':.42,
    'Spine02':.10,'Head':.14
   })
  original_time=values(idle['samplers'][0]['input'])
  seconds=3.4
  n=len(original_time)
  new_time=accessor([[seconds*j/(n-1)] for j in range(n)],'SCALAR')
  for s in r['samplers']:s['input']=new_time
  original_track=channels(idle)
  for bone,weight in target_parts.items():
   nid=ni[bone];path=(nid,'rotation');base_sm=original_track[path]
   target=sampled_key(agree[path],.25) if path in agree else sampled_key(base_sm,.25)
   bases=values(base_sm['output'])
   assert len(bases)==n
   result=[]
   for j,base in enumerate(bases):
    t=j/(n-1)
    strength=weight*intensity(t)
    if .38<t<.70:strength*=.985+.015*math.sin(2*math.pi*(t-.38)/.32)
    result.append(slerp(base,target,strength))
   ix=accessor(result,'VEC4')
   for ch in r['channels']:
    if (ch['target']['node'],ch['target']['path'])==path:
     r['samplers'][ch['sampler']]['output']=ix
     break
   else:raise AssertionError(path)
  r['extras']['inspect_item']=which
  r['extras']['hands_use_existing_sockets']=True
  output.append(r)
 output.append(cloned('GENESIS_MERC_EQUIPPED_WALK_V023',NAMES['walk_equipped']))
 g['animations']=output
 for prop in ('nodes','skins','meshes','images','textures','materials','scene','scenes'):
  assert g.get(prop)==old.get(prop),(prop,'protected source altered')
 assert len(g['animations'])==5
 out=write_glb(g,bytes(newbin))
 path=a.out/'mercenary_explorer_v024.glb';path.write_bytes(out)
 _,reparsed,_=read_glb(path)
 assert len(reparsed['animations'])==5 and [x['name'] for x in reparsed['animations']]==list(NAMES.values())
 for action in reparsed['animations']:
  for s in action['samplers']:
   for key in ('input','output'):assert 0<=s[key]<len(reparsed['accessors'])
  for ch in action['channels']:
   assert 0<=ch['sampler']<len(action['samplers'])
 report={
  'status':'V024_EXPERIMENTAL_NOT_VISUALLY_APPROVED',
  'scope':'walk, inspect sword, inspect shield, walk equipped, dynamic item attachment to hand sockets',
  'source_sha256':hashlib.sha256(raw).hexdigest(),
  'output_sha256':hashlib.sha256(out).hexdigest(),
  'source_actions':19,'export_actions':len(output),
  'export_clip_names':[x['name'] for x in output],
  'bones':24,'source_mesh_geometry_and_materials_unchanged':True,
  'socket_weapon_node':ni['GENESIS_SOCKET_WEAPON_R'],
  'socket_shield_node':ni['GENESIS_SOCKET_SHIELD_L'],
  'weapons_embedded_in_character_glb':False,
  'equip_logic':'Attach existing inventory GLB instances to named sockets; calibrated local offsets needed for exact model grips',
  'playcanvas_tested':False,'human_visual_approved':False,'source_glb_unmodified':True}
 (a.out/'MERCENARY_EXPLORER_V024_QA.json').write_text(json.dumps(report,indent=2))
 print('MERCENARY_EXPLORER_V024_BUILT',json.dumps(report),flush=True)

if __name__=='__main__':main()
