#!/usr/bin/env python3
"""Same real original V03/V175/V12B sword, exact camera/PBR and studio;
compare 8-bit LDR vs 32-bit/channel EXR environment only (not historical render)."""
import hashlib,json,sys,struct
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"fab_sword"))
import render_v12_v175_j_roughness as v12
# v12.main authentic pipeline: hash-checks GLB/EXR, configures actual sword
# and renders the V12B roughness .34 hero view with 32-bpc HDRI.
argv=sys.argv[sys.argv.index('--')+1:]
out=Path(argv[argv.index('--output-dir')+1])
ldr_path=Path(argv[argv.index('--ldr')+1])
# Run legacy V12 script with only its supported args. Wrapper-only --ldr
# is stripped temporarily so Blender's original argparse remains unchanged.
previous_argv=sys.argv[:]
i=sys.argv.index('--ldr')
del sys.argv[i:i+2]
v12.main()
sys.argv=previous_argv
b=ldr_path.read_bytes()
assert b[:8]==b'\x89PNG\r\n\x1a\n'
assert (b[24],b[25])==(8,2),f"Expected 8 bit RGB PNG, got {b[24:26]}"
ldr=bpy.data.images.load(str(ldr_path.resolve()),check_existing=False)
assert ldr.depth==24,(ldr.depth,ldr.size)
hdr=bpy.data.images.load(str(Path(argv[argv.index('--hdri')+1]).resolve()),check_existing=True)
assert hdr.depth==96,(hdr.depth,hdr.size)
assert tuple(ldr.size)==tuple(hdr.size),(ldr.size,hdr.size)
scene=bpy.context.scene
scene.camera=bpy.data.objects['CAM_hero']
assert scene.render.engine=='CYCLES'
world=scene.world
env=world.node_tree.nodes.get('STUDIO_SMALL_09_EXR_ORIGINAL')
assert env and env.type=='TEX_ENVIRONMENT'
assert env.image==hdr,(env.image,hdr)
render_hdr=out/'V12_V175_Color_J_Rugosidad034_Hero.png'
assert render_hdr.exists() and render_hdr.stat().st_size>100000
# Switch ONLY world environment source. Everything else is frozen.
before={
  'camera_location':list(scene.camera.location),
  'exposure':scene.view_settings.exposure,
  'world_strength':world.node_tree.nodes['HDRI_FOR_REFLECTIONS_AND_LIGHTING'].inputs['Strength'].default_value,
  'samples':scene.cycles.samples,
  'material_names':[m.name for ob in scene.objects if ob.type=='MESH' for m in ob.data.materials if m],
  'lights':[(o.name,o.data.energy) for o in scene.objects if o.type=='LIGHT'],
}
env.image=ldr
scene.render.filepath=str((out/'PG_Espada_V175_V12B_LDR8_Hero.png').resolve())
bpy.ops.render.render(write_still=True)
render_ldr=out/'PG_Espada_V175_V12B_LDR8_Hero.png'
assert render_ldr.exists() and render_ldr.stat().st_size>70000
# Restore exact HDRI before finishing (never save original source).
env.image=hdr
after={
  'camera_location':list(scene.camera.location),
  'exposure':scene.view_settings.exposure,
  'world_strength':world.node_tree.nodes['HDRI_FOR_REFLECTIONS_AND_LIGHTING'].inputs['Strength'].default_value,
  'samples':scene.cycles.samples,
  'material_names':[m.name for ob in scene.objects if ob.type=='MESH' for m in ob.data.materials if m],
  'lights':[(o.name,o.data.energy) for o in scene.objects if o.type=='LIGHT'],
}
assert before==after,('Inconsistent settings',before,after)
refs=json.loads((out/'render_audit.json').read_text())
surface=json.loads((out/'v12_surface_audit.json').read_text())
assert refs['source_sha256']==v12.EXPECTED_GLB
assert refs['hdri_sha256']==v12.EXPECTED_HDR
assert refs['geometry_triangles']==2150
assert surface['V10_color_socket_unchanged']
def report_file(p):
  data=p.read_bytes()
  assert data[:8]==b'\x89PNG\r\n\x1a\n'
  assert tuple(struct.unpack_from('>II',data,16))==(1200,1500)
  return {'name':p.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
manifest={
'asset':'Project Genesis genuine iron sword V03 V175 V12B',
'comparison':'New 8-bit LDR adaptation and original 32-bit HDRI under frozen original V12B look',
'do_not_claim_historical_pair':True,
'original_glb_sha256':refs['source_sha256'],'source_triangles':refs['geometry_triangles'],
'blender':bpy.app.version_string,'renderer':'Cycles','samples':scene.cycles.samples,
'exposure':scene.view_settings.exposure,'look':scene.view_settings.look,
'original_hdr_image_sha256':refs['hdri_sha256'],'original_hdr_bits_per_channel':32,
'derived_ldr_image_sha256':hashlib.sha256(b).hexdigest(),
'derived_ldr_bits_per_channel':8,
'derived_ldr_creation':'ffmpeg OpenEXR 32-bit image to 8-bit RGB PNG at full 4096x2048, clips extended range',
'only_change_between_views':'Environment texture source: LDR PNG vs EXR float32',
'softbox_lights_unchanged':True,'materials_unchanged_between_views':True,
'camera_unchanged_between_views':True,
'images':[report_file(render_ldr),report_file(render_hdr)]
}
(out/'PG_Anuario_LDR8_HDRI32_Compare_Audit.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print('PG_GENUINE_V175_V12B_8_VS_32_RENDER_SUCCESS',json.dumps(manifest),flush=True)
