#!/usr/bin/env python3
"""Actual Blender 4.5.13 / Cycles / HDRI32 QA of V008 sword+shield demo clips.

Shield-ready left arm is shown WITHOUT substituting an unapproved shield.
The approved V12B iron sword original is pulled temporarily into the runner,
never included in public uploads. The 10 source animations are preserved.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qa_grip_v007_palm_fit import (
  impt,ms,bnd,surface_v12b,lighting,sha,aim,lamp,centroid_for_group,attach_to_socket
)
def assign(arm,needle,fraction=0.):
    acts=[act for act in bpy.data.actions if needle in act.name]
    assert len(acts)==1,(needle,[a.name for a in bpy.data.actions])
    act=acts[0]
    if arm.animation_data is None:arm.animation_data_create()
    arm.animation_data.action=act
    if getattr(act,'slots',None):
        slots=list(act.slots)
        if slots:arm.animation_data.action_slot=slots[0]
    start,end=act.frame_range
    frame=round(start+(end-start)*fraction)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {'clip':act.name,'frame':frame,'source_frame_range':[start,end]}
def joint_position(arm,bone):
    return (arm.matrix_world@arm.pose.bones[bone].matrix).translation.copy()
def lowest_weighted_boot_sole(evaluated_person,foot_bone):
    """Measure real deformed boot geometry, not only the ankle joint."""
    pts=[];dep=bpy.context.evaluated_depsgraph_get()
    for ob in ms(evaluated_person):
        group=ob.vertex_groups.get(foot_bone)
        if not group:continue
        ev=ob.evaluated_get(dep)
        mesh=ev.to_mesh()
        try:
            for v in ob.data.vertices:
                if not any(g.group==group.index and g.weight>.55 for g in v.groups):continue
                pts.append((ev.matrix_world@mesh.vertices[v.index].co).z)
        finally:ev.to_mesh_clear()
    return (round(min(pts),5),len(pts)) if len(pts)>6 else (None,len(pts))
def main():
    parser=argparse.ArgumentParser()
    for k in ('character','sword','hdri','preset','out'):
        parser.add_argument('--'+k,required=True,type=Path)
    a=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.out.mkdir(parents=True,exist_ok=True)
    p=json.loads(a.preset.read_text())
    assert sha(a.sword)==p['source_original']['sha256'],'wrong sword'
    assert sha(a.hdri)==p['lighting']['hdri_sha256'],'wrong HDRI'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    person=impt(a.character)
    arms=[o for o in person if o.type=='ARMATURE']
    assert len(arms)==1
    arm=arms[0]
    assert len(arm.data.bones)==24
    assert len(bpy.data.actions)>=12
    poses={}
    poses['baseline']=assign(arm,'Idle_02',0.)
    baseline_l=joint_position(arm,'LeftHand')
    poses['idle']=assign(arm,'GENESIS_SWORD_SHIELD_IDLE_V010',0.)
    raised_l=joint_position(arm,'LeftHand')
    raise_up=raised_l.z-baseline_l.z
    shield_forward=baseline_l.y-raised_l.y
    assert raise_up>.065,('shield hand not raised',raise_up)
    assert shield_forward>.12,('shield arm still backwards',shield_forward)
    sockets={}
    for name,bone in (('GENESIS_SOCKET_WEAPON_R','RightHand'),('GENESIS_SOCKET_SHIELD_L','LeftHand')):
        ob=bpy.data.objects.get(name)
        assert ob is not None
        sockets[name]=ob
        # Repair Blender's centimeter-skin glTF-import joint-child Empty offset
        # for Cycles QA only. Native GLB child-of-joint transforms are preserved.
        w=arm.matrix_world@arm.pose.bones[bone].matrix@Matrix.Translation((0,6,0))
        ob.parent=None
        ob.matrix_world=w
        bpy.context.view_layer.update()
        store=ob.matrix_world.copy()
        ob.parent=arm;ob.parent_type='BONE';ob.parent_bone=bone;ob.matrix_world=store
        bpy.context.view_layer.update()
        gap=(ob.matrix_world.translation-joint_position(arm,bone)).length
        assert abs(gap-.06)<.015,(name,gap)
    sword=impt(a.sword)
    surf=surface_v12b(sword)
    iron=[ob for ob in ms(sword) if any(mat and 'Iron_Blade_V175' in mat.name for mat in ob.data.materials)]
    assert iron
    lo,hi=bnd(sword);ext=hi-lo
    axis=max(range(3),key=lambda i:ext[i])
    srcdir=Vector(tuple(int(i==axis) for i in range(3)))
    side=1. if sockets['GENESIS_SOCKET_WEAPON_R'].matrix_world.translation.x>0 else -1.
    desired=Vector((.11*side,-.06,-.992)).normalized()
    rot1=srcdir.rotation_difference(desired)
    ilo,ihi=bnd(iron);e=ihi-ilo
    transverse=[i for i in range(3) if i!=axis]
    thin_axis=min(transverse,key=lambda i:e[i])
    facing=Vector(tuple(int(i==thin_axis) for i in range(3)))
    face1=rot1@facing
    frontal=Vector((.18,-1,.17))
    ff=(frontal-desired*frontal.dot(desired)).normalized()
    face1=(face1-desired*face1.dot(desired)).normalized()
    rot=(face1.rotation_difference(ff)@rot1).to_matrix().to_4x4()
    grip=(lo+hi)*.5;grip[axis]=lo[axis]+.175*ext[axis]
    scale=.8925/ext[axis]
    palm,count=centroid_for_group(ms(person),'RightHand')
    assert palm is not None and count>=50
    hand=palm+Vector((-.013,-.013,-.003))
    target=Matrix.Translation(hand)@rot@Matrix.Scale(scale,4)@Matrix.Translation(-grip)
    root=attach_to_socket(sword,target,sockets['GENESIS_SOCKET_WEAPON_R'])
    assert root.parent==sockets['GENESIS_SOCKET_WEAPON_R']
    bpy.context.view_layer.update()
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU';scene.cycles.samples=22
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.30
    hdri=lighting(a.hdri)
    all_objs=ms(person)+ms(sword)
    b0,b1=bnd(all_objs)
    mid=(b0+b1)*.5
    size=(b1-b0).z
    blade0,blade1=bnd(iron);blade=(blade0+blade1)*.5
    lamp('V011_KEY',mid+Vector((-2.,-2.5,2.4)),mid,80,2.5,2.8)
    lamp('V011_RIM',mid+Vector((1.8,1.6,1.8)),mid,42,2.0,2.6)
    lamp('V011_BLADE_SOFTBOX',blade+Vector((-.5,-1.05,1.)),blade,99,1.45,2.1)
    lamp('V011_BLADE_RIM',blade+Vector((.4,-1.0,.6)),blade,29,.24,1.8)
    # Neutral ground/shadows in review renders only; not part of exported rig GLB.
    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.035))
    floor_obj=bpy.context.object;floor_obj.name='QA_ONLY_NEUTRAL_STUDIO_FLOOR'
    floor_mat=bpy.data.materials.new('QA_ONLY_GRAPHITE_FLOOR')
    floor_mat.use_nodes=True
    bsdf=floor_mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(.055,.057,.060,1.)
    bsdf.inputs['Metallic'].default_value=0.
    bsdf.inputs['Roughness'].default_value=.87
    floor_obj.data.materials.append(floor_mat)
    render_log=[]
    sole_samples=[]
    def snapshot(label,mode,fraction,offset,height=2.2,resolution=1152):
        pose=assign(arm,mode,fraction)
        left_min,left_count=lowest_weighted_boot_sole(person,'LeftFoot')
        right_min,right_count=lowest_weighted_boot_sole(person,'RightFoot')
        sole_samples.append({'pose':pose['clip'],'fraction':fraction,
          'left_min_z_m':left_min,'right_min_z_m':right_min,
          'left_vertices':left_count,'right_vertices':right_count})
        midpoint=Vector((0.,0.,1.05)) # full-body camera centered instead of mesh rest bounds
        cam_data=bpy.data.cameras.new('Camera_'+label)
        cam=bpy.data.objects.new('Camera_'+label,cam_data)
        scene.collection.objects.link(cam);scene.camera=cam
        cam.location=midpoint+Vector(offset).normalized()*size*2.65
        aim(cam,midpoint)
        cam_data.type='ORTHO';cam_data.ortho_scale=height
        scene.render.resolution_x=resolution;scene.render.resolution_y=resolution
        dst=a.out/(label+'.png')
        scene.render.filepath=str(dst.resolve())
        bpy.ops.render.render(write_still=True)
        assert dst.stat().st_size>120000
        render_log.append({'image':dst.name,'bytes':dst.stat().st_size,
                           'sha256':sha(dst),'pose':pose,
                           'right_hand_world_m':list(joint_position(arm,'RightHand')),
                           'left_hand_world_m':list(joint_position(arm,'LeftHand'))})
    # Twelve independent original Blender/Cycles animation frames, not
    # frame interpolation or a generated illustration.
    for i in range(12):
        fraction=i/12.
        snapshot('V011_WALK_%02d'%i,'GENESIS_SWORD_SHIELD_WALK_V010',fraction,
                 (.65,-1,.12),2.58,800)
    # Verify feet physically change position as the new WALK clip advances.
    feet=[]
    for f in (0,.25,.5,.75):
        assign(arm,'GENESIS_SWORD_SHIELD_WALK_V010',f)
        feet.append({'fraction':f,'left':list(joint_position(arm,'LeftFoot')),
                     'right':list(joint_position(arm,'RightFoot'))})
    left_max=max((Vector(v['left'])-Vector(feet[0]['left'])).length for v in feet)
    right_max=max((Vector(v['right'])-Vector(feet[0]['right'])).length for v in feet)
    assert max(left_max,right_max)>.07,('walk animation barely moving',left_max,right_max)
    report={
      'status':'V011_REAL_CYCLES_ANIMATION_12FRAMES_PENDING_VISUAL_REVIEW',
      'original_animations_intact':True,'new_clips':['GENESIS_SWORD_SHIELD_IDLE_V010','GENESIS_SWORD_SHIELD_WALK_V010'],
      'joint_count':len(arm.data.bones),'blender_action_count':len(bpy.data.actions),
      'shield_hand_raised_vertical_m':round(raise_up,4),
      'shield_hand_advanced_forward_m':round(shield_forward,4),
      'feet_positions':feet,'max_left_foot_travel_m':round(left_max,4),
      'max_right_foot_travel_m':round(right_max,4),
      'sword_original_sha256':sha(a.sword),'character_generated_sha256':sha(a.character),
      'sword_length_m':.8925,'sword_iron_material':surf,
      'approved_shield_model_mounted':False,'no_placeholder_shield':True,
      'finger_bones_added':False,
      'hdri':hdri,'renders':render_log,'playcanvas_runtime_tested':False,
      'human_visual_approved':False,
      'real_rendered_animation_frames':12,
      'animation_preview_source_glb':'V010 with 12 skeleton clips (10 original+2 new)',
      'studio_floor_z_m':-.035,
      'foot_sole_world_min_samples':sole_samples,
      'root_vertical_offset_m':-.065,
      'root_grounding_modified_only_new_animation_clips':True}
    (a.out/'POSE_QA_V011.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print('GENESIS_POSE_QA_V011',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
