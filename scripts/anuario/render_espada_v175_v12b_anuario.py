#!/usr/bin/env python3
"""Academic Anuario V175/V12B render: exact approved source and frozen EXR,
using Project Genesis's original Blender scripts. No geometry/source edits."""
from pathlib import Path
import hashlib,json,sys,struct
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"fab_sword"))
import render_v12_v175_j_roughness as historic

def validate_png(path):
    d=path.read_bytes()
    if d[:8]!=b"\x89PNG\r\n\x1a\n" or len(d)<50000:
        raise ValueError("PNG missing or invalid "+str(path))
    wh=struct.unpack_from(">II",d,16)
    if wh != (1200,1500):raise ValueError(f"wrong size: {wh}")
    return {"path":path.name,"size":len(d),"sha256":hashlib.sha256(d).hexdigest(),"width":wh[0],"height":wh[1]}

# Run the unmodified authentic V12 shader/material/lighting pipeline, including
# exact V03 source GLB SHA and studio_small_09 EXR HDRI hash validations.
historic.main()
scene=bpy.context.scene
a=sys.argv[sys.argv.index("--")+1:]
out=Path(a[a.index("--output-dir")+1])
assert bpy.app.version_string.startswith("4.5.13")
assert scene.render.engine=="CYCLES"
assert bpy.data.images.get("studio_small_09_4k.exr") is not None
for cam,name in [
    ("CAM_three_quarters","PG_Espada_V03_V175_V12B_HDRI32_TresCuartos.png"),
    ("CAM_BLADE_MACRO","PG_Espada_V03_V175_V12B_HDRI32_Detalle_Filo.png")
]:
    historic.render(scene,cam,name,out)
paths=[
"V12_V175_Color_J_Rugosidad034_Hero.png",
"PG_Espada_V03_V175_V12B_HDRI32_TresCuartos.png",
"PG_Espada_V03_V175_V12B_HDRI32_Detalle_Filo.png"
]
a1=json.loads((out/"render_audit.json").read_text())
a2=json.loads((out/"v12_surface_audit.json").read_text())
if a1["source_sha256"]!=historic.EXPECTED_GLB or a1["hdri_sha256"]!=historic.EXPECTED_HDR:raise ValueError("source mismatch")
if a1["hdri_image_depth_bpp"]!=96 or a1["hdri_dimensions"]!=[4096,2048]:raise ValueError("wrong HDRI")
if a1["geometry_triangles"]!=2150 or a1["geometry_or_material_edit"]:raise ValueError("source geometry altered")
if not a2["V10_color_socket_unchanged"] or a2["additional_channel_vfx"]:raise ValueError("source PBR modified")
audit={"render_type":"REAL_BLENDER_CYCLES_NOT_GENERATIVE",
"project":"Project Genesis","asset":"V03 V175 V12B approved shader look",
"source_glb_sha256":a1["source_sha256"],
"source_geometry_triangles":2150,"source_geometry_preserved":True,
"blender":bpy.app.version_string,"engine":"CYCLES","samples":scene.cycles.samples,
"hdri":"Poly Haven studio_small_09_4k.exr","hdri_sha256":a1["hdri_sha256"],
"hdri_bits_per_channel":32,"hdri_dimensions":a1["hdri_dimensions"],
"shader_profile":"V175 palette original + V12B original 0.34 roughness factor and 0.10 local oxidation",
"vfx":"off","approved_asset_game_integration":"not claimed",
"images":[validate_png(out/x) for x in paths]}
(out/"PG_Anuario_Render_Audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print("GENESIS_ANUARIO_REAL_V175_V12B_HDRI32_RENDER_VERIFIED",json.dumps(audit),flush=True)
