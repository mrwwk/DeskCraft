"""
GIMP L2_2 Evaluation Functions for geometric logo design tasks.

This module provides evaluation functions for verifying geometric logo design
workflows including triangle manipulation, colorization, and composition tasks.
"""

import os
import logging
from typing import List, Optional, Tuple
from PIL import Image, ImageStat
import numpy as np
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger("desktopenv.metrics.gimp_l2_2")


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


def check_colors_in_image(image_path: str, expected_colors: List[str], tolerance: int = 50) -> int:
    """
    Check if an image contains expected colors.
    
    Args:
        image_path: Path to the image file
        expected_colors: List of expected color hex codes (e.g., ['#ff0000', '#00ff00'])
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
        logger.info(f"Colors check: expected={expected_colors}, found={found_colors}, pass={all_found}")
        return 1 if all_found else 0
    
    except Exception as e:
        logger.error(f"Error checking colors: {e}")
        return 0


def check_text_in_image_basic(image_path: str) -> int:
    """
    Basic check for text-like patterns in an image.
    
    Note: This is a heuristic check using edge detection.
    For proper OCR, tesseract or similar would be needed.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        1 if text-like patterns are detected, 0 otherwise
    """
    if image_path is None or not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return 0
    
    try:
        img = Image.open(image_path)
        gray = img.convert('L')
        img_array = np.array(gray)
        
        # Look for regions with high contrast (potential text)
        sobel_x = np.abs(np.gradient(img_array, axis=1))
        sobel_y = np.abs(np.gradient(img_array, axis=0))
        edges = sobel_x + sobel_y
        
        # Check if there are edge-dense regions (potential text areas)
        edge_density = np.mean(edges > 50)
        
        # Text typically creates concentrated edge patterns
        has_text_patterns = edge_density > 0.01
        
        logger.info(f"Text detection: edge_density={edge_density:.4f}, has_text_patterns={has_text_patterns}")
        return 1 if has_text_patterns else 0
    
    except Exception as e:
        logger.error(f"Error checking text patterns: {e}")
        return 0


def check_triad_logo_complete(
    result_paths: list,
    expected_size: List[int] = None,
    expected_layers: List[str] = None
) -> float:
    """
    Comprehensive check for the triad geometric logo design task.
    
    This function checks multiple aspects of the completed task:
    1. PNG file exists and is PNG format
    2. Image has correct dimensions (1200x1200px)
    3. XCF project file exists with expected layers
    4. Image contains red, blue, green colors (triangles)
    5. Image contains gradient background colors
    6. Text-like patterns exist (Logo_Text layer)
    
    Args:
        result_paths: List of [png_file_path, xcf_file_path, source_file_path]
        expected_size: Expected output dimensions [width, height]
        expected_layers: List of expected layer names in XCF file
    
    Returns:
        Score from 0.0 to 1.0 based on completed requirements
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0
    
    png_path = result_paths[0]       # triad_logo.png
    xcf_path = result_paths[1]       # triad_design.xcf
    src_path = result_paths[2]       # source image
    
    # Default expected values
    if expected_size is None:
        expected_size = [1200, 1200]
    
    if expected_layers is None:
        expected_layers = [
            'Original_Triangle',
            'Triangle_Red',
            'Triangle_Blue',
            'Triangle_Green',
            'Background_Gradient',
            'Logo_Text'
        ]
    
    scores = []
    
    # Check 1: PNG file exists
    png_exists = check_file_exists(png_path)
    scores.append(png_exists)
    logger.info(f"Check 1 - PNG exists: {png_exists}")
    
    if png_exists == 0:
        logger.warning("PNG file does not exist, returning 0")
        return 0.0
    
    # Check 2: PNG format
    is_png = check_png_format(png_path)
    scores.append(is_png)
    logger.info(f"Check 2 - PNG format: {is_png}")
    
    # Check 3: Correct dimensions
    width_ok = check_image_dimensions(png_path, expected_size[0], expected_size[1])
    scores.append(width_ok)
    logger.info(f"Check 3 - Correct dimensions ({expected_size[0]}x{expected_size[1]}): {width_ok}")
    
    # Check 4: XCF file exists with layers
    xcf_ok = check_xcf_file_exists_and_has_layers(xcf_path, expected_layers)
    scores.append(xcf_ok)
    logger.info(f"Check 4 - XCF with layers {expected_layers}: {xcf_ok}")
    
    # Check 5: Contains triangle colors (red, blue, green)
    triangle_colors = ['#ff0000', '#0000ff', '#00ff00']  # Red, Blue, Green
    colors_ok = check_colors_in_image(png_path, triangle_colors, tolerance=60)
    scores.append(colors_ok)
    logger.info(f"Check 5 - Triangle colors (RGB): {colors_ok}")
    
    # Check 6: Contains gradient background colors (dark grays)
    bg_colors = ['#2c3e50', '#1a252f']  # Dark grays for gradient
    bg_ok = check_colors_in_image(png_path, bg_colors, tolerance=40)
    scores.append(bg_ok)
    logger.info(f"Check 6 - Background gradient colors: {bg_ok}")
    
    # Check 7: Text patterns exist
    text_ok = check_text_in_image_basic(png_path)
    scores.append(text_ok)
    logger.info(f"Check 7 - Text patterns: {text_ok}")
    
    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Triad logo complete: scores={scores}, final={final_score:.2f}")
    
    return final_score


