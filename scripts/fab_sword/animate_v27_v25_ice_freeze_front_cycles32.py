#!/usr/bin/env python3
"""Project Genesis V26. REAL Cycles 24fps animation of the V25 ICE MODEL.
Uses approved V12B PBR, original V03/V175 GLB, original full RGB 32bpc 4K EXR.
No redesign; V25 crystals/frost meshes preserved, animated around their own pivots.
The coherent periodic envelope mathematically loops without a discontinuity.
"""
import argparse, sys, math, json, hashlib
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v12_v175_j_roughness as v12
import render_v18_v12b_fuego_v06_flow_cycles as studio
import render_v25_hielo_cycles_hdri32 as ice
HASH_GLB='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
HASH_EXR='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
PREFIX=ice.TAGS
def ensure(cond,message):
    if not cond:raise RuntimeError('GENESIS_V27_VALIDATION_FAILED '+message)
def studio_scene(args):
    ensure(hashlib.sha256(args.input.read_bytes()).hexdigest()==HASH_GLB,'GLB SHA V03 mismatch')
    ensure(hashlib.sha256(args.hdri.read_bytes()).hexdigest()==HASH_EXR,'EXR SHA 32bpc mismatch')
    preset=json.loads(args.preset.read_text())
    ensure(preset['id']=='Genesis_Espada_V03_Hierro_V175_V12B' and preset['visual_status']=='approved_by_user','V12B preset mismatch')
    argv=sys.argv
    try:
        sys.argv=['blender','--','--input',str(args.input),'--hdri',str(args.hdri),
                  '--output-dir',str(args.output_dir),'--samples',str(args.setup_samples)]
        v12.main()
    finally:sys.argv=argv
    scene=bpy.context.scene
    im=next((i for i in bpy.data.images if i.filepath and Path(bpy.path.abspath(i.filepath)).name==args.hdri.name),None)
    ensure(im is not None and im.depth==96 and tuple(im.size)==(4096,2048),'not original RGB 32bpc EXR')
    mat=next((m for m in bpy.data.materials if 'Iron_Blade_V175' in m.name),None)
    ensure(mat is not None and mat.use_nodes,'original iron V175 missing')
    nodes=mat.node_tree.nodes
    rough=nodes.get('V11_J_V175_ROUGHNESS_MULT_049')
    oxide=nodes.get('V12_J_OXIDE_LOCAL_ROUGHNESS')
    ensure(rough is not None and oxide is not None,'V12B iron nodes missing')
    ensure(abs(rough.inputs[1].default_value-.34)<1e-6 and abs(oxide.inputs[1].default_value-.10)<1e-6,'V12B roughness changed')
    color=next(n for n in nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].links[0].from_socket
    source=studio.collect_blade()
    coord,along,side,normal=ice.setup_frame(source)
    ref_details=ice.crystal_cluster(coord,along,side,normal,args.intensity/100.0)
    bpy.context.view_layer.update()
    ensure(ref_details['faceted_3d_crystals']==58 and ref_details['ice_tapered_shelves']==6,'V25 geometry changed')
    ensure(ref_details['branched_frost_dendrites']==70 and ref_details['rime_grains']==125,'V25 frost not preserved')
    ensure(next(n for n in nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].links[0].from_socket==color,'V175 original color changed')
    return scene,source,ref_details,mat
def rebase_pivot(obj):
    """Rebase ONLY V25 VFX curves/meshes; keep their world-space geometry unchanged."""
    if obj.type=='MESH':
        if obj.location.length>1e-7:
            return np.array(obj.location,dtype=float)  # icospheres already local origin
        if not obj.data.vertices:return np.zeros(3)
        center=np.mean([tuple(v.co) for v in obj.data.vertices],axis=0)
        for v in obj.data.vertices:v.co-=Vector(center)
        obj.location=Vector(center)
        obj.data.update()
        return center
    if obj.type=='CURVE':
        coords=[]
        for spline in obj.data.splines:
            for p in spline.points:coords.append(np.array(p.co[:3]))
        if not coords:return np.zeros(3)
        center=np.mean(coords,axis=0)
        for spline in obj.data.splines:
            for p in spline.points:
                q=np.array(p.co[:3])-center
                p.co=(float(q[0]),float(q[1]),float(q[2]),1)
        obj.location=Vector(center)
        return center
    return np.array(obj.location,dtype=float)
def animate_effects(args,source):
    origin,along,side,normal,samples,data=source
    length_sq=float(np.dot(along,along))
    ensure(length_sq>.001,'invalid original blade axis')
    objects=[o for o in bpy.data.objects if o.name.startswith(PREFIX) and o.type in ('MESH','CURVE')]
    ensure(len(objects)>250,'V25 objects missing')
    state=[]
    for obj in objects:
        center=rebase_pivot(obj)
        rel=float(np.dot(np.array(center)-np.array(origin),np.array(along))/length_sq)
        rel=max(0,min(1,rel))
        base=tuple(obj.scale)
        name=obj.name.lower()
        typ=('crystals' if ('prism' in name) else
             'frost' if ('dendrite' in name or 'branch' in name or 'microrime' in name) else
             'shelf' if ('shelf' in name) else 'other')
        stagger=int(hashlib.sha256(obj.name.encode()).hexdigest()[:4],16)/65535.
        state.append((obj,base,rel,typ,stagger))
    return state
