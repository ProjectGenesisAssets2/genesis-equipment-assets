#!/usr/bin/env python3
"""Generate eight reusable grayscale masks in the EXACT V03 blade UV0 layout.

Masks are VFX DATA only. They are NOT painted on the V175 iron color texture.
The canal Base is non-emissive: physical iron wear/normal influence, not magic.
Original blade polygon UV footprint: U(front)=.741-.840, U(back)=.843-.940,
V(hilt->tip)=.005-.996. Never touch grip/guard material.
"""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

NAMES=("Base","Luz","Sombra","Fuego","Hielo","Naturaleza","Tierra","Rayo")
def smooth(lo,hi,value):
    t=np.clip((value-lo)/(hi-lo),0.,1.)
    return t*t*(3.-2.*t)
def gau(v,center,sigma):
    return np.exp(-0.5*((v-center)/sigma)**2)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--size',type=int,default=1536)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    W=args.size*2//3
    H=args.size
    u=(np.arange(W,dtype='float32')+.5)/W
    v=1.-(np.arange(H,dtype='float32')+.5)/H
    U,V=np.meshgrid(u,v)
    # Front/back original material UV islands; do not relayout source asset.
    front=(U>=.7412)&(U<=.8400)
    back=(U>=.8430)&(U<=.9403)
    side=front|back
    # Reverse back U so left-vs-right remains consistent in world view.
    X=np.where(front,(U-.7895)/.049,(.8916-U)/.049)
    # Gradual tip/heel fade. Color mask cannot extend past actual blade geometry.
    envelope=smooth(.015,.11,V)*(1.-smooth(.95,.995,V))
    edge=np.clip(1.-np.abs(X),0,1)
    wav=np.sin(V*39.0+np.sin(V*63.))
    fleck=(np.sin(X*52+V*107.)*np.sin(V*205+X*21.)+.45*np.sin(X*83-V*165.))/1.45
    rough=np.clip(.50+.27*np.sin(V*31.1+X*12.6)+.18*np.cos(V*72.-X*39.)+.12*np.sin(V*156+X*24.),0.,1.)
    # All non-Base masks are localized strips/branches; their spatial distributions
    # are independent so two channels can stack on the same unchanged blade.
    base=.12*edge+ .40*gau(X,np.sin(V*17)*.02,.035) * (.5+.5*rough)
    luz=(.25*gau(X,0.,.24)+.85*gau(X,.05+.09*np.sin(V*13),.040)*(.5+.5*rough))*(.7+.3*np.sin(V*9.)**2)
    sombra=(.8*gau(X,.45+.12*np.sin(V*19),.32)*rough+
            .65*gau(X,.33+.11*np.cos(V*32),.09)*(.55+.45*np.cos(V*54)))
    fire_line=-.48+.17*np.sin(V*46)+.04*np.sin(V*123)
    fuego=(.86*gau(X,fire_line,.15)*(.5+.5*np.cos(V*25.))+
           .55*gau(X,fire_line-.26*np.sin(V*69.),.065)*rough+
           .55*gau(X,-.80,.13)*(.5+.5*fleck))*(.6+.4*rough)
    frost=.5+.5*np.sin(X*19+V*128.)*np.sin(X*27-V*163.)
    hielo=(.60*gau(X,-.50,.24)+.45*(np.abs(np.sin(X*55+V*83.))>.89)*frost+
           .46*gau(X,-.7+.14*np.cos(V*78),.11))*(.7+.3*rough)
    vine=.40+.16*np.sin(V*22)+.04*np.sin(V*59)
    nat=(.92*gau(X,vine,.045)+
        .44*gau(X,vine+.35*np.sin(V*60),.075)*(.5+.5*rough)+
        .34*gau(X,.74,.16)*fleck)
    cracks=np.abs(np.sin(V*73+X*31.)*np.cos(V*21-X*29.))
    tierra=.85*gau(cracks,.94,.06)*(.4+.6*rough)+.25*gau(X,.0,.45)*rough
    bolt=.56+.20*np.sin(V*85)+.09*np.sin(V*211)
    rayo=(1.0*gau(X,bolt,.036)+
          .48*gau(X,bolt-.27*np.sin(V*57),.047)*(.7+.3*rough)+
          .27*gau(X,.9,.12)*fleck)
    data={"Base":base,"Luz":luz,"Sombra":sombra,"Fuego":fuego,
          "Hielo":hielo,"Naturaleza":nat,"Tierra":tierra,"Rayo":rayo}
    records=[]
    previews=[]
    for name in NAMES:
        intensity=np.maximum(data[name],0).astype('float32')
        # The ninth texture/overlay does not exist. Base is a non-glowing wear mask.
        # Avoid blacking the entire UV if shoulder has uv edge outside the two islands.
        img=np.uint8(np.clip(intensity*envelope*side*255,0,255))
        out=args.output_dir/("Genesis_Mask_%s_V001.png"%name)
        Image.fromarray(img,mode='L').save(out,optimize=True)
        records.append({'channel':name,'image':out.name,'width':W,'height':H,
                        'max':int(img.max()),'mean':round(float(img.mean()),2),
                        'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
                        'is_emissive':name!='Base'})
        pic=Image.fromarray(img).resize((W//2,H//2))
        previews.append(pic)
    # QA contact sheet, no source/GLB data redistributed.
    tilew=W//2;tileh=H//2
    sheet=Image.new('RGB',(4*tilew,2*(tileh+44)),(25,29,34))
    draw=ImageDraw.Draw(sheet)
    for i,(name,preview) in enumerate(zip(NAMES,previews)):
        x=i%4*tilew;y=i//4*(tileh+44)
        sheet.paste(Image.merge('RGB',(preview,preview,preview)),(x,y+44))
        draw.text((x+14,y+12),name,fill=(238,236,219))
    sheet.save(args.output_dir/'Genesis_8_Mascaras_ContactSheet.png')
    manifest={
        'schema':'ProjectGenesisEightCanalMasks-V001',
        'target':'Genesis_Sword_Iron_V03_V175_Colores.glb',
        'blade_uv_islands':{'front_U':[.7412,.8400],'back_U':[.8430,.9403],'blade_V':[.005,.996]},
        'material_slot':1,
        'channels':['Base','Luz','Sombra','Fuego','Hielo','Naturaleza','Tierra','Rayo'],
        'source_iron_texture_untouched':True,
        'use':'grayscale influence mask sampled by UV0 in blade-only shader',
        'lighting_rule':'intensity 1-100 scales emissive and coverage, two channels remain independent',
        'base_channel':'not an elemental emissive effect',
        'records':records}
    (args.output_dir/'mask_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print('GENESIS_8_VFX_MASKS_GENERATED',json.dumps({'count':len(records),'nonempty':all(x['max']>0 for x in records),'size':[W,H]},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
