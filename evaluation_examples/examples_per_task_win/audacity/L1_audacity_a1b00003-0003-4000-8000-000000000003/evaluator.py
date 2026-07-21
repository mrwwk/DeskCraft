"""Improved per-task evaluator for L1_audacity_a1b00003-0003-4000-8000-000000000003.

Task:
Open /home/user/Documents/delete_test.wav in Audacity,
delete the 3.0s-5.0s segment,
export to /home/user/Documents/exports/deleted.wav,
then save the Audacity project.
"""

import logging
import os
import wave
import math
from pathlib import Path

logger = logging.getLogger("desktopenv.metrics.audacity")


def _read_wav_info(file_path):
    """Read basic WAV info using the stdlib wave module."""
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
    """Read WAV samples as raw frames plus metadata."""
    with wave.open(file_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)

    return {
        "channels": channels,
        "sample_rate": sample_rate,
        "sampwidth": sampwidth,
        "n_frames": n_frames,
        "frames": frames,
    }


def _slice_frames(wav_data, start_sec, end_sec=None):
    """Slice raw WAV frames by time."""
    sample_rate = wav_data["sample_rate"]
    channels = wav_data["channels"]
    sampwidth = wav_data["sampwidth"]
    n_frames = wav_data["n_frames"]
    frames = wav_data["frames"]

    start_frame = int(round(start_sec * sample_rate))
    if end_sec is None:
        end_frame = n_frames
    else:
        end_frame = int(round(end_sec * sample_rate))

    start_frame = max(0, min(start_frame, n_frames))
    end_frame = max(0, min(end_frame, n_frames))

    frame_size = channels * sampwidth
    return frames[start_frame * frame_size:end_frame * frame_size]


def _raw_bytes_similarity(a: bytes, b: bytes) -> float:
    """Return byte-level similarity between two byte strings.

    1.0 means identical.
    This is simple but effective when the export keeps the same PCM format.
    """
    if not a or not b:
        return 0.0

    min_len = min(len(a), len(b))
    max_len = max(len(a), len(b))

    if max_len == 0:
        return 0.0

    same = 0
    for i in range(min_len):
        if a[i] == b[i]:
            same += 1

    return same / max_len


def _rms_energy_from_pcm_bytes(data: bytes, sampwidth: int) -> float:
    """Compute rough RMS energy from PCM bytes.

    Supports 1-byte, 2-byte, and 4-byte PCM approximately.
    Used as fallback when byte-level comparison is too strict.
    """
    if not data:
        return 0.0

    try:
        if sampwidth == 1:
            samples = [x - 128 for x in data]
        elif sampwidth == 2:
            import struct
            count = len(data) // 2
            samples = struct.unpack("<" + "h" * count, data[:count * 2])
        elif sampwidth == 4:
            import struct
            count = len(data) // 4
            samples = struct.unpack("<" + "i" * count, data[:count * 4])
        else:
            return 0.0

        if not samples:
            return 0.0

        mean_sq = sum(float(x) * float(x) for x in samples) / len(samples)
        return math.sqrt(mean_sq)
    except Exception:
        return 0.0


def _segment_energy_close(a: bytes, b: bytes, sampwidth: int, tolerance_ratio: float = 0.15) -> bool:
    """Fallback check: compare rough energy when raw bytes are not identical."""
    ea = _rms_energy_from_pcm_bytes(a, sampwidth)
    eb = _rms_energy_from_pcm_bytes(b, sampwidth)

    if ea == 0 and eb == 0:
        return True

    if max(ea, eb) == 0:
        return False

    diff_ratio = abs(ea - eb) / max(ea, eb)
    return diff_ratio <= tolerance_ratio


def _find_existing_path(candidates):
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def _check_project_saved(rule) -> float:
    """Check whether Audacity project was saved.

    This requires the project path to be accessible to evaluator.
    If the evaluation system does not copy .aup3 back from VM, this check
    must be supported by result getter / config.
    """
    project_paths = rule.get("project_paths") or []

    single_project_path = rule.get("project_path")
    if single_project_path:
        project_paths.append(single_project_path)

    if not project_paths:
        logger.warning("No project_path/project_paths provided; skip project save check.")
        return 1.0

    for path in project_paths:
        if os.path.isfile(path) and path.endswith(".aup3"):
            logger.info(f"Found saved Audacity project: {path}")
            return 1.0

    logger.error(f"No saved Audacity project found in candidates: {project_paths}")
    return 0.0


