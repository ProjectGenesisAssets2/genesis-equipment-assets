#!/usr/bin/env python3
"""Genesis V049: real Quaternius Ranger with corrected human eye/skin PBR.
Fix previous actual wax-white face via native skin atlas color correction and
separate human iris/pupil geometry skinned to existing 65-bone Head. Original
rig, finger skin weights and clothing remain untouched. Cycles EXR32.
No concept art, no main commit, visual candidate only.
"""
import argparse,bpy,sys,hashlib,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser()
for a in ('source','hdri','out'):p.add_argument('--'+a,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
raw=a.source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='fc1baff512c38a59660f7240b0da9e4a2bd19d038ccd055357b3635572fed7b4'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
arms=[o for o in bpy.data.objects if o.type=='ARMATURE']
assert len(arms)==1 and len(arms[0].data.bones)==65
arm=arms[0]
def obj(name):
 x=next((o for o in meshes if o.name.startswith(name)),None)
 assert x,name
 return x
face=obj('GENESIS_V045_BASE_MALE_REAL_FACE_AND_NECK')
eyes=obj('GENESIS_V045_BASE_MALE_EYES')
brows=obj('GENESIS_V045_BASE_MALE_EYEBROWS')
mat=next((m for m in bpy.data.materials if m.name.startswith('MI_Regular_Male')),None)
assert mat and mat.use_nodes
skin=mat.copy();skin.name='GENESIS_V049_ADULT_SKIN_PBR'
images=[n for n in skin.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
base=next((node for node in images if 'BaseColor' in node.image.name),None)
assert base,(skin.name,[n.image.name for n in images])
copy=base.image.copy();copy.name='GENESIS_V049_SKIN_WARMER_MATTE'
pixels=np.empty(len(copy.pixels),dtype=np.float32)
copy.pixels.foreach_get(pixels)
pixels=pixels.reshape((-1,4))
# Existing CC0 skin atlas is overexposed and mismatched to its realistic face.
# Warm and tone down the *albedo*, not the HDRI. Preserve original normal maps.
pixels[:,0]*=.79
pixels[:,1]*=.71
pixels[:,2]*=.65
pixels[:,:3]=np.clip(pixels[:,:3],0,1)
copy.pixels.foreach_set(pixels.ravel())
copy.pack()
base.image=copy
for mm in list(face.data.materials):
 face.data.materials.clear();break
face.data.materials.append(skin)
bs=next((n for n in skin.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
assert bs is not None
bs.inputs['Metallic'].default_value=0.
if not bs.inputs['Roughness'].is_linked:
 bs.inputs['Roughness'].default_value=.79
if 'Subsurface Weight' in bs.inputs:
 bs.inputs['Subsurface Weight'].default_value=.025
# Quaternius head eyes were accidentally assigned the *skin* material in V045.
# Keep original eye geometry, but give it proper warm-white sclera.
sclera=bpy.data.materials.new('GENESIS_V049_WARM_SCLERA_PBR')
sclera.diffuse_color=(.72,.70,.64,1)
sclera.use_nodes=True
pbr=sclera.node_tree.nodes.get('Principled BSDF')
pbr.inputs['Base Color'].default_value=(.72,.70,.64,1)
pbr.inputs['Roughness'].default_value=.29
eyes.data.materials.clear();eyes.data.materials.append(sclera)
eyebrow=bpy.data.materials.new('GENESIS_V049_DARK_BROWN_EYEBROWS')
eyebrow.diffuse_color=(.065,.037,.025,1)
eyebrow.use_nodes=True
pbr=eyebrow.node_tree.nodes.get('Principled BSDF')
pbr.inputs['Base Color'].default_value=(.065,.037,.025,1)
pbr.inputs['Roughness'].default_value=.93
brows.data.materials.clear();brows.data.materials.append(eyebrow)
# Locate existing physical eye geometry. Place actual 3D iris on its own
# natural sclera instead of drawing cartoon pupils or a 2D image concept.
positions=[eyes.matrix_world@v.co for v in eyes.data.vertices]
eye_positions={}
for side in (-1,1):
 cloud=[v for v in positions if v.x*side>.006]
 assert len(cloud)>50
 xs=sorted(v.x for v in cloud);ys=sorted(v.y for v in cloud);zs=sorted(v.z for v in cloud)
 eye_positions[str(side)]=(float(xs[len(xs)//2]),float(ys[0]-.006),float(zs[len(zs)//2]))
print('V049_REAL_EYE_POSITIONS',eye_positions,flush=True)

iris_mat=bpy.data.materials.new('GENESIS_V049_HAZEL_IRIS')
iris_mat.use_nodes=True
pn=iris_mat.node_tree.nodes.get('Principled BSDF')
pn.inputs['Base Color'].default_value=(.19,.125,.07,1)
pn.inputs['Roughness'].default_value=.22
pupil_mat=bpy.data.materials.new('GENESIS_V049_BLACK_PUPIL')
pupil_mat.use_nodes=True
pupil_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.008,.007,.006,1)
glint_mat=bpy.data.materials.new('GENESIS_V049_EYE_GLINT')
glint_mat.use_nodes=True
glint_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.72,.75,.77,1)
added=[]
for side in (-1,1):
 center=Vector(eye_positions[str(side)])
 for name,radius,depth,material,delta in (
  ('iris',.0125,.0030,iris_mat,0),
  ('pupil',.0060,.0022,pupil_mat,-.004),
  ('catchlight',.0023,.0011,glint_mat,-.007)):
  c=center.copy();c.y+=delta
  if name=='catchlight':c.x-=.003;c.z+=.003
  bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=c)
  o=bpy.context.object;o.name=f'GENESIS_V049_REAL_{name.upper()}_{"L" if side==1 else "R"}'
  o.scale=(radius,depth,radius)
  o.data.materials.clear();o.data.materials.append(material)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  w=o.matrix_world.copy()
  o.parent=arm;o.matrix_world=w
  grp=o.vertex_groups.new(name='Head');grp.add(list(range(len(o.data.vertices))),1,'REPLACE')
  mod=o.modifiers.new('GENESIS_V049_HEAD_SKIN','ARMATURE');mod.object=arm
  added.append(o)
# All 65 ORIGINAL bones and original outfit are untouched.
assert len(arm.data.bones)==65
outpath=a.out/'GENESIS_QUATERNIUS_RANGER_HUMAN_EYES_MATTE_SKIN_V049.glb'
bpy.ops.object.select_all(action='DESELECT')
for o in meshes+added+[arm]:o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(outpath.resolve()),export_format='GLB',
 use_selection=True,export_animations=False)
assert outpath.stat().st_size>2000000
headpos=arm.matrix_world@arm.data.bones['Head'].head_local
pelvis=arm.matrix_world@arm.data.bones['pelvis'].head_local
middle=(headpos+pelvis)*.5
scene=bpy.context.scene
world=bpy.data.worlds.new('GENESIS_V049_REAL_EXR_32BIT')
scene.world=world;world.use_nodes=True
nd=world.node_tree.nodes;nd.clear();links=world.node_tree.links
env=nd.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(a.hdri.resolve()))
assert env.image.depth>=96
bg=nd.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.70
ow=nd.new('ShaderNodeOutputWorld')
links.new(env.outputs['Color'],bg.inputs['Color'])
links.new(bg.outputs['Background'],ow.inputs['Surface'])
def aim(o,t):o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,t,offset,energy,size):
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d)
 scene.collection.objects.link(o);o.location=t+Vector(offset)
 aim(o,t);d.energy=energy;d.shape='DISK';d.size=size
