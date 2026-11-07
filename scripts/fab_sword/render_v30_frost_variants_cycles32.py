#!/usr/bin/env python3
"""Project Genesis V30: two REFINED REAL Cycles frost renders on the ORIGINAL V03 iron sword.
A = physical matte hoarfrost/dendrites; B = same real frost plus tiny cold luminous
crystal tips. No concept generation. Preserves V12B original iron, correct 32bpc EXR HDRI,
camera and Cycles studio by calling established V25 renderer without altering sources.
Only VFX geometry and surface materials are swapped in memory.
"""
import sys, math, json, hashlib, argparse
import bpy
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v25_hielo_cycles_hdri32 as ref

def patterned_frost_coat(variant):
    """Thin noise-masked powder frost deposited ON the real blade, without opaque ice plates.
    The translucent alpha and fractal microdetail give physically irregular hoarfrost
    coverage, while most of the underlying V175 metal is fully visible.
    """
    m=bpy.data.materials.new(ref.TAGS+'V30_REAL_HOARFROST_MICRO_RIME_FILM_'+variant)
    m.use_nodes=True
    ns=m.node_tree.nodes
    ns.clear()
    links=m.node_tree.links
    output=ns.new('ShaderNodeOutputMaterial')
    mix=ns.new('ShaderNodeMixShader')
    clear=ns.new('ShaderNodeBsdfTransparent')
    frost=ns.new('ShaderNodeBsdfPrincipled')
    frost.inputs['Base Color'].default_value=(.77,.80,.79,1) if variant=='A' else (.48,.67,.85,1)
    frost.inputs['Roughness'].default_value=.91 if variant=='A' else .78
    frost.inputs['Metallic'].default_value=0.
    frost.inputs['Transmission Weight'].default_value=.018
    if variant=='B':
        frost.inputs['Emission Color'].default_value=(.17,.36,.55,1)
        frost.inputs['Emission Strength'].default_value=.24
    tex=ns.new('ShaderNodeTexCoord')
    # Blade aspect-ratio correction: normalize frost cell size in real-world space.
    # Without multiplying the longitudinal dimension, 3D noise stretches into long
    # white stripes along the sword instead of round micro-scale frost colonies.
    anisotropic=ns.new('ShaderNodeVectorMath')
    anisotropic.operation='MULTIPLY'
    anisotropic.inputs[1].default_value=(1.0,12.4,1.0)
    links.new(tex.outputs['Generated'],anisotropic.inputs[0])
    noise=ns.new('ShaderNodeTexNoise')
    noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=6.2
    noise.inputs['Detail'].default_value=5.
    noise.inputs['Roughness'].default_value=.76
    links.new(anisotropic.outputs['Vector'],noise.inputs['Vector'])
    macro=ns.new('ShaderNodeMapRange')
    macro.interpolation_type='SMOOTHSTEP'
    macro.clamp=True
    macro.inputs['From Min'].default_value=.415
    macro.inputs['From Max'].default_value=.685
    macro.inputs['To Min'].default_value=0.
    macro.inputs['To Max'].default_value=.83 if variant=='A' else .79
    links.new(noise.outputs['Fac'],macro.inputs['Value'])
    fine=ns.new('ShaderNodeTexNoise')
    fine.noise_dimensions='3D'
    fine.inputs['Scale'].default_value=17.5
    fine.inputs['Detail'].default_value=2.1
    fine.inputs['Roughness'].default_value=.68
    links.new(anisotropic.outputs['Vector'],fine.inputs['Vector'])
    micro=ns.new('ShaderNodeMapRange')
    micro.interpolation_type='SMOOTHSTEP'
    micro.clamp=True
    micro.inputs['From Min'].default_value=.28
    micro.inputs['From Max'].default_value=.74
    micro.inputs['To Min'].default_value=.35
    micro.inputs['To Max'].default_value=1.
    links.new(fine.outputs['Fac'],micro.inputs['Value'])
    scale=ns.new('ShaderNodeMath')
    scale.operation='MULTIPLY'
    links.new(macro.outputs['Result'],scale.inputs[0])
    links.new(micro.outputs['Result'],scale.inputs[1])
    links.new(scale.outputs[0],mix.inputs[0])
    links.new(clear.outputs[0],mix.inputs[1])
    links.new(frost.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs['Surface'])
    return m

