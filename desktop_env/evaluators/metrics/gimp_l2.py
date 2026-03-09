"""
GIMP L2 Evaluation Functions for complex multi-step editing tasks.

This module provides evaluation functions for verifying professional pet portrait
editing workflows and other complex GIMP operations that require multiple steps.
"""

import os
import logging
import re
from typing import Tuple, Optional
from PIL import Image, ImageStat
import numpy as np
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger("desktopenv.metrics.gimp_l2")


def calculate_brightness(image: Image.Image) -> float:
    """Calculate the average brightness of an image"""
    grayscale = image.convert('L')
    stat = ImageStat.Stat(grayscale)
    return stat.mean[0]


def calculate_saturation(image: Image.Image) -> float:
    """Calculate the average saturation of an image"""
    hsv_image = image.convert('HSV')
    saturation_channel = hsv_image.split()[1]
    stat = ImageStat.Stat(saturation_channel)
    return stat.mean[0]


def calculate_contrast(image: Image.Image) -> float:
    """Calculate the contrast of an image as the standard deviation of pixel values"""
    grayscale = image.convert('L')
    stat = ImageStat.Stat(grayscale)
    return stat.stddev[0]


def has_transparency(image: Image.Image) -> bool:
    """Check if an image has transparency (alpha channel with transparent pixels)"""
    if image.mode == 'RGBA':
        alpha = image.split()[3]
        # Check if any pixel has alpha < 255
        alpha_array = np.array(alpha)
        return np.any(alpha_array < 255)
    elif image.mode == 'P' and 'transparency' in image.info:
        return True
    return False


def get_transparency_ratio(image: Image.Image) -> float:
    """Calculate the ratio of transparent pixels in an image"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    alpha = image.split()[3]
    alpha_array = np.array(alpha)
    # Count pixels that are mostly transparent (alpha < 128)
    transparent_pixels = np.sum(alpha_array < 128)
    total_pixels = alpha_array.size
    return transparent_pixels / total_pixels


def check_image_dimensions(image_path: str, expected_width: int, expected_height: Optional[int] = None, tolerance: int = 5) -> int:
    """
    Check if an image has the expected dimensions.
    
    Args:
        image_path: Path to the image file
        expected_width: Expected width in pixels
        expected_height: Expected height in pixels (if None, only check width)
        tolerance: Tolerance in pixels for dimension matching
    
    Returns:
        1 if dimensions match, 0 otherwise
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
        
        logger.info(f"Image dimensions: {width}x{height}, expected: {expected_width}x{expected_height}, match: {result}")
        return 1 if result else 0
    
    except Exception as e:
        logger.error(f"Error checking image dimensions: {e}")
        return 0


def check_png_format(image_path: str) -> int:
    """
    Check if the file is a valid PNG format.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        1 if PNG format, 0 otherwise
    """
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


