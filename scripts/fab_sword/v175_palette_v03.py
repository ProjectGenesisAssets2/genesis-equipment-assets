#!/usr/bin/env python3
"""Project Genesis Fab Sword V03: V175-approved-palette experiment.

Requires numpy, Pillow and opencv-python.
Sources are licensed local files; do not commit the Fab GLB or baked derivative.
This is a palette adaptation from an approved V175 reference render and the
existing Genesis 2K detail masks, NOT a byte-perfect Blender shader bake.
"""
import argparse, io, struct, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import cv2


def parse_glb(raw):
    magic, ver, total = struct.unpack_from("<4sII", raw, 0)
    if (magic, ver, total) != (b"glTF", 2, len(raw)):
        raise ValueError("Invalid GLB header")
    ptr, chunks = 12, {}
    while ptr < len(raw):
        n, typ = struct.unpack_from("<I4s", raw, ptr)
        ptr += 8
        chunks[typ] = raw[ptr:ptr+n]
        ptr += n
    if ptr != len(raw):
        raise ValueError("Bad GLB chunk lengths")
    return json.loads(chunks[b"JSON"]), bytearray(chunks[b"BIN\x00"])


def bake_v175_palette(base, detail):
    """Topological mask retains V175's forged-iron grayscale with oxide patches."""
    if base.shape[:2] != detail.shape[:2]:
        raise ValueError("Base/detail dimensions differ")
    rgb = base.astype(np.float32)
    luma = rgb[:,:,0]*.30 + rgb[:,:,1]*.59 + rgb[:,:,2]*.11
    delta = (luma-92.0)*.73
    iron = np.stack((88+delta, 91+delta, 95+delta), axis=2)
    # Mask contract: R wear, G oxidation, B pitting, A microscratches.
    oxide = cv2.GaussianBlur(detail[:,:,1].astype(np.float32)/255.0, (0,0), 2.2)
    alpha = np.clip(oxide**.82*.65,0,.55)[:,:,None]
    brown = np.array([112.,84.,70.],dtype=np.float32).reshape(1,1,3)
    iron = iron*(1-alpha) + brown*alpha
    iron -= (detail[:,:,2].astype(np.float32)/255.)[:,:,None]*11
    iron += (detail[:,:,0].astype(np.float32)/255.)[:,:,None]*4.5
    return Image.fromarray(np.uint8(np.clip(iron,1,255)), "RGB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path, help="Local V02 GLB")
    p.add_argument("--color", required=True, type=Path, help="T_Hierro_Color_2K.png")
    p.add_argument("--detail", required=True, type=Path, help="T_Hierro_DetailRGBA_2K.png")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--preview-texture", type=Path, required=True)
    a = p.parse_args()
    raw = a.source.read_bytes()
    doc, blob = parse_glb(raw)
    if len(doc["meshes"]) != 1 or len(doc["meshes"][0]["primitives"]) != 2:
        raise ValueError("Expected isolated V02 sword")
    grip, blade = doc["meshes"][0]["primitives"]
    if doc["accessors"][grip["indices"]]["count"] != 6156 or doc["accessors"][blade["indices"]]["count"] != 294:
        raise ValueError("Unexpected triangle count: do not recolor blindly")
    if grip["material"] != 0 or blade["material"] != 1:
        raise ValueError("Unexpected material isolation")

    rgb = np.asarray(Image.open(a.color).convert("RGB"))
    det = np.asarray(Image.open(a.detail).convert("RGBA"))
    result = bake_v175_palette(rgb,det)
    data = io.BytesIO()
    result.save(data,format="PNG",optimize=True)
    a.preview_texture.parent.mkdir(parents=True,exist_ok=True)
    a.preview_texture.write_bytes(data.getvalue())
    while len(blob)%4: blob.append(0)
    doc["bufferViews"].append({"buffer":0,"byteOffset":len(blob),"byteLength":len(data.getvalue())})
    blob.extend(data.getvalue())
    doc["images"].append({"bufferView":len(doc["bufferViews"])-1,
                          "mimeType":"image/png","name":"Genesis_V175_ApprovedPalette_V03"})
    doc["textures"].append({"sampler":0,"source":len(doc["images"])-1})
    doc["materials"][1]["name"]="Genesis_Iron_Blade_V175_Palette_V03_TEST"
    doc["materials"][1]["pbrMetallicRoughness"]["baseColorTexture"]={"index":len(doc["textures"])-1}
    doc["materials"][1]["pbrMetallicRoughness"]["baseColorFactor"]=[1.,1.,1.,1.]
    doc["buffers"][0]["byteLength"]=len(blob)
    j=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode("utf8")
    j+=b" " * (-len(j)%4)
    b=bytes(blob)+b"\0" * (-len(blob)%4)
    out=(struct.pack("<4sII",b"glTF",2,28+len(j)+len(b))
         +struct.pack("<I4s",len(j),b"JSON")+j
         +struct.pack("<I4s",len(b),b"BIN\x00")+b)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(out)
    print(json.dumps({"sha256":hashlib.sha256(out).hexdigest(),
                      "output_bytes":len(out),"triangles":2150,
                      "blade_triangles":98,"geometry_edited":False},indent=2))


if __name__ == "__main__":
    main()
