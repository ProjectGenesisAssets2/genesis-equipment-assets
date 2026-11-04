#!/usr/bin/env python3
"""Render exact Genesis V03 J iron with two independent dynamic-intensity channel masks, matched Studio Small 09 HDRI.

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


def create_vfx_ambience(channel,level,target,idx):
    """Preview-only Cycles curve glints, never exported with original GLB.
    The real runtime will use animated shader/particles instead."""
    if level < 1:return []
    pal={'Fuego':(.96,.16,.025),'Rayo':(.045,.40,1.0),
         'Hielo':(.27,.78,1.0),'Sombra':(.41,.08,.69)}
    c=pal[channel]
    shade=bpy.data.materials.new('PREVIEW_VFX_%s_%s'%(channel,idx))
    shade.use_nodes=True;nt=shade.node_tree;nt.nodes.clear()
    em=nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value=(c[0],c[1],c[2],1.)
    em.inputs['Strength'].default_value=3.0+4.5*level/100.
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0],out.inputs['Surface'])
    long_axis=Vector((.32,0.,.948)).normalized()
    side_axis=Vector((.948,0.,-.32)).normalized()
    camera_facing=Vector((0.,-.03,0.))
    models=[]
    count=1+int(level>=45)+int(level>=77)
    for j in range(count):
        cn=bpy.data.curves.new('%s arc_%d'%(channel,j),'CURVE')
        cn.dimensions='3D'
        cn.resolution_u=2
        cn.bevel_depth=.00145*(.7+level/110.)*(1.-.22*j)
        cn.bevel_resolution=2
        spline=cn.splines.new('POLY')
        N=56
        spline.points.add(N-1)
        for k,p in enumerate(spline.points):
            h=k/(N-1)
            # The actual source sword blade extends -0.42 .. +1.0 along its axis.
            t=-.37+1.20*h
            silhouette=.073*min(1.,max(.08,(1.-t)/.36))
            sign=-1 if channel in ('Fuego','Hielo') else +1
            wobble=.009*math.sin(t*54.+j*3.7)+.007*math.sin(t*116.+j*8.1)
            offset=silhouette+.010+j*.008+wobble
            # Tiny luminous tendrils outside the metal, separated from iron by camera offset.
            if channel=='Rayo':offset+=.014*math.sin(k*2.6+j)
            elif channel=='Sombra':offset+=.020*math.sin(t*11.+j*2.5)
            elif channel=='Fuego':offset+=.025*max(0,math.sin(t*34.+j*3.))
            elif channel=='Hielo':offset+=.009*math.sin(t*84.+j*1.7)
            pt=Vector(target)+long_axis*t+side_axis*(sign*offset)+camera_facing
            p.co=(*pt,1.)
        obj=bpy.data.objects.new('PREVIEW_%s_EMISSIVE_%d_%d'%(channel,idx,j),cn)
        bpy.context.collection.objects.link(obj)
        cn.materials.append(shade)
        models.append(obj)
    return models

def remove_vfx(models):
    for item in models:
        bpy.data.objects.remove(item,do_unlink=True)


def glowing_material(name, rgb, intensity=2.5):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    nt=m.node_tree;nt.nodes.clear()
    e=nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=(*rgb,1.0)
    e.inputs['Strength'].default_value=intensity
    out=nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(e.outputs[0],out.inputs['Surface'])
    return m,e

def glow_curve(name,n,material,radius):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D';curve.resolution_u=2
    curve.bevel_depth=radius;curve.bevel_resolution=2
    sp=curve.splines.new('POLY');sp.points.add(n-1)
    ob=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(ob)
    curve.materials.append(material)
    return ob,sp

def blade_pose(meshes,blade,axis):
    verts=[]
    for ob in meshes:
        for poly in ob.data.polygons:
            if ob.data.materials[poly.material_index]!=blade:
                continue
            for vid in poly.vertices:
                verts.append(ob.matrix_world@ob.data.vertices[vid].co)
    if len(verts)<20:
        raise ValueError('No original V03 blade faces')
    vals=[p.dot(axis) for p in verts]
    lo=min(vals);hi=max(vals)
    centroid=sum(verts,Vector())/len(verts)
    centerline=centroid-axis*centroid.dot(axis)
    return centerline+axis*lo,centerline+axis*hi,min(p.y for p in verts)-.025,len(verts)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--hdri',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--samples',type=int,default=18)
    p.add_argument('--pair',choices=['fire_ray','ice_shadow'],required=True)
    p.add_argument('--frames',type=int,default=18)
    p.add_argument('--masks',type=Path,required=True)
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
    scene.render.resolution_x=600
    scene.render.resolution_y=750
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
    # J remains the base: only V175/Fab PBR source textures on the original blade.
    oxide_strength.inputs[1].default_value=.84
    oxide_base.inputs[1].default_value=.20
    rough_scaled.inputs[1].default_value=.49
    rough_oxide.inputs[1].default_value=.13
    metal_oxide.inputs[1].default_value=.10
    iron_tone.inputs[2].default_value=(.72,.72,.72,1.0)

    # Layered emissive masks: BASE METAL TEXTURE IS NOT REPLACED.
    # Mask images are generated in the exact glTF blade UV0 islands.
    channel_images={}
    for c in ('Base','Luz','Sombra','Fuego','Hielo','Naturaleza','Tierra','Rayo'):
        f=a.masks/('Genesis_Mask_%s_V001.png'%c)
        if not f.exists():raise FileNotFoundError(str(f))
        image=bpy.data.images.load(str(f.resolve()))
        if tuple(image.size)!=(1024,1536):raise ValueError('Unexpected VFX mask size '+c+' '+str(tuple(image.size)))
        image.colorspace_settings.name='Non-Color'
        channel_images[c]=image
    uvnode=tree.nodes.new('ShaderNodeUVMap')
    uvnode.name='GENESIS_BLADE_UV0_FOR_VFX'
    uvnode.uv_map=meshes[0].data.uv_layers.active.name
    fx_textures=[]
    amplitudes=[]
    masks_colors=[]
    tint={'Fuego':(1.0,.115,.018,1.),'Rayo':(.065,.38,1.0,1.),
          'Hielo':(.31,.81,1.0,1.),'Sombra':(.39,.07,.73,1.)}
    for j in range(2):
        img=tree.nodes.new('ShaderNodeTexImage')
        img.name='VFX_CANAL_%d_MASK'%j
        tree.links.new(uvnode.outputs['UV'],img.inputs['Vector'])
        strength=tree.nodes.new('ShaderNodeMath')
        strength.operation='MULTIPLY'
        strength.name='VFX_CANAL_%d_INTENSIDAD_1_A_100'%j
        tree.links.new(img.outputs['Color'],strength.inputs[0])
        clr=tree.nodes.new('ShaderNodeMixRGB')
        clr.name='VFX_CANAL_%d_COLOR'%j
        clr.blend_type='MULTIPLY';clr.use_clamp=False
        clr.inputs[0].default_value=1.0
        tree.links.new(strength.outputs[0],clr.inputs[2])
        fx_textures.append(img);amplitudes.append(strength);masks_colors.append(clr)
    mixed=tree.nodes.new('ShaderNodeMixRGB')
    mixed.name='VFX_DOS_CANALES_COMBINADOS'
    mixed.blend_type='ADD';mixed.use_clamp=False
    mixed.inputs[0].default_value=1.0
    tree.links.new(masks_colors[0].outputs['Color'],mixed.inputs[1])
    tree.links.new(masks_colors[1].outputs['Color'],mixed.inputs[2])
    if 'Emission Color' not in shader.inputs or 'Emission Strength' not in shader.inputs:
        raise ValueError('Blender 4.5 Principled emission inputs unavailable')
    tree.links.new(mixed.outputs['Color'],shader.inputs['Emission Color'])
    shader.inputs['Emission Strength'].default_value=1.0
    # NOTE: metallic/roughness/normal and PBR base are otherwise identical to J.

    def channel_gain(channel,intensity):
        # These are render-preview VFX response curves, NOT game balance formulas.
        gain={'Fuego':4.3,'Rayo':5.0,'Hielo':2.3,'Sombra':2.4}[channel]
        return gain * (max(1,intensity)/100.)**1.35
    # Animation is on top of the existing EXACT J iron PBR:
    # source GLB, roughness, original normal and iron basecolor are not baked/edited.
    pair=a.pair
    names={'fire_ray':('Fuego','Rayo'),'ice_shadow':('Hielo','Sombra')}
    c1,c2=names[pair]
    for j,channel in enumerate((c1,c2)):
        fx_textures[j].image=channel_images[channel]
        masks_colors[j].inputs[1].default_value=tint[channel]
        amplitudes[j].inputs[1].default_value=channel_gain(channel,80)
    # UV flow moves each texture along the sword; noise/masks are independent per channel.
    uv_motion=[]
    for j in range(2):
        vec=tree.nodes.new('ShaderNodeVectorMath')
        vec.operation='ADD';vec.name='VFX_%s_ANIMATED_UV'%names[pair][j]
        tree.links.new(uvnode.outputs['UV'],vec.inputs[0])
        tree.links.new(vec.outputs['Vector'],fx_textures[j].inputs['Vector'])
        uv_motion.append(vec)
    # Dynamic exterior glows: all geometry is render-only and source mesh is untouched.
    ax=Vector((.32,0.,.948)).normalized()
    cross=Vector((ax.z,0.,-ax.x))
    bot,top,front,blade_vert_count=blade_pose(meshes,blade,ax)
    def blade_pos(t, offset=0.0, yback=0.0):
        p=bot.lerp(top,max(.03,min(.97,t)))+cross*offset
        return Vector((p.x,front+yback,p.z))
    strand_material,strand_emit=glowing_material('ANIMATED_%s_CORE'%c2,
         (.12,.47,1.) if pair=='fire_ray' else (.47,.13,.75),3.4)
    secondary_material,secondary_emit=glowing_material('ANIMATED_%s_ACCENT'%c1,
         (1.,.22,.035) if pair=='fire_ray' else (.27,.78,1.),2.2)
    glitter_material,glitter_emit=glowing_material('ANIMATED_SPARK_FRACTIONS',
         (.51,.88,1.) if pair=='fire_ray' else (.61,.83,1.),4.0)
    lines=[]
    for k in range(2 if pair=='fire_ray' else 4):
        ob,sp=glow_curve('VFX_DYNAMIC_STREAM_%d'%k,21,
                  strand_material if k%2==0 else secondary_material,
                  .0025 if pair=='fire_ray' else .0022)
        lines.append((ob,sp,k))
    sparks=[]
    for i in range(14):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
        ob=bpy.context.object
        ob.name='VFX_DYNAMIC_SPARK_%02d'%i
        ob.data.materials.append(glitter_material if i%3==0 else secondary_material)
        sparks.append(ob)
    # A faint local light makes the effect influence metal at higher channel values.
    light=bpy.data.lights.new('ANIMATED_CHANNEL_LIGHT','POINT')
    light.energy=0.0;light.shadow_soft_size=.3
    lob=bpy.data.objects.new('ANIMATED_CHANNEL_LIGHT',light)
    bpy.context.collection.objects.link(lob)
    lob.location=blade_pos(.55,0.,-.22)
    from math import sin,pi
    frame_report=[]
    view=(0,-4.6,.65)
    for f in range(a.frames):
        phase=f/a.frames
        # First half: 25/80; second half: 80/25. Values are fixed within each half.
        if f<a.frames//2:levels=(25,80)
        else:levels=(80,25)
        # Flicker is temporal VFX presentation; the channel value itself is fixed.
        flick1=.89+.11*sin(2*pi*(phase*3+.14))
        flick2=.82+.18*sin(2*pi*(phase*5+.31))
        amplitudes[0].inputs[1].default_value=channel_gain(c1,levels[0])*flick1
        amplitudes[1].inputs[1].default_value=channel_gain(c2,levels[1])*flick2
        uv_motion[0].inputs[1].default_value=(0.,-.035*phase,0.)
        uv_motion[1].inputs[1].default_value=(0.,.055*phase,0.)
        light.energy=8.+22.*max(levels)/100.*(.7+.3*sin(2*pi*(phase*4+.2))**2)
        light.color=(.64,.27,.30) if pair=='fire_ray' else (.25,.41,.82)
        seed=20261104+f*93+(0 if pair=='fire_ray' else 100000)
        import random
        rng=random.Random(seed)
        for ob,sp,k in lines:
            # Dynamic, non-rigid flow around/along the original blade.
            # Low intensity restricts width and lifetime; no fixed hanging wires.
            influence=(levels[1] if k%2==0 else levels[0])/100.
            ob.hide_render=(influence<.4 and k>0 and f%3==0)
            for i,p in enumerate(sp.points):
                t=.05+.88*i/(len(sp.points)-1)
                wobble=.018*sin(t*(65+k*7)+phase*24+k)+.012*(rng.random()-.5)
                drift=.017*sin(phase*2*pi+(t*13)+k)
                side=(.06 if k%2==0 else -.06)+k*.008
                pos=blade_pos(t,side+wobble+drift,-.029-.007*k)
                p.co=(*pos,1.0)
            ob.data.bevel_depth=(.0012+.0031*influence)*(1.0+.13*sin(phase*2*pi*4+k))
        for i,ob in enumerate(sparks):
            t=(i*.092+phase*(.28 if pair=='fire_ray' else .17)+.11*sin(i*1.7))%1.
            side=(-1 if i%2 else 1)*(.045+.037*sin(i*2.3+phase*5.))
            drift= .028*sin(phase*2*pi*(2+i%3)+i)
            ob.location=blade_pos(t,side+drift,-.040)
            size=.0035+.0055*max(levels)/100.
            if pair=='ice_shadow':size*=.78+.24*sin(phase*2*pi*2+i)
            ob.scale=(size,size,size*(1.3 if pair=='fire_ray' else 2.7))
            ob.hide_render=(f+i)%5==0
        strand_emit.inputs['Strength'].default_value=1.5+4.2*levels[1]/100.*flick2
        secondary_emit.inputs['Strength'].default_value=1.2+3.8*levels[0]/100.*flick1
        glitter_emit.inputs['Strength'].default_value=1.0+4.2*max(levels)/100.
        bpy.context.view_layer.update()
        output=a.output_dir/pair/('frame_%03d.png'%f)
        rendered=render_one(scene,meshes,target,output,'%s_%03d'%(pair,f),view)
        frame_report.append({'frame':f,'channels':{c1:levels[0],c2:levels[1]},
                             'source_glb_unchanged':True,'image':str(output.relative_to(a.output_dir)),
                             'bytes':rendered['bytes']})
        print('GENESIS_VFX_ANIM_FRAME_OK',pair,f,levels,flush=True)
    audit={
        'schema':'GenesisV03AnimatedDualChannelTest-V001',
        'status':'EXPERIMENT_NOT_APPROVED',
        'source_sha256':sha,'blender':bpy.app.version_string,'renderer':'Cycles',
        'samples':a.samples,'resolution':[600,750],
        'frame_rate_preview':8,'frame_count':a.frames,
        'pair':pair,'two_channel_levels':'first half 25/80, second half 80/25',
        'animated_parameters':['UV mask flow','emission amplitude flicker',
            'arc positions','spark movement','practical lighting'],
        'original_v03_triangle_count':tri,'original_blade_vertices':blade_vert_count,
        'original_glb_modified':False,'glb_exported':False,
        'source_material':'J iron V175 and Fab original normals',
        'hdr_real_exr_32bit':environment.depth==96,
        'hdr_dimensions':list(environment.size),
        'masks_distributed_as_images':list(channel_images),
        'animated_preview_geometry_is_separate_from_original':True,
        'frame_audit':frame_report}
    (a.output_dir/pair/'animation_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_VFX_ANIMATION_SUCCESS',json.dumps({k:audit[k] for k in ['pair','frame_count','source_sha256','hdr_real_exr_32bit']}),flush=True)

if __name__=='__main__':main()
