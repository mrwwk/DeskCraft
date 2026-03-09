#!/usr/bin/env python3
"""
Kdenlive Test Asset Generator

Generates test media files and pre-configured .kdenlive project files
for use in OSWorld Kdenlive L1 evaluation tasks.

Requirements:
- FFmpeg (for generating test video)
- Python 3.6+ (for xml.etree.ElementTree)

Usage:
    python3 generate_test_assets.py

Output:
    assets/sample_video.mp4           - 10-second 1080p 30fps test video with audio
    assets/project_with_clip.kdenlive  - Project with clip in bin only (for task 2)
    assets/project_with_timeline.kdenlive - Project with clip on timeline (for tasks 3, 4, 5)
"""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ============================================================================
# Configuration
# ============================================================================

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
VIDEO_FILENAME = "sample_video.mp4"
VIDEO_PATH_ON_VM = "/home/user/Desktop/sample_video.mp4"

# Video properties
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_DURATION = 10  # seconds
VIDEO_TOTAL_FRAMES = VIDEO_FPS * VIDEO_DURATION


# ============================================================================
# Helper: Pretty-print XML
# ============================================================================

def prettify_xml(element):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(element, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


# ============================================================================
# Generate Test Video with FFmpeg
# ============================================================================

def generate_test_video():
    """
    Generate a 10-second 1080p 30fps test video with:
    - Color bars + moving text overlay (visually distinctive)
    - Sine wave audio tone (440Hz, for audio volume testing)
    """
    output_path = os.path.join(ASSETS_DIR, VIDEO_FILENAME)

    if os.path.exists(output_path):
        print(f"  [SKIP] {output_path} already exists")
        return output_path

    print(f"  [GEN] Generating test video: {output_path}")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        # Video: SMPTE color bars with timestamp overlay
        "-f", "lavfi",
        "-i", f"smptebars=size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:rate={VIDEO_FPS}:duration={VIDEO_DURATION},"
              f"drawtext=text='Kdenlive Test %{{pts\\:hms}}':fontsize=48:fontcolor=white:"
              f"x=(w-text_w)/2:y=h-80:box=1:boxcolor=black@0.5",
        # Audio: 440Hz sine wave
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={VIDEO_DURATION}:sample_rate=48000",
        # Output settings
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]

    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"  [ERROR] FFmpeg failed: {result.stderr[:500]}")
            # Fallback: simpler command without text overlay
            print("  [RETRY] Trying simpler video generation...")
            ffmpeg_cmd_simple = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i",
                f"color=c=blue:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:rate={VIDEO_FPS}:duration={VIDEO_DURATION}",
                "-f", "lavfi", "-i",
                f"sine=frequency=440:duration={VIDEO_DURATION}:sample_rate=48000",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p", "-shortest",
                output_path
            ]
            result = subprocess.run(ffmpeg_cmd_simple, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  [ERROR] Fallback also failed: {result.stderr[:500]}")
                return None
        print(f"  [OK] Video generated: {output_path}")
        return output_path
    except FileNotFoundError:
        print("  [ERROR] FFmpeg not found. Please install FFmpeg.")
        return None
    except subprocess.TimeoutExpired:
        print("  [ERROR] FFmpeg timed out after 60 seconds")
        return None


# ============================================================================
# Generate .kdenlive Project Files (MLT XML)
# ============================================================================

def _create_base_mlt():
    """Create a base MLT XML root element with profile."""
    mlt = ET.Element("mlt")
    mlt.set("LC_NUMERIC", "C")
    mlt.set("producer", "main_bin")
    mlt.set("version", "7.1.0")
    mlt.set("root", "/home/user/Desktop")

    # Profile: 1080p 30fps
    profile = ET.SubElement(mlt, "profile")
    profile.set("description", "HD 1080p 30fps")
    profile.set("width", str(VIDEO_WIDTH))
    profile.set("height", str(VIDEO_HEIGHT))
    profile.set("progressive", "1")
    profile.set("sample_aspect_num", "1")
    profile.set("sample_aspect_den", "1")
    profile.set("display_aspect_num", "16")
    profile.set("display_aspect_den", "9")
    profile.set("frame_rate_num", str(VIDEO_FPS))
    profile.set("frame_rate_den", "1")
    profile.set("colorspace", "709")

    return mlt


def _add_video_producer(mlt, producer_id="producer0"):
    """Add a video producer referencing sample_video.mp4."""
    producer = ET.SubElement(mlt, "producer")
    producer.set("id", producer_id)
    producer.set("in", "00:00:00.000")
    producer.set("out", f"00:00:{VIDEO_DURATION:02d}.000")

    props = {
        "resource": VIDEO_PATH_ON_VM,
        "mlt_service": "avformat",
        "kdenlive:clipname": VIDEO_FILENAME,
        "kdenlive:clip_type": "0",
        "audio_index": "1",
        "video_index": "0",
    }
    for name, value in props.items():
        prop = ET.SubElement(producer, "property")
        prop.set("name", name)
        prop.text = value

    return producer


def _add_black_producer(mlt):
    """Add the default black background producer."""
    producer = ET.SubElement(mlt, "producer")
    producer.set("id", "black_track")
    producer.set("in", "00:00:00.000")
    producer.set("out", "00:10:00.000")

    prop = ET.SubElement(producer, "property")
    prop.set("name", "resource")
    prop.text = "black"

    prop2 = ET.SubElement(producer, "property")
    prop2.set("name", "mlt_service")
    prop2.text = "color"

    return producer


def generate_project_with_clip():
    """
    Generate a .kdenlive project file with a video clip imported in the
    project bin but NOT placed on the timeline.

    Used for Task 2 (Add clip to timeline).
    """
    output_path = os.path.join(ASSETS_DIR, "project_with_clip.kdenlive")

    print(f"  [GEN] Generating project (clip in bin only): {output_path}")

    mlt = _create_base_mlt()

    # Add video producer (in project bin)
    _add_video_producer(mlt, "producer0")

    # Add black background producer
    _add_black_producer(mlt)

    # Main bin playlist (contains references to clips in the project bin)
    main_bin = ET.SubElement(mlt, "playlist")
    main_bin.set("id", "main_bin")

    prop = ET.SubElement(main_bin, "property")
    prop.set("name", "kdenlive:docproperties.version")
    prop.text = "1.1"

    # Add clip reference to main_bin
    entry = ET.SubElement(main_bin, "entry")
    entry.set("producer", "producer0")
    entry.set("in", "00:00:00.000")
    entry.set("out", f"00:00:{VIDEO_DURATION:02d}.000")

    # Empty timeline playlists (V1 video track, A1 audio track)
    playlist_v1 = ET.SubElement(mlt, "playlist")
    playlist_v1.set("id", "playlist0")
    # V1 is empty - only has a blank space
    blank = ET.SubElement(playlist_v1, "blank")
    blank.set("length", "00:10:00.000")

    playlist_a1 = ET.SubElement(mlt, "playlist")
    playlist_a1.set("id", "playlist1")
    blank_a = ET.SubElement(playlist_a1, "blank")
    blank_a.set("length", "00:10:00.000")

    # Background track playlist
    playlist_bg = ET.SubElement(mlt, "playlist")
    playlist_bg.set("id", "background")
    bg_entry = ET.SubElement(playlist_bg, "entry")
    bg_entry.set("producer", "black_track")
    bg_entry.set("in", "00:00:00.000")
    bg_entry.set("out", "00:10:00.000")

    # Tractor (multi-track composition)
    tractor = ET.SubElement(mlt, "tractor")
    tractor.set("id", "tractor0")
    tractor.set("in", "00:00:00.000")
    tractor.set("out", "00:10:00.000")

    track_bg = ET.SubElement(tractor, "track")
    track_bg.set("producer", "background")

    track_v1 = ET.SubElement(tractor, "track")
    track_v1.set("producer", "playlist0")

    track_a1 = ET.SubElement(tractor, "track")
    track_a1.set("producer", "playlist1")
    track_a1.set("hide", "video")

    # Write file
    tree = ET.ElementTree(mlt)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="unicode", xml_declaration=True)

    print(f"  [OK] Project generated: {output_path}")
    return output_path


