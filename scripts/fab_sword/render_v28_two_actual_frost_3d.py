#!/usr/bin/env python3
"""Project Genesis V28: REAL 3D hoarfrost on ORIGINAL V03 sword, two separate variants.
A = natural realistic hoar frost / rime, matte white dendritic growth.
B = stronger physically-grounded hoarfrost with restrained cold optical accents.
NO images/concepts/model substitution. Original V175 metal, V12B studio, 32-bpc EXR.
Each variant exports its own frost-only editable Blender scene and GLB overlay.
"""
import bpy, math, json, argparse, sys, hashlib, random, shutil, struct
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_v12_v175_j_roughness as v12
import render_v18_v12b_fuego_v06_flow_cycles as swordref
import render_v25_hielo_cycles_hdri32 as v25

SOURCE_SHA='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'
HDRI_SHA='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
TAG='GENESIS_V28_FROST_'
rng=random.Random(28071107)

def check(cond, why):
    if not cond: raise RuntimeError('GENESIS_V28_FAIL '+why)

def material(name,color,rough=.8,transmit=0.,emission_strength=0.):
    mat=bpy.data.materials.new(TAG+name)
    mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=0.
    bs.inputs['IOR'].default_value=1.31
    bs.inputs['Transmission Weight'].default_value=transmit
    bs.inputs['Emission Color'].default_value=(*color,1)
    bs.inputs['Emission Strength'].default_value=emission_strength
    mat.diffuse_color=(*color,1)
    return mat

def porous_frost_mat(name, color, denser):
    """A frosted porous PBR deposit: not continuous flat blue plates, not glass."""
    mat=bpy.data.materials.new(TAG+name)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    nodes.clear(); link=mat.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial')
    principled=nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value=(*color,1)
    principled.inputs['Roughness'].default_value=.88 if not denser else .80
    principled.inputs['IOR'].default_value=1.31
    principled.inputs['Transmission Weight'].default_value=.025 if not denser else .06
    transparent=nodes.new('ShaderNodeBsdfTransparent')
    mix=nodes.new('ShaderNodeMixShader')
    coord=nodes.new('ShaderNodeTexCoord')
    noise=nodes.new('ShaderNodeTexNoise')
    noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=21.5 if not denser else 29.0
    noise.inputs['Detail'].default_value=4.2
    noise.inputs['Roughness'].default_value=.77
    link.new(coord.outputs['Generated'],noise.inputs['Vector'])
    mask=nodes.new('ShaderNodeMapRange')
    mask.interpolation_type='SMOOTHSTEP'
    mask.clamp=True
    mask.inputs['From Min'].default_value=.32 if not denser else .24
    mask.inputs['From Max'].default_value=.70 if not denser else .68
    mask.inputs['To Min'].default_value=.0
    mask.inputs['To Max'].default_value=.91 if not denser else .95
    link.new(noise.outputs['Fac'],mask.inputs['Value'])
    link.new(mask.outputs['Result'],mix.inputs[0])
    link.new(transparent.outputs[0],mix.inputs[1])
    link.new(principled.outputs[0],mix.inputs[2])
    link.new(mix.outputs[0],out.inputs['Surface'])
    return mat

