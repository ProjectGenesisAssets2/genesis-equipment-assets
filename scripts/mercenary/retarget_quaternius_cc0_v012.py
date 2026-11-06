#!/usr/bin/env python3
"""Transfer CC0 Quaternius sword/walk motion to Meshy Genesis mercenary glTF rig.

Source Quaternius 65-joint rotations are remapped as global rest-space motion
onto original 24-joint rig, retaining 10 original clips and original buffers.
NO arm-rotation guessing, no replacements of source geometry or approved sword.
This remains experimental until Blender/PlayCanvas and human visual QA.
"""
import argparse,copy,hashlib,json,math,struct
from pathlib import Path
# glTF quaternion [x,y,z,w]
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X,w*W-x*X-y*Y-z*Z]
def inv(a):return [-a[0],-a[1],-a[2],a[3]]
def unit(q):
 length=math.sqrt(sum(x*x for x in q))
 # Source GLB can contain intermediary root/helper nodes with a zero
 # quaternion; glTF's default is identity. Never apply this fallback to
 # the 24 verified target skin joints, whose rest rotations are unit length.
 if length<1e-8:return [0,0,0,1]
 return [x/length for x in q]
def slerp(a,b,t):
 dot=sum(x*y for x,y in zip(a,b))
 if dot<0:b=[-x for x in b];dot=-dot
 if dot>.9995:return unit([x*(1-t)+y*t for x,y in zip(a,b)])
 th=math.acos(max(-1,min(1,dot)));sn=math.sin(th)
 return unit([(x*math.sin((1-t)*th)+y*math.sin(t*th))/sn for x,y in zip(a,b)])
def parse(path):
 raw=path.read_bytes()
 assert raw[:4]==b'glTF'
 assert struct.unpack_from('<II',raw,4)==(2,len(raw))
 n,kind=struct.unpack_from('<I4s',raw,12)
 assert kind==b'JSON'
 g=json.loads(raw[20:20+n])
 clen,ckind=struct.unpack_from('<I4s',raw,20+n)
 assert ckind==b'BIN\x00'
 return raw,g,raw[28+n:28+n+clen]
def save(g,binary):
 binary+=b'\x00'*(-len(binary)%4)
 raw=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode()
 raw+=b' '*(-len(raw)%4)
 return b'glTF'+struct.pack('<II',2,20+len(raw)+8+len(binary))+struct.pack('<I4s',len(raw),b'JSON')+raw+struct.pack('<I4s',len(binary),b'BIN\x00')+binary
