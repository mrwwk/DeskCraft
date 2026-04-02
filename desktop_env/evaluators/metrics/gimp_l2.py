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


def _resolve_region_bbox(width: int, height: int, region_name: str):
    """Resolve a coarse named region to (x0, y0, x1, y1)."""
    w, h = width, height
    region = (region_name or "").lower().strip()
    if region == "top_left":
        return (0, 0, w // 3, h // 3)
    if region == "top_center":
        return (w // 3, 0, 2 * w // 3, h // 3)
    if region == "top_right":
        return (2 * w // 3, 0, w, h // 3)
    if region == "bottom_left":
        return (0, 2 * h // 3, w // 3, h)
    if region == "bottom_center":
        return (w // 3, 2 * h // 3, 2 * w // 3, h)
    if region == "bottom_right":
        return (2 * w // 3, 2 * h // 3, w, h)
    if region == "center":
        return (w // 4, h // 4, 3 * w // 4, 3 * h // 4)
    if region == "left":
        return (0, 0, w // 3, h)
    if region == "right":
        return (2 * w // 3, 0, w, h)
    if region == "top":
        return (0, 0, w, h // 4)
    if region == "bottom":
        return (0, 3 * h // 4, w, h)
    return (0, 0, w, h)


def _edge_density(gray_array: np.ndarray, edge_threshold: float = 40.0) -> float:
    gx = np.abs(np.gradient(gray_array, axis=1))
    gy = np.abs(np.gradient(gray_array, axis=0))
    edges = gx + gy
    return float(np.mean(edges > edge_threshold))


def _compute_sharpness_score(image: Image.Image) -> float:
    gray = np.array(image.convert('L'), dtype=np.float32)
    gx = np.gradient(gray, axis=1)
    gy = np.gradient(gray, axis=0)
    grad_mag = np.sqrt(gx * gx + gy * gy)
    return float(np.var(grad_mag))


def _to_rgb_array(image: Image.Image) -> np.ndarray:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return np.array(image)


def _build_foreground_mask(image: Image.Image, white_threshold: int = 245, alpha_threshold: int = 40) -> np.ndarray:
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


def check_image_file_size_range(image_path: str, rule: dict) -> int:
    """
    Check whether image file size is in [min_size, max_size].

    rule:
      - min_size (optional, bytes)
      - max_size (optional, bytes)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    min_size = int(rule.get("min_size", 0)) if rule else 0
    max_size = int(rule.get("max_size", 10 ** 18)) if rule else 10 ** 18

    try:
        size = os.path.getsize(image_path)
        ok = (size >= min_size) and (size <= max_size)
        logger.info(
            f"File size range check: size={size}, min={min_size}, max={max_size}, pass={ok}"
        )
        return 1 if ok else 0
    except Exception as e:
        logger.error(f"Error checking file size range: {e}")
        return 0


def check_xcf_layers_structure(xcf_path: str, rule: dict) -> int:
    """
    Check XCF file layer structure with optional order constraints.

    rule:
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
            layer_names = [getattr(layer, 'name', '') for layer in getattr(xcf, 'layers', [])]
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


def check_text_in_region_keywords(image_path: str, rule: dict) -> int:
    """
    Check text-like patterns (and optional OCR keywords) in designated regions.

    rule:
      - regions: list[str], e.g. ["bottom_left", "bottom_center", "bottom_right"]
      - keywords: optional list[str]
      - min_edge_density: optional float, default 0.008
      - edge_threshold: optional float, default 40
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    regions = (rule or {}).get("regions", ["center"])
    keywords = (rule or {}).get("keywords", [])
    min_edge_density = float((rule or {}).get("min_edge_density", 0.008))
    edge_threshold = float((rule or {}).get("edge_threshold", 40.0))

    try:
        img = Image.open(image_path)
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        # Region-level text pattern checks.
        for region_name in regions:
            x0, y0, x1, y1 = _resolve_region_bbox(w, h, region_name)
            crop = gray[y0:y1, x0:x1]
            if crop.size == 0:
                logger.info(f"Empty region for text check: {region_name}")
                return 0
            density = _edge_density(crop, edge_threshold=edge_threshold)
            if density < min_edge_density:
                logger.info(
                    f"Text-like edge density too low: region={region_name}, density={density:.4f}, "
                    f"required={min_edge_density:.4f}"
                )
                return 0

        if keywords:
            # Optional OCR pass; if unavailable, region checks above are used.
            try:
                import pytesseract

                full_text = pytesseract.image_to_string(img)
                normalized = re.sub(r'\s+', ' ', full_text).strip().lower()
                for kw in keywords:
                    if kw.lower() not in normalized:
                        logger.info(f"OCR keyword missing: {kw}")
                        return 0
            except Exception as ocr_e:
                logger.warning(f"OCR unavailable or failed in check_text_in_region_keywords: {ocr_e}")

        return 1
    except Exception as e:
        logger.error(f"Error checking text in region keywords: {e}")
        return 0


def check_text_keywords_simple_ocr(image_path: str, rule: dict) -> int:
    """
    Lightweight OCR keyword check with deterministic fallback.

    rule:
      - keywords: required list[str]
      - region: optional named region
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    keywords = (rule or {}).get("keywords", [])
    region = (rule or {}).get("region")

    if not keywords:
        logger.warning("check_text_keywords_simple_ocr: no keywords provided")
        return 0

    try:
        img = Image.open(image_path)

        if region:
            gray = np.array(img.convert('L'))
            h, w = gray.shape
            x0, y0, x1, y1 = _resolve_region_bbox(w, h, region)
            img = img.crop((x0, y0, x1, y1))

        try:
            import pytesseract

            text = pytesseract.image_to_string(img)
            norm = re.sub(r'\s+', ' ', text).strip().lower()
            ok = all(kw.lower() in norm for kw in keywords)
            logger.info(f"Simple OCR keyword check: keywords={keywords}, pass={ok}")
            return 1 if ok else 0
        except Exception as ocr_e:
            logger.warning(f"OCR unavailable, fallback to edge heuristic: {ocr_e}")
            # Fallback to region text pattern existence.
            fallback_rule = {
                "regions": [region] if region else ["center"],
                "keywords": [],
                "min_edge_density": float((rule or {}).get("min_edge_density", 0.01)),
                "edge_threshold": float((rule or {}).get("edge_threshold", 40.0)),
            }
            return check_text_in_region_keywords(image_path, fallback_rule)
    except Exception as e:
        logger.error(f"Error in check_text_keywords_simple_ocr: {e}")
        return 0


def check_subject_scale_and_center(image_path: str, rule: dict) -> int:
    """
    Check subject size ratio and center alignment for product-style composition.

    rule:
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
        bbox_w = x1 - x0 + 1
        height_ratio = bbox_h / float(h)

        center_x = (x0 + x1) / 2.0
        center_y = (y0 + y1) / 2.0

        dx_ratio = abs(center_x - (w / 2.0)) / float(w)
        dy_ratio = abs(center_y - (h / 2.0)) / float(h)

        # Vertical tolerance is relaxed because product centering is usually horizontal-first.
        pass_height = min_height_ratio <= height_ratio <= max_height_ratio
        pass_center = (dx_ratio <= center_tolerance_ratio) and (dy_ratio <= center_tolerance_ratio * 1.8)

        passed = pass_height and pass_center
        logger.info(
            "Subject scale/center: "
            f"bbox={bbox_w}x{bbox_h}, height_ratio={height_ratio:.4f}, "
            f"dx_ratio={dx_ratio:.4f}, dy_ratio={dy_ratio:.4f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking subject scale and center: {e}")
        return 0


def check_soft_shadow_presence(image_path: str, rule: dict) -> int:
    """
    Check soft shadow existence below primary subject.

    rule:
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


def check_white_background_ratio(image_path: str, rule: dict) -> int:
    """
    Check if image has dominant white background.

    rule:
      - white_threshold (default 245)
      - min_ratio (default 0.9)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    white_threshold = int(cfg.get("white_threshold", 245))
    min_ratio = float(cfg.get("min_ratio", 0.9))

    try:
        img = Image.open(image_path).convert('RGB')
        arr = np.array(img)
        white_mask = np.all(arr >= white_threshold, axis=2)
        ratio = float(np.mean(white_mask))
        passed = ratio >= min_ratio
        logger.info(
            f"White background ratio: ratio={ratio:.4f}, min={min_ratio:.4f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking white background ratio: {e}")
        return 0


def check_three_column_layout_balance(image_path: str, rule: dict) -> int:
    """
    Check if three-column layout is roughly balanced.

    rule:
      - columns (default 3)
      - min_foreground_ratio (default 0.02)
      - max_ratio_between_columns (default 2.2)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    columns = int(cfg.get("columns", 3))
    min_foreground_ratio = float(cfg.get("min_foreground_ratio", 0.02))
    max_ratio_between_columns = float(cfg.get("max_ratio_between_columns", 2.2))

    try:
        img = Image.open(image_path)
        mask = _build_foreground_mask(img)
        h, w = mask.shape

        if columns <= 1:
            return 0

        ratios = []
        for i in range(columns):
            x0 = int(i * w / columns)
            x1 = int((i + 1) * w / columns)
            col = mask[:, x0:x1]
            if col.size == 0:
                return 0
            ratios.append(float(np.mean(col)))

        if any(r < min_foreground_ratio for r in ratios):
            logger.info(
                f"Three-column layout: low foreground ratio in columns {ratios}, min={min_foreground_ratio}"
            )
            return 0

        r_min = min(ratios)
        r_max = max(ratios)
        if r_min <= 1e-6:
            return 0

        balanced = (r_max / r_min) <= max_ratio_between_columns
        logger.info(f"Three-column layout ratios={ratios}, balanced={balanced}")
        return 1 if balanced else 0
    except Exception as e:
        logger.error(f"Error checking three-column layout: {e}")
        return 0


def check_top_title_bar_and_text(image_path: str, rule: dict) -> int:
    """
    Check top title bar presence and text-like signal.

    rule:
      - bar_min_ratio (default 0.12)
      - bar_max_ratio (default 0.22)
      - min_darkness_delta (default 10)
      - min_edge_density (default 0.01)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    bar_min_ratio = float(cfg.get("bar_min_ratio", 0.12))
    bar_max_ratio = float(cfg.get("bar_max_ratio", 0.22))
    min_darkness_delta = float(cfg.get("min_darkness_delta", 10.0))
    min_edge_density = float(cfg.get("min_edge_density", 0.01))

    try:
        img = Image.open(image_path)
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        bar_h = int(h * ((bar_min_ratio + bar_max_ratio) / 2.0))
        bar_h = max(20, min(h // 2, bar_h))

        top = gray[:bar_h, :]
        mid0 = h // 3
        mid1 = min(h, mid0 + bar_h)
        middle = gray[mid0:mid1, :]

        if top.size == 0 or middle.size == 0:
            return 0

        mean_top = float(np.mean(top))
        mean_middle = float(np.mean(middle))
        darkness_ok = (mean_middle - mean_top) >= min_darkness_delta

        edge_top = _edge_density(top, edge_threshold=40.0)
        text_like_ok = edge_top >= min_edge_density

        passed = darkness_ok and text_like_ok
        logger.info(
            f"Top title bar check: mean_top={mean_top:.2f}, mean_mid={mean_middle:.2f}, "
            f"darkness_ok={darkness_ok}, edge_top={edge_top:.4f}, text_like_ok={text_like_ok}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking top title bar and text: {e}")
        return 0


def check_safe_margin_layout(image_path: str, rule: dict) -> int:
    """
    Check whether both side outer margins are relatively clean.

    rule:
      - margin_px (default 60)
      - max_outer_to_inner_ratio (default 1.2)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    margin_px = int(cfg.get("margin_px", 60))
    max_outer_to_inner_ratio = float(cfg.get("max_outer_to_inner_ratio", 1.2))

    try:
        img = Image.open(image_path)
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        if w < margin_px * 3:
            logger.warning("Image too narrow for safe margin check, fallback pass")
            return 1

        outer_l = gray[:, :margin_px]
        outer_r = gray[:, w - margin_px:]

        inner_l0 = min(w, margin_px)
        inner_l1 = min(w, margin_px * 2)
        inner_r0 = max(0, w - margin_px * 2)
        inner_r1 = max(0, w - margin_px)
        inner_l = gray[:, inner_l0:inner_l1]
        inner_r = gray[:, inner_r0:inner_r1]

        outer_density = (_edge_density(outer_l) + _edge_density(outer_r)) / 2.0
        inner_density = (_edge_density(inner_l) + _edge_density(inner_r)) / 2.0

        if inner_density < 1e-4:
            return 1

        ratio = outer_density / inner_density
        passed = ratio <= max_outer_to_inner_ratio
        logger.info(
            f"Safe margin check: outer_density={outer_density:.4f}, inner_density={inner_density:.4f}, "
            f"ratio={ratio:.3f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking safe margin layout: {e}")
        return 0


def check_icon_presence_region(image_path: str, rule: dict) -> int:
    """
    Check whether designated region contains icon-like high-frequency signal.

    rule:
      - region: named region OR
      - bbox: [x0, y0, x1, y1]
      - min_edge_density (default 0.02)
      - min_color_std (default 15)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    min_edge_density = float(cfg.get("min_edge_density", 0.02))
    min_color_std = float(cfg.get("min_color_std", 15.0))

    try:
        img = Image.open(image_path)
        rgb = _to_rgb_array(img)
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        if "bbox" in cfg and isinstance(cfg["bbox"], (list, tuple)) and len(cfg["bbox"]) == 4:
            x0, y0, x1, y1 = [int(v) for v in cfg["bbox"]]
            x0, y0 = max(0, x0), max(0, y0)
            x1, y1 = min(w, x1), min(h, y1)
        else:
            x0, y0, x1, y1 = _resolve_region_bbox(w, h, cfg.get("region", "bottom_left"))

        crop_gray = gray[y0:y1, x0:x1]
        crop_rgb = rgb[y0:y1, x0:x1, :]

        if crop_gray.size == 0:
            return 0

        edge_d = _edge_density(crop_gray, edge_threshold=45.0)
        color_std = float(np.mean(np.std(crop_rgb.reshape(-1, 3), axis=0))) if crop_rgb.size else 0.0

        passed = (edge_d >= min_edge_density) and (color_std >= min_color_std)
        logger.info(
            f"Icon region check: edge_density={edge_d:.4f}, color_std={color_std:.2f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking icon presence region: {e}")
        return 0


def check_sharpness_increase(src_path: str, tgt_path: str, min_increase_percent: float = 5.0) -> int:
    """Check whether target image sharpness increases by a minimum percentage."""
    if src_path is None or tgt_path is None:
        return 0
    if not os.path.exists(src_path) or not os.path.exists(tgt_path):
        logger.error(f"Image file not found: src={src_path}, tgt={tgt_path}")
        return 0

    try:
        src_img = Image.open(src_path)
        tgt_img = Image.open(tgt_path)

        src_sharp = _compute_sharpness_score(src_img)
        tgt_sharp = _compute_sharpness_score(tgt_img)

        if src_sharp <= 1e-9:
            return 0

        increase_percent = (tgt_sharp - src_sharp) * 100.0 / src_sharp
        passed = increase_percent >= float(min_increase_percent)
        logger.info(
            f"Sharpness increase: src={src_sharp:.4f}, tgt={tgt_sharp:.4f}, "
            f"increase={increase_percent:.2f}%, min={min_increase_percent:.2f}%, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking sharpness increase: {e}")
        return 0


def check_perspective_overlay_region(src_path: str, tgt_path: str, polygon: list = None, min_change_ratio: float = 0.15) -> int:
    """
    Check whether a polygon region was substantially changed (for perspective billboard replacement).

    polygon: list of [x, y] points. If None, defaults to a central-upper-right quadrilateral.
    """
    if src_path is None or tgt_path is None:
        return 0
    if not os.path.exists(src_path) or not os.path.exists(tgt_path):
        logger.error(f"Image file not found: src={src_path}, tgt={tgt_path}")
        return 0

    try:
        src = np.array(Image.open(src_path).convert('RGB'))
        tgt = np.array(Image.open(tgt_path).convert('RGB'))

        if src.shape != tgt.shape:
            # Resize src to tgt for robust diff.
            src_img = Image.fromarray(src).resize((tgt.shape[1], tgt.shape[0]))
            src = np.array(src_img)

        h, w = tgt.shape[:2]

        if not polygon:
            polygon = [
                [int(0.50 * w), int(0.18 * h)],
                [int(0.74 * w), int(0.18 * h)],
                [int(0.76 * w), int(0.48 * h)],
                [int(0.48 * w), int(0.50 * h)],
            ]

        # Rasterize polygon mask via PIL draw.
        mask_img = Image.new('L', (w, h), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(mask_img).polygon([tuple(p) for p in polygon], outline=1, fill=1)
        mask = np.array(mask_img, dtype=bool)

        if np.sum(mask) < 50:
            logger.info("Perspective region mask too small")
            return 0

        diff = np.mean(np.abs(src.astype(np.float32) - tgt.astype(np.float32)), axis=2)
        region_diff = diff[mask]
        outside_diff = diff[~mask]

        if region_diff.size == 0:
            return 0

        # Pixels with visible change.
        changed_ratio = float(np.mean(region_diff > 18.0))
        outside_ratio = float(np.mean(outside_diff > 18.0)) if outside_diff.size else 0.0

        passed = (changed_ratio >= float(min_change_ratio)) and (changed_ratio > outside_ratio)
        logger.info(
            f"Perspective overlay check: changed_ratio={changed_ratio:.4f}, "
            f"outside_ratio={outside_ratio:.4f}, min={min_change_ratio:.4f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking perspective overlay region: {e}")
        return 0


def check_annotation_callout_count(src_path: str, tgt_path: str, min_callouts: int = 3) -> int:
    """
    Approximate annotation count check by counting separated changed clusters.
    """
    if src_path is None or tgt_path is None:
        return 0
    if not os.path.exists(src_path) or not os.path.exists(tgt_path):
        logger.error(f"Image file not found: src={src_path}, tgt={tgt_path}")
        return 0

    try:
        src = np.array(Image.open(src_path).convert('L'))
        tgt = np.array(Image.open(tgt_path).convert('L'))

        if src.shape != tgt.shape:
            src_img = Image.fromarray(src).resize((tgt.shape[1], tgt.shape[0]))
            src = np.array(src_img)

        diff = np.abs(tgt.astype(np.float32) - src.astype(np.float32))
        changed = diff > 20

        # Focus upper/middle area for callouts and arrows.
        h, w = changed.shape
        roi = changed[: int(0.85 * h), :]

        # Connected components via skimage (already dependency in this module).
        from skimage.measure import label, regionprops

        labeled = label(roi.astype(np.uint8), connectivity=2)
        props = regionprops(labeled)

        # Filter tiny noise and giant full-screen changes.
        valid = [p for p in props if 80 <= p.area <= 0.08 * roi.size]
        count = len(valid)

        # A soft check: at least min_callouts clusters.
        passed = count >= int(min_callouts)
        logger.info(f"Annotation callout count: detected={count}, min={min_callouts}, pass={passed}")
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking annotation callout count: {e}")
        return 0


def check_split_before_after_layout(src_path: str, tgt_path: str, split_ratio: float = 0.5,
                                    min_right_change_ratio: float = 0.08,
                                    max_left_change_ratio: float = 0.03) -> int:
    """
    Verify before/after split layout.

    Validation strategy:
    1. Detect a visible divider near the expected split position.
    2. Ensure left/right halves are related but not identical.
    3. If source is available, one half should be closer to source than the other.

    Notes:
    - `max_left_change_ratio` is interpreted as the minimum required similarity gap
      between source-vs-left and source-vs-right comparisons.
    """
    if tgt_path is None or not os.path.exists(tgt_path):
        logger.error(f"Image file not found: tgt={tgt_path}")
        return 0

    try:
        tgt = np.array(Image.open(tgt_path).convert('RGB'))
        h, w = tgt.shape[:2]

        split_x = int(w * float(split_ratio))
        split_x = max(1, min(w - 1, split_x))

        left = tgt[:, :split_x, :]
        right = tgt[:, split_x:, :]
        if left.size == 0 or right.size == 0:
            return 0

        # Align widths if odd split caused 1px mismatch.
        common_w = min(left.shape[1], right.shape[1])
        left = left[:, :common_w, :]
        right = right[:, :common_w, :]

        # Left/right difference: should not be almost identical.
        lr_diff = np.mean(np.abs(left.astype(np.float32) - right.astype(np.float32)), axis=2)
        lr_change_ratio = float(np.mean(lr_diff > 12.0))

        left_gray = np.array(Image.fromarray(left).convert('L'))
        right_gray = np.array(Image.fromarray(right).convert('L'))
        lr_ssim = float(ssim(left_gray, right_gray, data_range=255))

        # Divider check around split location.
        band_w = max(2, int(0.01 * w))
        l0 = max(0, split_x - band_w)
        l1 = min(w, split_x + band_w)
        divider_band = np.array(Image.fromarray(tgt).convert('L'))[:, l0:l1]
        divider_edge = _edge_density(divider_band, edge_threshold=45.0) if divider_band.size else 0.0

        # Base layout checks independent of source image.
        base_pass = (
            lr_change_ratio >= float(min_right_change_ratio)
            and lr_ssim >= 0.35
            and lr_ssim <= 0.995
            and divider_edge >= 0.008
        )

        if not base_pass:
            logger.info(
                f"Split layout base check failed: lr_change={lr_change_ratio:.4f}, "
                f"lr_ssim={lr_ssim:.4f}, divider_edge={divider_edge:.4f}"
            )
            return 0

        # Optional source consistency check.
        if src_path is not None and os.path.exists(src_path):
            src = np.array(Image.open(src_path).convert('RGB'))
            src_resized = np.array(
                Image.fromarray(src).resize((common_w, h), resample=Image.BICUBIC).convert('L')
            )
            ssim_left_src = float(ssim(src_resized, left_gray, data_range=255))
            ssim_right_src = float(ssim(src_resized, right_gray, data_range=255))
            sim_gap = abs(ssim_left_src - ssim_right_src)

            # At least one side should plausibly correspond to the original.
            if max(ssim_left_src, ssim_right_src) < 0.3:
                logger.info(
                    f"Split layout source check failed: ssim_left_src={ssim_left_src:.4f}, "
                    f"ssim_right_src={ssim_right_src:.4f}"
                )
                return 0

            if sim_gap < float(max_left_change_ratio):
                logger.info(
                    f"Split layout source similarity gap too small: gap={sim_gap:.4f}, "
                    f"required={float(max_left_change_ratio):.4f}"
                )
                return 0

            logger.info(
                f"Split before/after pass: lr_change={lr_change_ratio:.4f}, lr_ssim={lr_ssim:.4f}, "
                f"divider_edge={divider_edge:.4f}, ssim_left_src={ssim_left_src:.4f}, "
                f"ssim_right_src={ssim_right_src:.4f}, sim_gap={sim_gap:.4f}"
            )
            return 1

        logger.info(
            f"Split before/after pass (without src): lr_change={lr_change_ratio:.4f}, "
            f"lr_ssim={lr_ssim:.4f}, divider_edge={divider_edge:.4f}"
        )
        return 1
    except Exception as e:
        logger.error(f"Error checking split before-after layout: {e}")
        return 0


def check_three_panel_tutorial_layout(image_path: str, rule: dict) -> int:
    """
    Check three-panel tutorial layout via vertical edge concentration near panel boundaries.

    rule:
      - columns (default 3)
      - tolerance_px (default 25)
      - min_boundary_edge_density (default 0.012)
      - regions/keywords (optional, for title checks)
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0

    cfg = rule or {}
    columns = int(cfg.get("columns", 3))
    tolerance_px = int(cfg.get("tolerance_px", 25))
    min_boundary_edge_density = float(cfg.get("min_boundary_edge_density", 0.012))

    try:
        img = Image.open(image_path)
        gray = np.array(img.convert('L'))
        h, w = gray.shape

        if columns < 2:
            return 0

        # Check expected divider neighborhoods.
        for i in range(1, columns):
            x = int(i * w / columns)
            x0 = max(0, x - tolerance_px)
            x1 = min(w, x + tolerance_px)
            band = gray[:, x0:x1]
            if band.size == 0:
                return 0
            d = _edge_density(band, edge_threshold=40.0)
            if d < min_boundary_edge_density:
                logger.info(
                    f"Panel boundary weak: idx={i}, edge_density={d:.4f}, "
                    f"required={min_boundary_edge_density:.4f}"
                )
                return 0

        # Optional title keywords check.
        keywords = cfg.get("keywords", [])
        if keywords:
            text_rule = {
                "regions": cfg.get("regions", ["top_left", "top_center", "top_right"]),
                "keywords": keywords,
                "min_edge_density": cfg.get("min_title_edge_density", 0.008),
            }
            if check_text_in_region_keywords(image_path, text_rule) == 0:
                return 0

        return 1
    except Exception as e:
        logger.error(f"Error checking three-panel tutorial layout: {e}")
        return 0


def _mean_binary_score(scores: list) -> float:
    valid = [float(s) for s in scores if s is not None]
    return sum(valid) / len(valid) if valid else 0.0


def _all_binary_checks_pass(scores: list) -> float:
    """Return 1.0 only when all binary checks pass, otherwise 0.0."""
    valid = [float(s) for s in scores if s is not None]
    if not valid:
        return 0.0
    return 1.0 if all(v >= 1.0 for v in valid) else 0.0


def check_l2_perfume_listing_complete(result_paths: list) -> float:
    """Composite evaluator for L2-1 perfume transparent listing task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l2_perfume_listing_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path, _src_path = result_paths[:3]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_transparency_exists(png_path),
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


def check_l2_watch_white_standard_complete(result_paths: list) -> float:
    """Composite evaluator for L2-2 watch white-background standard task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l2_watch_white_standard_complete invalid result_paths: {result_paths}")
        return 0.0

    jpg_path, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(jpg_path),
        check_jpeg_format(jpg_path),
        check_image_dimensions(jpg_path, 1600, 1600),
        check_image_file_size_range(jpg_path, {"max_size": 460800}),
        check_white_background_ratio(jpg_path, {"white_threshold": 245, "min_ratio": 0.9}),
        check_soft_shadow_presence(jpg_path, {"min_shadow_ratio": 0.004}),
        check_contrast_increase(src_path, jpg_path, min_increase_percent=8.0),
        check_xcf_layers_structure(
            xcf_path,
            {"layers": ["Watch_Main", "Shadow_Soft", "BG_White"], "ordered": False},
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_city_night_run_cover_complete(result_paths: list) -> float:
    """Composite evaluator for L2-4 city night run cover task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l2_city_night_run_cover_complete invalid result_paths: {result_paths}")
        return 0.0

    jpg_path, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(jpg_path),
        check_jpeg_format(jpg_path),
        check_image_dimensions(jpg_path, 1080, 1440),
        check_image_file_size_range(jpg_path, {"max_size": 716800}),
        check_contrast_increase(src_path, jpg_path, min_increase_percent=10.0),
        check_saturation_increase(src_path, jpg_path, min_increase_percent=10.0),
        check_top_title_bar_and_text(
            jpg_path,
            {
                "bar_min_ratio": 0.12,
                "bar_max_ratio": 0.22,
                "min_darkness_delta": 8,
                "min_edge_density": 0.008,
            },
        ),
        check_text_in_region_keywords(
            jpg_path,
            {"regions": ["top_center"], "keywords": ["CITY NIGHT RUN"], "min_edge_density": 0.006},
        ),
        check_xcf_layers_structure(
            xcf_path,
            {"layers": ["BG_City", "Title_Bar", "Title_Text"], "ordered": False},
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_wechat_header_mountain_complete(result_paths: list) -> float:
    """Composite evaluator for L2-5 wechat header task."""
    if not isinstance(result_paths, list) or len(result_paths) < 2:
        logger.error(f"check_l2_wechat_header_mountain_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path = result_paths[:2]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 900, 383),
        check_safe_margin_layout(
            png_path,
            {"margin_px": 60, "max_outer_to_inner_ratio": 1.25},
        ),
        check_icon_presence_region(
            png_path,
            {
                "region": "bottom_left",
                "min_edge_density": 0.015,
                "min_color_std": 8.0,
            },
        ),
        check_text_in_region_keywords(
            png_path,
            {
                "regions": ["bottom_right"],
                "keywords": ["WEEKEND ESCAPE"],
                "min_edge_density": 0.006,
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {"layers": ["BG_Mountain", "Logo_Icon", "Caption_Text"], "ordered": False},
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_avatar_refined_complete(result_paths: list) -> float:
    """Composite evaluator for L2-6 avatar dual-format delivery task."""
    if not isinstance(result_paths, list) or len(result_paths) < 4:
        logger.error(f"check_l2_avatar_refined_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, jpg_path, xcf_path, src_path = result_paths[:4]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 1024, 1024),
        check_file_exists(jpg_path),
        check_jpeg_format(jpg_path),
        check_image_dimensions(jpg_path, 1024, 1024),
        check_image_file_size_range(jpg_path, {"max_size": 256000}),
        check_contrast_increase(src_path, jpg_path, min_increase_percent=5.0),
        check_sharpness_increase(src_path, jpg_path, min_increase_percent=1.5),
        check_file_exists(xcf_path),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_camera_metal_poster_complete(result_paths: list) -> float:
    """Composite evaluator for L2-7 camera metal poster base task."""
    if not isinstance(result_paths, list) or len(result_paths) < 2:
        logger.error(f"check_l2_camera_metal_poster_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path = result_paths[:2]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 1600, 1000),
        check_icon_presence_region(
            png_path,
            {
                "region": "right",
                "min_edge_density": 0.018,
                "min_color_std": 12.0,
            },
        ),
        check_text_in_region_keywords(
            png_path,
            {
                "regions": ["top_left", "top_center"],
                "keywords": ["PRO SHOOT"],
                "min_edge_density": 0.006,
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["BG_Metal", "Camera_Main", "Shadow", "Vignette", "Title"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_street_billboard_mockup_complete(result_paths: list) -> float:
    """Composite evaluator for L2-8 billboard perspective replacement task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l2_street_billboard_mockup_complete invalid result_paths: {result_paths}")
        return 0.0

    jpg_path, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(jpg_path),
        check_jpeg_format(jpg_path),
        check_image_dimensions(jpg_path, 2200, 1365),
        check_perspective_overlay_region(
            src_path,
            jpg_path,
            polygon=[[1130, 260], [1580, 250], [1600, 620], [1100, 640]],
            min_change_ratio=0.14,
        ),
        check_text_in_region_keywords(
            jpg_path,
            {"regions": ["top_right"], "keywords": ["CITY DEALS"], "min_edge_density": 0.006},
        ),
        check_xcf_layers_structure(
            xcf_path,
            {"layers": ["Billboard_Art", "Billboard_Text", "Billboard_Composite"], "ordered": False},
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_beach_event_poster_complete(result_paths: list) -> float:
    """Composite evaluator for L2-9 beach event poster task."""
    if not isinstance(result_paths, list) or len(result_paths) < 2:
        logger.error(f"check_l2_beach_event_poster_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path = result_paths[:2]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 1200, 1800),
        check_text_in_region_keywords(
            png_path,
            {
                "regions": ["top_center", "center", "bottom_center"],
                "keywords": ["BEACH PARTY", "2026.08.16", "SANYA COAST"],
                "min_edge_density": 0.006,
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["BG_Group", "Photo_Group", "Text_Group", "Deco_Group"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l2_camera_annotation_complete(result_paths: list) -> float:
    """Composite evaluator for L2-10 camera annotation teaching asset task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l2_camera_annotation_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 2000, 1325),
        check_annotation_callout_count(src_path, png_path, min_callouts=3),
        check_text_in_region_keywords(
            png_path,
            {
                "regions": ["top_left", "top_right", "center"],
                "keywords": ["Lens", "Grip", "Mode Dial"],
                "min_edge_density": 0.006,
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["Base_Image", "Callout_1", "Callout_2", "Callout_3", "Footer_Note"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def _check_color_tone_consistency(image_a_path: str, image_b_path: str, max_mean_delta: float = 35.0) -> int:
    """Check whether two exports keep a roughly consistent global color tone."""
    if not image_a_path or not image_b_path:
        return 0
    if not os.path.exists(image_a_path) or not os.path.exists(image_b_path):
        return 0

    try:
        img_a = np.array(Image.open(image_a_path).convert('RGB'))
        img_b = np.array(Image.open(image_b_path).convert('RGB'))

        mean_a = np.mean(img_a.reshape(-1, 3), axis=0)
        mean_b = np.mean(img_b.reshape(-1, 3), axis=0)
        delta = float(np.mean(np.abs(mean_a - mean_b)))
        passed = delta <= float(max_mean_delta)
        logger.info(
            f"Color tone consistency: mean_a={mean_a}, mean_b={mean_b}, "
            f"delta={delta:.2f}, max={max_mean_delta:.2f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking color tone consistency: {e}")
        return 0


def _check_images_not_identical(image_a_path: str, image_b_path: str, min_diff_ratio: float = 0.03) -> int:
    """Check that two outputs are visually different enough."""
    if not image_a_path or not image_b_path:
        return 0
    if not os.path.exists(image_a_path) or not os.path.exists(image_b_path):
        return 0

    try:
        img_a = np.array(Image.open(image_a_path).convert('RGB'))
        img_b = np.array(Image.open(image_b_path).convert('RGB'))

        if img_a.shape != img_b.shape:
            img_a = np.array(
                Image.fromarray(img_a).resize((img_b.shape[1], img_b.shape[0]), resample=Image.BICUBIC)
            )

        diff = np.mean(np.abs(img_a.astype(np.float32) - img_b.astype(np.float32)), axis=2)
        diff_ratio = float(np.mean(diff > 12.0))
        passed = diff_ratio >= float(min_diff_ratio)
        logger.info(
            f"Image difference check: diff_ratio={diff_ratio:.4f}, "
            f"min_required={min_diff_ratio:.4f}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking image non-identity: {e}")
        return 0


def _check_infographic_step_modules(image_path: str, min_modules: int = 4) -> int:
    """
    Check that infographic contains at least `min_modules` horizontal bands
    with text-like content.
    """
    if not image_path or not os.path.exists(image_path):
        return 0

    try:
        gray = np.array(Image.open(image_path).convert('L'))
        h, w = gray.shape

        if min_modules <= 0:
            return 0

        detected = 0
        for i in range(min_modules):
            y0 = int(i * h / min_modules)
            y1 = int((i + 1) * h / min_modules)
            y1 = max(y1, y0 + 1)
            x0 = int(0.12 * w)
            x1 = int(0.88 * w)
            crop = gray[y0:y1, x0:x1]
            if crop.size == 0:
                continue

            # Require both texture edges and non-trivial intensity variation.
            edge_d = _edge_density(crop, edge_threshold=40.0)
            std_v = float(np.std(crop))
            if edge_d >= 0.007 and std_v >= 10.0:
                detected += 1

        passed = detected >= int(min_modules)
        logger.info(
            f"Infographic module check: detected={detected}, "
            f"required={min_modules}, pass={passed}"
        )
        return 1 if passed else 0
    except Exception as e:
        logger.error(f"Error checking infographic modules: {e}")
        return 0


def check_l3_city_music_poster_complete(result_paths: list) -> float:
    """Composite evaluator for L3-1 city music poster dual-format delivery."""
    if not isinstance(result_paths, list) or len(result_paths) < 4:
        logger.error(f"check_l3_city_music_poster_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, jpg_path, xcf_path, src_path = result_paths[:4]

    scores = [
        check_file_exists(png_path),
        check_file_exists(jpg_path),
        check_png_format(png_path),
        check_jpeg_format(jpg_path),
        check_image_dimensions(png_path, 2400, 3200),
        check_image_dimensions(jpg_path, 2400, 3200),
        check_image_file_size_range(jpg_path, {"max_size": 1048576}),
        check_text_in_region_keywords(
            png_path,
            {
                "regions": ["top_center", "center", "bottom_center"],
                "keywords": ["CITY MUSIC FEST", "LIVE", "NIGHT"],
                "min_edge_density": 0.006,
            },
        ),
        check_contrast_increase(src_path, jpg_path, min_increase_percent=6.0),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": [
                    "BG_Base",
                    "FX_Gradient",
                    "FX_Texture",
                    "Title_Main",
                    "Title_Sub",
                    "CTA",
                    "Frame",
                ],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_mag_cover_complete(result_paths: list) -> float:
    """Composite evaluator for L3-2 magazine portrait cover workflow."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l3_mag_cover_complete invalid result_paths: {result_paths}")
        return 0.0

    jpg_path, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(jpg_path),
        check_jpeg_format(jpg_path),
        check_image_dimensions(jpg_path, 1800, 2400),
        check_image_file_size_range(jpg_path, {"max_size": 921600}),
        check_text_in_region_keywords(
            jpg_path,
            {
                "regions": ["top_center", "left", "right", "bottom_center"],
                "keywords": ["STYLE", "ISSUE", "2026"],
                "min_edge_density": 0.007,
            },
        ),
        check_contrast_increase(src_path, jpg_path, min_increase_percent=3.0),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": [
                    "Masthead",
                    "Coverline_1",
                    "Coverline_2",
                    "Coverline_3",
                    "Date_Issue",
                    "Portrait_Base",
                    "Color_Grade",
                ],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_shoes_listing_complete(result_paths: list) -> float:
    """Composite evaluator for L3-4 shoes listing dual-output task."""
    if not isinstance(result_paths, list) or len(result_paths) < 4:
        logger.error(f"check_l3_shoes_listing_complete invalid result_paths: {result_paths}")
        return 0.0

    main_jpg, cutout_png, xcf_path, src_path = result_paths[:4]

    scores = [
        check_file_exists(main_jpg),
        check_file_exists(cutout_png),
        check_jpeg_format(main_jpg),
        check_png_format(cutout_png),
        check_image_dimensions(main_jpg, 1600, 1600),
        check_image_dimensions(cutout_png, 1600, 1600),
        check_image_file_size_range(main_jpg, {"max_size": 512000}),
        check_white_background_ratio(main_jpg, {"white_threshold": 245, "min_ratio": 0.78}),
        check_text_in_region_keywords(
            main_jpg,
            {"regions": ["top_left", "top_right"], "keywords": ["NEW"], "min_edge_density": 0.005},
        ),
        check_transparency_exists(cutout_png),
        check_subject_scale_and_center(
            cutout_png,
            {
                "min_height_ratio": 0.55,
                "max_height_ratio": 0.9,
                "center_tolerance_ratio": 0.18,
            },
        ),
        check_contrast_increase(src_path, main_jpg, min_increase_percent=3.0),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["Shoes_Product", "Shadow_Soft", "Badge_NEW", "BG_White"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_perfume_hero_complete(result_paths: list) -> float:
    """Composite evaluator for L3-5 perfume hero banner task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l3_perfume_hero_complete invalid result_paths: {result_paths}")
        return 0.0

    png_path, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(png_path),
        check_png_format(png_path),
        check_image_dimensions(png_path, 2200, 1400),
        check_text_in_region_keywords(
            png_path,
            {
                "regions": ["top_left", "top_center", "center"],
                "keywords": ["ESSENCE", "PREMIUM"],
                "min_edge_density": 0.006,
            },
        ),
        check_contrast_increase(src_path, png_path, min_increase_percent=5.0),
        check_saturation_increase(src_path, png_path, min_increase_percent=5.0),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": [
                    "Perfume_Main",
                    "BG_Concrete",
                    "BG_Metal",
                    "Light_Glow",
                    "Title",
                    "Subtitle",
                ],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_camera_detail_pack_complete(result_paths: list) -> float:
    """Composite evaluator for L3-6 camera detail 3-image pack task."""
    if not isinstance(result_paths, list) or len(result_paths) < 5:
        logger.error(f"check_l3_camera_detail_pack_complete invalid result_paths: {result_paths}")
        return 0.0

    main_jpg, closeup_jpg, specs_jpg, xcf_path, src_path = result_paths[:5]

    scores = [
        check_file_exists(main_jpg),
        check_file_exists(closeup_jpg),
        check_file_exists(specs_jpg),
        check_jpeg_format(main_jpg),
        check_jpeg_format(closeup_jpg),
        check_jpeg_format(specs_jpg),
        check_image_dimensions(main_jpg, 1600, 1600),
        check_image_dimensions(closeup_jpg, 1600, 1600),
        check_image_dimensions(specs_jpg, 1600, 1600),
        _check_color_tone_consistency(main_jpg, closeup_jpg, max_mean_delta=40.0),
        _check_color_tone_consistency(main_jpg, specs_jpg, max_mean_delta=45.0),
        check_annotation_callout_count(src_path, specs_jpg, min_callouts=3),
        check_text_in_region_keywords(
            specs_jpg,
            {
                "regions": ["top_left", "center", "bottom_right"],
                "keywords": ["LENS", "SENSOR", "ISO"],
                "min_edge_density": 0.006,
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["Main_View", "Closeup_View", "Specs_View"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_tutorial_pack_complete(result_paths: list) -> float:
    """Composite evaluator for L3-7 tutorial pack with overview board."""
    if not isinstance(result_paths, list) or len(result_paths) < 6:
        logger.error(f"check_l3_tutorial_pack_complete invalid result_paths: {result_paths}")
        return 0.0

    step1_jpg, step2_jpg, step3_jpg, overview_png, xcf_path, src_path = result_paths[:6]

    scores = [
        check_file_exists(step1_jpg),
        check_file_exists(step2_jpg),
        check_file_exists(step3_jpg),
        check_file_exists(overview_png),
        check_jpeg_format(step1_jpg),
        check_jpeg_format(step2_jpg),
        check_jpeg_format(step3_jpg),
        check_png_format(overview_png),
        check_contrast_increase(src_path, step2_jpg, min_increase_percent=6.0),
        check_saturation_increase(src_path, step2_jpg, min_increase_percent=6.0),
        check_split_before_after_layout(
            src_path,
            step3_jpg,
            split_ratio=0.5,
            min_right_change_ratio=0.06,
            max_left_change_ratio=0.04,
        ),
        check_three_panel_tutorial_layout(
            overview_png,
            {
                "columns": 3,
                "tolerance_px": 35,
                "min_boundary_edge_density": 0.009,
                "regions": ["top_left", "top_center", "top_right"],
                "keywords": ["STEP 1", "STEP 2", "STEP 3"],
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["Step1_Base", "Step2_Grade", "Step3_Compare", "Overview_Board"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_dog_portrait_dual_output_complete(result_paths: list) -> float:
    """Composite evaluator for L3-8 dual-style dog portrait workflow."""
    if not isinstance(result_paths, list) or len(result_paths) < 4:
        logger.error(f"check_l3_dog_portrait_dual_output_complete invalid result_paths: {result_paths}")
        return 0.0

    natural_jpg, clean_png, xcf_path, src_path = result_paths[:4]

    scores = [
        check_file_exists(natural_jpg),
        check_file_exists(clean_png),
        check_jpeg_format(natural_jpg),
        check_png_format(clean_png),
        check_image_dimensions(natural_jpg, 1800, 2400),
        check_image_dimensions(clean_png, 1800, 2400),
        check_contrast_increase(src_path, natural_jpg, min_increase_percent=4.0),
        check_sharpness_increase(src_path, natural_jpg, min_increase_percent=2.0),
        check_text_in_region_keywords(
            natural_jpg,
            {
                "regions": ["bottom_right"],
                "keywords": ["BY"],
                "min_edge_density": 0.005,
            },
        ),
        _check_images_not_identical(natural_jpg, clean_png, min_diff_ratio=0.06),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": [
                    "Dog_Subject",
                    "BG_Natural",
                    "BG_Clean",
                    "Detail_Enhance",
                    "Signature",
                ],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_restore_banner_complete(result_paths: list) -> float:
    """Composite evaluator for L3-9 old photo restoration banner task."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l3_restore_banner_complete invalid result_paths: {result_paths}")
        return 0.0

    banner_jpg, xcf_path, src_path = result_paths[:3]

    scores = [
        check_file_exists(banner_jpg),
        check_jpeg_format(banner_jpg),
        check_image_dimensions(banner_jpg, 2000, 1200),
        check_image_file_size_range(banner_jpg, {"max_size": 819200}),
        check_contrast_increase(src_path, banner_jpg, min_increase_percent=5.0),
        check_sharpness_increase(src_path, banner_jpg, min_increase_percent=1.0),
        check_text_in_region_keywords(
            banner_jpg,
            {
                "regions": ["top_center", "bottom_center"],
                "keywords": ["SUMMER", "2026"],
                "min_edge_density": 0.006,
            },
        ),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["Restore_Base", "Color_Grade", "Title", "Meta_Info"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_l3_transparency_course_assets_complete(result_paths: list) -> float:
    """Composite evaluator for L3-10 cover + infographic transparency asset pack."""
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"check_l3_transparency_course_assets_complete invalid result_paths: {result_paths}")
        return 0.0

    cover_png, infographic_png, xcf_path = result_paths[:3]

    scores = [
        check_file_exists(cover_png),
        check_file_exists(infographic_png),
        check_png_format(cover_png),
        check_png_format(infographic_png),
        check_image_dimensions(cover_png, 1600, 900),
        check_image_dimensions(infographic_png, 1600, 2000),
        check_text_in_region_keywords(
            cover_png,
            {
                "regions": ["top_left", "center", "bottom_right"],
                "keywords": ["TRANSPARENCY", "COURSE"],
                "min_edge_density": 0.006,
            },
        ),
        _check_infographic_step_modules(infographic_png, min_modules=4),
        check_xcf_layers_structure(
            xcf_path,
            {
                "layers": ["Cover_Group", "Infographic_Group", "Icons_Group", "Text_Group"],
                "ordered": False,
            },
        ),
    ]
    return _all_binary_checks_pass(scores)


def check_interactive_gimp_watch_white_standard_complete(result_paths: list) -> float:
    """Interactive wrapper for the white-background watch standard task."""
    return check_l2_watch_white_standard_complete(result_paths)


def check_interactive_gimp_city_night_run_complete(result_paths: list) -> float:
    """Interactive wrapper for the city night run cover task."""
    return check_l2_city_night_run_cover_complete(result_paths)


def check_interactive_gimp_perfume_listing_complete(result_paths: list) -> float:
    """Interactive wrapper for the perfume transparent listing task."""
    return check_l2_perfume_listing_complete(result_paths)


def check_interactive_gimp_avatar_refined_complete(result_paths: list) -> float:
    """Interactive wrapper for the refined avatar export task."""
    return check_l2_avatar_refined_complete(result_paths)


def check_interactive_gimp_camera_annotation_complete(result_paths: list) -> float:
    """Interactive wrapper for the camera annotation task."""
    return check_l2_camera_annotation_complete(result_paths)
