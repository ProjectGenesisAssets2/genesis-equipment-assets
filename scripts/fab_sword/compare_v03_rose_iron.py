#!/usr/bin/env python3
"""Render real V175 oxidized rose-iron blade palette candidates, using original Fab normals.

The source GLB remains byte-identical. Render variants adjust only material-node connections in memory to compare the iron palette and ORIGINAL Fab metallic texture.
"""
import argparse,hashlib,json,math,sys,struct,tempfile
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


def load_unused_embedded_iron_image(glb_path):
    # Original V175 color is embedded in GLB but is unused by baked-palette V03.
    payload=glb_path.read_bytes()
    offset=12;metadata=None;binary=None
    while offset<len(payload):
        n,tag=struct.unpack_from('<II',payload,offset);offset+=8
        part=payload[offset:offset+n];offset+=n
        if tag==0x4E4F534A: metadata=json.loads(part)
        if tag==0x004E4942: binary=part
    if metadata is None or binary is None:raise RuntimeError('Invalid input GLB')
    match=next((image for image in metadata['images'] if image.get('name')=='Genesis_V175_Hierro_Color_2K'),None)
    if not match:raise RuntimeError('Missing original embedded V175 iron color')
    view=metadata['bufferViews'][match['bufferView']]
    payload_image=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
    tmp=tempfile.NamedTemporaryFile(suffix='.png',delete=False)
    try:
        tmp.write(payload_image);tmp.close()
        image=bpy.data.images.load(tmp.name,check_existing=False)
        image.name='Genesis_V175_Hierro_Color_2K_FROM_EXACT_GLB'
        image.pack()
        return image
    finally:
        Path(tmp.name).unlink(missing_ok=True)

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
    blade=next((m for name,m in mats.items() if 'Genesis_Iron_Blade' in name),None)
    default=next((m for name,m in mats.items() if name=='DefaultMaterial'),None)
    if not blade or not default: raise ValueError('Missing source V175/Fab materials')
    tree=blade.node_tree
    bsdf=next((n for n in tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    baked=next((n for n in tree.nodes if n.type=='TEX_IMAGE' and n.image and
                'Genesis_V175_APPROVED_PALETTE_BAKED_V03' in n.image.name),None)
    normal=next((n for n in tree.nodes if n.type=='TEX_IMAGE' and n.image and
                'Genesis_V175_Hierro_Normal_2K' in n.image.name),None)
    v175_orm=next((n for n in tree.nodes if n.type=='TEX_IMAGE' and n.image and
                'Genesis_V175_Hierro_ORM_2K' in n.image.name),None)
    fab_orm=next((n.image for n in default.node_tree.nodes if n.type=='TEX_IMAGE'
                  and n.image and n.image.name=='Image_1'),None)
    fab_normal=next((n.image for n in default.node_tree.nodes if n.type=='TEX_IMAGE'
                     and n.image and n.image.name=='Image_2'),None)
    if not all((bsdf,baked,normal,v175_orm,fab_orm,fab_normal)):
        raise ValueError('Missing source V175/Fab texture or Principled BSDF')
    raw=load_unused_embedded_iron_image(a.input)
    original_baked=baked.image
    original_normal=normal.image
    if not bsdf.inputs['Base Color'].is_linked: raise ValueError('No source base color shader link')
    normal.image=fab_normal
    # Restore the original normal structure for the prominent central blade ridge.
    # E's metal reflection and roughness are held constant in ALL variants.
    metallic=tree.nodes.new('ShaderNodeTexImage')
    metallic.name='FAB_SOURCE_METALLIC';metallic.image=fab_orm
    metallic.image.colorspace_settings.name='Non-Color'
    if v175_orm.inputs['Vector'].is_linked:
        tree.links.new(v175_orm.inputs['Vector'].links[0].from_socket,metallic.inputs['Vector'])
    split=tree.nodes.new('ShaderNodeSeparateColor')
    split.mode='RGB';split.name='FAB_SOURCE_ORM_SPLIT'
    tree.links.new(metallic.outputs['Color'],split.inputs['Color'])
    metal_floor=tree.nodes.new('ShaderNodeMath')
    metal_floor.name='IRON_E_METALLIC_MIN';metal_floor.operation='MAXIMUM'
    metal_floor.inputs[1].default_value=.98
    tree.links.new(split.outputs['Blue'],metal_floor.inputs[0])
    tree.links.new(metal_floor.outputs[0],bsdf.inputs['Metallic'])
    if not bsdf.inputs['Roughness'].is_linked: raise ValueError('Source V175 roughness missing')
    rough_source=bsdf.inputs['Roughness'].links[0].from_socket
    rough_mult=tree.nodes.new('ShaderNodeMath')
    rough_mult.name='IRON_E_ROUGHNESS_SCALE';rough_mult.operation='MULTIPLY'
    rough_mult.use_clamp=True;rough_mult.inputs[1].default_value=.54
    tree.links.new(rough_source,rough_mult.inputs[0])
    tree.links.new(rough_mult.outputs[0],bsdf.inputs['Roughness'])
    # Two color maps are already embedded in this exact source:
    # raw grey iron V175 and approved-palette baked warm/rose iron V175.
    # Mix ONLY their color, never the entire shader or normal/roughness.
    raw_node=tree.nodes.new('ShaderNodeTexImage')
    raw_node.name='V175_UNCOLOURED_GREY_IRON'
    raw_node.image=raw
    if baked.inputs['Vector'].is_linked:
        tree.links.new(baked.inputs['Vector'].links[0].from_socket,raw_node.inputs['Vector'])
    blend=tree.nodes.new('ShaderNodeMixRGB')
    blend.name='V175_WARM_IRON_OXIDE_BLEND'
    blend.blend_type='MIX';blend.use_clamp=True
    tree.links.new(raw_node.outputs['Color'],blend.inputs[1])
    tree.links.new(baked.outputs['Color'],blend.inputs[2])
    tree.links.new(blend.outputs[0],bsdf.inputs['Base Color'])
    v=(0,-4.6,.65)
    results=[]
    variants=[
        ('A_gris_hierro_ref',0.0),
        ('B_vetas_rosadas_sutiles',0.27),
        ('C_vetas_rosadas_naturales',0.52),
        ('D_oxidacion_marcada',0.78),
    ]
    for title,factor in variants:
        blend.inputs[0].default_value=factor
        bpy.context.view_layer.update()
        results.append(render_one(scene,meshes,target,a.output_dir/(title+'.png'),title,v))
    # Never export the copyrighted original GLB or any modified GLB.
    report={
      'blender':bpy.app.version_string,'renderer':'Cycles','samples':a.samples,
      'source_sha256':sha,'source_glb_modified':False,
      'geometry_triangles':tri,'mesh_objects':len(meshes),
      'real_32bit_exr_hdri':a.hdri.name,'hdri_image_depth_bpp':environment.depth,
      'original_fab_normal_image':fab_normal.name,
      'normal_shader_source':normal.name,
      'raw_v175_iron':raw.name,
      'warm_v175_iron_approved_palette_embedded':original_baked.name,
      'e_metallic_minimum':.98,'e_v175_roughness_multiplier':.54,
      'material_variants':[{'name':name,'oxidized_palette_fraction':f} for name,f in variants],
      'blade_shape_changed':False,'rendered':results}
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'render_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_V175_ROSE_IRON_RENDER_COMPLETE',json.dumps(report),flush=True)

if __name__=='__main__': main()
