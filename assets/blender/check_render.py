"""check_render.py - Check render settings in Blender scene.

Outputs JSON with render engine, resolution, frame rate, samples, output format, etc.

Usage:
    blender --background scene.blend --python check_render.py 2>/dev/null | grep '^RESULT:'
"""
import bpy
import json

scene = bpy.context.scene
result = {
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "fps": scene.render.fps,
    "fps_base": scene.render.fps_base,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "frame_current": scene.frame_current,
    "film_transparent": scene.render.film_transparent,
    "image_format": scene.render.image_settings.file_format,
    "color_mode": scene.render.image_settings.color_mode,
    "output_path": scene.render.filepath,
}

# Engine-specific settings
if scene.render.engine == 'CYCLES':
    result["samples"] = scene.cycles.samples
    result["preview_samples"] = scene.cycles.preview_samples
    result["use_denoising"] = scene.cycles.use_denoising
    result["device"] = scene.cycles.device
elif scene.render.engine == 'BLENDER_EEVEE_NEXT':
    result["samples"] = scene.eevee.taa_render_samples
    result["preview_samples"] = scene.eevee.taa_samples
elif scene.render.engine == 'BLENDER_EEVEE':
    result["samples"] = scene.eevee.taa_render_samples if hasattr(scene.eevee, 'taa_render_samples') else None

# Video output settings
if scene.render.image_settings.file_format == 'FFMPEG':
    result["ffmpeg_format"] = scene.render.ffmpeg.format
    result["ffmpeg_codec"] = scene.render.ffmpeg.codec

# Active camera
if scene.camera:
    result["active_camera"] = scene.camera.name
    result["camera_location"] = [round(v, 4) for v in scene.camera.location]
else:
    result["active_camera"] = None

print(f"RESULT:{json.dumps(result)}")