def check_transparency_exists(image_path: str) -> int:
    """
    Check if an image has transparency (alpha channel with some transparent areas).
    
    Args:
        image_path: Path to the image file
    
    Returns:
        1 if transparency exists, 0 otherwise
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    
    try:
        img = Image.open(image_path)
        has_alpha = has_transparency(img)
        logger.info(f"Image has transparency: {has_alpha}")
        return 1 if has_alpha else 0
    
    except Exception as e:
        logger.error(f"Error checking transparency: {e}")
        return 0


def check_saturation_increase(src_path: str, tgt_path: str, min_increase_percent: float = 10.0) -> int:
    """
    Check if the target image has increased saturation compared to source.
    
    Args:
        src_path: Path to the source image
        tgt_path: Path to the target image
        min_increase_percent: Minimum required saturation increase percentage
    
    Returns:
        1 if saturation increased by at least min_increase_percent, 0 otherwise
    """
    if src_path is None or tgt_path is None:
        return 0
    
    if not os.path.exists(src_path) or not os.path.exists(tgt_path):
        logger.error(f"Image file not found: src={src_path}, tgt={tgt_path}")
        return 0
    
    try:
        src_img = Image.open(src_path)
        tgt_img = Image.open(tgt_path)
        
        src_saturation = calculate_saturation(src_img)
        tgt_saturation = calculate_saturation(tgt_img)
        
        if src_saturation == 0:
            logger.warning("Source saturation is 0, cannot calculate increase")
            return 0
        
        increase_percent = ((tgt_saturation - src_saturation) / src_saturation) * 100
        result = increase_percent >= min_increase_percent
        
        logger.info(f"Saturation: src={src_saturation:.2f}, tgt={tgt_saturation:.2f}, increase={increase_percent:.2f}%, required={min_increase_percent}%, pass={result}")
        return 1 if result else 0
    
    except Exception as e:
        logger.error(f"Error checking saturation increase: {e}")
        return 0


def check_contrast_increase(src_path: str, tgt_path: str, min_increase_percent: float = 10.0) -> int:
    """
    Check if the target image has increased contrast compared to source.
    
    Args:
        src_path: Path to the source image
        tgt_path: Path to the target image
        min_increase_percent: Minimum required contrast increase percentage
    
    Returns:
        1 if contrast increased by at least min_increase_percent, 0 otherwise
    """
    if src_path is None or tgt_path is None:
        return 0
    
    if not os.path.exists(src_path) or not os.path.exists(tgt_path):
        logger.error(f"Image file not found: src={src_path}, tgt={tgt_path}")
        return 0
    
    try:
        src_img = Image.open(src_path)
        tgt_img = Image.open(tgt_path)
        
        src_contrast = calculate_contrast(src_img)
        tgt_contrast = calculate_contrast(tgt_img)
        
        if src_contrast == 0:
            logger.warning("Source contrast is 0, cannot calculate increase")
            return 0
        
        increase_percent = ((tgt_contrast - src_contrast) / src_contrast) * 100
        result = increase_percent >= min_increase_percent
        
        logger.info(f"Contrast: src={src_contrast:.2f}, tgt={tgt_contrast:.2f}, increase={increase_percent:.2f}%, required={min_increase_percent}%, pass={result}")
        return 1 if result else 0
    
    except Exception as e:
        logger.error(f"Error checking contrast increase: {e}")
        return 0


def check_file_exists(file_path: str) -> int:
    """
    Check if a file exists.
    
    Args:
        file_path: Path to the file
    
    Returns:
        1 if file exists, 0 otherwise
    """
    if file_path is None:
        return 0
    
    result = 1 if os.path.isfile(file_path) else 0
    logger.info(f"File exists check: {file_path} -> {result}")
    return result


def check_xcf_file_exists_and_has_layers(xcf_path: str, expected_layers: list) -> int:
    """
    Check if an XCF file exists and contains expected layer names.
    
    Note: XCF parsing is limited - we check for layer name strings in the file.
    
    Args:
        xcf_path: Path to the XCF file
        expected_layers: List of expected layer names
    
    Returns:
        1 if file exists and contains all expected layers, 0 otherwise
    """
    if xcf_path is None or not os.path.exists(xcf_path):
        logger.error(f"XCF file not found: {xcf_path}")
        return 0
    
    try:
        # Read XCF file as binary and search for layer names
        with open(xcf_path, 'rb') as f:
            content = f.read()
        
        # Check for XCF magic number
        if not content.startswith(b'gimp xcf'):
            logger.error(f"Not a valid XCF file: {xcf_path}")
            return 0
        
        # Search for layer names in the file content
        # Layer names in XCF are stored as UTF-8 strings
        found_layers = []
        for layer_name in expected_layers:
            if layer_name.encode('utf-8') in content:
                found_layers.append(layer_name)
        
        all_found = len(found_layers) == len(expected_layers)
        logger.info(f"XCF layers check: expected={expected_layers}, found={found_layers}, pass={all_found}")
        return 1 if all_found else 0
    
    except Exception as e:
        logger.error(f"Error checking XCF file: {e}")
        return 0


def check_text_in_image(image_path: str, expected_text: str) -> int:
    """
    Check if expected text appears in the image.
    
    Note: This is a basic check that looks for text-like patterns.
    For proper OCR, additional dependencies would be needed.
    
    Args:
        image_path: Path to the image file
        expected_text: Text that should appear in the image
    
    Returns:
        1 if text is likely present, 0 otherwise
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    
    try:
        img = Image.open(image_path)
        
        # Convert to grayscale
        gray = img.convert('L')
        img_array = np.array(gray)
        
        # Look for regions with high contrast (potential text)
        # Text typically has sharp transitions between light and dark
        sobel_x = np.abs(np.gradient(img_array, axis=1))
        sobel_y = np.abs(np.gradient(img_array, axis=0))
        edges = sobel_x + sobel_y
        
        # Check if there are edge-dense regions (potential text areas)
        # This is a heuristic - real OCR would be more accurate
        edge_density = np.mean(edges > 50)  # Threshold for edges
        
        # For "HUSKY" we expect some text-like patterns
        # This is a basic check - in practice, you'd use tesseract or similar
        has_text_patterns = edge_density > 0.01  # At least 1% edge pixels
        
        logger.info(f"Text detection: edge_density={edge_density:.4f}, has_text_patterns={has_text_patterns}")
        
        # Since we can't do reliable OCR without tesseract, we return 1 if text patterns exist
        # This is a lenient check
        return 1 if has_text_patterns else 0
    
    except Exception as e:
        logger.error(f"Error checking text in image: {e}")
        return 0


