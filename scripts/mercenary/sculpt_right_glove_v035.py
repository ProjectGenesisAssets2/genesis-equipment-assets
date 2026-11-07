#!/usr/bin/env python3
"""Experiment V035: curl actual anatomical RightHand glove geometry only.
Preserve approved sources, exact LEFT hand, glTF rig, sockets, clips, UV and PBR.
Not a new model; must pass real Cycles 32-bit close-up QA, not auto-approved.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--angle',type=float,default=3.10)
p.add_argument('--pivot',type=float,required=True)
p.add_argument('--radius',type=float,required=True)
p.add_argument('--label',choices=('A','B','C'),required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
raw=a.source.read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
jl,jt=struct.unpack_from('<I4s',raw,12);assert jt==b'JSON'
g=json.loads(raw[20:20+jl]);bl,bt=struct.unpack_from('<I4s',raw,20+jl);assert bt==b'BIN\0'
begin=28+jl;bin=bytearray(raw[begin:begin+bl]);assert len(bin)==g['buffers'][0]['byteLength']
nodes={v.get('name'):i for i,v in enumerate(g['nodes'])};bones=g['skins'][0]['joints']
assert len(g['skins'])==1 and len(bones)==24 and len(g['animations'])==5
right=nodes['RightHand'];left=nodes['LeftHand']
assert right in bones and left in bones
assert nodes['GENESIS_SOCKET_WEAPON_R'] in g['nodes'][right]['children']
assert nodes['GENESIS_SOCKET_SHIELD_L'] in g['nodes'][left]['children']
rid= bones.index(right);lid=bones.index(left)
attrs=g['meshes'][0]['primitives'][0]['attributes']
def acc(index):
 ac=g['accessors'][index];v=g['bufferViews'][ac['bufferView']]
 fmt={5126:'f',5123:'H',5121:'B'}[ac['componentType']]
 count={'VEC3':3,'VEC4':4}[ac['type']]
 width=struct.calcsize('<'+fmt*count)
 start=v.get('byteOffset',0)+ac.get('byteOffset',0);stride=v.get('byteStride',width)
 return [(start+i*stride,struct.unpack_from('<'+fmt*count,bin,start+i*stride)) for i in range(ac['count'])]
P=acc(attrs['POSITION']);N=acc(attrs['NORMAL']);J=acc(attrs['JOINTS_0']);W=acc(attrs['WEIGHTS_0'])
assert len(P)==len(N)==len(J)==len(W)
changed=0;strong=0;max_d=0.;left_vertices=0
pivot=a.pivot;radius=a.radius
for ((po,xyz),(no,norm),(jo,ids),(wo,weights)) in zip(P,N,J,W):
 wr=sum(float(w) for ix,w in zip(ids,weights) if ix==rid)
 wl=sum(float(w) for ix,w in zip(ids,weights) if ix==lid)
 if wl>.5:
  left_vertices+=1;continue
 x,y,z=map(float,xyz)
 if wr<.55 or x>=pivot or x>=0:continue
 influence=max(0.,min(1.,(pivot-x)/.014))
 influence=influence*influence*(3.-2.*influence)
 influence*=max(0.,min(1.,(.110-z)/.030))
 influence*=max(0.,min(1.,(wr-.55)/.30))
 if influence<.002:continue
 theta=min(a.angle,(pivot-x)/radius)
 xc=pivot-radius*math.sin(theta)
 yc=y-radius*(1-math.cos(theta))
 dest=(x+influence*(xc-x),y+influence*(yc-y),z)
 assert dest[0]<-.64,'anatomical right side crossed'
 struct.pack_into('<fff',bin,po,*dest)
 nx,ny,nz=map(float,norm);q=theta*influence
 rotated=(math.cos(q)*nx-math.sin(q)*ny, math.sin(q)*nx+math.cos(q)*ny,nz)
 norm_factor=math.sqrt(sum(t*t for t in rotated))
 struct.pack_into('<fff',bin,no,*(t/norm_factor for t in rotated))
 d=math.sqrt(sum((u-v)**2 for u,v in zip(xyz,dest)))
 max_d=max(max_d,d);changed+=1;strong+=influence>.6
assert 80<changed<600,(changed,'invalid glove edit')
assert left_vertices>=500 and max_d<.080
out=raw[:begin]+bytes(bin)+raw[begin+bl:]
path=a.out/f'mercenary_grip_{a.label}_v035.glb';path.write_bytes(out)
report={'status':'V035_EXPERIMENTAL_NEEDS_VISUAL_REVIEW','source_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashlib.sha256(out).hexdigest(),'right_grip_vertices_edited':changed,
 'strongly_curled_vertices':strong,'max_position_change_m':round(max_d,6),
 'anatomical_right_hand_joint':right,'anatomical_left_hand_joint':left,
 'right_weapon_socket':'GENESIS_SOCKET_WEAPON_R','left_shield_socket':'GENESIS_SOCKET_SHIELD_L',
 'curl_radians':a.angle,'curl_pivot_x_m':a.pivot,'curl_radius_m':a.radius,'candidate_label':a.label,'left_hand_and_rig_unchanged':True,
 'geometry_edit':'Comparative anatomical right-hand fingertip curvature; no skin/bones/socket editing',
 'playcanvas_tested':False,'human_approved':False}
(a.out/f'MERCENARY_GRIP_{a.label}_V035_QA.json').write_text(json.dumps(report,indent=2))
print('V035_GLOVE_SCULPT_QA',json.dumps(report),flush=True)
