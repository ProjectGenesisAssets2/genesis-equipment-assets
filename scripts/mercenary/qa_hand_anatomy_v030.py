#!/usr/bin/env python3
"""Genesis mercenary: refuse accidental left/right swaps and wrong glTF sockets.

For V029 original imported Meshy rig with 24 named bones and 2 child sockets.
This is static anatomy QA, NOT a grip-approved or visual-quality certificate.
Pure Python standard library; never modifies its input asset.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path

COMP={5121:'B',5123:'H',5125:'I',5126:'f'}
SIZE={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def vec3(x):return [round(float(v),5) for v in x]
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def matmul(a,b):
 return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def transform(n):
 t=n.get('translation',[0,0,0]);x,y,z,w=n.get('rotation',[0,0,0,1]);sx,sy,sz=n.get('scale',[1,1,1])
 r=[
 [(1-2*(y*y+z*z))*sx,2*(x*y-z*w)*sy,2*(x*z+y*w)*sz,t[0]],
 [2*(x*y+z*w)*sx,(1-2*(x*x+z*z))*sy,2*(y*z-x*w)*sz,t[1]],
 [2*(x*z-y*w)*sx,2*(y*z+x*w)*sy,(1-2*(x*x+y*y))*sz,t[2]],
 [0,0,0,1]]
 return r
def sample_acc(g,buffer,ix):
 a=g['accessors'][ix];v=g['bufferViews'][a['bufferView']]
 dims=SIZE[a['type']];typ=COMP[a['componentType']];width=struct.calcsize('<'+typ)*dims
 offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width)
 fmt='<'+typ*dims
 return [struct.unpack_from(fmt,buffer,offset+stride*i) for i in range(a['count'])]

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--character',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();raw=a.character.read_bytes()
 assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
 jlen,typ=struct.unpack_from('<I4s',raw,12);assert typ==b'JSON'
 g=json.loads(raw[20:20+jlen]);zlen,typ=struct.unpack_from('<I4s',raw,20+jlen);assert typ==b'BIN\0'
 buffer=raw[28+jlen:28+jlen+zlen]
 names={v.get('name'):i for i,v in enumerate(g['nodes'])}
 bones=g['skins'][0]['joints'];bone_names={g['nodes'][i].get('name','') for i in bones}
 right=names['RightHand'];left=names['LeftHand']
 r_socket=names['GENESIS_SOCKET_WEAPON_R'];l_socket=names['GENESIS_SOCKET_SHIELD_L']
 assert len(g['skins'])==1 and len(bones)==24
 assert right in bones and left in bones
 assert r_socket in g['nodes'][right].get('children',[]), 'CRITICAL: sword socket not on RightHand'
 assert l_socket in g['nodes'][left].get('children',[]), 'CRITICAL: shield socket not on LeftHand'
 assert r_socket not in g['nodes'][left].get('children',[]), 'CRITICAL: right and left swapped'
 assert l_socket not in g['nodes'][right].get('children',[]), 'CRITICAL: right and left swapped'
 parent={child:i for i,node in enumerate(g['nodes']) for child in node.get('children',[])}
 cache={}
 def world(i):
  if i in cache:return cache[i]
  m=transform(g['nodes'][i])
  if i in parent:m=matmul(world(parent[i]),m)
  cache[i]=m;return m
 def origin(i):return [world(i)[j][3] for j in range(3)]
 rw=origin(right);lw=origin(left);rs=origin(r_socket);ls=origin(l_socket)
 assert rw[0]<0 and lw[0]>0, ('RightHand/LeftHand rest pose crossed X axis',rw,lw)
 assert rs[0]<0 and ls[0]>0, ('weapon/shield socket crossed wrong side',rs,ls)
 attrs=g['meshes'][0]['primitives'][0]['attributes']
 position=sample_acc(g,buffer,attrs['POSITION'])
 joints=sample_acc(g,buffer,attrs['JOINTS_0'])
 weights=sample_acc(g,buffer,attrs['WEIGHTS_0'])
 def palm_center(node):
  j=bones.index(node);total=0.;xyz=[0.,0.,0.];selected=0
  for pos,indices,ws in zip(position,joints,weights):
   w=sum(weight for index,weight in zip(indices,ws) if index==j)
   if w<=.5:continue
   selected+=1;total+=w
   for k in range(3):xyz[k]+=pos[k]*w
  assert total>5 and selected>=100,(node,'no skinned glove/hand geometry')
  return [v/total for v in xyz],selected
 rc,rverts=palm_center(right);lc,lverts=palm_center(left)
 assert rc[0]<0 and lc[0]>0, ('glove mesh groups swapped',rc,lc)
 assert abs(abs(rc[0])-abs(lc[0]))<.03,('palms not symmetric in source',rc,lc)
 # Mesh POSITION is in meters; skeleton world is in meters even though the
 # Armature root carries a 0.01 Meshy normalization scale.
 r_offset=dist(rc,rs);l_offset=dist(lc,ls)
 if r_offset>.085 or l_offset>.085:
  raise AssertionError(('socket outside hand region',r_offset,l_offset))
 finger_bones=sorted(x for x in bone_names if any(w in x.lower() for w in ('finger','thumb','index','middle','ring','pinky')))
 # This is a detection, not a policy requiring individually rigged fingers.
 assert len(finger_bones)==0,'Expected historic 24-bone rig, inspect before proceeding'
 action_names=[v['name'] for v in g.get('animations',[])]
 assert len(action_names)==5 and all('ATTACK' not in n and 'BLOCK' not in n for n in action_names)
 report={
  'status':'V030_HANDEDNESS_GEOMETRY_AUDITED_NOT_GRIP_APPROVED',
  'input':a.character.name,
  'sha256':hashlib.sha256(raw).hexdigest(),
  'rest_hand_world_m':{'RightHand':vec3(rw),'LeftHand':vec3(lw)},
  'native_socket_world_m':{'GENESIS_SOCKET_WEAPON_R':vec3(rs),'GENESIS_SOCKET_SHIELD_L':vec3(ls)},
  'hand_skinned_geometry_center_m':{'RightHand':vec3(rc),'LeftHand':vec3(lc)},
  'skinned_hand_vertex_count':{'RightHand':rverts,'LeftHand':lverts},
  'socket_to_hand_geometry_center_m':{'RightHand':round(r_offset,5),'LeftHand':round(l_offset,5)},
  'mapping_verified':{'RightHand_right_of_actor':rw[0]<0,
   'LeftHand_left_of_actor':lw[0]>0,
   'Sword_socket_parent_RightHand':True,'Shield_socket_parent_LeftHand':True},
  'finger_bones':finger_bones,
  'critical_limitation':'Fingers are part of skinned hand geometry but have no individual deformation bones; a wrist or socket rotation cannot close/reverse individual fingers.',
  'diagnosis_needed':'Real Cycles closeups from front/back and knuckles; sword hilt/hand orientation contact and wrist angles to be checked before any V030 pose revision.',
  'action_names':action_names,
  'asset_models_changed':False,'animations_changed':False,
  'playcanvas_tested':False,'grip_visual_approved':False,'human_approved':False,
 }
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('GENESIS_HAND_ANATOMY_AUDIT_PASS',json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
