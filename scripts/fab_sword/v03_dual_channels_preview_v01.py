#!/usr/bin/env python3
"""Render Project Genesis original V03 with two independent channel effects on the V175 iron blade.

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


def vfx_material(name,color,base_strength):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nodes=m.node_tree.nodes;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial')
    em=nodes.new('ShaderNodeEmission')
    em.name='CHANNEL_EMISSION'
    em.inputs['Color'].default_value=(*color,1)
    em.inputs['Strength'].default_value=base_strength
    m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
    return m,em

def path_obj(name,pts,material,radius):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=8
    cu.bevel_depth=radius;cu.bevel_resolution=3;cu.resolution_u=12
    spl=cu.splines.new('POLY');spl.points.add(len(pts)-1)
    for i,p in enumerate(pts):
        spl.points[i].co=(*p,1)
    obj=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj

def channel_shader(tree,shade,source_name,color):
    # UV-independent procedural mask. Applied to the V175 BLADE material only.
    co=tree.nodes.new('ShaderNodeTexCoord');co.name=source_name+'_TEXCOORD'
    noise=tree.nodes.new('ShaderNodeTexNoise')
    noise.name=source_name+'_MASK_NOISE'
    noise.inputs['Scale'].default_value=12 if source_name=='FUEGO' else 8
    noise.inputs['Detail'].default_value=3
    tree.links.new(co.outputs['Generated'],noise.inputs['Vector'])
    ramp=tree.nodes.new('ShaderNodeValToRGB')
    ramp.name=source_name+'_MASK'
    ramp.color_ramp.elements[0].position=.47 if source_name=='FUEGO' else .61
    ramp.color_ramp.elements[1].position=.74 if source_name=='FUEGO' else .80
    tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    power=tree.nodes.new('ShaderNodeMath');power.operation='MULTIPLY'
    power.name=source_name+'_VALUE_CONTROL'
    tree.links.new(ramp.outputs['Color'],power.inputs[0])
    power.inputs[1].default_value=0
    emission=tree.nodes.new('ShaderNodeEmission')
    emission.name=source_name+'_BLADE_LIGHT'
    emission.inputs['Color'].default_value=(*color,1)
    tree.links.new(power.outputs[0],emission.inputs['Strength'])
    current=shade.inputs['Surface'].links[0].from_socket
    combine=tree.nodes.new('ShaderNodeAddShader');combine.name=source_name+'_COMBINE'
    tree.links.new(current,combine.inputs[0])
    tree.links.new(emission.outputs[0],combine.inputs[1])
    tree.links.new(combine.outputs[0],shade.inputs['Surface'])
    return power

def blade_segment(obj,blade_material,axis):
    vertices=[]
    for polygon in obj.data.polygons:
        if obj.data.materials[polygon.material_index] != blade_material:continue
        for k in polygon.vertices:
            vertices.append(obj.matrix_world@obj.data.vertices[k].co)
    if len(vertices)<10:raise ValueError('Could not isolate V175 blade vertices')
    samples=sorted([(v.dot(axis),v) for v in vertices],key=lambda x:x[0])
    n=max(3,len(samples)//18)
    p0=sum((p for _,p in samples[:n]),Vector())/n
    p1=sum((p for _,p in samples[-n:]),Vector())/n
    print('GENESIS_VFX_BLADE_ENDPOINTS',list(p0),list(p1),'vertices',len(vertices),flush=True)
    return p0,p1

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
    # Exact established J iron treatment from prior Cycles audit; do NOT change.
    oxide_strength.inputs[1].default_value=.84
    oxide_base.inputs[1].default_value=.20
    rough_scaled.inputs[1].default_value=.49
    rough_oxide.inputs[1].default_value=.13
    metal_oxide.inputs[1].default_value=.10
    iron_tone.inputs[2].default_value=(.72,.72,.72,1.0)
    # Combine two independent emission layers exclusively on blade material.
    material_output=next((n for n in tree.nodes if n.type=='OUTPUT_MATERIAL'),None)
    if material_output is None:raise RuntimeError('No V175 material output')
    fire_shader=channel_shader(tree,material_output,'FUEGO',(1.0,.085,.015))
    ray_shader=channel_shader(tree,material_output,'RAYO',(.08,.39,1.0))
    ice_shader=channel_shader(tree,material_output,'HIELO',(.19,.81,1.0))
    shadow_shader=channel_shader(tree,material_output,'SOMBRA',(.29,.07,.58))
    # The blade vertex group is computed from original glTF material assignments.
    blade_object=next((ob for ob in meshes if blade in ob.data.materials),None)
    if blade_object is None: raise ValueError('No blade primitive to attach VFX')
    blade_axis=Vector((.32,0,.948)).normalized()
    side=Vector((blade_axis.z,0,-blade_axis.x))
    p0,p1=blade_segment(blade_object,blade,blade_axis)
    blade_front=min((blade_object.matrix_world@blade_object.data.vertices[v].co).y
        for poly in blade_object.data.polygons if blade_object.data.materials[poly.material_index]==blade
        for v in poly.vertices)-.06
    def where(t,lateral=0,front=0):
        q=p0.lerp(p1,t)+side*lateral
        return Vector((q.x,blade_front+front,q.z))
    # Emissive curves are PREVIEW meshes only, anchored to true V175 blade bounds.
    # Masks/strength parameters can later be implemented as UV atlases in WebGL.
    fire_mat,fire_em=vfx_material('VFX_FUEGO_FIERY_EDGES',(1,.075,.014),4)
    fire_core_mat,fire_core_em=vfx_material('VFX_FUEGO_GOLD_CORE',(1,.38,.03),5)
    ray_mat,ray_em=vfx_material('VFX_RAYO_ELECTRIC_BLUE',(.025,.31,1),7)
    ray_core_mat,ray_core_em=vfx_material('VFX_RAYO_WHITE_ARC',(.4,.79,1),8)
    ice_mat,ice_em=vfx_material('VFX_HIELO_FROST',(.09,.72,1),3)
    ice_core_mat,ice_core_em=vfx_material('VFX_HIELO_LIGHT_ICE',(.55,.9,1),4)
    shadow_mat,shadow_em=vfx_material('VFX_SOMBRA_PURPLE_VAPOR',(.28,.035,.54),3.4)
    shadow_high_mat,shadow_high_em=vfx_material('VFX_SOMBRA_LILAC_ARC',(.5,.19,.83),4)
    import random
    rng=random.Random(20261104)
    duo={'fire_ray':[],'ice_shadow':[]}
    # Fire tongues: anchored to edges with short asymmetric plumes.
    for side_id in [-1,1]:
        for k in range(14):
            t=.06+k*.064+rng.uniform(-.012,.012)
            lateral=side_id*(.055+(.01 if t<.75 else -.012))
            depth=.045+rng.uniform(0,.055)
            q=[
              where(t-.018,side_id*.012,-.006),
              where(t,lateral,-.012),
              where(min(.99,t+depth),lateral+side_id*rng.uniform(.02,.07),-.02),
              where(min(.99,t+depth+.035),lateral+side_id*rng.uniform(.01,.06),-.015),
            ]
            duo['fire_ray'].append(path_obj('FIRE_TONGUE_%d_%02d'%(side_id,k),q,
                                            fire_mat if k%3 else fire_core_mat,.006 if k%3 else .004))
    # Lightning travels near and occasionally crosses the true central ridge.
    for path in range(3):
        points=[]
        for i in range(26):
            t=.06+.87*i/25
            lateral=(path-1)*.085+(rng.random()-.5)*.051
            points.append(where(t,lateral,-.044-path*.012))
        duo['fire_ray'].append(path_obj('RAYO_BLADE_ARC_%d'%path,points,
                                       ray_mat if path!=1 else ray_core_mat,.004 if path!=1 else .0025))
    for i in range(13):
        t=.07+i*.068
        src=where(t,rng.uniform(-.035,.035),-.035)
        end=where(min(.98,t+rng.uniform(.023,.07)),rng.choice([-1,1])*rng.uniform(.07,.17),-.045)
        duo['fire_ray'].append(path_obj('RAYO_BRANCH_%02d'%i,
                [src,where(min(.98,t+.022),rng.uniform(-.08,.08),-.055),end],
                ray_mat,.0026))
    # Frost: short crystalline veins and icicles clinging to the physical blade.
    for i in range(33):
        t=.05+i*.027+rng.uniform(-.009,.009)
        side_id=-1 if i%2 else 1
        lateral=side_id*(.025+rng.uniform(0,.046))
        points=[
            where(t-.015,lateral*.3,-.018),
            where(t,lateral,-.042),
            where(min(.98,t+.018),lateral+side_id*rng.uniform(.015,.052),-.037),
        ]
        duo['ice_shadow'].append(path_obj('ICE_CRYSTAL_%02d'%i,points,
                              ice_core_mat if i%5==0 else ice_mat,.0028 if i%5 else .004))
    # Shadow: violet curl wisps parallel to blade, never changing hilt material.
    for j in range(9):
        x=rng.choice([-1,1])*rng.uniform(.06,.14)
        phase=rng.uniform(0,6.28)
        pts=[]
        for i in range(20):
            t=.08+.85*i/19
            lateral=x+.031*math.sin(phase+t*11)
            pts.append(where(t,lateral,-.09-0.018*j/9))
        duo['ice_shadow'].append(path_obj('SHADOW_CURL_%02d'%j,pts,
                               shadow_high_mat if j%3==0 else shadow_mat,.0033))
    # Discreet colored practical lights; brightness scales with channel values.
    practical={}
    for key,rgb in [('fire_ray',(1.0,.22,.12)),('ice_shadow',(.14,.57,1.0))]:
        name='VFX_CHANNEL_LIGHT_'+key
        bpy.ops.object.light_add(type='POINT',location=where(.60,-.02,-.35))
        ob=bpy.context.object
        ob.name=name;ob.data.color=rgb;ob.data.energy=0
        ob.data.shadow_soft_size=.35
        practical[key]=ob
        duo[key].append(ob)
    def setting(pair,value):
        active={'fire_ray' if pair=='fire_ray' else 'ice_shadow'}
        for group,objects in duo.items():
            for obj in objects:obj.hide_render=(group not in active)
        for node in [fire_shader,ray_shader,ice_shader,shadow_shader]:
            node.inputs[1].default_value=0.0
        value=float(value)
        if pair=='fire_ray':
            fire_shader.inputs[1].default_value=2.2*value
            ray_shader.inputs[1].default_value=3.2*value
            for emission in [fire_em,fire_core_em,ray_em,ray_core_em]:
                emission.inputs['Strength'].default_value=2.0+7.0*value
        else:
            ice_shader.inputs[1].default_value=2.4*value
            shadow_shader.inputs[1].default_value=3.2*value
            for emission in [ice_em,ice_core_em,shadow_em,shadow_high_em]:
                emission.inputs['Strength'].default_value=1.4+6.5*value
        practical['fire_ray'].data.energy=55*value if pair=='fire_ray' else 0
        practical['ice_shadow'].data.energy=42*value if pair=='ice_shadow' else 0
        bpy.context.view_layer.update()
    renders=[]
    for pair in ['fire_ray','ice_shadow']:
        for val in [.30,.80]:
            setting(pair,val)
            label=pair+'_intensity_'+str(int(val*100))
            renders.append(render_one(scene,meshes,target,a.output_dir/(label+'.png'),label,(0,-4.6,.65)))
    # audit: no asset source ever modified, independently controlled blade shader slots
    report={
      'status':'EXPERIMENT_NOT_APPROVED','source_sha256':sha,
      'geometry_triangles':tri,'source_geometry_modified':False,
      'normal':fab_normal.name,'basecolor':'V175 iron J','hdr':a.hdri.name,
      'hdr_depth_bpp':environment.depth,'hdr_size':list(environment.size),
      'blender':bpy.app.version_string,'engine':'Cycles','samples':a.samples,
      'vfx_isolated_to_blade_material':True,
      'additional_vfx_preview_curves':{'Fuego+Rayo':len(duo['fire_ray']),'Hielo+Sombra':len(duo['ice_shadow'])},
      'channel_intensities_are_experimental_normalized_examples':[.30,.80],
      'target_engine': 'PlayCanvas/WebGL','source_model_exported':False,
      'variants':renders
    }
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'render_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_V03_DUAL_CHANNEL_RENDER_SUCCESS',json.dumps(report),flush=True)

if __name__=='__main__':main()
