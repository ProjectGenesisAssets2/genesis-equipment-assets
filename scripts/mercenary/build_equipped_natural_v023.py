#!/usr/bin/env python3
"""Genesis V023: native upright upper body; Quaternius CC0 gait/guard;
no Euler arm guessing, GLB source preserved. Experimental only."""
import argparse,copy,hashlib,json,math,struct
from pathlib import Path
I=[0.,0.,0.,1.]
def qnorm(q):
 m=math.sqrt(sum(x*x for x in q));assert m>.5
 return [x/m for x in q]
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def qrot(q,v):
 x,y,z,w=q
 t=[2*(y*v[2]-z*v[1]),2*(z*v[0]-x*v[2]),2*(x*v[1]-y*v[0])]
 return [v[0]+w*t[0]+y*t[2]-z*t[1],v[1]+w*t[1]+z*t[0]-x*t[2],v[2]+w*t[2]+x*t[1]-y*t[0]]
def slerp(a,b,t):
 a=qnorm(a);b=qnorm(b);d=sum(x*y for x,y in zip(a,b))
 if d<0:b=[-x for x in b];d=-d
 if d>.9995:return qnorm([(1-t)*x+t*y for x,y in zip(a,b)])
 ang=math.acos(max(-1.,min(1.,d)));sn=math.sin(ang)
 return qnorm([(x*math.sin((1-t)*ang)+y*math.sin(t*ang))/sn for x,y in zip(a,b)])
def readglb(path):
 data=path.read_bytes();assert data[:4]==b'glTF' and struct.unpack_from('<I',data,8)[0]==len(data)
 n,typ=struct.unpack_from('<I4s',data,12);assert typ==b'JSON'
 g=json.loads(data[20:20+n]);m,typ=struct.unpack_from('<I4s',data,20+n);assert typ==b'BIN\0'
 return data,g,data[28+n:28+n+m]