def generate_project_with_timeline():
    """
    Generate a .kdenlive project file with a video clip already placed
    on the V1 timeline track.

    Used for Task 3 (Grayscale effect), Task 4 (Volume adjustment),
    and Task 5 (Render MP4).
    """
    output_path = os.path.join(ASSETS_DIR, "project_with_timeline.kdenlive")

    print(f"  [GEN] Generating project (clip on timeline): {output_path}")

    mlt = _create_base_mlt()

    # Add video producer
    _add_video_producer(mlt, "producer0")

    # Add black background producer
    _add_black_producer(mlt)

    # Main bin playlist
    main_bin = ET.SubElement(mlt, "playlist")
    main_bin.set("id", "main_bin")

    prop = ET.SubElement(main_bin, "property")
    prop.set("name", "kdenlive:docproperties.version")
    prop.text = "1.1"

    bin_entry = ET.SubElement(main_bin, "entry")
    bin_entry.set("producer", "producer0")
    bin_entry.set("in", "00:00:00.000")
    bin_entry.set("out", f"00:00:{VIDEO_DURATION:02d}.000")

    # V1 video track with clip on timeline
    playlist_v1 = ET.SubElement(mlt, "playlist")
    playlist_v1.set("id", "playlist0")

    timeline_entry = ET.SubElement(playlist_v1, "entry")
    timeline_entry.set("producer", "producer0")
    timeline_entry.set("in", "00:00:00.000")
    timeline_entry.set("out", f"00:00:{VIDEO_DURATION:02d}.000")

    # A1 audio track (empty)
    playlist_a1 = ET.SubElement(mlt, "playlist")
    playlist_a1.set("id", "playlist1")
    blank_a = ET.SubElement(playlist_a1, "blank")
    blank_a.set("length", "00:10:00.000")

    # Background track
    playlist_bg = ET.SubElement(mlt, "playlist")
    playlist_bg.set("id", "background")
    bg_entry = ET.SubElement(playlist_bg, "entry")
    bg_entry.set("producer", "black_track")
    bg_entry.set("in", "00:00:00.000")
    bg_entry.set("out", "00:10:00.000")

    # Tractor
    tractor = ET.SubElement(mlt, "tractor")
    tractor.set("id", "tractor0")
    tractor.set("in", "00:00:00.000")
    tractor.set("out", f"00:00:{VIDEO_DURATION:02d}.000")

    track_bg = ET.SubElement(tractor, "track")
    track_bg.set("producer", "background")

    track_v1 = ET.SubElement(tractor, "track")
    track_v1.set("producer", "playlist0")

    track_a1 = ET.SubElement(tractor, "track")
    track_a1.set("producer", "playlist1")
    track_a1.set("hide", "video")

    # Add audio mix transition between tracks
    transition = ET.SubElement(tractor, "transition")
    transition.set("id", "transition0")

    t_prop1 = ET.SubElement(transition, "property")
    t_prop1.set("name", "mlt_service")
    t_prop1.text = "mix"

    t_prop2 = ET.SubElement(transition, "property")
    t_prop2.set("name", "a_track")
    t_prop2.text = "0"

    t_prop3 = ET.SubElement(transition, "property")
    t_prop3.set("name", "b_track")
    t_prop3.text = "1"

    t_prop4 = ET.SubElement(transition, "property")
    t_prop4.set("name", "always_active")
    t_prop4.text = "1"

    # Write file
    tree = ET.ElementTree(mlt)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="unicode", xml_declaration=True)

    print(f"  [OK] Project generated: {output_path}")
    return output_path


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    print("=" * 60)
    print("Kdenlive Test Asset Generator")
    print("=" * 60)

    # Create output directory
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print(f"\nOutput directory: {ASSETS_DIR}\n")

    # Step 1: Generate test video
    print("[Step 1/3] Generating test video...")
    video_path = generate_test_video()

    # Step 2: Generate project_with_clip.kdenlive
    print("\n[Step 2/3] Generating project with clip in bin only...")
    clip_project = generate_project_with_clip()

    # Step 3: Generate project_with_timeline.kdenlive
    print("\n[Step 3/3] Generating project with clip on timeline...")
    timeline_project = generate_project_with_timeline()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nGenerated files in: {ASSETS_DIR}/")

    files = [
        (VIDEO_FILENAME, "Test video (10s, 1080p, 30fps, with audio)"),
        ("project_with_clip.kdenlive", "Project with clip in bin only (for Task 2)"),
        ("project_with_timeline.kdenlive", "Project with clip on timeline (for Tasks 3, 4, 5)"),
    ]

    for fname, desc in files:
        fpath = os.path.join(ASSETS_DIR, fname)
        exists = "✓" if os.path.exists(fpath) else "✗"
        size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
        print(f"  [{exists}] {fname:<40s} ({size:>8,d} bytes) - {desc}")

    print("\n" + "-" * 60)
    print("UPLOAD INSTRUCTIONS")
    print("-" * 60)
    print("""
These files need to be uploaded to a publicly accessible URL
(e.g., HuggingFace datasets) for the task JSON download configs.

Expected URLs (update task JSONs if different):
  - .../kdenlive/sample_video.mp4
  - .../kdenlive/project_with_clip.kdenlive
  - .../kdenlive/project_with_timeline.kdenlive
""")


if __name__ == "__main__":
    main()
