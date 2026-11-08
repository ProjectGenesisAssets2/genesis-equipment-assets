#!/usr/bin/env python3
"""Genesis V046b: restore authentic CC0 VitruvianGodot male-human facial PBR maps.

Do not invent a head, re-sculpt geometry or add a fake 'skin' recolor. Reconnect
actual UV0 on VitSkin to vit_face_bc, vit_face_n, vit_face_rough and source
textures for iris, sclera and mouth. Export genuine self-contained GLB and
render three real Cycles views under 32-bit/channel EXR studio HDRI.
No integration with Quaternius yet; no main change or approval.
"""
import argparse,bpy,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector

pa=argparse.ArgumentParser()
for key in ('source','textures','hdri','out'):pa.add_argument('--'+key,type=Path,required=True)
a=pa.parse_args(sys.argv[sys.argv.index('--')+1:])
a.out.mkdir(parents=True,exist_ok=True)
old_bytes=a.source.read_bytes()
assert old_bytes[:4]==b'glTF' and len(old_bytes)>9000000
files={
 'face_color':'vit_face_bc.png','face_normal':'vit_face_n.png',
 'face_roughness':'vit_face_rough.png',
 'iris':'vit_iris.png','sclera':'vit_sclera.png','mouth':'vit_mouth.png'
}
assert all((a.textures/n).stat().st_size>10000 for n in files.values())
source_hashes={name:hashlib.sha256((a.textures/n).read_bytes()).hexdigest() for name,n in files.items()}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
scene=bpy.context.scene
meshes=[x for x in bpy.data.objects if x.type=='MESH']
assert len(meshes)==7, [(ob.name,len(ob.data.vertices)) for ob in meshes]
assert not [x for x in bpy.data.objects if x.type=='ARMATURE'],'do not introduce a made-up rig'
src_verts={ob.name:len(ob.data.vertices) for ob in meshes}
face=next(ob for ob in meshes if ob.name.startswith('cm_vitruvian') and len(ob.data.vertices)>10000)
material_names={mat.name for ob in meshes for mat in ob.data.materials if mat}
assert 'VitSkin' in material_names and 'VitIris' in material_names

def texture(kind,noncolor=False):
  name=files[kind];im=bpy.data.images.load(str((a.textures/name).resolve()),check_existing=True)
  im.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
  assert im.size[0]>=512 and im.size[1]>=512,(kind,tuple(im.size))
  im.pack()
  return im
images={name:texture(name,name in ('face_normal','face_roughness')) for name in files}

def material(name,rgba=(1,1,1,1),rough=.60,sss=0.0,base=None,normal=None,roughmap=None,alpha=None):
  m=bpy.data.materials.new('GENESIS_V046B_'+name)
  m.use_nodes=True
  nd=m.node_tree.nodes;nd.clear();li=m.node_tree.links
  output=nd.new('ShaderNodeOutputMaterial');output.location=(760,0)
  bsdf=nd.new('ShaderNodeBsdfPrincipled');bsdf.location=(430,0)
  li.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
  bsdf.inputs['Base Color'].default_value=rgba
  bsdf.inputs['Metallic'].default_value=0.0
  bsdf.inputs['Roughness'].default_value=rough
  bsdf.inputs['IOR'].default_value=1.43
  if 'Subsurface Weight' in bsdf.inputs:bsdf.inputs['Subsurface Weight'].default_value=sss
  if 'Subsurface Radius' in bsdf.inputs:bsdf.inputs['Subsurface Radius'].default_value=(0.85,0.40,0.26)
  if alpha is not None:
    bsdf.inputs['Alpha'].default_value=alpha
    try:m.surface_render_method='DITHERED'
    except:pass
  if base:
    im=nd.new('ShaderNodeTexImage');im.image=images[base];im.label=base;im.location=(-520,300)
    li.new(im.outputs['Color'],bsdf.inputs['Base Color'])
  if roughmap:
    im=nd.new('ShaderNodeTexImage');im.image=images[roughmap];im.label=roughmap;im.location=(-520,-120)
    # The source's original Godot shader uses the *green* roughness channel.
    sep=nd.new('ShaderNodeSeparateColor');sep.mode='RGB';sep.location=(-250,-120)
    li.new(im.outputs['Color'],sep.inputs['Color'])
    li.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
  if normal:
    im=nd.new('ShaderNodeTexImage');im.image=images[normal];im.label=normal;im.location=(-520,-500)
    nm=nd.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.55;nm.location=(-200,-460)
    li.new(im.outputs['Color'],nm.inputs['Color'])
    li.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
  return m

# Skin color and original face UV0 from VitruvianGodot, not a painted concept.
mats={
 'VitSkin':material('HUMAN_SKIN_SOURCE_UV0',rough=.62,sss=.095,
                    base='face_color',normal='face_normal',roughmap='face_roughness'),
 'VitMouth':material('MOUTH_TEXTURE',rough=.67,base='mouth'),
 'VitIris':material('IRIS_TEXTURE',rough=.46,base='iris'),
 'VitSclera':material('SCLERA_TEXTURE',rgba=(.88,.86,.83,1),rough=.38,base='sclera'),
 'VitEyeBack':material('PUPIL_BACK',rgba=(.016,.014,.016,1),rough=.32),
 'VitCornea2':material('CLEAR_CORNEA',rgba=(.85,.85,.85,1),rough=.06,alpha=.04),
 'VitEyeshadow':material('EYELID_CONTACT',rgba=(.25,.14,.11,1),rough=.84,alpha=.22),
 'VitTearline':material('LACRIMAL_LINE',rgba=(.28,.095,.085,1),rough=.23,alpha=.64),
 'VitCaruncle':material('EYE_CORNER',rgba=(.49,.18,.17,1),rough=.38),
}
assigned={}
for ob in meshes:
  for i,old in enumerate(list(ob.data.materials)):
    if old is None:continue
    typ=old.name.split('.')[0]
    assert typ in mats,(ob.name,old.name)
    ob.data.materials[i]=mats[typ]
    assigned[typ]=assigned.get(typ,0)+1