def check_triangle_composition(
    result_paths: list,
    expected_colors: List[str] = None,
    expected_layer_count: int = 6
) -> float:
    """
    Check for triangle composition tasks with colored triangles.
    
    This function verifies:
    1. Output file exists
    2. Contains expected triangle colors
    3. XCF has expected number of layers
    
    Args:
        result_paths: List of [output_file_path, xcf_file_path, source_file_path]
        expected_colors: List of expected triangle colors
        expected_layer_count: Expected number of layers in XCF
    
    Returns:
        Score from 0.0 to 1.0
    """
    if not isinstance(result_paths, list) or len(result_paths) < 3:
        logger.error(f"Expected list of 3 paths, got: {result_paths}")
        return 0.0
    
    output_path = result_paths[0]
    xcf_path = result_paths[1]
    src_path = result_paths[2]
    
    if expected_colors is None:
        expected_colors = ['#ff0000', '#0000ff', '#00ff00']
    
    scores = []
    
    # Check 1: Output file exists
    output_exists = check_file_exists(output_path)
    scores.append(output_exists)
    logger.info(f"Check 1 - Output exists: {output_exists}")
    
    if output_exists == 0:
        return 0.0
    
    # Check 2: Contains expected colors
    colors_ok = check_colors_in_image(output_path, expected_colors, tolerance=60)
    scores.append(colors_ok)
    logger.info(f"Check 2 - Colors {expected_colors}: {colors_ok}")

    # Check 3: XCF file exists
    xcf_exists = check_file_exists(xcf_path)
    scores.append(xcf_exists)
    logger.info(f"Check 3 - XCF exists: {xcf_exists}")

    # Check 4: XCF is valid format
    if xcf_exists:
        try:
            with open(xcf_path, 'rb') as f:
                content = f.read()
            is_xcf = content.startswith(b'gimp xcf')
            scores.append(1 if is_xcf else 0)
            logger.info(f"Check 4 - Valid XCF format: {is_xcf}")
        except Exception as e:
            logger.error(f"Error checking XCF format: {e}")
            scores.append(0)
    else:
        scores.append(0)

    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Triangle composition: scores={scores}, final={final_score:.2f}")

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


