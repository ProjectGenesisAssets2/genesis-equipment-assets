#!/usr/bin/env python3
"""V13 TRUE Cycles render: user-approved V12B iron sword + independent experimental Fire VFX.
The exact original V03 GLB (SHA-256 checked by V12) and 32-bit RGB EXR HDRI remain unchanged.
VFX curves sample the actual 98-triangle blade cross-sections; no invented sword shape.
The fire is a Cycles look-development translation of Fuego V01's four streak ribbons,
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

def create_fire(intensity,frame,source):
    origin,along,side,normal,samples,geometry=source
    v=intensity/100.
    colors=[
      material('ember_low',(.92,.08,.013),2.1+1.2*v),
      material('copper', (1.,.29,.027),3.2+2.5*v),
      material('hot_amber',(1.,.61,.085),5.0+3*v),
      material('hot_core',(1.,.86,.34),7.2+4.8*v)]
    objects=[];lane_stats=[]
    # Four real-blade-derived independent paths: left/right cutting edges and inner heat veins.
    # GLSL prototype Fuego V01 uses wave 41,102,175; reproduce the spatial phase
    # without replacing the approved V12B PBR metal material.
    lanes=[(.12,0,False),(.88,.32,False),(.38,.62,True),(.62,.88,True)]
    for lane,(qfrac,phase,inner) in enumerate(lanes):
        active=[];vals=[];runs=[]
        for t,u,left,right,front in samples:
            x=t+phase
            wave=math.sin(x*41.-frame*10.3+math.sin(x*97.+frame*2.1)*.55)
            wave2=math.sin(x*102.-frame*7.2+math.sin(x*22.+frame*3.3)*1.3)
            wave3=math.sin(x*175.+frame*5.6)
            burn=(wave*.70+wave2*.22+wave3*.08+.28)/(.71+.28)
            hot=max(0,min(1,burn))
            travel=max(0,math.sin(x*87.-frame*(9.5+v*4.0)))**5
            # Discontinuous lava filaments, never an uninterrupted neon border.
            hot=.72*hot+.28*travel
            selected=hot>(.35 if inner else .26)
            q=left*(1-qfrac)+right*qfrac
            wiggle=.0012*math.sin(t*115+lane*1.8)+.00065*math.sin(t*237+lane)
            q+=wiggle*(1. if qfrac>.5 else -1.)
            xyz=origin+along*u+side*q+normal*(front+.0018+.0007*math.sin(t*31+lane))
            if selected:
                active.append(xyz)
                vals.append(hot)
            else:
                if len(active)>=2:runs.append((active,vals))
                active=[];vals=[]
        if len(active)>=2:runs.append((active,vals))
        segment_count=0
        for i,(coords,levels) in enumerate(runs):
            strength=float(np.mean(levels))
            if len(coords)<2:continue
            count=len(coords)
            radii=[max(.25,math.sin(math.pi*(j+.5)/count)**.6)*(.65+.55*levels[j]) for j in range(count)]
            power_idx= min(3,int(max(.0,strength)*3.5))
            scale=.00105 if inner else .0017
            scale*=.67+.6*v
            # Increasing line brightness is shader emission, independent of base material.
            obj=curve_line('FUEGO_'+str(lane)+'_VEIN_'+str(i),coords,colors[power_idx],radii,scale)
            if obj:objects.append(obj);segment_count+=1
        lane_stats.append({'lane':lane,'inner':inner,'segments':segment_count})
    # Sparse small tongues of fire anchored to blade edges. These are VFX geometry,
    # not sword replacement mesh and not a change to PBR/GLB.
    if intensity>=30:
        for i,tgoal in enumerate((.20,.37,.55,.73,.86)):
            sample=min(samples,key=lambda s:abs(s[0]-tgoal))
            t,u,left,right,front=sample
            qs=left if i%2==0 else right
            width=right-left
            path=[]
            for j in range(12):
                k=j/11
                u2=u+(k*k)*(.014+.014*v)
                q=qs + (-1 if i%2==0 else 1)*(width*.2+.014)*k +.007*math.sin(math.pi*k)
                n=front+.006+.010*math.sin(math.pi*k)+k*.004
                path.append(origin+along*u2+side*q+normal*n)
            radii=[max(.025,(1-j/11)**1.5)*(.5+.4*math.sin(math.pi*j/11)) for j in range(12)]
            ob=curve_line('FUEGO_TONGUE_'+str(i),path,colors[1 if i%2 else 2],radii,.0014+.0011*v)
            if ob:objects.append(ob)
    lights=[]
    # Actual emitted heat affects PBR blade with modest warm light, not texture replacement.
    for i,idx in enumerate((int(.27*len(samples)),int(.69*len(samples)))):
        t,u,left,right,front=samples[idx]
        point=origin+along*u+side*(left+right)*.5+normal*(front+.08)
        lamp=bpy.data.lights.new('GENESIS_FIRE_VFX_LIGHT_'+str(i),'POINT')
        lamp.energy=14.*v;lamp.color=(1.0,.26,.043)
        lamp.shadow_soft_size=.12
        obj=bpy.data.objects.new(lamp.name,lamp)
        bpy.context.collection.objects.link(obj)
        obj.location=Vector(point.tolist())
        lights.append(obj)
    return objects,lights,geometry,lane_stats

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
    v12.main()
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
      (60,1.4,'CAM_hero','Fuego_060_V12B_Hero.png'),
      (60,1.4,'CAM_BLADE_MACRO','Fuego_060_V12B_Detalle_Filo.png'),
      (100,1.4,'CAM_hero','Fuego_100_V12B_Hero.png')]:
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
     'schema':'Genesis_Fuego_V13_RealV12B_Cycles_Render',
     'original_sword_GLBSHA256':preset['source_original']['sha256'],
     'blade_material':'V12B user approved, unchanged',
     'blade_triangles':98,'full_sword_triangles':2150,
     'original_GLB_geometry_modified':False,'original_PBR_blade_color_modified':False,
     'roughness_multiplier_V12B':.34,'oxide_roughness_V12B':.10,
     'actual_blade_surface_sampled':geometry,
     'vfx_objects_are_separate_not_in_source':True,
     'shader_source':'vfx/experimental/Genesis_Fuego_Filo_V01.mjs',
     'render_implementation':'Blender Cycles emissive geometry translation of four Fuego V01 paths. NOT direct GLSL execution.',
     'visual_status':'experimental_only_user_review_required',
     'hdr_source':'studio_small_09_4k.exr','hdri_rgb_bits_per_channel':32,
     'hdri_sha256':preset['lighting']['hdri_sha256'],
     'blender':bpy.app.version_string,'engine':'Cycles','samples':a.samples,
     'rendered_files':results,'fire_segments':stats,
     'playcanvas_shader_modified':False,'original_model_exported':False,
     'concept_or_imagegen_used':False
    }
    (target/'fuego_real_v12b_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V13_REAL_SWORD_V12B_FIRE_RENDER_COMPLETE',json.dumps(audit),flush=True)

if __name__=='__main__':main()