def build_frost(coord,along,side,normal,intensity,variant):
    if variant not in ('A','B'):
        raise RuntimeError('V30_WRONG_VARIANT')
    rng=ref.rng
    rng.seed(281107 if variant=='A' else 281107)  # EXACT same geometry and lighting; only material accents change
    vfx=ref.TAGS
    assert vfx=='GENESIS_V22_'   # use same prefix so V25 audit/cleanup only affects our new VFX
    cold_matte=ref.pbr('V30_HOARFROST_WHITISH_RIME',(.76,.78,.77) if variant=='A' else (.58,.72,.81),
                       roughness=.86,metallic=0,transmission=.015)
    crystal_silver=ref.pbr('V30_MICRO_ICE_SURFACE',(.65,.72,.73) if variant=='A' else (.47,.69,.80),
                           roughness=.57,metallic=0,transmission=.13)
    powder=ref.pbr('V30_WHITE_FROST_GRAINS',(.82,.83,.81) if variant=='A' else (.68,.80,.88),
                    roughness=.91,metallic=0,transmission=0)
    mint=ref.pbr('V30_BLUE_DARK_CRYSTAL',(.23,.43,.57),
                  roughness=.29,metallic=0,transmission=.38)
    if variant=='B':
        luminous=ref.pbr('V30_SUBTLE_COLD_BIOLUMINESCENCE',(.42,.73,.85),
                         roughness=.43,metallic=0,transmission=.17,
                         emission=(.25,.52,.80),emission_power=.88)
        glow=ref.pbr('V30_SUBTLE_REFRACTIVE_EDGE',(.53,.79,.83),
                     roughness=.22,metallic=0,transmission=.45,
                     emission=(.13,.27,.45),emission_power=.32)
    else:
        luminous=crystal_silver
        glow=cold_matte
    coat=patterned_frost_coat(variant)
    # Porous, masked translucent coat on the outer blade, two very thin PBR meshes.
    # All alpha variation is generated from physically small-scale turbulence.
    coats=0
    for sign in (-1,1):
        verts=[]
        for k in range(151):
            t=.14+.81*k/150
            inner,_=coord(t,sign*.14,.0052)
            outer,_=coord(t,sign*.975,.0053)
            verts.extend([inner,outer])
        faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(150)]
        ref.geo('V30_PHYSICAL_POWDER_FROST_COAT_'+str(sign),verts,faces,coat)
        coats+=1
    branches=0;subbranches=0;axes=0;microcrystals=0;powder_grains=0;tips=0
    # Rime deposits arise from irregular nucleation sites at the exposed edges.
    # Each site grows thin feathery branching ice into the blade surface, while
    # the central ridge remains mostly original steel, with preserved V175 highlights.
    for sign in (-1,1):
        for colony in range(24):
            t0=.143+.79*(colony+.38)/24 +.0038*(rng.random()-.5)
            t0=max(.135,min(.95,t0))
            extent=.22+.23*rng.random()
            drift=(rng.random()-.5)*.072
            def trace(u, side_shift=0., long_shift=0., height=.0054):
                t=max(.12,min(.967,t0+drift*u+long_shift))
                lateral=sign*(.95-extent*u)+side_shift
                return coord(t,lateral,height)[0]
            central=[]
            for k in range(10):
                u=k/9
                central.append(trace(u,sign*.014*math.sin(u*math.pi*1.3+colony*.59)*u,
                                     .008*math.sin(u*math.pi*.75+colony*.51)*u))
            ref.line('V30_DENDRITIC_ROOT_%s_%02d'%(sign,colony),central,
                     cold_matte,width=.00054+.00021*rng.random())
            axes+=1
            # Frost grows like tiny hoarfrost ferns, not giant translucent polygons.
            for j in range(2,9):
                u=j/9
                start=central[j]
                direction=(-1 if j%2 else 1)
                seg=.007+.010*rng.random()
                inward=direction*(.030+.034*rng.random())
                arm=[]
                for m in range(7):
                    v=m/6
                    t_delta=direction*seg*v
                    lateral_delta=sign*(.011+.023*rng.random())*v
                    anchor=trace(min(1.,u+.10*v),side_shift=lateral_delta,long_shift=t_delta,
                                 height=.0057+v*.0003)
                    arm.append(anchor)
                ref.line('V30_FROST_FERN_ARM_%s_%02d_%02d'%(sign,colony,j),arm,
                         cold_matte if j%3 else crystal_silver,
                         width=.00035+.00016*rng.random())
                branches+=1
                # One fork on most arms, asymmetric like atmospheric frost.
                for b in (2,4):
                    if j==8 and b==4:continue
                    p=arm[b]
                    u2=min(1.,u+.10*b/6+.055)
                    branch_tip=trace(u2,
                                     side_shift=sign*(.028+.018*rng.random()),
                                     long_shift=t_delta+direction*(.004+.005*rng.random()),
                                     height=.00585)
                    ref.line('V30_DENDRITE_TWIG_%s_%02d_%02d_%02d'%(sign,colony,j,b),
                             [p,branch_tip],crystal_silver if (colony+j+b)%4 else powder,
                             width=.00022+.00011*rng.random())
                    subbranches+=1
            # White hoar grain scattered at frost source (tiny physical beads).
            for n in range(4):
                u=.10+.75*rng.random()
                p=trace(u,side_shift=sign*(rng.random()-.5)*.043,height=.0053)
                size=.0015+.00220*rng.random()
                ref.ellipsoid('V30_HOAR_GRAIN_%s_%02d_%d'%(sign,colony,n),
                              p,(size*.58,size*1.42,size*.42),powder)
                powder_grains+=1
            # Very small tetrahedral ice crystals are sparse ornaments of the frost,
            # never the main form, unlike V25.
            for n in range(2):
                p=trace(.40+.45*rng.random(),height=.0057)
                sz=.0030+.0045*rng.random()
                prism=[p-side*sz,p+side*sz,p+along*(sz*.65),p+normal*(.0017+.0025*rng.random())]
                material=mint if (colony+n)%5==0 else crystal_silver
                ref.geo('V30_MICRO_FACET_%s_%02d_%d'%(sign,colony,n),
                        prism,[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],material)
                microcrystals+=1
            if variant=='B' and colony%2==0:
                # A FEW teal highlights: visually not electrical, no helices.
                p=trace(.72,height=.0075)
                sz=.0028+.0018*math.sin(colony+2.8)**2
                ref.ellipsoid('V30_GENTLE_COLD_TIP_%s_%02d'%(sign,colony),
                              p,(sz*.63,sz*.94,sz*.48),luminous)
                tips+=1
    # Wisp-thin discontinuous matte rime at the cutting edges. Its construction
    # uses grains instead of blue sheets, preventing the plate-armour appearance.
    for sign in (-1,1):
        for n in range(90):
            t=.13+.80*rng.random()
            if math.sin(t*71+sign*5.8)>.57:continue  # visible bare-iron gaps
            lateral=sign*(.88+.080*rng.random())
            p,_=coord(t,lateral,.0051)
            length=.0018+.0035*rng.random()
            width=.0012+.0018*rng.random()
            ref.ellipsoid('V30_EDGE_FROST_%s_%03d'%(sign,n),p,
                          (width,length,width*.31),glow if variant=='B' and n%17==0 else powder)
            powder_grains+=1
    # Light atmospheric frost is primarily matte, no neon electric edges.
    return {
      'powder_coat_thin_noise_masked_pbr_strips':coats,
      'variant':variant,'type':'real_hoarfrost' if variant=='A' else 'hoarfrost_slightly_enchanted',
      'principal_form':'feathery branching matte rime adherent to original steel',
      'nucleation_sites':48,'feather_axes':axes,'secondary_fern_arms':branches,
      'tertiary_dendrites':subbranches,'powder_rime_grains':powder_grains,
      'tiny_faceted_microcrystals':microcrystals,
      'cold_fantasy_tips':tips,'hero_light':'original_V12B_32bpc_EXR',
      'noise_corrected_for_blade_aspect_ratio':True,
      'no_flat_translucent_ice_sheets':True,'original_iron_ridge_uncovered':True,
      'no_electric_strings':True,
      'subtle_magic_only':variant=='B'
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',choices=['A','B'],required=True)
    args,_=parser.parse_known_args(sys.argv[sys.argv.index('--')+1:])
    original_argv=list(sys.argv)
    ref.BUILDERS['Hielo']=lambda coord,along,side,normal,intensity:build_frost(coord,along,side,normal,intensity,args.variant)
    try:
        # The existing renderer still enforces original source SHA, EXR depth=96,
        # the V12B metal roughness and preserves source meshes byte-for-byte.
        raw=original_argv[original_argv.index('--')+1:]
        clean=[]
        skip=False
        for a in raw:
            if skip:skip=False;continue
            if a=='--variant':skip=True;continue
            clean.append(a)
        sys.argv=['blender','--']+clean
        ref.main()
        opts=dict(zip(clean[::2],clean[1::2]))
        out=Path(opts['--output-dir'])
        result=json.loads((out/'v25_hielo_cycles_audit.json').read_text())
        for name in ('Hero','Detalle'):
            old=out/('Hielo_V25_V12B_HDRI32_'+name+'.png')
            new=out/('Escarcha_'+args.variant+'_V30_V12B_HDRI32_'+name+'.png')
            if not old.is_file():raise RuntimeError('V30_MISSING_REAL_CYCLES_'+str(old))
            old.rename(new)
        detail=result['results'][0]['details']
        if detail['nucleation_sites']!=48 or detail['feather_axes']!=48 or detail['secondary_fern_arms']<320:
            raise RuntimeError('V30_FROST_GEOMETRY_INCOMPLETE')
        result['schema']='Genesis_V30_Hoarfrost_RealCycles_V12B_EXR_RGB32'
        result['source_base']='V25 unchanged same iron/hdr/camera'
        result['selected_variant']=args.variant
        result['no_image_generation']=True
        result['video_animation_created']=False
        result['user_approval']='pending_actual_visual_comparison'
        result['results'][0]['renders']=[
            {'name':'Escarcha_'+args.variant+'_V30_V12B_HDRI32_'+name+'.png'} for name in ('Hero','Detalle')]
        (out/('Escarcha_'+args.variant+'_V30_Audit.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print('GENESIS_V30_REAL_FROST_'+args.variant+'_CYCLES_FINISHED',json.dumps(detail),flush=True)
    finally:
        sys.argv=original_argv

if __name__=='__main__':main()
