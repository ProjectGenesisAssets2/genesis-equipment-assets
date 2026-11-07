#!/usr/bin/env python3
"""Project Genesis V28: two REAL Cycles frost renders on the ORIGINAL V03 iron sword.
A = physical matte hoarfrost/dendrites; B = same real frost plus tiny cold luminous
crystal tips. No concept generation. Preserves V12B original iron, correct 32bpc EXR HDRI,
camera and Cycles studio by calling established V25 renderer without altering sources.
Only VFX geometry and surface materials are swapped in memory.
"""
import sys, math, json, hashlib, argparse
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v25_hielo_cycles_hdri32 as ref

def build_frost(coord,along,side,normal,intensity,variant):
    if variant not in ('A','B'):
        raise RuntimeError('V28_WRONG_VARIANT')
    rng=ref.rng
    rng.seed(281107 if variant=='A' else 281107)  # EXACT same geometry and lighting; only material accents change
    vfx=ref.TAGS
    assert vfx=='GENESIS_V22_'   # use same prefix so V25 audit/cleanup only affects our new VFX
    cold_matte=ref.pbr('V28_HOARFROST_WHITISH_RIME',(.69,.77,.79),
                       roughness=.86,metallic=0,transmission=.015)
    crystal_silver=ref.pbr('V28_MICRO_ICE_SURFACE',(.49,.65,.73),
                           roughness=.57,metallic=0,transmission=.13)
    powder=ref.pbr('V28_WHITE_FROST_GRAINS',(.79,.81,.80),
                    roughness=.91,metallic=0,transmission=0)
    mint=ref.pbr('V28_BLUE_DARK_CRYSTAL',(.23,.43,.57),
                  roughness=.29,metallic=0,transmission=.38)
    if variant=='B':
        luminous=ref.pbr('V28_SUBTLE_COLD_BIOLUMINESCENCE',(.42,.73,.85),
                         roughness=.43,metallic=0,transmission=.17,
                         emission=(.18,.41,.67),emission_power=.34)
        glow=ref.pbr('V28_SUBTLE_REFRACTIVE_EDGE',(.53,.79,.83),
                     roughness=.22,metallic=0,transmission=.45,
                     emission=(.08,.21,.37),emission_power=.19)
    else:
        luminous=crystal_silver
        glow=cold_matte
    branches=0;subbranches=0;axes=0;microcrystals=0;powder_grains=0;tips=0
    # Rime deposits arise from irregular nucleation sites at the exposed edges.
    # Each site grows thin feathery branching ice into the blade surface, while
    # the central ridge remains mostly original steel, with preserved V175 highlights.
    for sign in (-1,1):
        for colony in range(24):
            t0=.143+.79*(colony+.38)/24 +.0038*(rng.random()-.5)
            t0=max(.135,min(.95,t0))
            extent=.095+.095*rng.random()
            drift=(rng.random()-.5)*.028
            def trace(u, side_shift=0., long_shift=0., height=.0054):
                t=max(.12,min(.967,t0+drift*u+long_shift))
                lateral=sign*(.95-extent*u)+side_shift
                return coord(t,lateral,height)[0]
            central=[]
            for k in range(10):
                u=k/9
                central.append(trace(u,sign*.014*math.sin(u*math.pi*1.3+colony*.59)*u,
                                     .008*math.sin(u*math.pi*.75+colony*.51)*u))
            ref.line('V28_DENDRITIC_ROOT_%s_%02d'%(sign,colony),central,
                     cold_matte,width=.00039+.00017*rng.random())
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
                ref.line('V28_FROST_FERN_ARM_%s_%02d_%02d'%(sign,colony,j),arm,
                         cold_matte if j%3 else crystal_silver,
                         width=.00024+.00015*rng.random())
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
                    ref.line('V28_DENDRITE_TWIG_%s_%02d_%02d_%02d'%(sign,colony,j,b),
                             [p,branch_tip],crystal_silver if (colony+j+b)%4 else powder,
                             width=.00016+.00010*rng.random())
                    subbranches+=1
            # White hoar grain scattered at frost source (tiny physical beads).
            for n in range(4):
                u=.10+.75*rng.random()
                p=trace(u,side_shift=sign*(rng.random()-.5)*.043,height=.0053)
                size=.00088+.00120*rng.random()
                ref.ellipsoid('V28_HOAR_GRAIN_%s_%02d_%d'%(sign,colony,n),
                              p,(size*.58,size*1.42,size*.42),powder)
                powder_grains+=1
            # Very small tetrahedral ice crystals are sparse ornaments of the frost,
            # never the main form, unlike V25.
            for n in range(2):
                p=trace(.40+.45*rng.random(),height=.0057)
                sz=.0017+.0025*rng.random()
                prism=[p-side*sz,p+side*sz,p+along*(sz*.65),p+normal*(.0017+.0025*rng.random())]
                material=mint if (colony+n)%5==0 else crystal_silver
                ref.geo('V28_MICRO_FACET_%s_%02d_%d'%(sign,colony,n),
                        prism,[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],material)
                microcrystals+=1
            if variant=='B' and colony%4==0:
                # A FEW teal highlights: visually not electrical, no helices.
                p=trace(.72,height=.0075)
                sz=.0014+.001*rng.random()
                ref.ellipsoid('V28_GENTLE_COLD_TIP_%s_%02d'%(sign,colony),
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
            length=.0011+.0026*rng.random()
            width=.0007+.001*rng.random()
            ref.ellipsoid('V28_EDGE_FROST_%s_%03d'%(sign,n),p,
                          (width,length,width*.31),glow if variant=='B' and n%17==0 else powder)
            powder_grains+=1
    # Light atmospheric frost is primarily matte, no neon electric edges.
    return {
      'variant':variant,'type':'real_hoarfrost' if variant=='A' else 'hoarfrost_slightly_enchanted',
      'principal_form':'feathery branching matte rime adherent to original steel',
      'nucleation_sites':48,'feather_axes':axes,'secondary_fern_arms':branches,
      'tertiary_dendrites':subbranches,'powder_rime_grains':powder_grains,
      'tiny_faceted_microcrystals':microcrystals,
      'cold_fantasy_tips':tips,'hero_light':'original_V12B_32bpc_EXR',
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
            new=out/('Escarcha_'+args.variant+'_V28_V12B_HDRI32_'+name+'.png')
            if not old.is_file():raise RuntimeError('V28_MISSING_REAL_CYCLES_'+str(old))
            old.rename(new)
        detail=result['results'][0]['details']
        if detail['nucleation_sites']!=48 or detail['feather_axes']!=48 or detail['secondary_fern_arms']<320:
            raise RuntimeError('V28_FROST_GEOMETRY_INCOMPLETE')
        result['schema']='Genesis_V28_Hoarfrost_RealCycles_V12B_EXR_RGB32'
        result['source_base']='V25 unchanged same iron/hdr/camera'
        result['selected_variant']=args.variant
        result['no_image_generation']=True
        result['video_animation_created']=False
        result['user_approval']='pending_actual_visual_comparison'
        result['results'][0]['renders']=[
            {'name':'Escarcha_'+args.variant+'_V28_V12B_HDRI32_'+name+'.png'} for name in ('Hero','Detalle')]
        (out/('Escarcha_'+args.variant+'_V28_Audit.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print('GENESIS_V28_REAL_FROST_'+args.variant+'_CYCLES_FINISHED',json.dumps(detail),flush=True)
    finally:
        sys.argv=original_argv

if __name__=='__main__':main()
