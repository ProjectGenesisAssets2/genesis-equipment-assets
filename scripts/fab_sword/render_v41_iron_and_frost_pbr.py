#!/usr/bin/env python3
"""Project Genesis V41 — original V175 HIELO material, spatial motion separated
from intensity on the ORIGINAL V03/V175/V12B iron sword. Experimental review only.
The source material is loaded byte-for-byte from user's preserved V175 .blend.
Its original shader node graph stays intact; only transparent blending and
subtle animated cold vein highlights are added to a separate blade overlay.
"""
import sys, json, hashlib, argparse, math, random
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v25_hielo_cycles_hdri32 as ref

MASTER_SOURCE_SHA='9a24ffe1865ccf33c80b535ba27db0726fa1caca0f352425c82c8ae91e34ec89'
MASTER_MATERIAL='M_Ingot_Universal_Affinity_HIELO'
MASTER_PATH=None
ICE_VALUE=None
MOTION=None
CRYSTAL_VALUES=[]
ORIGINAL_RENDER=ref.render
TAGS=ref.TAGS

def mathn(nodes, links, operation, a=None, b=None):
    n=nodes.new('ShaderNodeMath');n.operation=operation
    if a is not None:
        if hasattr(a,'node'):links.new(a,n.inputs[0])
        else:n.inputs[0].default_value=float(a)
    if b is not None:
        if hasattr(b,'node'):links.new(b,n.inputs[1])
        else:n.inputs[1].default_value=float(b)
    return n.outputs[0]

def smooth(nodes,links,value,a,b,reverse=False):
    n=nodes.new('ShaderNodeMapRange')
    n.clamp=True;n.interpolation_type='SMOOTHSTEP'
    n.inputs['From Min'].default_value=a
    n.inputs['From Max'].default_value=b
    if reverse:
        n.inputs['To Min'].default_value=1.0
        n.inputs['To Max'].default_value=0.0
    links.new(value,n.inputs['Value'])
    return n.outputs[0]

