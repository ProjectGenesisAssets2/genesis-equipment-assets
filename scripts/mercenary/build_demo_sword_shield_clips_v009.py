#!/usr/bin/env python3
"""Project Genesis: two original-compatible, in-place sword/shield animation clips.

Rig is Meshy source with native right/left child-of-hand joint sockets. This does
NOT pretend an approved shield has been mounted; it prepares the left-hand hold.
Existing 10 clips, skins, meshes, materials, normals and texture buffers are
preserved. All new arm/leg poses are quaternion-based on the actual Idle_02 rig.
"""
import argparse,copy,hashlib,json,math,struct
from pathlib import Path

def parse(data):
    assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2
    jlen,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
    scene=json.loads(data[20:20+jlen]);pos=20+jlen
    blen,typ=struct.unpack_from('<I4s',data,pos);assert typ==b'BIN\x00'
    return scene,data[pos+8:pos+8+blen]
def pack(scene,binary):
    data=json.dumps(scene,ensure_ascii=False,separators=(',',':')).encode('utf8')
    data+=b' '*((-len(data))%4)
    binary+=b'\x00'*((-len(binary))%4)
    return b'glTF'+struct.pack('<II',2,20+len(data)+8+len(binary))+struct.pack('<I4s',len(data),b'JSON')+data+struct.pack('<I4s',len(binary),b'BIN\x00')+binary
def qmul(a,b):
    x,y,z,w=a;X,Y,Z,W=b
    return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def qinv(q):return [-q[0],-q[1],-q[2],q[3]]
def qnorm(q):
    m=math.sqrt(sum(v*v for v in q))
    return [v/m for v in q]
def qaxis(axis,angle):
    v=math.sin(math.radians(angle)/2.)
    return [axis[0]*v,axis[1]*v,axis[2]*v,math.cos(math.radians(angle)/2.)]
