#!/usr/bin/env python3
"""Matched-light original Fab sword, V175/E, and two source-texture normal-map hybrids.

The original source GLB is byte-identical across four render passes; the original Fab look is reproduced by its unchanged original material, from the same original embedded texture images and identical geometry/UVs.
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
    # Original Fab source and Genesis V03 were audited locally:
    # 1406 vertex POSITION, NORMAL, TANGENT, UV0 exact match;
    # 2150 triangles identical, only split into 2052 and 98 material subsets.
    blade=next((m for name,m in mats.items() if 'Genesis_Iron_Blade' in name),None)
    default=next((m for name,m in mats.items() if name=='DefaultMaterial'),None)
    if blade is None or default is None: raise ValueError('Original Fab and V175 materials missing')
    bsdf=next((n for n in blade.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bsdf is None: raise ValueError('V175 material has no Principled BSDF')
    blade_base=next((n for n in blade.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and
         'Genesis_V175_APPROVED_PALETTE_BAKED_V03' in n.image.name),None)
    blade_normal=next((n for n in blade.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and
         'Genesis_V175_Hierro_Normal_2K' in n.image.name),None)
    blade_orm=next((n for n in blade.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and
         'Genesis_V175_Hierro_ORM_2K' in n.image.name),None)
    fab_base=next((n.image for n in default.node_tree.nodes if n.type=='TEX_IMAGE'
                   and n.image and n.image.name=='Image_0'),None)
    fab_orm=next((n.image for n in default.node_tree.nodes if n.type=='TEX_IMAGE'
                  and n.image and n.image.name=='Image_1'),None)
    fab_normal=next((n.image for n in default.node_tree.nodes if n.type=='TEX_IMAGE'
                     and n.image and n.image.name=='Image_2'),None)
    if not all((blade_base,blade_normal,blade_orm,fab_base,fab_orm,fab_normal)):
        raise ValueError('Missing original Fab or V175 embedded color/normal/ORM image')
    iron_base=load_unused_embedded_iron_image(a.input)
    original_normal_image=blade_normal.image
    original_baked_image=blade_base.image
    material_slots=[]
    for obj in meshes:
        for idx,material in enumerate(obj.data.materials):
            if material==blade: material_slots.append((obj,idx))
    if not material_slots: raise ValueError('No V175 blade polygons found')

    # Step 1: ORIGINAL Fab material on the blade mask, matching original glTF
    # from /free_medieval_sword.glb in source library. All mesh and UV data match.
    for obj,idx in material_slots: obj.data.materials[idx]=default
    bpy.context.view_layer.update()
    render_files=[]
    camera_view=(0,-4.6,.65)
    render_files.append(render_one(scene,meshes,target,a.output_dir/'01_Original_Fab_Material.png','01_original_fab',camera_view))
    for obj,idx in material_slots: obj.data.materials[idx]=blade
    bpy.context.view_layer.update()

    graph=blade.node_tree
    blade_base.image=iron_base

    # Use original Fab packed ORM texture blue=metallic, green=roughness.
    original_orm_node=graph.nodes.new('ShaderNodeTexImage')
    original_orm_node.name='Fab_Original_Packed_Metallic_Roughness'
    original_orm_node.image=fab_orm
    original_orm_node.image.colorspace_settings.name='Non-Color'
    if blade_orm.inputs['Vector'].is_linked:
        graph.links.new(blade_orm.inputs['Vector'].links[0].from_socket,original_orm_node.inputs['Vector'])
    original_channels=graph.nodes.new('ShaderNodeSeparateColor')
    original_channels.mode='RGB';original_channels.name='Fab_Original_ORM_Channels'
    graph.links.new(original_orm_node.outputs['Color'],original_channels.inputs['Color'])

    # Save original V175 roughness source before linking the E variation.
    if not bsdf.inputs['Roughness'].is_linked: raise ValueError('V175 roughness node disconnected')
    v175_roughness_socket=bsdf.inputs['Roughness'].links[0].from_socket
    rough_scale=graph.nodes.new('ShaderNodeMath')
    rough_scale.name='V175_Roughness_E_054';rough_scale.operation='MULTIPLY'
    rough_scale.use_clamp=True;rough_scale.inputs[1].default_value=.54
    graph.links.new(v175_roughness_socket,rough_scale.inputs[0])
    floor=graph.nodes.new('ShaderNodeMath')
    floor.name='Fab_Metallic_Floor_E_098';floor.operation='MAXIMUM'
    floor.inputs[1].default_value=.98
    graph.links.new(original_channels.outputs['Blue'],floor.inputs[0])

    # Step 2: exact E configuration, same HDRI, camera, light positions, exposure.
    graph.links.new(rough_scale.outputs[0],bsdf.inputs['Roughness'])
    graph.links.new(floor.outputs[0],bsdf.inputs['Metallic'])
    if blade_normal.image != original_normal_image: raise ValueError('V175 normal unexpectedly changed')
    render_files.append(render_one(scene,meshes,target,a.output_dir/'02_E_V175_Metal_Intenso.png','02_E_v175',camera_view))

    # Step 3: V175 iron color + ORIGINAL Fab normal + ORIGINAL Fab metal/rough.
    graph.links.new(original_channels.outputs['Green'],bsdf.inputs['Roughness'])
    graph.links.new(original_channels.outputs['Blue'],bsdf.inputs['Metallic'])
    blade_normal.image=fab_normal
    bpy.context.view_layer.update()
    render_files.append(render_one(scene,meshes,target,a.output_dir/'03_Hibrida_V175Color_NormalOriginal.png','03_v175color_fabnormal',camera_view))

    # Step 4: ORIGINAL Fab color + V175 normal + ORIGINAL Fab metal/rough.
    blade_base.image=fab_base
    blade_normal.image=original_normal_image
    bpy.context.view_layer.update()
    render_files.append(render_one(scene,meshes,target,a.output_dir/'04_Hibrida_ColorOriginal_NormalV175.png','04_fabcolor_v175normal',camera_view))

    # Do not export any modified 3D file; the original input remains identical.
    report={
        'blender':bpy.app.version_string,'render_engine':'Cycles','samples':a.samples,
        'source_sha256':sha,'input_sword_unmodified':True,
        'original_sword_geom_uv_verified_identical_locally':True,
        'triangles':tri,'imported_mesh_objects':len(meshes),
        'hdri':a.hdri.name,'hdr_bits_per_pixel':environment.depth,'hdr_resolution':list(environment.size),
        'camera_and_lights_identical_between_variants':True,
        'textures':{
            'original_fab_basecolor':fab_base.name,
            'original_fab_normal':fab_normal.name,
            'original_fab_metallic_roughness':fab_orm.name,
            'v175_iron_basecolor':iron_base.name,
            'v175_normal':original_normal_image.name,
            'v175_packed_metallic_roughness':blade_orm.image.name},
        'variants':{
            '01_Original_Fab_Material':'Original Fab DefaultMaterial (same as source sword) across whole sword',
            '02_E_V175_Metal_Intenso':'V175 iron color + V175 normal + V175 roughness x0.54, original Fab metallic blue channel min 0.98',
            '03_Hibrida_V175Color_NormalOriginal':'V175 iron color + original Fab normal + unmodified original Fab ORM metallic blue/roughness green',
            '04_Hibrida_ColorOriginal_NormalV175':'original Fab basecolor + V175 normal + unmodified original Fab ORM metallic blue/roughness green',
        },
        'renders':render_files}
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'render_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_4WAY_ORIGINAL_NORMAL_COMPARE',json.dumps(report),flush=True)

if __name__=='__main__':main()
