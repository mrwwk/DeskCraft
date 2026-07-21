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


def _extract_time_range(samples, sr, start_time, end_time):
    start_idx = int(float(start_time) * sr)
    end_idx = int(float(end_time) * sr)
    start_idx = max(0, min(start_idx, len(samples)))
    end_idx = max(0, min(end_idx, len(samples)))
    return samples[start_idx:end_idx]


def _resolve_reference_path(path):
    """Resolve repo asset paths when evaluator runs from repo root or task dir."""
    if os.path.isabs(path) and os.path.isfile(path):
        return path

    candidates = [
        os.path.abspath(path),
        os.path.join(os.path.dirname(__file__), path),
    ]

    base = os.path.dirname(__file__)
    for _ in range(8):
        candidates.append(os.path.join(base, path))
        base = os.path.dirname(base)

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return path


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


def check_audio_noise_reduced(file_path, rule) -> float:
    """Check output is quieter than the source after noise reduction.

    rule: {
      "source_path": str,
      "noise_start": float,
      "noise_end": float,
      "min_noise_reduction_db": float (default 6.0),
      "min_overall_reduction_db": float (default 3.0),
      "min_output_rms_db": float (default -45.0),
      "max_output_noise_rms_db": float (optional),
      "max_output_overall_rms_db": float (optional)
    }
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"Output file not found: {file_path}")
            return 0.0

        source_path = _resolve_reference_path(rule["source_path"])
        if not os.path.isfile(source_path):
            logger.error(f"Source reference file not found: {source_path}")
            return 0.0

        source_samples, source_sr = _get_mono_samples(source_path)
        output_samples, output_sr = _get_mono_samples(file_path)
        if source_sr != output_sr:
            logger.info(f"Sample rate mismatch: source={source_sr}, output={output_sr}")
            return 0.0

        noise_start = float(rule.get("noise_start", 0.0))
        noise_end = float(rule.get("noise_end", 0.5))
        source_noise = _extract_time_range(source_samples, source_sr, noise_start, noise_end)
        output_noise = _extract_time_range(output_samples, output_sr, noise_start, noise_end)
        if not source_noise or not output_noise:
            logger.error("Empty noise-profile region")
            return 0.0

        source_noise_rms = _rms_db(source_noise)
        output_noise_rms = _rms_db(output_noise)
        source_overall_rms = _rms_db(source_samples)
        output_overall_rms = _rms_db(output_samples)
        noise_reduction = source_noise_rms - output_noise_rms
        overall_reduction = source_overall_rms - output_overall_rms

        logger.info(
            "check_audio_noise_reduced: "
            f"noise {source_noise_rms:.2f}->{output_noise_rms:.2f}dB "
            f"(reduction {noise_reduction:.2f}dB), "
            f"overall {source_overall_rms:.2f}->{output_overall_rms:.2f}dB "
            f"(reduction {overall_reduction:.2f}dB)"
        )

        if noise_reduction < float(rule.get("min_noise_reduction_db", 6.0)):
            return 0.0
        if overall_reduction < float(rule.get("min_overall_reduction_db", 3.0)):
            return 0.0
        if output_overall_rms < float(rule.get("min_output_rms_db", -45.0)):
            return 0.0
        if "max_output_noise_rms_db" in rule and output_noise_rms > float(rule["max_output_noise_rms_db"]):
            return 0.0
        if "max_output_overall_rms_db" in rule and output_overall_rms > float(rule["max_output_overall_rms_db"]):
            return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_audio_noise_reduced error: {e}")
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