def add_ice_faceted_microcrystals(coord,along,side,normal):
    """Small irregular cohesive rime colonies, NOT isolated white rods.

    Low translucent ice shelves hug the actual V03 triangle-sampled blade.
    Short faceted microcrystals share each shelf's edge. Their microfacets
    reflect the real 32-bit EXR; no white emission or neon geometry.
    Source V03, original iron shader, and original ingot V175 stay intact.
    """
    global CRYSTAL_VALUES
    rng=random.Random(381108)
    materials=[]
    specifications=[
        ('V41_Rime_Glass',(.57,.68,.74,1),.20,.62,.25,.12,.62),
        ('V41_Rime_Coalesced',(.68,.76,.79,1),.36,.28,.17,.20,.58),
        ('V41_Rime_Microfacet',(.48,.60,.67,1),.24,.51,.30,.13,.57),
    ]
    for name,color,rough,transmission,coat,coat_rough,opacity in specifications:
        m=bpy.data.materials.new(name)
        m.use_nodes=True
        ns=m.node_tree.nodes; ns.clear()
        ln=m.node_tree.links
        output=ns.new('ShaderNodeOutputMaterial')
        principled=ns.new('ShaderNodeBsdfPrincipled')
        principled.inputs['Base Color'].default_value=color
        principled.inputs['Metallic'].default_value=.0
        principled.inputs['Roughness'].default_value=rough
        principled.inputs['Transmission Weight'].default_value=transmission
        principled.inputs['IOR'].default_value=1.31
        principled.inputs['Coat Weight'].default_value=coat
        principled.inputs['Coat Roughness'].default_value=coat_rough
        principled.inputs['Emission Strength'].default_value=0.
        transparent=ns.new('ShaderNodeBsdfTransparent')
        alpha=ns.new('ShaderNodeValue')
        alpha.name='V41_Facet_Intensity'
        alpha.label='Independent from animated frost phase'
        alpha.outputs[0].default_value=.5
        CRYSTAL_VALUES.append(alpha)
        blend=ns.new('ShaderNodeMixShader')
        strength=mathn(ns,ln,'MULTIPLY',alpha.outputs[0],opacity)
        ln.new(strength,blend.inputs[0])
        ln.new(transparent.outputs[0],blend.inputs[1])
        ln.new(principled.outputs['BSDF'],blend.inputs[2])
        ln.new(blend.outputs[0],output.inputs['Surface'])
        materials.append(m)
    verts=[];faces=[];indices=[]
    shelves=0;crystals=0
    bands=[(.422,.482),(.531,.605),(.658,.726)]
    for group,(lo,hi) in enumerate(bands):
        # Broad, broken shallow ice base: sloped across one cutting edge.
        # These sheets keep clusters visually attached to the blade.
        n=16
        beginning=len(verts)
        for j in range(n+1):
            q=j/n
            t=lo+(hi-lo)*q
            fade=math.sin(math.pi*q)**.8
            broad=.15+.055*math.sin(j*1.21+group*1.9)**2
            lat_outer=-.92+.018*math.sin(t*51+group)
            lat_inner=lat_outer+(broad*fade)
            inner,_=coord(t,lat_inner,.0052)
            outer,_=coord(t,lat_outer,.0055+.0009*fade)
            verts.extend([inner,outer])
        for j in range(n):
            faces.append((beginning+2*j,beginning+2*j+1,
                          beginning+2*j+3,beginning+2*j+2))
            indices.append(group%len(materials))
        shelves+=1
        # Facets in connected colonies, with staggered heights and orientation.
        for k in range(12):
            t=lo+(hi-lo)*(.08+.84*(k+rng.random()*.50)/12)
            t=min(hi-.004,max(lo+.004,t))
            lateral=-.89+.12*rng.random()
            length=.008+.012*rng.random()
            width=.0022+.0030*rng.random()
            height=.0015+.0023*rng.random()
            base_pos,_=coord(t,lateral,.00565)
            drift=side*((rng.random()-.5)*.006)
            peak=base_pos + along*(length*.55) + normal*height + drift
            # Five small facets all meet at one crystal tip; the basal
            # quadrilateral lies flush on the actual blade sample.
            corners=[
                base_pos-along*(length*.32)-side*width,
                base_pos-along*(length*.32)+side*width,
                base_pos+along*(length*.61)+side*(width*.68),
                base_pos+along*(length*.61)-side*(width*.68),
                peak,
            ]
            vi=len(verts)
            verts.extend(corners)
            for tri in ((0,2,1),(0,3,2),(0,1,4),
                        (1,2,4),(2,3,4),(3,0,4)):
                faces.append(tuple(vi+x for x in tri))
                indices.append((group+k)%len(materials))
            crystals+=1
    mesh=bpy.data.meshes.new('V41_CoalescedRimeColonies_Mesh')
    mesh.from_pydata([tuple(map(float,x)) for x in verts],[],faces)
    mesh.update()
    obj=bpy.data.objects.new(TAGS+'V41_CoalescedMicroCrystals_ReviewOnly',mesh)
    bpy.context.collection.objects.link(obj)
    for m in materials:mesh.materials.append(m)
    for polygon,idx in zip(mesh.polygons,indices):
        polygon.material_index=idx
    return {
        'facet_crystals':crystals,
        'facet_sheets':shelves,
        'facet_faces':len(faces),
        'facet_pbr_materials':len(materials),
        'facet_transmission':True,
        'facet_roughness_range':[.20,.36],
        'facet_animated_time':False,
        'intensity_controls_facets':True,
        'no_opaque_white_shards':True,
        'one_cutting_edge_only':True,
        'coalesced_clustering':True
    }

