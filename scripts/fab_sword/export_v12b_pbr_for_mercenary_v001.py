#!/usr/bin/env python3
"""Project Genesis V175/V12B: incremental WebGL GLB output from exact approved preset.
SOURCE GLB and approved preset are NEVER overwritten.
Run inside 4.5.13 LTS GitHub Actions using original 4K 32-bit/channel EXR HDRI.
Note: baked ROUGHNESS is an LDR texture; the HDRI remains float32 EXR for the Cycles render.
"""
import bpy,sys,json,struct,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render_v12_v175_j_roughness as v12

def arg(name):
    parts=sys.argv[sys.argv.index('--')+1:]
    return Path(parts[parts.index(name)+1])

source=arg('--input')
hdri=arg('--hdri')
out=arg('--output-dir')
out.mkdir(parents=True,exist_ok=True)
EXACT_SOURCE='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
EXACT_HDRI='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
assert hashlib.sha256(source.read_bytes()).hexdigest()==EXACT_SOURCE
assert hashlib.sha256(hdri.read_bytes()).hexdigest()==EXACT_HDRI
# Original script uses exact V175 color, J ridge normal, metallic 0.98,
# roughness multiplier 0.34 and oxide addition 0.10 on final V12B render.
v12.main()
s=bpy.context.scene
assert s.render.engine=='CYCLES'
im=next(i for i in bpy.data.images if i.filepath and Path(bpy.path.abspath(i.filepath)).name==hdri.name)
assert im.file_format=='OPEN_EXR' and im.depth==96 and tuple(im.size)==(4096,2048)
meshes=[o for o in s.objects if o.type=='MESH']
tr=sum(len(o.data.loop_triangles) for o in meshes)
assert tr==2150,('Changed source geometry',tr)
materials=list({m.name:m for o in meshes for m in o.data.materials if m}.values())
blade=next(m for m in materials if 'Iron_Blade_V175' in m.name)
bsdf=next(n for n in blade.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert bsdf.inputs['Base Color'].is_linked
rough=bsdf.inputs['Roughness'].links[0].from_node
assert rough.name=='V12_CLEAN_IRON_PLUS_OXIDIZED_GROOVES'
mult=next(n for n in blade.node_tree.nodes if n.name=='V11_J_V175_ROUGHNESS_MULT_049')
oxide=next(n for n in blade.node_tree.nodes if n.name=='V12_J_OXIDE_LOCAL_ROUGHNESS')
assert abs(mult.inputs[1].default_value-0.34)<1e-7
assert abs(oxide.inputs[1].default_value-0.10)<1e-7
# Bake procedural V12B roughness into a portable texture. This is *not* an HDRI
# replacement or a lighting bake: physical surface properties stay dynamic.
bakeimg=bpy.data.images.new('Genesis_V175_V12B_BAKED_ROUGHNESS_1536',1536,1536,alpha=False,float_buffer=False)
bakeimg.colorspace_settings.name='Non-Color'
target_nodes=[]
for mat in materials:
    node=mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.name='V12B_ROUGHNESS_BAKE_TARGET'
    node.image=bakeimg
    for n in mat.node_tree.nodes:n.select=False
    node.select=True;mat.node_tree.nodes.active=node
    target_nodes.append((mat,node))
s.render.bake.use_clear=True
s.render.bake.margin=8
for i,obj in enumerate(meshes):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    s.render.bake.use_clear=(i==0)
    bpy.ops.object.bake(type='ROUGHNESS')
bakeimg.filepath_raw=str((out/'Genesis_V175_V12B_Roughness_1536.png').resolve())
bakeimg.file_format='PNG';bakeimg.save()
assert (out/'Genesis_V175_V12B_Roughness_1536.png').stat().st_size>10000
# Disconnect ONLY export-material roughness and use baked surface texture.
# Original source and approved preset/preview stay immutable.
for mat,node in target_nodes:
    princ=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not princ:continue
    mat.node_tree.links.new(node.outputs['Color'],princ.inputs['Roughness'])
# Current metallic V12B material nodes are procedural/unsupported in GLB.
# Approved metallic minimum is 0.98, so preserve its physically plausible
# scalar value in game while avoiding Blender-only nodes.
for mat in materials:
    if mat==blade:
        princ=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        for link in tuple(princ.inputs['Metallic'].links):mat.node_tree.links.remove(link)
        princ.inputs['Metallic'].default_value=0.98
# These have already been used for real 32-bit HDRI-rendered approved V12B views.
# Export only model mesh, no key/rim lights/cameras/world content.
bpy.ops.object.select_all(action='DESELECT')
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
glb=out/'Genesis_Sword_Iron_V03_V175_V12B_PBR_WebGL_CANDIDATE.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,
                           export_animations=False,export_yup=True,
                           export_normals=True,export_materials='EXPORT',export_texcoords=True)
d=glb.read_bytes()
assert d[:4]==b'glTF' and struct.unpack_from('<I',d,4)[0]==2 and struct.unpack_from('<I',d,8)[0]==len(d)
jlen,ctype=struct.unpack_from('<I4s',d,12)
assert ctype==b'JSON'
gltf=json.loads(d[20:20+jlen])
assert gltf.get('meshes') and gltf.get('materials') and gltf.get('images')
assert len(gltf.get('meshes',[]))>=1
report={
 'asset':'Genesis Sword V03 Iron V175 V12B',
 'status':'EXPERIMENTAL_NOT_APPROVED_FOR_GAME',
 'source_sha256':EXACT_SOURCE,'approved_preset':'presets/approved/Genesis_Espada_V03_Hierro_V175_V12B.json',
 'source_geometry_triangles':tr,'geometry_unchanged':True,
 'blender':bpy.app.version_string,'renderer':'Cycles',
 'hdri':'studio_small_09_4k.exr','hdri_sha256':EXACT_HDRI,
 'hdri_bits_per_channel':32,'hdri_dimensions':list(im.size),
 'v12b_roughness_multiplier':0.34,'v12b_oxidation_roughness':0.10,
 'v12b_game_metallic':0.98,'blender_procedural_roughness_baked_to_uv':True,
 'baked_texture_bits_per_channel':8,
 'game_glb':glb.name,'glb_bytes':len(d),'glb_sha256':hashlib.sha256(d).hexdigest(),
 'gltf_mesh_count':len(gltf['meshes']),'gltf_material_count':len(gltf['materials']),
 'gltf_image_count':len(gltf['images']),
 'game_integrated':False,'visual_approved_for_mercenary':False,
 'caution':'Verify V12B actual imported GLB appearance. Do not confuse float32 EXR HDRI used for Cycles rendering with 8bit PBR textures used for WebGL.',
 'render_refs':['V12_V175_Color_J_Rugosidad034_Hero.png','V12_V175_Color_J_Rugosidad042_Detalle_Filo.png']
}
(out/'V12B_web_export_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('GENESIS_SWORD_V12B_GLTF_EXPORT',json.dumps(report),flush=True)