assert assigned.get('VitSkin')==1 and assigned.get('VitMouth')==1
# The mouth is a different original UDIM tile (1006), and already has
# a local 0..1 UV1 on the GLB. Use that UV for mouth image.
for ob in meshes:
  if mats['VitMouth'] not in ob.data.materials:continue
  assert len(ob.data.uv_layers)>=2,(ob.name,list(ob.data.uv_layers))
  mouth_node=next(n for n in mats['VitMouth'].node_tree.nodes if n.type=='TEX_IMAGE')
  uv=bpy.data.materials['GENESIS_V046B_MOUTH_TEXTURE'].node_tree.nodes.new('ShaderNodeUVMap')
  uv.uv_map=ob.data.uv_layers[1].name;uv.location=(-750,300)
  mats['VitMouth'].node_tree.links.new(uv.outputs['UV'],mouth_node.inputs['Vector'])
  print('V046B_MOUTH_USE_ORIGINAL_UDIM_LOCAL_UV1',uv.uv_map)
assert len(meshes)==7 and {ob.name:len(ob.data.vertices) for ob in meshes}==src_verts

out_glb=a.out/'GENESIS_VITRUVIAN_HUMAN_FACE_PBR_V046B.glb'
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes:ob.select_set(True)
bpy.context.view_layer.objects.active=face
bpy.ops.export_scene.gltf(filepath=str(out_glb.resolve()),export_format='GLB',use_selection=True,export_animations=False,
                           export_image_format='AUTO')
assert out_glb.stat().st_size>10000000
print('V046B_SOURCE_PBR_GLB_EXPORTED',out_glb.stat().st_size)

allpoints=[ob.matrix_world@v.co for ob in meshes for v in ob.data.vertices]
lo=Vector(tuple(min(p[i] for p in allpoints) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in allpoints) for i in range(3)))
center=(lo+hi)/2
dimensions=hi-lo
world=bpy.data.worlds.new('GENESIS_V046B_32BIT_EXR_CYCLES')
scene.world=world;world.use_nodes=True
nodes=world.node_tree.nodes;nodes.clear();links=world.node_tree.links
env=nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(str(a.hdri.resolve()),check_existing=True)
assert env.image.depth>=96,('HDRI must be 32bit/channel',env.image.depth)
bg=nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.72
out=nodes.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color']);links.new(bg.outputs['Background'],out.inputs['Surface'])

def aim(ob,target):ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,offset,power,size):
  light=bpy.data.lights.new(name,'AREA')
  ob=bpy.data.objects.new(name,light)
  scene.collection.objects.link(ob)
  ob.location=center+Vector(offset)
  aim(ob,center)
  light.energy=power;light.shape='DISK';light.size=size
area('GENESIS_SOFTBOX_KEY',(-1.1,-1.65,1.6),500,2.6)
area('GENESIS_SOFTBOX_RIM',(1.5,1.2,1.3),310,2.4)
area('GENESIS_SOFTBOX_FILL',(.85,-1.4,.5),190,2.0)
scene.render.engine='CYCLES'
scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=750;scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.17

renders=[]
for name,vec in [('V046B_01_SKIN_FRONT',(0,-1,.05)),('V046B_02_SKIN_THREE_QUARTER',(.72,-1,.14)),('V046B_03_SKIN_SIDE',(1,-.10,.17))]:
  camdata=bpy.data.cameras.new(name+'_CameraData')
  cam=bpy.data.objects.new(name+'_Camera',camdata)
  scene.collection.objects.link(cam)
  cam.location=center+Vector(vec).normalized()*3.8
  aim(cam,center);camdata.type='ORTHO';camdata.ortho_scale=max(dimensions)*1.42
  scene.camera=cam
  target=a.out/(name+'.png');scene.render.filepath=str(target.resolve())
  bpy.ops.render.render(write_still=True)
  assert target.stat().st_size>65000,(name,target.stat().st_size)
  renders.append({'file':target.name,'bytes':target.stat().st_size})

report={
 'status':'V046B_REAL_SOURCE_SKIN_PBR_APPLIED_TO_ORIGINAL_VITRUVIAN_HEAD_UNAPPROVED',
 'license':'CC0 original character and images, code MIT, source ibrews/VitruvianGodot',
 'source_original_sha256':hashlib.sha256(old_bytes).hexdigest(),
 'output_glb_sha256':hashlib.sha256(out_glb.read_bytes()).hexdigest(),
 'output_glb_bytes':out_glb.stat().st_size,
 'unmodified_geometry':True,
 'original_mesh_vertex_counts':src_verts,
 'original_glb_uv0_preserved':True,
 'PBR_textures_original_sha256':source_hashes,
 'PBR_image_files_original':files,
 'material_uses':assigned,
 'original_skin_material':mats['VitSkin'].name,
 'skin_subsurface_weight':.095,
 'source_hdr_exr32':a.hdri.name,'HDRI_total_bits':env.image.depth,
 'render_engine':'CYCLES','renders':renders,
 'fitted_to_Ranger':False,'rebound_to_65bone_Ranger':False,
 'visual_approval':False,'main_changed':False
}
(a.out/'V046B_SOURCE_SKIN_QA.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('V046B_REAL_SKIN_PBR_AND_THREE_CYCLES_RENDER_PASS',
      json.dumps({'bytes':out_glb.stat().st_size,'materials':assigned,'renders':len(renders),'textures':files}),flush=True)
