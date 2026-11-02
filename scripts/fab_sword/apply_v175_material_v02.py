#!/usr/bin/env python3
"""Apply Genesis V175-derived 2K iron maps only to the sword blade.

This public script contains no source mesh or licensed 2K texture bytes.
Start from the already audited Iron V01 GLB and extract the four material
maps from your own Genesis_Demo_Kit_Materiales_UE5_2K.zip.

Usage:
 python scripts/fab_sword/apply_v175_material_v02.py \
   --input Genesis_Sword_Iron_V01.glb \
   --textures /secure/Genesis_Demo_Materiales/Texturas/Basicos \
   --output Genesis_Sword_Iron_V02_V175_PBR.glb
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def parse_glb(raw):
    magic, version, total = struct.unpack_from("<4sII", raw, 0)
    if (magic, version, total) != (b"glTF", 2, len(raw)):
        raise ValueError("Invalid GLB")
    offset = 12
    chunks = {}
    while offset < len(raw):
        n, name = struct.unpack_from("<I4s", raw, offset)
        offset += 8
        chunks[name] = raw[offset:offset+n]
        offset += n
    if offset != len(raw):
        raise ValueError("Unexpected trailing bytes")
    return json.loads(chunks[b"JSON"]), bytearray(chunks[b"BIN\x00"])


def apply(source, textures, output):
    raw = source.read_bytes()
    doc, buffer = parse_glb(raw)
    mesh = doc["meshes"][0]
    if len(doc["meshes"]) != 1 or len(mesh["primitives"]) != 2:
        raise ValueError("Expected isolated sword with 2 material primitives")
    blade = mesh["primitives"][1]
    if doc["accessors"][blade["indices"]]["count"] != 294:
        raise ValueError("Expected exactly 98 blade triangles")
    if doc["accessors"][mesh["primitives"][0]["indices"]]["count"] != 6156:
        raise ValueError("Expected exactly 2052 hilt+guard triangles")
    if len(doc["materials"]) < 2 or blade["material"] != 1:
        raise ValueError("Unexpected material layout")

    def add_image(path, name):
        data = path.read_bytes()
        while len(buffer) % 4:
            buffer.append(0)
        doc["bufferViews"].append({
            "buffer": 0, "byteOffset": len(buffer), "byteLength": len(data)
        })
        buffer.extend(data)
        doc["images"].append({
            "bufferView": len(doc["bufferViews"])-1,
            "mimeType": "image/png", "name": name
        })
        doc["textures"].append({
            "sampler": 0, "source": len(doc["images"])-1
        })
        return len(doc["textures"])-1

    color = add_image(textures/"T_Hierro_Color_2K.png", "Genesis_V175_Hierro_Color_2K")
    orm = add_image(textures/"T_Hierro_ORM_2K.png", "Genesis_V175_Hierro_ORM_2K")
    normal = add_image(textures/"T_Hierro_Normal_2K.png", "Genesis_V175_Hierro_Normal_2K")
    mat = doc["materials"][1]
    mat["name"] = "Genesis_Hoja_Hierro_V175_Maps_TEST_V02"
    mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": color}
    mat["pbrMetallicRoughness"]["metallicRoughnessTexture"] = {"index": orm}
    mat["pbrMetallicRoughness"]["baseColorFactor"] = [1, 1, 1, 1]
    mat["normalTexture"] = {"index": normal, "scale": 1}
    mat["occlusionTexture"] = {"index": orm, "strength": .6}
    doc["buffers"][0]["byteLength"] = len(buffer)
    j = json.dumps(doc, separators=(",",":"), ensure_ascii=False).encode("utf-8")
    j += b" " * (-len(j)%4)
    b = bytes(buffer)+b"\0" * (-len(buffer)%4)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(
        struct.pack("<4sII",b"glTF",2,28+len(j)+len(b))+
        struct.pack("<I4s",len(j),b"JSON")+j+
        struct.pack("<I4s",len(b),b"BIN\x00")+b
    )
    return {"source_sha256": hashlib.sha256(raw).hexdigest(),
            "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "output_bytes": output.stat().st_size,
            "blade_triangles": 98, "other_triangles": 2052,
            "source_unchanged": True, "uv_unchanged": True,
            "note": "V175-derived experimental 2K maps. Not a bake of V175 original .blend"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--textures", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(apply(a.input,a.textures,a.output), indent=2))