area('MAIN',middle,(-2,-2.3,2.4),500,2.8)
area('RIM',middle,(2.0,1.7,1.6),280,2.6)
area('HOOD_FILL',headpos,(0,-.9,.12),120,.9)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32
scene.render.resolution_x=700;scene.render.resolution_y=850
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.19
recs=[]
for label,dir,pt,scale in [
 ('V049_01_FACE_MATTE_ADULT_FRONT',(.08,-1,.10),headpos,.78),
 ('V049_02_FACE_MATTE_ADULT_THREEQUARTER',(.70,-1,.10),headpos,.81),
 ('V049_03_FULL_RANGER_HUMAN_EYES',(.18,-1,.14),middle,3.26)]:
 data=bpy.data.cameras.new(label+'_lens');cam=bpy.data.objects.new(label+'_cam',data)
 scene.collection.objects.link(cam);cam.location=pt+Vector(dir).normalized()*4
 aim(cam,pt);data.type='ORTHO';data.ortho_scale=scale;scene.camera=cam
 f=a.out/(label+'.png');scene.render.filepath=str(f.resolve())
 bpy.ops.render.render(write_still=True)
 assert f.stat().st_size>45000
 recs.append(f.name)
qa={'status':'V049_GENUINE_RANGER_EYES_SKIN_PBR_EXPERIMENTAL_NOT_APPROVED',
 'source_v045b_sha256':hashlib.sha256(raw).hexdigest(),
 'output_glb_sha256':hashlib.sha256(outpath.read_bytes()).hexdigest(),
 'real_ranger_65_bones':len(arm.data.bones),
 'eye_positions':eye_positions,
 'existing_face_geometry_modified':False,
 'existing_eyes_material_corrected':True,
 'existing_eyebrows_material_corrected':True,
 'native_CC0_PBR_skin_texture_recolored':True,
 'PBR_skin_original_normal_maps_preserved':True,
 'native_3D_irises_pupils_added':len(added),
 'artwork_based_on_original_ranger':True,
 'HDRI':a.hdri.name,'HDRI_bits':env.image.depth,
 'renderer':'CYCLES','renders':recs,
 'animations_tested':False,'PlayCanvas_tested':False,
 'user_approved':False,'main_modified':False}
(a.out/'V049_REAL_HUMAN_EYES_SKIN_QA.json').write_text(json.dumps(qa,indent=2))
print('GENESIS_V049_GENUINE_CC0_RANGER_WARM_SKIN_BROWN_EYES_DONE_UNAPPROVED',json.dumps({'assets':recs,'eyes':eye_positions,'glb_bytes':outpath.stat().st_size}),flush=True)
