#!/usr/bin/env python3
"""V45 experimental REAL Cycles render: original V03 iron V175/V12B sword with
Fuego V18 (CC0 image atlas), Hielo V42 (original shader V175) and a physically
modeled Blender adaptation of approved PlayCanvas Rayo V07 3.15-turn helix.
This does not alter original sword geometry or approved source effects.
It is a *single combined 3D scene*, not an ImageGen mockup.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render_v42_moving_crystal_ice as frost
import render_v18_v12b_fuego_v06_flow_cycles as fire

ORIGINAL_ICE_BUILDER=frost.add_ice_layer
CAPTURED_SOURCE=None
READY=False
RESULTS=[]
FIRE_INFO={}
FIRE_TGA_PATH=None
RAY_INFO={}
SOURCE_GLBSHA='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
HDRI_SHA='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
ICE_SHA='9a24ffe1865ccf33c80b535ba27db0726fa1caca0f352425c82c8ae91e34ec89'

def prepared_ice_builder(coord,along,side,normal,intensity):
    """Cache true blade triangle cross-sections before frost overlay is added."""
    global CAPTURED_SOURCE
    CAPTURED_SOURCE=fire.collect_blade()
    if CAPTURED_SOURCE[-1]['blade_triangles']!=98:
        raise RuntimeError('V45_ORIGINAL_BLADE_TRIANGLES_CHANGED')
    return ORIGINAL_ICE_BUILDER(coord,along,side,normal,intensity)

def lightning_material(name,color,energy):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    ns=mat.node_tree.nodes
    ns.clear()
    out=ns.new('ShaderNodeOutputMaterial')
    e=ns.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=(*color,1.0)
    e.inputs['Strength'].default_value=energy
    mat.node_tree.links.new(e.outputs['Emission'],out.inputs['Surface'])
    return mat

def path_curve(name,points,material,radius):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D'
    curve.resolution_u=12
    curve.bevel_depth=radius
    curve.bevel_resolution=3
    spline=curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p,pt in zip(spline.points,points):
        p.co=(*tuple(map(float,pt)),1.0)
    obj=bpy.data.objects.new(frost.TAGS+name,curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(material)
    return obj

def add_approved_v07_helix_look(source,level=60,time=0.0):
    """3D Cycles look-dev adaptation of approved V07 geometry and timing.
    Approved JS/GLSL source vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs is unchanged.
    3.15-turn helix, fixed 60 intensity, 2 travelling luminous pulses.
    """
    center,along,side,normal,samples,meta=source
    turns=3.15
    r0=0.063
    z0=0.064
    start_t,end_t=.075,.946
    samples=sorted(samples,key=lambda r:r[0])
    tarr=np.array([r[0] for r in samples])
    neutral=lightning_material('V45_RayoV07_CoronaBlue',(0.055,.33,1.00),3.5+1.3*math.sin(2.0*math.pi*time/3.0)**2)
    core=lightning_material('V45_RayoV07_WhiteCyanCore',(.52,.78,1.0),16.+8.*math.sin(2.0*math.pi*time/3.0+.8)**2)
    arc_count=0
    def point(t):
        tt=max(0.,min(1.,t))
        pos=start_t+(end_t-start_t)*tt
        j=int(np.argmin(np.abs(tarr-pos)))
        st,u,left,right,top=samples[j]
        radscale=1-.46*max(0.,(tt-.76)/.24)**1.45
        ang=math.tau*(turns*tt+.18)
        # Use measured V03 blade boundaries rather than a generic new sword.
        mean=.5*(left+right)
        half=.5*(right-left)
        lateral=mean+(min(half+.014,r0)*radscale)*math.cos(ang)
        # Physically outside/inside front: depth test and genuine occlusion.
        z=top+.026 + z0*math.sin(ang)
        jag=.0021*math.sin(tt*411)+.0011*math.sin(tt*979)
        return center+along*u+side*(lateral+jag)+normal*z
    # Reproduce two bright temporal windows of the approved V07 pulse equation
    # at fixed time, rather than making a continuous neon tube.
    shift=.19*math.sin(math.tau*time/3.)
    for slot,(lo0,hi0) in enumerate(((.095,.405),(.555,.765))):
        lo=max(.015,lo0+shift)
        hi=min(.985,hi0+shift)
        if hi<lo+.045:continue
        pts=[point(lo+(hi-lo)*i/126.) for i in range(127)]
        path_curve('V45_RayoV07_Arc%d_Halo'%slot,pts,neutral,.0032)
        path_curve('V45_RayoV07_Arc%d_Core'%slot,pts,core,.0010)
        arc_count+=2
        # A couple of restrained tertiary fork discharges attached to the helix.
        for idx in (39,86):
            p=pts[idx]
            jump=side*(.019*(1 if (slot+idx)%2 else -1))+normal*.021
            tail=[p,p+jump*.38+along*.011,p+jump+along*.027]
            path_curve('V45_RayoV07_Branch%d_%d'%(slot,idx),tail,neutral,.0011)
            arc_count+=1
    return {'source':'vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs',
            'render_representation':'Blender Cycles approximate physical 3D helix; NOT original WebGL GLSL shader',
            'approved_glsl_unmodified':True,'helix_turns':turns,'intensity':level,
            'path_curve_objects':arc_count,'original_sword_mesh_modified':False}

def build_fusion(scene):
    global READY,FIRE_INFO,RAY_INFO
    if READY:return
    if CAPTURED_SOURCE is None:
        raise RuntimeError('V45_MISSING_ORIGINAL_SOURCE_BEFORE_FROST')
    frost.add_iron_lighting()
    frame=37
    scene.frame_set(frame)
    frost.ICE_VALUE.outputs[0].default_value=.67
    for n in frost.CRYSTAL_VALUES:n.outputs[0].default_value=.67
    fire_level=64
    fire_time=1.4
    fire.FLAME_IMAGE_TGA=bpy.data.images.load(FIRE_TGA_PATH,check_existing=False)
    fire.FLAME_IMAGE_TGA.reload()
    if tuple(fire.FLAME_IMAGE_TGA.size)!=(2048,1024):raise RuntimeError('V45_BAD_FLAME_ATLAS_AFTER_SCENE')
    objects,lights,geom,stats=fire.create_fire(fire_level,fire_time,CAPTURED_SOURCE)
    for obj in objects:
        obj.name=frost.TAGS+'V45_FUEGO_V18_'+obj.name
    FIRE_INFO={'source':'render_v18_v12b_fuego_v06_flow_cycles.py',
               'render_source':'Unity Labs CC0 SmallFlame01 mini 16x4 atlas TGA',
               'intensity':fire_level,'ribbons':len(objects),
               'original_glb_mesh_modified':False,
               'flame_tga_sha256':fire.FLAME_SHA_TGA,
               'fire_design_reused':stats}
    RAY_INFO=add_approved_v07_helix_look(CAPTURED_SOURCE,70,time=0.)
    # The initial V45 still overlays are replaced by animated scene geometry.
    # Preserve their source materials, do not mutate the approved sword.

    scene.view_settings.exposure=.5
    bpy.context.view_layer.update()
    READY=True

ANIM_SOURCE_FPS=12
ANIM_CAPTURE_FRAMES=24
FIRE_LIVE_OBJS=[]
RAY_LIVE_OBJS=[]

def replace_flame_geometry(time):
    """Use original V18 fire function, actual CC0 atlas cell per frame.
    Rebuild only VFX meshes. Do not alter V03 original blade or V175/V12B iron.
    """
    global FIRE_LIVE_OBJS
    if not FIRE_LIVE_OBJS:
        # Remove first static source preview from V43 (avoids double fire).
        FIRE_LIVE_OBJS=[o for o in bpy.data.objects if 'V45_FUEGO_V18_' in o.name]
    for ob in FIRE_LIVE_OBJS:
        if ob.name not in bpy.data.objects:continue
        mesh=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if mesh and mesh.users==0:bpy.data.meshes.remove(mesh)
    FIRE_LIVE_OBJS=[]
    for i in range(4):
        material=fire.v18_flame_material(64,i)
        obj=fire.flowing_s_flame_ribbon(CAPTURED_SOURCE,64,time,i,material)
        obj.name=frost.TAGS+'V45_FUEGO_V18_ANIM_'+str(i)
        FIRE_LIVE_OBJS.append(obj)


def replace_helix_geometry(time):
    """Retain geometry basis of V07 approved 3.15-turn helix; shift its two
    bright current arcs in real 3D along the V03 blade under the same HDRI.
    This is a Cycles adaptation, NOT a substitution for the approved WebGL GLSL.
    """
    global RAY_LIVE_OBJS
    if not RAY_LIVE_OBJS:
        # Remove static V43 source helix on first frame; keep ONE moving helix.
        RAY_LIVE_OBJS=[o for o in bpy.data.objects if 'V45_RayoV07_' in o.name]
    for ob in RAY_LIVE_OBJS:
        if ob.name not in bpy.data.objects:continue
        curve=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if curve and curve.users==0:bpy.data.curves.remove(curve)
    before=set(o.name for o in bpy.data.objects)
    add_approved_v07_helix_look(CAPTURED_SOURCE,70,time=time)
    RAY_LIVE_OBJS=[o for o in bpy.data.objects if o.name not in before and 'V45_RayoV07_' in o.name]


def fusion_render(camera,output):
    """True Cycles render through V12B+original 32-bit EXR.
    24 frames over a 3-second moving phase in exactly the same scene,
    with the user-intensity channels fixed at 64/70/67.
    """
    scene=bpy.context.scene
    build_fusion(scene)
    scene.render.resolution_x=1080
    scene.render.resolution_y=1350
    scene.render.resolution_percentage=100
    scene.cycles.samples=40
    # We preserve the 32-bit EXR world and the V175/V12B iron material.
    kind='Hero' if camera=='CAM_hero' else 'Detalle'
    if kind=='Hero':
        for i in range(ANIM_CAPTURE_FRAMES):
            time=3.0*i/ANIM_CAPTURE_FRAMES
            # Pre-existing Hielo V42 loop: time-only keyed phase. No intensity keys.
            scene.frame_set(1+round(i*96/ANIM_CAPTURE_FRAMES))
            frost.ICE_VALUE.outputs[0].default_value=.67
            for node in frost.CRYSTAL_VALUES:node.outputs[0].default_value=.67
            replace_flame_geometry(time)
            replace_helix_geometry(time)
            path=Path(output).with_name('V45_Triple_V175V12B_HDRI32_Frame_%03d.png'%i)
            rendered=frost.ORIGINAL_RENDER(camera,path)
            RESULTS.append({'file':path.name,'bytes':path.stat().st_size,
                            'camera':camera,'phase_seconds':time,'hielo':67,
                            'fuego':64,'rayo':70})
            print('V45_TRIPLE_REAL_CYCLES_FRAME',i+1,'/',ANIM_CAPTURE_FRAMES,
                  'bytes',path.stat().st_size,flush=True)
        return rendered
    else:
        scene.frame_set(49)
        frost.ICE_VALUE.outputs[0].default_value=.67
        for node in frost.CRYSTAL_VALUES:node.outputs[0].default_value=.67
        replace_flame_geometry(1.5)
        replace_helix_geometry(1.5)
        path=Path(output).with_name('V45_Triple_V175V12B_HDRI32_Detalle.png')
        rendered=frost.ORIGINAL_RENDER(camera,path)
        RESULTS.append({'file':path.name,'bytes':path.stat().st_size,
                        'camera':camera,'phase_seconds':1.5})
        return rendered

def main():
    global FIRE_TGA_PATH
    ap=argparse.ArgumentParser()
    for k in ('input','hdri','hielo-blend','flame-exr','flame-tga','output-dir','preset'):
        ap.add_argument('--'+k,required=True)
    ap.add_argument('--samples',type=int,default=80)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    for path,expected in [(args.input,SOURCE_GLBSHA),(args.hdri,HDRI_SHA),(args.hielo_blend,ICE_SHA)]:
        got=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if got!=expected:raise RuntimeError('V45_REJECT_UNVERIFIED_ORIGINAL '+path+' '+got)
    preset=json.loads(Path(args.preset).read_text())
    if preset['id']!='Genesis_Espada_V03_Hierro_V175_V12B' or preset['visual_status']!='approved_by_user':
        raise RuntimeError('V45_NOT_V12B_APPROVED_BASE')
    flame=Path(args.flame_tga)
    if not flame.is_file():raise RuntimeError('V45_CC0_FLAME_TGA_MISSING')
    # v12.main() clears the Blender scene and its images. Load CC0 atlas only
    # AFTER that reset, immediately before constructing the V18 fire material.
    FIRE_TGA_PATH=str(flame.resolve())
    fire.FLAME_IMAGE_EXR=None
    fire.FLAME_SHA_TGA=hashlib.sha256(flame.read_bytes()).hexdigest()
    fire.FLAME_SHA_EXR=hashlib.sha256(Path(args.flame_exr).read_bytes()).hexdigest()
    frost.add_ice_layer=prepared_ice_builder
    frost.render_frames=fusion_render
    sys.argv=['blender','--','--input',args.input,'--hdri',args.hdri,
        '--hielo-blend',args.hielo_blend,'--output-dir',args.output_dir,
        '--preset',args.preset,'--samples',str(args.samples),'--channels','Hielo']
    frost.main()
    if len(RESULTS)!=25:raise RuntimeError('V45_NOT_ALL_24_ANIMATED_FRAMES_AND_DETAIL_RENDERED '+str(len(RESULTS)))
    r=Path(args.output_dir)
    base_audit=json.loads((r/'v42_escarcha_cristal_audit.json').read_text())
    audit={
        'schema':'Genesis_V45_OriginalV03_V175V12B_Cycles_HDRI32_TripleVFX_24FrameAnimation',
        'asset_source_sha256':SOURCE_GLBSHA,'iron_preset':preset['id'],
        'hdri_rgb_32bit_channel_sha256':HDRI_SHA,'hielo_blend_sha256':ICE_SHA,
        'flame_tga_sha256':fire.FLAME_SHA_TGA,
        'renderer':'Cycles','blender':bpy.app.version_string,
        'original_sword_geometry_modified':False,
        'original_v175_v12b_iron_modified':False,
        'three_effects_in_one_scene':True,
        'temporal_animation_frames':24,
        'render_resolution':[1080,1350],
        'frame_animation_hz':12,
        'hielo_intensity_no_animation':True,
        'fire_atlas_uv_updated_each_frame':True,
        'lightning_helix_moved_each_frame':True,
        'fire':FIRE_INFO,'rayo':RAY_INFO,
        'hielo':{'source':'V42 original Hielo material and physical crystals',
                 'intensity':67,'original_material_from_blend':True,
                 'physical_crystals':base_audit['results'][0]['details']['physical_ice_facets']},
        'renders':RESULTS,'user_approved_triple_combination':False,
        'no_imagegen':True,'experimental_only':True,'PlayCanvas_integration':False
    }
    (r/'v45_fusion_3_efectos_audit.json').write_text(
        json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V45_TRIPLE_ELEMENTAL_REAL_CYCLES_COMPLETE',json.dumps(audit),flush=True)

if __name__=='__main__':main()
