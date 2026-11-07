#!/usr/bin/env python3
"""Project Genesis V24 - ice refinement using existing V23 Cycles studio separate affinity lookdev (NOT approved).
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


def smoke_alpha_material(name,seed=0.):
    """Transparent, spatially noisy charcoal smoke — avoids opaque purple paper strips."""
    m=bpy.data.materials.new(TAGS+name);m.use_nodes=True
    nodes=m.node_tree.nodes;nodes.clear();ln=m.node_tree.links
    output=nodes.new('ShaderNodeOutputMaterial')
    mix=nodes.new('ShaderNodeMixShader')
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    tint=nodes.new('ShaderNodeBsdfPrincipled')
    tint.inputs['Base Color'].default_value=(.009,.008,.014,1)
    tint.inputs['Roughness'].default_value=.96
    tint.inputs['Emission Color'].default_value=(.022,.012,.039,1)
    tint.inputs['Emission Strength'].default_value=.12
    tex=nodes.new('ShaderNodeTexCoord')
    noise=nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=9.8
    noise.inputs['Detail'].default_value=4.2
    noise.inputs['Roughness'].default_value=.73
    ln.new(tex.outputs['Generated'],noise.inputs['Vector'])
    shape=nodes.new('ShaderNodeMapRange')
    shape.inputs['From Min'].default_value=.28
    shape.inputs['From Max'].default_value=.73
    shape.inputs['To Min'].default_value=.0
    shape.inputs['To Max'].default_value=.48
    shape.interpolation_type='SMOOTHSTEP'
    ln.new(noise.outputs['Fac'],shape.inputs['Value'])
    ln.new(shape.outputs['Result'],mix.inputs[0])
    ln.new(transparent.outputs[0],mix.inputs[1])
    ln.new(tint.outputs[0],mix.inputs[2])
    ln.new(mix.outputs[0],output.inputs['Surface'])
    return m

def soft_radial_material(name,color,strength=.85):
    """Physically soft diffuse luminosity, not star icons or drawn plus signs."""
    m=bpy.data.materials.new(TAGS+name);m.use_nodes=True
    nodes=m.node_tree.nodes;nodes.clear();ln=m.node_tree.links
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    emission=nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value=(*color,1)
    emission.inputs['Strength'].default_value=strength
    out=nodes.new('ShaderNodeOutputMaterial')
    mix=nodes.new('ShaderNodeMixShader')
    tc=nodes.new('ShaderNodeTexCoord')
    sep=nodes.new('ShaderNodeSeparateXYZ')
    ln.new(tc.outputs['Generated'],sep.inputs[0])
    x=nodes.new('ShaderNodeMath');x.operation='SUBTRACT';x.inputs[1].default_value=.5
    y=nodes.new('ShaderNodeMath');y.operation='SUBTRACT';y.inputs[1].default_value=.5
    ln.new(sep.outputs['X'],x.inputs[0]);ln.new(sep.outputs['Y'],y.inputs[0])
    xx=nodes.new('ShaderNodeMath');xx.operation='MULTIPLY'
    yy=nodes.new('ShaderNodeMath');yy.operation='MULTIPLY'
    ln.new(x.outputs[0],xx.inputs[0]);ln.new(x.outputs[0],xx.inputs[1])
    ln.new(y.outputs[0],yy.inputs[0]);ln.new(y.outputs[0],yy.inputs[1])
    a=nodes.new('ShaderNodeMath');a.operation='ADD'
    ln.new(xx.outputs[0],a.inputs[0]);ln.new(yy.outputs[0],a.inputs[1])
    root=nodes.new('ShaderNodeMath');root.operation='SQRT'
    ln.new(a.outputs[0],root.inputs[0])
    ramp=nodes.new('ShaderNodeMapRange');ramp.interpolation_type='SMOOTHSTEP'
    ramp.clamp=True;ramp.inputs['From Min'].default_value=.015
    ramp.inputs['From Max'].default_value=.67
    ramp.inputs['To Min'].default_value=.40
    ramp.inputs['To Max'].default_value=0.
    ln.new(root.outputs[0],ramp.inputs['Value'])
    ln.new(ramp.outputs['Result'],mix.inputs[0])
    ln.new(transparent.outputs[0],mix.inputs[1])
    ln.new(emission.outputs[0],mix.inputs[2])
    ln.new(mix.outputs[0],out.inputs['Surface'])
    return m

def crystal_cluster(coord,along,side,normal,intensity):
    """V24: coherent blade-edge rime, physical translucent crystalline colonies.
    Metal ridge visible; no neon decals; all coordinates sampled on real V03 blade triangles.
    """
    ice_glaze=pbr('ice_etched_blue_glaze',(.28,.55,.66),roughness=.35,transmission=.38)
    ice_body=pbr('ice_tinted_crystal',(.29,.63,.81),roughness=.13,transmission=.73)
    ice_core=pbr('ice_cyan_deep_refraction',(.12,.34,.49),roughness=.09,transmission=.78)
    frost=pbr('ice_white_matte_rime',(.66,.79,.81),roughness=.66,transmission=.08)
    wet=pbr('ice_meltwater_film',(.16,.33,.37),roughness=.10,transmission=.45)
    frozen_edges=0
    # Intermittent ice shelf runs from both blade edges, leaving its center ridge bare.
    # Unlike a single painted stripe, these sheaths have uneven inner fracture fronts.
    for sign in (-1,1):
        for band,(start,end) in enumerate([(.155,.374),(.400,.653),(.681,.926)]):
            segments=32
            vertices=[]
            for j in range(segments+1):
                q=j/segments
                t=start+(end-start)*q
                envelope=math.sin(math.pi*q)**.55
                irregular=.5+.5*math.sin(t*88+sign*2.3)+.22*math.sin(t*211+band*2.1)
                nib=.29+.25*irregular+.13*(1.-envelope)
                inner=sign*(.37+.13*irregular)
                outer=sign*(.94-.03*math.sin(t*43+sign))
                if abs(inner)>=abs(outer):raise RuntimeError('Ice shelf inverted')
                p1,_=coord(t,inner,.0047)
                p2,_=coord(t,outer,.0048)
                vertices.extend([p1,p2])
            geo('ice_edge_shelf_'+str(sign)+'_'+str(band),vertices,
                [(2*j,2*j+1,2*j+3,2*j+2) for j in range(segments)],
                ice_glaze if band!=1 else wet)
            frozen_edges+=1
    ice_cluster_specs=[
        (.188,-1,.68,5),(.252,1,.65,6),(.336,-1,.55,5),
        (.423,1,.59,7),(.510,-1,.62,7),(.595,1,.60,6),
        (.692,-1,.67,7),(.758,1,.62,5),(.844,-1,.61,6),(.906,1,.50,4)
    ]
    crystals=0;fractals=0
    for group,(base,sgn,offset,n) in enumerate(ice_cluster_specs):
        for k in range(n):
            q=(k-(n-1)*.5)/max(1,n-1)
            t=base+q*(.050+.023*rng.random())+.004*(rng.random()-.5)
            t=max(.13,min(.96,t))
            lateral=sgn*(offset+.10*q+.08*(rng.random()-.5))
            p,_=coord(t,lateral,.006)
            radial=.0039+.0068*rng.random()
            prism_length=.017+.035*rng.random()
            raised=.004+.012*rng.random()
            bend=side*(.1+.3*rng.random())*sgn
            tip=p+along*prism_length+normal*raised+bend*(.008+.008*rng.random())
            transversal=side*radial
            back=along*radial*.65
            verts=[
                p-transversal-back, p+transversal-back,
                p+normal*(radial*.85), tip,
                p+along*(radial*.6)+normal*(radial*.4)
            ]
            geo('ice_tapered_prism_'+str(group)+'_'+str(k),verts,
                [(0,1,4),(0,4,2),(2,4,1),(0,2,3),(2,1,3),(1,0,3)],
                [ice_body,ice_core,ice_glaze][(group+k)%3])
            crystals+=1
        # Snowflake branching contours travel onto metal from the ice shelf;
        # forks are curved, imperfect and have different scale.
        for j in range(7):
            t=base+.013*(j-3)
            t=max(.13,min(.96,t))
            route=[]
            for k in range(9):
                u=k/8
                inward=.65-.45*u + .025*math.sin(u*11+j*2.1)
                sample,_=coord(t+u*(.018+.009*math.sin(group+j)**2),sgn*inward,.005)
                route.append(sample)
            line('ice_branch_white_'+str(group)+'_'+str(j),route,frost,.00036+.00020*rng.random())
            if j%2==0:
                for step in (3,5,7):
                    side_branch=side*sgn*(.004+.005*rng.random())
                    tip=route[step]+along*(.007+.003*rng.random())+side_branch
                    line('ice_branch_fork_'+str(group)+'_'+str(j)+'_'+str(step),
                        [route[step],tip],frost,.00029)
            fractals+=1
    # Frost granules at sides form a continuous cold finish, with intentional breaks.
    grains=0
    for k in range(125):
        t=.15+.78*rng.random()
        lateral=(-1 if k%2 else 1)*(.78+.16*rng.random())
        p,_=coord(t,lateral,.0052)
        size=.00065+.0017*rng.random()
        ellipsoid('ice_microrime_'+str(k),p,(size*.8,size*1.4,size*.26),frost)
        grains+=1
    return {'ice_shelves':frozen_edges,'faceted_3d_crystals':crystals,
            'branched_frost_dendrites':fractals,'rime_grains':grains,
            'PBR_refraction_roughness':.13,'ice_bands_reach_cutting_edges':True,
            'centre_ridge_metal_exposed':True,'all_geometry_sampled_on_V03_blade':True}

def radiant_gold(coord,along,side,normal,intensity):
    core=emitter('light_radial_white_core',(1.0,.90,.67),3.4+3.8*intensity)
    gold=emitter('light_warm_edge',(.80,.53,.21),1.3+1.5*intensity)
    halo=soft_radial_material('light_diffuse_agx_halo',(1.,.79,.40),2.2+1.5*intensity)
    pearl=pbr('light_luminescent_metal_pearl',(.72,.65,.41),roughness=.19,metallic=.83,
              emission=(.5,.37,.13),emission_power=.18)
    spots=0
    # Smooth luminous spots, soft bloom falloff. Not a repeated set of plus signs.
    for i in range(14):
        t=.14+.72*(i+.4)/14
        lat=math.sin(i*2.1)*.63
        pos,half=coord(t,lat,.012)
        ellipsoid('light_photon_seed_'+str(i),pos,
                  (.0021+.0015*rng.random(),.0034+.002*rng.random(),.0018),
                  core if i%3 else pearl)
        # Diffuse camera-facing pearl glow, soft edge in alpha shader.
        radius=.014+.006*(.5+.5*math.sin(i*2.3))
        verts=[pos-side*radius-along*radius,
               pos+side*radius-along*radius,
               pos+side*radius+along*radius,
               pos-side*radius+along*radius]
        geo('light_subtle_atmospheric_radial_'+str(i),verts,[(0,1,2,3)],halo)
        spots+=1
    # Elegant arcs follow the original iron ridge; not straight electrically oscillating lines.
    for i in range(7):
        begin=.14+i*.104
        trail=[]
        for j in range(24):
            u=j/23
            p,_=coord(begin+u*.061,.14+(.49*u)*math.sin(i*1.2+u*math.pi),.010)
            trail.append(p)
        line('light_curved_reflection_'+str(i),trail,gold,.00056)
    return {'warm_white_radiance_centres':spots,'diffuse_soft_halations':spots,
            'curved_specular_accents':7,'no_cross_symbol':True}

def shadow_ink(coord,along,side,normal,intensity):
    shadow=pbr('shadow_charcoal_depth',(.008,.008,.013),roughness=.96,
               emission=(.007,.006,.013),emission_power=.03)
    violet=pbr('shadow_dim_indigo_edge',(.040,.020,.064),roughness=.85,
               emission=(.10,.04,.14),emission_power=.06)
    translucent=smoke_alpha_material('shadow_turbulent_soft_smoke')
    # Elongated inky streaks curl around the fuller; make haze rather than paper decals.
    trails=0;sheets=0
    for k in range(12):
        begin=.11+k*.067
        sgn=(-1 if k%2 else 1)
        pts=[]
        for j in range(30):
            u=j/29
            t=begin+u*.082
            lateral=sgn*(.24+.31*math.sin((u*.75+k*.3)*math.pi))+.10*math.sin(u*12.+k)
            p,_=coord(t,lateral,.008+.006*math.sin(u*math.pi))
            pts.append(p)
        line('shadow_etched_ink_'+str(k),pts,shadow,.0015)
        if k%2==0:
            line('shadow_umbra_edge_'+str(k),pts[3:23],violet,.00068)
        trails+=1
        # A narrow ragged smoke veil crosses part of the iron, folds off to its dark edge.
        verts=[]
        for j in range(23):
            u=j/22
            p,_=coord(begin+u*.089,sgn*(.47+.08*math.sin(u*10.+k)),.014+u*.013)
            w=(.007+.012*math.sin(math.pi*u)**.9)*(1.+.25*math.sin(u*17.+k))
            verts.extend([p-side*w,p+side*w])
        geo('shadow_noise_veils_'+str(k),verts,
            [(2*j,2*j+1,2*j+3,2*j+2) for j in range(22)],translucent)
        sheets+=1
    return {'dark_etched_tracks':trails,'noise_masked_transparent_smoke_sheets':sheets,
            'smoke_alpha_max':.48,'not_opaque_lavender_paper':True}

def organic_vines(coord,along,side,normal,intensity):
    bark=pbr('nature_olive_creeping_stem',(.047,.145,.052),roughness=.66,
             emission=(.027,.070,.018),emission_power=.09)
    wet=pbr('nature_real_leaf_green',(.105,.285,.073),roughness=.29,
            transmission=.14,emission=(.035,.11,.017),emission_power=.13)
    forest=pbr('nature_olive_leaf',(.075,.19,.055),roughness=.45,transmission=.11)
    pale=pbr('nature_new_sap_lamina',(.24,.39,.12),roughness=.32,transmission=.09)
    sap=emitter('nature_muted_sap_bioluminescence',(.17,.58,.082),.60+.30*intensity)
    leaves=0;trunks=0;twigs=0
    # Asymmetric organic trunks creep diagonally from the lower blade toward the tip.
    for lane,(start,sgn,span) in enumerate([(.14,-1,.26),(.41,1,.30),(.68,-1,.21)]):
        backbone=[]
        for j in range(50):
            u=j/49
            t=start+u*span
            lateral=sgn*(.62-.31*u)+.10*math.sin(u*math.pi*2.6+lane)
            p,_=coord(t,lateral,.007+.001*math.sin(u*math.pi*2.0))
            backbone.append(p)
        line('nature_primary_spiral_'+str(lane),backbone,bark,.00155+.0003*lane)
        line('nature_sap_gloss_'+str(lane),backbone[2:45],sap,.00036)
        trunks+=1
        for j in [5,11,17,23,28,34,39,44]:
            step=1 if (j//5)%2 else -1
            sgn2=sgn*step
            branch=[]
            for k in range(9):
                u=k/8
                t=start+(j/49)*span+.010*u
                lat=sgn*(.62-.31*j/49)+.10*math.sin((j/49)*math.pi*2.6+lane)
                lat+=sgn2*.20*u+.034*math.sin(u*math.pi+lane+j)
                pos,_=coord(t,lat,.008+.0018*u)
                branch.append(pos)
            line('nature_secondary_branch_'+str(lane)+'_'+str(j),branch,bark,.00074)
            twigs+=1
            for m in (4,7):
                p=branch[m]
                growth=side*sgn2*(.007+.003*rng.random())+along*(.010+.003*rng.random())
                tip=p+growth+normal*.003
                sidevec=side*(.004+.002*rng.random())-along*(.002*rng.random())
                v=[p,p+growth*.50-sidevec,tip,p+growth*.48+sidevec]
                geo('nature_actual_leaf_'+str(lane)+'_'+str(j)+'_'+str(m),v,[(0,1,2),(0,2,3)],
                    wet if (j+m)%3 else forest)
                leafvein=p+growth*.72
                line('nature_leaf_vein_'+str(lane)+'_'+str(j)+'_'+str(m),
                     [p,leafvein],pale,.00026)
                leaves+=1
    for j in range(15):
        t=.15+.75*rng.random()
        p,_=coord(t,(rng.random()-.5)*1.45,.015)
        ellipsoid('nature_seed_spore_'+str(j),p,(.0011,.0013,.0010),sap)
    return {'full_creeping_vines':trunks,'natural_secondary_branches':twigs,
            'large_asymmetrical_leaves':leaves,'pollen':15,
            'no_repetitive_grass_stitch_pattern':True}

def earth_fractures(coord,along,side,normal,intensity):
    fracture=pbr('earth_black_subsurface_fault',(.036,.029,.023),roughness=.90,metallic=.12)
    ochre=pbr('earth_raw_ochre_stone',(.31,.23,.14),roughness=.81)
    slate=pbr('earth_grey_igneous_rock',(.17,.17,.16),roughness=.78)
    bronze=pbr('earth_iron_pyrite',(.40,.32,.22),roughness=.36,metallic=.51)
    matte=pbr('earth_dust_grey',(.28,.26,.22),roughness=.92)
    fault_groups=0;plate_fragments=0;branches=0
    for group,at in enumerate([.19,.37,.55,.71,.86]):
        fault_groups+=1
        start_lateral=(-.16 if group%2 else .17)
        for arm in range(5):
            angle=arm*math.tau/5 +.33*group
            coords=[]
            for j in range(17):
                u=j/16
                t=at+math.cos(angle)*(.018+.033*u)+u*.010*math.sin(u*14.+arm)
                t=max(.075,min(.96,t))
                lat=start_lateral+math.sin(angle)*(.31*u)+.06*u*math.sin(u*17.+arm*2.5)
                p,_=coord(t,lat,.006)
                coords.append(p)
            line('earth_broken_fault_'+str(group)+'_'+str(arm),coords,fracture,
                 .0011+.0010*math.sin(angle)**2)
            if arm%2==0:
                line('earth_subtle_pyrite_' +str(group)+'_'+str(arm),
                     [p+side*.0017 for p in coords[2:11]],bronze,.00042)
            branches+=1
        for i in range(16):
            offset=(rng.random()-.5)*.080
            lateral=start_lateral+(rng.random()-.5)*.63
            p,_=coord(at+offset,lateral,.006)
            size=.003+.0065*rng.random()
            h=.0015+.0045*rng.random()
            a=p-side*size*.75-along*size*.35
            b=p+side*size*.9-along*size*.2
            c=p+along*size*1.3
            apex=p+normal*h+along*size*.25
            geo('earth_exposed_rock_'+str(group)+'_'+str(i),
                [a,b,c,apex],[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],
                [ochre,slate,matte,bronze][(group+i)%4])
            plate_fragments+=1
    return {'nonuniform_fracture_centres':fault_groups,'black_fracture_branches':branches,
            'raised_faceted_earth_stone':plate_fragments,
            'not_just_glittering_gold_dots':True}

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
        renders=[render('CAM_hero',args.output_dir/(ch+'_V24_V12B_HDRI32_Hero.png'))]
        # Macro view is vital to inspect crystalline/organic shape, not just glowing pixels.
        renders.append(render('CAM_BLADE_MACRO',args.output_dir/(ch+'_V24_V12B_HDRI32_Detalle.png')))
        count_after=len([o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(TAGS)])
        if count_before!=count_after:raise RuntimeError('Approved original sword mesh list changed!')
        all_results.append({'affinity':ch,'details':details,'renders':renders,
           'vfx_objects':len([o for o in bpy.data.objects if o.name.startswith(TAGS)]),
           'approved':False,'human_visual_score':None})
        clear_effects()
        print('GENESIS_V24_CYCLES_CHANNEL_RENDERED',ch,json.dumps(details),flush=True)
    if bsdf.inputs['Base Color'].links[0].from_socket!=color_source:
        raise RuntimeError('Changed approved V175 base color!')
    if abs(rough.inputs[1].default_value-.34)>1e-6 or abs(oxide.inputs[1].default_value-.10)>1e-6:
        raise RuntimeError('Changed approved V12B look!')
    audit={'schema':'Genesis_V24_RealCycles_32bitHDRI_RealIceFrost',
      'status':'V24_ICE_ONLY_QUALITY_REVIEW_PENDING',
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
    (args.output_dir/'v24_hielo_cycles_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V24_REAL_CYCLES_COMPLETE',json.dumps(audit),flush=True)
if __name__=='__main__':main()
