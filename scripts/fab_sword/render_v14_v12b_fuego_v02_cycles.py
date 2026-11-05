#!/usr/bin/env python3
"""V14 TRUE Cycles render: user-approved V12B iron sword + independent experimental Fire VFX.
The exact original V03 GLB (SHA-256 checked by V12) and 32-bit RGB EXR HDRI remain unchanged.
VFX curves sample the actual 98-triangle blade cross-sections; no invented sword shape.
The fire is a Cycles look-development test of Fuego V02 rooted ember veins and flames,
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
    """RGBA-like translucent thermal flame; warm color without clipping to white."""
    m=bpy.data.materials.new('GENESIS_FUEGO_V02_FLAME_SURFACE_ONLY')
    m.use_nodes=True
    tree=m.node_tree;tree.nodes.clear()
    output=tree.nodes.new('ShaderNodeOutputMaterial')
    transparent=tree.nodes.new('ShaderNodeBsdfTransparent')
    emit=tree.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value=(1.0,.22,.013,1.0)
    emit.inputs['Strength'].default_value=2.2+2.2*(intensity/100)
    mix=tree.nodes.new('ShaderNodeMixShader')
    coords=tree.nodes.new('ShaderNodeTexCoord')
    sep=tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(coords.outputs['UV'],sep.inputs[0])
    across=tree.nodes.new('ShaderNodeMath')
    across.operation='MULTIPLY';across.inputs[1].default_value=2
    tree.links.new(sep.outputs['X'],across.inputs[0])
    diff=tree.nodes.new('ShaderNodeMath')
    diff.operation='SUBTRACT';diff.inputs[1].default_value=1
    tree.links.new(across.outputs[0],diff.inputs[0])
    absnode=tree.nodes.new('ShaderNodeMath')
    absnode.operation='ABSOLUTE';tree.links.new(diff.outputs[0],absnode.inputs[0])
    center=tree.nodes.new('ShaderNodeMath')
    center.operation='SUBTRACT';center.inputs[0].default_value=1
    tree.links.new(absnode.outputs[0],center.inputs[1])
    fade=tree.nodes.new('ShaderNodeMath')
    fade.operation='SUBTRACT';fade.inputs[0].default_value=1
    tree.links.new(sep.outputs['Y'],fade.inputs[1])
    fac=tree.nodes.new('ShaderNodeMath')
    fac.operation='MULTIPLY';fac.use_clamp=True
    tree.links.new(center.outputs[0],fac.inputs[0])
    tree.links.new(fade.outputs[0],fac.inputs[1])
    strength=tree.nodes.new('ShaderNodeMath')
    strength.operation='MULTIPLY';strength.use_clamp=True
    strength.inputs[1].default_value=.86
    tree.links.new(fac.outputs[0],strength.inputs[0])
    tree.links.new(strength.outputs[0],mix.inputs[0])
    tree.links.new(transparent.outputs[0],mix.inputs[1])
    tree.links.new(emit.outputs[0],mix.inputs[2])
    tree.links.new(mix.outputs[0],output.inputs['Surface'])
    return m

def tongue_mesh(name,root,outward,along,front_normal,extent,length,
                flame_width,mat,phase):
    """A rooted, tapered ribbon waving OUT from original blade edge."""
    n=16
    verts=[];faces=[];uv_data=[]
    for i in range(n):
        p=i/(n-1)
        wave=math.sin(p*math.pi)**1.1
        curl=.20*math.sin(p*4.4+phase)+.10*math.sin(2.9*p+phase)
        base=root+outward*extent*(p**.78)+along*length*(p**.75+curl*.20)
        base+=front_normal*(.002+.0045*wave)
        spread=flame_width*(.16+.84*wave)*max(.025,(1-p)**.42)
        side_vec=along+outward*.18
        side_vec=side_vec/np.linalg.norm(side_vec)
        verts.extend([tuple(base-side_vec*spread),tuple(base+side_vec*spread)])
        if i:
            k=(i-1)*2
            faces.append((k,k+1,k+3,k+2))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for loop in poly.loop_indices:
            vid=mesh.loops[loop].vertex_index
            uv.data[loop].uv=((vid%2),vid//2/(n-1))
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

def create_fire(intensity,frame,source):
    """Fuego V02: opaque-hot ember veins fused to ORIGINAL iron, genuinely rooted flame ribbons."""
    origin,along,side,normal,samples,geometry=source
    power=float(intensity)/100.
    if power<.001:
        return [],[],geometry,{'vein_segments':0,'flame_tongues':0,'points':0}
    front_sampler,source_face_count=actual_surface_sampler(source)
    mats={
       'ember': material('V02_DEEP_RED_EMBER',(0.92,.045,.003),1.25+1.35*power),
       'orange': material('V02_MOLTEN_COPPER',(1.0,.165,.012),2.0+1.9*power),
       'hot': material('V02_INCANDESCENT_ORANGE',(1.0,.34,.039),2.55+3.05*power)
    }
    objects=[]
    count_segments=0
    # Dense irregular bright molten filaments run LONGITUDINALLY around both
    # cutting edges, always sampled on the real metal surface. No billboard overlay.
    lanes=[(.045,0.0,'orange'),(.955,1.2,'hot'),(.16,2.1,'ember'),(.84,3.4,'orange'),
           (.30,1.4,'ember'),(.73,2.5,'ember')]
    if intensity>=85:
        lanes.extend([(.055,4.3,'hot'),(.94,5.5,'orange'),(.44,3.1,'ember')])
    for lane,(fraction,phase,color) in enumerate(lanes):
        run=[];runs=[]
        for t,u,left,right,front in samples:
            spatial=(.63*math.sin(t*43.0+phase-frame*4.8)
                    +.23*math.sin(t*93+phase*1.6+frame*1.3)
                    +.14*math.sin(t*171-phase*1.4))
            threshold=-.28 if intensity>=85 else -.12
            active=spatial>threshold
            # Exact blade surface including ridge, not a synthetic flat plane.
            q=left+(right-left)*fraction
            q+=.0018*math.sin(t*62+phase)+.0011*math.sin(t*113-phase)
            n=front_sampler(u,q,front)
            p=origin+along*u+side*q+normal*(n+.00105)
            if active:
                run.append((p,t,spatial))
            else:
                if len(run)>=2:runs.append(run)
                run=[]
        if len(run)>=2:runs.append(run)
        for j,segment in enumerate(runs):
            coords=[q[0] for q in segment]
            vals=[max(.0,q[2]+.6) for q in segment]
            L=len(coords)
            radii=[max(.17,math.sin(math.pi*(i+.5)/L)**.7)*(.70+.35*vals[i]) for i in range(L)]
            size=(.0019 if fraction in (.045,.955,.055,.94) else .0012)*(1+power*.68)
            mat=mats[color]
            ob=curve_line('FUEGO_V02_ON_IRON_'+str(lane)+'_'+str(j),coords,mat,radii,size)
            if ob:
                objects.append(ob)
                count_segments+=1
    # Additional branching ember fractures on the iron, subtle but recognizable;
    # they never change the source PBR node or sword geometry.
    branches=8 if intensity==60 else 14
    for i in range(branches):
        t=(.105+i*.087) % .92
        sample=min(samples,key=lambda s:abs(s[0]-t))
        _,u,left,right,front=sample
        mid=(left+right)/2
        width=right-left
        startq=left+width*(.10 if i%2==0 else .90)
        endq=startq+width*((.30 if i%2==0 else -.30)+.16*math.sin(i*4.7))
        coords=[]
        for j in range(14):
            k=j/13
            uj=u+(k-.5)*.018
            q=startq+(endq-startq)*k+.0019*math.sin(k*8.4+i)
            n=front_sampler(uj,q,front)
            coords.append(origin+along*uj+side*q+normal*(n+.001))
        radii=[max(.12,math.sin(math.pi*(j+.5)/14)) for j in range(14)]
        mat=mats['ember' if i%3 else 'orange']
        ob=curve_line('FUEGO_V02_BRANCH_'+str(i),coords,mat,radii,.00065+.00070*power)
        if ob:
            objects.append(ob)
            count_segments+=1
    # Flame tongues actually grow FROM THE CUTTING EDGES in blade-tangent plane.
    # No V13-style little unattached hooks; pointed flame sheets are partially
    # transparent with orange core, attached to a molten root directly on iron.
    sheets=fire_sheet_material(intensity)
    placement=[(.10,0),(.18,1),(.26,0),(.34,1),(.42,0),(.50,1),
               (.58,0),(.66,1),(.74,0),(.82,1),(.90,0)]
    if intensity>=85:
        placement.extend([(.14,1),(.39,0),(.61,1),(.87,0)])
    elif intensity<=65:
        placement=placement[:10]
    tongue_count=0
    for i,(t,flag) in enumerate(placement):
        sample=min(samples,key=lambda s:abs(s[0]-t))
        _,u,left,right,front=sample
        width=right-left
        if width<.018:continue
        q=left+width*.035 if flag==0 else right-width*.035
        n=front_sampler(u,q,front)
        root=origin+along*u+side*q+normal*(n+.0014)
        outward=side*(-1.0 if flag==0 else 1.0)
        eccentric=.66+.34*math.sin(i*2.89)**2
        extent=(.025+.025*power)*eccentric*(.90+.20*math.sin(i*1.55)**2)
        length=(.052+.060*power)*(.75+.30*math.sin(i*1.71)**2)
        w=(.012+.008*power)*eccentric
        ob=tongue_mesh('FUEGO_V02_BLADE_EDGE_FLAME_'+str(i),
                      root,outward,along,normal,extent,length,w,sheets,phase=i*1.27+frame*1.3)
        objects.append(ob)
        tongue_count+=1
        # Thin molten root AND upward orange current connecting flame to edge:
        rootpath=[]
        for j in range(9):
            k=j/8
            rootpath.append(root+outward*(extent*.43*k)+along*(length*.55*k)
                            +normal*(.001+.003*math.sin(math.pi*k)))
        radii=[max(.12,1-k/8) for k in range(9)]
        attachment=curve_line('FUEGO_V02_INCANDESCENT_ROOT_'+str(i),rootpath,mats['hot'],radii,
                               (.0015+.0018*power))
        if attachment:objects.append(attachment)
    geometry=dict(geometry)
    geometry['blade_real_front_triangles_sampled']=source_face_count
    geometry['real_blade_mesh_used_as_only_attachment_reference']=True
    geometry['no_point_lights_or_round_blobs']=True
    # No separate fake point lights, avoiding V13 circular orange patches.
    return objects,[],geometry,{'vein_segments':count_segments,'flame_tongues':tongue_count,
                               'vfx_objects':len(objects),'emission_strength_varies_with_intensity':True}

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
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
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
        idx=sys.argv.index('--preset')
        sys.argv=sys.argv[:idx]+sys.argv[idx+2:]
        v12.main()
    finally:
        sys.argv=saved_argv
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
      (60,1.4,'CAM_hero','Fuego_V02_060_V12B_Hero.png'),
      (60,1.4,'CAM_BLADE_MACRO','Fuego_V02_060_V12B_Detalle_Filo.png'),
      (100,1.4,'CAM_hero','Fuego_V02_100_V12B_Hero.png')]:
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
     'schema':'Genesis_Fuego_V14_FuegoV02_RealV12B_Cycles_Render',
     'original_sword_GLBSHA256':preset['source_original']['sha256'],
     'blade_material':'V12B user approved, unchanged',
     'blade_triangles':98,'full_sword_triangles':2150,
     'original_GLB_geometry_modified':False,'original_PBR_blade_color_modified':False,
     'roughness_multiplier_V12B':.34,'oxide_roughness_V12B':.10,
     'actual_blade_surface_sampled':geometry,
     'vfx_objects_are_separate_not_in_source':True,
     'shader_source':'vfx/experimental/Genesis_Fuego_Filo_V01.mjs',
     'fire_variant':'V02_BLENDER_CYCLES_PREVISUALIZATION_FOR_NEW_GLASSL_IMPLEMENTATION',,
     'render_implementation':'Blender Cycles experimental Fuego V02 emissive surface curves and flame sheets on original V12B. NOT direct PlayCanvas GLSL execution.',
     'visual_status':'experimental_only_user_review_required',
     'hdr_source':'studio_small_09_4k.exr','hdri_rgb_bits_per_channel':32,
     'hdri_sha256':preset['lighting']['hdri_sha256'],
     'blender':bpy.app.version_string,'engine':'Cycles','samples':a.samples,
     'rendered_files':results,'fire_segments':stats,
     'playcanvas_shader_modified':False,'original_model_exported':False,
     'concept_or_imagegen_used':False
    }
    (target/'fuego_v02_real_v12b_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V14_FIRE_V02_ON_REAL_APPROVED_V12B_RENDER_COMPLETE',json.dumps(audit),flush=True)

if __name__=='__main__':main()
