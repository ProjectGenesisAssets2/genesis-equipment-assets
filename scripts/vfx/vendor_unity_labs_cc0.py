#!/usr/bin/env python3
"""Vendor unmodified CC0 flame ZIPs, browser PNG atlases and real animated previews.

Reads three original Unity Labs Paris archives already downloaded by CI;
never generates fake sprites or changes approved 3D assets.
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from PIL import Image

DATA = {
 "Flame02": ("Flame02-flipbooks.zip", "Flame02_16x4.tga",
             "f37b12cdae090591d537ed3bb50396f03833a49864362bf665d6817b7282c954"),
 "Flame03": ("Flame03-flipbooks.zip", "Flame03_16x4.tga",
             "248c2d09c6599ded36085633d4c7fdb9a9a05bdf1a98ab34b8f14d282cef87a9"),
 "SmallFlame01": ("SmallFlame01-mini-flipbooks.zip", "SmallFlame01-mini_16x4.tga",
             "a9585630cdfa568849f82b62fe1dac93045012f90963cc21ee909cceaa23953e")
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def composite_frame(sheet, index):
    w,h=sheet.size
    cw,ch=w//16,h//4
    col,row=index%16,index//16
    rgba=sheet.crop((col*cw,row*ch,(col+1)*cw,(row+1)*ch)).convert("RGBA")
    # Display fire over a dark backdrop without losing its source alpha.
    bg=Image.new("RGBA",rgba.size,(13,19,29,255))
    bg.alpha_composite(rgba)
    return bg.convert("RGB")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("assets/vfx/experimental/unity-labs-cc0"))
    a=p.parse_args()
    for path in ("source","atlases","previews"):
        (a.output/path).mkdir(parents=True,exist_ok=True)
    audit={"schema":"Genesis_UnityLabs_Paris_CC0_FlameLibrary_V17",
           "license":"CC0","source":"https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks",
           "source_verified_run":42081013414,"grid":[16,4],"frames":64,
           "effects":{},"approved_in_game":False}
    for key,(archive,filename,expected) in DATA.items():
        raw=(a.source/archive).read_bytes()
        assert sha(raw)==expected,(key,"original archive checksum mismatch",sha(raw))
        (a.output/"source"/archive).write_bytes(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist()
            assert filename in names,(filename,names)
            original=z.read(filename)
        (a.output/"source"/filename).write_bytes(original)
        sheet=Image.open(io.BytesIO(original)).convert("RGBA")
        w,h=sheet.size
        assert w in (1024,2048) and h*2==w and w%16==0
        atlas=a.output/"atlases"/(Path(filename).stem+".png")
        sheet.save(atlas,format="PNG",optimize=True)
        # Same 64 source frames, actual animation at 12.5fps.
        frames=[composite_frame(sheet,i).resize((256,512),Image.Resampling.BICUBIC)
                for i in range(64)]
        gif=a.output/"previews"/(key+"_animado.gif")
        frames[0].save(gif,format="GIF",save_all=True,append_images=frames[1:],
                       duration=80,loop=0,optimize=True)
        tiles=a.output/"previews"/(key+"_fotogramas_0_16_32_48.png")
        montage=Image.new("RGB",(256*4,512),(13,19,29))
        for idx,frameid in enumerate((0,16,32,48)):
            montage.paste(frames[frameid],(idx*256,0))
        montage.save(tiles,format="PNG",optimize=True)
        audit["effects"][key]={
            "archive":str((a.output/"source"/archive).as_posix()),
            "zip_bytes":len(raw),"zip_sha256":sha(raw),
            "original_atlas_tga":str((a.output/"source"/filename).as_posix()),
            "original_atlas_sha256":sha(original),"atlas_resolution":[w,h],
            "playcanvas_atlas":str(atlas.as_posix()),
            "playcanvas_png_sha256":sha(atlas.read_bytes()),
            "animated_preview":str(gif.as_posix()),
            "frame_size":[w//16,h//4],"frames":64}
        print("GENESIS_CC0_LIBRARY_VERIFIED",key,"atlas",w,h,
              "png",atlas.stat().st_size,"gif",gif.stat().st_size,flush=True)
    report=a.output/"vfx_source_audit.json"
    report.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
    print("GENESIS_CC0_LIBRARY_ALL_THREE_VFX_VERIFIED",report,flush=True)

if __name__=="__main__":
    main()