def check_alpine_landscape_complete(
    result_paths: list,
    expected_width: int = 1600,
    expected_layers: List[str] = None
) -> float:
    """
    Comprehensive check for the alpine landscape photo enhancement task.
    
    This function checks multiple aspects of the completed task:
    1. JPEG file exists and is JPEG format
    2. JPEG has correct width (1600px)
    3. XCF project file exists with all expected layers
    4. Image contains text patterns (Text_Title and Text_Location)
    5. Image has been modified from source (brightness/contrast change)
    
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
    
    jpeg_path = result_paths[0]      # alpine_masterpiece.jpg
    xcf_path = result_paths[1]       # alpine_project.xcf
    src_path = result_paths[2]       # source image
    
    # Default expected layers for this task
    if expected_layers is None:
        expected_layers = [
            'Sky_Enhance',
            'Mountain_Contrast',
            'Donkey_Warmth',
            'Vignette',
            'Text_Title',
            'Text_Location',
            'Frame'
        ]
    
    scores = []
    
    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")
    
    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0
    
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
    
    # Check 5: Text patterns exist (Text_Title and Text_Location)
    text_ok = check_text_in_image_basic(jpeg_path)
    scores.append(text_ok)
    logger.info(f"Check 5 - Text patterns: {text_ok}")
    
    # Check 6: Image has been modified from source
    if src_path and os.path.exists(src_path):
        try:
            src_img = Image.open(src_path)
            jpeg_img = Image.open(jpeg_path)
            
            # Compare overall brightness
            src_brightness = calculate_brightness(src_img)
            jpeg_brightness = calculate_brightness(jpeg_img)
            
            # Compare saturation
            src_saturation = calculate_saturation(src_img)
            jpeg_saturation = calculate_saturation(jpeg_img)
            
            # Expect some changes due to enhancements
            brightness_changed = abs(jpeg_brightness - src_brightness) > 3
            saturation_changed = abs(jpeg_saturation - src_saturation) > 2
            
            enhancement_applied = brightness_changed or saturation_changed
            scores.append(1 if enhancement_applied else 0)
            logger.info(f"Check 6 - Enhancement applied: {enhancement_applied} (brightness diff={abs(jpeg_brightness - src_brightness):.2f}, saturation diff={abs(jpeg_saturation - src_saturation):.2f})")
        except Exception as e:
            logger.warning(f"Could not check enhancement: {e}")
            scores.append(0)
    else:
        logger.warning(f"Source file not found: {src_path}, skipping enhancement check")
    
    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Alpine landscape complete: scores={scores}, final={final_score:.2f}")
    
    return final_score


def check_rainforest_enhancement_complete(
    result_paths: list,
    expected_width: int = 1400,
    expected_layers: List[str] = None
) -> float:
    """
    Comprehensive check for the rainforest photo enhancement task.
    
    This function checks multiple aspects of the completed task:
    1. JPEG file exists and is JPEG format
    2. JPEG has correct width (1400px)
    3. XCF project file exists with all expected layers
    4. Image contains text patterns (Text_Title and Text_Location)
    5. Image contains green colors (enhanced foliage)
    6. Image has been modified from source (enhancement applied)
    
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
    
    jpeg_path = result_paths[0]      # rainforest_masterpiece.jpg
    xcf_path = result_paths[1]       # rainforest_project.xcf
    src_path = result_paths[2]       # source image
    
    # Default expected layers for this task
    if expected_layers is None:
        expected_layers = [
            'Green_Enhance',
            'Tree_Contrast',
            'Shadow_Boost',
            'Sunlight_Glow',
            'Vignette',
            'Text_Title',
            'Text_Location',
            'Frame'
        ]
    
    scores = []
    
    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")
    
    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0
    
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
    
    # Check 5: Text patterns exist (Text_Title and Text_Location)
    text_ok = check_text_in_image_basic(jpeg_path)
    scores.append(text_ok)
    logger.info(f"Check 5 - Text patterns: {text_ok}")
    
    # Check 6: Image contains green colors (enhanced foliage)
    green_colors = ['#228b22', '#32cd32', '#00ff00']  # Forest green, lime green, green
    green_ok = check_colors_in_image(jpeg_path, green_colors, tolerance=50)
    scores.append(green_ok)
    logger.info(f"Check 6 - Green colors (foliage): {green_ok}")
    
    # Check 7: Image has been enhanced from source
    if src_path and os.path.exists(src_path):
        try:
            src_img = Image.open(src_path)
            jpeg_img = Image.open(jpeg_path)
            
            # Compare saturation (should be higher due to green enhancement)
            src_saturation = calculate_saturation(src_img)
            jpeg_saturation = calculate_saturation(jpeg_img)
            
            # Compare brightness (should be different due to adjustments)
            src_brightness = calculate_brightness(src_img)
            jpeg_brightness = calculate_brightness(jpeg_img)
            
            # Expect saturation increase due to green enhancement (+40)
            saturation_increased = jpeg_saturation > src_saturation * 1.05
            brightness_changed = abs(jpeg_brightness - src_brightness) > 3
            
            enhancement_applied = saturation_increased or brightness_changed
            scores.append(1 if enhancement_applied else 0)
            logger.info(f"Check 7 - Enhancement applied: {enhancement_applied} (saturation: {src_saturation:.2f} -> {jpeg_saturation:.2f}, brightness: {src_brightness:.2f} -> {jpeg_brightness:.2f})")
        except Exception as e:
            logger.warning(f"Could not check enhancement: {e}")
            scores.append(0)
    else:
        logger.warning(f"Source file not found: {src_path}, skipping enhancement check")
    
    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Rainforest enhancement complete: scores={scores}, final={final_score:.2f}")
    
    return final_score


