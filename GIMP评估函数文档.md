# GIMP Evaluation Functions Documentation

This document provides detailed information about the various check functions used in the GIMP evaluator, including their functionality, input parameters, and output results.

## Function List

### 1. check_brightness_decrease_and_structure_sim

**Functionality**: Checks if the brightness of the source image is lower than the target image, and the structures of both images are similar.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path
- `threshold` (float, optional): Structure similarity threshold, default is 0.03

**Output**:
- `float`: Returns 1.0 if brightness is decreased and structures are similar, otherwise returns 0.0

**Implementation Details**:
1. Calculate the average brightness of both images
2. Check if the source image brightness is lower than the target image
3. Normalize the brightness of both images to the same level (128)
4. Compare the structure of normalized images using MSE (Mean Squared Error) method
5. Return 1.0 if brightness is decreased and structures are similar (MSE < threshold)

---

### 2. check_config_status

**Functionality**: Checks if the GIMP configuration status matches the expected rules.

**Input Parameters**:
- `actual_config_path` (str): Actual configuration file path
- `rule` (dict): Dictionary containing configuration rules, format: `{"key": "configuration key", "value": "expected value"}`

**Output**:
- `float`: Returns 1.0 if configuration matches expectations, otherwise returns 0.0

**Implementation Details**:
1. Read the configuration file content
2. Iterate through each line, skipping comments and empty lines
3. Check if configuration key and value match the rules
4. Supports both single-key and double-key formats

---

### 3. check_contrast_increase_and_structure_sim

**Functionality**: Checks if the contrast of the source image is higher than the target image, and the structures of both images are similar.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if contrast is increased and structures are similar, otherwise returns 0.0

**Implementation Details**:
1. Calculate the contrast of both images (using standard deviation of pixel values)
2. Check if the source image contrast is higher than the target image
3. Compare image structures using SSIM (Structural Similarity Index) method
4. Return 1.0 if contrast is increased and structures are similar (SSIM >= 0.65)

---

### 4. check_file_exists_and_structure_sim

**Functionality**: Checks if the file exists and has a similar structure to the target image.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if file exists and structures are similar, otherwise returns 0.0

**Implementation Details**:
1. Check if the source file exists
2. If file exists, load both source and target images
3. Compare the structure of both images using SSIM method
4. Return 1.0 if structures are similar

---

### 5. check_green_background

**Functionality**: Checks if the background of the source image is green.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path (used to identify background regions)

**Output**:
- `float`: Returns 1.0 if background is green, otherwise returns 0.0

**Implementation Details**:
1. Load both source and target images
2. Iterate through each pixel in the target image
3. Identify non-black pixels as background regions
4. Check if corresponding pixels in the source image are green (green component greater than red and blue components)
5. Return 1.0 if all background pixels are green

---

### 6. check_image_mirror

**Functionality**: Checks if the source image is a horizontal mirror of the target image.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if image is mirrored, otherwise returns 0.0

**Implementation Details**:
1. Load both source and target images
2. Perform horizontal flip operation on the source image
3. Compare the flipped image with the target image using SSIM method
4. Return 1.0 if similarity reaches 0.99 or above

---

### 7. check_image_size

**Functionality**: Checks if the image dimensions match the expected size.

**Input Parameters**:
- `src_path` (str): Source image file path
- `rule` (dict): Dictionary containing size rules, format: `{"width": width, "height": height, "ignore_transparent": boolean}`

**Output**:
- `float`: Returns 1.0 if dimensions match expectations, otherwise returns 0.0

**Implementation Details**:
1. Load the image
2. If `ignore_transparent` is set, calculate the actual size of non-transparent regions
3. Compare actual dimensions with expected dimensions in the rules
4. Return 1.0 if dimensions match

---

### 8. check_include_exclude

**Functionality**: Checks if the result string contains all required strings and does not contain any excluded strings.

**Input Parameters**:
- `result` (str): Result string to be checked
- `rules` (dict): Dictionary containing rules, format: `{"include": ["list of strings to include"], "exclude": ["list of strings to exclude"]}`

