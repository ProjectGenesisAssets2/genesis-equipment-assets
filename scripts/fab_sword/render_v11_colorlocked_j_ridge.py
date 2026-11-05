#!/usr/bin/env python3
"""V11: Recover approved candidate J's ridge reflections while keeping EXACT V10 V175 iron BASE COLOR.
Blender 4.5.13 LTS + original 32-bit/channel RGB EXR + unchanged 2150-triangle GLB.
Only in-memory normal/roughness/metallic connections on iron blade, plus an area strip.
No VFX and no writeback to original model.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v03_v175_hdri32_master_v10 as v10
import render_v03_real_hdri32 as studio

EXPECTED_GLB='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
EXPECTED_HDR='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'

def node_image(mat,fragment):
    return next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and fragment in n.image.name),None)

def render(scene,cam,name,out):
    scene.camera=bpy.data.objects[cam]
    scene.render.filepath=str((out/name).resolve())
    bpy.ops.render.render(write_still=True)
    p=out/name
    if not p.exists() or p.stat().st_size<100000:raise RuntimeError('Real Cycles file not written '+str(p))
    return {'file':name,'bytes':p.stat().st_size}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--hdri',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--samples',type=int,default=96)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if hashlib.sha256(a.input.read_bytes()).hexdigest()!=EXPECTED_GLB:raise RuntimeError('wrong sword GLB')
    if hashlib.sha256(a.hdri.read_bytes()).hexdigest()!=EXPECTED_HDR:raise RuntimeError('wrong RGB 32bpc HDRI')
    # First generate the actual V10 baseline with unchanged source and identical camera/light.
    v10.main()
    scene=bpy.context.scene
    mats={m.name:m for obj in scene.objects if obj.type=='MESH'
          for m in obj.data.materials if m}
    blade=next((m for k,m in mats.items() if 'Iron_Blade_V175' in k),None)
    fab=mats.get('DefaultMaterial')
    if blade is None or fab is None:raise RuntimeError('missing exact blade and Fab original')
    tree=blade.node_tree
    bsdf=next((n for n in tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    normal_node=node_image(blade,'Genesis_V175_Hierro_Normal_2K')
    v175_orm=node_image(blade,'Genesis_V175_Hierro_ORM_2K')
    fab_orm=node_image(fab,'Image_1')
    fab_normal=node_image(fab,'Image_2')
    if any(x is None for x in [bsdf,normal_node,v175_orm,fab_orm,fab_normal]):
        raise RuntimeError('required authentic PBR maps missing')
    if not bsdf.inputs['Base Color'].is_linked:
        raise RuntimeError('V10 V175 color must remain physically sourced from texture')
    base_link=bsdf.inputs['Base Color'].links[0].from_socket
    baseline_color_node=base_link.node.name
    baseline_color_socket=base_link.name
    original_normal_image=normal_node.image.name
    if not bsdf.inputs['Roughness'].is_linked:
        raise RuntimeError('V175 mapped roughness not connected')
    v175_rough_source=bsdf.inputs['Roughness'].links[0].from_socket
    # The J candidate's surface BRDF: original Fab normal restores the ridge,
    # authentic Fab ORM metallic map plus minimum 0.98 and V175 roughness * 0.49.
    # Iron palette and its Base Color connection are left BYTE-EXACTLY as V10.
    normal_node.image=fab_normal.image
    metallic=tree.nodes.new('ShaderNodeTexImage')
    metallic.name='V11_APPROVED_J_ORIGINAL_FAB_METALLIC'
    metallic.image=fab_orm.image
    metallic.image.colorspace_settings.name='Non-Color'
    if v175_orm.inputs['Vector'].is_linked:
        tree.links.new(v175_orm.inputs['Vector'].links[0].from_socket,metallic.inputs['Vector'])
    split=tree.nodes.new('ShaderNodeSeparateColor')
    split.mode='RGB';split.name='V11_FAB_METAL_RGB'
    tree.links.new(metallic.outputs['Color'],split.inputs['Color'])
    metal_floor=tree.nodes.new('ShaderNodeMath')
    metal_floor.operation='MAXIMUM';metal_floor.name='V11_J_METALLIC_MIN_098'
    metal_floor.inputs[1].default_value=.98
    tree.links.new(split.outputs['Blue'],metal_floor.inputs[0])
    tree.links.new(metal_floor.outputs[0],bsdf.inputs['Metallic'])
    rough=tree.nodes.new('ShaderNodeMath')
    rough.operation='MULTIPLY';rough.name='V11_J_V175_ROUGHNESS_MULT_049'
    rough.use_clamp=True;rough.inputs[1].default_value=.49
    tree.links.new(v175_rough_source,rough.inputs[0])
    tree.links.new(rough.outputs[0],bsdf.inputs['Roughness'])
    if bsdf.inputs['Base Color'].links[0].from_socket != base_link:
        raise RuntimeError('V175 ORIGINAL BASE COLOR WAS MODIFIED')
    meshes=[o for o in scene.objects if o.type=='MESH']
    low,high=studio.bounds(meshes)
    target=(low+high)/2
    studio.lamp('V11_J_LONGITUDINAL_NERVIO_STRIP',(-.35,-2.3,2.15),target,85,.24,2.8)
    light=bpy.data.objects['V11_J_LONGITUDINAL_NERVIO_STRIP']
    bpy.context.view_layer.update()
    out=a.output_dir
    results=[render(scene,'CAM_hero','V11_V175_Color_Original_J_Nervio_Hero.png',out)]
    results.append(render(scene,'CAM_three_quarters','V11_V175_Color_Original_J_Nervio_TresCuartos.png',out))
    results.append(render(scene,'CAM_BLADE_MACRO','V11_V175_Color_Original_J_Nervio_Filo_Detalle.png',out))
    # A lighting-only brighter strip variant to distinguish reflectivity from overlighting.
    light.data.energy=145
    results.append(render(scene,'CAM_hero','V11_V175_Color_Original_J_Nervio_Strip145_Hero.png',out))
    audit={
      'schema':'Genesis_V11_V175_ColorLocked_J_Nervio_Reflections',
      'status':'experimental_visual_approval_pending',
      'source_sha256':EXPECTED_GLB,'source_glb_modified':False,
      'triangles':2150,'renderer':'Cycles','blender':bpy.app.version_string,
      'cycles_samples':a.samples,'hdri_sha256':EXPECTED_HDR,
      'hdri_dimensions':[4096,2048],'hdri_rgb_bits_per_channel':32,
      'V10_color_socket_unchanged':True,
      'V10_color_node':baseline_color_node,'V10_color_socket':baseline_color_socket,
      'normal_from':'Fab Image_2','normal_previous':original_normal_image,
      'metallic_from':'Fab Image_1 ORM blue + floor 0.98',
      'roughness_from':'V175 ORM green * 0.49',
      'new_strip_width_m':.24,'new_strip_length_m':2.8,'new_strip_watts':[85,145],
      'additional_texture_or_palette_tint':False,
      'additional_channel_vfx':False,
      'J_reference':'v03_fine_oxide_reflection_v02.py; J had Fab normal, metallic min .98, roughness mult .49, plus oxide patina. V11 preserves V10 Base Color and does NOT copy J iron tone .72.',
      'previous_baseline':'V10 original PBR, with same full rig lights HDRI and cameras',
      'rendered_files':results
    }
    (out/'v11_surface_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print('GENESIS_V11_COLOR_LOCKED_J_RIDGE_REFLECTION_RENDER_COMPLETE',json.dumps(audit),flush=True)

if __name__=='__main__':main()
