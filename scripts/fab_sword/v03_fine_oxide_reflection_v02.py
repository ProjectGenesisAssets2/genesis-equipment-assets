#!/usr/bin/env python3
"""Render incremental Genesis sword V03 iron patina V02, matched Studio Small 09 HDRI.

Source V03 GLB remains byte-identical and is never re-exported. All iron colors come from embedded V175 maps; normal and metallicity come from the original Fab map. Candidate color and oxide masks change in memory only.
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
    default=next((m for name,m in mats.items() if m.name=='DefaultMaterial'),None)
    if not blade or not default: raise ValueError('V03 blade/original Fab missing')
    tree=blade.node_tree
    shader=next((n for n in tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
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
    if not all((shader,baked,normal,v175_orm,fab_orm,fab_normal)):
        raise ValueError('Missing approved V175/Fab normal/ORM PBR textures')
    raw=load_unused_embedded_iron_image(a.input)
    normal.image=fab_normal
    # Preserve Fab's detail/longitudinal blade ridge; original sword geometry unchanged.
    metallic=tree.nodes.new('ShaderNodeTexImage')
    metallic.name='FAB_SOURCE_ORM_METALLIC'
    metallic.image=fab_orm
    metallic.image.colorspace_settings.name='Non-Color'
    if v175_orm.inputs['Vector'].is_linked:
        tree.links.new(v175_orm.inputs['Vector'].links[0].from_socket,metallic.inputs['Vector'])
    fab_channels=tree.nodes.new('ShaderNodeSeparateColor')
    fab_channels.name='FAB_ORM_CHANNELS'
    fab_channels.mode='RGB'
    tree.links.new(metallic.outputs['Color'],fab_channels.inputs['Color'])
    metal_floor=tree.nodes.new('ShaderNodeMath')
    metal_floor.name='FAB_METAL_MIN_098'
    metal_floor.operation='MAXIMUM';metal_floor.inputs[1].default_value=.98
    tree.links.new(fab_channels.outputs['Blue'],metal_floor.inputs[0])
    if not shader.inputs['Roughness'].is_linked: raise ValueError('V175 roughness input disconnected')
    v175_rough=shader.inputs['Roughness'].links[0].from_socket
    rough_scaled=tree.nodes.new('ShaderNodeMath')
    rough_scaled.name='IRON_MAIN_ROUGHNESS'
    rough_scaled.operation='MULTIPLY';rough_scaled.use_clamp=True
    tree.links.new(v175_rough,rough_scaled.inputs[0])
    # Blend two already embedded authentic V175 iron palettes; NO synthetic RGB tint.
    raw_node=tree.nodes.new('ShaderNodeTexImage')
    raw_node.name='IRON_V175_GREY_RAW'
    raw_node.image=raw
    if baked.inputs['Vector'].is_linked:
        tree.links.new(baked.inputs['Vector'].links[0].from_socket,raw_node.inputs['Vector'])
    palette=tree.nodes.new('ShaderNodeMixRGB')
    palette.name='APPROVED_V175_WARM_PATINA_BLEND'
    palette.blend_type='MIX';palette.use_clamp=True
    tree.links.new(raw_node.outputs['Color'],palette.inputs[1])
    tree.links.new(baked.outputs['Color'],palette.inputs[2])
    # Luminance calibration ONLY of V175 iron palette; ingot/source texture remains unchanged.
    iron_tone=tree.nodes.new('ShaderNodeMixRGB')
    iron_tone.name='APPROVED_V175_IRON_TONE_CALIBRATION'
    iron_tone.blend_type='MULTIPLY';iron_tone.use_clamp=True
    iron_tone.inputs[0].default_value=1.0
    tree.links.new(palette.outputs['Color'],iron_tone.inputs[1])
    tree.links.new(iron_tone.outputs['Color'],shader.inputs['Base Color'])
    # The stock C texture blends broad color blobs. For V01 masks use
    # anisotropic low-frequency noise on Generated local mesh coordinates:
    # many changes across blade width but slow variation along its long axis.
    texcoord=tree.nodes.new('ShaderNodeTexCoord')
    texcoord.name='BLADE_LOCAL_COORDS'
    axis=tree.nodes.new('ShaderNodeVectorMath')
    axis.name='ELONGATED_IRON_FORGING_STREAK_COORDS';axis.operation='MULTIPLY'
    axis.inputs[1].default_value=(27.0,3.2,8.0)
    tree.links.new(texcoord.outputs['Generated'],axis.inputs[0])
    noise=tree.nodes.new('ShaderNodeTexNoise')
    noise.name='IRON_PATINA_WEAR_MASK_NOISE'
    noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=1.0
    noise.inputs['Detail'].default_value=3.0
    noise.inputs['Roughness'].default_value=.67
    noise.inputs['Distortion'].default_value=.12
    tree.links.new(axis.outputs['Vector'],noise.inputs['Vector'])
    threshold=tree.nodes.new('ShaderNodeMapRange')
    threshold.name='IRON_NARROW_VEIN_SELECTION'
    threshold.interpolation_type='SMOOTHSTEP';threshold.clamp=True
    threshold.inputs['From Min'].default_value=.52
    threshold.inputs['From Max'].default_value=.66
    threshold.inputs['To Min'].default_value=0.0
    threshold.inputs['To Max'].default_value=1.0
    tree.links.new(noise.outputs['Fac'],threshold.inputs['Value'])
    oxide_strength=tree.nodes.new('ShaderNodeMath')
    oxide_strength.name='IRON_OXIDE_COVERAGE'
    oxide_strength.operation='MULTIPLY';oxide_strength.use_clamp=True
    tree.links.new(threshold.outputs['Result'],oxide_strength.inputs[0])
    oxide_base=tree.nodes.new('ShaderNodeMath')
    oxide_base.name='IRON_OXIDE_BASELINE'
    oxide_base.operation='ADD';oxide_base.use_clamp=True
    tree.links.new(oxide_strength.outputs[0],oxide_base.inputs[0])
    tree.links.new(oxide_base.outputs[0],palette.inputs[0])
    # Oxide appears more matte in stained areas while clean iron stays polished.
    rough_oxide=tree.nodes.new('ShaderNodeMath')
    rough_oxide.name='OXIDE_ADDITIONAL_ROUGHNESS'
    rough_oxide.operation='MULTIPLY';rough_oxide.use_clamp=True
    tree.links.new(threshold.outputs['Result'],rough_oxide.inputs[0])
    rough_final=tree.nodes.new('ShaderNodeMath')
    rough_final.name='LOCAL_OXIDE_ROUGHNESS_ADDED'
    rough_final.operation='ADD';rough_final.use_clamp=True
    tree.links.new(rough_scaled.outputs[0],rough_final.inputs[0])
    tree.links.new(rough_oxide.outputs[0],rough_final.inputs[1])
    tree.links.new(rough_final.outputs[0],shader.inputs['Roughness'])
    metal_oxide=tree.nodes.new('ShaderNodeMath')
    metal_oxide.name='IRON_OXIDE_METAL_LOSS'
    metal_oxide.operation='MULTIPLY';metal_oxide.use_clamp=True
    tree.links.new(threshold.outputs['Result'],metal_oxide.inputs[0])
    metal_final=tree.nodes.new('ShaderNodeMath')
    metal_final.name='METAL_SOURCE_MINUS_OXIDATION'
    metal_final.operation='SUBTRACT';metal_final.use_clamp=True
    tree.links.new(metal_floor.outputs[0],metal_final.inputs[0])
    tree.links.new(metal_oxide.outputs[0],metal_final.inputs[1])
    tree.links.new(metal_final.outputs[0],shader.inputs['Metallic'])
    # The same extra narrow strip is present for ALL candidates, to
    # reveal longitudinal metal reflections without clipping overall exposure.
    lamp('POLISHED_BLADE_STUDIO_STRIP',(-.35,-2.3,2.15),target,85,.24,2.8)
    parameters=[
        # name, baseline palette, fine veins, V175 rough scale, oxide rough+, oxide metal loss, iron tone multiplier
        ('01_G_original_reference',.20,.84,.48,.13,.10,1.0),
        ('02_I_hierro_v175_082',.20,.84,.48,.13,.10,.82),
        ('03_J_hierro_v175_072',.20,.84,.49,.13,.10,.72),
        ('04_K_hierro_forged_076',.26,.86,.55,.16,.13,.76),
    ]
    results=[]
    view=(0,-4.6,.65)
    for name,base,fine,rough,oxide_rough,oxide_metal,tone in parameters:
        oxide_strength.inputs[1].default_value=fine
        oxide_base.inputs[1].default_value=base
        rough_scaled.inputs[1].default_value=rough
        rough_oxide.inputs[1].default_value=oxide_rough
        metal_oxide.inputs[1].default_value=oxide_metal
        iron_tone.inputs[2].default_value=(tone,tone,tone,1.0)
        bpy.context.view_layer.update()
        results.append(render_one(scene,meshes,target,a.output_dir/(name+'.png'),name,view))
    # More angles only for the leading candidates; same HDRI and actual 32-bit EXR.
    name,base,fine,rough,oxide_rough,oxide_metal,tone=parameters[2]
    oxide_strength.inputs[1].default_value=fine
    oxide_base.inputs[1].default_value=base
    rough_scaled.inputs[1].default_value=rough
    rough_oxide.inputs[1].default_value=oxide_rough
    metal_oxide.inputs[1].default_value=oxide_metal
    iron_tone.inputs[2].default_value=(tone,tone,tone,1.0)
    bpy.context.view_layer.update()
    results.append(render_one(scene,meshes,target,a.output_dir/'05_J_tres_cuartos.png','J_threequarters',(1.75,-4.5,1.10)))
    results.append(render_one(scene,meshes,target,a.output_dir/'06_J_cara_posterior.png','J_back',(0,4.6,0.65)))
    report={
        'status':'EXPERIMENT_ONLY_VISUAL_APPROVAL_PENDING',
        'experiment_version':'V02_iron_tone',
        'blender':bpy.app.version_string,
        'render_engine':'Cycles',
        'samples':a.samples,
        'source_sha256':sha,
        'source_file_unchanged':True,
        'geometry_triangle_count':tri,
        'original_mesh_count':len(meshes),
        'pbr_iron_color_source':['Genesis_V175_Hierro_Color_2K','Genesis_V175_APPROVED_PALETTE_BAKED_V03'],
        'pbr_original_normal':fab_normal.name,
        'pbr_v175_roughness_source':v175_orm.image.name,
        'pbr_original_fab_metallic_source':fab_orm.name,
        'hdr':a.hdri.name,
        'hdr_bits_per_pixel':environment.depth,
        'hdr_size':list(environment.size),
        'reference_same_lighting':True,
        'parameters':[{'name':n,'iron_palette_baseline':base,'localized_patina_strength':fine,'roughness_multiplier':r,'oxide_roughness_added':orx,'oxide_metallicity_loss':om,'iron_tone_multiplier':tone} for n,base,fine,r,orx,om,tone in parameters],
        'renders':results
    }
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'render_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_FINE_OXIDE_EXPERIMENT_DONE',json.dumps(report),flush=True)

if __name__=='__main__':main()
