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
    # No full-coverage frozen sword: only the central 35-40 percent length
    # and the two outer blade bands, with metallic ridge left visible.
    edgeDistance=math_node(ns,links,'SUBTRACT',split.outputs['X'],.5)
    absEdge=math_node(ns,links,'ABSOLUTE',edgeDistance)
    ridge=ns.new('ShaderNodeMapRange');ridge.clamp=True;ridge.interpolation_type='SMOOTHSTEP'
    ridge.inputs['From Min'].default_value=.10;ridge.inputs['From Max'].default_value=.22
    links.new(absEdge,ridge.inputs['Value'])
    low=ns.new('ShaderNodeMapRange');low.clamp=True;low.interpolation_type='SMOOTHSTEP'
    low.inputs['From Min'].default_value=.28;low.inputs['From Max'].default_value=.34
    links.new(split.outputs['Y'],low.inputs['Value'])
    hi=ns.new('ShaderNodeMapRange');hi.clamp=True;hi.interpolation_type='SMOOTHSTEP'
    hi.inputs['From Min'].default_value=.66;hi.inputs['From Max'].default_value=.72
    hi.inputs['To Min'].default_value=1;hi.inputs['To Max'].default_value=0
    links.new(split.outputs['Y'],hi.inputs['Value'])
    span=math_node(ns,links,'MULTIPLY',low.outputs[0],hi.outputs[0])
    limited=math_node(ns,links,'MULTIPLY',span,ridge.outputs[0])
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
    cloud.color_ramp.elements[0].color=(.065,.115,.165,1)
    cloud.color_ramp.elements[1].position=.82
    cloud.color_ramp.elements[1].color=(.33,.53,.66,1)
    cloud.color_ramp.elements.new(.49).color=(.13,.25,.34,1)
    links.new(noise.outputs['Fac'],cloud.inputs['Fac'])
    icyWhite=ns.new('ShaderNodeMixRGB');icyWhite.blend_type='MIX'
    icyWhite.inputs[2].default_value=(.78,.88,.93,1)
    links.new(vein.outputs[0],icyWhite.inputs[0])
    links.new(cloud.outputs[0],icyWhite.inputs[1])
    bs=ns.new('ShaderNodeBsdfPrincipled')
    links.new(icyWhite.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Metallic'].default_value=.12
    bs.inputs['Roughness'].default_value=.35
    bs.inputs['Transmission Weight'].default_value=.13
    bs.inputs['IOR'].default_value=1.31
    rough=math_node(ns,links,'MULTIPLY',vein.outputs[0],.11)
    rough=math_node(ns,links,'ADD',rough,.30)
    links.new(rough,bs.inputs['Roughness'])
    trans=ns.new('ShaderNodeBsdfTransparent')
    mix=ns.new('ShaderNodeMixShader')
    ICE_VALUE=ns.new('ShaderNodeValue');ICE_VALUE.label='V31_ICE_INTENSITY_0_TO_100'
    # 0->50->100 animated, editable without changing geometry/materials.
    for frame,value in ((1,0.),(51,.5),(101,1.)):
        ICE_VALUE.outputs[0].default_value=value
        ICE_VALUE.outputs[0].keyframe_insert('default_value',frame=frame)
    ICE_VALUE.outputs[0].default_value=1.
    mask=math_node(ns,links,'MULTIPLY',limited,ICE_VALUE.outputs[0])
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
             'limited_blade_length_fraction':.38,
             'central_ridge_clear':True,'geometric_crystals_added':0,
             'animation_keyframes':{'1':0,'51':50,'101':100},
             'original_sword_mesh_modified':False,
             'overlay_faces':len(faces)}
    return DETAILS

def render_levels(camera,out):
    name='Hero' if 'Hero' in out.name else 'Detalle'
    frames=[(1,0),(51,50),(101,100)] if name=='Hero' else [(101,100)]
    last=None
    for frame,pct in frames:
        bpy.context.scene.frame_set(frame)
        out2=out.with_name('V31_Escarcha_'+str(pct)+'_'+name+'.png')
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
    audit['schema']='Genesis_V31_PartialIcyV175_PRELIMINARY_Cycles32'
    audit['intensity_animation_created_in_blender']=True
    audit['material_source_exact_original_blend']=False
    audit['not_approved']=True
    audit['results'][0]['renders']=[{'name':p.name} for p in sorted(root.glob('V31_Escarcha_*.png'))]
    (root/'v31_escarcha_intensidad_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V31_PRELIMINARY_REAL_CYCLES_FINISHED',flush=True)

if __name__=='__main__':main()