def check_gradient_colors(image_path: str, expected_colors: list, tolerance: int = 40) -> int:
    """
    Check if an image contains expected gradient colors.
    
    Args:
        image_path: Path to the image file
        expected_colors: List of expected color hex codes (e.g., ['#1a237e', '#4a148c'])
        tolerance: Color matching tolerance (0-255)
    
    Returns:
        1 if all expected colors are found, 0 otherwise
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_array = np.array(img)
        
        # Parse expected colors
        expected_rgb = []
        for color in expected_colors:
            if color.startswith('#'):
                color = color[1:]
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            expected_rgb.append((r, g, b))
        
        # Check if each expected color exists in the image (within tolerance)
        found_colors = []
        for exp_r, exp_g, exp_b in expected_rgb:
            # Calculate color distance for all pixels
            diff = np.sqrt(
                (img_array[:, :, 0].astype(float) - exp_r) ** 2 +
                (img_array[:, :, 1].astype(float) - exp_g) ** 2 +
                (img_array[:, :, 2].astype(float) - exp_b) ** 2
            )
            # Check if any pixel is within tolerance
            if np.any(diff < tolerance):
                found_colors.append(f'#{exp_r:02x}{exp_g:02x}{exp_b:02x}')
        
        all_found = len(found_colors) == len(expected_colors)
        logger.info(f"Gradient colors: expected={expected_colors}, found={found_colors}, pass={all_found}")
        return 1 if all_found else 0
    
    except Exception as e:
        logger.error(f"Error checking gradient colors: {e}")
        return 0


def check_husky_portrait_complete(
    result_paths: list,
    expected_width: int = 1920
) -> float:
    """
    Comprehensive check for the husky portrait editing task.
    
    This function checks multiple aspects of the completed task:
    1. Output file exists and is PNG format
    2. Image has correct width (1920px)
    3. Image has transparency (background removed)
    4. XCF project file exists with expected layers
    5. Saturation increased (color adjustment applied)
    6. Contrast increased (color adjustment applied)
    
    Args:
        result_paths: List of [png_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels
    
    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0
    
    result_path = result_paths[0]  # husky_portrait.png
    xcf_path = result_paths[1]     # husky_project.xcf
    src_path = result_paths[2]     # dog_with_background.png (source)
    
    scores = []
    
    # Check 1: PNG file exists
    png_exists = check_file_exists(result_path)
    scores.append(png_exists)
    logger.info(f"Check 1 - PNG exists: {png_exists}")
    
    if png_exists == 0:
        logger.warning("PNG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist
    
    # Check 2: PNG format
    is_png = check_png_format(result_path)
    scores.append(is_png)
    logger.info(f"Check 2 - PNG format: {is_png}")
    
    # Check 3: Correct width
    width_ok = check_image_dimensions(result_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width: {width_ok}")
    
    # Check 4: Has transparency
    has_trans = check_transparency_exists(result_path)
    scores.append(has_trans)
    logger.info(f"Check 4 - Has transparency: {has_trans}")
    
    # Check 5: XCF file exists with layers
    expected_layers = ['Gradient_BG', 'Vignette']
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 5 - XCF with layers: {xcf_ok}")
    
    # Check 6: Saturation increased (if source exists)
    if src_path and os.path.exists(src_path):
        sat_ok = check_saturation_increase(src_path, result_path, min_increase_percent=10.0)
        scores.append(sat_ok)
        logger.info(f"Check 6 - Saturation increase: {sat_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping saturation check")
    
    # Check 7: Contrast increased (if source exists)
    if src_path and os.path.exists(src_path):
        cont_ok = check_contrast_increase(src_path, result_path, min_increase_percent=10.0)
        scores.append(cont_ok)
        logger.info(f"Check 7 - Contrast increase: {cont_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping contrast check")
    
    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Husky portrait complete: scores={scores}, final={final_score:.2f}")

    return final_score


def check_jpeg_format(image_path: str) -> int:
    """
    Check if the file is a valid JPEG format.

    Args:
        image_path: Path to the image file

    Returns:
        1 if JPEG format, 0 otherwise
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    try:
        img = Image.open(image_path)
        is_jpeg = img.format == 'JPEG'
        logger.info(f"Image format: {img.format}, is JPEG: {is_jpeg}")
        return 1 if is_jpeg else 0

    except Exception as e:
        logger.error(f"Error checking JPEG format: {e}")
        return 0


def check_barn_landscape_complete(
    result_paths: list,
    expected_path: str = None,
    expected_width: int = 1600
) -> float:
    """
    Comprehensive check for the rural barn landscape enhancement workflow task.

    This function checks multiple aspects of the completed task:
    1. Exported JPEG file exists and is JPEG format
    2. JPEG has correct width (1600px)
    3. XCF project file exists with all expected layers
    4. Saturation increased (color adjustment applied)
    5. Contrast increased (color adjustment applied)

    Expected layers in XCF:
    - Sky_Drama
    - Barn_Red
    - Grass_Vibrant
    - Roof_Detail
    - Vignette
    - Text_Title
    - Text_Location
    - Frame

    Args:
        result_paths: List of [jpeg_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels (default 1600)

    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0

    jpeg_path = result_paths[0]   # country_barn.jpg
    xcf_path = result_paths[1]    # barn_project.xcf
    src_path = result_paths[2]    # publicdomainpictures-clouds-220109_1920.jpg (source)

    scores = []

    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")

    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist

    # Check 2: JPEG format
    is_jpeg = check_jpeg_format(jpeg_path)
    scores.append(is_jpeg)
    logger.info(f"Check 2 - JPEG format: {is_jpeg}")

    # Check 3: Correct width (1600px, height auto)
    width_ok = check_image_dimensions(jpeg_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width: {width_ok}")

    # Check 4: XCF file exists with all expected layers
    expected_layers = [
        'Sky_Drama',
        'Barn_Red',
        'Grass_Vibrant',
        'Roof_Detail',
        'Vignette',
        'Text_Title',
        'Text_Location',
        'Frame'
    ]
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with all layers: {xcf_ok}")

    # Check 5: Saturation increased (if source exists)
    if src_path and os.path.exists(src_path):
        sat_ok = check_saturation_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(sat_ok)
        logger.info(f"Check 5 - Saturation increase: {sat_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping saturation check")

    # Check 6: Contrast increased (if source exists)
    if src_path and os.path.exists(src_path):
        cont_ok = check_contrast_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(cont_ok)
        logger.info(f"Check 6 - Contrast increase: {cont_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping contrast check")

    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Barn landscape complete: scores={scores}, final={final_score:.2f}")

    return final_score


def check_portrait_edit_complete(
    result_paths: list,
    expected_width: int = 1600,
    expected_layers: list = None
) -> float:
    """
    Comprehensive check for the portrait editing workflow task.
    
    This function checks multiple aspects of the completed task:
    1. Exported JPEG file exists and is JPEG format
    2. JPEG has correct width (1600px)
    3. XCF project file exists with all expected layers
    4. Brightness increased on subject layer
    5. Contrast increased on subject layer
    
    Args:
        result_paths: List of [jpeg_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels
        expected_layers: List of expected layer names in XCF file
    
    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0
    
    jpeg_path = result_paths[0]      # portrait_final.jpg
    xcf_path = result_paths[1]       # portrait_edit.xcf
    src_path = result_paths[2]       # woman_sitting_by_the_tree.png (source)
    
    # Default expected layers for this task
    if expected_layers is None:
        expected_layers = [
            'Subject',
            'Solid_BG',
            'Warm_Overlay',
            'Vignette',
            'Text_Title',
            'Text_Subtitle',
            'Text_Year'
        ]
    
    scores = []
    
    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")
    
    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist
    
    # Check 2: JPEG format
    is_jpeg = check_jpeg_format(jpeg_path)
    scores.append(is_jpeg)
    logger.info(f"Check 2 - JPEG format: {is_jpeg}")
    
    # Check 3: Correct width
    width_ok = check_image_dimensions(jpeg_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width ({expected_width}px): {width_ok}")
    
    # Check 4: XCF file exists with layers
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with layers {expected_layers}: {xcf_ok}")
    
    # Check 5: Brightness increased (if source exists)
    # Note: This is a simplified check - actual brightness adjustment on subject layer
    # would require more sophisticated analysis
    if src_path and os.path.exists(src_path):
        try:
            src_img = Image.open(src_path)
            jpeg_img = Image.open(jpeg_path)
            
            # Compare overall brightness (simplified)
            src_brightness = calculate_brightness(src_img)
            jpeg_brightness = calculate_brightness(jpeg_img)
            
            # Expect some brightness change (could be increase or decrease based on edits)
            brightness_changed = abs(jpeg_brightness - src_brightness) > 5
            scores.append(1 if brightness_changed else 0)
            logger.info(f"Check 5 - Brightness changed: {brightness_changed} (src={src_brightness:.2f}, jpeg={jpeg_brightness:.2f})")
        except Exception as e:
            logger.warning(f"Could not check brightness: {e}")
            scores.append(0)
    else:
        logger.warning(f"Source file not found: {src_path}, skipping brightness check")
    
    # Check 6: Contrast increased (if source exists)
    if src_path and os.path.exists(src_path):
        cont_ok = check_contrast_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(cont_ok)
        logger.info(f"Check 6 - Contrast increase: {cont_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping contrast check")
    
    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Portrait edit complete: scores={scores}, final={final_score:.2f}")

    return final_score


def check_fashion_portrait_complete(
    result_paths: list,
    expected_path: str = None,
    expected_width: int = 1400
) -> float:
    """
    Comprehensive check for the fashion portrait editing workflow task.

    This function checks multiple aspects of the completed task:
    1. Exported JPEG file exists and is JPEG format
    2. JPEG has correct width (1400px)
    3. XCF project file exists with all expected layers
    4. Saturation increased (color adjustment applied)
    5. Contrast increased (color adjustment applied)

    Expected layers in XCF:
    - Subject_Cutout
    - Background_Pink
    - Skin_Tone
    - Clothing_Pop
    - Contrast_Boost
    - Vignette
    - Text_Style
    - Text_Season
    - Frame

    Args:
        result_paths: List of [jpeg_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels (default 1400)

    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0

    jpeg_path = result_paths[0]   # fashion_portrait.jpg
    xcf_path = result_paths[1]    # fashion_project.xcf
    src_path = result_paths[2]    # pexels-marvellous-adu-2148798496-36125485.jpg (source)

    scores = []

    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")

    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist

    # Check 2: JPEG format
    is_jpeg = check_jpeg_format(jpeg_path)
    scores.append(is_jpeg)
    logger.info(f"Check 2 - JPEG format: {is_jpeg}")

    # Check 3: Correct width (1400px, height auto)
    width_ok = check_image_dimensions(jpeg_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width: {width_ok}")

    # Check 4: XCF file exists with all expected layers
    expected_layers = [
        'Subject_Cutout',
        'Background_Pink',
        'Skin_Tone',
        'Clothing_Pop',
        'Contrast_Boost',
        'Vignette',
        'Text_Style',
        'Text_Season',
        'Frame'
    ]
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with all layers: {xcf_ok}")

    # Check 5: Saturation increased (if source exists)
    if src_path and os.path.exists(src_path):
        sat_ok = check_saturation_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(sat_ok)
        logger.info(f"Check 5 - Saturation increase: {sat_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping saturation check")

    # Check 6: Contrast increased (if source exists)
    if src_path and os.path.exists(src_path):
        cont_ok = check_contrast_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(cont_ok)
        logger.info(f"Check 6 - Contrast increase: {cont_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping contrast check")

    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Fashion portrait complete: scores={scores}, final={final_score:.2f}")

    return final_score


def check_city_sunset_complete(
    result_paths: list,
    expected_width: int = 1400
) -> float:
    """
    Comprehensive check for the city sunset skyline enhancement workflow task.

    This function checks multiple aspects of the completed task:
    1. Exported JPEG file exists and is JPEG format
    2. JPEG has correct width (1400px, quality 94)
    3. XCF project file exists with all expected layers
    4. Saturation increased (color adjustments applied to sky and buildings)
    5. Contrast increased (S-curve applied)

    Expected layers in XCF (in order from bottom to top):
    - Background (original image layer)
    - Sky_Purple (Free Select + Hue-Saturation: Purple +30)
    - Building_Gold (Hue-Saturation: Yellow +35)
    - Rainbow_Enhance (Color Balance: Red +20, Blue +15)
    - Contrast_Boost (Curves: S-curve, 22% contrast)
    - Vignette (Elliptical Select + Feather 90px + black 25% opacity)
    - Text_Title ("CITY OF GOLD", 38px, #ffd700, top-center)
    - Text_Time ("SUNSET", 24px, #ff69b4, bottom-right)
    - Frame (8px border #4b0082)

    Args:
        result_paths: List of [jpeg_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels (default 1400)

    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0

    jpeg_path = result_paths[0]   # city_sunset.jpg
    xcf_path = result_paths[1]    # city_project.xcf
    src_path = result_paths[2]    # pexels-houwng-nguyen-3756130-32529063.jpg (source)

    scores = []

    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")

    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist

    # Check 2: JPEG format
    is_jpeg = check_jpeg_format(jpeg_path)
    scores.append(is_jpeg)
    logger.info(f"Check 2 - JPEG format: {is_jpeg}")

    # Check 3: Correct width (1400px, height auto)
    width_ok = check_image_dimensions(jpeg_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width ({expected_width}px): {width_ok}")

    # Check 4: XCF file exists with all expected layers
    expected_layers = [
        'Sky_Purple',
        'Building_Gold',
        'Rainbow_Enhance',
        'Contrast_Boost',
        'Vignette',
        'Text_Title',
        'Text_Time',
        'Frame'
    ]
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with layers {expected_layers}: {xcf_ok}")

    # Check 5: Saturation increased (if source exists)
    # The task involves multiple saturation adjustments (Purple +30, Yellow +35)
    # so overall saturation should increase
    if src_path and os.path.exists(src_path):
        sat_ok = check_saturation_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(sat_ok)
        logger.info(f"Check 5 - Saturation increase: {sat_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping saturation check")

    # Check 6: Contrast increased (if source exists)
    # The task specifies 22% contrast increase via S-curve
    if src_path and os.path.exists(src_path):
        cont_ok = check_contrast_increase(src_path, jpeg_path, min_increase_percent=10.0)
        scores.append(cont_ok)
        logger.info(f"Check 6 - Contrast increase: {cont_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping contrast check")

    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"City sunset complete: scores={scores}, final={final_score:.2f}")

    return final_score


def check_lake_landscape_complete(
    result_paths: list,
    expected_width: int = 1600
) -> float:
    """
    Comprehensive check for the lake landscape photo enhancement workflow task.

    This function checks multiple aspects of the completed task:
    1. Exported JPEG file exists and is JPEG format
    2. JPEG has correct width (1600px, quality 94)
    3. XCF project file exists with all expected layers
    4. Saturation increased (color adjustments applied to sky and water)
    5. Contrast increased (S-curve applied to forest area)

    Expected layers in XCF (in order from bottom to top):
    - Background (original image layer)
    - Sky_Blue (Free Select + Hue-Saturation: Blue +35)
    - Water_Reflection (Hue-Saturation: +25)
    - Forest_Contrast (Curves: S-curve, 18% contrast)
    - Grass_Vibrant (Color Balance: Green +20, Yellow +10)
    - Vignette (Elliptical Select + Feather 90px + black 22% opacity)
    - Text_Title ("SERENE LAKE", 38px, #ffffff, top-center)
    - Text_Location ("THE NEEDLE", 22px, #87ceeb, bottom-right)
    - Frame (10px border #2e8b57)

    Args:
        result_paths: List of [jpeg_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels (default 1600)

    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0

    jpeg_path = result_paths[0]   # lake_masterpiece.jpg
    xcf_path = result_paths[1]    # lake_project.xcf
    src_path = result_paths[2]    # nicolagiordano-the-needle-3400239_1920.jpg (source)

    scores = []

    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")

    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist

    # Check 2: JPEG format
    is_jpeg = check_jpeg_format(jpeg_path)
    scores.append(is_jpeg)
    logger.info(f"Check 2 - JPEG format: {is_jpeg}")

    # Check 3: Correct width (1600px, height auto)
    width_ok = check_image_dimensions(jpeg_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width ({expected_width}px): {width_ok}")

    # Check 4: XCF file exists with all expected layers
    expected_layers = [
        'Sky_Blue',
        'Water_Reflection',
        'Forest_Contrast',
        'Grass_Vibrant',
        'Vignette',
        'Text_Title',
        'Text_Location',
        'Frame'
    ]
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with layers {expected_layers}: {xcf_ok}")

    # Check 5: Saturation increased (if source exists)
    # The task involves multiple saturation adjustments (Blue +35, Water +25)
    # so overall saturation should increase
    if src_path and os.path.exists(src_path):
        sat_ok = check_saturation_increase(src_path, jpeg_path, min_increase_percent=5.0)
        scores.append(sat_ok)
        logger.info(f"Check 5 - Saturation increase: {sat_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping saturation check")

    # Check 6: Contrast increased (if source exists)
    # The task specifies 18% contrast increase via S-curve
    if src_path and os.path.exists(src_path):
        cont_ok = check_contrast_increase(src_path, jpeg_path, min_increase_percent=10.0)
        scores.append(cont_ok)
        logger.info(f"Check 6 - Contrast increase: {cont_ok}")
    else:
        logger.warning(f"Source file not found: {src_path}, skipping contrast check")

    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Lake landscape complete: scores={scores}, final={final_score:.2f}")

    return final_score


def check_beach_footprint_art_complete(
    result_paths: list,
    expected_width: int = 1200
) -> float:
    """
    Comprehensive check for the beach footprint artistic enhancement workflow task.

    This function checks multiple aspects of the completed task:
    1. Exported JPEG file exists and is JPEG format
    2. JPEG has correct width (1200px, quality 90)
    3. XCF project file exists with all expected layers
    4. Image contains text patterns (Text_Title and Text_Date)
    5. Image contains expected colors (sand beige, sky blue, gold)
    6. Image has been artistically enhanced from source

    Expected layers in XCF (in order from bottom to top):
    - Background (original image layer)
    - Sand_Texture (solid color #c2b280)
    - Footprint_Select (footprint cutout)
    - Footprint_Shadow (blurred shadow, 40% opacity)
    - Footprint_Glow (blue glow, Screen mode, 50% opacity)
    - Decor_Shells (3 decorative elements: star, circle, heart)
    - Vignette (elliptical feather 60px, 30% opacity)
    - Text_Title ("SUMMER MEMORIES", 32px, white)
    - Text_Date ("2024", 24px, gold)
    - Frame (8px border #deb887)

    Args:
        result_paths: List of [jpeg_file_path, xcf_file_path, source_file_path]
        expected_width: Expected output width in pixels (default 1200)

    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0

    jpeg_path = result_paths[0]   # beach_footprint_art.jpg
    xcf_path = result_paths[1]    # footprint_project.xcf
    src_path = result_paths[2]    # memorycatcher-footprint-347817_1920.jpg (source)

    scores = []

    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")

    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0  # Cannot continue if output file doesn't exist

    # Check 2: JPEG format
    is_jpeg = check_jpeg_format(jpeg_path)
    scores.append(is_jpeg)
    logger.info(f"Check 2 - JPEG format: {is_jpeg}")

    # Check 3: Correct width (1200px, height auto)
    width_ok = check_image_dimensions(jpeg_path, expected_width)
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct width ({expected_width}px): {width_ok}")

    # Check 4: XCF file exists with all expected layers
    expected_layers = [
        'Footprint_Select',
        'Sand_Texture',
        'Footprint_Shadow',
        'Footprint_Glow',
        'Decor_Shells',
        'Vignette',
        'Text_Title',
        'Text_Date',
        'Frame'
    ]
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with layers {expected_layers}: {xcf_ok}")

    # Check 5: Text patterns exist (Text_Title "SUMMER MEMORIES" and Text_Date "2024")
    text_ok = check_text_in_image(jpeg_path, "SUMMER")
    scores.append(text_ok)
    logger.info(f"Check 5 - Text patterns: {text_ok}")

    # Check 6: Image contains expected colors (sand beige, sky blue, gold, pink)
    # The task specifies multiple colors: #c2b280 (sand), #87ceeb (sky blue), 
    # #ffd700 (gold), #ff69b4 (pink), #deb887 (burlywood)
    expected_colors = ['#c2b280', '#87ceeb', '#ffd700']  # Sand, sky blue, gold
    colors_ok = check_gradient_colors(jpeg_path, expected_colors, tolerance=50)
    scores.append(colors_ok)
    logger.info(f"Check 6 - Expected colors (sand/blue/gold): {colors_ok}")

    # Check 7: Image has been artistically enhanced from source
    if src_path and os.path.exists(src_path):
        try:
            src_img = Image.open(src_path)
            jpeg_img = Image.open(jpeg_path)

            # Compare overall properties (artistic enhancement should change appearance)
            src_brightness = calculate_brightness(src_img)
            jpeg_brightness = calculate_brightness(jpeg_img)
            brightness_changed = abs(jpeg_brightness - src_brightness) > 5

            src_saturation = calculate_saturation(src_img)
            jpeg_saturation = calculate_saturation(jpeg_img)
            
            # Artistic enhancement typically increases saturation
            saturation_changed = jpeg_saturation > src_saturation * 0.95

            enhancement_applied = brightness_changed or saturation_changed
            scores.append(1 if enhancement_applied else 0)
            logger.info(f"Check 7 - Enhancement applied: {enhancement_applied}")
        except Exception as e:
            logger.warning(f"Could not check enhancement: {e}")
            scores.append(0)
    else:
        logger.warning(f"Source file not found: {src_path}, skipping enhancement check")

    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Beach footprint art complete: scores={scores}, final={final_score:.2f}")

    return final_score
