#!/usr/bin/env python3
"""Apply bloom ONLY in the recorded video; source GLB and PlayCanvas scene untouched."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter,ImageChops,ImageEnhance
import argparse,json,os
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('vfx-video-output'));a=p.parse_args()
counts={}
for folder in sorted(a.root.glob('variant_*')):
    paths=sorted(folder.glob('frame_*.png'))
    if not paths:continue
    for path in paths:
        orig=Image.open(path).convert('RGB')
        raw=np.asarray(orig).astype(np.float32)
        mx=raw.max(axis=2);mn=raw.min(axis=2)
        chroma=mx-mn
        bright=np.clip((mx-120)/100,0,1)
        color=np.clip((chroma-25)/100,0,1)
        mask=(bright*color)**1.4
        yy,xx=np.mgrid[0:raw.shape[0],0:raw.shape[1]]
        mask*=((xx>385)&(xx<895)&(yy>40)&(yy<688))
        lights=(raw*mask[:,:,None]*0.72).clip(0,255).astype(np.uint8)
        glow=Image.fromarray(lights,'RGB')
        tight=glow.filter(ImageFilter.GaussianBlur(radius=4))
        broad=glow.filter(ImageFilter.GaussianBlur(radius=15))
        out=ImageChops.screen(orig,ImageEnhance.Brightness(tight).enhance(.5))
        out=ImageChops.screen(out,ImageEnhance.Brightness(broad).enhance(.4))
        out.save(path)
    counts[folder.name]=len(paths)
print('GENESIS_PLAYCANVAS_VIDEO_BLOOM_POST',json.dumps(counts))
