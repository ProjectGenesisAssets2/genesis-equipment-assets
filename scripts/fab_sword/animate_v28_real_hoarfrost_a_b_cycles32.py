#!/usr/bin/env python3
"""Project Genesis V28 - genuine animated 3D hoarfrost A/B on approved V03/V175/V12B.
Real Cycles with original RGB 32 bits/channel HDRI; original sword unchanged.
Convert only the existing V28 frost geometry into 12 progressive animated mesh sectors.
Export separate *animated* GLB overlays and editable .blend; create actual Cycles frames.
Do not change approved fire, lightning, sword mesh, or master materials.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from bisect import bisect_right
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v12_v175_j_roughness as v12
import render_v18_v12b_fuego_v06_flow_cycles as studio
import render_v25_hielo_cycles_hdri32 as ice25
import render_v28_two_actual_frost_3d as frost28

HASH_GLB = frost28.SOURCE_SHA
HASH_EXR = frost28.HDRI_SHA
PREFIX = frost28.TAG

def require(test, reason):
    if not test:
        raise RuntimeError("GENESIS_V28_ANIMATION_FAILED " + reason)

def start_studio(args):
    require(hashlib.sha256(args.input.read_bytes()).hexdigest() == HASH_GLB, "V03 GLB checksum")
    require(hashlib.sha256(args.hdri.read_bytes()).hexdigest() == HASH_EXR, "real EXR checksum")
    preset = json.loads(args.preset.read_text(encoding="utf-8"))
    require(preset.get("id") == "Genesis_Espada_V03_Hierro_V175_V12B", "wrong preset")
    require(preset.get("visual_status") == "approved_by_user", "base sword not approved")
    saved = list(sys.argv)
    try:
        sys.argv = ["blender", "--", "--input", str(args.input), "--hdri", str(args.hdri),
                    "--output-dir", str(args.output_dir), "--samples", str(args.setup_samples)]
        v12.main()
    finally:
        sys.argv = saved
    scene = bpy.context.scene
    require(scene.render.engine == "CYCLES", "Cycles inactive")
    image = next((im for im in bpy.data.images if im.filepath and
                  Path(bpy.path.abspath(im.filepath)).name == args.hdri.name), None)
    require(image is not None and image.depth == 96 and tuple(image.size) == (4096, 2048),
            "HDRI is not REAL 32-bit RGB 4K")
    iron = next((m for m in bpy.data.materials if "Iron_Blade_V175" in m.name), None)
    require(iron is not None, "V175 blade iron not found")
    rough = iron.node_tree.nodes.get("V11_J_V175_ROUGHNESS_MULT_049")
    oxide = iron.node_tree.nodes.get("V12_J_OXIDE_LOCAL_ROUGHNESS")
    require(rough is not None and oxide is not None, "V12B iron shader absent")
    require(abs(rough.inputs[1].default_value - .34) < 1e-5 and
            abs(oxide.inputs[1].default_value - .10) < 1e-5, "approved gloss altered")
    original = {o.name:(len(o.data.vertices), len(o.data.polygons))
                for o in bpy.data.objects if o.type == "MESH"}
    src = studio.collect_blade()
    coord, along, side, normal = ice25.setup_frame(src)
    return scene, original, src, coord, along, side, normal, iron

def segment_effects(source, slices, variant, intensity):
    """Assign actual mesh polygons to blade-length sectors without inventing a 2D effect.
    At 100% all resulting polygons exactly reproduce V28's native 3D geometry.
    """
    origin, along = Vector(source[0]), Vector(source[1])
    denom = along.length_squared
    require(denom > 1e-5, "invalid sword blade axis")
    objects = [o for o in bpy.data.objects if o.name.startswith(PREFIX) and
               o.type in ("MESH", "CURVE")]
    require(len(objects) >= 10, "V28 A/B frost objects missing")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.convert(target="MESH")
    converted = [o for o in bpy.context.selected_objects if o.name.startswith(PREFIX)]
    require(len(converted) >= 10 and all(o.type == "MESH" for o in converted),
            "V28 curve-to-mesh conversion failed")
    buckets = [
        {"verts": [], "faces": [], "mats": [], "mat_lookup": {}, "mids": [], "smooth": []}
        for _ in range(slices)
    ]
    # Balanced *physical* length sections: the original blade-space t values are
    # not uniformly distributed in [0,1], so use exact projected polygon quantiles.
    # This preserves every original face and produces actual populated growth bands.
    projections = []
    for obj in converted:
        world = [obj.matrix_world @ v.co for v in obj.data.vertices]
        for poly in obj.data.polygons:
            centre = sum((world[i] for i in poly.vertices), Vector()) / len(poly.vertices)
            projections.append((centre - origin).dot(along) / denom)
    ordered = sorted(projections)
    require(len(ordered) > 100, "empty V28 procedural frost geometry")
    cutoffs = [ordered[(i * len(ordered)) // slices] for i in range(1, slices)]
    require(cutoffs[0] < cutoffs[-1], "frost has no lengthwise spread")
    print("GENESIS_V28_ACTUAL_FROST_BLADE_PROJECTION", variant,
          {"minimum": ordered[0], "maximum": ordered[-1], "cuts": cutoffs}, flush=True)
    original_face_count = 0
    for obj in converted:
        verts_world = [obj.matrix_world @ vert.co for vert in obj.data.vertices]
        indices = [dict() for _ in range(slices)]
        slots = [slot.material for slot in obj.material_slots]
        require(bool(slots) and all(m is not None for m in slots),
                "missing frost material " + obj.name)
        for poly in obj.data.polygons:
            original_face_count += 1
            centroid = sum((verts_world[i] for i in poly.vertices), Vector()) / len(poly.vertices)
            relative = (centroid - origin).dot(along) / denom
            idx = bisect_right(cutoffs, relative)
            block = buckets[idx]
            local_to_global = indices[idx]
            face = []
            for vertex_idx in poly.vertices:
                if vertex_idx not in local_to_global:
                    local_to_global[vertex_idx] = len(block["verts"])
                    block["verts"].append(verts_world[vertex_idx].copy())
                face.append(local_to_global[vertex_idx])
            mat = slots[poly.material_index]
            if mat.name not in block["mat_lookup"]:
                block["mat_lookup"][mat.name] = len(block["mats"])
                block["mats"].append(mat)
            block["faces"].append(tuple(face))
            block["mids"].append(block["mat_lookup"][mat.name])
            block["smooth"].append(poly.use_smooth)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in converted:
        obj.select_set(True)
    bpy.ops.object.delete(use_global=False)
    require(sum(len(b["faces"]) for b in buckets) == original_face_count,
            "V28 polygon loss during segmentation")
    segments = []
    total_faces = 0
    for i, bucket in enumerate(buckets):
        if not bucket["faces"]:
            continue
        centre = sum(bucket["verts"], Vector()) / len(bucket["verts"])
        mesh = bpy.data.meshes.new(PREFIX + variant + "_Sector_" + str(i) + "_Mesh")
        mesh.from_pydata([tuple(v - centre) for v in bucket["verts"]], [],
                         bucket["faces"])
        mesh.update()
        for material in bucket["mats"]:
            mesh.materials.append(material)
        for polygon, index, smooth in zip(mesh.polygons, bucket["mids"], bucket["smooth"]):
            polygon.material_index = index
            polygon.use_smooth = smooth
        obj = bpy.data.objects.new(PREFIX + variant + "_AnimatedSector_" + str(i).zfill(2), mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = centre
        # One physically progressive freezing front from hilt towards point,
        # then natural thaw and loop, with short overlapping growth windows.
        start = 2.0 + i * 1.10
        fully_grown = start + 5.0
        thaw = 29.0 + (slices - 1 - i) * .80
        gone = min(47.0, thaw + 6.5)
        amp = intensity / 100.0
        keys = [(1.0, .003), (start, .003), (fully_grown, amp),
                (thaw, amp), (gone, .003), (48.0, .003)]
        for frame, scalar in keys:
            obj.scale = (scalar, scalar, scalar)
            obj.keyframe_insert(data_path="scale", frame=frame, group="GENESIS_V28_FROST_GROWTH")
        segments.append(obj)
        total_faces += len(mesh.polygons)
    require(len(segments) >= 10, "insufficient populated growth sectors")
    require(total_faces == original_face_count, "segmentation topology mismatch")
    return segments, {"sectors": len(segments),
                      "original_v28_polygons": original_face_count,
                      "animated_polygons": total_faces,
                      "intensity_0_to_100": intensity,
                      "geometric_not_postprocessed": True}

def export_animated_overlay(scene, objects, path):
    scene.frame_start = 1
    scene.frame_end = 48
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB",
                              use_selection=True, export_animations=True,
                              export_frame_range=True, export_force_sampling=True)
    data = path.read_bytes()
    require(data[:4] == b"glTF" and struct.unpack_from("<I", data, 8)[0] == len(data),
            "animated GLB header invalid")
    n, kind = struct.unpack_from("<I4s", data, 12)
    require(kind == b"JSON", "missing GLB JSON chunk")
    gltf = json.loads(data[20:20 + n])
    animations = gltf.get("animations", [])
    require(len(animations) >= 1 and sum(len(a.get("channels", [])) for a in animations) >= 10,
            "GLB does not actually contain growth animation channels")
    require(len(gltf.get("meshes", [])) >= 10, "GLB frost meshes absent")
    bpy.ops.object.select_all(action="DESELECT")
    return {"name": path.name, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "animation_count": len(animations),
            "animation_channels": sum(len(a.get("channels", [])) for a in animations),
            "meshes": len(gltf["meshes"]), "actual_GLTF_keyframe_animation": True}

def render_variant(scene, args, variant, objects, result_dir):
    scene.frame_start = 1
    scene.frame_end = 48
    scene.render.fps = 24
    scene.render.engine = "CYCLES"
    scene.cycles.samples = args.samples
    scene.render.resolution_percentage = args.resolution_pct
    scene.camera = bpy.data.objects["CAM_hero"]
    scene.render.image_settings.file_format = "PNG"
    bpy.context.view_layer.cycles.use_denoising = True
    frames_dir = result_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    for frame in range(1, 49):
        scene.frame_set(frame)
        out = frames_dir / ("frame_%03d.png" % (frame - 1))
        scene.render.filepath = str(out.absolute())
        bpy.ops.render.render(write_still=True)
        require(out.exists() and out.stat().st_size > 18000,
                "missing actual Cycles frame " + str(frame))
        if frame in (1, 8, 16, 24, 36, 48):
            samples.append({"frame": frame, "file": out.name,
                            "bytes": out.stat().st_size,
                            "sha256": hashlib.sha256(out.read_bytes()).hexdigest()})
        print("GENESIS_V28_REAL_CYCLES_FRAME", variant, frame, "/48",
              out.stat().st_size, flush=True)
    require(samples[0]["sha256"] != samples[3]["sha256"],
            "animation did not visibly change from unfrozen to frozen")
    require(samples[3]["sha256"] != samples[-1]["sha256"],
            "animation did not thaw")
    # High-quality true 3D macro still at fully crystallized frame.
    scene.frame_set(24)
    scene.camera = bpy.data.objects["CAM_BLADE_MACRO"]
    scene.render.resolution_percentage = 100
    scene.cycles.samples = args.hero_samples
    macro = result_dir / ("V28_Escarcha_" + variant + "_Cycles32_Macro.png")
    scene.render.filepath = str(macro.absolute())
    bpy.ops.render.render(write_still=True)
    require(macro.exists() and macro.stat().st_size > 100000,
            "missing Cycles macro confirmation")
    scene.camera = bpy.data.objects["CAM_hero"]
    scene.render.resolution_percentage = args.resolution_pct
    scene.cycles.samples = args.samples
    return {"actual_cycles_frames": 48, "fps": 24, "duration_seconds": 2.0,
            "samples_per_frame": args.samples, "resolution_pct": args.resolution_pct,
            "keyframe_samples": samples, "macro": macro.name,
            "morph": "12 mesh sectors grow hilt-to-tip, hold, thaw tip-to-hilt"}

def validate_original(original, iron):
    after = {o.name:(len(o.data.vertices), len(o.data.polygons))
             for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith(PREFIX)}
    require(after == original, "approved V03 base geometry changed")
    rough = iron.node_tree.nodes.get("V11_J_V175_ROUGHNESS_MULT_049")
    oxide = iron.node_tree.nodes.get("V12_J_OXIDE_LOCAL_ROUGHNESS")
    require(abs(rough.inputs[1].default_value - .34) < 1e-5 and
            abs(oxide.inputs[1].default_value - .10) < 1e-5, "V175/V12B changed")

def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "hdri", "preset", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--samples", type=int, default=18)
    parser.add_argument("--setup-samples", type=int, default=12)
    parser.add_argument("--hero-samples", type=int, default=64)
    parser.add_argument("--resolution-pct", type=int, default=58)
    parser.add_argument("--intensity", type=int, default=100)
    parser.add_argument("--variant", choices=("A", "B", "both"), default="both")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    require(0 <= args.intensity <= 100, "intensity must be 0-100")
    require(12 <= args.samples <= 128 and 40 <= args.resolution_pct <= 100,
            "invalid render quality")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene, original, source, coord, along, side, normal, iron = start_studio(args)
    results = []
    variants = ("A", "B") if args.variant == "both" else (args.variant,)
    for variant in variants:
        v28_details = frost28.build_frost(variant, coord, along, side, normal)
        segments, geometry = segment_effects(source, 12, variant, args.intensity)
        validate_original(original, iron)
        out = args.output_dir / variant
        out.mkdir(parents=True, exist_ok=True)
        scene.frame_start = 1
        scene.frame_end = 48
        scene.frame_set(24)
        # Editable Blender file is saved separately; never overwrite the approved master.
        bpy.ops.file.pack_all()
        scene_path = out / ("V28_Escarcha_" + variant + "_Animada_Cycles32.blend")
        bpy.ops.wm.save_as_mainfile(filepath=str(scene_path), compress=True)
        require(scene_path.stat().st_size > 1000000, "animated BLEND not saved")
        glb = export_animated_overlay(scene, segments,
                                      out / ("V28_Escarcha_" + variant + "_AnimatedOverlay.glb"))
        qa = render_variant(scene, args, variant, segments, out)
        validate_original(original, iron)
        results.append({"variant": variant, "source_V28": v28_details, "geometry": geometry,
                        "animated_glb": glb, "editable_scene": scene_path.name,
                        "render": qa, "approved": False, "playcanvas_tested": False})
        for obj in list(bpy.data.objects):
            if obj.name.startswith(PREFIX):
                bpy.data.objects.remove(obj, do_unlink=True)
        print("GENESIS_V28_ANIMATED_VARIANT_COMPLETE", variant, glb["animation_channels"], flush=True)
    audit = {"schema": "Genesis_V28_RealHoarfrost_A_B_24fps_Cycles_AnimatedGLB",
             "status": "experimental_animated_not_yet_user_approved",
             "original_V03_GLB_SHA256": HASH_GLB,
             "original_studio_EXR_SHA256": HASH_EXR,
             "RGB_HDRI_bits_per_channel": 32,
             "HDRI_resolution": [4096, 2048],
             "Blender": bpy.app.version_string, "renderer": "Cycles",
             "approved_preset": "Genesis_Espada_V03_Hierro_V175_V12B",
             "source_3D_not_imagegen": True, "approved_sword_unchanged": True,
             "fire_and_lightning_untouched": True, "in_main": False,
             "variants": results}
    (args.output_dir / "v28_animated_real_hoarfrost_a_b_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print("GENESIS_V28_BOTH_REAL_ANIMATED_CYCLES_GLBS_COMPLETED", len(results), flush=True)

if __name__ == "__main__":
    main()
