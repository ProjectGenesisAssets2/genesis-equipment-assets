#!/usr/bin/env python3
"""Render the *exact* Genesis V03 sword using Blender Cycles and real EXR HDRI.

The source GLB remains byte-identical. Render variants adjust only material-node connections in memory to compare the iron palette and ORIGINAL Fab metallic texture.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view

EXPECTED='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def bounds(items):
    p=[o.matrix_world@Vector(c) for o in items for c in o.bound_box]
    return (Vector(tuple(min(v[i] for v in p) for i in range(3))),
            Vector(tuple(max(v[i] for v in p) for i in range(3))))

def lamp(name,location,target,power,width,height,color=(1,1,1)):
    obj=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'))
    bpy.context.collection.objects.link(obj)
    obj.location=location;aim(obj,target)
    obj.data.shape='RECTANGLE';obj.data.size=width;obj.data.size_y=height;obj.data.energy=power;obj.data.color=color

def setup_world(path,strength=.92,rotation=0):
    image=bpy.data.images.load(str(path),check_existing=True)
    if image.size[0]<1024 or image.size[1]<512:
        raise ValueError('HDRI EXR low resolution '+str(tuple(image.size)))
    if image.file_format!='OPEN_EXR':
        raise ValueError('Expected OPEN_EXR not '+image.file_format)
    # Blender reports depth 48 for 16-bit half float RGB and 96 for float32 RGB.
    print('GENESIS_HDRI_EXR',image.name,'bits_per_pixel',image.depth,'dimensions',tuple(image.size),flush=True)
    w=bpy.data.worlds.new('Studio Small 09 — real HDRI EXR')
    w.use_nodes=True;bpy.context.scene.world=w
    tree=w.node_tree;tree.nodes.clear()
    tex=tree.nodes.new('ShaderNodeTexEnvironment')
    tex.name='STUDIO_SMALL_09_EXR_ORIGINAL';tex.image=image;tex.location=(-480,100)
    geom=tree.nodes.new('ShaderNodeTexCoord');geom.location=(-900,100)
    rot=tree.nodes.new('ShaderNodeMapping');rot.location=(-700,100);rot.inputs['Rotation'].default_value[2]=rotation
    hdri=tree.nodes.new('ShaderNodeBackground');hdri.name='HDRI_FOR_REFLECTIONS_AND_LIGHTING';hdri.inputs['Strength'].default_value=strength;hdri.location=(-240,120)
    dark=tree.nodes.new('ShaderNodeBackground');dark.name='DARK_BACKGROUND_CAMERA_ONLY';dark.inputs['Color'].default_value=(0.012,0.017,0.027,1);dark.inputs['Strength'].default_value=1;dark.location=(-240,-150)
    lightpath=tree.nodes.new('ShaderNodeLightPath');lightpath.location=(-500,-270)
    mix=tree.nodes.new('ShaderNodeMixShader');mix.location=(0,120)
    output=tree.nodes.new('ShaderNodeOutputWorld');output.location=(240,120)
    tree.links.new(geom.outputs['Generated'] if False else geom.outputs['Generated'] if False else geom.outputs['Normal'],rot.inputs['Vector'])
    # Use generated texture coordinates for spherical environment? Environment uses world direction:
    tree.links.remove(rot.inputs['Vector'].links[0])
    tree.links.new(geom.outputs['Generated'] if False else geom.outputs['Reflection'],rot.inputs['Vector'])
    # Texture Coordinate -> Generated is inappropriate for World; use Generated? Instead use Texture Coordinate: Generated in world unsupported.
    tree.links.remove(rot.inputs['Vector'].links[0])
    tree.links.new(geom.outputs['Normal'],rot.inputs['Vector'])
    tree.links.new(rot.outputs['Vector'],tex.inputs['Vector'])
    tree.links.new(tex.outputs['Color'],hdri.inputs['Color'])
    tree.links.new(lightpath.outputs['Is Camera Ray'],mix.inputs[0])
    tree.links.new(hdri.outputs[0],mix.inputs[1])
    tree.links.new(dark.outputs[0],mix.inputs[2])
    tree.links.new(mix.outputs[0],output.inputs['Surface'])
    return image

def render_one(scene,objects,target,outpath,label,view_dir):
    camera=bpy.data.objects.new('CAM_'+label,bpy.data.cameras.new('CAM_'+label))
    bpy.context.collection.objects.link(camera)
    camera.location=target+Vector(view_dir)
    aim(camera,target);scene.camera=camera
    camera.data.type='ORTHO';camera.data.ortho_scale=2.7;camera.data.lens=60
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    p=[world_to_camera_view(scene,camera,v) for v in pts]
    minx=min(v.x for v in p);maxx=max(v.x for v in p)
    miny=min(v.y for v in p);maxy=max(v.y for v in p)
    camera.data.ortho_scale*=max((maxx-minx)/.75,(maxy-miny)/.80,0.7)
    bpy.context.view_layer.update()
    points=[world_to_camera_view(scene,camera,v) for v in pts]
    bb=[min(v.x for v in points),max(v.x for v in points),min(v.y for v in points),max(v.y for v in points)]
    print('GENESIS_CAMERA',label,'projected',bb,flush=True)
    if bb[0]<.02 or bb[1]>.98 or bb[2]<.02 or bb[3]>.98:
        raise ValueError('Bad camera framing '+str(bb))
    outpath.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(outpath)
    bpy.ops.render.render(write_still=True)
    if not outpath.exists() or outpath.stat().st_size<50000:
        raise RuntimeError('Render not saved '+str(outpath))
    return {'file':outpath.name,'bytes':outpath.stat().st_size,'camera_bounds':bb}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--hdri',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--samples',type=int,default=96)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    sha=hashlib.sha256(a.input.read_bytes()).hexdigest()
    if sha!=EXPECTED: raise ValueError('Exact V03 GLB hash mismatch '+sha)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(a.input.resolve()))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    tri=sum(len(o.data.loop_triangles) for o in meshes)
    if tri!=2150: raise ValueError('Source geometry changed! '+str(tri))
    mats={m.name:m for o in meshes for m in o.data.materials if m}
    if len(mats)<2: raise ValueError('Missing V03 materials '+str(list(mats)))
    for material in mats.values():
        if not material.use_nodes: raise ValueError('Non-node PBR material')
        images=[n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
        if not images: raise ValueError('Material has no original image textures: '+material.name)
    bmin,bmax=bounds(meshes)
    dimensions=bmax-bmin;long_axis=max(range(3),key=lambda k:dimensions[k])
    axis=Vector(tuple(float(k==long_axis) for k in range(3)))
    # Place original sword with blade pointing diagonally upward across the image.
    desired=Vector((.32,0,.948)).normalized()
    turn=axis.rotation_difference(desired).to_matrix().to_4x4()
    center=(bmin+bmax)/2
    original_matrices={o.name:o.matrix_world.copy() for o in meshes}
    for o in meshes:
        o.parent=None
        o.matrix_world=turn@Matrix.Translation(-center)@original_matrices[o.name]
    bpy.context.view_layer.update()
    low,high=bounds(meshes);target=(low+high)/2
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=a.samples
    scene.cycles.use_adaptive_sampling=True
    bpy.context.view_layer.cycles.use_denoising=True
    scene.render.resolution_x=1200
    scene.render.resolution_y=1500
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-0.25
    scene.render.engine='CYCLES'
    # Real HDRI supplies illumination and reflections; softboxes shape metal highlights.
    environment=setup_world(a.hdri,strength=.60,rotation=.45)
    lamp('Wide key reflection',(-1.8,-2.0,3),target,155,2.2,3.2)
    lamp('Long blade strip',(1.5,-1.3,2.8),target,90,0.52,3.0)
    lamp('Rim separation',(1.6,1.7,1.5),target,135,1.0,2.4)
    lamp('Hilt warm fill',(-.9,-1.6,-1.0),target,35,1.4,1.6,(1,.88,.72))
    # Material comparison, all textures come embedded in the exact GLB.
    blade=next((m for name,m in mats.items() if 'Genesis_Iron_Blade' in name),None)
    if blade is None: raise ValueError('V175 blade material missing')
    default=next((m for name,m in mats.items() if name=='DefaultMaterial'),None)
    if default is None: raise ValueError('Original Fab material missing')
    principled=next((n for n in blade.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if principled is None: raise ValueError('V175 Principled BSDF missing')
    original_metal_image=next((n.image for n in default.node_tree.nodes
        if n.type=='TEX_IMAGE' and n.image and n.image.name=='Image_1'),None)
    original_v175_orm=next((n for n in blade.node_tree.nodes
        if n.type=='TEX_IMAGE' and n.image and 'Genesis_V175_Hierro_ORM_2K' in n.image.name),None)
    baked=next((n for n in blade.node_tree.nodes
        if n.type=='TEX_IMAGE' and n.image and 'Genesis_V175_APPROVED_PALETTE_BAKED_V03' in n.image.name),None)
    original_raw_iron=next((n.image for n in blade.node_tree.nodes
        if n.type=='TEX_IMAGE' and n.image and 'Genesis_V175_Hierro_Color_2K' in n.image.name),None)
    if not all((original_metal_image,original_v175_orm,baked,original_raw_iron)):
        raise ValueError('Missing original Fab metallic, V175 ORM or baked/raw V175 colors')
    orig_metal_links=[(l.from_node.name,l.from_socket.name) for l in principled.inputs['Metallic'].links]
    orig_rough_links=[(l.from_node.name,l.from_socket.name) for l in principled.inputs['Roughness'].links]
    results=[]
    v=(0,-4.6,.65)
    results.append(render_one(scene,meshes,target,a.output_dir/'A_V175_Intact_LessLight.png','A_V175_intact',v))
    # B: keep V175 iron base color, V175 roughness and normal; use only
    # channel B of the ORIGINAL Fab-packed metallic-roughness map for metallicity.
    tree=blade.node_tree
    source=tree.nodes.new('ShaderNodeTexImage')
    source.name='ORIGINAL_FAB_ORM_METALLIC_ONLY';source.image=original_metal_image
    source.image.colorspace_settings.name='Non-Color'
    if original_v175_orm.inputs['Vector'].is_linked:
        link=original_v175_orm.inputs['Vector'].links[0]
        tree.links.new(link.from_socket,source.inputs['Vector'])
    split=tree.nodes.new('ShaderNodeSeparateColor')
    split.mode='RGB';split.name='ORIGINAL_FAB_ORM_SPLIT'
    tree.links.new(source.outputs['Color'],split.inputs['Color'])
    tree.links.new(split.outputs['Blue'],principled.inputs['Metallic'])
    metallic_links=[(l.from_node.name,l.from_socket.name) for l in principled.inputs['Metallic'].links]
    if not metallic_links or metallic_links[0][0]!='ORIGINAL_FAB_ORM_SPLIT':
        raise RuntimeError('Original metallic layer not wired successfully')
    results.append(render_one(scene,meshes,target,a.output_dir/'B_OriginalMetal_V175Color.png','B_original_metal',v))
    # C: compare original V175 iron base color to experimental palette-baked V03.
    baked.image=original_raw_iron
    results.append(render_one(scene,meshes,target,a.output_dir/'C_OriginalMetal_RawV175IronColor.png','C_raw_iron',v))
    baked.image=next(n.image for n in bpy.data.images if n.name=='Genesis_V175_APPROVED_PALETTE_BAKED_V03')
    report={'blender':bpy.app.version_string,'renderer':'Cycles','samples':a.samples,'source_sha256':sha,
       'geometry_triangles':tri,'meshes':len(meshes),'original_materials':list(mats),
       'pbr_source_textures':{n: [x.image.name for x in m.node_tree.nodes if x.type=='TEX_IMAGE' and x.image] for n,m in mats.items()},
       'hdri_name':a.hdri.name,'hdri_sha256':hashlib.sha256(a.hdri.read_bytes()).hexdigest(),
       'hdri_image_depth_bpp':environment.depth,'hdri_dimensions':list(environment.size),
       'source_glb_modified':False,'test_material_nodes_modified_in_memory':True,
       'baseline_metallic_link':orig_metal_links,'baseline_roughness_link':orig_rough_links,
       'original_metallic_layer':'Image_1 packed ORM blue channel',
       'corrected_metallic_link':metallic_links,
       'variant_a':'V175 baked palette + V175 ORM + V175 normal, original connections',
       'variant_b':'V175 baked palette and V175 roughness/normal, original Fab packed ORM blue-channel metallic',
       'variant_c':'V175 raw iron color 2K, V175 roughness/normal and original Fab metallic',
       'renders':results}
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'render_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_REAL_BLENDER_HDRI_RENDER_COMPLETE',json.dumps(report),flush=True)

if __name__=='__main__':main()
