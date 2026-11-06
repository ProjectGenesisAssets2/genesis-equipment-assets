#!/usr/bin/env python3
"""Audit native glTF skeleton and CC0 Quaternius 120+ clips before retarget.

No guessing about rig compatibility, skeleton handedness or clip selection.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path
def parse(path):
 data=path.read_bytes()
 assert data[:4]==b'glTF' and struct.unpack_from('<I',data,4)[0]==2
 length,tag=struct.unpack_from('<I4s',data,12)
 assert tag==b'JSON'
 g=json.loads(data[20:20+length])
 return data,g
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--character',type=Path,required=True)
 ap.add_argument('--source',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args()
 a.out.parent.mkdir(parents=True,exist_ok=True)
 b,c=parse(a.character);s,d=parse(a.source)
 def inspect(g):
  names=[(i,n.get('name','')) for i,n in enumerate(g['nodes'])]
  joints=sorted({i for skin in g.get('skins',[]) for i in skin['joints']})
  animations=[]
  for anim in g.get('animations',[]):
   targets=[(g['nodes'][x['target']['node']].get('name',''),x['target']['path']) for x in anim.get('channels',[])]
   animations.append({'name':anim.get('name',''),'channels':len(targets),'rotation_channels':sum(path=='rotation' for _,path in targets),
                      'target_bones':[name for name,path in targets if path=='rotation'][:50]})
  return {'nodes':len(names),'mesh_count':len(g.get('meshes',[])),
   'skin_joint_count':len(joints),'skins':len(g.get('skins',[])),
   'joints':[{'id':i,'name':g['nodes'][i].get('name'),'rotation':g['nodes'][i].get('rotation',[0,0,0,1]),
              'translation':g['nodes'][i].get('translation',[0,0,0]),
              'scale':g['nodes'][i].get('scale',[1,1,1])} for i in joints],
   'animations_total':len(animations),
   'relevant_clips':[entry for entry in animations if any(t in entry['name'].lower() for t in
                    ('sword','shield','walk','jog','idle','fight','run','block','guard','slash','attack'))],
   'animation_name_index':[x['name'] for x in animations],
   'scene_root_ids':g.get('scenes',[{}])[g.get('scene',0)].get('nodes',[]) if g.get('scenes') else [],
   'all_named_nodes':names[:145]}
 person=inspect(c);source=inspect(d)
 # Cross skeleton structural checks must drive retarget mapping.
 cross=set(x['name'] for x in person['joints']) & set(x['name'] for x in source['joints'])
 out={'status':'V012_CC0_SOURCE_AND_RETARGET_AUDIT_ONLY',
      'mercenary_sha256':hashlib.sha256(b).hexdigest(),
      'cc0_quaternius_sha256':hashlib.sha256(s).hexdigest(),
      'cc0_source':'Quaternius Universal Animation Library CC0, derived audit source via Seyamalam/blood-league-kickoff',
      'mercenary':person,'quaternius':source,
      'identical_joint_names':sorted(cross),
      'identical_joint_name_count':len(cross),
      'retarget_required':True,'original_game_modified':False,
      'further_pose_qa_needed':True}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print('QUATERNIUS_V012_AUDIT',json.dumps({'source_clips':source['animations_total'],'relevant':source['relevant_clips'],
   'source_joints':source['skin_joint_count'],'target_joints':person['skin_joint_count'],'matching_joint_names':sorted(cross)}),flush=True)
if __name__=='__main__':main()