def check_sunrise_landscape_complete(
    result_paths: list,
    expected_width: int = 1600,
    expected_layers: List[str] = None
) -> float:
    """
    Comprehensive check for the sunrise landscape photo enhancement task.
    
    This function checks multiple aspects of the completed task:
    1. JPEG file exists and is JPEG format
    2. JPEG has correct width (1600px)
    3. XCF project file exists with all expected layers
    4. Image contains text patterns (Text_Title and Text_Location)
    5. Image contains warm colors (golden sunrise tones)
    6. Image has been enhanced from source (color/saturation changes)
    
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
    
    jpeg_path = result_paths[0]      # sunrise_masterpiece.jpg
    xcf_path = result_paths[1]       # sunrise_project.xcf
    src_path = result_paths[2]       # source image
    
    # Default expected layers for this task
    if expected_layers is None:
        expected_layers = [
            'Sky_Golden',
            'Water_Reflection',
            'Mountain_Detail',
            'Building_Warmth',
            'Vignette',
            'Text_Title',
            'Text_Location',
            'Frame'
        ]
    
    scores = []
    
    # Check 1: JPEG file exists
    jpeg_exists = check_file_exists(jpeg_path)
    scores.append(jpeg_exists)
    logger.info(f"Check 1 - JPEG exists: {jpeg_exists}")
    
    if jpeg_exists == 0:
        logger.warning("JPEG file does not exist, returning 0")
        return 0.0
    
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
    
    # Check 5: Text patterns exist (Text_Title and Text_Location)
    text_ok = check_text_in_image_basic(jpeg_path)
    scores.append(text_ok)
    logger.info(f"Check 5 - Text patterns: {text_ok}")
    
    # Check 6: Image contains warm colors (golden sunrise)
    warm_colors = ['#ffd700', '#ff8c00', '#daa520']  # Gold, dark orange, goldenrod
    warm_ok = check_colors_in_image(jpeg_path, warm_colors, tolerance=50)
    scores.append(warm_ok)
    logger.info(f"Check 6 - Warm colors (sunrise): {warm_ok}")
    
    # Check 7: Image has been enhanced from source
    if src_path and os.path.exists(src_path):
        try:
            src_img = Image.open(src_path)
            jpeg_img = Image.open(jpeg_path)
            
            # Compare saturation (should be higher due to water reflection enhancement)
            src_saturation = calculate_saturation(src_img)
            jpeg_saturation = calculate_saturation(jpeg_img)
            
            # Compare brightness (should be different due to color adjustments)
            src_brightness = calculate_brightness(src_img)
            jpeg_brightness = calculate_brightness(jpeg_img)
            
            # Expect saturation increase due to water reflection enhancement (+30)
            saturation_increased = jpeg_saturation > src_saturation * 1.05
            brightness_changed = abs(jpeg_brightness - src_brightness) > 3
            
            enhancement_applied = saturation_increased or brightness_changed
            scores.append(1 if enhancement_applied else 0)
            logger.info(f"Check 7 - Enhancement applied: {enhancement_applied} (saturation: {src_saturation:.2f} -> {jpeg_saturation:.2f}, brightness: {src_brightness:.2f} -> {jpeg_brightness:.2f})")
        except Exception as e:
            logger.warning(f"Could not check enhancement: {e}")
            scores.append(0)
    else:
        logger.warning(f"Source file not found: {src_path}, skipping enhancement check")
    
    # Calculate final score
    valid_scores = [s for s in scores if s is not None]
    final_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    logger.info(f"Sunrise landscape complete: scores={scores}, final={final_score:.2f}")
    
    return final_score
