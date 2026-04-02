"""
Audacity evaluator functions for OSWorld.

Two verification approaches:
1. Exported WAV analysis — duration, sample rate, channels, RMS level, fades, silence
2. .aup3 SQLite parsing — track count, gain, mute/solo state, labels
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
# Internal helpers
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
    """Extract samples in [start_time, end_time] seconds."""
    start_idx = int(start_time * sr)
    end_idx = int(end_time * sr)
    start_idx = max(0, min(start_idx, len(samples)))
    end_idx = max(0, min(end_idx, len(samples)))
    return samples[start_idx:end_idx]


# ---------------------------------------------------------------------------
# .aup3 helpers
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


def check_audio_channels(file_path, rule) -> float:
    """Check audio channel count.
    rule: {"expected_channels": int}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        info = _read_wav_info(file_path)
        expected = int(rule["expected_channels"])
        actual = info["channels"]
        logger.info(f"check_audio_channels: actual={actual}, expected={expected}")
        return 1.0 if actual == expected else 0.0
    except Exception as e:
        logger.error(f"check_audio_channels error: {e}")
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


def check_audio_fade_in(file_path, rule) -> float:
    """Check that audio has a fade-in (RMS increases over initial windows).
    rule: {"fade_duration": float, "num_windows": int (default 5)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        samples, sr = _get_mono_samples(file_path)
        fade_dur = float(rule["fade_duration"])
        num_windows = int(rule.get("num_windows", 5))

        fade_samples = int(fade_dur * sr)
        if fade_samples > len(samples):
            logger.error("Fade duration exceeds audio length")
            return 0.0

        window_size = fade_samples // num_windows
        if window_size < 1:
            return 0.0

        rms_values = []
        for i in range(num_windows):
            start = i * window_size
            end = start + window_size
            chunk = samples[start:end]
            rms_values.append(_rms_db(chunk))

        logger.info(f"check_audio_fade_in: window RMS values = {[f'{v:.1f}' for v in rms_values]}")

        # Check that RMS is generally increasing: at least (num_windows - 1) increases
        increases = sum(1 for i in range(len(rms_values) - 1) if rms_values[i + 1] > rms_values[i])
        # Allow at most 1 non-increase for robustness
        if increases >= num_windows - 2:
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_audio_fade_in error: {e}")
        return 0.0


def check_audio_fade_out(file_path, rule) -> float:
    """Check that audio has a fade-out (RMS decreases over final windows).
    rule: {"fade_duration": float, "num_windows": int (default 5)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        samples, sr = _get_mono_samples(file_path)
        fade_dur = float(rule["fade_duration"])
        num_windows = int(rule.get("num_windows", 5))

        fade_samples = int(fade_dur * sr)
        if fade_samples > len(samples):
            logger.error("Fade duration exceeds audio length")
            return 0.0

        window_size = fade_samples // num_windows
        if window_size < 1:
            return 0.0

        offset = len(samples) - fade_samples
        rms_values = []
        for i in range(num_windows):
            start = offset + i * window_size
            end = start + window_size
            chunk = samples[start:end]
            rms_values.append(_rms_db(chunk))

        logger.info(f"check_audio_fade_out: window RMS values = {[f'{v:.1f}' for v in rms_values]}")

        # Check that RMS is generally decreasing
        decreases = sum(1 for i in range(len(rms_values) - 1) if rms_values[i + 1] < rms_values[i])
        if decreases >= num_windows - 2:
            return 1.0
        return 0.0
    except Exception as e:
        logger.error(f"check_audio_fade_out error: {e}")
        return 0.0


def check_audio_silence_at(file_path, rule) -> float:
    """Check that a region of audio is silence (below threshold).
    rule: {"start_time": float, "end_time": float, "max_rms_db": float (default -40)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        samples, sr = _get_mono_samples(file_path)
        start = float(rule["start_time"])
        end = float(rule["end_time"])
        max_rms = float(rule.get("max_rms_db", -40))

        region = _extract_time_range(samples, sr, start, end)
        if not region:
            logger.error("Empty region for silence check")
            return 0.0

        rms = _rms_db(region)
        logger.info(f"check_audio_silence_at: [{start}-{end}s] rms={rms:.2f}dB, max={max_rms}dB")
        return 1.0 if rms <= max_rms else 0.0
    except Exception as e:
        logger.error(f"check_audio_silence_at error: {e}")
        return 0.0


def check_audio_has_content_at(file_path, rule) -> float:
    """Check that a region of audio has content (above threshold).
    rule: {"start_time": float, "end_time": float, "min_rms_db": float (default -30)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        samples, sr = _get_mono_samples(file_path)
        start = float(rule["start_time"])
        end = float(rule["end_time"])
        min_rms = float(rule.get("min_rms_db", -30))

        region = _extract_time_range(samples, sr, start, end)
        if not region:
            logger.error("Empty region for content check")
            return 0.0

        rms = _rms_db(region)
        logger.info(f"check_audio_has_content_at: [{start}-{end}s] rms={rms:.2f}dB, min={min_rms}dB")
        return 1.0 if rms >= min_rms else 0.0
    except Exception as e:
        logger.error(f"check_audio_has_content_at error: {e}")
        return 0.0


def check_audio_peak_amplitude(file_path, rule) -> float:
    """Check peak amplitude is within a dB range.
    rule: {"min_peak_db": float, "max_peak_db": float}
    """
    try:
        if not os.path.isfile(file_path):
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


def check_audio_file_valid(file_path, rule) -> float:
    """Check that an audio file exists and is readable.
    rule: {} (optional: {"expected_format": "WAV"})
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
            return 0.0
        info = _read_wav_info(file_path)
        logger.info(f"check_audio_file_valid: sr={info['sample_rate']}, ch={info['channels']}, dur={info['duration']:.2f}s")
        return 1.0
    except Exception as e:
        logger.error(f"check_audio_file_valid error: {e}")
        return 0.0


# ===========================================================================
# Composite evaluators — WAV files
# ===========================================================================

def check_audio_properties(file_path, rule) -> float:
    """Check multiple audio properties at once (duration + sample_rate + channels).
    rule: {"expected_duration": float, "tolerance": float (default 0.5),
           "expected_sr": int (optional), "expected_channels": int (optional)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        info = _read_wav_info(file_path)

        # Duration check
        expected_dur = float(rule["expected_duration"])
        tolerance = float(rule.get("tolerance", 0.5))
        if abs(info["duration"] - expected_dur) > tolerance:
            logger.info(f"Duration mismatch: {info['duration']:.2f} vs {expected_dur:.2f}")
            return 0.0

        # Sample rate check (optional)
        if "expected_sr" in rule:
            expected_sr = int(rule["expected_sr"])
            if info["sample_rate"] != expected_sr:
                logger.info(f"Sample rate mismatch: {info['sample_rate']} vs {expected_sr}")
                return 0.0

        # Channels check (optional)
        if "expected_channels" in rule:
            expected_ch = int(rule["expected_channels"])
            if info["channels"] != expected_ch:
                logger.info(f"Channels mismatch: {info['channels']} vs {expected_ch}")
                return 0.0

        logger.info(f"check_audio_properties: all checks passed")
        return 1.0
    except Exception as e:
        logger.error(f"check_audio_properties error: {e}")
        return 0.0


def check_audio_with_fades(file_path, rule) -> float:
    """Check duration and optionally fade-in/fade-out.
    rule: {"expected_duration": float, "tolerance": float (default 0.5),
           "fade_in_duration": float (optional), "fade_out_duration": float (optional),
           "num_windows": int (default 5)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0

        # Duration check
        info = _read_wav_info(file_path)
        expected_dur = float(rule["expected_duration"])
        tolerance = float(rule.get("tolerance", 0.5))
        if abs(info["duration"] - expected_dur) > tolerance:
            logger.info(f"Duration mismatch: {info['duration']:.2f} vs {expected_dur:.2f}")
            return 0.0

        num_windows = int(rule.get("num_windows", 5))

        # Fade-in check
        if "fade_in_duration" in rule:
            fade_rule = {"fade_duration": rule["fade_in_duration"], "num_windows": num_windows}
            if check_audio_fade_in(file_path, fade_rule) < 1.0:
                return 0.0

        # Fade-out check
        if "fade_out_duration" in rule:
            fade_rule = {"fade_duration": rule["fade_out_duration"], "num_windows": num_windows}
            if check_audio_fade_out(file_path, fade_rule) < 1.0:
                return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_audio_with_fades error: {e}")
        return 0.0


# ===========================================================================
# .aup3 project evaluators
# ===========================================================================

def check_aup3_track_count(file_path, rule) -> float:
    """Check track count in an .aup3 project.
    rule: {"expected_track_count": int}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        tracks = _parse_aup3_tracks(file_path)
        expected = int(rule["expected_track_count"])
        actual = len(tracks)
        logger.info(f"check_aup3_track_count: actual={actual}, expected={expected}")
        return 1.0 if actual == expected else 0.0
    except Exception as e:
        logger.error(f"check_aup3_track_count error: {e}")
        return 0.0


def check_aup3_track_gain(file_path, rule) -> float:
    """Check a track's gain in the .aup3 project.
    rule: {"track_index": int, "expected_gain_db": float, "tolerance": float (default 2.0)}

    Gain in .aup3 is stored as a linear multiplier. We convert to dB for comparison.
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        tracks = _parse_aup3_tracks(file_path)
        idx = int(rule["track_index"])
        if idx >= len(tracks):
            logger.error(f"Track index {idx} out of range (have {len(tracks)} tracks)")
            return 0.0

        track = tracks[idx]
        gain_linear = track.get("gain", 1.0)
        if gain_linear <= 0:
            actual_db = -100.0
        else:
            actual_db = 20.0 * math.log10(gain_linear)

        expected_db = float(rule["expected_gain_db"])
        tolerance = float(rule.get("tolerance", 2.0))
        logger.info(f"check_aup3_track_gain: track[{idx}] gain={actual_db:.2f}dB, expected={expected_db:.2f}dB")
        return 1.0 if abs(actual_db - expected_db) <= tolerance else 0.0
    except Exception as e:
        logger.error(f"check_aup3_track_gain error: {e}")
        return 0.0


def check_aup3_track_mute(file_path, rule) -> float:
    """Check a track's mute state in the .aup3 project.
    rule: {"track_index": int, "expected_mute": bool}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        tracks = _parse_aup3_tracks(file_path)
        idx = int(rule["track_index"])
        if idx >= len(tracks):
            logger.error(f"Track index {idx} out of range")
            return 0.0

        track = tracks[idx]
        actual = track.get("mute", False)
        expected = bool(rule["expected_mute"])
        logger.info(f"check_aup3_track_mute: track[{idx}] mute={actual}, expected={expected}")
        return 1.0 if actual == expected else 0.0
    except Exception as e:
        logger.error(f"check_aup3_track_mute error: {e}")
        return 0.0


def check_aup3_labels(file_path, rule) -> float:
    """Check labels in an .aup3 project.
    rule: {"expected_labels": [{"time": float, "text": str}, ...],
           "time_tolerance": float (default 1.0)}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0
        tracks = _parse_aup3_tracks(file_path)

        # Find label tracks
        all_labels = []
        for track in tracks:
            if track.get("type") == "label":
                all_labels.extend(track.get("labels", []))

        expected_labels = rule["expected_labels"]
        time_tol = float(rule.get("time_tolerance", 1.0))

        if len(all_labels) < len(expected_labels):
            logger.info(f"Label count mismatch: have {len(all_labels)}, expected {len(expected_labels)}")
            return 0.0

        # For each expected label, find a matching actual label
        matched = set()
        for exp in expected_labels:
            found = False
            for i, actual in enumerate(all_labels):
                if i in matched:
                    continue
                time_match = abs(actual["time"] - exp["time"]) <= time_tol
                text_match = exp["text"].strip().lower() in actual["text"].strip().lower() or \
                             actual["text"].strip().lower() in exp["text"].strip().lower()
                if time_match and text_match:
                    matched.add(i)
                    found = True
                    break
            if not found:
                logger.info(f"Label not found: time={exp['time']}, text='{exp['text']}'")
                return 0.0

        logger.info(f"check_aup3_labels: all {len(expected_labels)} labels matched")
        return 1.0
    except Exception as e:
        logger.error(f"check_aup3_labels error: {e}")
        return 0.0


# ===========================================================================
# Additional composite evaluators for interactive Audacity tasks
# ===========================================================================

def check_audio_duration_range(file_path, rule) -> float:
    """Check that duration is within [min_duration, max_duration].
    rule: {"min_duration": float, "max_duration": float}
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0

        info = _read_wav_info(file_path)
        actual = info["duration"]
        min_duration = float(rule["min_duration"])
        max_duration = float(rule["max_duration"])
        logger.info(
            f"check_audio_duration_range: actual={actual:.2f}s, range=[{min_duration:.2f}, {max_duration:.2f}]"
        )
        return 1.0 if min_duration <= actual <= max_duration else 0.0
    except Exception as e:
        logger.error(f"check_audio_duration_range error: {e}")
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


def check_interactive_audacity_ia01(file_path, rule) -> float:
    """IA-01 validator: partial denoise delivery.
    Ensures duration is preserved and both intro/tail still contain content.
    """
    try:
        if not os.path.isfile(file_path):
            return 0.0

        duration_rule = {
            "expected_duration": float(rule["expected_duration"]),
            "tolerance": float(rule.get("duration_tolerance", 1.0)),
        }
        if check_audio_duration(file_path, duration_rule) < 1.0:
            return 0.0

        samples, sr = _get_mono_samples(file_path)
        intro = _extract_time_range(
            samples,
            sr,
            float(rule.get("intro_start", 0.0)),
            float(rule.get("intro_end", 2.0)),
        )
        tail = _extract_time_range(
            samples,
            sr,
            float(rule.get("tail_start", 2.0)),
            float(rule.get("tail_end", duration_rule["expected_duration"])),
        )

        if not intro or not tail:
            return 0.0

        intro_rms = _rms_db(intro)
        tail_rms = _rms_db(tail)
        intro_min = float(rule.get("intro_min_rms_db", -30.0))
        tail_min = float(rule.get("tail_min_rms_db", -38.0))
        logger.info(
            f"check_interactive_audacity_ia01: intro_rms={intro_rms:.2f}dB (min {intro_min}), "
            f"tail_rms={tail_rms:.2f}dB (min {tail_min})"
        )

        if intro_rms < intro_min:
            return 0.0
        if tail_rms < tail_min:
            return 0.0
        return 1.0
    except Exception as e:
        logger.error(f"check_interactive_audacity_ia01 error: {e}")
        return 0.0


def check_interactive_audacity_ia02(file_path, rule) -> float:
    """IA-02 validator: trim + normalize (peak) + fade-out."""
    try:
        if not os.path.isfile(file_path):
            return 0.0

        duration_rule = {
            "expected_duration": float(rule["expected_duration"]),
            "tolerance": float(rule.get("duration_tolerance", 0.8)),
        }
        if check_audio_duration(file_path, duration_rule) < 1.0:
            return 0.0

        peak_rule = {
            "min_peak_db": float(rule.get("min_peak_db", -3.0)),
            "max_peak_db": float(rule.get("max_peak_db", -0.1)),
        }
        if check_audio_peak_amplitude(file_path, peak_rule) < 1.0:
            return 0.0

        fade_rule = {
            "fade_duration": float(rule.get("fade_duration", 2.0)),
            "num_windows": int(rule.get("num_windows", 5)),
        }
        if check_audio_fade_out(file_path, fade_rule) < 1.0:
            return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_interactive_audacity_ia02 error: {e}")
        return 0.0


def check_interactive_audacity_ia03(file_path, rule) -> float:
    """IA-03 validator: denoise + head cut + fade-out export."""
    try:
        if not os.path.isfile(file_path):
            return 0.0

        duration_rule = {
            "expected_duration": float(rule["expected_duration"]),
            "tolerance": float(rule.get("duration_tolerance", 0.8)),
        }
        if check_audio_duration(file_path, duration_rule) < 1.0:
            return 0.0

        fade_rule = {
            "fade_duration": float(rule.get("fade_duration", 3.0)),
            "num_windows": int(rule.get("num_windows", 5)),
        }
        if check_audio_fade_out(file_path, fade_rule) < 1.0:
            return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_interactive_audacity_ia03 error: {e}")
        return 0.0


def check_interactive_audacity_ia04(file_path, rule) -> float:
    """IA-04 validator: mixed output with inserted gap and mono export."""
    try:
        if not os.path.isfile(file_path):
            return 0.0

        duration_rule = {
            "min_duration": float(rule.get("min_duration", 29.5)),
            "max_duration": float(rule.get("max_duration", 33.5)),
        }
        if check_audio_duration_range(file_path, duration_rule) < 1.0:
            return 0.0

        silence_rule = {
            "start_time": float(rule.get("silence_start", 15.0)),
            "end_time": float(rule.get("silence_end", 16.8)),
            "max_rms_db": float(rule.get("max_rms_db", -38.0)),
        }
        if check_audio_silence_at(file_path, silence_rule) < 1.0:
            return 0.0

        channel_rule = {"expected_channels": int(rule.get("expected_channels", 1))}
        if check_audio_channels(file_path, channel_rule) < 1.0:
            return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_interactive_audacity_ia04 error: {e}")
        return 0.0


def check_interactive_audacity_ia05(file_path, rule) -> float:
    """IA-05 validator: revised clip duration + fade-out."""
    try:
        if not os.path.isfile(file_path):
            return 0.0

        duration_rule = {
            "expected_duration": float(rule["expected_duration"]),
            "tolerance": float(rule.get("duration_tolerance", 1.0)),
        }
        if check_audio_duration(file_path, duration_rule) < 1.0:
            return 0.0

        fade_rule = {
            "fade_duration": float(rule.get("fade_duration", 3.0)),
            "num_windows": int(rule.get("num_windows", 5)),
        }
        if check_audio_fade_out(file_path, fade_rule) < 1.0:
            return 0.0

        return 1.0
    except Exception as e:
        logger.error(f"check_interactive_audacity_ia05 error: {e}")
        return 0.0