def qslerp(a,b,t):
    dot=sum(x*y for x,y in zip(a,b))
    if dot<0:b=[-v for v in b];dot=-dot
    if dot>.9995:return qnorm([(1-t)*x+t*y for x,y in zip(a,b)])
    angle=math.acos(max(-1.,min(1.,dot)))
    x=math.sin((1-t)*angle)/math.sin(angle);y=math.sin(t*angle)/math.sin(angle)
    return qnorm([x*p+y*q for p,q in zip(a,b)])
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    original=a.source.read_bytes();g,body=parse(original);before=copy.deepcopy(g)
    assert len(g['skins'])==1 and len(g['animations'])==10
    names={n.get('name'):i for i,n in enumerate(g['nodes'])}
    parents={child:i for i,n in enumerate(g['nodes']) for child in n.get('children',[])}
    required=['Hips','Spine','Head','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand',
              'LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot']
    assert all(n in names for n in required)
    assert names['GENESIS_SOCKET_WEAPON_R'] in g['nodes'][names['RightHand']].get('children',[])
    assert names['GENESIS_SOCKET_SHIELD_L'] in g['nodes'][names['LeftHand']].get('children',[])
    cache={}
    def accessor(idx):
        if idx in cache:return cache[idx]
        c=g['accessors'][idx];v=g['bufferViews'][c['bufferView']]
        num={'SCALAR':1,'VEC3':3,'VEC4':4}[c['type']]
        assert c['componentType']==5126
        format='<'+num*'f';step=v.get('byteStride',struct.calcsize(format))
        offset=v.get('byteOffset',0)+c.get('byteOffset',0)
        ret=[struct.unpack_from(format,body,offset+i*step) for i in range(c['count'])]
        cache[idx]=ret;return ret
    source=next(x for x in g['animations'] if x['name']=='Idle_02')
    duration=max(accessor(s['input'])[-1][0] for s in source['samplers'])
    assert 1.<duration<3.
    source_tracks={}
    for ch in source['channels']:
        sampler=source['samplers'][ch['sampler']]
        source_tracks[(ch['target']['node'],ch['target']['path'])]=(
            accessor(sampler['input']),accessor(sampler['output']),sampler.get('interpolation','LINEAR'))
    def sample_track(times,values,interpolation,t,path):
        if t<=times[0][0]:return list(values[0])
        if t>=times[-1][0]:return list(values[-1])
        lo=0;hi=len(times)-1
        while hi-lo>1:
            mi=(lo+hi)//2
            if times[mi][0]<=t:lo=mi
            else:hi=mi
        if interpolation=='STEP':return list(values[lo])
        k=(t-times[lo][0])/(times[hi][0]-times[lo][0])
        if path=='rotation':return qslerp(list(values[lo]),list(values[hi]),k)
        return [(1-k)*a+k*b for a,b in zip(values[lo],values[hi])]
    def base_pose(t):
        return {i:{path:sample_track(*track,t,path) for (n,path),track in source_tracks.items() if n==i}
                for i in set(n for n,_ in source_tracks)}
    def world_quat(i,pose,memo):
        if i in memo:return memo[i]
        q=pose.get(i,{}).get('rotation',g['nodes'][i].get('rotation',[0,0,0,1]))
        v=qmul(world_quat(parents[i],pose,memo),q) if i in parents else list(q)
        memo[i]=qnorm(v)
        return memo[i]
    def world_delta(name,pose,angles):
        """Actual world-axis rotation remapped through animated parent orientation."""
        i=names[name];memo={}
        parent_q=world_quat(parents[i],pose,memo) if i in parents else [0,0,0,1]
        delta=[0,0,0,1]
        for axis,degree in angles:
            delta=qmul(qaxis(axis,degree),delta)
        local=qmul(qmul(qinv(parent_q),delta),parent_q)
        old=pose[i]['rotation']
        pose[i]['rotation']=qnorm(qmul(local,old))
    def clip_values(mode,t):
        if mode=='idle':
            src_t=duration*(t/2.0)
            phase=2*math.pi*t/2.0
        else:
            src_t=duration*(t/1.20)
            phase=2*math.pi*t/1.20
        pose=base_pose(src_t)
        # Natural asymmetric sword low guard, shield forearm raised across the
        # body in front. Both hands remain driven by their real skeletal bones.
        world_delta('LeftArm',pose,[((1,0,0),-42.),((0,0,1),-8.)])
        world_delta('LeftForeArm',pose,[((1,0,0),-6.),((0,1,0),-31.),((0,0,1),-16.)])
        world_delta('LeftHand',pose,[((1,0,0),13.),((0,1,0),5.)])
        world_delta('RightArm',pose,[((1,0,0),4.),((0,0,1),-3.)])
        world_delta('RightForeArm',pose,[((1,0,0),3.)])
        # Small, restrained wrist turn; avoid forcing an anatomically reversed
        # glove. A definitive finger-curled hand needs new weighted finger bones.
        world_delta('RightHand',pose,[((0,1,0),-12.)])
        if mode=='idle':
            breathe=math.sin(phase)
            world_delta('Spine',pose,[((1,0,0),.85*breathe)])
            world_delta('Head',pose,[((0,1,0),1.2*math.sin(phase+.8))])
        else:
            swing=math.sin(phase);slow=math.sin(phase*2)
            l=20.*swing;r=-20.*swing
            lf=-24.*max(0.,swing)**2
            rf=-24.*max(0.,-swing)**2
            world_delta('LeftUpLeg',pose,[((1,0,0),l)])
            world_delta('RightUpLeg',pose,[((1,0,0),r)])
            world_delta('LeftLeg',pose,[((1,0,0),lf)])
            world_delta('RightLeg',pose,[((1,0,0),rf)])
            world_delta('LeftFoot',pose,[((1,0,0),-l-lf)])
            world_delta('RightFoot',pose,[((1,0,0),-r-rf)])
            world_delta('Spine',pose,[((1,0,0),2.2),((0,0,1),1.4*slow)])
            world_delta('Head',pose,[((1,0,0),-1.6)])
            world_delta('LeftArm',pose,[((1,0,0),2.*swing)])
            world_delta('RightArm',pose,[((1,0,0),-3.*swing)])
            hips=pose[names['Hips']]['translation'].copy()
            hips[1]+=1.7*(1.-math.cos(phase*2.))/2.
            hips[0]+=.6*math.sin(phase)
            pose[names['Hips']]['translation']=hips
        return pose
    # Append all new floating-point times/quaternions to the existing binary.
    # Legacy buffer views and binary prefix remain bit-exact.
    output=bytearray(body)
    def buffer_view(rows,kind):
        nonlocal output
        off=len(output)
        while off%4:output.append(0);off+=1
        flat=[float(v) for row in rows for v in row]
        output.extend(struct.pack('<'+'f'*len(flat),*flat))
        length=len(flat)*4
        view=len(g['bufferViews'])
        g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':length})
        index=len(g['accessors'])
        g['accessors'].append({'bufferView':view,'byteOffset':0,'componentType':5126,
                              'count':len(rows),'type':kind,
                              'min':[min(row[i] for row in rows) for i in range(len(rows[0]))],
                              'max':[max(row[i] for row in rows) for i in range(len(rows[0]))]})
        return index
    output_clips=[]
    original_targets=sorted(source_tracks)
    for mode,name,length,steps in [
        ('idle','GENESIS_SWORD_SHIELD_IDLE_V009',2.0,40),
        ('walk','GENESIS_SWORD_SHIELD_WALK_V009',1.20,36)]:
        times=[length*i/steps for i in range(steps+1)]
        poses=[clip_values(mode,t) for t in times]
        # Continuous loop: same pose at first and last frame.
        for (bone,path) in original_targets:
            if path in ('translation','rotation','scale'):
                assert all(len(pose[bone][path])==(4 if path=='rotation' else 3) for pose in poses)
        assert len(original_targets)==72
        time_accessor=buffer_view([(t,) for t in times],'SCALAR')
        samplers=[];channels=[]
        for (bone,path) in original_targets:
            rows=[p[bone][path] for p in poses]
            if path=='rotation':
                for j in range(1,len(rows)):
                    if sum(x*y for x,y in zip(rows[j-1],rows[j]))<0:rows[j]=[-x for x in rows[j]]
            ix=buffer_view(rows,'VEC4' if path=='rotation' else 'VEC3')
            samplers.append({'input':time_accessor,'output':ix,'interpolation':'LINEAR'})
            channels.append({'sampler':len(samplers)-1,'target':{'node':bone,'path':path}})
        g['animations'].append({'name':name,'samplers':samplers,'channels':channels,
                                'extras':{'genesis_demo':True,'in_place':True,
                                          'equipment_profile':'sword_shield',
                                          'shield_original_asset_not_baked':True,
                                          'source_idle_animation':'Idle_02'}})
        output_clips.append({'name':name,'duration_sec':length,'frames':len(times),
                             'channels':len(channels),'in_place':True})
    assert g['animations'][:10]==before['animations']
    for k in ['meshes','materials','textures','images','skins']:
        assert g.get(k)==before.get(k),(k,'protected source changed')
    assert len(g['animations'])==12
    g['buffers'][0]['byteLength']=len(output)
    dest=a.out/'mercenary_sword_shield_idle_walk_v009.glb'
    result=pack(g,bytes(output));dest.write_bytes(result)
    test,bb=parse(result)
    assert bb.startswith(body)
    assert len(test['animations'])==12 and test['animations'][:10]==before['animations']
    assert test['buffers'][0]['byteLength']==len(output)
    report={'status':'V009_REFINED_SHIELD_GUARD_ANIMATION_PROTOTYPE',
            'source_sha256':hashlib.sha256(original).hexdigest(),
            'output_sha256':hashlib.sha256(result).hexdigest(),
            'original_animation_count':10,'new_animation_count':2,
            'total_animation_count':12,'new_clips':output_clips,
            'mesh_skin_material_texture_data_unchanged':True,
            'finger_bones_added':False,
            'shield_arm_forward_guard_pivot_degrees':{'upper_arm_x':-42,'upper_arm_z':-8,'forearm_x':-6,'forearm_y':-31,'forearm_z':-16},
            'shield_asset_baked_or_replaced':False,
            'in_place_walk_not_yet_tested_in_playcanvas':True,
            'human_visual_approved':False}
    (a.out/'demo_sword_shield_poses_v009.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_DEMO_V009',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
