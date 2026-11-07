#!/usr/bin/env python3
"""Project Genesis V037: non-destructive real RIGHT glove arc bending experiment.

Unlike V031/V035's pointwise sin projection, this bends the finger strip and
its transverse thickness together around a virtual knuckle arc. RightHand only.
No bone, animation, UV, skin weight, material, shield, or socket modifications.
Requires actual Blender Cycles review before any use in game.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--variant',choices=['A','B'],required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
params={'A':{'pivot_x':-.715,'pivot_y':1.47,'radius':.045},
        'B':{'pivot_x':-.72,'pivot_y':1.47,'radius':.055}}[a.variant]
raw=a.source.read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
jlen,jt=struct.unpack_from('<I4s',raw,12);assert jt==b'JSON'
g=json.loads(raw[20:20+jlen])
blen,bt=struct.unpack_from('<I4s',raw,20+jlen);assert bt==b'BIN\0'
bin_start=28+jlen
data=bytearray(raw[bin_start:bin_start+blen])
nodes={v.get('name'):i for i,v in enumerate(g['nodes'])}
right=nodes['RightHand'];left=nodes['LeftHand']
joints=g['skins'][0]['joints'];rindex=joints.index(right);lindex=joints.index(left)
assert len(joints)==24 and len(g['animations'])==5
assert nodes['GENESIS_SOCKET_WEAPON_R'] in g['nodes'][right]['children']
assert nodes['GENESIS_SOCKET_SHIELD_L'] in g['nodes'][left]['children']
attrs=g['meshes'][0]['primitives'][0]['attributes']

def accessor(ix):
    ac=g['accessors'][ix];view=g['bufferViews'][ac['bufferView']]
    k={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']]
    typ={5121:'B',5123:'H',5125:'I',5126:'f'}[ac['componentType']]
    fmt='<'+typ*k;span=struct.calcsize(fmt)
    off=view.get('byteOffset',0)+ac.get('byteOffset',0)
    stride=view.get('byteStride',span)
    return [(off+i*stride,struct.unpack_from(fmt,data,off+i*stride)) for i in range(ac['count'])]
P=accessor(attrs['POSITION']);N=accessor(attrs['NORMAL'])
J=accessor(attrs['JOINTS_0']);W=accessor(attrs['WEIGHTS_0'])
T=accessor(g['meshes'][0]['primitives'][0]['indices'])
assert len(P)==len(N)==len(J)==len(W)
assert len(T)%3==0
right_weights=[];left_weights=[]
for (_,js),(_,ws) in zip(J,W):
    right_weights.append(sum(float(w) for j,w in zip(js,ws) if j==rindex))
    left_weights.append(sum(float(w) for j,w in zip(js,ws) if j==lindex))
original=[xyz for _,xyz in P]
edited=list(original)
affected=set()
max_shift=0.
def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)
for i,((off,xyz),(no,nrm)) in enumerate(zip(P,N)):
    x,y,z=map(float,xyz)
    wr=right_weights[i];wl=left_weights[i]
    if wl>.5 or wr<=.48 or x>=params['pivot_x'] or x>0:continue
    d=max(0.,params['pivot_x']-x)
    theta=min(1.8,d/params['radius'])
    f=smooth(d/.018)*smooth((wr-.48)/.45)*(1-smooth((z-.080)/.032))
    if f<.002:continue
    offset=y-params['pivot_y']
    newx=params['pivot_x']-(params['radius']+offset)*math.sin(theta)
    newy=params['pivot_y']-params['radius']*(1-math.cos(theta))+offset*math.cos(theta)
    pos=[x+f*(newx-x),y+f*(newy-y),z]
    shift=math.dist(pos,xyz)
    max_shift=max(max_shift,shift)
    if shift<.00001:continue
    struct.pack_into('<fff',data,off,*pos)
    edited[i]=pos
    normal_turn=theta*f;cx=math.cos(normal_turn);sx=math.sin(normal_turn)
    nx,ny,nz=map(float,nrm)
    corrected=(cx*nx-sx*ny,sx*nx+cx*ny,nz)
    magnitude=math.sqrt(sum(v*v for v in corrected))
    struct.pack_into('<fff',data,no,*(v/magnitude for v in corrected))
    affected.add(i)

def face(v):
    a0,b0,c0=v
    u=[b0[k]-a0[k] for k in range(3)]
    w=[c0[k]-a0[k] for k in range(3)]
    return (u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0])
flipped=collapsed=expanded=analyzed=0
for i in range(0,len(T),3):
    ids=[int(T[i+j][1][0]) for j in range(3)]
    if not any(right_weights[j]>.5 for j in ids):continue
    old=[original[j] for j in ids];new=[edited[j] for j in ids]
    fa=face(old);fb=face(new)
    a0=math.sqrt(sum(v*v for v in fa));b0=math.sqrt(sum(v*v for v in fb))
    if a0<1e-10:continue
    analyzed+=1
    if sum(x*y for x,y in zip(fa,fb))<0:flipped+=1
    ratio=b0/a0
    if ratio<.2:collapsed+=1
    if ratio>5:expanded+=1
assert 190<len(affected)<280,('unexpected changed vertex count',len(affected))
assert flipped==0 and collapsed==0 and expanded==0,('mesh topology folded',flipped,collapsed,expanded)
assert max_shift<.065,('excessive deformation',max_shift)
out=raw[:bin_start]+bytes(data)+raw[bin_start+blen:]
assert len(out)==len(raw)
dst=a.out/f'mercenary_arc_fingers_{a.variant}_v037.glb';dst.write_bytes(out)
report={'status':'V037_EXPERIMENTAL_ARC_FINGER_CURVATURE_VISUAL_QA_REQUIRED',
  'source_sha256':hashlib.sha256(raw).hexdigest(),
  'output_sha256':hashlib.sha256(out).hexdigest(),
  'variant':a.variant,'radius_m':params['radius'],'pivot_x_m':params['pivot_x'],
  'pivot_y_m':params['pivot_y'],'right_hand_edited_vertices':len(affected),
  'max_vertex_displacement_m':round(max_shift,5),
  'original_triangle_count_near_hand':analyzed,'flipped_triangles':flipped,
  'collapsed_triangles':collapsed,'excessive_area_triangles':expanded,
  'right_bone':'RightHand','right_socket':'GENESIS_SOCKET_WEAPON_R',
  'left_bone':'LeftHand','left_socket':'GENESIS_SOCKET_SHIELD_L',
  'rig_bones':24,'animations':5,'left_hand_untouched':True,
  'materials_UV_skin_animations_original_unchanged':True,
  'source_asset_unchanged':True,'approved':False,'game_tested':False}
(a.out/f'MERCENARY_ARC_FINGERS_{a.variant}_V037_QA.json').write_text(json.dumps(report,indent=2))
print('V037_ARC_BEND_STATIC_TOPOLOGY_PASS',json.dumps(report),flush=True)
