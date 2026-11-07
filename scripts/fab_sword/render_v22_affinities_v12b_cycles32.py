#!/usr/bin/env python3
"""Project Genesis V22 - physically illuminated separate affinity lookdev (NOT approved).
Reuses the unchanged V12B Cycles sword/lighting code, exact V03/V175 GLB, exact 32-bit/ch RGB EXR.
Adds only independent procedural objects in memory. No ImageGen, no replacement material.
Five distinct original visual effects - realistic crystal / light / shadows / living plant / fractured rock.
Real-time PlayCanvas GLSL remains a separate representation and has not been changed.
"""
import bpy, math, json, hashlib, argparse, sys, random
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v12_v175_j_roughness as v12
import render_v18_v12b_fuego_v06_flow_cycles as swordref

ORIGINAL='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
HDRI='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
TAGS='GENESIS_V22_'
rng=random.Random(220722)
COUNT={}

def pbr(name,color,roughness=.31,metallic=.0,transmission=0.,emission=None,emission_power=0.):
    m=bpy.data.materials.new(TAGS+name);m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Transmission Weight'].default_value=transmission
    bs.inputs['IOR'].default_value=1.31 if transmission else 1.45
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1)
        bs.inputs['Emission Strength'].default_value=emission_power
    m.diffuse_color=(*color,1)
    return m

def emitter(name,color,energy):
    m=bpy.data.materials.new(TAGS+name);m.use_nodes=True
    ns=m.node_tree.nodes;ns.clear()
    e=ns.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=(*color,1)
    e.inputs['Strength'].default_value=energy
    out=ns.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
    return m

def geo(name,verts,faces,mat):
    mesh=bpy.data.meshes.new(TAGS+name+'_mesh')
    mesh.from_pydata([tuple(map(float,v)) for v in verts],[],faces)
    mesh.update()
    o=bpy.data.objects.new(TAGS+name,mesh)
    bpy.context.collection.objects.link(o)
    mesh.materials.append(mat)
    return o

def line(name,pts,mat,width=.0017):
    if len(pts)<2:return None
    curve=bpy.data.curves.new(TAGS+name+'_curve','CURVE')
    curve.dimensions='3D';curve.resolution_u=2
    curve.bevel_depth=width;curve.bevel_resolution=3
    spline=curve.splines.new('POLY');spline.points.add(len(pts)-1)
    for i,xyz in enumerate(pts):
        spline.points[i].co=(*map(float,xyz),1)
    o=bpy.data.objects.new(TAGS+name,curve)
    bpy.context.collection.objects.link(o)
    curve.materials.append(mat)
    return o

def ellipsoid(name,pos,scale,mat,segments=6):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=tuple(map(float,pos)))
    o=bpy.context.object;o.name=TAGS+name;o.scale=scale
    o.data.materials.append(mat)
    return o

def clear_effects():
    for o in [o for o in bpy.data.objects if o.name.startswith(TAGS)]:
        bpy.data.objects.remove(o,do_unlink=True)

def setup_frame(source):
    origin,along,side,normal,samples,data=source
    sample_fn,triangles=swordref.actual_surface_sampler(source)
    assert triangles==98
    def coord(t,lateral=0.,height=.008):
        row=min(samples,key=lambda x:abs(x[0]-t))
        _,u,left,right,front=row
        frac=max(-.98,min(.98,lateral))
        q=(left+right)*.5+frac*(right-left)*.5
        actual=sample_fn(u,q,front)
        p=origin+along*u+side*q+normal*(actual+height)
        return np.array(p,dtype=float),.5*(right-left)
    return coord,along,side,normal

def crystal_cluster(coord,along,side,normal,intensity):
    ice=pbr('ice_glass',(.17,.52,.75),roughness=.13,transmission=.62)
    frost=pbr('cold_ice_surface',(.43,.74,.83),roughness=.30,transmission=.20,
              emission=(.04,.12,.20),emission_power=.10)
    ridge=emitter('frozen_vein',(.20,.58,.86),1.6+2.1*intensity)
    count=0
    # True faceted prisms: triangular side walls, dark base and blue-lit facets.
    for n in range(90):
        t=.16+.74*(n+.4)/90
        lateral=(-1 if n%2 else 1)*(.50+.30*rng.random())
        pos,half=coord(t,lateral,.006)
        size=(.0036+.0066*rng.random())*(.75+.38*intensity)
        height=(.0040+.0120*rng.random())*(.7+.45*intensity)
        up=along*(.006+.012*rng.random())+normal*height
        angle=rng.random()*math.tau
        xdir=side*math.cos(angle)+along*math.sin(angle)
        v1=pos-xdir*size;v2=pos+xdir*size;v3=pos+normal*(size*.48)
        tip=pos+up+(side*(rng.random()-.5)*size*.5)
        geo('ice_faceted_'+str(n),[v1,v2,v3,tip],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],
            ice if n%3 else frost)
        count+=1
    # Organic frost branching near crystal roots - never an opaque blue overlay on center ridge.
    for k in range(18):
        t=.18+k*.038
        for sgn in (-1,1):
            pts=[]
            for j in range(6):
                p,_=coord(t+j*.007,sgn*(.66-.08*j)+.05*math.sin(k+j),.006)
                pts.append(p)
            line('ice_frost_microridge_'+str(k)+'_'+str(sgn),pts,frost,.00065)
            if k%3==0:line('ice_luminal_fissure_'+str(k)+'_'+str(sgn),pts,ridge,.00035)
    return {'faceted_crystals':count,'frost_lines':36,'color':'physically tinted pale blue translucent ice',
            'visible_metal_central_ridge':True}

