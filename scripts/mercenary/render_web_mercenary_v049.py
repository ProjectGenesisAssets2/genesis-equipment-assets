#!/usr/bin/env python3
"""Genesis V049: genuinely render the standalone WebGL/PlayCanvas GLB after
repairing V015 forged iron PBR. Static guard stance, approved sword V12B.
Uses actual Blender 4.5.13 LTS Cycles and RGB 32bit EXR HDRI, no concepts.
"""
import bpy,argparse,sys,hashlib,json
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser()
for k in ('glb','hdri','out'):p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
data=a.glb.read_bytes();assert data[:4]==b'glTF'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.glb.resolve()))
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(rigs)==1 and len(rigs[0].data.bones)==65
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert len(meshes)>=14,len(meshes)
iron=next(m for m in bpy.data.materials if 'V015_IronV175_Hammered_Only_Front_DERIVED' in m.name)
bsdf=next(n for n in iron.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
face_color=tuple(round(float(x),4) for x in bsdf.inputs['Base Color'].default_value)
assert .08<face_color[0]<.30,('V015 still white!',face_color)
assert .70<bsdf.inputs['Metallic'].default_value<.9
print('V049_REAL_FORGED_IRON_FACE_PBR_VALUES',face_color,
      'metallic',bsdf.inputs['Metallic'].default_value,
      'rough',bsdf.inputs['Roughness'].default_value,flush=True)
world=bpy.data.worlds.new('GENESIS_STUDIO_EXR32_PUBLISHER_QA')
bpy.context.scene.world=world;world.use_nodes=True
nd=world.node_tree.nodes;nd.clear();lk=world.node_tree.links
env=nd.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth==96
bg=nd.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.54
out=nd.new('ShaderNodeOutputWorld')
lk.new(env.outputs['Color'],bg.inputs['Color']);lk.new(bg.outputs['Background'],out.inputs['Surface'])
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
focus=Vector((0,0,.98))
for name,vec,power,size in [('GENESIS_KEY',(-2,-2,2.4),330,3.0),
                            ('GENESIS_RIM',(1.9,1.8,1.7),185,2.4),
                            ('GENESIS_SHIELD_FRONT',(.55,-1.55,.9),115,2)]:
 dat=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,dat)
 bpy.context.scene.collection.objects.link(ob);ob.location=focus+Vector(vec)
 aim(ob,focus);dat.energy=power;dat.shape='DISK';dat.size=size
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-.045))
floor=bpy.context.object;floor.name='QA_FLOOR_ONLY'
fm=bpy.data.materials.new('QA_STONE_FLOOR');fm.use_nodes=True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.09,.095,.105,1)
fm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
floor.data.materials.append(fm)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=32
sc.cycles.device='CPU';sc.render.resolution_x=820;sc.render.resolution_y=900
sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc.view_settings.view_transform='AgX'
sc.view_settings.look='AgX - Medium High Contrast'
sc.view_settings.exposure=-.28
images=[]
def render(label,vec,target,scale):
 cam=bpy.data.objects.new(label+'_cam',bpy.data.cameras.new(label+'_camera'))
 sc.collection.objects.link(cam);cam.location=Vector(target)+Vector(vec).normalized()*4.9
 aim(cam,target);cam.data.type='ORTHO';cam.data.ortho_scale=scale
 sc.camera=cam
 dest=a.out/(label+'.png');sc.render.filepath=str(dest.resolve())
 bpy.ops.render.render(write_still=True)
 assert dest.stat().st_size>55000
 images.append({'file':dest.name,'bytes':dest.stat().st_size})
render('V049_01_REAL_GENESIS_MERCENARY_SWORD_SHIELD_FRONT',(0,-1,.1),focus,2.65)
render('V049_02_REAL_GENESIS_MERCENARY_SWORD_SHIELD_THREE_QUARTER',(.65,-1,.16),focus,2.65)
# Read left wrist from original rig rest and center on genuine shield surface
left=(rigs[0].matrix_world@rigs[0].pose.bones['hand_l'].matrix).translation
render('V049_03_REAL_V015_FORGED_IRON_SHIELD_DETAIL',(-.45,-1,.13),left+Vector((.12,-.12,-.15)),1.14)
qa={'status':'V049_REAL_STANDALONE_GLB_REIMPORT_AND_CYCLES32_RENDERED_UNAPPROVED',
    'glb_sha256':hashlib.sha256(data).hexdigest(),
    'imported_mesh_count':len(meshes),'original_bones':len(rigs[0].data.bones),
    'V015_forged_iron_material_PBR_base_color':face_color,
    'V015_forged_metallic_factor':float(bsdf.inputs['Metallic'].default_value),
    'V015_forged_roughness_factor':float(bsdf.inputs['Roughness'].default_value),
    'hdri':a.hdri.name,'hdri_depth':env.image.depth,
    'render_engine':'CYCLES','renders':images,
    'in_game_scene_playwright_tested':False,'human_approved':False,'main_changed':False}
(a.out/'V049_ACTUAL_RENDER_IMPORT_QA.json').write_text(json.dumps(qa,indent=2))
print('V049_REAL_GENESIS_GUARD_STANCE_WEB_GLB_CYCLES32_VISUAL_TEST_PASS',json.dumps({'renders':len(images),'mats':face_color,'bones':len(rigs[0].data.bones)}),flush=True)