**Output**:
- `float`: Returns 1.0 if rules are satisfied, otherwise returns 0.0

**Implementation Details**:
1. Check if the result contains all strings in the `include` list
2. Check if the result does not contain any strings in the `exclude` list
3. Return 1.0 if both conditions are satisfied

---

### 9. check_palette_and_structure_sim

**Functionality**: Checks if the source image uses palette mode and has a similar structure to the target image.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if using palette and structures are similar, otherwise returns 0.0

**Implementation Details**:
1. Safely open the source image using retry mechanism
2. Check if the source image mode is 'P' (palette mode)
3. Convert the source image to RGB mode
4. Compare the structure of source and target images using SSIM method
5. Return 1.0 if using palette and structures are similar

---

### 10. check_saturation_increase_and_structure_sim

**Functionality**: Checks if the saturation of the source image is higher than the target image, and the structures of both images are similar.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if saturation is increased and structures are similar, otherwise returns 0.0

**Implementation Details**:
1. Convert both images to HSV mode
2. Calculate the average saturation of both images
3. Check if the source image saturation is higher than the target image
4. Compare the structure similarity of hue (H) and value (V) channels separately
5. Return 1.0 if saturation is increased and both hue and value channels have similar structures

---

### 11. check_structure_sim

**Functionality**: Checks if the structures of two images are similar.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if structures are similar, otherwise returns 0.0

**Implementation Details**:
1. Load both source and target images
2. Check if both images have the same dimensions
3. Compare the structure of both images using SSIM method
4. Return 1.0 if structures are similar (SSIM >= 0.9)

---

### 12. check_structure_sim_resized

**Functionality**: Checks if the source image, after resizing, has a similar structure to the target image.

**Input Parameters**:
- `src_path` (str): Source image file path
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if resized structure is similar, otherwise returns 0.0

**Implementation Details**:
1. Load both source and target images
2. If the source image has transparency, extract and crop the non-transparent region
3. Resize the source image to match the target image size
4. Compare the structure of the resized source image and target image using SSIM method
5. Return 1.0 if structures are similar

---

### 13. check_textbox_on_leftside

**Functionality**: Checks if the textbox is located on the left side of the image.

**Input Parameters**:
- `src_path` (str): Source image file path

**Output**:
- `float`: Returns 1.0 if textbox is on the left side, otherwise returns 0.0

**Implementation Details**:
1. Load the image and convert to grayscale
2. Iterate through each row to find the leftmost dark pixel (brightness < 128)
3. Check if the leftmost dark pixel is within 5% of the image width
4. Return 1.0 if within the left side range

---

### 14. check_triangle_position

**Functionality**: Checks if the triangle is located in the center of the image.

**Input Parameters**:
- `tgt_path` (str): Target image file path

**Output**:
- `float`: Returns 1.0 if triangle is in the center, otherwise returns 0.0

**Implementation Details**:
1. Load the image
2. Identify unique colors in the image
3. Assume the background is the most common color and the triangle is the second most common color
4. Create a mask for triangle pixels
5. Calculate the centroid of the triangle
6. Check if the centroid is within 5% tolerance of the image center
7. Return 1.0 if within the center range

---

## Helper Functions

### calculate_brightness

Calculates the average brightness of an image.

### normalize_brightness

Normalizes the brightness of an image to a target brightness level.

### measure_saturation

Measures the average saturation of an HSV image.

### calculate_contrast

Calculates the contrast of an image (standard deviation of pixel values).

### structure_check_by_mse

Checks the structural similarity of two images using MSE (Mean Squared Error) method.

### structure_check_by_ssim

Checks the structural similarity of two images using SSIM (Structural Similarity Index) method.

---

## Notes

1. All functions return 0.0 when input parameters are `None`
2. Image comparison functions typically require both images to have the same dimensions (unless otherwise specified)
3. The default SSIM threshold is 0.9, but some functions use different thresholds
4. Some functions support transparency handling and can ignore transparent regions
5. All functions include error handling to prevent crashes due to file reading failures or image processing errors