def radiant_gold(coord,along,side,normal,intensity):
    gold=emitter('luz_soft_gold',(.78,.53,.17),2.6+3.5*intensity)
    white=emitter('luz_white_core',(1,.94,.73),3.5+4.5*intensity)
    halo=pbr('luz_metal',(.65,.50,.25),roughness=.17,metallic=.68,
             emission=(1,.73,.30),emission_power=.28+.4*intensity)
    glints=0
    for k in range(24):
        t=.11+.78*((k+.4)/24)
        lateral=[-.72,.61,.13,-.35,.45][k%5]
        pos,half=coord(t,lateral,.012)
        size=.0025+(.0052+.003*rng.random())*intensity
        ellipsoid('light_seed_'+str(k),pos,(size*.57,size*.60,size*.35),white if k%3==0 else gold)
        glints+=1
        if k%2==0:
            beams=[
                (along*(.010+.009*intensity), .00045),
                (side*(.008+.007*intensity), .00040),
            ]
            for bi,(direction,w) in enumerate(beams):
                line('luz_beam_'+str(k)+'_'+str(bi),
                     [pos-direction,pos+direction],white if bi==0 else gold,w)
        if k%5==0:
            ellipsoid('light_metal_charm_'+str(k),
                      pos-normal*.003,(size*1.5,size*1.5,.002),halo)
    # Discrete curved optically convincing streaks rather than stripes.
    for j in range(5):
        pts=[]
        for k in range(17):
            t=.17+j*.13+k*.0032
            p,_=coord(t,-.44+.05*k+.05*math.sin(k*.47+j),.008)
            pts.append(p)
        line('luz_gloss_filigree_'+str(j),pts,gold,.00055)
    return {'radiant_glints':glints,'cross_beam_glints':12,'diffuse_filigree':5,
            'not_a_single_yellow_paint_dot':True}

def shadow_ink(coord,along,side,normal,intensity):
    soot=pbr('shadow_cold_absorption',(.018,.016,.035),roughness=.92,
             emission=(.045,.024,.075),emission_power=.18)
    edge=pbr('shadow_purple_ash',(.10,.043,.16),roughness=.68,
             emission=(.17,.08,.26),emission_power=.22+.2*intensity)
    vapor=pbr('shadow_translucent_violet',(.08,.055,.12),roughness=.75,
              transmission=.15)
    n=0
    # Broad, smoky, asymmetrical undulating bands shading portions of the iron surface.
    for k in range(18):
        t=.13+k*.044
        lateral=(-.60 if k%2 else .48)
        coords=[]
        for j in range(11):
            q=j/10
            p,_=coord(t+q*.034,lateral+.11*math.sin(q*4.2+k*1.7),
                      .009+.003*math.sin(q*math.pi))
            coords.append(p)
        line('shadow_feather_'+str(k),coords,soot,.002+.0012*intensity)
        if k%3==0:
            line('shadow_faint_edge_'+str(k),coords[2:9],edge,.00075)
        n+=1
    # Overlaid torn vapor sheets hovering just above the blade; no blue lightning.
    for k in range(13):
        t=.20+k*.047
        verts=[]
        for j in range(12):
            q=j/11
            p,_=coord(t+q*.063,(-.54 if k%2 else .50)+.21*math.sin(q*3.+k),
                      .016+q*.012)
            width=.006+.007*math.sin(q*math.pi)**.8
            verts.extend([p-side*width,p+side*width])
        faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(11)]
        geo('shadow_ragged_veil_'+str(k),verts,faces,vapor if k%2 else soot)
    return {'ink_wisps':n,'torn_smoke_veils':13,'colors':'dark charcoal + subtle purple',
            'no_electricity_pulses':True}