def check_audio_duration(file_path, rule) -> float:
    """Improved evaluator.

    Required rule fields:
    {
        "expected_duration": 8.0,
        "tolerance": 0.5,
        "remove_start": 3.0,
        "remove_end": 5.0
    }

    Recommended additional fields:
    {
        "original_file_path": "/home/user/Documents/delete_test.wav",
        "check_content": true,
        "check_project": true,
        "project_path": "/home/user/Documents/delete_test.aup3"
    }
    """
    try:
        if not os.path.isfile(file_path):
            logger.error(f"Exported WAV not found: {file_path}")
            return 0.0

        expected_duration = float(rule.get("expected_duration", 8.0))
        tolerance = float(rule.get("tolerance", 0.5))
        remove_start = float(rule.get("remove_start", 3.0))
        remove_end = float(rule.get("remove_end", 5.0))

        check_content = bool(rule.get("check_content", True))
        check_project = bool(rule.get("check_project", False))

        # -------------------------
        # 1. Check exported WAV duration
        # -------------------------
        out_info = _read_wav_info(file_path)
        actual_duration = out_info["duration"]

        logger.info(
            f"Duration check: actual={actual_duration:.3f}s, "
            f"expected={expected_duration:.3f}s, tolerance={tolerance:.3f}s"
        )

        duration_ok = abs(actual_duration - expected_duration) <= tolerance
        if not duration_ok:
            logger.error("Duration check failed.")
            return 0.0

        # -------------------------
        # 2. Check content correctness
        # Output should equal:
        # original[0:3s] + original[5s:end]
        # -------------------------
        content_score = 1.0

        if check_content:
            original_candidates = []

            if rule.get("original_file_path"):
                original_candidates.append(rule["original_file_path"])

            original_candidates.extend([
                "/home/user/Documents/delete_test.wav",
                "delete_test.wav",
                os.path.join(os.path.dirname(file_path), "delete_test.wav"),
            ])

            original_path = _find_existing_path(original_candidates)

            if original_path is None:
                logger.error(
                    "Original WAV not found. Cannot verify whether the correct 3s-5s segment was removed."
                )
                return 0.0

            original = _read_wav_samples(original_path)
            output = _read_wav_samples(file_path)

            # Basic format check
            if original["channels"] != output["channels"]:
                logger.error("Channel count mismatch.")
                return 0.0

            if original["sample_rate"] != output["sample_rate"]:
                logger.error("Sample rate mismatch.")
                return 0.0

            if original["sampwidth"] != output["sampwidth"]:
                logger.error("Sample width mismatch.")
                return 0.0

            expected_frames = (
                _slice_frames(original, 0.0, remove_start)
                + _slice_frames(original, remove_end, None)
            )

            actual_frames = output["frames"]

            similarity = _raw_bytes_similarity(expected_frames, actual_frames)
            logger.info(f"Byte-level content similarity: {similarity:.4f}")

            byte_similarity_threshold = float(rule.get("byte_similarity_threshold", 0.98))

            if similarity >= byte_similarity_threshold:
                content_score = 1.0
            else:
                # Fallback: compare coarse energy of two major segments
                expected_first = _slice_frames(original, 0.0, remove_start)
                expected_second = _slice_frames(original, remove_end, None)

                output_first = _slice_frames(output, 0.0, remove_start)
                output_second = _slice_frames(output, remove_start, None)

                first_ok = _segment_energy_close(
                    expected_first,
                    output_first,
                    original["sampwidth"],
                    tolerance_ratio=float(rule.get("energy_tolerance_ratio", 0.15)),
                )

                second_ok = _segment_energy_close(
                    expected_second,
                    output_second,
                    original["sampwidth"],
                    tolerance_ratio=float(rule.get("energy_tolerance_ratio", 0.15)),
                )

                if first_ok and second_ok:
                    logger.warning(
                        "Byte-level similarity is low, but coarse segment energy check passed."
                    )
                    content_score = 0.8
                else:
                    logger.error(
                        "Content check failed: output does not match original[0:3s] + original[5s:end]."
                    )
                    return 0.0

        # -------------------------
        # 3. Check Audacity project saved
        # -------------------------
        project_score = 1.0

        if check_project:
            project_score = _check_project_saved(rule)
            if project_score == 0.0:
                logger.error("Project save check failed.")
                return 0.0

        # Strict version: all required checks must pass.
        final_score = min(1.0, content_score, project_score)
        logger.info(f"Final evaluator score: {final_score}")
        return final_score

    except Exception as e:
        logger.error(f"Improved evaluator error: {e}")
        return 0.0