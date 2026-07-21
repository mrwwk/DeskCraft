"""
GIMP L2 Evaluation — Perfume Listing (transparent e-commerce hero image).

This evaluator checks whether an agent has correctly:
  1. Exported a valid PNG file.
  2. Removed the near-white background (verified by sufficient transparency).
  3. Placed the product on a 1200×1200 transparent canvas.
  4. Kept the product roughly 70%–80% of canvas height and centered.
  5. Added a soft shadow below the product.
  6. Named the XCF layers exactly Product, Shadow, and Guide_BG.
"""

import os
import logging
from typing import Optional

from PIL import Image
import numpy as np

logger = logging.getLogger("desktopenv.metrics.gimp_l2")


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _has_transparency(image: Image.Image) -> bool:
    """Check if an image has transparency (alpha channel with transparent pixels)."""
    if image.mode == 'RGBA':
        alpha = image.split()[3]
        alpha_array = np.array(alpha)
        return bool(np.any(alpha_array < 255))
    if image.mode == 'P' and 'transparency' in image.info:
        return True
    return False


def _get_transparency_ratio(image: Image.Image) -> float:
    """Calculate the ratio of transparent pixels (alpha < 128) in an image."""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    alpha = image.split()[3]
    alpha_array = np.array(alpha)
    transparent_pixels = np.sum(alpha_array < 128)
    total_pixels = alpha_array.size
    return float(transparent_pixels) / float(total_pixels)


def _build_foreground_mask(
    image: Image.Image,
    white_threshold: int = 245,
    alpha_threshold: int = 40,
) -> np.ndarray:
    """Build a coarse foreground mask for product-centric tasks."""
    if image.mode != 'RGBA':
        rgba = image.convert('RGBA')
    else:
        rgba = image

    arr = np.array(rgba)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    # Prefer alpha when meaningful; otherwise fallback to non-white foreground.
    if np.any(alpha < 250):
        return alpha > alpha_threshold

    non_white = np.any(rgb < white_threshold, axis=2)
    return non_white


# ---------------------------------------------------------------------------
# Binary check functions  (1 = pass, 0 = fail)
# ---------------------------------------------------------------------------

def check_file_exists(file_path: str) -> int:
    """Check if a file exists."""
    if file_path is None:
        return 0
    result = 1 if os.path.isfile(file_path) else 0
    logger.info(f"File exists check: {file_path} -> {result}")
    return result


def check_png_format(image_path: str) -> int:
    """Check if the file is a valid PNG format."""
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        img = Image.open(image_path)
        is_png = img.format == 'PNG'
        logger.info(f"Image format: {img.format}, is PNG: {is_png}")
        return 1 if is_png else 0
    except Exception as e:
        logger.error(f"Error checking PNG format: {e}")
        return 0


def check_transparency_exists(
    image_path: str,
    min_transparency_ratio: float = 0.05,
) -> int:
    """
    Check if an image has sufficient transparency indicating background removal.

    This is stricter than merely checking for any transparent pixel – it requires
    at least `min_transparency_ratio` of the total pixels to be transparent
    (alpha < 128), ruling out cases where only anti-aliasing edge pixels are
    transparent while the background is still present.
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        img = Image.open(image_path)
        if not _has_transparency(img):
            logger.info("Image has no transparency at all")
            return 0

        ratio = _get_transparency_ratio(img)
        if ratio < min_transparency_ratio:
            logger.info(
                f"Transparency ratio too low: {ratio:.4f} < {min_transparency_ratio:.4f}"
            )
            return 0

        logger.info(f"Image has sufficient transparency: ratio={ratio:.4f}")
        return 1
    except Exception as e:
        logger.error(f"Error checking transparency: {e}")
        return 0


def check_image_dimensions(
    image_path: str,
    expected_width: int,
    expected_height: Optional[int] = None,
    tolerance: int = 5,
) -> int:
    """
    Check if an image has the expected dimensions.

    Args:
        image_path: Path to the image file.
        expected_width: Expected width in pixels.
        expected_height: Expected height in pixels (if None, only check width).
        tolerance: Tolerance in pixels for dimension matching.

    Returns:
        1 if dimensions match, 0 otherwise.
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    try:
        img = Image.open(image_path)
        width, height = img.size
        width_match = abs(width - expected_width) <= tolerance
        if expected_height is not None:
            height_match = abs(height - expected_height) <= tolerance
            result = width_match and height_match
        else:
            result = width_match
        logger.info(
            f"Image dimensions: {width}x{height}, expected: {expected_width}x{expected_height}, match: {result}"
        )
        return 1 if result else 0
    except Exception as e:
        logger.error(f"Error checking image dimensions: {e}")
        return 0