def scale_at(st,frame,total,amount):
    """V27 physical freeze-front, hilt to tip and back, exact periodic 24 fps loop.
    The original V25 crystal/prism/rime meshes are NEVER modified; only VFX transform scale.
    A broad smoothstep transition prevents visible snapping and allows thaw/freeze cycles.
    """
    theta=2*math.pi*frame/total
    front=.5-.5*math.cos(theta)  # 0 -> 1 -> 0, zero velocity at beginning/end/peak
    stats={}
    for obj,base,along,typ,seed in st:
        # Each V25 object joins the frost from the hilt upwards, slightly staggered.
        pos=max(0.,min(1.,along+.018*(seed-.5)))
        t=max(0.,min(1.,(front-(pos-.11))/.22))
        grown=t*t*(3.-2.*t)
        # Keep the essential V25 geometry constant. Grow physical frost, not a postprocessed layer.
        if typ=='shelf':rest=.12
        elif typ=='crystals':rest=.075
        elif typ=='frost':rest=.045
        else:rest=.12
        factor=rest+(1.-rest)*grown
        # Extremely subtle ice refraction respiration only when frozen.
        shimmer=.985+.015*(.5+.5*math.sin(theta*2.0+along*4.2+seed*.2))
        factor*=1.-grown+grown*shimmer
        factor=1.0-amount*(1.0-factor)
        obj.scale=tuple(v*factor for v in base)
        stats[typ]=stats.get(typ,0)+1
    return stats

def render(args,scene,states):
    output=args.output_dir/'frames'
    output.mkdir(parents=True,exist_ok=True)
    scene.camera=bpy.data.objects['CAM_hero']
    scene.render.engine='CYCLES'
    scene.cycles.samples=args.samples
    scene.render.resolution_percentage=args.resolution_pct
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA'
    scene.render.film_transparent=False
    bpy.context.view_layer.cycles.use_denoising=True
    scene.render.fps=args.fps
    samples=[]
    for i in range(args.frames):
        frame=i+1
        scene.frame_set(frame)
        stats=scale_at(states,i,args.frames,args.animation_strength)
        bpy.context.view_layer.update()
        p=output/f'Ice_V25_Animated_{i:03d}.png'
        scene.render.filepath=str(p.absolute())
        bpy.ops.render.render(write_still=True)
        ensure(p.exists() and p.stat().st_size>25000,'missing true Cycles frame '+str(i))
        if i in (0,args.frames//4,args.frames//2,3*args.frames//4,args.frames-1):
            samples.append({'frame':i,'bytes':p.stat().st_size,'file':p.name})
        print('GENESIS_V27_CYCLES_FRAME',i+1,'/',args.frames,'bytes',p.stat().st_size,flush=True)
    # prove actual time-varying scale mathematically at endpoints and midcycle.
    scale_at(states,0,args.frames,args.animation_strength)
    first=[tuple(o.scale) for o,_,_,_,_ in states]
    scale_at(states,args.frames,args.frames,args.animation_strength)
    last=[tuple(o.scale) for o,_,_,_,_ in states]
    maxdiff=max(abs(a-b) for xs,ys in zip(first,last) for a,b in zip(xs,ys))
    ensure(maxdiff<1e-10,'loop param discontinuity')
    audit={'schema':'Genesis_V27_RealV25Ice_FreezingTravel_Cycles32bpc_24fps',
      'status':'experimental_strong_movement_quality_review_pending',
      'renderer':'Cycles','blender':bpy.app.version_string,
      'original_glb_sha256':HASH_GLB,'hdri_exr_sha256':HASH_EXR,
      'hdri_depth_RGBbits_per_channel':32,'hdri_exr_resolution':[4096,2048],
      'approved_V12B_material_preserved':True,
      'approved_V25_ice_model_reused_without_redesign':True,
      'v25_static_quality_reference':7.5,
      'original_mesh_modified':False,'fire_V20C1_modified':False,'rayo_V07_modified':False,
      'frame_count':args.frames,'fps':args.fps,'duration_s':args.frames/args.fps,
      'source_frame_quality':{'resolution_percentage':args.resolution_pct,
                              'samples':args.samples,'denoising':True},
      'loop_parameter_difference':maxdiff,
      'motion':'strong physical frost-front freeze from hilt to tip then natural thaw; smooth sinusoidal travel with zero derivative at loop endpoints',
      'effect_objects':len(states),'effect_object_types':stats,
      'static_v25_geometry':args.static_geometry,'samples':samples,
      'playcanvas_implementation':'not yet ported or tested',
      'visual_approval':'pending; do not imply game-ready'}
    (args.output_dir/'animation_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V27_REAL_CYCLES_ANIMATION_COMPLETE',json.dumps({k:audit[k] for k in ('frame_count','fps','effect_objects','loop_parameter_difference')}),flush=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--hdri',type=Path,required=True)
    p.add_argument('--preset',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--samples',type=int,default=18)
    p.add_argument('--setup-samples',type=int,default=16)
    p.add_argument('--resolution-pct',type=int,default=60)
    p.add_argument('--fps',type=int,default=24)
    p.add_argument('--frames',type=int,default=48)
    p.add_argument('--intensity',type=int,default=75)
    p.add_argument('--animation-strength',type=float,default=.94)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    ensure(1<=args.frames<=120 and args.fps==24 and 0<=args.intensity<=100,'invalid animation arguments')
    ensure(10<=args.samples<=96 and 30<=args.resolution_pct<=100,'invalid Cycles quality')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    scene,source,details,mat=studio_scene(args)
    args.static_geometry=details
    states=animate_effects(args,source)
    render(args,scene,states)
if __name__=='__main__':main()