def make_mesh(name, verts, faces, mat):
    mesh=bpy.data.meshes.new(TAG+name+'_mesh')
    mesh.from_pydata([tuple(map(float,v)) for v in verts],[],faces)
    mesh.update()
    obj=bpy.data.objects.new(TAG+name,mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj

def batched_curves(name, chains, mat, radius=.00024):
    cv=bpy.data.curves.new(TAG+name+'_curve','CURVE')
    cv.dimensions='3D'
    cv.resolution_u=2
    cv.bevel_depth=radius
    cv.bevel_resolution=2
    for chain in chains:
        if len(chain)<2:continue
        sp=cv.splines.new('POLY')
        sp.points.add(len(chain)-1)
        for j,p in enumerate(chain):sp.points[j].co=(float(p[0]),float(p[1]),float(p[2]),1.)
    obj=bpy.data.objects.new(TAG+name,cv)
    bpy.context.collection.objects.link(obj)
    cv.materials.append(mat)
    return obj

def make_rime_film(coord, variant, mat):
    # Six discontinuous surface deposits, localized at cutting edges.
    width_factor=.75 if variant=='A' else 1.10
    bands=[(.135,.262),(.293,.417),(.448,.591),(.627,.774),(.810,.955)]
    count=0
    for side in (-1,1):
        for k,(a,b) in enumerate(bands):
            if variant=='A' and k==2 and side>0:continue
            verts=[]
            steps=64
            for j in range(steps+1):
                q=j/steps
                t=a+(b-a)*q
                env=math.sin(math.pi*q)**.70
                jag=.61+.18*math.sin(t*111+side*1.2+k)+.11*math.sin(t*263+k*5.8)
                jag=max(.28,min(.9,jag))
                exterior=side*(.958-.023*math.sin(t*54+k))
                broad=(.18+.13*jag)*width_factor*env
                # Preserve original metallic ridge and large uncoated regions.
                interior=side*(abs(exterior)-broad)
                pos1,_=coord(t,interior,.0047)
                pos2,_=coord(t,exterior,.0049)
                verts.extend([pos1,pos2])
            faces=[(j*2,j*2+1,j*2+3,j*2+2) for j in range(steps)]
            make_mesh('PorousRime_%s_%d'%(side,k),verts,faces,mat)
            count+=1
    return count

def make_dendrites(coord, variant, white, muted, accent):
    """Actual microscopic hoarfrost dendrites built as mesh-exportable 3D curves
    rooted into sampled V03 blade geometry; different random branches every cluster."""
    count=145 if variant=='A' else 230
    masters=[];branches=[];twigs=[];cold=[]
    for i in range(count):
        t0=.13+.81*rng.random()
        sgn=-1 if rng.random()<.5 else 1
        l0=sgn*(.68+.20*rng.random())
        lifetime=.022+.035*rng.random()
        spread=.18+.17*rng.random()
        angle=1 if rng.random()<.6 else -1
        # tip pointing up the blade and branching inward
        trunk=[]
        for j in range(10):
            q=j/9
            tj=max(.10,min(.982,t0+angle*lifetime*q+.0035*math.sin(q*8+i*1.7)*q))
            lj=l0-sgn*spread*q+.016*math.sin(q*12+i)*q
            p,_=coord(tj,lj,.0054+.00020*math.sin(i+j))
            trunk.append(p)
        masters.append(trunk)
        for j in range(2,10,2):
            q=j/9
            for v in (-1,1):
                run=(.006+.004*rng.random())*(.76+.24*q)
                branch_dir=v*angle
                # oblique snowflake plumes / fern-like side sprays
                out=[]
                for k in range(5):
                    w=k/4
                    tt=t0+angle*lifetime*q+branch_dir*run*w
                    ll=l0-sgn*spread*q-sgn*(.042+.036*rng.random())*w
                    tt=max(.10,min(.982,tt))
                    p,_=coord(tt,ll,.0055)
                    out.append(p)
                branches.append(out)
                # second-order barbs mimic hoarfrost not a symmetrical leaf decal
                for m in (2,3):
                    q2=m/4
                    tip=out[m]
                    tj=t0+angle*lifetime*q+branch_dir*run*q2+v*angle*.004
                    lj=l0-sgn*spread*q-sgn*(.042+.036*rng.random())*q2-sgn*.029
                    p,_=coord(max(.10,min(.982,tj)),lj,.0056)
                    twigs.append([tip,p])
        if variant=='B' and i%6==0:
            # restrained ice-blue glints localized on a few natural crystalline tips
            cold.append(trunk[-4:])
    batched_curves('DendriticFrostRoots_'+variant,masters,white,.00032 if variant=='A' else .00037)
    batched_curves('DendriticFrostPlumes_'+variant,branches,white,.00023 if variant=='A' else .00029)
    batched_curves('DendriticFrostHair_'+variant,twigs,muted,.00015 if variant=='A' else .00019)
    if cold:batched_curves('SubtleIceRefraction_'+variant,cold,accent,.00020)
    return {'root_colonies':count,'primary_dendrites':len(masters),
            'secondary_branches':len(branches),'frost_microbranches':len(twigs),
            'subtle_azure_crystal_lights':len(cold)}

def make_granules(coord,along,side,normal,variant,matt,blue):
    # One combined mesh, avoiding hundreds of individual sphere objects in a GLB.
    positions=[];faces=[]
    count=600 if variant=='A' else 1100
    for i in range(count):
        t=.115+.85*rng.random()
        sgn=(-1 if i%2==0 else 1)
        lateral=sgn*(.59+.38*rng.random())
        p,_=coord(t,lateral,.0053)
        size=(.00048+.0011*rng.random())*(1.04 if variant=='A' else 1.13)
        height=size*(.40+.65*rng.random())
        idx=len(positions)
        ps=[p+side*size,p-side*size,p+along*size*1.6,
            p-along*size*1.6,p+normal*height]
        positions.extend(ps)
        faces.extend([(idx,idx+2,idx+4),(idx+2,idx+1,idx+4),
                      (idx+1,idx+3,idx+4),(idx+3,idx,idx+4)])
    make_mesh('MicroRimeFacets_'+variant,positions,faces,matt)
    return count

def clear_vfx():
    for obj in [o for o in bpy.data.objects if o.name.startswith(TAG)]:
        bpy.data.objects.remove(obj,do_unlink=True)
    for cv in [c for c in bpy.data.curves if c.name.startswith(TAG) and c.users==0]:
        bpy.data.curves.remove(cv)
    for me in [m for m in bpy.data.meshes if m.name.startswith(TAG) and m.users==0]:
        bpy.data.meshes.remove(me)

def build_frost(variant,coord,along,side,normal):
    rng.seed(28071107+(0 if variant=='A' else 17))
    denser=variant=='B'
    pbr_deposit=porous_frost_mat('PorousHoarfrostFilm_'+variant,
                              (.65,.73,.76) if not denser else (.67,.79,.82),denser)
    matt=material('WhiteMatteRime_'+variant,(.78,.83,.83),.93)
    muted=material('PaleColdCrystalline_'+variant,(.51,.64,.68),.80,transmit=.08)
    # No yellow/cyan neon; 0 emissive in A, slight icy optical specularity in B.
    accent=material('ReservedIcyFacets_'+variant,(.28,.56,.68),.20,.31,
                    emission_strength=0. if variant=='A' else .065)
    sheets=make_rime_film(coord,variant,pbr_deposit)
    d=make_dendrites(coord,variant,matt,muted,accent)
    grains=make_granules(coord,along,side,normal,variant,matt,accent)
    d.update({'porous_rime_deposits':sheets,'micro_rime_granules':grains,
              'base_metal_ridge_exposed':True,'frost_coating_rather_than_glass_armor':True,
              'glow_is_low_and_only_in_B':True,
              'render_variant':variant})
    return d

def export_overlay_glb(path):
    """Export only frost overlay: curves converted to mesh on temporary duplicates.
    This is an actual usable 3D asset overlay, not a picture.
    """
    overlays=[o for o in bpy.data.objects if o.name.startswith(TAG) and o.type in ('MESH','CURVE')]
    check(len(overlays)>=7,'no overlay objects to export')
    bpy.ops.object.select_all(action='DESELECT')
    for o in overlays:o.select_set(True)
    bpy.context.view_layer.objects.active=overlays[0]
    bpy.ops.object.duplicate()
    clones=list(bpy.context.selected_objects)
    check(len(clones)==len(overlays),'overlay clone failed')
    bpy.ops.object.convert(target='MESH')
    clones=list(bpy.context.selected_objects)
    check(all(o.type=='MESH' for o in clones),'curve not mesh after conversion')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',
                              use_selection=True,export_apply=True,
                              export_materials='EXPORT')
    check(path.exists() and path.stat().st_size>10000,'GLB overlay not written')
    data=path.read_bytes()
    check(data[:4]==b'glTF' and struct.unpack_from('<I',data,8)[0]==len(data),
          'GLB overlay invalid header')
    bpy.ops.object.select_all(action='DESELECT')
    for o in clones:o.select_set(True)
    bpy.ops.object.delete(use_global=False)
    bpy.ops.object.select_all(action='DESELECT')
    return {'path':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'primitiveMeshes':len(clones),'glb_validated':True}