# Target mercenary joint : source Quaternius joint
MAP={
 'Hips':'pelvis','Spine':'spine_01','Spine01':'spine_02','Spine02':'spine_03',
 'neck':'neck_01','Head':'Head',
 'LeftShoulder':'clavicle_l','LeftArm':'upperarm_l',
 'LeftForeArm':'lowerarm_l','LeftHand':'hand_l',
 'RightShoulder':'clavicle_r','RightArm':'upperarm_r',
 'RightForeArm':'lowerarm_r','RightHand':'hand_r',
 'LeftUpLeg':'thigh_l','LeftLeg':'calf_l','LeftFoot':'foot_l',
 'LeftToeBase':'ball_l',
 'RightUpLeg':'thigh_r','RightLeg':'calf_r','RightFoot':'foot_r',
 'RightToeBase':'ball_r'
}
def main():
 p=argparse.ArgumentParser()
 for x in ('character','source','out'):p.add_argument('--'+x,type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 traw,tar,oldbin=parse(a.character);sraw,src,sbin=parse(a.source)
 before=copy.deepcopy(tar)
 assert len(tar['skins'])==1 and len(tar['animations'])==10
 assert len(src['skins'])==1 and len(src['animations'])>=40
 ti={n.get('name'):i for i,n in enumerate(tar['nodes'])}
 si={n.get('name'):i for i,n in enumerate(src['nodes'])}
 assert all(t in ti and sn in si for t,sn in MAP.items())
 parent_t={c:i for i,n in enumerate(tar['nodes']) for c in n.get('children',[])}
 parent_s={c:i for i,n in enumerate(src['nodes']) for c in n.get('children',[])}
 def full_quat(nodes,parent,mods,i,memo):
  if i in memo:return memo[i]
  local=mods.get(i,{}).get('rotation',nodes[i].get('rotation',[0,0,0,1]))
  assert len(local)==4
  ret=unit(mul(full_quat(nodes,parent,mods,parent[i],memo),local)) if i in parent else unit(local)
  memo[i]=ret;return ret
 rest_s={i:full_quat(src['nodes'],parent_s,{},i,{}) for i in range(len(src['nodes']))}
 rest_t={i:full_quat(tar['nodes'],parent_t,{},i,{}) for i in range(len(tar['nodes']))}
 reader_cache={}
 def accessor(g,binary,ix):
  key=(id(g),ix)
  if key in reader_cache:return reader_cache[key]
  info=g['accessors'][ix];view=g['bufferViews'][info['bufferView']]
  typ=info['type'];count={'SCALAR':1,'VEC3':3,'VEC4':4}.get(typ)
  assert count and info['componentType']==5126,(info,ix)
  fmt='<'+count*'f'
  offset=view.get('byteOffset',0)+info.get('byteOffset',0)
  stride=view.get('byteStride',4*count)
  data=[struct.unpack_from(fmt,binary,offset+k*stride) for k in range(info['count'])]
  reader_cache[key]=data
  return data
 source_animations={x['name']:x for x in src['animations']}
 selected=['Sword_Idle','Sword_Attack','Walk_Loop','Jog_Fwd_Loop']
 assert all(n in source_animations for n in selected),sorted(source_animations)
 def source_tracks(name):
  anim=source_animations[name]
  out={};end=0.
  for ch in anim['channels']:
   sp=anim['samplers'][ch['sampler']]
   times=accessor(src,sbin,sp['input'])
   vals=accessor(src,sbin,sp['output'])
   interp=sp.get('interpolation','LINEAR')
   assert interp in ('LINEAR','STEP'),(name,interp)
   key=(ch['target']['node'],ch['target']['path'])
   out[key]=(times,vals,interp)
   end=max(end,times[-1][0])
  assert end>.2
  return out,end
 def interpolate(track,t,path):
  times,vals,mode=track
  if t<=times[0][0]:return list(vals[0])
  if t>=times[-1][0]:return list(vals[-1])
  left=0;right=len(times)-1
  while right-left>1:
   mid=(left+right)//2
   if times[mid][0]<=t:left=mid
   else:right=mid
  r=(t-times[left][0])/(times[right][0]-times[left][0])
  if mode=='STEP':r=0
  if path=='rotation':return slerp(vals[left],vals[right],r)
  return [x*(1-r)+y*r for x,y in zip(vals[left],vals[right])]
 def sample(name,fraction):
  tracks,length=source_tracks(name)
  t=length*fraction
  mods={}
  for (idx,path),tr in tracks.items():
   if path in ('rotation','translation','scale'):
    mods.setdefault(idx,{})[path]=interpolate(tr,t,path)
  return mods,length
 targets=[ti[n] for n in MAP]
 src_ids={ti[t]:si[s] for t,s in MAP.items()}
 depth_cache={}
 def depth(i):
  if i not in depth_cache:depth_cache[i]=1+depth(parent_t[i]) if i in parent_t else 0
  return depth_cache[i]
 targets.sort(key=depth)
 assert len(targets)==22
 # Preserve full binary prefix and all original bufferView/accessor indices.
 newdata=bytearray(oldbin)
 def new_accessor(values,shape):
  nonlocal newdata
  while len(newdata)%4:newdata.append(0)
  off=len(newdata)
  vals=[float(x) for row in values for x in row]
  newdata.extend(struct.pack('<'+'f'*len(vals),*vals))
  view=len(tar['bufferViews'])
  tar['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(vals)*4})
  ix=len(tar['accessors'])
  tar['accessors'].append({'bufferView':view,'componentType':5126,'count':len(values),'type':shape,
   'min':[min(row[k] for row in values) for k in range(len(values[0]))],
   'max':[max(row[k] for row in values) for k in range(len(values[0]))]})
  return ix
 specs=[
  ('Sword_Idle',None,'GENESIS_CC0_SWORD_IDLE_V012',60,True),
  ('Walk_Loop',None,'GENESIS_CC0_WALK_V012',45,True),
  ('Walk_Loop','Sword_Idle','GENESIS_CC0_WALK_SWORD_GUARD_V012',45,True),
  ('Sword_Attack',None,'GENESIS_CC0_SWORD_ATTACK_V012',40,False),
  ('Jog_Fwd_Loop','Sword_Idle','GENESIS_CC0_JOG_SWORD_GUARD_V012',45,True),
 ]
 clip_reports=[]
 for driver,upper,name,frames,loop in specs:
  frames=min(frames,65)
  dt=source_tracks(driver)[1]
  times=[dt*i/frames for i in range(frames+1)]
  rotations={i:[] for i in targets}
  hip_motion=[]
  # Animate only target humanoid joint rotations using actual Quaternius motions.
  for f in range(frames+1):
   phase=f/frames
   drivers,_=sample(driver,phase)
   arms,_=sample(upper,phase) if upper else (None,None)
   mods=drivers
   # Upper-body sword guard is a full Quaternius Sword_Idle pose (not
   # artificially cranked arm pivots), combined with Quaternius walk legs.
   if arms is not None:
    mods={i:dict(channels) for i,channels in drivers.items()}
    for t,s in MAP.items():
     if t in ('LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase',
              'RightUpLeg','RightLeg','RightFoot','RightToeBase','Hips'):
      continue
     src_index=si[s]
     if src_index in arms:
      mods.setdefault(src_index,{}).update(arms[src_index])
   source_world={i:full_quat(src['nodes'],parent_s,mods,i,{}) for i in src_ids.values()}
   new_world={}
   for t in targets:
    origin=src_ids[t]
    motion=mul(source_world[origin],inv(rest_s[origin]))
    target_global=unit(mul(motion,rest_t[t]))
    # Calculate local quaternion relative to retargeted parent.
    pp=parent_t.get(t)
    parent_world=new_world[pp] if pp in new_world else rest_t.get(pp,[0,0,0,1])
    local=unit(mul(inv(parent_world),target_global))
    new_world[t]=target_global
    rotations[t].append(local)
   # Hips translation: use source pelvis height changes in pelvis local
   # Y-up (after source -90deg X root), converted from meters to Meshy cm.
   p=si['pelvis']
   current=mods.get(p,{}).get('translation',src['nodes'][p].get('translation',[0,0,0]))
   rest=src['nodes'][p].get('translation',[0,0,0])
   dx=[current[i]-rest[i] for i in range(3)]
   # Source pelvis local z up; target hips glTF local y up, keep subtle only.
   hs=list(tar['nodes'][ti['Hips']].get('translation',[0,0,0]))
   hs[1]+=max(-7.0,min(7.0,dx[2]*100.))
   hip_motion.append(hs)
  tim=new_accessor([(x,) for x in times],'SCALAR')
  sampler=[];channels=[]
  for t in targets:
   data=rotations[t]
   for i in range(1,len(data)):
    if sum(x*y for x,y in zip(data[i],data[i-1]))<0:data[i]=[-x for x in data[i]]
   rid=new_accessor(data,'VEC4')
   sampler.append({'input':tim,'output':rid,'interpolation':'LINEAR'})
   channels.append({'sampler':len(sampler)-1,'target':{'node':t,'path':'rotation'}})
  hid=new_accessor(hip_motion,'VEC3')
  sampler.append({'input':tim,'output':hid,'interpolation':'LINEAR'})
  channels.append({'sampler':len(sampler)-1,'target':{'node':ti['Hips'],'path':'translation'}})
  tar['animations'].append({'name':name,'samplers':sampler,'channels':channels,
    'extras':{'origin':'Quaternius Universal Animation Library CC0',
              'source_clip':driver,'upper_body_clip':upper,
              'retarget_schema':'global_rest_relative_quaternion_v012',
              'original_source_bones':65,'target_bones':24,
              'sword_geometry_not_baked':True,'shield_geometry_not_baked':True,
              'in_place':True,'human_approved':False}})
  def qdist(a,b):
   dot=min(1,max(-1,abs(sum(x*y for x,y in zip(a,b)))))
   return math.degrees(2*math.acos(dot))
  clip_reports.append({'name':name,'source':driver,'upper_body':upper,
   'duration_sec':round(dt,3),'samples':len(times),'animated_target_rotations':len(targets),
   'right_arm_rotation_change_deg':round(max(qdist(rotations[ti['RightArm']][0],r) for r in rotations[ti['RightArm']]),2),
   'right_wrist_rotation_change_deg':round(max(qdist(rotations[ti['RightHand']][0],r) for r in rotations[ti['RightHand']]),2),
   'left_foot_rotation_change_deg':round(max(qdist(rotations[ti['LeftFoot']][0],r) for r in rotations[ti['LeftFoot']]),2),
   'seam_right_hand_deg':round(qdist(rotations[ti['RightHand']][0],rotations[ti['RightHand']][-1]),2),
   'loop_requested':loop})
 for key in ('meshes','skins','materials','textures','images','nodes'):
  assert tar.get(key)==before.get(key),(key,'original protected scene mutated')
 assert tar['animations'][:10]==before['animations']
 assert len(tar['animations'])==15
 tar['buffers'][0]['byteLength']=len(newdata)
 new_glb=save(tar,bytes(newdata))
 outpath=a.out/'mercenary_quaternius_cc0_sword_guard_v012.glb'
 outpath.write_bytes(new_glb)
 bb,check,buffer=parse(outpath)
 assert buffer.startswith(oldbin) and len(check['animations'])==15
 report={'status':'V012_CC0_RETARGET_EXPERIMENTAL_BONE_QA_PENDING',
  'original_glb_sha256':hashlib.sha256(traw).hexdigest(),
  'source_animation_glb_sha256':hashlib.sha256(sraw).hexdigest(),
  'retargeted_glb_sha256':hashlib.sha256(new_glb).hexdigest(),
  'mercenary_bones':24,'source_quaternius_bones':65,
  'original_animations':10,'new_quaternius_clips':len(specs),
  'total_animations':15,'mapped_bones':MAP,
  'clips':clip_reports,
  'mesh_skin_material_and_original_animation_bytes_unchanged':True,
  'sword_v12b_source_not_embedded':True,'shield_v016_source_not_embedded':True,
  'playcanvas_tested':False,'human_approved':False}
 (a.out/'RETARGET_QA_V012.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('GENESIS_QUATERNIUS_V012_RETARGET',json.dumps({'output_sha256':report['retargeted_glb_sha256'],
  'animations':report['total_animations'],'clips':clip_reports},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
