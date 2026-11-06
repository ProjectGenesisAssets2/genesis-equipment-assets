#!/usr/bin/env python3
"""Project Genesis: actual Meshy character + original V03/V175 V12B sword.
Private Fab sword is used ephemerally in CI, NEVER exported or published.
Renders in Blender Cycles with real verified EXR HDRI RGB 32 bits/channel.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def impt(p):
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(p.resolve()))
    added=[x for x in bpy.context.scene.objects if x not in before]
    assert any(x.type=='MESH' for x in added),p
    return added
def ms(objects):return [x for x in objects if x.type=='MESH']
def bnd(objects):
    pts=[o.matrix_world@Vector(v) for o in ms(objects) for v in o.bound_box]
    assert pts,"empty mesh bounds"
    return Vector([min(x[i] for x in pts) for i in range(3)]),Vector([max(x[i] for x in pts) for i in range(3)])
def attach(objs,target,arm,bone,name):
    root=bpy.data.objects.new(name,None)
    bpy.context.scene.collection.objects.link(root)
    root.empty_display_type='ARROWS';root.empty_display_size=.08
    original=set(objs)
    for o in objs:
        if o.parent not in original:
            world=o.matrix_world.copy()
            o.parent=root
            o.matrix_world=world
    bpy.context.view_layer.update()
    root.matrix_world=target
    bpy.context.view_layer.update()
    world=root.matrix_world.copy()
    root.parent=arm
    root.parent_type='BONE'
    root.parent_bone=bone
    root.matrix_world=world
    root['genesis_socket']=bone
    bpy.context.view_layer.update()
    return root
def img(mat,fragment):
    return next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and fragment in n.image.name),None)
def surface_v12b(objects):
    mats={mat.name:mat for ob in ms(objects) for mat in ob.data.materials if mat}
    iron=next((mat for name,mat in mats.items() if 'Iron_Blade_V175' in name),None)
    fab=mats.get('DefaultMaterial')
    assert iron and fab, 'Original approved iron palette and Fab PBR material not found: '+repr(list(mats))
    t=iron.node_tree
    bsdf=next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED')
    src_color=bsdf.inputs['Base Color'].links[0].from_socket
    src_rough=bsdf.inputs['Roughness'].links[0].from_socket
    normal=img(iron,'Genesis_V175_Hierro_Normal_2K')
    orm=img(iron,'Genesis_V175_Hierro_ORM_2K')
    fab_orm=img(fab,'Image_1')
    fab_normal=img(fab,'Image_2')
    assert all((normal,orm,fab_orm,fab_normal)),'V12B authentic PBR source maps missing'
    normal.image=fab_normal.image
    metal=t.nodes.new('ShaderNodeTexImage');metal.image=fab_orm.image;metal.image.colorspace_settings.name='Non-Color'
    if orm.inputs['Vector'].is_linked:t.links.new(orm.inputs['Vector'].links[0].from_socket,metal.inputs['Vector'])
    split=t.nodes.new('ShaderNodeSeparateColor');split.mode='RGB'
    t.links.new(metal.outputs['Color'],split.inputs['Color'])
    floor=t.nodes.new('ShaderNodeMath');floor.operation='MAXIMUM';floor.inputs[1].default_value=.98
    t.links.new(split.outputs['Blue'],floor.inputs[0])
    t.links.new(floor.outputs[0],bsdf.inputs['Metallic'])
    rough=t.nodes.new('ShaderNodeMath');rough.operation='MULTIPLY';rough.use_clamp=True;rough.inputs[1].default_value=.34
    t.links.new(src_rough,rough.inputs[0])
    coord=t.nodes.new('ShaderNodeTexCoord');axes=t.nodes.new('ShaderNodeVectorMath');axes.operation='MULTIPLY'
    axes.inputs[1].default_value=(27,3.2,8)
    t.links.new(coord.outputs['Generated'],axes.inputs[0])
    noise=t.nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='3D'
    noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=3
    noise.inputs['Roughness'].default_value=.67;noise.inputs['Distortion'].default_value=.12
    t.links.new(axes.outputs['Vector'],noise.inputs['Vector'])
    mask=t.nodes.new('ShaderNodeMapRange');mask.interpolation_type='SMOOTHSTEP';mask.clamp=True
    mask.inputs['From Min'].default_value=.52;mask.inputs['From Max'].default_value=.66
    mask.inputs['To Min'].default_value=0;mask.inputs['To Max'].default_value=1
    t.links.new(noise.outputs['Fac'],mask.inputs['Value'])
    oxide=t.nodes.new('ShaderNodeMath');oxide.operation='MULTIPLY'
    oxide.inputs[1].default_value=.10
    t.links.new(mask.outputs['Result'],oxide.inputs[0])
    finish=t.nodes.new('ShaderNodeMath');finish.operation='ADD';finish.use_clamp=True
    t.links.new(rough.outputs[0],finish.inputs[0]);t.links.new(oxide.outputs[0],finish.inputs[1])
    t.links.new(finish.outputs[0],bsdf.inputs['Roughness'])
    assert bsdf.inputs['Base Color'].links[0].from_socket == src_color,'V175 color altered'
    triangles=sum(len(ob.data.loop_triangles) for ob in ms(objects))
    assert triangles==2150,'Original V03 geometry modified: '+str(triangles)
    return {'triangles':triangles,'base_color':'V175 unchanged','roughness_multiplier':.34,
     'oxide_roughness':.10,'metallic_min':.98,'normal':'Fab Image_2'}
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def lamp(n,p,target,w,size,sy):
    d=bpy.data.lights.new(n,'AREA');d.energy=w;d.shape='RECTANGLE';d.size=size;d.size_y=sy
    o=bpy.data.objects.new(n,d);bpy.context.collection.objects.link(o);o.location=p;aim(o,target)
def lighting(hdr):
    h=bpy.data.images.load(str(hdr.resolve()))
    assert h.file_format=='OPEN_EXR' and h.depth==96 and list(h.size)==[4096,2048],('HDRI must be 32-bit RGB per channel',h.depth,list(h.size))
    w=bpy.data.worlds.new('PolyHaven_Studio_Small_09_32bpc');w.use_nodes=True;bpy.context.scene.world=w
    ns=w.node_tree.nodes;ns.clear();links=w.node_tree.links
    env=ns.new('ShaderNodeTexEnvironment');env.image=h
    bg=ns.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.70
    links.new(env.outputs['Color'],bg.inputs['Color'])
    dark=ns.new('ShaderNodeBackground');dark.inputs['Color'].default_value=(.016,.020,.027,1);dark.inputs['Strength'].default_value=1
    lp=ns.new('ShaderNodeLightPath');mx=ns.new('ShaderNodeMixShader')
    links.new(lp.outputs['Is Camera Ray'],mx.inputs[0]);links.new(bg.outputs[0],mx.inputs[1]);links.new(dark.outputs[0],mx.inputs[2])
    o=ns.new('ShaderNodeOutputWorld');links.new(mx.outputs[0],o.inputs['Surface'])
    return {'name':hdr.name,'depth_bpp':h.depth,'dimensions':list(h.size),'sha256':sha(hdr)}
def photo(out,objects):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=50
    scene.render.resolution_x=900;scene.render.resolution_y=1000
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.10
    mn,mx=bnd(objects);center=(mn+mx)*.5
    height=max(mx.z-mn.z,1)
    lamp('KEY_LARGE',center+Vector((-2.3,-2.7,2.3)),center,150,2.2,3.2)
    lamp('IRON_BLADE_STRIP',center+Vector((1.1,-2.0,2.4)),center,95,.3,2.6)
    lamp('REAR_RIM',center+Vector((1.8,2.2,1.6)),center,85,1.8,2.6)
    outputs=[]
    for n,v in [('frente',(0,-1,.10)),('tres_cuartos',(.72,-1,.18)),('perfil',(1,0,.10)),('posterior',(0,1,.13))]:
        c=bpy.data.objects.new('CAM_'+n,bpy.data.cameras.new('CAM_'+n))
        bpy.context.collection.objects.link(c)
        c.location=center+Vector(v).normalized()*height*2.8;aim(c,center)
        c.data.type='ORTHO';c.data.ortho_scale=height*1.15
        scene.camera=c
        p=out/(n+'_MERCENARIO_ESPADA_V12B_HDRI32.png')
        scene.render.filepath=str(p.resolve())
        bpy.ops.render.render(write_still=True)
        assert p.stat().st_size>70000
        outputs.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
    return outputs
def main():
    p=argparse.ArgumentParser()
    for key in ('mercenary','sword','shield','hdri','preset','out'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
    preset=json.loads(a.preset.read_text())
    assert preset['id']=='Genesis_Espada_V03_Hierro_V175_V12B'
    assert preset['visual_status']=='approved_by_user'
    assert sha(a.sword)==preset['source_original']['sha256']
    assert sha(a.hdri)==preset['lighting']['hdri_sha256']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    person=impt(a.mercenary)
    arms=[o for o in person if o.type=='ARMATURE']
    assert arms
    arm=max(arms,key=lambda x:len(x.data.bones))
    assert len(arm.data.bones)==24,('unexpected rig bones',len(arm.data.bones))
    assert len(bpy.data.actions)>=10,'Missing Meshy animated clips'
    bpy.context.view_layer.update()
    pR=arm.matrix_world @ arm.pose.bones['RightHand'].matrix
    pL=arm.matrix_world @ arm.pose.bones['LeftHand'].matrix
    handR=pR.translation;handL=pL.translation
    body_min,body_max=bnd(person);char_center=(body_min+body_max)*.5
    ext=body_max-body_min
    assert 1.2<ext.z<5,('Unexpected model scale',list(ext))
    sword=impt(a.sword);surface=surface_v12b(sword)
    smin,smax=bnd(sword);slen=smax-smin
    axis=max(range(3),key=lambda i:slen[i])
    srcdir=Vector([int(i==axis) for i in range(3)])
    side=1.0 if handR.x>char_center.x else -1.0
    desired=Vector((.37*side,-.2,-.91)).normalized()
    grip=(smin+smax)*.5;grip[axis]=smin[axis]+.13*slen[axis]
    scale=1.05/slen[axis]
    rot=srcdir.rotation_difference(desired).to_matrix().to_4x4()
    transform=Matrix.Translation(handR+Vector((side*.015,-.04,.01)))@rot@Matrix.Scale(scale,4)@Matrix.Translation(-grip)
    attach(sword,transform,arm,'RightHand','GENESIS_RIGHT_SWORD_V03_V175_V12B')
    shield=impt(a.shield)
    # This is the game placeholder shield, NOT the unapproved experimental V015.
    # Neutral PBR colors avoid V002's washed-out white back.
    for mat in {m for ob in ms(shield) for m in ob.data.materials if m and m.use_nodes}:
        shader=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if shader is None:continue
        base=shader.inputs['Base Color']
        rgba=base.default_value
        metal=(sum(rgba[:3])>1.65 or 'shield' in mat.name.lower())
        for link in list(base.links):mat.node_tree.links.remove(link)
        base.default_value=((.19,.22,.24,1) if metal else (.32,.17,.10,1))
        shader.inputs['Metallic'].default_value=.72 if metal else .0
        shader.inputs['Roughness'].default_value=.43 if metal else .78
    dmin,dmax=bnd(shield);dd=dmax-dmin;cc=(dmin+dmax)*.5
    planar=sorted(range(3),key=lambda i:dd[i],reverse=True)[:2]
    thin=next(i for i in range(3) if i not in planar)
    normal=Vector([int(i==thin) for i in range(3)])
    rot=normal.rotation_difference(Vector((0,1,0))).to_matrix().to_4x4()
    scale_sh=.70/max(dd[i] for i in planar)
    other=-side
    center=handL+Vector((other*.10,-.19,.12))
    target=Matrix.Translation(center)@rot@Matrix.Scale(scale_sh,4)@Matrix.Translation(-cc)
    attach(shield,target,arm,'LeftHand','GENESIS_LEFT_SHIELD_TEMPORARY')
    bpy.context.view_layer.update()
    hdri=lighting(a.hdri)
    renders=photo(a.out,ms(person)+ms(sword)+ms(shield))
    report={'status':'V003_UNAPPROVED_EXPERIMENTAL_RENDER_ONLY','character':'Meshy captain CC0 candidate',
      'character_sha256':sha(a.mercenary),'rig_bones':len(arm.data.bones),
      'animation_clips':len(bpy.data.actions),'sword_name':'V03 V175 V12B','sword_sha256':sha(a.sword),
      'sword_source_published':False,'sword_surface':surface,'sword_scale':scale,
      'shield':'existing game shield_round.glb TEMPORARY PBR LOOK (NOT V015)','shield_sha256':sha(a.shield),
      'right_bone':'RightHand','left_bone':'LeftHand','right_hand_world':list(handR),
      'left_hand_world':list(handL),'hdri':hdri,'blender':bpy.app.version_string,
      'renderer':'Cycles','renders':renders,'glb_exported':False,'game_integrated':False,
      'main_untouched':True,'visual_approval':False}
    (a.out/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('GENESIS_MERCENARY_REAL_V12B_RENDER',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
