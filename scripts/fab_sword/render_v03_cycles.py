#!/usr/bin/env python3
"""Project Genesis — real Blender Cycles render of the supplied V03 GLB.

Uses the exact GLB from the user's existing V175 color pass. No AI images,
no geometry replacement, no procedural substitute for the existing materials.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector, Matrix


EXPECTED_SHA256 = "e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b"


def world_bounds(mesh_objects):
    pts = [ob.matrix_world @ Vector(v) for ob in mesh_objects for v in ob.bound_box]
    return (Vector([min(p[i] for p in pts) for i in range(3)]),
            Vector([max(p[i] for p in pts) for i in range(3)]))


def aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def area(name, loc, power, size, target, shape="DISK", size_y=None):
    bpy.ops.object.light_add(type="AREA", location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.energy = power
    ob.data.shape = shape
    ob.data.size = size
    if shape == "RECTANGLE" and size_y:
        ob.data.size_y = size_y
    aim(ob, target)


def make_ground():
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.017))
    floor = bpy.context.object
    floor.name = "GENESIS_STUDIO_FLOOR"
    mat = bpy.data.materials.new("Studio graphite / not part of asset")
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (0.095, 0.095, 0.099, 1.0)
    principled.inputs["Metallic"].default_value = 0
    principled.inputs["Roughness"].default_value = 0.84
    floor.data.materials.append(mat)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--samples", type=int, default=80)
    args = p.parse_args()
    source = args.input.resolve()
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError("V03 GLB does not match exact source SHA256: " + sha)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert mesh_objects, "No imported sword mesh"
    triangles = sum(len(o.data.loop_triangles) for o in mesh_objects)
    assert triangles == 2150, "The source was modified or imported unexpectedly"
    material_names = sorted({m.name for ob in mesh_objects for m in ob.data.materials if m})
    assert any("Iron_Blade" in s for s in material_names), material_names
    # Blender imports glTF with the source transformed into Z-up coordinates.
    low, high = world_bounds(mesh_objects)
    dimensions = high - low
    long_axis = dimensions[:].index(max(dimensions))
    axis = Vector(tuple(1 if i == long_axis else 0 for i in range(3)))
    intended = Vector((0.78, 0.63, 0.0)).normalized()
    rotate = axis.rotation_difference(intended).to_matrix().to_4x4()
    center = (low + high) / 2.0
    bpy.ops.object.empty_add(location=(0, 0, 0))
    parent = bpy.context.object
    parent.name = "Studio positioning only — not exported"
    # Parent using world-preserving transform, then orient entire sword.
    for ob in mesh_objects:
        matrix = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_world = matrix
    parent.matrix_world = rotate @ Matrix.Translation(-center)
    # Bring the sword low to the tabletop without changing any local mesh coordinates.
    low, high = world_bounds(mesh_objects)
    parent.location.z += -low.z + 0.005
    low, high = world_bounds(mesh_objects)
    center = (low + high) / 2.0
    target = Vector((center.x, center.y, (low.z + high.z)*0.5))
    span = max(high.x-low.x, high.y-low.y)
    make_ground()
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = max(16,min(args.samples,256))
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.context.view_layer.cycles.use_denoising = True
    # Broad area lights create clear metallic highlights while respecting V175 roughness.
    area("Large softbox left",(-1.3,-1.1,2.9),680,3.0,target)
    area("Rim strip", (1.2,1.6,2.2),550,2.5,target,shape="RECTANGLE",size_y=0.75)
    area("Soft ambient fill",(-1.4,1.2,1.7),250,2.8,target)
    world=bpy.data.worlds.new("Studio World 0.28") if scene.world is None else scene.world
    scene.world=world
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.28,0.29,0.31,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.35
    bpy.ops.object.camera_add(location=(2.25,-2.7,2.8))
    camera=bpy.context.object
    camera.name="Cycles hero camera"
    aim(camera, target)
    camera.data.type="ORTHO"
    camera.data.ortho_scale=max(2.3, span*1.45)
    scene.camera=camera
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(args.output.resolve())
    bpy.ops.render.render(write_still=True)
    assert args.output.exists() and args.output.stat().st_size > 10000
    report={"engine":"BLENDER_CYCLES","source_sha256":sha,"blender":bpy.app.version_string,
            "cycles_device":"CPU","cycles_samples":scene.cycles.samples,
            "triangles":triangles,"materials":material_names,"mesh_geometry_changed":False,
            "render_file":args.output.name,"render_bytes":args.output.stat().st_size,
            "image_gen_used":False,"visual_approval":False}
    args.report.write_text(json.dumps(report,indent=2),encoding="utf8")
    print("GENESIS_REAL_CYCLES_RENDER:", json.dumps(report))


if __name__=="__main__":
    main()
