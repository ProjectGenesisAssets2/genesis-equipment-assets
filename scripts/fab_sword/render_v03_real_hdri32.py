#!/usr/bin/env python3
"""Render the *exact* Genesis V03 sword using Blender Cycles and real EXR HDRI.

Geometry/PBR image textures/node materials imported from GLB are never changed.
Only mesh object world-space positioning, studio lighting, and camera vary.
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
    scene.view_settings.look='Medium High Contrast'
    scene.view_settings.view_settings if False else None
    scene.view_settings.exposure=0.5
    scene.render.engine='CYCLES'
    # Real HDRI supplies illumination and reflections; softboxes shape metal highlights.
    environment=setup_world(a.hdri,strength=.9,rotation=.45)
    lamp('Wide key reflection',(-1.8,-2.0,3),target,320,2.2,3.2)
    lamp('Long blade strip',(1.5,-1.3,2.8),target,230,0.52,3.0)
    lamp('Rim separation',(1.6,1.7,1.5),target,270,1.0,2.4)
    lamp('Hilt warm fill',(-.9,-1.6,-1.0),target,85,1.4,1.6,(1,.88,.72))
    results=[]
    results.append(render_one(scene,meshes,target,a.output_dir/'V03_Blender_Cycles_HDRI32_Hero.png','hero',(0,-4.6,.65)))
    results.append(render_one(scene,meshes,target,a.output_dir/'V03_Blender_Cycles_HDRI32_TresCuartos.png','three_quarters',(1.65,-4.5,1.05)))
    report={'blender':bpy.app.version_string,'renderer':'Cycles','samples':a.samples,'source_sha256':sha,
       'geometry_triangles':tri,'meshes':len(meshes),'original_materials':list(mats),
       'pbr_source_textures':{n: [x.image.name for x in m.node_tree.nodes if x.type=='TEX_IMAGE' and x.image] for n,m in mats.items()},
       'hdri_name':a.hdri.name,'hdri_sha256':hashlib.sha256(a.hdri.read_bytes()).hexdigest(),
       'hdri_image_depth_bpp':environment.depth,'hdri_dimensions':list(environment.size),
       'geometry_or_material_edit':False,'renders':results}
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'render_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_REAL_BLENDER_HDRI_RENDER_COMPLETE',json.dumps(report),flush=True)

if __name__=='__main__':main()
