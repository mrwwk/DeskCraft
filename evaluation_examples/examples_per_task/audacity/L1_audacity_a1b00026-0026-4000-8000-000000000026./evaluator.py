"""
Audacity evaluator functions for mini-osworld task.

Two metrics:
1. check_audio_peak_amplitude — verify exported WAV peak amplitude is near -1.0 dB
2. check_aup3_project_valid — verify .aup3 project file was saved and has tracks
"""

import logging
import math
import os
import sqlite3
import struct
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


def _read_wav_samples(file_path):
    """Read WAV samples as a list of floats in [-1.0, 1.0].
    For multi-channel, returns interleaved samples."""
    with wave.open(file_path, "rb") as wf:
        n_frames = wf.getnframes()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(n_frames)

    total_samples = n_frames * channels
    if sampwidth == 1:
        samples = struct.unpack(f"{total_samples}B", raw)
        return [(s - 128) / 128.0 for s in samples]
    elif sampwidth == 2:
        samples = struct.unpack(f"<{total_samples}h", raw)
        return [s / 32768.0 for s in samples]
    elif sampwidth == 3:
        result = []
        for i in range(total_samples):
            b = raw[i * 3: i * 3 + 3]
            val = int.from_bytes(b, byteorder="little", signed=True)
            result.append(val / 8388608.0)
        return result
    elif sampwidth == 4:
        samples = struct.unpack(f"<{total_samples}i", raw)
        return [s / 2147483648.0 for s in samples]
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")


def _get_mono_samples(file_path):
    """Read WAV and return mono samples (average channels) + sample_rate."""
    info = _read_wav_info(file_path)
    samples = _read_wav_samples(file_path)
    channels = info["channels"]
    if channels > 1:
        mono = []
        for i in range(0, len(samples), channels):
            mono.append(sum(samples[i:i + channels]) / channels)
        return mono, info["sample_rate"]
    return samples, info["sample_rate"]


# ---------------------------------------------------------------------------
# Internal helpers — .aup3 project
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
# Metric 1: check_audio_peak_amplitude
# ===========================================================================

def check_audio_peak_amplitude(file_path, rule) -> float:
    """Check peak amplitude is within a dB range.

    Args:
        file_path: Path to the exported WAV file.
        rule: dict with keys:
            - min_peak_db (float): minimum acceptable peak in dB
            - max_peak_db (float): maximum acceptable peak in dB

    Returns:
        1.0 if peak is within [min_peak_db, max_peak_db], else 0.0.
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return 0.0
        samples, sr = _get_mono_samples(file_path)
        peak = max(abs(s) for s in samples) if samples else 0.0
        if peak < 1e-10:
            peak_db = -100.0
        else:
            peak_db = 20.0 * math.log10(peak)

        min_db = float(rule["min_peak_db"])
        max_db = float(rule["max_peak_db"])
        logger.info(f"check_audio_peak_amplitude: peak={peak_db:.2f}dB, range=[{min_db}, {max_db}]")
        return 1.0 if min_db <= peak_db <= max_db else 0.0
    except Exception as e:
        logger.error(f"check_audio_peak_amplitude error: {e}")
        return 0.0


# ===========================================================================
# Metric 2: check_aup3_project_valid
# ===========================================================================

def check_aup3_project_valid(file_path, rule) -> float:
    """Check an .aup3 project is readable and has at least the required tracks.

    Args:
        file_path: Path to the .aup3 project file.
        rule: dict with keys:
            - min_track_count (int, default 1): minimum total tracks
            - min_wave_tracks (int, optional): minimum wave tracks
            - min_label_tracks (int, optional): minimum label tracks

    Returns:
        1.0 if project exists, is readable, and meets track requirements, else 0.0.
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