def check_subject_scale_and_center(image_path: str, rule: dict) -> int:
    """
    Check subject size ratio and center alignment for product-style composition.

    rule keys:
      - min_height_ratio, max_height_ratio
      - center_tolerance_ratio
      - white_threshold, alpha_threshold
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    min_height_ratio = float(cfg.get("min_height_ratio", 0.65))
    max_height_ratio = float(cfg.get("max_height_ratio", 0.85))
    center_tolerance_ratio = float(cfg.get("center_tolerance_ratio", 0.12))
    white_threshold = int(cfg.get("white_threshold", 245))
    alpha_threshold = int(cfg.get("alpha_threshold", 40))

    try:
        img = Image.open(image_path)
        mask = _build_foreground_mask(
            img,
            white_threshold=white_threshold,
            alpha_threshold=alpha_threshold,
        )

        ys, xs = np.where(mask)
        if len(xs) == 0 or len(ys) == 0:
            logger.info("No foreground pixels found for subject scale/center check")
            return 0

        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())

        h, w = mask.shape
        bbox_h = y1 - y0 + 1
        height_ratio = bbox_h / float(h)

        center_x = (x0 + x1) / 2.0
        center_y = (y0 + y1) / 2.0

        dx_ratio = abs(center_x - (w / 2.0)) / float(w)
        dy_ratio = abs(center_y - (h / 2.0)) / float(h)

        # Vertical tolerance is relaxed because product centering is usually horizontal-first.
        pass_height = min_height_ratio <= height_ratio <= max_height_ratio
        pass_center = (dx_ratio <= center_tolerance_ratio) and (
            dy_ratio <= center_tolerance_ratio * 1.8
        )

        passed = pass_height and pass_center
        logger.info(
            "Subject scale/center: "
            f"height_ratio={height_ratio:.4f}, "
            f"dx_ratio={dx_ratio:.4f}, dy_ratio={dy_ratio:.4f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking subject scale and center: {e}")
        return 0


def check_soft_shadow_presence(image_path: str, rule: dict) -> int:
    """
    Check soft shadow existence below primary subject.

    rule keys:
      - min_shadow_ratio: minimum ratio of soft-shadow pixels in search band
      - alpha_low, alpha_high: semi-transparent alpha bounds
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    min_shadow_ratio = float(cfg.get("min_shadow_ratio", 0.01))
    alpha_low = int(cfg.get("alpha_low", 20))
    alpha_high = int(cfg.get("alpha_high", 220))

    try:
        img = Image.open(image_path).convert('RGBA')
        arr = np.array(img)
        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3]
        h, w = alpha.shape

        fg_mask = alpha > 180
        ys, xs = np.where(fg_mask)
        if len(xs) == 0 or len(ys) == 0:
            logger.info("No dominant foreground detected for shadow check")
            return 0

        x0, x1 = int(xs.min()), int(xs.max())
        y1 = int(ys.max())

        band_top = min(h - 1, y1 + 1)
        band_bottom = min(h, y1 + max(8, h // 5))
        x_pad = max(10, (x1 - x0) // 8)
        sx0 = max(0, x0 - x_pad)
        sx1 = min(w, x1 + x_pad)

        if band_bottom <= band_top or sx1 <= sx0:
            return 0

        shadow_alpha_mask = (alpha[band_top:band_bottom, sx0:sx1] >= alpha_low) & (
            alpha[band_top:band_bottom, sx0:sx1] <= alpha_high
        )

        shadow_ratio = float(np.mean(shadow_alpha_mask))

        if shadow_ratio < min_shadow_ratio:
            # Fallback for opaque white background composition.
            crop = rgb[band_top:band_bottom, sx0:sx1]
            white_like = np.all(crop >= 245, axis=2)
            dark_like = np.mean(crop, axis=2) < 220
            low_sat = (np.max(crop, axis=2) - np.min(crop, axis=2)) < 20
            gray_shadow = (~white_like) & dark_like & low_sat
            shadow_ratio = float(np.mean(gray_shadow))

        passed = shadow_ratio >= min_shadow_ratio
        logger.info(
            f"Soft shadow check: ratio={shadow_ratio:.4f}, min={min_shadow_ratio:.4f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking soft shadow presence: {e}")
        return 0


def check_xcf_layers_structure(xcf_path: str, rule: dict) -> int:
    """
    Check XCF file layer structure with optional order constraints.

    rule keys:
      - layers: required layer names list
      - ordered: whether order should be preserved (default False)
    """
    if xcf_path is None or not os.path.exists(xcf_path):
        logger.error(f"XCF file not found: {xcf_path}")
        return 0

    expected_layers = (rule or {}).get("layers", [])
    ordered = bool((rule or {}).get("ordered", False))

    if not expected_layers:
        logger.warning("check_xcf_layers_structure: no expected layers provided")
        return 0

    try:
        with open(xcf_path, 'rb') as f:
            content = f.read()

        if not content.startswith(b'gimp xcf'):
            logger.error(f"Not a valid XCF file: {xcf_path}")
            return 0

        # Preferred path: parse with gimpformats if available.
        try:
            import gimpformats

            xcf = gimpformats.GimpXcfFile(xcf_path)
            layer_names = [
                getattr(layer, 'name', '') for layer in getattr(xcf, 'layers', [])
            ]
            layer_names = [n for n in layer_names if n]

            if not layer_names:
                raise ValueError("No layer names parsed from gimpformats")

            if not all(name in layer_names for name in expected_layers):
                logger.info(
                    f"XCF structure check failed: expected={expected_layers}, parsed={layer_names}"
                )
                return 0

            if ordered:
                positions = [layer_names.index(name) for name in expected_layers]
                if positions != sorted(positions):
                    logger.info(
                        f"XCF ordered check failed: expected order {expected_layers}, positions={positions}"
                    )
                    return 0

            logger.info(
                f"XCF structure check pass (gimpformats): expected={expected_layers}, ordered={ordered}"
            )
            return 1
        except Exception:
            # Fallback: byte-level string search (less strict but deterministic).
            positions = []
            for name in expected_layers:
                pos = content.find(name.encode('utf-8'))
                if pos < 0:
                    logger.info(f"XCF layer missing in binary search: {name}")
                    return 0
                positions.append(pos)

            if ordered and positions != sorted(positions):
                logger.info(f"XCF ordered binary check failed: positions={positions}")
                return 0

            logger.info(
                f"XCF structure check pass (binary fallback): expected={expected_layers}, ordered={ordered}"
            )
            return 1
    except Exception as e:
        logger.error(f"Error checking XCF structure: {e}")
        return 0


# ---------------------------------------------------------------------------
# Score aggregation
# ---------------------------------------------------------------------------

def _all_binary_checks_pass(scores: list) -> float:
    """Return 1.0 only when all binary checks pass, otherwise 0.0."""
    valid = [float(s) for s in scores if s is not None]
    if not valid:
        return 0.0
    return 1.0 if all(v >= 1.0 for v in valid) else 0.0


# ---------------------------------------------------------------------------
# Composite evaluator  (exactly one entry point referenced by task.json)
# ---------------------------------------------------------------------------

def check_l2_perfume_listing_complete(result_paths: list) -> float:
    """
    Composite evaluator for the L2 perfume transparent listing task.

    result_paths[0] → perfume_listing.png
    result_paths[1] → perfume_listing.xcf
    result_paths[2] → product_perfume_965989.jpg (source, may be used for diff checks)

    Returns 1.0 only when **all** of the following pass:
      1. PNG file exists
      2. Valid PNG format
      3. Sufficient transparency (≥5% of pixels transparent → background removed)
      4. Exactly 1200×1200 pixels
      5. Subject occupies 68%–84% of canvas height and is centered
      6. Soft shadow detected below subject
      7. XCF layers contain Product, Shadow, Guide_BG (order not enforced)
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(
            f"check_l2_perfume_listing_complete invalid result_paths: {result_paths}"
        )
        return 0.0

    png_path, xcf_path, _src_path = result_paths[:3]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_transparency_exists(png_path, min_transparency_ratio=0.05),
        check_image_dimensions(png_path, 1200, 1200),
        check_subject_scale_and_center(
            png_path,
            {
                "min_height_ratio": 0.68,
                "max_height_ratio": 0.84,
                "center_tolerance_ratio": 0.14,
            },
        ),
        check_soft_shadow_presence(png_path, {"min_shadow_ratio": 0.008}),
        check_xcf_layers_structure(
            xcf_path,
            {"layers": ["Product", "Shadow", "Guide_BG"], "ordered": False},
        ),
    ]
    return _all_binary_checks_pass(scores)
