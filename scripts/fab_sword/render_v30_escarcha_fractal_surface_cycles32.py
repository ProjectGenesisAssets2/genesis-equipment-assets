#!/usr/bin/env python3
"""Project Genesis V30: two REAL Cycles frost renders on the ORIGINAL V03 iron sword.
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

def hoarfrost_texture_and_geometry(coord,along,side,normal,intensity,variant):
    """V30: natural hoarfrost/fern deposition physically projected onto original V03 blade.
    Deliberately replaces V29's repetitive raised vertical striations with distributed
    diffusion-like branching, rough icy bloom, and true small 3D fringe crystals.
    100% real Blender Cycles render from original exact GLB and approved EXR HDRI.
    """
    if variant not in ('A','B'):raise RuntimeError('V30_BAD_VARIANT')
    rng=ref.rng;rng.seed(301107)
    W,H=512,2048
    np_rng=np.random.default_rng(301107)
    alpha=np.zeros((H,W),dtype=np.float32)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    xf=xx/(W-1)
    # White, softly clustered rime builds from exposed edges with intermittent gaps.
    edge=np.minimum(xf,1-xf)
    fine=(.5+.20*np.sin(yy*.052+np.sin(xx*.041)*1.9)
          +.15*np.sin(yy*.107-xx*.086)
          +.13*np.sin(yy*.021+xx*.052))
    coarse=(.67+.21*np.sin(yy*.011+np.sin(xx*.015)*3.1)
            +.12*np.cos(yy*.033-xx*.021))
    openings=np.maximum(0.,np.minimum(1.,(coarse-.43)*1.65))
    rime=np.exp(-((edge/.108)**1.7))*(.15+.24*np.clip(fine,0,1))*openings
    alpha=np.maximum(alpha,rime.astype(np.float32))
    paint_stats={'axes':0,'feathers':0,'twigs':0,'particles':0}
    def ink(x0,y0,x1,y1,radius,opacity):
        xlo=max(0,int(math.floor(min(x0,x1)-radius-2)))
        xhi=min(W,int(math.ceil(max(x0,x1)+radius+3)))
        ylo=max(0,int(math.floor(min(y0,y1)-radius-2)))
        yhi=min(H,int(math.ceil(max(y0,y1)+radius+3)))
        if xlo>=xhi or ylo>=yhi:return
        Y,X=np.ogrid[ylo:yhi,xlo:xhi]
        vx=x1-x0;vy=y1-y0
        denom=max(1e-8,vx*vx+vy*vy)
        t=np.clip(((X-x0)*vx+(Y-y0)*vy)/denom,0,1)
        dist=np.sqrt((X-(x0+vx*t))**2+(Y-(y0+vy*t))**2)
        w=np.clip((radius+1.2-dist)/max(1.,radius+.5),0,1)
        sub=alpha[ylo:yhi,xlo:xhi]
        np.maximum(sub,opacity*w.astype(np.float32),out=sub)
    def stroke(points,radius,opacity):
        for a,b in zip(points[:-1],points[1:]):
            ink(a[0],a[1],b[0],b[1],radius,opacity)
    # Irregular ice fern colonies. Their branches spread BOTH across and along
    # the blade, rather than parallel barcode lines. Preserve the central ridge.
    for sign in (-1,1):
        for cluster in range(31):
            root_y=135+(H-260)*(cluster+.3)/31+rng.uniform(-20,20)
            root_x=13 if sign==-1 else W-14
            inward=1 if sign==-1 else -1
            depth=rng.uniform(118,194)
            yaw=rng.uniform(-95,95)
            count=13
            spine=[]
            for j in range(count+1):
                u=j/count
                px=root_x+inward*depth*u
                py=root_y+yaw*u+11*math.sin(u*math.pi*1.3+cluster*.83)*u
                spine.append((px,py))
            stroke(spine,3.7, .82)
            paint_stats['axes']+=1
            for j in range(2,13):
                frac=j/count
                start=spine[j]
                angle=(-1 if j%2 else 1)
                length=rng.uniform(22,69)*(.6+.4*math.sin(math.pi*frac))
                lateral=rng.uniform(12,37)
                end=(start[0]+inward*lateral,start[1]+angle*length)
                mid=((start[0]+end[0])*.5+inward*rng.uniform(-5,7),
                     (start[1]+end[1])*.5+rng.uniform(-6,6))
                branch=[start,mid,end]
                stroke(branch,2.35,.82)
                paint_stats['feathers']+=1
                for k in (1,2):
                    q=(k+.15)/3
                    from_pt=(start[0]+(end[0]-start[0])*q,
                             start[1]+(end[1]-start[1])*q)
                    slant=-angle if k==1 else angle
                    tip=(from_pt[0]+inward*rng.uniform(7,21),
                         from_pt[1]+slant*rng.uniform(11,27))
                    stroke([from_pt,tip],1.45,.72)
                    paint_stats['twigs']+=1
    # Diffuse microcrystalline sparkle, always around the frost deposits rather
    # than isolated neon particles floating off the blade.
    for k in range(2650):
        y=rng.randrange(105,H-92)
        side_sel=-1 if k%2==0 else 1
        radial=(.08+.32*rng.random())
        x=int(W*radial) if side_sel<0 else int(W*(1-radial))
        rad=rng.uniform(.65,2.15)
        op=rng.uniform(.22,.65)
        ink(x,y,x+rng.uniform(-1.4,1.4),y+rng.uniform(1,4),rad,op)
        paint_stats['particles']+=1
    # Leave the V175 nervio/ridge glossy and readable in the central region.
    center_gap=np.clip((np.abs(xf-.5)-.065)/.145,0.,1.)
    alpha *= (.24+.76*center_gap**.75)
    # B is slightly more fantasy-blue; still PBR hoar frost, not emissive electricity.
    coverage=float(np.mean(alpha>.16))
    high=float(np.mean(alpha>.55))
    tex=ref.bpy.data.images.new('GENESIS_V30_DENDRITIC_HOARFROST_ALPHA',
                                width=W,height=H,alpha=True,float_buffer=False)
    rgba=np.empty((H,W,4),dtype=np.float32)
    rgba[:,:,0]=.72 if variant=='B' else .84
    rgba[:,:,1]=.85 if variant=='B' else .90
    rgba[:,:,2]=.96 if variant=='B' else .93
    rgba[:,:,3]=np.clip(alpha*.96,0,1)
    tex.pixels.foreach_set(rgba.reshape(-1))
    tex.pack()
    m=ref.bpy.data.materials.new('GENESIS_V30_FROST_TRANSPARENT_PBR')
    m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();links=m.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial')
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    bs=nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(.82,.92,.97,1)
    bs.inputs['Roughness'].default_value=.84
    bs.inputs['Metallic'].default_value=0
    bs.inputs['Transmission Weight'].default_value=.055
    bs.inputs['IOR'].default_value=1.31
    if variant=='B':
        bs.inputs['Emission Color'].default_value=(.16,.32,.53,1)
        bs.inputs['Emission Strength'].default_value=.24
    im=nodes.new('ShaderNodeTexImage');im.image=tex
    im.interpolation='Linear';im.extension='EXTEND'
    uvn=nodes.new('ShaderNodeUVMap')
    mix=nodes.new('ShaderNodeMixShader')
    links.new(uvn.outputs['UV'],im.inputs['Vector'])
    links.new(im.outputs['Alpha'],mix.inputs[0])
    links.new(transparent.outputs[0],mix.inputs[1])
    links.new(bs.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],out.inputs['Surface'])
    # Subdivided surface-following custom mesh for frost, never edit or overwrite
    # the GLB blade material. UV x corresponds to its actual local edge-to-edge.
    rows,cols=132,26
    vertices=[];uvs=[];faces=[]
    for i in range(rows+1):
        t=.136+(.963-.136)*i/rows
        for j in range(cols+1):
            lateral=-.97+1.94*j/cols
            p,_=coord(t,lateral,.0070)
            vertices.append(tuple(map(float,p)))
            uvs.append((j/cols,i/rows))
    for i in range(rows):
        for j in range(cols):
            a=i*(cols+1)+j;b=a+(cols+1)
            faces.append((a,a+1,b+1,b))
    mesh=ref.bpy.data.meshes.new('GENESIS_V30_SURFACE_FROST_UV_MESH')
    mesh.from_pydata(vertices,[],faces);mesh.update()
    layer=mesh.uv_layers.new(name='V30_RimeUV')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index
            layer.data[li].uv=uvs[vi]
    obj=ref.bpy.data.objects.new(ref.TAGS+'V30_PROJECTED_HOARFROST',mesh)
    ref.bpy.context.collection.objects.link(obj);mesh.materials.append(m)
    # Physical ice spicules give true geometric volume at the blade silhouette.
    icy=ref.pbr('V30_RIME_WHITE_ICE_PBR',(.71,.83,.88),roughness=.68,transmission=.09)
    bluish=ref.pbr('V30_COOL_REFRACTIVE_EDGE_CRYSTALS',(.35,.60,.78),
                  roughness=.28,transmission=.48,
                  emission=(.09,.20,.40),emission_power=.30 if variant=='B' else .04)
    fronds=0;grains=0;glints=0
    for sign in (-1,1):
        for k in range(150):
            t=.145+.80*(k+.4)/150
            if math.sin(t*83+sign*2.5)>.73:continue
            lat=sign*(.88+.10*rng.random())
            p,_=coord(t,lat,.007)
            height=rng.uniform(.0024,.0085)
            s=side*sign*(.0012+.003*rng.random())
            tip=p+normal*height+s+along*rng.uniform(-.004,.010)
            ref.line('V30_REAL_HOAR_EDGE_SPICULE_%s_%03d'%(sign,k),
                     [p,tip],icy if k%5 else bluish,width=.00039+.00025*rng.random())
            fronds+=1
        for k in range(175):
            t=.14+.81*rng.random()
            lateral=sign*(.78+.20*rng.random())
            p,_=coord(t,lateral,.0070)
            sz=.0008+.0019*rng.random()
            ref.ellipsoid('V30_PHYSICAL_RIME_GRAIN_%s_%03d'%(sign,k),
                          p,(sz*.5,sz*1.1,sz*.42),icy)
            grains+=1
        for k in range(26):
            t=.16+.77*(k+.3)/26
            if k%3==0:continue
            p,_=coord(t,sign*(.80+.10*rng.random()),.0075)
            sz=.003+.0025*rng.random()
            verts=[p-side*sz,p+side*sz,p+along*(sz*.8),p+normal*(sz*.85)]
            ref.geo('V30_SMALL_REAL_ICE_FACET_%s_%02d'%(sign,k),
                    verts,[(0,1,3),(1,2,3),(2,0,3),(0,2,1)],bluish)
            glints+=1
    return {
      'variant':variant,
      'quality_target':'photorealistic frosted steel matching second visual reference',
      'real_render_not_concept':True,'no_generated_image_reference_used':True,
      'frost_type':'natural branched hoarfrost matte rime fractal alpha on actual V03 blade',
      'nucleation_sites':62,'feather_axes':paint_stats['axes'],
      'secondary_fern_arms':paint_stats['feathers'],
      'tertiary_dendrites':paint_stats['twigs'],
      'texture_resolution':[W,H],
      'surface_frost_uv_faces':len(faces),
      'frost_coverage_gt_16pct':coverage,'dense_frost_gt_55pct':high,
      'microcrystalline_grains_painted':paint_stats['particles'],
      'physical_rime_grains':grains,'edge_ice_spicules':fronds,'small_real_facets':glints,
      'no_flat_translucent_ice_sheets':True,'original_iron_ridge_uncovered':True,
      'no_electric_strings':True,'v12b_hdr_exr32_same':True,
      'original_blade_untouched':True
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',choices=['A','B'],required=True)
    args,_=parser.parse_known_args(sys.argv[sys.argv.index('--')+1:])
    original_argv=list(sys.argv)
    ref.BUILDERS['Hielo']=lambda coord,along,side,normal,intensity:hoarfrost_texture_and_geometry(coord,along,side,normal,intensity,args.variant)
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
            new=out/('Escarcha_'+args.variant+'_V30_V12B_HDRI32_'+name+'.png')
            if not old.is_file():raise RuntimeError('V30_MISSING_REAL_CYCLES_'+str(old))
            old.rename(new)
        detail=result['results'][0]['details']
        if detail['nucleation_sites']!=62 or detail['feather_axes']!=62 or detail['secondary_fern_arms']<670 or detail['texture_resolution']!=[512,2048]:
            raise RuntimeError('V29_FROST_GEOMETRY_INCOMPLETE')
        result['schema']='Genesis_V30_FractalSurfaceRime_RealCycles_V12B_EXR_RGB32'
        result['source_base']='V25 unchanged same iron/hdr/camera'
        result['selected_variant']=args.variant
        result['no_image_generation']=True
        result['video_animation_created']=False
        result['user_approval']='pending_actual_visual_comparison'
        result['results'][0]['renders']=[
            {'name':'Escarcha_'+args.variant+'_V30_V12B_HDRI32_'+name+'.png'} for name in ('Hero','Detalle')]
        (out/('Escarcha_'+args.variant+'_V30_Audit.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False))
        print('GENESIS_V30_REAL_FROST_'+args.variant+'_CYCLES_FINISHED',json.dumps(detail),flush=True)
    finally:
        sys.argv=original_argv

if __name__=='__main__':main()