def add_ice_layer(coord,along,side,normal,intensity):
    global ICE_VALUE,MOTION
    if MASTER_PATH is None or not MASTER_PATH.exists():
        raise RuntimeError('V41_MISSING_ORIGINAL_MASTER_BLEND')
    sha=hashlib.sha256(MASTER_PATH.read_bytes()).hexdigest()
    if sha!=MASTER_SOURCE_SHA:raise RuntimeError('V41_ORIGINAL_BLEND_SHA_MISMATCH '+sha)
    with bpy.data.libraries.load(str(MASTER_PATH),link=False) as (src,dst):
        choices=[n for n in src.materials if n==MASTER_MATERIAL]
        if len(choices)!=1:
            raise RuntimeError('V41_MATERIAL_NOT_FOUND candidates='+repr([m for m in src.materials if 'HIELO' in m.upper()]))
        dst.materials=choices
    material=dst.materials[0]
    if material is None or not material.use_nodes:
        raise RuntimeError('V41_ORIGINAL_MATERIAL_IMPORT_FAILED')
    # Crucial: original V175 material nodes are retained; only the output is wrapped.
    nodes=material.node_tree.nodes; links=material.node_tree.links
    original_nodes=len(nodes)
    output=next((n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
    if output is None:output=next((n for n in nodes if n.type=='OUTPUT_MATERIAL'),None)
    if output is None or not output.inputs['Surface'].is_linked:
        raise RuntimeError('V41_ORIGINAL_MATERIAL_HAS_NO_SURFACE')
    surface_link=output.inputs['Surface'].links[0]
    original_shader=surface_link.from_socket
    links.remove(surface_link)
    missing_textures=[im.name for node in nodes if node.type=='TEX_IMAGE'
                      for im in [node.image] if im is None or not im.has_data]
    if missing_textures:
        raise RuntimeError('V41_MISSING_MASTER_TEXTURES '+repr(missing_textures))
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='V41_BladeUV'
    xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],xyz.inputs[0])
    u=xyz.outputs['X'];v=xyz.outputs['Y']
    # One cutting edge, no central ridge: irregular 32%-length frost footprint.
    x1=smooth(nodes,links,u,.035,.095)
    x2=smooth(nodes,links,u,.39,.51,True)
    edge=mathn(nodes,links,'MULTIPLY',x1,x2)
    y1=smooth(nodes,links,v,.235,.305)
    y2=smooth(nodes,links,v,.765,.835,True)
    area=mathn(nodes,links,'MULTIPLY',edge,mathn(nodes,links,'MULTIPLY',y1,y2))
    # Lateral frost-lace material only: fixed deposition shape, no recolouring
    # the steel elsewhere.  The irregular mask is spatially stationary; only
    # the cold filaments inside it evolve over time.
    stationary=nodes.new('ShaderNodeTexNoise')
    stationary.noise_dimensions='3D'
    stationary.inputs['Scale'].default_value=6.1
    stationary.inputs['Detail'].default_value=4.6
    stationary.inputs['Roughness'].default_value=.68
    links.new(uv.outputs['UV'],stationary.inputs['Vector'])
    granularity=smooth(nodes,links,stationary.outputs['Fac'],.26,.73)
    spatial_roughness=mathn(nodes,links,'ADD',
                            mathn(nodes,links,'MULTIPLY',granularity,.32),.68)
    spatial=mathn(nodes,links,'MULTIPLY',area,spatial_roughness)
    # User intensity never receives animation keys. All motion is driven by
    # the separate phase node, even at a fixed 20 or 100 percent.
    ICE_VALUE=nodes.new('ShaderNodeValue')
    ICE_VALUE.name='V41_Ice_Intensity'
    ICE_VALUE.label='V41_INTENSITY_FIXED_INDEPENDENT_OF_TIME'
    ICE_VALUE.outputs[0].default_value=.5
    MOTION=nodes.new('ShaderNodeValue')
    MOTION.name='V41_Ice_Animation_Time'
    MOTION.label='V41_SEAMLESS_VEIN_FLOW_TIME'
    for frame,value in ((1,0.),(97,1.)):
        MOTION.outputs[0].default_value=value
        MOTION.outputs[0].keyframe_insert('default_value',frame=frame)
    MOTION.outputs[0].default_value=0.
    # Timeline drives only the moving frost field, never the intensity.
    phase=mathn(nodes,links,'MULTIPLY',MOTION.outputs[0],math.tau)
    sine=mathn(nodes,links,'SINE',phase)
    cosine=mathn(nodes,links,'COSINE',phase)
    offset=nodes.new('ShaderNodeCombineXYZ')
    links.new(mathn(nodes,links,'MULTIPLY',sine,.22),offset.inputs['X'])
    links.new(mathn(nodes,links,'MULTIPLY',cosine,.28),offset.inputs['Y'])
    shifted=nodes.new('ShaderNodeVectorMath')
    shifted.operation='ADD'
    links.new(uv.outputs['UV'],shifted.inputs[0])
    links.new(offset.outputs[0],shifted.inputs[1])
    # Warped frost lattice: two branch scales, instead of uniform straight
    # light scratches. The large branch network has trailing small forks.
    warpnoise=nodes.new('ShaderNodeTexNoise')
    warpnoise.noise_dimensions='3D'
    warpnoise.inputs['Scale'].default_value=7.5
    warpnoise.inputs['Detail'].default_value=5.
    warpnoise.inputs['Roughness'].default_value=.70
    links.new(shifted.outputs[0],warpnoise.inputs['Vector'])
    warpscale=nodes.new('ShaderNodeVectorMath')
    warpscale.operation='SCALE'
    links.new(warpnoise.outputs['Color'],warpscale.inputs[0])
    warpscale.inputs['Scale'].default_value=.18
    warped=nodes.new('ShaderNodeVectorMath')
    warped.operation='ADD'
    links.new(shifted.outputs[0],warped.inputs[0])
    links.new(warpscale.outputs[0],warped.inputs[1])
    primary=nodes.new('ShaderNodeTexVoronoi')
    primary.feature='DISTANCE_TO_EDGE'
    primary.inputs['Scale'].default_value=8.8
    links.new(warped.outputs[0],primary.inputs['Vector'])
    mainvein=smooth(nodes,links,primary.outputs['Distance'],.020,.145,True)
    secondary=nodes.new('ShaderNodeTexVoronoi')
    secondary.feature='DISTANCE_TO_EDGE'
    secondary.inputs['Scale'].default_value=17.1
    links.new(warped.outputs[0],secondary.inputs['Vector'])
    twigs=smooth(nodes,links,secondary.outputs['Distance'],.013,.079,True)
    filaments=mathn(nodes,links,'MAXIMUM',mainvein,
                   mathn(nodes,links,'MULTIPLY',twigs,.43))
    # A moving crystallisation front flows along existing dendritic tracks.
    # Its phase loops, while opacity is always bounded by the fixed intensity.
    ypace=mathn(nodes,links,'MULTIPLY',v,1.35)
    wnoise=mathn(nodes,links,'MULTIPLY',warpnoise.outputs['Fac'],.24)
    ypace=mathn(nodes,links,'ADD',ypace,wnoise)
    phasepos=mathn(nodes,links,'SUBTRACT',ypace,MOTION.outputs[0])
    advancing=mathn(nodes,links,'SINE',
                    mathn(nodes,links,'MULTIPLY',phasepos,math.tau))
    advancing=smooth(nodes,links,advancing,-.24,.55)
    # The traveling growth front alters coverage even when small filaments
    # cannot be resolved at the full hero distance.
    # Animation is entirely time-driven; ICE_VALUE has NO animation keys.
    moving_front=mathn(nodes,links,'MULTIPLY',advancing,
                        mathn(nodes,links,'ADD',.28,
                              mathn(nodes,links,'MULTIPLY',filaments,.72)))
    active=mathn(nodes,links,'MULTIPLY',filaments,advancing)
    # Branches remain crystalline tracks; the PBR-coated front advances.
    # Whitish silver rather than neon blue, with low emission.
    ice_pbr=nodes.new('ShaderNodeBsdfPrincipled')
    ice_pbr.name='V41_MovingDendriticFrostHighlights'
    ice_pbr.inputs['Base Color'].default_value=(.58,.72,.78,1)
    ice_pbr.inputs['Roughness'].default_value=.20
    ice_pbr.inputs['Metallic'].default_value=.0
    ice_pbr.inputs['Transmission Weight'].default_value=.43
    ice_pbr.inputs['IOR'].default_value=1.31
    ice_pbr.inputs['Coat Weight'].default_value=.34
    ice_pbr.inputs['Coat Roughness'].default_value=.12
    # Microfacets change real specular directions under the actual EXR HDRI.
    # Normal detail changes only frost shader, never the approved iron metal.
    micro=nodes.new('ShaderNodeTexVoronoi')
    micro.feature='F1'
    micro.inputs['Scale'].default_value=34.
    links.new(warped.outputs[0],micro.inputs['Vector'])
    cracklet=smooth(nodes,links,micro.outputs['Distance'],.13,.65)
    relief=mathn(nodes,links,'ADD',
                 mathn(nodes,links,'MULTIPLY',cracklet,.68),
                 mathn(nodes,links,'MULTIPLY',twigs,.32))
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.19
    bump.inputs['Distance'].default_value=.0017
    links.new(relief,bump.inputs['Height'])
    links.new(bump.outputs['Normal'],ice_pbr.inputs['Normal'])
    ice_pbr.inputs['Emission Color'].default_value=(.27,.39,.44,1)
    links.new(mathn(nodes,links,'MULTIPLY',active,.016),
              ice_pbr.inputs['Emission Strength'])
    blend_material=nodes.new('ShaderNodeMixShader')
    # A traveling crystalline film changes actual reflection/refraction
    # rather than only a thin line's glow. Original metal remains unmodified.
    highlight=mathn(nodes,links,'ADD',
                    mathn(nodes,links,'MULTIPLY',moving_front,.76),
                    mathn(nodes,links,'MULTIPLY',active,.24))
    links.new(highlight,blend_material.inputs[0])
    links.new(original_shader,blend_material.inputs[1])
    links.new(ice_pbr.outputs['BSDF'],blend_material.inputs[2])
    transparency=nodes.new('ShaderNodeBsdfTransparent')
    surface=nodes.new('ShaderNodeMixShader')
    # Deliberately animated *coverage of the filaments*, not just their
    # emission. At 50% strength the network remains discernible in full hero.
    base_ice=mathn(nodes,links,'ADD',.060,
                   mathn(nodes,links,'MULTIPLY',moving_front,.94))
    strength=mathn(nodes,links,'MULTIPLY',spatial,base_ice)
    strength=mathn(nodes,links,'MULTIPLY',strength,ICE_VALUE.outputs[0])
    strength=mathn(nodes,links,'MULTIPLY',strength,2.04)
    strength=mathn(nodes,links,'MINIMUM',strength,.82)
    links.new(strength,surface.inputs[0])
    links.new(transparency.outputs[0],surface.inputs[1])
    links.new(blend_material.outputs[0],surface.inputs[2])
    links.new(surface.outputs[0],output.inputs['Surface'])
    # Original sword untouched: independent 3D-following UV mesh on V03 blade.
    rows,cols=138,30
    verts=[];uvdata=[];faces=[]
    for i in range(rows+1):
        t=.136+(.963-.136)*i/rows
        for j in range(cols+1):
            lateral=-.97+1.94*j/cols
            p,_=coord(t,lateral,.0052)
            verts.append(tuple(map(float,p)))
            uvdata.append((j/cols,i/rows))
    for i in range(rows):
        for j in range(cols):
            a=i*(cols+1)+j
            b=a+cols+1
            faces.append((a,a+1,b+1,b))
    mesh=bpy.data.meshes.new('V41_SeparateOriginalMaterialProjection')
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    layer=mesh.uv_layers.new(name='V41_BladeUV')
    for polygon in mesh.polygons:
        for li in polygon.loop_indices:
            vi=mesh.loops[li].vertex_index
            layer.data[li].uv=uvdata[vi]
    obj=bpy.data.objects.new(TAGS+'V41_USER_ORIGINAL_HIELO_SHADER_OVERLAY',mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    facets=add_ice_faceted_microcrystals(coord,along,side,normal)
    return {'version':'V41',
            'physical_ice_facets':facets,
            'source_blend_sha256':sha,
            'source_hielo_material':MASTER_MATERIAL,
            'source_original_node_count':original_nodes,
            'source_graph_preserved_and_only_wrapped':True,
            'original_hielo_blend_applied':True,
            'source_material_textures_missing':False,
            'single_cutting_edge':True,
            'blade_length_frost_envelope':.60,
            'motion_mode':'travelling translucent crystal front and branching specular frost, 0-100 intensity static',
            'frost_bump_microfacets':True,
            'ice_pbr_coat_weight':.34,
            'original_iron_shader_modified':False,
            'frost_strength_clamped_to':.82,
            'central_ridge_uncovered':True,
            'original_sword_mesh_modified':False,
            'intensity_node':ICE_VALUE.name,
            'intensity_has_animation_keyframes':False,
            'motion_node':MOTION.name,
            'motion_keyframes':{'1':0,'97':1},
            'intensity_motion_independent':True,
            'overlay_faces':len(faces)}

IRON_LIGHTS_ADDED=False

def add_iron_lighting():
    """Additional genuine softbox reflection on approved V12B iron, not shader change.

    V40 at 0% ice is already dull/oxidized, so reflection is a studio issue,
    not solely an overlay-ice issue. Keep original HDRI 32bpc and V12B lights,
    add a reflected elongated white strip and low-power neutral fill.
    """
    global IRON_LIGHTS_ADDED
    if IRON_LIGHTS_ADDED:
        return
    studio=ref.v12.studio
    source=ref.swordref.collect_blade()
    origin,along,side,normal,samples,data=source
    center=origin+along*.48
    # Both reflectors are physically soft, neutral and stationary between
    # all intensity/time comparisons. No steel texture alteration.
    studio.lamp('V41_IRON_PBR_SILVER_RIDGE_STRIP',
                (1.20,-1.85,2.75),center,145,.18,2.35,
                color=(.92,.95,1.))
    studio.lamp('V41_IRON_METAL_NEUTRAL_SOFT_FILL',
                (.10,1.7,2.75),center,62,.92,2.10,
                color=(1.,.975,.94))
    IRON_LIGHTS_ADDED=True

def render_frames(camera,output):
    add_iron_lighting()
    # Motion at constant 50% versus strength 20/50/100 at exactly the same time.
    name='Hero' if 'Hero' in output.name else 'Detalle'
    variants=[(0,1),(20,1),(50,1),(100,1)]
    if name=='Hero':
        variants += [(50,t) for t in (13,25,37,49,61,73,85,97)]
    else:variants=[(100,1)]
    last=None
    for intensity,frame in variants:
        bpy.context.scene.frame_set(frame)
        ICE_VALUE.outputs[0].default_value=intensity/100.
        for facet_value in CRYSTAL_VALUES:
            facet_value.outputs[0].default_value=intensity/100.
        path=output.with_name('V41_Escarcha_V175_I%03d_T%03d_%s.png'%(intensity,frame,name))
        last=ORIGINAL_RENDER(camera,path)
    return last

def main():
    global MASTER_PATH
    args0=list(sys.argv[sys.argv.index('--')+1:])
    parser=argparse.ArgumentParser()
    for nm in ('input','hdri','output-dir','preset','hielo-blend','samples'):
        parser.add_argument('--'+nm)
    parser.add_argument('--channels',nargs='+')
    args=parser.parse_args(args0)
    if args.channels!=['Hielo']:raise RuntimeError('V41_ONLY_HIELO')
    MASTER_PATH=Path(args.hielo_blend)
    ref.BUILDERS['Hielo']=add_ice_layer
    ref.render=render_frames
    sys.argv=['blender','--']+[s for option,val in
             (('--input',args.input),('--hdri',args.hdri),
              ('--output-dir',args.output_dir),('--preset',args.preset),
              ('--samples',args.samples))
             for s in (option,val)]+['--channels','Hielo']
    try: ref.main()
    finally: sys.argv=['blender','--']+args0
    root=Path(args.output_dir)
    audit=json.loads((root/'v25_hielo_cycles_audit.json').read_text())
    audit['schema']='Genesis_V41_ReflectiveIronAndDynamicIce_V175_Experimental'
    audit['material_source_exact_original_blend']=True
    audit['intensity_has_animation']=False
    audit['continuous_ice_motion_animated_in_blender']=True
    audit['intensity_and_motion_independent']=True
    audit['not_approved']=True
    audit['experimental_studio_light_added']=True
    audit['iron_base_material_preserved']=True
    audit['studio_lights']=['V41_IRON_PBR_SILVER_RIDGE_STRIP','V41_IRON_METAL_NEUTRAL_SOFT_FILL']
    audit['results'][0]['renders']=[{'name':x.name} for x in sorted(root.glob('V41_Escarcha_*.png'))]
    (root/'v41_hierro_escarcha_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V41_ORIGINAL_V175_HIELO_REAL_CYCLES_COMPLETE',flush=True)

if __name__=='__main__':main()