def writeglb(g,binary):
 binary+=b'\0'*(-len(binary)%4)
 meta=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode();meta+=b' '*(-len(meta)%4)
 return b'glTF'+struct.pack('<II',2,20+len(meta)+8+len(binary))+struct.pack('<I4s',len(meta),b'JSON')+meta+struct.pack('<I4s',len(binary),b'BIN\0')+binary
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--source',type=Path,required=True)
 parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 raw,g,binary=readglb(args.source);orig=copy.deepcopy(g)
 assert len(g['skins'])==1 and len(g['skins'][0]['joints'])==24 and len(g['animations'])==15
 nodes=g['nodes'];names={n.get('name'):i for i,n in enumerate(nodes)}
 parent={c:p for p,n in enumerate(nodes) for c in n.get('children',[])}
 bones=g['skins'][0]['joints']
 assert all(x in names for x in ['Hips','Spine','Spine01','Spine02','Head','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand','LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot'])
 animations={a['name']:a for a in g['animations']}
 sources=['Idle_02','GENESIS_CC0_WALK_SWORD_GUARD_V015','GENESIS_CC0_SWORD_ATTACK_V015','GENESIS_CC0_SWORD_STANDING_IDLE_V015','GENESIS_CC0_WALK_V015']
 assert all(x in animations for x in sources)
 acache={}
 def access(i):
  if i in acache:return acache[i]
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
  dim={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];assert a['componentType']==5126
  fmt='<'+dim*'f';off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dim*4)
  ret=[list(struct.unpack_from(fmt,binary,off+j*stride)) for j in range(a['count'])];acache[i]=ret;return ret
 tracks={};durations={}
 for key in sources:
  a=animations[key];d={};last=0.
  for ch in a['channels']:
   sm=a['samplers'][ch['sampler']];ts=[v[0] for v in access(sm['input'])];vals=access(sm['output'])
   mode=sm.get('interpolation','LINEAR')
   if mode=='CUBICSPLINE':
    assert len(vals)==len(ts)*3
    vals=[vals[i*3+1] for i in range(len(ts))]
   elif mode not in ('LINEAR','STEP'):raise RuntimeError('interpolation '+key+' '+mode)
   d[(ch['target']['node'],ch['target']['path'])]=(ts,vals,mode)
   last=max(last,ts[-1]);assert len(ts)==len(vals)
  tracks[key]=d;durations[key]=last
 def interp(pair,t,path):
  ts,vals,mode=pair
  if t<=ts[0]:return vals[0][:]
  if t>=ts[-1]:return vals[-1][:]
  lo=0;hi=len(ts)-1
  while hi-lo>1:
   m=(lo+hi)//2
   if ts[m]<=t:lo=m
   else:hi=m
  a=(t-ts[lo])/(ts[hi]-ts[lo]) if mode!='STEP' else 0.
  return slerp(vals[lo],vals[hi],a) if path=='rotation' else [(1-a)*x+a*y for x,y in zip(vals[lo],vals[hi])]
 def sample(name,fraction):
  tr=tracks[name];t=durations[name]*(fraction%1.)
  return {i:{path:interp(info,t,path) for (node,path),info in tr.items() if node==i} for i in bones}
 def compose(kind,phase):
  idle=sample('Idle_02',phase)
  walk=sample('GENESIS_CC0_WALK_SWORD_GUARD_V015',phase)
  attack=sample('GENESIS_CC0_SWORD_ATTACK_V015',phase)
  guard=sample('GENESIS_CC0_SWORD_STANDING_IDLE_V015',phase)
  walk_arms=sample('GENESIS_CC0_WALK_V015',phase)
  walk_start=sample('GENESIS_CC0_WALK_V015',0.)
  result={}
  for id in bones:
   name=nodes[id].get('name','')
   base=idle.get(id,{}).get('rotation',nodes[id].get('rotation',I))
   rotation=list(base)
   if kind=='walk' and name in ('LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase'):
    rotation=slerp(base,walk.get(id,{}).get('rotation',base),.53)
   if kind=='walk' and name in ('LeftShoulder','LeftArm','LeftForeArm','RightShoulder','RightArm','RightForeArm','Spine','Spine01'):
    current=walk_arms.get(id,{}).get('rotation',base)
    previous=walk_start.get(id,{}).get('rotation',base)
    delta=mul(current,[-previous[0],-previous[1],-previous[2],previous[3]])
    swinging=mul(delta,base)
    amplitude=.24 if name.startswith('Right') else .12
    rotation=slerp(base,swinging,amplitude)
   if kind=='attack' and name in ('Spine','Spine01','Spine02','RightShoulder','RightArm','RightForeArm','RightHand'):
    weight=(.66 if name.startswith('Right') else .16)*math.sin(math.pi*phase)**2
    rotation=slerp(base,attack.get(id,{}).get('rotation',base),weight)
   if kind=='block' and name in ('Spine','Spine01','LeftShoulder','LeftArm','LeftForeArm','LeftHand'):
    weight=(.57 if name.startswith('Left') else .14)*math.sin(math.pi*phase)**2
    rotation=slerp(base,guard.get(id,{}).get('rotation',base),weight)
   result[id]={'rotation':qnorm(rotation),
    'translation':list(idle.get(id,{}).get('translation',nodes[id].get('translation',[0,0,0]))),
    'scale':list(idle.get(id,{}).get('scale',nodes[id].get('scale',[1,1,1])))}
  h=names['Hips'];hbase=idle.get(h,{}).get('translation',nodes[h].get('translation',[0,0,0]))
  diff=[0,0,0]
  if kind=='walk':
   cur=walk.get(h,{}).get('translation',hbase)
   zero=sample('GENESIS_CC0_WALK_SWORD_GUARD_V015',0.).get(h,{}).get('translation',hbase)
   diff=[(cur[0]-zero[0])*.25,(cur[1]-zero[1])*.60,(cur[2]-zero[2])*.25]
  result[h]['translation']=[hbase[i]+diff[i] for i in range(3)]
  return result
 def fk(overrides):
  cache={}
  def solve(i):
   if i in cache:return cache[i]
   n=nodes[i];a=overrides.get(i,{})
   loc=a.get('translation',n.get('translation',[0,0,0]))
   q=a.get('rotation',n.get('rotation',I))
   s=a.get('scale',n.get('scale',[1,1,1]))
   if i in parent:
    p,rot,sc=solve(parent[i]);v=qrot(rot,[sc[j]*loc[j] for j in range(3)])
    pos=[p[j]+v[j] for j in range(3)];r=qnorm(mul(rot,q));size=[sc[j]*s[j] for j in range(3)]
   else:pos=loc;r=qnorm(q);size=s
   cache[i]=(pos,r,size);return cache[i]
  for i in bones:solve(i)
  return cache
 baseline=min(fk(compose('idle',0.))[names[x]][0][1] for x in ['LeftFoot','RightFoot'])
 newbin=bytearray(binary);clips=[]
 def add(data,typ):
  while len(newbin)%4:newbin.append(0)
  pos=len(newbin);flat=[float(x) for row in data for x in row]
  newbin.extend(struct.pack('<'+'f'*len(flat),*flat))
  view=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':pos,'byteLength':len(flat)*4})
  ix=len(g['accessors']);g['accessors'].append({'bufferView':view,'componentType':5126,'count':len(data),'type':typ})
  return ix
 for kind,seconds,frames in [('idle',2.,50),('walk',1.45,44),('attack',1.1,38),('block',.85,35)]:
  poses=[compose(kind,j/frames) for j in range(frames+1)]
  offsets=[];h=names['Hips']
  for pose in poses:
   y=min(fk(pose)[names[f]][0][1] for f in ('LeftFoot','RightFoot'))
   correction=(baseline-y)/.01
   assert abs(correction)<=12.,(kind,correction)
   pose[h]['translation'][1]+=correction
   assert abs(min(fk(pose)[names[f]][0][1] for f in ('LeftFoot','RightFoot'))-baseline)<.001
   offsets.append(correction)
  tid=add([[seconds*j/frames] for j in range(frames+1)],'SCALAR')
  channels=[];samplers=[]
  for bone in bones:
   rotations=[p[bone]['rotation'] for p in poses]
   for i in range(1,len(rotations)):
    if sum(x*y for x,y in zip(rotations[i],rotations[i-1]))<0:rotations[i]=[-x for x in rotations[i]]
   val=add(rotations,'VEC4')
   channels.append({'sampler':len(samplers),'target':{'node':bone,'path':'rotation'}})
   samplers.append({'input':tid,'output':val,'interpolation':'LINEAR'})
  for bone in bones:
   for channel in ('translation','scale'):
    val=add([p[bone][channel] for p in poses],'VEC3')
    channels.append({'sampler':len(samplers),'target':{'node':bone,'path':channel}})
    samplers.append({'input':tid,'output':val,'interpolation':'LINEAR'})
  clip='GENESIS_MERC_EQUIPPED_'+kind.upper()+'_V023'
  g['animations'].append({'name':clip,'channels':channels,'samplers':samplers,
   'extras':{'origin':'original Meshy Idle_02 + partial CC0 Quaternius',
   'game_equipment':'separate sword+shield native joint sockets',
   'loop':kind in ('idle','walk'),'experimental':True,'approved':False}})
  f0=fk(poses[0])
  clips.append({'name':clip,'frames':frames+1,'duration_seconds':seconds,
   'foot_correction_cm_min':round(min(offsets),2),'foot_correction_cm_max':round(max(offsets),2),
   'head_world_y_m':round(f0[names['Head']][0][1],4),
   'left_hand_y_m':round(f0[names['LeftHand']][0][1],4),
   'right_hand_y_m':round(f0[names['RightHand']][0][1],4)})
 assert len(g['animations'])==19 and g['animations'][:15]==orig['animations']
 for field in ('nodes','skins','meshes','images','materials','textures'):
  assert g.get(field)==orig.get(field),field
 g['buffers'][0]['byteLength']=len(newbin)
 out=writeglb(g,bytes(newbin))
 dst=args.out/'mercenary_equipment_natural_v023.glb';dst.write_bytes(out)
 report={'status':'V023_EXPERIMENTAL_REAL_NATIVE_ANIMATION_PENDING_CYCLES_HUMAN_REVIEW',
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),
 'original_15_animations_untouched':True,'new_animations':clips,
 'original_model_bones_and_materials_untouched':True,'total_animations':19,
 'playcanvas_tested':False,'human_approved':False}
 (args.out/'MERCENARY_NATURAL_MOTION_V023.json').write_text(json.dumps(report,indent=2))
 print('GENESIS_EQUIPPED_NATURAL_MOTION_V023',json.dumps({'clips':clips,'sha256':report['output_sha256']}),flush=True)
if __name__=='__main__':main()