def organic_vines(coord,along,side,normal,intensity):
    root=pbr('nature_branch_bark',(.06,.22,.055),roughness=.62,
             emission=(.05,.10,.018),emission_power=.12)
    fresh=pbr('nature_live_leaf',(.15,.38,.075),roughness=.33,
              transmission=.13,emission=(.06,.26,.035),emission_power=.30+.18*intensity)
    edges=emitter('nature_sap_glimmer',(.25,.83,.09),1.0+1.35*intensity)
    stems=0;leaves=0
    for lane in range(6):
        start=.16+lane*.125
        sgn=1 if lane%2 else -1
        trail=[]
        for j in range(24):
            q=j/23
            p,_=coord(start+q*.095,sgn*(.64-.23*q)+.15*math.sin(q*math.pi*2+lane)*q,
                      .008+.002*math.sin(q*math.pi))
            trail.append(p)
        line('nature_vine_'+str(lane),trail,root,.0014)
        if lane%2==0:line('nature_sap_'+str(lane),trail,edges,.00043)
        stems+=1
        for j in range(2,23,2):
            q=j/23
            p=trail[j]
            direction=side*(sgn*((-.012 if j%4 else .013)))+along*(.005+.004*rng.random())
            tip=p+direction+normal*(.001+.001*math.sin(j))
            line('nature_branch_'+str(lane)+'_'+str(j),[p,tip],root,.00065)
            v1=p-direction*.25-side*.0048
            v2=p-direction*.25+side*.0048
            v3=tip+along*.004
            geo('nature_leaf_'+str(lane)+'_'+str(j),
                [p,v1,v3,v2],[(0,1,2),(0,2,3)],fresh)
            leaves+=1
    for k in range(18):
        t=.18+(k+.3)*.038
        p,_=coord(t,(-.55 if k%2 else .52),.014)
        ellipsoid('nature_micropollen_'+str(k),p,(.0018,.0018,.0018),edges)
    return {'branching_vines':stems,'physical_leaves':leaves,'subtle_pollen':18,
            'organic_real_geometry':True}

def earth_fractures(coord,along,side,normal,intensity):
    crack=pbr('earth_dark_mineral_crack',(.07,.046,.025),roughness=.88,
              metallic=.15)
    bedrock=pbr('earth_rough_stone',(.29,.21,.12),roughness=.74,
                metallic=.07)
    quartz=pbr('earth_quartz',(.34,.28,.22),roughness=.38,metallic=.18,
               emission=(.18,.10,.035),emission_power=.08)
    ore=pbr('earth_veined_bronze',(.52,.34,.14),roughness=.30,metallic=.68)
    fissures=0;rocks=0
    for i in range(11):
        start=.12+i*.070
        sgn=-1 if i%2 else 1
        trail=[]
        for j in range(13):
            q=j/12
            t=start+q*.045
            lat=sgn*(.13+.40*q)+.09*math.sin(j*3.4+i*1.77)
            p,_=coord(t,lat,.007)
            trail.append(p)
        line('earth_main_fault_'+str(i),trail,crack,.0015+.0005*intensity)
        alt=[p+side*(.0024*sgn) for p in trail]
        line('earth_fault_golden_mineral_edge_'+str(i),alt,ore,.00048)
        fissures+=1
        for q in (3,7,10):
            p=trail[q]
            a=p+side*(sgn*.013)+along*(.008+rng.random()*.005)
            b=p+side*(sgn*.020)+along*(.017+rng.random()*.003)
            line('earth_tributary_crack_'+str(i)+'_'+str(q),[p,a,b],crack,.00085)
        for j in range(5):
            q=(j+.4)/5
            p,_=coord(start+q*.035,sgn*(.30+.23*rng.random()),.008)
            l=.0035+.002*rng.random()
            h=.002+.005*rng.random()
            geo('earth_rock_shard_'+str(i)+'_'+str(j),
              [p-side*l,p+side*l,p+along*l,p+normal*h],
              [(0,1,3),(1,2,3),(2,0,3),(0,2,1)],
              bedrock if (i+j)%3 else quartz)
            rocks+=1
    return {'angular_faults':fissures,'branch_faults':33,'faceted_rock_fragments':rocks,
            'earth_rough_non_emissive_material':True}

BUILDERS={
 'Hielo':crystal_cluster,
 'Luz':radiant_gold,
 'Sombra':shadow_ink,
 'Naturaleza':organic_vines,
 'Tierra':earth_fractures
}

