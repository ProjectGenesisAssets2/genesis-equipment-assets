#!/usr/bin/env python3
"""Find official, freely released Quaternius medieval outfits for a verified
existing finger-rigged humanoid. No paywalls, no decryption, no user cookies.
Only inspect public source pages and already licensed files.
"""
import json,re,urllib.request,html,hashlib,struct
from pathlib import Path
from html.parser import HTMLParser

OUT=Path("output/mercenary_finger_rig_v040");OUT.mkdir(parents=True,exist_ok=True)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   d=dict(attrs);self.current=d.get('href');self.links.append({'href':self.current,'attrs':d})
 def handle_endtag(self,tag):
  if tag=='a':self.current=None
def req(url):
 r=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 GenesisCC0SourceAudit/1.0'})
 with urllib.request.urlopen(r,timeout=35) as f:return f.read()
links={}
for kind,url in {
 'base':'https://quaternius.com/packs/universalbasecharacters.html',
 'outfits':'https://quaternius.com/packs/modularcharacteroutfitsfantasy.html',
 'outfits_itch':'https://quaternius.itch.io/modular-character-outfits-fantasy/purchase'
}.items():
 try:
  text=req(url).decode('utf-8','replace')
  p=Links();p.feed(text)
  relevant=[entry for entry in p.links if any(tok in str(entry).lower() for tok in ['itch','download','drive.google','zip','mega.nz','dropbox'])]
  paths=re.findall(r'https?://[^<"\s]{8,230}',text)
  links[kind]={'url':url,'entries':relevant[:40],'embedded_urls':[x for x in paths if any(z in x.lower() for z in ['itch.io','drive.google','zip','cdn.','storage.'])][:30]}
 except Exception as exc:links[kind]={'url':url,'error':str(exc)}
# Get existing actual CC0 65-bone male Rig GLB from repo that attributes Quaternius
u='https://raw.githubusercontent.com/programasweights/avatar/main/public/assets/character.glb'
try:
 data=req(u)
 assert data[:4]==b'glTF' and struct.unpack_from('<II',data,4)==(2,len(data))
 n,t=struct.unpack_from('<I4s',data,12);assert t==b'JSON'
 g=json.loads(data[20:20+n])
 sk=g.get('skins',[])
 assert sk and g['meshes']
 bones=[g['nodes'][j].get('name','') for j in sk[0]['joints']]
 l=[x for x in bones if re.search(r'(?i)(thumb|index|middle|ring|pinky).*(?:_l|Left)',x)]
 r=[x for x in bones if re.search(r'(?i)(thumb|index|middle|ring|pinky).*(?:_r|Right)',x)]
 audit={'sha256':hashlib.sha256(data).hexdigest(),'file_size':len(data),'nodes':len(g['nodes']),
 'skins':len(sk),'joints':len(bones),'left_finger_bones':l,'right_finger_bones':r,
 'animations':len(g.get('animations',[])),'model_source':'Quaternius Universal Base Characters[Standard] CC0 via programasweights/avatar',
 'is_medieval_outfit':False}
 if len(l)>=10 and len(r)>=10:
  (OUT/'QUATERNIUS_FINGER_RIG_BASE_SOURCE.glb').write_bytes(data)
 links['base_rig']=audit
except Exception as e:links['base_rig']={'error':str(e)}
(OUT/'OFFICIAL_CC0_KNIGHT_DISCOVERY.json').write_text(json.dumps(links,indent=2,ensure_ascii=False))
print('GENESIS_V040_DISCOVERY',json.dumps(links,ensure_ascii=False),flush=True)
