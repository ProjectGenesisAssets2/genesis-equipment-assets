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
    x_right=smooth_gate(x,.26,.34,True)
    one_edge=math_node(ns,links,'MULTIPLY',x_left,x_right)
    # Patch occupies only approximately 27% of blade length, not full span.
    y_left=smooth_gate(y,.39,.425)
    y_right=smooth_gate(y,.66,.705,True)
    length_patch=math_node(ns,links,'MULTIPLY',y_left,y_right)
    fixed_patch=math_node(ns,links,'MULTIPLY',one_edge,length_patch)
    # Branching ice vein texture, blue-gray cloudy body, not opaque white crystal.
    noise=ns.new('ShaderNodeTexNoise');noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=17
    noise.inputs['Detail'].default_value=5
    noise.inputs['Roughness'].default_value=.72
    links.new(uv.outputs['UV'],noise.inputs['Vector'])
    noise2=ns.new('ShaderNodeTexNoise');noise2.noise_dimensions='3D'
    noise2.inputs['Scale'].default_value=7
    noise2.inputs['Detail'].default_value=4.5
    links.new(noise.outputs['Color'],noise2.inputs['Vector'])
    vor=ns.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value=13.
    links.new(noise2.outputs['Color'],vor.inputs['Vector'])
    vein=ns.new('ShaderNodeMapRange');vein.clamp=True;vein.interpolation_type='SMOOTHSTEP'
    vein.inputs['From Min'].default_value=.012;vein.inputs['From Max'].default_value=.085
    vein.inputs['To Min'].default_value=.93;vein.inputs['To Max'].default_value=0
    links.new(vor.outputs['Distance'],vein.inputs['Value'])
    cloud=ns.new('ShaderNodeValToRGB')
    cloud.color_ramp.elements[0].position=.24
    cloud.color_ramp.elements[0].color=(.065,.095,.115,1)
    cloud.color_ramp.elements[1].position=.82
    cloud.color_ramp.elements[1].color=(.19,.285,.33,1)
    cloud.color_ramp.elements.new(.49).color=(.11,.17,.205,1)
    links.new(noise.outputs['Fac'],cloud.inputs['Fac'])
    icyWhite=ns.new('ShaderNodeMixRGB');icyWhite.blend_type='MIX'
    icyWhite.inputs[2].default_value=(.53,.65,.69,1)
    links.new(vein.outputs[0],icyWhite.inputs[0])
    links.new(cloud.outputs[0],icyWhite.inputs[1])
    bs=ns.new('ShaderNodeBsdfPrincipled')
    links.new(icyWhite.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value=.34
    bs.inputs['Roughness'].default_value=.35
    bs.inputs['Transmission Weight'].default_value=.045
    bs.inputs['IOR'].default_value=1.31
    rough=math_node(ns,links,'MULTIPLY',vein.outputs[0],.11)
    rough=math_node(ns,links,'ADD',rough,.30)
    links.new(rough,bs.inputs['Roughness'])
    trans=ns.new('ShaderNodeBsdfTransparent')
    mix=ns.new('ShaderNodeMixShader')
    ICE_VALUE=ns.new('ShaderNodeValue');ICE_VALUE.label='V31_ICE_INTENSITY_0_TO_100'
    # Strongly limited local icy patch: animate spatial emergence along the
    # blade, not merely global opacity. 0=no ice; 100=one localized edge band.
    # 101 frames of Blender node-keyframed intensity; smooth interpolated.
    for frame,value in ((1,0.),(21,.2),(41,.4),(61,.6),(81,.8),(101,1.)):
        ICE_VALUE.outputs[0].default_value=value
        ICE_VALUE.outputs[0].keyframe_insert('default_value',frame=frame)
    ICE_VALUE.outputs[0].default_value=1.
    # Moving growth front. Procedural noise gives irregular frost margins.
    ice_fraction=math_node(ns,links,'SUBTRACT',y,.39)
    ice_fraction=math_node(ns,links,'DIVIDE',ice_fraction,.31)
    noise_margin=math_node(ns,links,'SUBTRACT',noise.outputs['Fac'],.5)
    noise_margin=math_node(ns,links,'MULTIPLY',noise_margin,.17)
    ice_fraction=math_node(ns,links,'ADD',ice_fraction,noise_margin)
    advancing=math_node(ns,links,'SUBTRACT',ICE_VALUE.outputs[0],ice_fraction)
    advancing=smooth_gate(advancing,.0,.13)
    # Slight material translucence: even 100% must NOT become opaque cyan.
    local_mask=math_node(ns,links,'MULTIPLY',fixed_patch,advancing)
    irregular=math_node(ns,links,'MULTIPLY',local_mask,noise.outputs['Fac'])
    mask=math_node(ns,links,'MULTIPLY',irregular,.52)
    links.new(mask,mix.inputs[0]);links.new(trans.outputs[0],mix.inputs[1])
    links.new(bs.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
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
    DETAILS={'version':'V31','original_hielo_blend_applied':False,
             'source_hielo_blend':'Library source identified, not yet in GitHub',
             'material':'procedural preview of Hielo ingot colors/veins, NOT original node-tree',
             'limited_blade_length_fraction':.27,
             'max_local_opacity':.52,
             'single_edge_patch':True,
             'advancing_growth_front':True,
             'central_ridge_clear':True,'geometric_crystals_added':0,
             'animation_keyframes':{'1':0,'21':20,'41':40,'61':60,'81':80,'101':100},
             'original_sword_mesh_modified':False,
             'overlay_faces':len(faces)}
    return DETAILS

def render_levels(camera,out):
    name='Hero' if 'Hero' in out.name else 'Detalle'
    frames=[(1,0),(21,20),(41,40),(61,60),(81,80),(101,100)] if name=='Hero' else [(101,100)]
    last=None
    for frame,pct in frames:
        bpy.context.scene.frame_set(frame)
        out2=out.with_name('V32_Escarcha_'+str(pct)+'_'+name+'.png')
        last=ORIGINAL_RENDER(camera,out2)
    # Return a render already verified by original renderer
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
    audit['schema']='Genesis_V32_LocalizedIce_Animated_PRELIMINARY_Cycles32'
    audit['intensity_animation_created_in_blender']=True
    audit['material_source_exact_original_blend']=False
    audit['not_approved']=True
    audit['results'][0]['renders']=[{'name':p.name} for p in sorted(root.glob('V32_Escarcha_*.png'))]
    (root/'v32_escarcha_intensidad_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V32_PRELIMINARY_REAL_CYCLES_FINISHED',flush=True)

if __name__=='__main__':main()
