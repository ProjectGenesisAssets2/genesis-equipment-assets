#!/usr/bin/env python3
"""Project Genesis Fab sword iron PBR v01 - run locally with licensed source only.

Requires Python 3.10+, numpy, Pillow.
Splits the original indexed sword mesh into two glTF primitives without moving
vertices or modifying normals, tangents, UVs or triangle topology.
Does not include or upload any Fab model bytes in this public repository.
"""
import argparse
import copy
import hashlib
import io
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image

SOURCE_SHA256 = "493b3b9080b3b209de66186e0265c3b68d2fcfdbfe7c8b214425e197b3086b32"
BLADE_TRIANGLES = 98

def read_glb(data):
    magic, version, size = struct.unpack_from("<4sII", data, 0)
    if (magic, version, size) != (b"glTF", 2, len(data)):
        raise ValueError("Unexpected GLB header")
    cursor = 12
    chunks = {}
    while cursor < len(data):
        length, tag = struct.unpack_from("<I4s", data, cursor)
        cursor += 8
        chunks[tag] = data[cursor:cursor+length]
        cursor += length
    if cursor != len(data) or b"JSON" not in chunks or b"BIN\x00" not in chunks:
        raise ValueError("Invalid GLB chunks")
    return json.loads(chunks[b"JSON"]), chunks[b"BIN\x00"]

def accessor(doc, blob, idx):
    a = doc["accessors"][idx]
    view = doc["bufferViews"][a["bufferView"]]
    dt = {5123:"<u2",5125:"<u4",5126:"<f4"}[a["componentType"]]
    cols = {"SCALAR":1,"VEC3":3}[a["type"]]
    itemsize = np.dtype(dt).itemsize
    return np.ndarray((a["count"],cols), dtype=dt, buffer=blob,
                      offset=view.get("byteOffset",0)+a.get("byteOffset",0),
                      strides=(view.get("byteStride",itemsize*cols),itemsize)).copy()

def blade_mask(tris, pos):
    # Connected shells. Some guard faces overlap the blade root in XYZ;
    # a plain bounding box would incorrectly retexture them.
    neighbors = [[] for _ in pos]
    for face_idx, tri in enumerate(tris):
        for vertex in tri: neighbors[int(vertex)].append(face_idx)
    seen = set()
    selected = np.zeros(len(tris), dtype=bool)
    for seed in range(len(tris)):
        if seed in seen: continue
        stack = [seed]; seen.add(seed); component = []
        while stack:
            idx = stack.pop()
            component.append(idx)
            for v in tris[idx]:
                for f in neighbors[int(v)]:
                    if f not in seen: seen.add(f); stack.append(f)
        vertices = pos[tris[component]].reshape(-1, 3)
        min_y, max_y = vertices[:,1].min(), vertices[:,1].max()
        bound_x = np.abs(vertices[:,0]).max()
        blade_surface = max_y > .95 and min_y >= -.425 and bound_x < .09
        blade_side = len(component) == 3 and min_y >= -.425 and max_y > -.28 and bound_x < .09
        if blade_surface or blade_side: selected[component] = True
    if selected.sum() != BLADE_TRIANGLES:
        raise ValueError(f"Ambiguous blade isolation: {int(selected.sum())} triangles")
    return selected

def save_glb(doc, blob, target):
    doc["buffers"][0]["byteLength"] = len(blob)
    meta = json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode("utf8")
    meta += b" " * (-len(meta)%4)
    blob += b"\0" * (-len(blob)%4)
    data = (struct.pack("<4sII",b"glTF",2,28+len(meta)+len(blob))
            +struct.pack("<I4s",len(meta),b"JSON")+meta
            +struct.pack("<I4s",len(blob),b"BIN\x00")+blob)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)

def build(source, target, report, tint=(.83,.85,.86), roughness_floor=172):
    raw = source.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != SOURCE_SHA256: raise ValueError(f"Unrecognized GLB SHA256 {sha}")
    doc, bin_data = read_glb(raw)
    if len(doc["meshes"]) != 1 or len(doc["materials"]) != 1:
        raise ValueError("Unexpected mesh/material layout")
    prim = doc["meshes"][0]["primitives"][0]
    coords = accessor(doc,bin_data,prim["attributes"]["POSITION"])
    inds = accessor(doc,bin_data,prim["indices"]).flatten().reshape(-1,3)
    mask = blade_mask(inds,coords)
    blob = bytearray(bin_data)
    def new_view(data,target_type=None):
        while len(blob)%4: blob.append(0)
        offset=len(blob);blob.extend(data)
        view={"buffer":0,"byteOffset":offset,"byteLength":len(data)}
        if target_type: view["target"]=target_type
        doc["bufferViews"].append(view)
        return len(doc["bufferViews"])-1
    def new_index_acc(selected):
        values=inds[selected].flatten()
        dtype={5123:"<u2",5125:"<u4"}[doc["accessors"][prim["indices"]]["componentType"]]
        bv=new_view(values.astype(dtype).tobytes(),34963)
        doc["accessors"].append({"bufferView":bv,
            "componentType":doc["accessors"][prim["indices"]]["componentType"],
            "count":len(values),"type":"SCALAR",
            "min":[int(values.min())],"max":[int(values.max())]})
        return len(doc["accessors"])-1
    nonblade_acc=new_index_acc(~mask)
    blade_acc=new_index_acc(mask)
    original=doc["materials"][prim["material"]]
    pbr=original["pbrMetallicRoughness"]
    mr_id=pbr["metallicRoughnessTexture"]["index"]
    image_id=doc["textures"][mr_id]["source"]
    bv=doc["bufferViews"][doc["images"][image_id]["bufferView"]]
    image_bytes=bin_data[bv["byteOffset"]:bv["byteOffset"]+bv["byteLength"]]
    rough=np.asarray(Image.open(io.BytesIO(image_bytes)).convert("RGB")).copy()
    rough[:,:,1]=np.maximum(rough[:,:,1],roughness_floor)  # green=roughness
    f=io.BytesIO()
    Image.fromarray(rough).save(f,format="PNG",optimize=True)
    doc["images"].append({"bufferView":new_view(f.getvalue()),
                          "mimeType":"image/png","name":"Genesis_IronBlade_Roughness_V01"})
    tex=copy.deepcopy(doc["textures"][mr_id]);tex["source"]=len(doc["images"])-1
    doc["textures"].append(tex)
    blade_material=copy.deepcopy(original)
    blade_material["name"]="Genesis_IronBlade_PBR_V01"
    blade_material["pbrMetallicRoughness"]["baseColorFactor"]=[*tint,1.]
    blade_material["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"]=len(doc["textures"])-1
    doc["materials"].append(blade_material)
    doc["meshes"][0]["primitives"]=[
        dict(copy.deepcopy(prim),indices=nonblade_acc),
        dict(copy.deepcopy(prim),indices=blade_acc,material=len(doc["materials"])-1)]
    output_sha,output_size=save_glb(doc,blob,target)
    audit={"source_sha256":sha,"output_sha256":output_sha,"original_vertices":len(coords),
           "triangles":len(inds),"blade_triangles":int(mask.sum()),
           "rest_triangles":int((~mask).sum()),
           "materials":len(doc["materials"]),"output_bytes":output_size,
           "geometry_unchanged":True,"public_source_asset_distribution":False}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf8")
    return audit

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.input,a.output,a.report),indent=2))
