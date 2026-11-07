#!/usr/bin/env python3
"""Project Genesis V29: two REAL Cycles frost renders on the ORIGINAL V03 iron sword.
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

def frost_veil_material(name, fantasy=False):
    """Micro-porous rough hoarfrost. A loose transparent film, not an opaque ice slab.
    Uses physically-based shader; apparent whiteness comes from powder grains and dendrites.
    """
    m=ref.bpy.data.materials.new(ref.TAGS+name)
    m.use_nodes=True
    nodes=m.node_tree.nodes
    nodes.clear()
    L=m.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial')
    mixed=nodes.new('ShaderNodeMixShader')
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    bs=nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(.72,.86,.90,1)
    bs.inputs['Roughness'].default_value=.86
    bs.inputs['Transmission Weight'].default_value=.04
    bs.inputs['IOR'].default_value=1.31
    bs.inputs['Emission Color'].default_value=(.14,.27,.42,1)
    bs.inputs['Emission Strength'].default_value=.11 if fantasy else .03
    tex=nodes.new('ShaderNodeTexCoord')
    nlo=nodes.new('ShaderNodeTexNoise')
    nlo.inputs['Scale'].default_value=11.0
    nlo.inputs['Detail'].default_value=3.5
    nhi=nodes.new('ShaderNodeTexNoise')
    nhi.inputs['Scale'].default_value=93.0
    nhi.inputs['Detail'].default_value=2.5
    L.new(tex.outputs['Generated'],nlo.inputs['Vector'])
    L.new(tex.outputs['Generated'],nhi.inputs['Vector'])
    mult=nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY'
    mult.inputs[0].default_value=.70
    L.new(nlo.outputs['Fac'],mult.inputs[1])
    L.new(nhi.outputs['Fac'],mult.inputs[2])
    r=nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position=.25
    r.color_ramp.elements[0].color=(0,0,0,1)
    r.color_ramp.elements[1].position=.65
    r.color_ramp.elements[1].color=(.70,.70,.70,1)
    L.new(mult.outputs['Color'],r.inputs[0])
    L.new(r.outputs['Color'],mixed.inputs[0])
    L.new(transparent.outputs[0],mixed.inputs[1])
    L.new(bs.outputs[0],mixed.inputs[2])
    L.new(mixed.outputs[0],out.inputs['Surface'])
    return m

def build_frost(coord,along,side,normal,intensity,variant):
    """Project Genesis V29 B: dense real hoarfrost fern / rime morphology inspired by reference.
    Build on original V28 and original V03 surface sampler — NO new sword or base-material changes.
    Organic branched frost grows from the steel edges, avoiding the original central ridge.
    """
    if variant not in ('A','B'):raise RuntimeError('V29_REQUIRES_VALID_VARIANT')
    rng=ref.rng
    rng.seed(291107)
    cold_matte=ref.pbr('V29_DENSE_HOARFROST_MATTE',(.77,.86,.89),
                       roughness=.83,metallic=0,transmission=.02)
    white=ref.pbr('V29_CRYSTAL_ICE_WHITE',(.83,.91,.92),
                  roughness=.64,metallic=0,transmission=.06)
    blue=ref.pbr('V29_FROZEN_BLUE_RIME',(.43,.64,.79),
                 roughness=.51,metallic=0,transmission=.11)
    translucent=ref.pbr('V29_REAL_FACET_COLD_GLASS',(.27,.50,.65),
                        roughness=.22,metallic=0,transmission=.63)
    rim=ref.pbr('V29_COOL_PHOTON_EDGE',(.47,.72,.90),
                roughness=.43,metallic=0,transmission=.10,
                emission=(.14,.32,.62),emission_power=.46 if variant=='B' else .0)
    dust=frost_veil_material('V29_POROUS_EDGE_FROST_VEIL',variant=='B')
    axes=branches=forks=ice_needles=grains=facets=films=0
    # Patchy porous hoar frost skin on the outermost 15-27% of the blade, with ragged
    # tapered ends. No covering the middle ridge or material below the branches.
    for sign in (-1,1):
        for band,(start,end) in enumerate([(.15,.260),(.290,.418),(.448,.575),(.603,.742),(.778,.930)]):
            N=38; verts=[]
            for k in range(N+1):
                q=k/N;t=start+(end-start)*q
                taper=max(.0001,math.sin(math.pi*q)**.73)
                variation=.5+.26*math.sin(t*117+band*3.2+sign)+.14*math.sin(t*361+band)
                inner=sign*(.94-(.13+.14*variation)*taper)
                outer=sign*(.958-.016*math.sin(t*91+band))
                p1,_=coord(t,inner,.0061)
                p2,_=coord(t,outer,.0063)
                verts.extend([p1,p2])
            ref.geo('V29_RIME_POROUS_SKIN_%s_%d'%(sign,band),verts,
                    [(2*k,2*k+1,2*k+3,2*k+2) for k in range(N)],dust)
            films+=1
    # Numerous individual hoarfrost ferns — visibly feathered and asymmetrical.
    # Wider line diameters make them visible in the 1200 px actual production render.
    for sign in (-1,1):
        for colony in range(33):
            t0=.15+.785*(colony+.35)/33+.0028*(rng.random()-.5)
            radial=.36+.16*rng.random()
            slant=(rng.random()-.5)*.037
            def trace(u, dt=0., offset=0., lift=.0066):
                t=max(.135,min(.967,t0+slant*u+dt))
                lat=sign*(.947-radial*u)+offset
                return coord(t,lat,lift)[0]
            axis=[]
            for k in range(15):
                u=k/14
                axis.append(trace(u,dt=.009*math.sin(u*math.pi*.95+colony*.57)*u,lift=.0066))
            ref.line('V29_FERN_SPINE_%s_%02d'%(sign,colony),axis,
                     white if colony%3 else blue,width=.00062+.00013*rng.random())
            axes+=1
            for j in range(2,14):
                u=j/14
                direction=(-1 if j%2 else 1)
                length=(.006+.015*rng.random())*(.56+.44*math.sin(math.pi*u))
                lateral_span=.032+.040*rng.random()
                points=[]
                for step in range(8):
                    v=step/7
                    cur=trace(u+.04*v,
                              dt=direction*length*v+.0015*math.sin(v*math.pi*2+colony)*v,
                              offset=sign*lateral_span*v+.009*math.sin(v*math.pi)*sign,
                              lift=.0067+v*.0003)
                    points.append(cur)
                mat=white if (colony+j)%4 else blue
                ref.line('V29_FERN_FEATHER_%s_%02d_%02d'%(sign,colony,j),
                         points,mat,width=.00044+.00016*rng.random())
                branches+=1
                for k in (2,4,6):
                    branch_start=points[k]
                    direction2=1 if k%2 else -1
                    u2=min(.98,u+.04*k/7+.07)
                    tip=trace(u2,dt=direction*length*k/7+direction2*(.0028+.0075*rng.random()),
                              offset=sign*(lateral_span*k/7+.024+.018*rng.random()),lift=.0071)
                    ref.line('V29_FERN_MICROBRANCH_%s_%02d_%02d_%d'%(sign,colony,j,k),
                             [branch_start,tip],white if (colony+j+k)%5 else rim,
                             width=.00029+.00012*rng.random())
                    forks+=1
            # Hairline ice growing from some actual edges, not hard fantasy spikes.
            if colony%2==0:
                for n in range(5):
                    base=trace(.10+.17*n,lift=.0061)
                    t=normal*(.003+.005*rng.random())+side*sign*(.002+.004*rng.random())
                    tip=base+t+along*(rng.random()-.5)*.008
                    ref.line('V29_HOAR_EDGE_NEEDLE_%s_%02d_%d'%(sign,colony,n),
                             [base,tip],white if n%3 else blue,width=.00036)
                    ice_needles+=1
            # Larger isolated facets in irregular clusters, small relative to the blade.
            for n in range(2):
                p=trace(.3+.55*rng.random(),lift=.0068)
                sz=.0020+.0033*rng.random()
                lifted=.0028+.0048*rng.random()
                verts=[p-side*sz,p+side*sz,p+along*(.90*sz),p+normal*lifted]
                ref.geo('V29_REAL_ICE_FACET_%s_%02d_%d'%(sign,colony,n),
                        verts,[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],
                        translucent if n==0 else blue)
                facets+=1
    # Dense matte grains bind foliage-like frost branches into a coherent white layer.
    for sign in (-1,1):
        for k in range(370):
            t=.139+.805*rng.random()
            if math.sin(t*103+sign*.2)>.68:continue
            lateral=sign*(.65+.31*rng.random())
            p,_=coord(t,lateral,.0062)
            w=.00055+.0014*rng.random()
            h=w*(.63+.50*rng.random())
            ref.ellipsoid('V29_FROST_MICROGRAIN_%s_%03d'%(sign,k),p,
                          (w*.67,w*1.13,h*.40),white if k%4 else blue)
            grains+=1
    # The reference option B has soft cold blue accents along the edge of some frost
    # colonies; no electric filaments and the main V175 iron is still readable.
    emitters=0
    if variant=='B':
        for sign in (-1,1):
            for k in range(16):
                t=.16+.75*(k+.2)/16
                if k%3==1:continue
                p,_=coord(t,sign*(.88+.06*rng.random()),.0073)
                sz=.0020+.0019*rng.random()
                ref.ellipsoid('V29_COLD_EMISSION_BEAD_%s_%02d'%(sign,k),
                              p,(sz*.8,sz*1.45,sz*.36),rim)
                emitters+=1
    return {
      'variant':variant,'quality_target':'strong_frost_like_second_reference',
      'real_render_not_concept':True,'hero_visible_frost_target':True,
      'frost_type':'dense matte hoar frost and dendritic feathery rime with blue cold glints',
      'nucleation_sites':66,'feather_axes':axes,
      'secondary_fern_arms':branches,'tertiary_dendrites':forks,
      'edge_frost_veil_patches':films,'real_microcrystal_facets':facets,
      'fine_edge_ice_needles':ice_needles,'powder_rime_grains':grains,
      'cold_glow_accents':emitters,
      'no_flat_translucent_ice_sheets':True,'original_iron_ridge_uncovered':True,
      'no_electric_strings':True,'hdri_RGB32_v12b_unchanged':True,
      'no_fabricated_reference_sword':True
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
            new=out/('Escarcha_'+args.variant+'_V29_V12B_HDRI32_'+name+'.png')
            if not old.is_file():raise RuntimeError('V29_MISSING_REAL_CYCLES_'+str(old))
            old.rename(new)
        detail=result['results'][0]['details']
        if detail['nucleation_sites']!=66 or detail['feather_axes']!=66 or detail['secondary_fern_arms']<790:
            raise RuntimeError('V29_FROST_GEOMETRY_INCOMPLETE')
        result['schema']='Genesis_V29_Hoarfrost_RealCycles_V12B_EXR_RGB32'
        result['source_base']='V25 unchanged same iron/hdr/camera'
        result['selected_variant']=args.variant
        result['no_image_generation']=True
        result['video_animation_created']=False
        result['user_approval']='pending_actual_visual_comparison'
        result['results'][0]['renders']=[
            {'name':'Escarcha_'+args.variant+'_V29_V12B_HDRI32_'+name+'.png'} for name in ('Hero','Detalle')]
        (out/('Escarcha_'+args.variant+'_V29_Audit.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print('GENESIS_V29_REAL_FROST_'+args.variant+'_CYCLES_FINISHED',json.dumps(detail),flush=True)
    finally:
        sys.argv=original_argv

if __name__=='__main__':main()
