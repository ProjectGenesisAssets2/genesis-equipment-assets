#!/usr/bin/env python3
"""Check glTF socket inheritance in ALL source animation clips (native glTF units).
Independent of Blender's bone-parent Empty reimport offset bug.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path

def qrot(q,v):
 x,y,z,w=q
 t=(2*(y*v[2]-z*v[1]),2*(z*v[0]-x*v[2]),2*(x*v[1]-y*v[0]))
 return (v[0]+w*t[0]+y*t[2]-z*t[1],v[1]+w*t[1]+z*t[0]-x*t[2],v[2]+w*t[2]+x*t[1]-y*t[0])
def qmul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rig',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
 args=ap.parse_args();raw=args.rig.read_bytes()
 length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);bin=raw[28+length:]
 nodes=g['nodes'];parents={ch:i for i,node in enumerate(nodes) for ch in node.get('children',[])}
 names={node.get('name'):i for i,node in enumerate(nodes)}
 pairs=(('RightHand','GENESIS_SOCKET_WEAPON_R'),('LeftHand','GENESIS_SOCKET_SHIELD_L'))
 for bone,socket in pairs:assert parents[names[socket]]==names[bone],(bone,socket)
 access_cache={}
 def accessor(index):
  if index in access_cache:return access_cache[index]
  a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
  stride_n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
  code={5126:'f',5123:'H'}[a['componentType']]
  fmt='<'+code*stride_n
  off=v.get('byteOffset',0)+a.get('byteOffset',0)
  stride=v.get('byteStride',struct.calcsize(fmt))
  res=[struct.unpack_from(fmt,bin,off+i*stride) for i in range(a['count'])]
  access_cache[index]=res
  return res
 def world(i,overrides,memo):
  if i in memo:return memo[i]
  o=nodes[i];mods=overrides.get(i,{})
  tr=mods.get('translation',o.get('translation',[0,0,0]))
  rot=mods.get('rotation',o.get('rotation',[0,0,0,1]))
  scl=mods.get('scale',o.get('scale',[1,1,1]))
  if i in parents:
   pp,pq,ps=world(parents[i],overrides,memo)
   v=qrot(pq,[ps[k]*tr[k] for k in range(3)])
   value=tuple(pp[k]+v[k] for k in range(3)),qmul(pq,rot),tuple(ps[k]*scl[k] for k in range(3))
  else:value=tuple(tr),tuple(rot),tuple(scl)
  memo[i]=value;return value
 clips=[]
 for animation in g['animations']:
  samp=animation['samplers'];end=max(accessor(s['input'])[-1][0] for s in samp)
  snapshots=[]
  for t in (0,end/3,end*2/3,end):
   changes={}
   for ch in animation['channels']:
    sampler=samp[ch['sampler']];times=accessor(sampler['input']);values=accessor(sampler['output'])
    at=min(range(len(times)),key=lambda k:abs(times[k][0]-t))
    changes.setdefault(ch['target']['node'],{})[ch['target']['path']]=values[at]
   memo={};points={}
   for bone,socket in pairs:
    p=world(names[bone],changes,memo)[0];q=world(names[socket],changes,memo)[0]
    distance=math.dist(p,q)
    assert abs(distance-.06)<.0002,(animation['name'],bone,t,distance)
    points[bone]=list(round(x,5) for x in p)
    points[socket]=list(round(x,5) for x in q)
   snapshots.append(points)
  dr=max(math.dist(snapshots[0]['GENESIS_SOCKET_WEAPON_R'],p['GENESIS_SOCKET_WEAPON_R']) for p in snapshots[1:])
  dl=max(math.dist(snapshots[0]['GENESIS_SOCKET_SHIELD_L'],p['GENESIS_SOCKET_SHIELD_L']) for p in snapshots[1:])
  clips.append({'clip':animation['name'],'duration_sec':round(end,3),
   'right_socket_motion_m':round(dr,4),'left_socket_motion_m':round(dl,4),
   'all_four_samples_follow_bones_exactly':True})
 assert len(clips)==10
 assert sum(c['right_socket_motion_m']>.03 or c['left_socket_motion_m']>.03 for c in clips)>=5
 report={'status':'PASS_ALL_TEN_ANIMATED_SOCKETS','rig_sha256':hashlib.sha256(raw).hexdigest(),
  'animations':clips,'right_joint':'RightHand','left_joint':'LeftHand','offset_m':.06,
  'all_clips_follow_skeletal_joints':True,'game_playcanvas_not_yet_tested':True}
 args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print('ANIMATED_SOCKET_VALIDATION_PASS',json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
