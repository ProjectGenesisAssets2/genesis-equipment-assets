#!/usr/bin/env python3
"""V18 actual Cycles: approved V12B iron sword + CC0 real-fire textured continuous elegant VFX.
The exact original V03 GLB (SHA-256 checked by V12) and 32-bit RGB EXR HDRI remain unchanged.
Four continuous flowing translucent ribbons sample the actual 98-triangle blade geometry; no invented sword shape.
The fire is a Cycles look-development test of user reference: restrained curling orange flame,
NOT a claim that Blender executes the original PlayCanvas GLSL shader.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render_v12_v175_j_roughness as v12

def normalized(a):
    n=np.linalg.norm(a)
    if n<1e-9:raise ValueError('zero direction')
    return a/n

def collect_blade():
    all_tris=[];other=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        ob.data.calc_loop_triangles()
        m=ob.matrix_world
        for tri in ob.data.loop_triangles:
            poly=ob.data.polygons[tri.polygon_index]
            mat=ob.data.materials[poly.material_index] if poly.material_index<len(ob.data.materials) else None
            pts=[np.array(m@ob.data.vertices[i].co,dtype=float) for i in tri.vertices]
            if mat and 'Iron_Blade_V175' in mat.name:all_tris.append(pts)
            else:other.extend(pts)
    if len(all_tris)!=98:raise RuntimeError('Expected V03 real blade 98 tris, got '+str(len(all_tris)))
    if not other:raise RuntimeError('Sword guard not found')
    points=np.array([p for t in all_tris for p in t])
    center=points.mean(axis=0)
    _,vec=np.linalg.eigh(np.cov((points-center).T))
    length_dir=normalized(vec[:,2])
    if np.dot(length_dir,center-np.mean(other,axis=0))<0:length_dir=-length_dir
    camera=np.array(bpy.data.objects['CAM_hero'].location,dtype=float)
    plane_normal=normalized(vec[:,0])
    if np.dot(plane_normal,camera-center)<0:plane_normal=-plane_normal
    width_dir=normalized(np.cross(plane_normal,length_dir))
    # Actual blade triangles in orthogonal UV+normal coordinates, no hardcoded dimensions.
    projected=[[(float(np.dot(p-center,length_dir)),
                  float(np.dot(p-center,width_dir)),
                  float(np.dot(p-center,plane_normal))) for p in tri] for tri in all_tris]
    lo=min(p[0] for tri in projected for p in tri)
    hi=max(p[0] for tri in projected for p in tri)
    def cross_section(u):
        hits=[]
        for tri in projected:
            for p,q in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                if min(p[0],q[0])-1e-7<=u<=max(p[0],q[0])+1e-7:
                    diff=q[0]-p[0]
                    if abs(diff)<1e-8:
                        hits.extend([(p[1],p[2]),(q[1],q[2])])
                    else:
                        k=max(0,min(1,(u-p[0])/diff))
                        hits.append((p[1]+k*(q[1]-p[1]),p[2]+k*(q[2]-p[2])))
        if len(hits)<2:return None
        return min(q for q,n in hits),max(q for q,n in hits),max(n for q,n in hits)
    samples=[]
    for i in range(200):
        t=.045+(.96-.045)*i/199
        u=lo+(hi-lo)*t
        section=cross_section(u)
        if section is None:continue
        left,right,upper=section
        if right-left<.008:continue
        samples.append((t,u,left,right,upper))
    if len(samples)<120:raise RuntimeError('Blade cross section extraction failed: '+str(len(samples)))
    return center,length_dir,width_dir,plane_normal,samples,{'blade_triangles':len(all_tris),
       'blade_longitudinal_span_m':hi-lo,'blade_sampled_sections':len(samples),
       'average_width_m':float(np.mean([s[3]-s[2] for s in samples])),
       'front_side_derived_from_real_camera':True}

def material(name,rgb,emission):
    m=bpy.data.materials.new('GENESIS_FUEGO_V13_ONLY_'+name)
    m.use_nodes=True
    ns=m.node_tree.nodes;ns.clear()
    output=ns.new('ShaderNodeOutputMaterial')
    e=ns.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=(*rgb,1)
    e.inputs['Strength'].default_value=emission
    m.node_tree.links.new(e.outputs[0],output.inputs['Surface'])
    return m

def curve_line(name,coords,mat,radii,width):
    if len(coords)<2:return None
    cv=bpy.data.curves.new(name,'CURVE')
    cv.dimensions='3D'
    cv.resolution_u=2;cv.bevel_depth=width;cv.bevel_resolution=2
    cv.use_fill_caps=False
    spline=cv.splines.new('POLY')
    spline.points.add(len(coords)-1)
    for p,co,r in zip(spline.points,coords,radii):
        p.co=(float(co[0]),float(co[1]),float(co[2]),1.0)
        p.radius=float(r)
    o=bpy.data.objects.new(name,cv)
    bpy.context.collection.objects.link(o)
    cv.materials.append(mat)
    return o



def fire_sheet_material(intensity):
    """Flowing orange/red flame body: broad soft core, gradient root-to-tip, no white glow."""
    m=bpy.data.materials.new('GENESIS_FUEGO_V04_ORANGE_FLAME_BODY')
    m.use_nodes=True
    tree=m.node_tree;tree.nodes.clear()
    output=tree.nodes.new('ShaderNodeOutputMaterial')
    transparent=tree.nodes.new('ShaderNodeBsdfTransparent')
    emission=tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value=2.8+2.2*(intensity/100)
    mix=tree.nodes.new('ShaderNodeMixShader')
    coords=tree.nodes.new('ShaderNodeTexCoord')
    sep=tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(coords.outputs['UV'],sep.inputs[0])
    # Root burns brighter orange; taper toward cooler red at the curling tip.
    palette=tree.nodes.new('ShaderNodeValToRGB')
    palette.color_ramp.interpolation='EASE'
    palette.color_ramp.elements[0].position=0.0
    palette.color_ramp.elements[0].color=(1.0,.44,.036,1.0)
    palette.color_ramp.elements[1].position=1.0
    palette.color_ramp.elements[1].color=(.94,.070,.005,1.0)
    e=palette.color_ramp.elements.new(.28);e.color=(1.0,.37,.024,1.0)
    e=palette.color_ramp.elements.new(.68);e.color=(1.0,.20,.012,1.0)
    tree.links.new(sep.outputs['Y'],palette.inputs[0])
    tree.links.new(palette.outputs['Color'],emission.inputs['Color'])
    # Soft-edge transparent flame: sqrt shaping avoids invisible needle-thin center
    # but the mesh geometry tapers to an actual point, not a detached soft blob.
    across=tree.nodes.new('ShaderNodeMath')
    across.operation='MULTIPLY';across.inputs[1].default_value=2
    tree.links.new(sep.outputs['X'],across.inputs[0])
    diff=tree.nodes.new('ShaderNodeMath')
    diff.operation='SUBTRACT';diff.inputs[1].default_value=1
    tree.links.new(across.outputs[0],diff.inputs[0])
    absolute=tree.nodes.new('ShaderNodeMath')
    absolute.operation='ABSOLUTE';tree.links.new(diff.outputs[0],absolute.inputs[0])
    center=tree.nodes.new('ShaderNodeMath')
    center.operation='SUBTRACT';center.inputs[0].default_value=1
    tree.links.new(absolute.outputs[0],center.inputs[1])
    softcenter=tree.nodes.new('ShaderNodeMath')
    softcenter.operation='POWER';softcenter.inputs[1].default_value=.42
    tree.links.new(center.outputs[0],softcenter.inputs[0])
    fade=tree.nodes.new('ShaderNodeMath')
    fade.operation='SUBTRACT';fade.inputs[0].default_value=1
    tree.links.new(sep.outputs['Y'],fade.inputs[1])
    tip=tree.nodes.new('ShaderNodeMath')
    tip.operation='POWER';tip.inputs[1].default_value=.42
    tree.links.new(fade.outputs[0],tip.inputs[0])
    product=tree.nodes.new('ShaderNodeMath')
    product.operation='MULTIPLY';product.use_clamp=True
    tree.links.new(softcenter.outputs[0],product.inputs[0])
    tree.links.new(tip.outputs[0],product.inputs[1])
    strength=tree.nodes.new('ShaderNodeMath')
    strength.operation='MULTIPLY';strength.use_clamp=True
    strength.inputs[1].default_value=.96
    tree.links.new(product.outputs[0],strength.inputs[0])
    tree.links.new(strength.outputs[0],mix.inputs[0])
    tree.links.new(transparent.outputs[0],mix.inputs[1])
    tree.links.new(emission.outputs[0],mix.inputs[2])
    tree.links.new(mix.outputs[0],output.inputs['Surface'])
    return m

def tongue_mesh(name,root,outward,along,front_normal,extent,length,
                flame_width,mat,phase):
    """Wide, curled flame SHEET with tip curling back toward blade, rooted on actual edge."""
    n=22
    verts=[];faces=[]
    for i in range(n):
        p=i/(n-1)
        wave=max(0,math.sin(math.pi*p))**.72
        curl=.20*math.sin(p*4.2+phase)*math.sin(math.pi*p)
        lateral=.66*(math.sin(p*math.pi*.82)**1.35)+.34*p
        longitudinal=p**.72+curl*.27
        base=root+outward*extent*lateral+along*length*longitudinal
        base+=front_normal*(.0022+.003*wave)
        spread=flame_width*(.12+.88*wave)*max(.018,(1-p)**.55)
        tangent=along+outward*.15
        tangent=tangent/np.linalg.norm(tangent)
        verts.extend([tuple(base-tangent*spread),tuple(base+tangent*spread)])
        if i:
            k=(i-1)*2
            faces.append((k,k+1,k+3,k+2))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for loop in poly.loop_indices:
            v=mesh.loops[loop].vertex_index
            uv.data[loop].uv=(float(v%2),float(v//2)/(n-1))
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(mat)
    return ob

def actual_surface_sampler(source):
    """Sample actual *front* blade triangle height for any longitudinal and lateral point."""
    center,along,side,normal,samples,geometry=source
    tris=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        ob.data.calc_loop_triangles()
        for tri in ob.data.loop_triangles:
            poly=ob.data.polygons[tri.polygon_index]
            mat=ob.data.materials[poly.material_index] if poly.material_index<len(ob.data.materials) else None
            if not (mat and 'Iron_Blade_V175' in mat.name):continue
            pts=[np.array(ob.matrix_world@ob.data.vertices[i].co,dtype=float)-center for i in tri.vertices]
            values=np.array([(np.dot(p,along),np.dot(p,side),np.dot(p,normal)) for p in pts])
            ax,bx,cx=values
            det=(bx[1]-cx[1])*(ax[0]-cx[0])+(cx[0]-bx[0])*(ax[1]-cx[1])
            if abs(det)<1e-11:continue
            tris.append((values,det))
    def getfront(u,q,fallback):
        heights=[]
        for p,det in tris:
            A,B,C=p
            x=((B[1]-C[1])*(u-C[0])+(C[0]-B[0])*(q-C[1]))/det
            y=((C[1]-A[1])*(u-C[0])+(A[0]-C[0])*(q-C[1]))/det
            z=1-x-y
            if x>=-.008 and y>=-.008 and z>=-.008:
                heights.append(x*A[2]+y*B[2]+z*C[2])
        return max(heights) if heights else fallback
    return getfront,len(tris)


FLAME_IMAGE_EXR=None
FLAME_IMAGE_TGA=None
FLAME_SHA_EXR=None
FLAME_SHA_TGA=None
FLAME_ATLAS_INFO={}


def mathnode(nodes, links, op, lhs, rhs=None, clamp=False):
    n=nodes.new('ShaderNodeMath')
    n.operation=op;n.use_clamp=clamp
    if isinstance(lhs,(int,float)):n.inputs[0].default_value=lhs
    else:links.new(lhs,n.inputs[0])
    if rhs is not None:
        if isinstance(rhs,(int,float)):n.inputs[1].default_value=rhs
        else:links.new(rhs,n.inputs[1])
    return n.outputs[0]

def v18_flame_material(intensity,ribbon_index):
    """Continuous 0-100 / airy flame VEIL, not tiny 64 isolated sprites.
    Actual Unity Labs CC0 frame adds texture/detail while a continuous alpha
    envelope preserves smooth curling flame body along the real blade.
    """
    if FLAME_IMAGE_TGA is None:
        raise RuntimeError('Original CC0 Unity Labs RGBA flame atlas unavailable')
    strength=max(0.0,min(100.0,float(intensity)))/100.
    m=bpy.data.materials.new('GENESIS_V18_CONTINUOUS_CC0_FLAME_'+str(ribbon_index)+'_INT_'+str(intensity))
    m.use_nodes=True
    n=m.node_tree.nodes;n.clear();ln=m.node_tree.links
    output=n.new('ShaderNodeOutputMaterial')
    transparent=n.new('ShaderNodeBsdfTransparent')
    emission=n.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value=1.25+1.15*strength
    mix=n.new('ShaderNodeMixShader')
    atlasUV=n.new('ShaderNodeUVMap');atlasUV.uv_map='ATLAS_UV'
    sheetUV=n.new('ShaderNodeUVMap');sheetUV.uv_map='SHEET_UV'
    image=n.new('ShaderNodeTexImage')
    image.image=FLAME_IMAGE_TGA;image.interpolation='Linear';image.extension='CLIP'
    image.label='Original CC0 64-frame real flame texture, Unity Labs Paris'
    ln.new(atlasUV.outputs['UV'],image.inputs['Vector'])
    sep=n.new('ShaderNodeSeparateXYZ');ln.new(sheetUV.outputs['UV'],sep.inputs[0])
    # Heat colors: orange/amber-yellow center, cooler cinnabar orange on outer
    # ribbons. No white-hot lines and no changing the approved V12B material.
    gradient=n.new('ShaderNodeValToRGB')
    gradient.color_ramp.interpolation='EASE'
    gradient.color_ramp.elements[0].position=0
    gradient.color_ramp.elements[0].color=(.96,.25,.015,1)
    gradient.color_ramp.elements[1].position=1
    gradient.color_ramp.elements[1].color=(.74,.055,.004,1)
    e=gradient.color_ramp.elements.new(.32);e.color=(1.0,.47,.037,1)
    e=gradient.color_ramp.elements.new(.63);e.color=(1.0,.19,.012,1)
    ln.new(sep.outputs['Y'],gradient.inputs['Fac'])
    # Original flame RGB tint very lightly modulates the primary gradient,
    # so color remains consistent throughout sword and isn't a white stripe.
    actualColor=n.new('ShaderNodeHueSaturation')
    actualColor.inputs['Hue'].default_value=.50
    actualColor.inputs['Saturation'].default_value=.9
    actualColor.inputs['Value'].default_value=.68
    ln.new(image.outputs['Color'],actualColor.inputs['Color'])
    add=n.new('ShaderNodeMixRGB');add.blend_type='MULTIPLY'
    add.inputs[0].default_value=.24
    ln.new(gradient.outputs['Color'],add.inputs[1])
    ln.new(actualColor.outputs['Color'],add.inputs[2])
    ln.new(add.outputs[0],emission.inputs['Color'])
    # Floating silk-like diffusion: edge softness, end-to-end taper,
    # original CC0 alpha turbulence, and low-frequency procedural breakup.
    # Base veil never disappears inside a frame: prevents V16's "dashed" effect.
    across=mathnode(n,ln,'MULTIPLY',sep.outputs['X'],2.)
    centered=mathnode(n,ln,'SUBTRACT',across,1.)
    edgeAbs=mathnode(n,ln,'ABSOLUTE',centered)
    edgeInv=mathnode(n,ln,'SUBTRACT',1.,edgeAbs)
    edges=mathnode(n,ln,'POWER',edgeInv,.58)
    longitudinal=mathnode(n,ln,'MULTIPLY',sep.outputs['Y'],math.pi)
    sine=mathnode(n,ln,'SINE',longitudinal)
    verticalFade=mathnode(n,ln,'POWER',sine,.37)
    shape=mathnode(n,ln,'MULTIPLY',edges,verticalFade)
    # Original real fire from 64-frame CC0 is the LUMINANCE/detail mask,
    # not a repeated sprite. Low-level background keeps each S-flame connected.
    realAlpha=mathnode(n,ln,'MULTIPLY',image.outputs['Alpha'],.40)
    detail=mathnode(n,ln,'ADD',realAlpha,.60)
    noise=n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=6.7
    noise.inputs['Detail'].default_value=3
    noise.inputs['Roughness'].default_value=.60
    ln.new(sheetUV.outputs['UV'],noise.inputs['Vector'])
    noiseScale=mathnode(n,ln,'MULTIPLY',noise.outputs['Fac'],.48)
    noiseFloor=mathnode(n,ln,'ADD',noiseScale,.52)
    fluct=mathnode(n,ln,'MULTIPLY',detail,noiseFloor)
    baseAlpha=mathnode(n,ln,'MULTIPLY',shape,fluct)
    # Continuous alpha from 0 to 100, never discrete 'number of flames'.
    alphaScale=.0 if intensity==0 else (.13+.76*(strength**1.30))
    finalAlpha=mathnode(n,ln,'MULTIPLY',baseAlpha,alphaScale,clamp=True)
    ln.new(finalAlpha,mix.inputs[0])
    ln.new(transparent.outputs[0],mix.inputs[1])
    ln.new(emission.outputs[0],mix.inputs[2])
    ln.new(mix.outputs[0],output.inputs['Surface'])
    return m

def flowing_s_flame_ribbon(source,intensity,time,ordinal,material):
    """Long, one-piece serpentine flame around the V12B blade.
    Its centreline repeatedly crosses the blade but its broad veil remains
    translucent. Nothing is attached to the crossguard or sword handle.
    """
    origin,along,side,normal,samples,geometry=source
    getfront,_=actual_surface_sampler(source)
    strength=max(0.,min(100.,float(intensity)))/100.
    # Three/four continuous flame paths, fixed over 0..100 to avoid popping.
    config=[
      (-.035,1.78,.10,.11,.12),
      (2.20,1.56,-.09,-.10,.27),
      (1.12,2.30,.06,.09,.08),
      (3.10,1.94,-.06,-.08,.42),
    ]
    phase,cycles,shift,offset,start=config[ordinal]
    # Each main loop stays anchored from near guard to near tip.
    flameScale=(.43+.57*strength)
    waviness=(.078+.039*strength)*.40
    transverseWidth=(.029+.037*strength)*.40
    verts=[];faces=[];uvs=[]
    selected=[row for row in samples if start<=row[0]<=.985]
    if len(selected)<64:raise RuntimeError('Insufficient sampled actual V12B blade geometry')
    atlasFrame=(int(time*11.0)+ordinal*13)%64
    tileX=atlasFrame%16;tileY=3-atlasFrame//16
    for j,(t,u,left,right,front) in enumerate(selected):
        normalizedLong=j/(len(selected)-1)
        fade=(math.sin(math.pi*normalizedLong)**.45)
        theta=2*math.pi*(cycles*normalizedLong)+phase-time*.64
        # Ribbon snakes around both edges; in front on some turns, behind others.
        halfspan=.5*(right-left)
        middle=.5*(right+left)
        q=middle+shift*halfspan+waviness*math.sin(theta)*flameScale
        worldfront=getfront(u,max(left,min(right,q)),front)
        # Temperature-layer depth by ordinal, subtle changes in normal Z.
        depth=(.010 if ordinal%2==0 else -.004)+(.016+.008*strength)*math.sin(theta+.4)
        base=origin+along*u+side*q+normal*(worldfront+depth)
        tangent=side+normal*(.19*math.cos(theta)+.05)
        tangent=tangent/max(1e-8,float(np.linalg.norm(tangent)))
        width=transverseWidth*(.48+.52*math.sin(math.pi*normalizedLong)**.45)
        width*=1+.2*math.sin(theta*1.57+ordinal*.9)
        # Gentle fiery petals, no wide static envelope or oversized pyrotechnics.
        width*=fade
        for k in (0,1):
            cross=(-1. if k==0 else 1.)
            vert=base+cross*tangent*width
            verts.append(tuple(map(float,vert)))
            # CC0 atlas UV maps ONE flame cell along each entire S-shaped streamer.
            # This is a big continuous veil, not dozens of 3cm sprites.
            uvid=(tileX+(.035+.93*k))/16
            vvid=(tileY+(.025+.95*normalizedLong))/4
            uvs.append(((float(k),float(normalizedLong)),(uvid,vvid)))
        if j>0:
            ix=2*(j-1)
            faces.append((ix,ix+1,ix+3,ix+2))
    mesh=bpy.data.meshes.new('V18_REF_S_FLAME_MESH_'+str(ordinal))
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    sheet=mesh.uv_layers.new(name='SHEET_UV')
    tex=mesh.uv_layers.new(name='ATLAS_UV')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index
            sheet.data[li].uv=uvs[vi][0]
            tex.data[li].uv=uvs[vi][1]
    ob=bpy.data.objects.new('GENESIS_V18_REAL_FLAME_SHEET_'+str(ordinal),mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(material)
    return ob

def create_fire(intensity,frame,source):
    """Intensity 0..100 is a continuous user-controlled scalar, not a threshold."""
    intensity=max(0.,min(100.,float(intensity)))
    if intensity<=0.:
        geometry=dict(source[-1]);geometry.update({'reference_wisps':0,
          'flame_atlas_tiles':[16,4],'continuous_intensity_range':[0,100],
          'flame_original_tga_sha256':FLAME_SHA_TGA,
          'no_source_geometry_changes':True,'flame_source':'Unity Labs CC0'})
        return [],[],geometry,{'flame_tongues':0,'veil_strands':0,
                               'intensity_scalar':0,'vfx_objects':0,'original_flipbook_frames':64}
    _,tri_count=actual_surface_sampler(source)
    objs=[]
    for i in range(4):
        material=v18_flame_material(intensity,i)
        objs.append(flowing_s_flame_ribbon(source,intensity,frame,i,material))
    geometry=dict(source[-1])
    geometry.update({
        'blade_real_front_triangles_sampled':tri_count,
        'reference_wisps':len(objs),
        'flame_atlas_tiles':[16,4],
        'continuous_intensity_range':[0,100],
        'flame_source':'Unity Labs Paris CC0 TGA RGB and opacity details on flowing long flame veils',
        'flame_original_exr_sha256':FLAME_SHA_EXR,
        'flame_original_tga_sha256':FLAME_SHA_TGA,
        'no_point_lights_or_round_blobs':True,
        'no_source_geometry_changes':True,
        'no_short_repetitive_fire_cards':True
    })
    return objs,[],geometry,{
         'flame_tongues':len(objs),'veil_strands':len(objs),
         'intensity_scalar':intensity,
         'intensity_is_continuous_and_clamped':True,
         'vfx_objects':len(objs),
         'original_flipbook_frames':64,
         'flame_source':'Unity Labs CC0 SmallFlame01 mini 64 frame atlas',
         'reference':'user-provided vertical sword with restrained flowing spiraling orange flames'
    }

def render(scene,camera,out):
    scene.camera=bpy.data.objects[camera]
    scene.render.filepath=str(out.resolve())
    bpy.ops.render.render(write_still=True)
    if not out.exists() or out.stat().st_size<100000:raise RuntimeError('No real Cycles render '+str(out))
    return {'file':out.name,'bytes':out.stat().st_size}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--hdri',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--preset',type=Path,required=True)
    p.add_argument('--samples',type=int,default=96)
    p.add_argument('--flame-exr',type=Path,required=True)
    p.add_argument('--flame-tga',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    global FLAME_IMAGE_EXR,FLAME_IMAGE_TGA,FLAME_SHA_EXR,FLAME_SHA_TGA
    if not a.flame_exr.exists() or not a.flame_tga.exists():
        raise RuntimeError('Original Unity Labs CC0 asset is required')

    preset=json.loads(a.preset.read_text())
    assert preset['id']=='Genesis_Espada_V03_Hierro_V175_V12B'
    assert preset['visual_status']=='approved_by_user'
    assert preset['surface']['roughness_multiplier']==.34 and preset['surface']['oxide_roughness_add']==.10
    assert hashlib.sha256(a.input.read_bytes()).hexdigest()==preset['source_original']['sha256']
    assert hashlib.sha256(a.hdri.read_bytes()).hexdigest()==preset['lighting']['hdri_sha256']
    # Generate exact V12B using the ORIGINAL November 5 real Blender script, no rebuild.
    # Old V12/V10 parsers do not accept our new --preset argument.
    saved_argv=sys.argv[:]
    try:
        for key in ('--preset','--flame-exr','--flame-tga'):
            idx=sys.argv.index(key)
            sys.argv=sys.argv[:idx]+sys.argv[idx+2:]
        v12.main()
    finally:
        sys.argv=saved_argv
    FLAME_SHA_EXR=hashlib.sha256(a.flame_exr.read_bytes()).hexdigest()
    FLAME_SHA_TGA=hashlib.sha256(a.flame_tga.read_bytes()).hexdigest()
    # Verified CC0 real-flame TGA is RGBA and decodes correctly; source ZIP also
    # includes an EXR which Blender 4.5.13 currently reports as 0x0. Do not
    # substitute a procedural texture or change the ORIGINAL 32bpc EXR HDRI.
    FLAME_IMAGE_EXR=None
    FLAME_IMAGE_TGA=bpy.data.images.load(str(a.flame_tga.resolve()),check_existing=False)
    FLAME_IMAGE_TGA.reload()
    w,h=[int(v) for v in FLAME_IMAGE_TGA.size]
    print('GENESIS_V16_CC0_TGA_LOADED',FLAME_IMAGE_TGA.name,
          [w,h],'depth',FLAME_IMAGE_TGA.depth,
          'unreadable_exr_sha256_preserved',FLAME_SHA_EXR,flush=True)
    if (w,h)!=(2048,1024):
        raise RuntimeError('CC0 RGBA flame atlas is not 2048x1024: '+repr((w,h)))

    scene=bpy.context.scene
    iron=next((mat for mat in bpy.data.materials if 'Iron_Blade_V175' in mat.name),None)
    if not iron:raise RuntimeError('Approved V12B blade material missing')
    base=next((n for n in iron.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if base is None:raise RuntimeError('V12B PBR shader missing')
    original_base_color_link=base.inputs['Base Color'].links[0].from_socket
    rough=iron.node_tree.nodes.get('V11_J_V175_ROUGHNESS_MULT_049')
    oxide=iron.node_tree.nodes.get('V12_J_OXIDE_LOCAL_ROUGHNESS')
    if not rough or not oxide or abs(rough.inputs[1].default_value-.34)>1e-6 or abs(oxide.inputs[1].default_value-.10)>1e-6:
        raise RuntimeError('Preset V12B not active, REFUSE FIRE OVER DIFFERENT IRON')
    source=collect_blade()
    target=a.output_dir
    original=(target/'V12_V175_Color_J_Rugosidad034_Hero.png')
    if not original.exists():raise RuntimeError('Expected exact pre-fire V12B reference render missing')
    results=[{'file':original.name,'bytes':original.stat().st_size,'effect':'Fuego','intensity':0,'note':'actual V12B no fire reference'}]
    count=0;geometry=None;stats=[]
    for intensity,frame,camera,label in [
      (25,1.4,'CAM_hero','Fuego_V06_025_V12B_Hero.png'),
      (50,1.4,'CAM_hero','Fuego_V06_050_V12B_Hero.png'),
      (60,1.4,'CAM_hero','Fuego_V06_060_V12B_Hero.png'),
      (60,1.4,'CAM_BLADE_MACRO','Fuego_V06_060_V12B_Detalle_Filo.png'),
      (75,1.4,'CAM_hero','Fuego_V06_075_V12B_Hero.png'),
      (100,1.4,'CAM_hero','Fuego_V06_100_V12B_Hero.png')]:
        objects,lights,geometry,lanes=create_fire(intensity,frame,source)
        count+=len(objects)
        bpy.context.view_layer.update()
        result=render(scene,camera,target/label)
        result.update({'effect':'Fuego','intensity':intensity,
                       'vfx_geometry_objects':len(objects),'separate_emissive_material':True})
        results.append(result)
        stats.append({'intensity':intensity,'ribbons':lanes,'objects':len(objects)})
        for obj in objects+lights:bpy.data.objects.remove(obj,do_unlink=True)
        # Emissive materials are not base material; no dirtying original PBR maps.
    if base.inputs['Base Color'].links[0].from_socket != original_base_color_link:
        raise RuntimeError('ERROR: V12B BASE COLOR CONNECTION CHANGED')
    if abs(rough.inputs[1].default_value-.34)>1e-6 or abs(oxide.inputs[1].default_value-.10)>1e-6:
        raise RuntimeError('ERROR: approved V12B roughness changed')
    audit={
     'schema':'Genesis_Fuego_V18_FuegoV06_CC0Flowing_V12B_Cycles_Render',
     'original_sword_GLBSHA256':preset['source_original']['sha256'],
     'blade_material':'V12B user approved, unchanged',
     'blade_triangles':98,'full_sword_triangles':2150,
     'original_GLB_geometry_modified':False,'original_PBR_blade_color_modified':False,
     'roughness_multiplier_V12B':.34,'oxide_roughness_V12B':.10,
     'actual_blade_surface_sampled':geometry,
     'vfx_objects_are_separate_not_in_source':True,
     'shader_source':'Unity Labs Paris CC0 SmallFlame01-mini TGA atlas for real flame details; custom 0..100 contiguous flowing ribbon surface shader in Blender; PlayCanvas runtime pending visual approval',
     'fire_variant':'V06_CC0_FLUID_4_LONG_S_WISPS_CONTINUOUS_0_TO_100',
     'render_implementation':'Blender Cycles V06 with FOUR continuous wave-like translucent flame ribbons shaped along true sword and detailed with original CC0 RGBA 64-frame atlas. NOT the PlayCanvas real-time GLSL runtime.',
     'visual_status':'experimental_only_user_review_required',
     'hdr_source':'studio_small_09_4k.exr','hdri_rgb_bits_per_channel':32,
     'hdri_sha256':preset['lighting']['hdri_sha256'],
     'blender':bpy.app.version_string,'engine':'Cycles','samples':a.samples,
     'rendered_files':results,'fire_segments':stats,
     'playcanvas_shader_modified':False,'original_model_exported':False,
     'flame_original_exr_sha256':FLAME_SHA_EXR,'flame_original_tga_sha256':FLAME_SHA_TGA,
     'flame_source_license':'Unity Labs Paris CC0 Unity.com Nov 28 2016',
     'flame_render_texture':'original 64-frame CC0 TGA RGBA reused as microdetail and thermal palette; EXR source downloaded and hashed but decoder unavailable in Blender 4.5.13',
     'intensity_behavior':{'range':[0,100],'type':'continuous_float','zero_has_no_geometry':True,'no_thresholded_lanes':True},
     'reference_style':'user request V18: flame halo 60 percent thinner than V17; centerline waviness 60 percent lower; preserve original approved V175 V12B',
      'halo_thickness_scale_vs_v17':0.40,'lateral_waviness_scale_vs_v17':0.40,
      'width_reduction_vs_v17_percent':60,
     'concept_or_imagegen_used':False
    }
    (target/'fuego_v06_fluid_real_v12b_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V18_FIRE_V06_CC0_FLOWING_V12B_RENDER_COMPLETE',json.dumps(audit),flush=True)

if __name__=='__main__':main()
