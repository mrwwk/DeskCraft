"""Evaluator for the interactive camera annotation task."""

import logging
import os
from collections import deque

import numpy as np
from PIL import Image

logger = logging.getLogger("desktopenv.metrics.gimp_l2")


def check_file_exists(file_path: str) -> int:
    if file_path is None:
        return 0
    result = 1 if os.path.isfile(file_path) else 0
    logger.info(f"File exists check: {file_path} -> {result}")
    return result


def _check_valid_image(image_path: str) -> int:
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        with Image.open(image_path) as img:
            img.verify()
        return 1
    except Exception as e:
        logger.error(f"Invalid image {image_path}: {e}")
        return 0


def check_png_format(image_path: str) -> int:
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        with Image.open(image_path) as img:
            is_png = img.format == "PNG"
        logger.info(f"PNG format check: {image_path} -> {is_png}")
        return 1 if is_png else 0
    except Exception as e:
        logger.error(f"Error checking PNG format: {e}")
        return 0


def check_image_dimensions(
    image_path: str,
    expected_width: int,
    expected_height: int,
    tolerance: int = 5,
) -> int:
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        with Image.open(image_path) as img:
            width, height = img.size
        passed = (
            abs(width - expected_width) <= tolerance
            and abs(height - expected_height) <= tolerance
        )
        logger.info(
            f"Dimension check: actual={width}x{height}, "
            f"expected={expected_width}x{expected_height}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking image dimensions: {e}")
        return 0


def _edge_density(gray_array: np.ndarray, edge_threshold: float = 40.0) -> float:
    gx = np.abs(np.gradient(gray_array, axis=1))
    gy = np.abs(np.gradient(gray_array, axis=0))
    edges = gx + gy
    return float(np.mean(edges > edge_threshold))


def _check_image_has_text_like_content(image_path: str) -> int:
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    try:
        with Image.open(image_path) as img:
            gray = np.array(img.convert("L"))
        h, w = gray.shape
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
                if _edge_density(crop, edge_threshold=45.0) >= 0.012:
                    text_regions += 1

        passed = text_regions >= 4
        logger.info(f"Text-like region check: regions={text_regions}, pass={passed}")
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error in text-like content check: {e}")
        return 0


def check_text_keywords(image_path: str, keywords: list[str]) -> int:
    """Check annotation keywords, using OCR when available with edge fallback."""
    try:
        import pytesseract

        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img).lower()
        missing = [keyword for keyword in keywords if keyword.lower() not in text]
        if not missing:
            logger.info(f"OCR keyword check passed: {keywords}")
            return 1
        logger.info(f"OCR keyword check missing {missing}; falling back to text-like check")
    except Exception as e:
        logger.info(f"OCR unavailable or failed ({e}); falling back to text-like check")

    return _check_image_has_text_like_content(image_path)


def check_annotation_callout_count(src_path: str, tgt_path: str, min_callouts: int = 3) -> int:
    """Estimate whether at least three callout/annotation components were added."""
    if not src_path or not tgt_path or not os.path.exists(src_path) or not os.path.exists(tgt_path):
        logger.error(f"Missing source or target for callout check: src={src_path}, tgt={tgt_path}")
        return 0

    try:
        with Image.open(src_path) as src_img:
            src = src_img.convert("RGB")
        with Image.open(tgt_path) as tgt_img:
            tgt = tgt_img.convert("RGB")
        if src.size != tgt.size:
            src = src.resize(tgt.size, Image.Resampling.LANCZOS)

        src_arr = np.asarray(src, dtype=np.int16)
        tgt_arr = np.asarray(tgt, dtype=np.int16)
        diff = np.mean(np.abs(tgt_arr - src_arr), axis=2)
        mask = diff > 35

        h, w = mask.shape
        visited = np.zeros(mask.shape, dtype=bool)
        components = 0

        # Downsample the traversal grid for speed while preserving callout-scale changes.
        step = 2
        for y in range(0, h, step):
            for x in range(0, w, step):
                if not mask[y, x] or visited[y, x]:
                    continue

                queue = deque([(y, x)])
                visited[y, x] = True
                count = 0

                while queue:
                    cy, cx = queue.popleft()
                    count += 1
                    for ny, nx in (
                        (cy - step, cx),
                        (cy + step, cx),
                        (cy, cx - step),
                        (cy, cx + step),
                    ):
                        if (
                            0 <= ny < h
                            and 0 <= nx < w
                            and mask[ny, nx]
                            and not visited[ny, nx]
                        ):
                            visited[ny, nx] = True
                            queue.append((ny, nx))

                if 25 <= count <= 15000:
                    components += 1

        passed = components >= min_callouts
        logger.info(
            f"Callout component check: components={components}, "
            f"required={min_callouts}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking annotation callout count: {e}")
        return 0


def check_xcf_layers_structure(xcf_path: str, expected_layers: list[str]) -> int:
    if xcf_path is None or not os.path.exists(xcf_path):
        logger.error(f"XCF file not found: {xcf_path}")
        return 0

    try:
        with open(xcf_path, "rb") as f:
            content = f.read()
        missing = [layer for layer in expected_layers if layer.encode("utf-8") not in content]
        passed = not missing
        logger.info(f"XCF layer check: missing={missing}, pass={passed}")
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking XCF layers: {e}")
        return 0


def _all_binary_checks_pass(scores: list) -> float:
    valid = [float(score) for score in scores if score is not None]
    if not valid:
        return 0.0
    return 1.0 if all(score >= 1.0 for score in valid) else 0.0


def check_interactive_gimp_camera_annotation_complete(
    result_paths: list,
    expected=None,
    **options,
) -> float:
    """
    Check the final clarified requirements:
    - camera_annotation.png exists, is PNG, and preserves original 2000x1325 size
    - at least three callout-like annotation components were added
    - Lens, Grip, and Mode Dial labels are present or text-like annotations are visible
    - camera_annotation.xcf exists and contains the required layer names
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path, src_path = result_paths[:3]
    required_layers = ["Base_Image", "Callout_1", "Callout_2", "Callout_3", "Footer_Note"]

    scores = [
        check_file_exists(png_path),
        check_file_exists(xcf_path),
        _check_valid_image(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 2000, 1325),
        check_annotation_callout_count(src_path, png_path, min_callouts=3),
        check_text_keywords(png_path, ["Lens", "Grip", "Mode Dial"]),
        check_xcf_layers_structure(xcf_path, required_layers),
    ]

    logger.info(f"Camera annotation check scores: {scores}")
    return _all_binary_checks_pass(scores)
