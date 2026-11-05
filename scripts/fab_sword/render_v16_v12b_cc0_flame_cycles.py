#!/usr/bin/env python3
"""V14 TRUE Cycles render: user-approved V12B iron sword + independent experimental Fire VFX.
The exact original V03 GLB (SHA-256 checked by V12) and 32-bit RGB EXR HDRI remain unchanged.
VFX curves sample the actual 98-triangle blade cross-sections; no invented sword shape.
The fire is a Cycles look-development test of Fuego V03 rooted ember veins and flames,
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

def flame_atlas_material(intensity):
    """Actual 64-frame Unity Labs Paris CC0 flame flipbook. HDR EXR RGB + RGBA TGA alpha.
    This is NOT ImageGen, not a procedural fire concept, and not a baked change to sword.
    """
    if FLAME_IMAGE_EXR is None or FLAME_IMAGE_TGA is None:
        raise RuntimeError('Missing actual CC0 flame images; fire render must not proceed')
    m=bpy.data.materials.new('GENESIS_V16_CC0_UNITY_LABS_REAL_FLAME_'+str(intensity))
    m.use_nodes=True
    nodes=m.node_tree.nodes;nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial')
    emit=nodes.new('ShaderNodeEmission')
    emit.inputs['Strength'].default_value=0.9+0.012*intensity
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    mix=nodes.new('ShaderNodeMixShader')
    exr=nodes.new('ShaderNodeTexImage')
    exr.image=FLAME_IMAGE_EXR;exr.interpolation='Linear'
    exr.extension='CLIP'
    exr.label='64-frame original HDR EXR Unity Labs (CC0)'
    tga=nodes.new('ShaderNodeTexImage')
    tga.image=FLAME_IMAGE_TGA;tga.interpolation='Linear'
    tga.extension='CLIP'
    tga.label='Actual 64-frame RGBA fire mask Unity Labs (CC0)'
    alpha=nodes.new('ShaderNodeMath')
    alpha.operation='MULTIPLY';alpha.use_clamp=True
    alpha.inputs[1].default_value=(.74 if intensity<=60 else .92)
    # Use HDR EXR actual flame color, but clamp peak values gently to preserve
    # orange/red body instead of excessive white, with existing AgX tone mapping.
    color=nodes.new('ShaderNodeHueSaturation')
    color.inputs['Hue'].default_value=.49
    color.inputs['Saturation'].default_value=1.10
    color.inputs['Value'].default_value=.94
    m.node_tree.links.new(exr.outputs['Color'],color.inputs['Color'])
    m.node_tree.links.new(color.outputs['Color'],emit.inputs['Color'])
    m.node_tree.links.new(tga.outputs['Alpha'],alpha.inputs[0])
    m.node_tree.links.new(alpha.outputs[0],mix.inputs[0])
    m.node_tree.links.new(transparent.outputs[0],mix.inputs[1])
    m.node_tree.links.new(emit.outputs[0],mix.inputs[2])
    m.node_tree.links.new(mix.outputs[0],output.inputs['Surface'])
    return m

def authentic_flame_card(name,root,along,outward,front_normal,
                        width,height,frame,material,phase):
    """2-sided bent card carrying ORIGINAL frame UV, anchored to actual blade edge."""
    rows=4;cols=16
    frame=int(frame)%64
    col=frame%cols;row=rows-1-frame//cols
    inset=.025
    u0=(col+inset)/cols;u1=(col+1-inset)/cols
    v0=(row+inset)/rows;v1=(row+1-inset)/rows
    # Flame rises in physical 3D space away from the cutting edge while
    # drifting along the blade. Base is on iron, not floating.
    n=9
    verts=[];faces=[]
    tangent=along
    for i in range(n):
        p=i/(n-1)
        bend=(.18+.09*math.sin(phase))*math.sin(math.pi*p)
        center=root+outward*(height*(p**.82)) + along*(height*(.16*p+.16*bend))
        center+=front_normal*(.0035+.012*math.sin(math.pi*p))
        spread=(.90-.48*p)*width*.5
        # mild turbulence on the card geometry is different per card
        center+=along*(.006*math.sin(p*6+phase)*p)
        verts.extend([tuple(center-tangent*spread),tuple(center+tangent*spread)])
        if i:
            k=2*(i-1);faces.append((k,k+1,k+3,k+2))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    layer=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vert=mesh.loops[li].vertex_index
            y=vert//2/(n-1)
            x=vert%2
            layer.data[li].uv=(u0+(u1-u0)*x,v0+(v1-v0)*y)
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    return obj

def create_fire(intensity,frame,source):
    """Fire V04: actual CC0 high-resolution HDR flame flipbook on blade-attached cards."""
    origin,along,side,normal,samples,geometry=source
    strength=float(intensity)/100.0
    if strength<.001:return [],[],geometry,{'vein_segments':0,'flame_tongues':0,'original_flipbook_frames':64}
    getfront,tri_count=actual_surface_sampler(source)
    material=flame_atlas_material(intensity)
    objects=[]
    cards=0
    positions=([.13,.22,.31,.40,.49,.58,.67,.76,.85,.92]
               if intensity<=65 else
               [.10,.155,.21,.265,.32,.375,.43,.485,.54,.595,.65,.705,.76,.815,.87,.925])
    # Individual flame elements are independent and asynchronous in the 64-frame sheet;
    # 60 visibly burns, 100 more and larger tongues but V175 remains visible.
    for sideflag in (-1,1):
        for i,t in enumerate(positions):
            sample=min(samples,key=lambda s:abs(s[0]-t))
            _,u,left,right,front=sample
            span=right-left
            if span<.014:continue
            q=left+span*.036 if sideflag==-1 else right-span*.036
            surface=getfront(u,q,front)
            root=origin+along*u+side*q+normal*(surface+.0009)
            outward=side*sideflag
            phase=i*1.614+(0 if sideflag==-1 else 3.92)
            tile=int(frame*12+i*7+(4 if sideflag==-1 else 19))%64
            height=(.056+.051*strength)*(.74+.33*(math.sin(phase*1.8)**2))
            width=(.038+.016*strength)*(.77+.28*(math.cos(phase)**2))
            card=authentic_flame_card('REAL_CC0_FLAME_'+str(intensity)+'_'+str(sideflag)+'_'+str(i),
                  root,along,outward,normal,width,height,tile,material,phase)
            objects.append(card);cards+=1
    # Existing iron is NOT replaced: only subtle dark-red ember current.
    core=globals()['material']('V04_EMBERS_UNDER_REAL_FLAME',(.94,.07,.003),1.45+.006*intensity)
    vein_runs=0
    for lane,fraction in enumerate((.085,.915,.22,.78)):
        active=[];segments=[]
        for t,u,left,right,front in samples:
            wave=math.sin(t*39+lane*1.92-frame*2.4)+.36*math.sin(t*109-lane*2.3)
            live=wave>(.08 if intensity<=65 else -.12)
            q=left+(right-left)*fraction
            height=getfront(u,q,front)
            v=origin+along*u+side*q+normal*(height+.001)
            if live:active.append(v)
            else:
                if len(active)>2:segments.append(active)
                active=[]
        if len(active)>2:segments.append(active)
        for j,pts in enumerate(segments):
            radii=[max(.12,math.sin(math.pi*(k+.5)/len(pts))) for k in range(len(pts))]
            o=curve_line('V04_SUBTLE_EMBER_'+str(lane)+'_'+str(j),pts,core,radii,.00083+.000004*intensity)
            if o:objects.append(o);vein_runs+=1
    geometry=dict(geometry)
    geometry.update({
       'blade_real_front_triangles_sampled':tri_count,
       'real_blade_mesh_used_as_only_attachment_reference':True,
       'flame_source':'Unity Labs Paris CC0 HDR EXR 64-frame flipbook',
       'flame_original_exr_sha256':FLAME_SHA_EXR,
       'flame_original_tga_sha256':FLAME_SHA_TGA,
       'flame_atlas_tiles':[16,4],
       'no_point_lights_or_round_blobs':True,
       'vfx_own_geometry_only':True})
    return objects,[],geometry,{
      'vein_segments':vein_runs,
      'flame_tongues':cards,
      'original_flipbook_frames':64,
      'fire_cards':cards,
      'vfx_objects':len(objects),
      'source':'UnityLabs CC0 SmallFlame01-mini HDR EXR+TGA',
      'emission_strength_varies_with_intensity':True
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
    FLAME_IMAGE_EXR=bpy.data.images.load(str(a.flame_exr.resolve()),check_existing=False)
    FLAME_IMAGE_TGA=bpy.data.images.load(str(a.flame_tga.resolve()),check_existing=False)
    source_sizes={}
    for im in [FLAME_IMAGE_EXR,FLAME_IMAGE_TGA]:
        im.reload()
        w,h=[int(v) for v in im.size]
        print('GENESIS_V16_CC0_IMAGE_METADATA',im.name,'size',w,h,
              'format',im.file_format,'depth',im.depth,flush=True)
        if w<256 or h<128 or not (1.90<=w/h<=2.10):
            raise RuntimeError('Flame 16x4 atlas has invalid size '+im.name+': '+repr([w,h]))
        source_sizes[im.name]=[w,h]
    print('GENESIS_V16_REAL_CC0_FLAME_SOURCE_LOADED',
          FLAME_SHA_EXR,FLAME_SHA_TGA,source_sizes,flush=True)

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
      (60,1.4,'CAM_hero','Fuego_V04_060_V12B_Hero.png'),
      (60,1.4,'CAM_BLADE_MACRO','Fuego_V04_060_V12B_Detalle_Filo.png'),
      (100,1.4,'CAM_hero','Fuego_V04_100_V12B_Hero.png')]:
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
     'schema':'Genesis_Fuego_V16_FuegoV03_RealV12B_Cycles_Render',
     'original_sword_GLBSHA256':preset['source_original']['sha256'],
     'blade_material':'V12B user approved, unchanged',
     'blade_triangles':98,'full_sword_triangles':2150,
     'original_GLB_geometry_modified':False,'original_PBR_blade_color_modified':False,
     'roughness_multiplier_V12B':.34,'oxide_roughness_V12B':.10,
     'actual_blade_surface_sampled':geometry,
     'vfx_objects_are_separate_not_in_source':True,
     'shader_source':'Unity Labs Paris free CC0 SmallFlame01-mini original EXR+TGA atlas; PlayCanvas modular shader to be built after visual review',
     'fire_variant':'V04_ACTUAL_CC0_FLAME_ATLAS_HDR_EXR_PREVISUALIZATION_FOR_PLAYCANVAS',
     'render_implementation':'Blender Cycles V04 with actual Unity Labs CC0 flame HDR EXR color and TGA mask atlas, applied as moving cards on genuine V12B blade, not PlayCanvas GLSL runtime.',
     'visual_status':'experimental_only_user_review_required',
     'hdr_source':'studio_small_09_4k.exr','hdri_rgb_bits_per_channel':32,
     'hdri_sha256':preset['lighting']['hdri_sha256'],
     'blender':bpy.app.version_string,'engine':'Cycles','samples':a.samples,
     'rendered_files':results,'fire_segments':stats,
     'playcanvas_shader_modified':False,'original_model_exported':False,
     'flame_original_exr_sha256':FLAME_SHA_EXR,'flame_original_tga_sha256':FLAME_SHA_TGA,
     'flame_source_license':'Unity Labs Paris CC0 Unity.com Nov 28 2016',
     'concept_or_imagegen_used':False
    }
    (target/'fuego_v04_cc0_real_v12b_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V16_FIRE_V04_CC0_REAL_FLAME_ON_APPROVED_V12B_COMPLETE',json.dumps(audit),flush=True)

if __name__=='__main__':main()
