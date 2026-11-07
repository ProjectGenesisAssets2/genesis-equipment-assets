#!/usr/bin/env python3
"""V31 preliminary Cycles material-placement and intensity test on actual V03 sword.
Uses approved V175/V12B iron and verified 32bpc EXR, with a *procedural
lookdev approximation* of the located V175 Hielo ingot. Does NOT claim exact
shader node transfer from the original Library .blend; that binary is NOT in git.
No V28-V30 ice crystal geometry. Unapproved isolated visual experiment.
"""
import sys, json, argparse, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v25_hielo_cycles_hdri32 as ref

bpy=ref.bpy
ICE_VALUE=None
DETAILS=None
ORIGINAL_RENDER=ref.render

def math_node(nodes, links, op, a, b=None, value=None):
    n=nodes.new('ShaderNodeMath');n.operation=op
    if hasattr(a,'node'):links.new(a,n.inputs[0])
    elif a is not None:n.inputs[0].default_value=a
    if b is not None:
        if hasattr(b,'node'):links.new(b,n.inputs[1])
        else:n.inputs[1].default_value=b
    if value is not None:n.inputs[1].default_value=value
    return n.outputs[0]

def build_ice_overlay(coord, along, side, normal, intensity):
    global ICE_VALUE, DETAILS
    m=bpy.data.materials.new('V31_PRELIMINARY_ICE_INGOT_COLOR_PLACEMENT')
    m.use_nodes=True
    ns=m.node_tree.nodes;ns.clear();links=m.node_tree.links
    out=ns.new('ShaderNodeOutputMaterial')
    uv=ns.new('ShaderNodeUVMap');uv.uv_map='V31_BladeUV'
    split=ns.new('ShaderNodeSeparateXYZ');links.new(uv.outputs['UV'],split.inputs[0])
    # V32: Limit ice to a single asymmetric near-edge patch, not both sides.
    # The center ridge remains bare iron; growth spreads along the blade at
    # increasing intensity (rather than washing the whole blade blue).
    x=split.outputs['X']; y=split.outputs['Y']
    def smooth_gate(socket,lo,hi,reverse=False):
        n=ns.new('ShaderNodeMapRange');n.clamp=True
        n.interpolation_type='SMOOTHSTEP'
        n.inputs['From Min'].default_value=lo;n.inputs['From Max'].default_value=hi
        if reverse:
            n.inputs['To Min'].default_value=1
            n.inputs['To Max'].default_value=0
        links.new(socket,n.inputs['Value'])
        return n.outputs[0]
    # Narrow band ONLY near one cutting edge: 0.05..0.28 of UV width.
    x_left=smooth_gate(x,.045,.095)
    x_right=smooth_gate(x,.33,.45,True)
    one_edge=math_node(ns,links,'MULTIPLY',x_left,x_right)
    # Patch occupies only approximately 27% of blade length, not full span.
    y_left=smooth_gate(y,.32,.355)
    y_right=smooth_gate(y,.72,.76,True)
    length_patch=math_node(ns,links,'MULTIPLY',y_left,y_right)
    fixed_patch=math_node(ns,links,'MULTIPLY',one_edge,length_patch)
    # V34: visibly animated frosty veins on ONE localized blade-edge patch.
    # The original metal and center ridge are not modified.
    # Ice_Intensity has NO animation keys; Ice_Time loops separately.
    ICE_VALUE=ns.new('ShaderNodeValue')
    ICE_VALUE.name='V34_Ice_Intensity'
    ICE_VALUE.label='V34_ICE_INTENSITY_CONSTANT_0_TO_100'
    ICE_VALUE.outputs[0].default_value=.5
    motion=ns.new('ShaderNodeValue')
    motion.name='V34_Ice_Animation_Time'
    motion.label='V34_ICE_TIME_SEAMLESS_0_TO_1'
    for frame,value in ((1,0.),(97,1.)):
        motion.outputs[0].default_value=value
        motion.outputs[0].keyframe_insert('default_value',frame=frame)
    motion.outputs[0].default_value=0.
    # Moving noise domain gives actual displacement of branching frost texture.
    angle=math_node(ns,links,'MULTIPLY',motion.outputs[0],math.tau)
    sx=math_node(ns,links,'SINE',angle)
    cy=math_node(ns,links,'COSINE',angle)
    sx=math_node(ns,links,'MULTIPLY',sx,.18)
    cy=math_node(ns,links,'MULTIPLY',cy,.22)
    offset=ns.new('ShaderNodeCombineXYZ')
    links.new(sx,offset.inputs['X'])
    links.new(cy,offset.inputs['Y'])
    move=ns.new('ShaderNodeVectorMath');move.operation='ADD'
    links.new(uv.outputs['UV'],move.inputs[0])
    links.new(offset.outputs[0],move.inputs[1])
    noise=ns.new('ShaderNodeTexNoise')
    noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=10.5
    noise.inputs['Detail'].default_value=5.5
    noise.inputs['Roughness'].default_value=.68
    links.new(move.outputs[0],noise.inputs['Vector'])
    warp=ns.new('ShaderNodeVectorMath');warp.operation='SCALE'
    links.new(noise.outputs['Color'],warp.inputs[0])
    warp.inputs['Scale'].default_value=.16
    warped=ns.new('ShaderNodeVectorMath');warped.operation='ADD'
    links.new(move.outputs[0],warped.inputs[0])
    links.new(warp.outputs[0],warped.inputs[1])
    vor=ns.new('ShaderNodeTexVoronoi')
    vor.feature='DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value=12.0
    links.new(warped.outputs[0],vor.inputs['Vector'])
    vein=ns.new('ShaderNodeMapRange');vein.clamp=True
    vein.interpolation_type='SMOOTHSTEP'
    vein.inputs['From Min'].default_value=.018
    vein.inputs['From Max'].default_value=.105
    vein.inputs['To Min'].default_value=1
    vein.inputs['To Max'].default_value=0
    links.new(vor.outputs['Distance'],vein.inputs['Value'])
    # A moving light front reveals icy *veins* in succession. At constant
    # intensity, the bright section travels along the blade and loops.
    stripes=math_node(ns,links,'MULTIPLY',split.outputs['Y'],3.4)
    time_shift=math_node(ns,links,'SUBTRACT',stripes,motion.outputs[0])
    twopi=math_node(ns,links,'MULTIPLY',time_shift,math.tau)
    phase=math_node(ns,links,'SINE',twopi)
    wave=ns.new('ShaderNodeMapRange');wave.clamp=True
    wave.interpolation_type='SMOOTHSTEP'
    wave.inputs['From Min'].default_value=-.18
    wave.inputs['From Max'].default_value=.83
    links.new(phase,wave.inputs['Value'])
    active_veins=math_node(ns,links,'MULTIPLY',vein.outputs[0],wave.outputs[0])
    faint_veins=math_node(ns,links,'MULTIPLY',vein.outputs[0],.18)
    vein_bright=math_node(ns,links,'MULTIPLY',active_veins,.82)
    vein_bright=math_node(ns,links,'ADD',vein_bright,faint_veins)
    cloud=ns.new('ShaderNodeValToRGB')
    cloud.color_ramp.elements[0].position=.21
    cloud.color_ramp.elements[0].color=(.065,.095,.115,1)
    cloud.color_ramp.elements[1].position=.79
    cloud.color_ramp.elements[1].color=(.22,.34,.40,1)
    cloud.color_ramp.elements.new(.46).color=(.11,.17,.20,1)
    links.new(noise.outputs['Fac'],cloud.inputs['Fac'])
    icy_white=ns.new('ShaderNodeMixRGB')
    icy_white.blend_type='MIX'
    links.new(vein_bright,icy_white.inputs[0])
    links.new(cloud.outputs[0],icy_white.inputs[1])
    icy_white.inputs[2].default_value=(.80,.89,.93,1)
    bs=ns.new('ShaderNodeBsdfPrincipled')
    links.new(icy_white.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value=.35
    bs.inputs['Roughness'].default_value=.38
    bs.inputs['Transmission Weight'].default_value=.035
    bs.inputs['IOR'].default_value=1.31
    bs.inputs['Emission Color'].default_value=(.30,.50,.58,1)
    emission=math_node(ns,links,'MULTIPLY',active_veins,.26)
    links.new(emission,bs.inputs['Emission Strength'])
    # Mask is spatially limited and weighted by independently fixed intensity.
    # Veins shimmer while the base remains dark steel; no full-cyan blade.
    base_opacity=math_node(ns,links,'MULTIPLY',wave.outputs[0],.30)
    frost_opacity=math_node(ns,links,'MULTIPLY',active_veins,.64)
    ice_opacity=math_node(ns,links,'ADD',base_opacity,frost_opacity)
    ice_opacity=math_node(ns,links,'ADD',ice_opacity,.20)
    capped=math_node(ns,links,'MINIMUM',ice_opacity,.80)
    confined=math_node(ns,links,'MULTIPLY',fixed_patch,capped)
    mask=math_node(ns,links,'MULTIPLY',confined,ICE_VALUE.outputs[0])
    trans=ns.new('ShaderNodeBsdfTransparent')
    mix=ns.new('ShaderNodeMixShader')
    links.new(mask,mix.inputs[0])
    links.new(trans.outputs[0],mix.inputs[1])
    links.new(bs.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],out.inputs['Surface'])
    # Surface sampled directly from original V03 blade triangles, without edits.
    rows,cols=130,24
    verts=[];uvs=[];faces=[]
    for i in range(rows+1):
        t=.136+(.963-.136)*i/rows
        for j in range(cols+1):
            lateral=-.970+1.94*j/cols
            p,_=coord(t,lateral,.0055)
            verts.append(tuple(map(float,p)))
            uvs.append((j/cols,i/rows))
    for i in range(rows):
        for j in range(cols):
            a=i*(cols+1)+j;b=a+cols+1
            faces.append((a,a+1,b+1,b))
    mesh=bpy.data.meshes.new('V31_SAMPLED_BLADE_UV_MESH')
    mesh.from_pydata(verts,[],faces);mesh.update()
    uvLayer=mesh.uv_layers.new(name='V31_BladeUV')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index
            uvLayer.data[li].uv=uvs[vi]
    obj=bpy.data.objects.new(ref.TAGS+'V31_SAMPLED_FROST_OVERLAY',mesh)
    bpy.context.collection.objects.link(obj);mesh.materials.append(m)
    DETAILS={'version':'V34','original_hielo_blend_applied':False,
             'material':'provisional procedural lookdev, original .blend not yet transferred',
             'limited_blade_length_fraction':.40,'single_edge_patch':True,
             'max_local_opacity_factor':.80,
             'central_ridge_clear':True,'geometric_crystals_added':0,
             'intensity_node':'V34_Ice_Intensity',
             'intensity_has_animation_keyframes':False,
             'animated_time_node':'V34_Ice_Animation_Time',
             'time_loop_keyframes':{'1':0,'97':1},
             'moving_veins':True,'moving_wave':True,
             'intensity_and_time_independent':True,
             'original_sword_mesh_modified':False,
             'overlay_faces':len(faces)}
    return DETAILS

