"""Audit a licensed local Fab sword GLB with Blender 4.5 LTS.

Blender invocation:
    blender -b --factory-startup --python blender_inspect.py -- \\
        --input /secure/free_medieval_sword.glb --report /tmp/sword_audit.json

This script does not change or export the source asset.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def args_after_dash():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def connected_face_components(mesh):
    """Components connected through shared *vertex indices* (not UV islands)."""
    by_vertex = [[] for _ in mesh.vertices]
    for poly in mesh.polygons:
        for vid in poly.vertices:
            by_vertex[vid].append(poly.index)
    seen = set()
    out = []
    for poly in mesh.polygons:
        if poly.index in seen:
            continue
        stack = [poly.index]
        seen.add(poly.index)
        part = []
        while stack:
            fid = stack.pop()
            part.append(fid)
            for vid in mesh.polygons[fid].vertices:
                for other in by_vertex[vid]:
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
        out.append(part)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    ns = parser.parse_args(args_after_dash())
    source = Path(ns.input).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".glb":
        raise ValueError("A locally available .glb source is required")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))

    report = {
        "source": source.name,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "blender": bpy.app.version_string,
        "objects": [],
    }
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        components = connected_face_components(mesh)
        comp_reports = []
        for comp in components:
            positions = [obj.matrix_world @ mesh.vertices[vid].co
                         for fid in comp for vid in mesh.polygons[fid].vertices]
            low = [min(v[axis] for v in positions) for axis in range(3)]
            high = [max(v[axis] for v in positions) for axis in range(3)]
            comp_reports.append({
                "triangles": sum(max(0, len(mesh.polygons[fid].vertices) - 2) for fid in comp),
                "polygons": len(comp),
                "bounds_min": [round(float(x), 6) for x in low],
                "bounds_max": [round(float(x), 6) for x in high],
                "blade_candidate": high[1] > 0.95 and max(abs(low[0]), abs(high[0])) < 0.09,
            })
        materials = []
        for mat in mesh.materials:
            if mat is None:
                continue
            images = []
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        images.append({"name": node.image.name, "size": list(node.image.size)})
            materials.append({"name": mat.name, "images": images})
        report["objects"].append({
            "name": obj.name,
            "vertices": len(mesh.vertices),
            "triangles": sum(max(0, len(p.vertices) - 2) for p in mesh.polygons),
            "component_count": len(components),
            "components": comp_reports,
            "materials": materials,
        })
    output = Path(ns.report).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("[GENESIS] Sword audit saved:", output)
    print("[GENESIS] Original GLB unchanged:", source)


if __name__ == "__main__":
    main()
