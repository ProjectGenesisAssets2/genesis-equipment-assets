"""Project Genesis — original provisional iron sword for PlayCanvas QA.
Original mesh generated here. NOT the Fab sword. One silhouette for all rarities.
Units metres, Z-up; Blender exports glTF Y-up. No rarity-based geometry variation.
"""
import bpy, math, json, pathlib, hashlib
from mathutils import Vector

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"playcanvas"/"swords"/"provisional_v001"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mat(name,rgba,metal,rough):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgba,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*rgba,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    return m
blade=mat("Genesis_Provisional_HandForged_Iron",(0.37,0.405,0.43),0.88,0.4)
edge=mat("Genesis_Provisional_Iron_Edge",(0.51,0.54,0.55),0.9,0.28)
hilt=mat("Genesis_Provisional_Dark_Iron",(0.16,0.155,0.15),0.78,0.46)
leather=mat("Genesis_Provisional_Brown_Leather",(0.18,0.105,0.055),0.0,0.88)
brass=mat("Genesis_Provisional_Subdued_Brass",(0.33,0.23,0.115),0.76,0.42)

def finish(obj,name,material,bevel=0):
    obj.name=name;obj.data.materials.append(material)
    if bevel:
        mod=obj.modifiers.new("Soft forged edges","BEVEL")
        mod.width=bevel;mod.segments=2
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return obj
def box(name,loc,scale,material,bevel):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object;obj.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(obj,name,material,bevel)
def cylinder(name,loc,radius,depth,material,vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc)
    return finish(bpy.context.object,name,material,0.004)

# Fixed blade geometry, broad double-sided faces, crisp edges and tapered spear tip.
# Blade begins at z=0.14 and ends z=1.13. Diamond section around x=0.
rings=[
 (0.14,0.052,0.009),
 (0.24,0.061,0.011),
 (0.45,0.058,0.010),
 (0.83,0.042,0.007),
 (1.08,0.019,0.003),
 (1.14,0.0005,0.0005),
]
verts=[]
for z,half,thick in rings:
    verts.extend([(-half,0,z),(0,-thick,z),(half,0,z),(0,thick,z)])
faces=[]
for i in range(len(rings)-1):
    for side in range(4):
        a=4*i+side;b=4*i+(side+1)%4;c=4*(i+1)+(side+1)%4;d=4*(i+1)+side
        faces.append((a,b,c,d))
faces.append(tuple(reversed(range(4))))
faces.append(tuple(range(4*(len(rings)-1),4*len(rings))))
mesh=bpy.data.meshes.new("Sword blade fixed silhouette");mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new("Genesis_Sword_Blade_Provisional",mesh);bpy.context.collection.objects.link(obj)
obj.data.materials.append(blade);obj.data.materials.append(edge)
for poly in obj.data.polygons:
    if poly.index < 4*(len(rings)-1) and poly.index%4 in (0,1):poly.material_index=0
    else:poly.material_index=1

# Subdued working guard and handle; no decorative rarity additions.
box("Genesis_Guard_Main",(0,0,0.113),(0.29,0.037,0.039),hilt,0.011)
for x in (-0.135,0.135):
    box("Genesis_Guard_End",(x,0,0.114),(0.036,0.044,0.048),hilt,0.008)
cylinder("Genesis_Grip_Core",(0,0,-0.065),0.024,0.31,leather,20)
for i in range(8):
    z=-0.197+i*0.036
    cylinder("Genesis_Grip_Wrap_%02d"%i,(0,0,z),0.026,0.008,leather,20)
cylinder("Genesis_Grip_Collar_Top",(0,0,0.087),0.032,0.025,brass,20)
cylinder("Genesis_Grip_Collar_Bottom",(0,0,-0.22),0.031,0.025,hilt,20)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=1,location=(0,0,-0.25))
pom=bpy.context.object;pom.scale=(0.045,0.031,0.05)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
finish(pom,"Genesis_Pommel",hilt)

scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE_NEXT"
# Export only sword mesh objects (not cameras, no animations, textures external).
for o in bpy.context.selected_objects:o.select_set(False)
objects=[o for o in scene.objects if o.type=="MESH"]
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
target=OUT/"genesis_sword_provisional_v001.glb"
bpy.ops.export_scene.gltf(filepath=str(target),export_format="GLB",use_selection=True,export_yup=True,export_apply=True)
raw=target.read_bytes()
assert raw[:4]==b'glTF', "Not a valid GLB container"
assert len(raw)>2500
audit={"model":"GENESIS_SWORD_PROVISIONAL_V001","origin":"original_geometry_generated_for_Project_Genesis","fab_asset_used":False,
"purpose":"temporary visual only, same sword for all item rarity",
"source":"scripts/create_provisional_sword.py","materials":[m.name for m in (blade,edge,hilt,leather,brass)],
"mesh_count":len(objects),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
"blade_present":any(o.name=="Genesis_Sword_Blade_Provisional" for o in objects)}
(OUT/"audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
print("GENESIS_PROVISIONAL_SWORD_READY",json.dumps(audit),flush=True)
