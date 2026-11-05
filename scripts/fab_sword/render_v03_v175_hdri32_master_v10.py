#!/usr/bin/env python3
"""Non-destructive V10 master studio render of EXACT approved V03/V175 sword.

Reuses the last verified Blender/Cycles real 32-bit EXR studio script.
Adds a true blade close-up, QA and JSON profile for subsequent VFX renders.
No geometry or PBR edits. All real camera positions/lights are in scene only.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v03_real_hdri32 as original

EXPECTED_HDRI_SHA='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
EXPECTED_SOURCE_SHA='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--hdri',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=96)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if hashlib.sha256(args.input.read_bytes()).hexdigest()!=EXPECTED_SOURCE_SHA:
        raise ValueError('Not V03 V175 exact approved sword source')
    if hashlib.sha256(args.hdri.read_bytes()).hexdigest()!=EXPECTED_HDRI_SHA:
        raise ValueError('HDRI changed: studio lighting must be exactly reproducible')

    original.main()
    auditfile=args.output_dir/'render_audit.json'
    audit=json.loads(auditfile.read_text())
    if audit['hdri_image_depth_bpp'] != 96 or audit['hdri_dimensions'] != [4096,2048]:
        raise RuntimeError('Not true float32 RGB HDRI EXR or wrong resolution')
    if audit['geometry_triangles']!=2150 or audit['geometry_or_material_edit']:
        raise RuntimeError('Original sword unexpectedly edited')

    scene=bpy.context.scene
    sword=[obj for obj in scene.objects if obj.type=='MESH']
    blade=[]
    for ob in sword:
        indices={i for i,m in enumerate(ob.data.materials) if m and 'Iron_Blade_V175' in m.name}
        for poly in ob.data.polygons:
            if poly.material_index in indices:
                for i in poly.vertices:
                    blade.append(ob.matrix_world@ob.data.vertices[i].co)
    if len(blade)<40:
        raise RuntimeError('Cannot locate original V175 blade faces for macro')
    low=Vector(tuple(min(p[i] for p in blade) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in blade) for i in range(3)))
    target=(low+high)/2
    cam=bpy.data.objects.new('CAM_BLADE_MACRO',bpy.data.cameras.new('CAM_BLADE_MACRO'))
    bpy.context.collection.objects.link(cam)
    cam.location=target+Vector((.83,-4.55,.95))
    original.aim(cam,target)
    cam.data.type='ORTHO'
    cam.data.ortho_scale=2.7
    cam.data.lens=60
    scene.camera=cam
    bpy.context.view_layer.update()
    projected=[world_to_camera_view(scene,cam,p) for p in blade]
    spanx=max(p.x for p in projected)-min(p.x for p in projected)
    spany=max(p.y for p in projected)-min(p.y for p in projected)
    cam.data.ortho_scale*=max(spanx/.73,spany/.82,.25)
    bpy.context.view_layer.update()
    projected=[world_to_camera_view(scene,cam,p) for p in blade]
    frame=[min(p.x for p in projected),max(p.x for p in projected),
           min(p.y for p in projected),max(p.y for p in projected)]
    if frame[0]<.035 or frame[1]>.965 or frame[2]<.035 or frame[3]>.965:
        raise RuntimeError('Macro blade not correctly framed: '+str(frame))
    detail=args.output_dir/'V03_V175_HDRI32_Detalle_Filo.png'
    scene.render.filepath=str(detail.resolve())
    bpy.ops.render.render(write_still=True)
    if not detail.exists() or detail.stat().st_size<40000:
        raise RuntimeError('Macro render missing or empty')
    audit['renders'].append({'file':detail.name,'bytes':detail.stat().st_size,
                             'camera_bounds_blade_only':frame})
    audit['hdri_verified_rgb_float32']=True
    audit['original_v175_blade_triangles']=98
    audit['effects_present']=False
    audit['camera_profile']='V10 fixed HDRI studio for comparisons; three angles'
    auditfile.write_text(json.dumps(audit,indent=2,ensure_ascii=False))

    profile={
       'schema_version':1,'asset':'Genesis_Sword_Iron_V03_V175_Colores',
       'master_reference_only':True,'visual_approval':'pending',
       'source_sha256':EXPECTED_SOURCE_SHA,'geometry_triangles':2150,
       'metal':'Genesis_Iron_Blade_V175_Approved_Palette_V03_EXPERIMENTAL',
       'renderer':'Blender Cycles','blender':'4.5.13 LTS',
       'samples':args.samples,'output_pixels':[1200,1500],
       'hdri':{
          'name':'studio_small_09_4k.exr',
          'source':'Poly Haven Studio Small 09 - 4K EXR',
          'url':'https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/4k/studio_small_09_4k.exr',
          'sha256':EXPECTED_HDRI_SHA,'dimensions':[4096,2048],
          'bits_per_channel':32,'channels':'RGB','world_strength':0.9,
          'environment_rotation_radians':0.45,'camera_background':'dark only'},
       'exposure_ev':0.5,'view_transform':'AgX','look':'AgX - Medium High Contrast',
       'softboxes':[
          {'name':'Wide key reflection','power_watts':320,'width_m':2.2,'height_m':3.2},
          {'name':'Long blade strip','power_watts':230,'width_m':0.52,'height_m':3.0},
          {'name':'Rim separation','power_watts':270,'width_m':1.0,'height_m':2.4},
          {'name':'Hilt warm fill','power_watts':85,'width_m':1.4,'height_m':1.6}],
       'images':[r['file'] for r in audit['renders']],
       'channel_effects':'NONE — base PBR reference only',
       'for_later_vfx':'Freeze HDRI hash, camera setup, exposure and sword material; render channels separately',
       'do_not_publish_source_glb':True}
    (args.output_dir/'lighting_profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2))
    print('GENESIS_V10_MASTER_HDRI32_VERIFIED',json.dumps({
      'hdri_depth':audit['hdri_image_depth_bpp'],'source_sha':audit['source_sha256'],
      'triangle_count':audit['geometry_triangles'],'files':profile['images'],
      'material':profile['metal'],'source_glb_changed':False
    }),flush=True)

if __name__=='__main__':
    main()
