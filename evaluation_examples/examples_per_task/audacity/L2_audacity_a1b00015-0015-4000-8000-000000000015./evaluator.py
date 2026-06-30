"""
Audacity evaluator functions for OSWorld.

Covers:
1. Exported WAV analysis — duration and RMS level
2. Project file validation — supports both .aup (XML) and .aup3 (SQLite)
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
        # 8-bit unsigned
        samples = struct.unpack(f"{total_samples}B", raw)
        return [(s - 128) / 128.0 for s in samples]
    elif sampwidth == 2:
        # 16-bit signed
        samples = struct.unpack(f"<{total_samples}h", raw)
        return [s / 32768.0 for s in samples]
    elif sampwidth == 3:
        # 24-bit signed
        result = []
        for i in range(total_samples):
            b = raw[i * 3: i * 3 + 3]
            val = int.from_bytes(b, byteorder="little", signed=True)
            result.append(val / 8388608.0)
        return result
    elif sampwidth == 4:
        # 32-bit signed
        samples = struct.unpack(f"<{total_samples}i", raw)
        return [s / 2147483648.0 for s in samples]
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")


def _rms_db(samples):
    """Compute RMS in dB for a list of float samples."""
    if not samples:
        return -100.0
    mean_sq = sum(s * s for s in samples) / len(samples)
    rms = math.sqrt(mean_sq)
    if rms < 1e-10:
        return -100.0
    return 20.0 * math.log10(rms)


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


# ===========================================================================
# Atomic evaluators — WAV files
# ===========================================================================

def check_audio_duration(file_path, rule) -> float:
    """Check audio file duration.
    rule: {"expected_duration": float, "tolerance": float (default 0.5)}
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return 0.0
        info = _read_wav_info(file_path)
        expected = float(rule["expected_duration"])
        tolerance = float(rule.get("tolerance", 0.5))
        actual = info["duration"]
        logger.info(f"check_audio_duration: actual={actual:.2f}s, expected={expected:.2f}s, tol={tolerance:.2f}s")
        if abs(actual - expected) <= tolerance:
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_audio_duration error: {e}")
        return 0.0


def check_audio_rms_level(file_path, rule) -> float:
    """Check audio RMS level is within a dB range.
    rule: {"min_rms_db": float, "max_rms_db": float}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        samples, sr = _get_mono_samples(file_path)
        rms = _rms_db(samples)
        min_db = float(rule["min_rms_db"])
        max_db = float(rule["max_rms_db"])
        logger.info(f"check_audio_rms_level: rms={rms:.2f}dB, range=[{min_db}, {max_db}]")
        return 1.0 if min_db <= rms <= max_db else 0.0
    except Exception as e:
        logger.error(f"check_audio_rms_level error: {e}")
        return 0.0


# ===========================================================================
# Project file evaluators
# ===========================================================================

def check_aup_project_exists(file_path, rule) -> float:
    """Check that an Audacity project file exists and is valid.
    Supports both .aup (XML-based, Audacity 2.x) and .aup3 (SQLite-based,
    Audacity 3.x) formats.

    rule: {"min_file_size": int (default 100)}
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"Project file not found: {file_path}")
            return 0.0

        min_size = int(rule.get("min_file_size", 100))
        actual_size = os.path.getsize(file_path)
        if actual_size < min_size:
            logger.error(
                f"Project file too small: {actual_size} bytes < {min_size}"
            )
            return 0.0

        # Try .aup3 (SQLite) format first
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('project', 'autosave')"
            )
            row = cursor.fetchone()
            conn.close()
            if row is not None:
                logger.info(
                    f"check_aup_project_exists: valid .aup3 (SQLite), "
                    f"size={actual_size} bytes"
                )
                return 1.0
        except Exception:
            pass

        # Try .aup (XML) format
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            if root is not None:
                logger.info(
                    f"check_aup_project_exists: valid .aup (XML), "
                    f"size={actual_size} bytes"
                )
                return 1.0
        except Exception:
            pass

        logger.error(
            f"Project file could not be parsed as .aup or .aup3: {file_path}"
        )
        return 0.0

    except Exception as e:
        logger.error(f"check_aup_project_exists error: {e}")
        return 0.0
