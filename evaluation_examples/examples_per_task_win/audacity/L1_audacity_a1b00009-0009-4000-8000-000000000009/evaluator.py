"""
Audacity evaluator functions for OSWorld.

Two verification approaches:
1. Exported WAV analysis — sample rate
2. .aup3 SQLite parsing — project validity (track count)
"""

import logging
import os
import sqlite3
import wave
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers — WAV
# ---------------------------------------------------------------------------

def _read_wav_info(file_path):
    """Read basic WAV info using the stdlib wave module. Returns dict with
    'channels', 'sample_rate', 'n_frames', 'duration', 'sampwidth'."""
    with wave.open(file_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        sampwidth = wf.getsampwidth()
        duration = n_frames / sample_rate if sample_rate > 0 else 0.0
        return {
            "channels": channels,
            "sample_rate": sample_rate,
            "n_frames": n_frames,
            "duration": duration,
            "sampwidth": sampwidth,
        }


# ---------------------------------------------------------------------------
# Internal helpers — .aup3
# ---------------------------------------------------------------------------

def _open_aup3(file_path):
    """Open an .aup3 file as a SQLite database and return the connection."""
    conn = sqlite3.connect(file_path)
    return conn


def _get_aup3_project_xml(file_path):
    """Extract the project XML from an .aup3 file."""
    conn = _open_aup3(file_path)
    try:
        cursor = conn.execute("SELECT doc FROM project LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            # Try autosave table
            cursor = conn.execute("SELECT doc FROM autosave LIMIT 1")
            row = cursor.fetchone()
        if row is None:
            return None
        xml_str = row[0]
        if isinstance(xml_str, bytes):
            xml_str = xml_str.decode("utf-8")
        return xml_str
    finally:
        conn.close()


def _parse_aup3_tracks(file_path):
    """Parse .aup3 project XML and return list of track info dicts."""
    xml_str = _get_aup3_project_xml(file_path)
    if xml_str is None:
        return []

    root = ET.fromstring(xml_str)
    tracks = []

    # Handle namespace
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    for elem in root:
        tag = elem.tag.replace(ns, "")
        if tag in ("wavetrack", "WaveTrack"):
            track_info = {
                "type": "wave",
                "name": elem.get("name", ""),
                "gain": float(elem.get("gain", "1.0")),
                "mute": elem.get("mute", "0") == "1",
                "solo": elem.get("solo", "0") == "1",
                "pan": float(elem.get("pan", "0.0")),
            }
            tracks.append(track_info)
        elif tag in ("labeltrack", "LabelTrack"):
            labels = []
            for label_elem in elem:
                label_tag = label_elem.tag.replace(ns, "")
                if label_tag in ("label", "Label"):
                    labels.append({
                        "time": float(label_elem.get("t", label_elem.get("t0", "0"))),
                        "t1": float(label_elem.get("t1", label_elem.get("t", "0"))),
                        "text": label_elem.get("title", label_elem.get("text", "")),
                    })
            track_info = {
                "type": "label",
                "name": elem.get("name", ""),
                "labels": labels,
            }
            tracks.append(track_info)

    return tracks


# ===========================================================================
# Metric functions
# ===========================================================================

def check_audio_sample_rate(file_path, rule) -> float:
    """Check audio sample rate.
    rule: {"expected_sr": int}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        info = _read_wav_info(file_path)
        expected = int(rule["expected_sr"])
        actual = info["sample_rate"]
        logger.info(f"check_audio_sample_rate: actual={actual}, expected={expected}")
        return 1.0 if actual == expected else 0.0
    except Exception as e:
        logger.error(f"check_audio_sample_rate error: {e}")
        return 0.0


def check_aup3_project_valid(file_path, rule) -> float:
    """Check an .aup3 project is readable and has at least required tracks.
    rule: {
      "min_track_count": int (default 1),
      "min_wave_tracks": int (optional),
      "min_label_tracks": int (optional)
    }
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"AUP3 project not found: {file_path}")
            return 0.0

        tracks = _parse_aup3_tracks(file_path)
        if not tracks:
            logger.error("No tracks parsed from .aup3 project")
            return 0.0

        total = len(tracks)
        wave_count = sum(1 for t in tracks if t.get("type") == "wave")
        label_count = sum(1 for t in tracks if t.get("type") == "label")

        min_track_count = int(rule.get("min_track_count", 1))
        min_wave_tracks = int(rule.get("min_wave_tracks", 0))
        min_label_tracks = int(rule.get("min_label_tracks", 0))

        logger.info(
            f"check_aup3_project_valid: total={total}, wave={wave_count}, label={label_count}, "
            f"requirements(total>={min_track_count}, wave>={min_wave_tracks}, label>={min_label_tracks})"
        )

        if total < min_track_count:
            return 0.0
        if wave_count < min_wave_tracks:
            return 0.0
        if label_count < min_label_tracks:
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_aup3_project_valid error: {e}")
        return 0.0
