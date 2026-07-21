"""
Evaluator for task: Resize image to 1920x1080 pixels in GIMP.

This module provides the check_8ea73f6f_resize_1920x1080 function that verifies:
1. The result image dimensions are exactly 1920x1080 pixels
2. The image content is structurally preserved compared to the source image
"""

import os
import logging
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


def check_8ea73f6f_resize_1920x1080(result_path, expected_path, **options):
    """
    Evaluator for task: Resize image to 1920x1080 pixels.

    Checks:
    1. The result image dimensions are exactly 1920x1080 pixels (checked on result_path)
    2. The image content is structurally preserved compared to the source image
       (by resizing source to 1920x1080 and computing SSIM against result)

    Args:
        result_path: Path to the agent's output image (resized result, from VM)
        expected_path: Path to the source/original image (for content comparison, from VM)
        **options: Additional options:
            - ssim_threshold (float): SSIM threshold for content preservation check (default: 0.85)

    Returns:
        float: 1.0 if success, 0.0 if failure
    """
    if result_path is None:
        logger.warning("Result path is None")
        return 0.0

    if not os.path.exists(result_path):
        logger.error(f"Result file not found: {result_path}")
        return 0.0

    try:
        result_img = Image.open(result_path)

        # Check 1: Image dimensions must be exactly 1920x1080
        expected_width = 1920
        expected_height = 1080
        actual_width, actual_height = result_img.size

        size_correct = (actual_width == expected_width and actual_height == expected_height)
        logger.info(
            f"Size check: expected={expected_width}x{expected_height}, "
            f"actual={actual_width}x{actual_height}, correct={size_correct}"
        )

        if not size_correct:
            logger.warning(
                f"Image size incorrect: {actual_width}x{actual_height} "
                f"!= {expected_width}x{expected_height}"
            )
            return 0.0

        # Check 2: Content structure should be preserved (compare with source image)
        if expected_path is not None and os.path.exists(expected_path):
            source_img = Image.open(expected_path)

            # Convert both to RGB for consistent comparison
            if result_img.mode != 'RGB':
                result_img = result_img.convert('RGB')
            if source_img.mode != 'RGB':
                source_img = source_img.convert('RGB')

            # Resize source to target dimensions for pixel-level comparison
            source_resized = source_img.resize(
                (expected_width, expected_height), Image.Resampling.BICUBIC
            )

            result_array = np.array(result_img)
            source_array = np.array(source_resized)

            # Compute SSIM for structure similarity
            ssim_threshold = options.get('ssim_threshold', 0.85)

            min_dim = min(result_array.shape[0], result_array.shape[1])
            if min_dim < 7:
                win_size = min_dim if min_dim % 2 == 1 else min_dim - 1
                if win_size < 1:
                    logger.warning("Image too small for SSIM")
                    return 0.0
            else:
                win_size = 7

            try:
                similarity = ssim(source_array, result_array,
                                  win_size=win_size, channel_axis=2)
            except TypeError:
                similarity = ssim(source_array, result_array,
                                  win_size=win_size, multichannel=True)

            structure_preserved = similarity >= ssim_threshold
            logger.info(
                f"SSIM: {similarity:.4f}, threshold: {ssim_threshold}, "
                f"preserved: {structure_preserved}"
            )

            if not structure_preserved:
                logger.warning(
                    f"Content not preserved: SSIM={similarity:.4f} < {ssim_threshold}"
                )
                return 0.0
        else:
            # If no source image available, skip content check
            # (dimensions check alone is sufficient for resize tasks)
            logger.info(
                "No expected/source image provided, "
                "content check skipped (size check passed)"
            )

        logger.info("check_8ea73f6f_resize_1920x1080: PASS")
        return 1.0

    except Exception as e:
        logger.error(f"check_8ea73f6f_resize_1920x1080 error: {e}")
        return 0.0
