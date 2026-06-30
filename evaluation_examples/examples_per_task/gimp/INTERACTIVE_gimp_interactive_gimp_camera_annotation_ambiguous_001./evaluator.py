"""
Evaluator for interactive / ambiguous camera annotation task.

This evaluator is designed for the ambiguous-instruction scenario where
the agent only receives phase 1: "帮我做一张相机说明图"
(Make me a camera annotation diagram).

It checks that:
1. An output image file exists and can be opened by PIL
2. The image has annotation-like content (text edges detected via edge analysis)

It does NOT check:
- Specific image format (accepts PNG or JPEG)
- Specific dimensions
- XCF project file or layer structure
- Specific keywords in annotations
- Specific annotation count via diff-based comparison
"""

import os
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger("desktopenv.metrics.gimp_l2")


def _edge_density(gray_array: np.ndarray, edge_threshold: float = 40.0) -> float:
    """Compute ratio of pixels with gradient magnitude above edge_threshold."""
    gx = np.abs(np.gradient(gray_array, axis=1))
    gy = np.abs(np.gradient(gray_array, axis=0))
    edges = gx + gy
    return float(np.mean(edges > edge_threshold))


def check_file_exists(file_path: str) -> int:
    """Check if a file exists."""
    if file_path is None:
        return 0
    result = 1 if os.path.isfile(file_path) else 0
    logger.info(f"File exists check: {file_path} -> {result}")
    return result


def _check_valid_image(image_path: str) -> int:
    """Check if file can be opened as a valid image by PIL."""
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        img = Image.open(image_path)
        img.verify()
        logger.info(f"Valid image check: {image_path} -> pass")
        return 1
    except Exception as e:
        logger.error(f"Invalid image {image_path}: {e}")
        return 0


def _check_image_has_text_like_content(image_path: str, **options) -> int:
    """
    Check if image contains text-like annotation content.

    Uses multi-region edge density analysis to detect text/annotation patterns.
    Text annotations create thin, high-contrast edges that are detectable via
    gradient analysis across a grid of sub-regions.

    options:
      - min_text_regions: minimum grid cells with text-like edges (default 3)
      - edge_threshold: gradient threshold for edge detection (default 45)
      - min_edge_density: minimum edge density per region (default 0.01)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    min_text_regions = int(options.get("min_text_regions", 3))
    edge_threshold = float(options.get("edge_threshold", 45.0))
    min_edge_density = float(options.get("min_edge_density", 0.01))

    try:
        img = Image.open(image_path)
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        # Divide into 4x4 grid and check each cell for text-like edges
        rows, cols = 4, 4
        cell_h, cell_w = h // rows, w // cols

        text_regions = 0
        for r in range(rows):
            for c in range(cols):
                y0 = r * cell_h
                y1 = min((r + 1) * cell_h, h)
                x0 = c * cell_w
                x1 = min((c + 1) * cell_w, w)
                crop = gray[y0:y1, x0:x1]
                if crop.size < 100:
                    continue
                density = _edge_density(crop, edge_threshold=edge_threshold)
                if density >= min_edge_density:
                    text_regions += 1

        passed = text_regions >= min_text_regions
        logger.info(
            f"Text content check: {text_regions}/{rows*cols} regions with "
            f"edge_density >= {min_edge_density}, min_required={min_text_regions}, "
            f"pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error in text content check: {e}")
        return 0


def _all_binary_checks_pass(scores: list) -> float:
    """Return 1.0 only when all binary checks pass, otherwise 0.0."""
    valid = [float(s) for s in scores if s is not None]
    if not valid:
        return 0.0
    return 1.0 if all(v >= 1.0 for v in valid) else 0.0


def check_interactive_gimp_camera_annotation_complete(
    result_paths: list, expected=None, **options
) -> float:
    """
    Evaluator for ambiguous camera annotation task.

    The agent received only the phase-1 instruction ("帮我做一张相机说明图")
    and was expected to produce an image with visible annotations on the camera photo.

    Checks (all must pass for score 1.0):
      1. Output image file exists (PNG or JPEG)
      2. File is a valid openable image
      3. Image contains text-like annotation content (edge density analysis)

    Args:
        result_paths: [png_path, xcf_path, jpg_path] - uses first available
        expected: unused (kept for framework compatibility)
        **options: optional thresholds (min_text_regions, edge_threshold, min_edge_density)

    Returns:
        1.0 if all checks pass, 0.0 otherwise
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Invalid result_paths: {result_paths}")
        return 0.0

    # Accept any available output (PNG preferred, JPG fallback)
    output_path = result_paths[0] if result_paths[0] is not None else result_paths[2]

    if output_path is None:
        logger.error("No output image available (both PNG and JPG are null)")
        return 0.0

    scores = [
        check_file_exists(output_path),
        _check_valid_image(output_path),
        _check_image_has_text_like_content(output_path, **options),
    ]

    logger.info(f"Camera annotation check scores: {scores}")
    return _all_binary_checks_pass(scores)
