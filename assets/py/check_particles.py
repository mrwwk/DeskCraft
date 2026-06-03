"""check_particles.py - Check particle systems in Blender scene.

Outputs JSON with particle system info per object: type (EMITTER/HAIR), count, settings.

Usage:
    blender --background scene.blend --python check_particles.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

result = {}

for obj in bpy.data.objects:
    if not obj.particle_systems:
        continue

    particles = []
    for ps in obj.particle_systems:
        ps_info = {
            "name": ps.name,
            "type": ps.settings.type,
            "count": ps.settings.count,
            "lifetime": ps.settings.lifetime,
            "emit_from": ps.settings.emit_from,
        }

        if ps.settings.type == 'HAIR':
            ps_info["hair_length"] = round(ps.settings.hair_length, 4)
            ps_info["hair_step"] = ps.settings.hair_step

        elif ps.settings.type == 'EMITTER':
            ps_info["frame_start"] = ps.settings.frame_start
            ps_info["frame_end"] = ps.settings.frame_end
            ps_info["normal_factor"] = round(ps.settings.normal_factor, 4)

        # Render settings
        ps_info["render_type"] = ps.settings.render_type

        particles.append(ps_info)

    result[obj.name] = particles

print(f"RESULT:{json.dumps(result)}")
