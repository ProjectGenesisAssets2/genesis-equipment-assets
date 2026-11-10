import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
glb=Path(args[args.index('--input')+1]); hdri=Path(args[args.index('--hdri')+1]); out=Path(args[args.index('--out')+1]);out.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(glb.read_bytes()).hexdigest()=='2c3e2dd8761ad337dd1d0c63ecab2fab68a8698d072dbeb8594b257cb1cdecc3'
assert hashlib.sha256(hdri.read_bytes()).hexdigest()=='bbb83755cf731a87373bdd25e28b4a74f58c8c8a02bf348e960635265ffda558'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(glb))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert meshes
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
center=(lo+hi)/2;span=max((hi-lo).length,0.01)
cam_data=bpy.data.cameras.new('V12B identical camera');cam=bpy.data.objects.new('V12B identical camera',cam_data);bpy.context.collection.objects.link(cam)
cam.location=center+Vector((span*1.35,-span*1.85,span*0.9));direction=center-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=span*1.2
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=40
scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('A B environment');scene.world.use_nodes=True
nodes=scene.world.node_tree.nodes;nodes.clear();outnode=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');env=nodes.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(hdri));assert env.image.depth==96
scene.world.node_tree.links.new(bg.outputs['Background'],outnode.inputs['Surface'])
reports=[]
for name,use_hdri in [('A_NEUTRAL_LOW_REFLECTION',False),('B_APPROVED_EXR_HDRI32',True)]:
    if use_hdri:
        scene.world.node_tree.links.new(env.outputs['Color'],bg.inputs['Color']);bg.inputs['Strength'].default_value=0.9
        scene.view_settings.view_settings if False else None
        scene.view_settings.look='Medium High Contrast'
        scene.view_settings.view_settings if False else None
        scene.view_settings.exposure=0.5
    else:
        if bg.inputs['Color'].is_linked:scene.world.node_tree.links.remove(bg.inputs['Color'].links[0])
        bg.inputs['Color'].default_value=(0.12,0.12,0.12,1);bg.inputs['Strength'].default_value=1
        scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=0.5
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
    reports.append({'file':name+'.png','hdri_32bit':use_hdri,'camera':list(cam.location),'cycles_samples':scene.cycles.samples})
(out/'report.json').write_text(json.dumps({'source_glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'hdri_sha256':hashlib.sha256(hdri.read_bytes()).hexdigest(),'comparison':'Same GLB/camera/Cycles; neutral dark environment vs approved EXR HDRI32; not a WebGL rendering test','renders':reports},indent=2))