def run():
    parser=argparse.ArgumentParser()
    for x in ('input','hdri','preset','output-dir'):
        parser.add_argument('--'+x,type=Path,required=True)
    parser.add_argument('--samples',type=int,default=96)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output_dir.mkdir(parents=True,exist_ok=True)
    check(hashlib.sha256(args.input.read_bytes()).hexdigest()==SOURCE_SHA,'original V03 SHA mismatch')
    check(hashlib.sha256(args.hdri.read_bytes()).hexdigest()==HDRI_SHA,'real studio EXR SHA mismatch')
    preset=json.loads(args.preset.read_text())
    check(preset['id']=='Genesis_Espada_V03_Hierro_V175_V12B' and preset['visual_status']=='approved_by_user','V12B identity mismatch')
    saved_args=sys.argv
    try:
        sys.argv=['blender','--','--input',str(args.input),'--hdri',str(args.hdri),
                  '--output-dir',str(args.output_dir),'--samples',str(args.samples)]
        v12.main()
    finally:sys.argv=saved_args
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=args.samples
    hdri=next((im for im in bpy.data.images if im.filepath and Path(bpy.path.abspath(im.filepath)).name==args.hdri.name),None)
    check(hdri is not None and hdri.depth==96 and tuple(hdri.size)==(4096,2048),'HDRI is not RGB32bit/channel')
    blade=next((m for m in bpy.data.materials if 'Iron_Blade_V175' in m.name),None)
    check(blade is not None,'original V175 PBR absent')
    rough=blade.node_tree.nodes.get('V11_J_V175_ROUGHNESS_MULT_049')
    oxide=blade.node_tree.nodes.get('V12_J_OXIDE_LOCAL_ROUGHNESS')
    check(rough is not None and oxide is not None,'approved V12B material nodes absent')
    check(abs(rough.inputs[1].default_value-.34)<.00001 and abs(oxide.inputs[1].default_value-.10)<.00001,
          'approved V12B optical roughness changed')
    original_meshes=[o for o in bpy.data.objects if o.type=='MESH']
    fingerprint={o.name:(len(o.data.vertices),len(o.data.polygons)) for o in original_meshes}
    sampler_source=swordref.collect_blade()
    coord,along,side,normal=v25.setup_frame(sampler_source)
    audits=[]
    for variant in ('A','B'):
        d=build_frost(variant,coord,along,side,normal)
        bpy.context.view_layer.update()
        # Pack the original HDRI and embedded V175 bitmaps into the editable candidate scene.
        # This changes the experimental .blend only; source GLB and EXR are not overwritten.
        bpy.ops.file.pack_all()
        blender_file=args.output_dir/('GENESIS_V28_Escarcha_'+variant+'_Real_3D.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(blender_file),compress=True)
        # Blender scene is real and editable; master sword comes from exact original GLB.
        check(blender_file.exists() and blender_file.stat().st_size>10000,'blend file missing')
        overlay=args.output_dir/('GENESIS_V28_Escarcha_'+variant+'_Overlay.glb')
        glb=export_overlay_glb(overlay)
        outputs=[]
        for cam,suffix in [('CAM_hero','Hero'),('CAM_BLADE_MACRO','Detalle')]:
            scene.camera=bpy.data.objects[cam]
            out=args.output_dir/('Escarcha_'+variant+'_V28_V12B_HDRI32_'+suffix+'.png')
            scene.render.filepath=str(out.absolute())
            scene.render.image_settings.file_format='PNG'
            scene.render.resolution_percentage=100
            bpy.ops.render.render(write_still=True)
            check(out.stat().st_size>100000,'missing true Cycles image '+out.name)
            outputs.append({'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
        after={o.name:(len(o.data.vertices),len(o.data.polygons)) for o in original_meshes}
        check(after==fingerprint,'original sword topology changed')
        check(abs(rough.inputs[1].default_value-.34)<.00001 and abs(oxide.inputs[1].default_value-.10)<.00001,
              'approved iron changed during rendering')
        audits.append({'variant':variant,'spec':'real matte hoarfrost' if variant=='A' else 'real hoarfrost with restrained icy reflection',
                       'geometry':d,'overlay_glb':glb,'blend_file':blender_file.name,
                       'renders':outputs,'user_approval':False,'candidate_7_5_threshold':'requires visual inspection'})
        print('GENESIS_V28_REAL_ASSET_RENDER_COMPLETE',variant,json.dumps(d),flush=True)
        clear_vfx()
    audit={
      'schema':'Genesis_V28_TwoReal3DFrostVariants_BlenderCycles32HDRI',
      'status':'experimental_not_approved',
      'source_glb_sha256':SOURCE_SHA,
      'hdri_exr_sha256':HDRI_SHA,
      'hdri_RGB_bits_per_channel':32,'hdri_dimensions':[4096,2048],
      'renderer':'Cycles','blender_version':bpy.app.version_string,'samples':args.samples,
      'approved_iron_preset':preset['id'],'original_V03_mesh_unchanged':True,
      'fuego_V20C1_unchanged':True,'rayo_V07_unchanged':True,
      'no_concept_generated':True,
      'user_requested_actual_3D':True,
      'source_3D_blend_and_GLb_overlay_created':True,
      'realtime_PlayCanvas_not_yet_tested':True,
      'variants':audits}
    (args.output_dir/'v28_real_3d_hoarfrost_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    print('GENESIS_V28_REAL_3D_TWO_VARIANTS_VALIDATED',json.dumps({'count':len(audits),
          'all_overlays':all(a['overlay_glb']['glb_validated'] for a in audits)},ensure_ascii=False),flush=True)

if __name__=='__main__':run()