def render(camera,output):
    scene=bpy.context.scene
    scene.camera=bpy.data.objects[camera]
    scene.render.filepath=str(output.absolute())
    bpy.ops.render.render(write_still=True)
    if not output.exists() or output.stat().st_size<100000:
        raise RuntimeError('FAILED ACTUAL CYCLES RENDER '+str(output))
    return {'name':output.name,'bytes':output.stat().st_size,'camera':camera}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--hdri',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--preset',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=64)
    parser.add_argument('--channels',nargs='+',default=list(BUILDERS))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    preset=json.loads(args.preset.read_text())
    if preset['id']!='Genesis_Espada_V03_Hierro_V175_V12B' or preset['visual_status']!='approved_by_user':
        raise RuntimeError('Wrong approved V12B preset')
    if hashlib.sha256(args.input.read_bytes()).hexdigest()!=ORIGINAL:
        raise RuntimeError('Wrong original V03 GLB')
    if hashlib.sha256(args.hdri.read_bytes()).hexdigest()!=HDRI:
        raise RuntimeError('Wrong approved RGB 32bits/ch EXR')
    for key in ('--preset','--channels'):
        pass
    # V12's unchanged parser accepts only its 4 original parameters.
    old_args=list(sys.argv)
    sys.argv=['blender','--','--input',str(args.input),'--hdri',str(args.hdri),
              '--output-dir',str(args.output_dir),'--samples',str(args.samples)]
    try:v12.main()
    finally:sys.argv=old_args
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=args.samples
    scene.render.image_settings.file_format='PNG'
    hdri_image=bpy.data.images.get(args.hdri.name)
    if hdri_image is None:
        hdri_image=next((im for im in bpy.data.images if im.filepath and Path(bpy.path.abspath(im.filepath)).name==args.hdri.name),None)
    if hdri_image is None or hdri_image.depth!=96 or tuple(hdri_image.size)!=(4096,2048):
        raise RuntimeError('32bit per RGB channel HDRI was not actually loaded!')
    src=swordref.collect_blade()
    iron=next((m for m in bpy.data.materials if 'Iron_Blade_V175' in m.name),None)
    if iron is None:raise RuntimeError('Original approved V175 iron material absent')
    bsdf=next(n for n in iron.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    color_source=bsdf.inputs['Base Color'].links[0].from_socket
    rough=iron.node_tree.nodes.get('V11_J_V175_ROUGHNESS_MULT_049')
    oxide=iron.node_tree.nodes.get('V12_J_OXIDE_LOCAL_ROUGHNESS')
    if rough is None or oxide is None or abs(rough.inputs[1].default_value-.34)>1e-5 or abs(oxide.inputs[1].default_value-.10)>1e-5:
        raise RuntimeError('Wrong V12B oxide/roughness')
    frame=ssetup=setup_frame(src)
    coord,along,side,normal=frame
    all_results=[]
    for ch in args.channels:
        if ch not in BUILDERS:raise RuntimeError('Unknown channel '+str(ch))
        count_before=len([o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(TAGS)])
        details=BUILDERS[ch](coord,along,side,normal,.75)
        bpy.context.view_layer.update()
        renders=[render('CAM_hero',args.output_dir/(ch+'_V22_V12B_HDRI32_Hero.png'))]
        # Macro view is vital to inspect crystalline/organic shape, not just glowing pixels.
        renders.append(render('CAM_BLADE_MACRO',args.output_dir/(ch+'_V22_V12B_HDRI32_Detalle.png')))
        count_after=len([o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(TAGS)])
        if count_before!=count_after:raise RuntimeError('Approved original sword mesh list changed!')
        all_results.append({'affinity':ch,'details':details,'renders':renders,
           'vfx_objects':len([o for o in bpy.data.objects if o.name.startswith(TAGS)]),
           'approved':False,'human_visual_score':None})
        clear_effects()
        print('GENESIS_V22_CYCLES_CHANNEL_RENDERED',ch,json.dumps(details),flush=True)
    if bsdf.inputs['Base Color'].links[0].from_socket!=color_source:
        raise RuntimeError('Changed approved V175 base color!')
    if abs(rough.inputs[1].default_value-.34)>1e-6 or abs(oxide.inputs[1].default_value-.10)>1e-6:
        raise RuntimeError('Changed approved V12B look!')
    audit={'schema':'Genesis_V22_RealCycles_32bitHDRI_AffinityLookdev',
      'status':'experimental_not_approved_do_not_show_before_private_7_5_review',
      'source_sha256':ORIGINAL,'hdri_sha256':HDRI,
      'hdri_RGB_bits_per_channel':32,'hdri_bits_per_pixel':96,
      'hdri_size':[4096,2048],
      'renderer':'Cycles','blender':bpy.app.version_string,'samples':args.samples,
      'approved_base_preset':preset['id'],'original_triangles':2150,'blade_triangles':98,
      'geometry_modified':False,'base_material_modified':False,'approved_rayo_modified':False,
      'approved_fire_modified':False,'no_concepts':True,'no_imagegen':True,
      'vfx_not_yet_adapted_to_PlayCanvas':True,
      'exposure_ev':preset['lighting']['exposure_ev'],
      'agx_look':preset['lighting']['look'],'world_strength':preset['lighting']['world_strength'],
      'results':all_results}
    (args.output_dir/'v22_affinities_real_cycles_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V22_REAL_CYCLES_COMPLETE',json.dumps(audit),flush=True)
if __name__=='__main__':main()