def render_levels(camera,out):
    # Constant-intensity loop plus separate static comparisons at the same time.
    name='Hero' if 'Hero' in out.name else 'Detalle'
    variants=[(20,1),(50,1),(100,1)] if name=='Hero' else [(100,1)]
    if name=='Hero':
        variants += [(50,13),(50,25),(50,37),(50,49),(50,61),(50,73),(50,85),(50,97)]
    last=None
    for intensity,frame in variants:
        bpy.context.scene.frame_set(frame)
        ICE_VALUE.outputs[0].default_value=intensity/100.
        path=out.with_name('V34_Escarcha_I'+str(intensity)+'_T'+str(frame)+'_'+name+'.png')
        last=ORIGINAL_RENDER(camera,path)
    return last

def main():
    parser=argparse.ArgumentParser()
    args0=sys.argv[sys.argv.index('--')+1:]
    parser.add_argument('--input');parser.add_argument('--hdri');parser.add_argument('--output-dir')
    parser.add_argument('--preset');parser.add_argument('--samples');parser.add_argument('--channels',nargs='+')
    opts=parser.parse_args(args0)
    if opts.channels!=['Hielo']:raise RuntimeError('V31 only Hielo')
    ref.BUILDERS['Hielo']=build_ice_overlay
    ref.render=render_levels
    ref.main()
    root=Path(opts.output_dir)
    audit=json.loads((root/'v25_hielo_cycles_audit.json').read_text())
    audit['schema']='Genesis_V34_IndependentTimeIntensity_PRELIMINARY_Cycles32'
    audit['intensity_animation_created_in_blender']=False
    audit['continuous_ice_motion_animated_in_blender']=True
    audit['intensity_and_motion_independent']=True
    audit['material_source_exact_original_blend']=False
    audit['not_approved']=True
    audit['results'][0]['renders']=[{'name':p.name} for p in sorted(root.glob('V34_Escarcha_*.png'))]
    (root/'v34_escarcha_movimiento_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V34_MOVEMENT_INDEPENDENT_INTENSITY_REAL_CYCLES_FINISHED',flush=True)

if __name__=='__main__':main()
