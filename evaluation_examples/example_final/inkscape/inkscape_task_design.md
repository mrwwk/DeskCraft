# Inkscape Task Design Document

## 0. Inkscape Launch Configuration

Inkscape is launched via its absolute binary path:

```
/usr/bin/inkscape
```

In all task JSON config blocks, use this form:

```json
{
  "type": "launch",
  "parameters": {
    "command": ["/usr/bin/inkscape", "/home/user/Documents/file.svg"]
  }
}
```

> **Note**: Do NOT use a bare `inkscape` command — use the full path `/usr/bin/inkscape` to ensure correct invocation on the test VM. After launch, add a `sleep` step (3–5 seconds) so the GUI fully initializes before the agent begins acting.

Typical task config sequence:

```json
"config": [
  {"type": "upload_file",  "parameters": {"src": "assets/inkscape/file.svg", "dest": "/home/user/Documents/file.svg"}},
  {"type": "launch",       "parameters": {"command": ["/usr/bin/inkscape", "/home/user/Documents/file.svg"]}},
  {"type": "sleep",        "parameters": {"seconds": 3}}
]
```

---

## 1. Available Resources

All resource files are located at: `assets/inkscape/`

### 1.1 SVG Files

| Filename | Dimensions | Size | Description |
|----------|-----------|------|-------------|
| `simple_rect_circle.svg` | 800×600 | ~856 B | Blue rectangle (id=rect1) + red circle (id=circle1), basic shapes for property editing |
| `text_hello.svg` | 800×600 | ~969 B | "Hello World" title (id=text_title, 48px) + subtitle (id=text_subtitle, 24px) |
| `three_layers.svg` | 800×600 | ~1.75 KB | 3 Inkscape layers: Background, Shapes, Labels |
| `star_polygon.svg` | 800×600 | ~1.26 KB | Five-pointed star (id=star1) + hexagon (id=hexagon1) + triangle (id=triangle1) paths |
| `overlapping_circles.svg` | 800×600 | ~898 B | Two semi-transparent overlapping circles for boolean operations |
| `logo_design.svg` | 400×400 | ~1.35 KB | Concentric circles logo + letter "A" + decorative dots |
| `complex_drawing.svg` | 800×600 | ~2.63 KB | Gradients, blur/shadow filters, cloned circles, rotated text |
| `poster_template.svg` | A4 (595×842) | ~3.14 KB | Dark-themed conference poster with 3 layers |
| `export_test.svg` | 1024×768 | ~2.77 KB | Countryside landscape scene for export tasks |
| `complex_path.svg` | 800×600 | ~1.76 KB | Bezier curves, spiral, zigzag, blob shape for path editing |
| `grouped_shapes.svg` | 800×600 | ~1.1 KB | Pre-grouped inner shapes (group1: inner_rect + inner_circle) + outer_rect outside group |
| `multi_rects.svg` | 800×600 | ~900 B | Three rectangles at different positions: rect_bottom, rect_middle, rect_top |
| `zorder_shapes.svg` | 800×600 | ~1.1 KB | Three overlapping shapes (large_rect, medium_circle, small_rect) for z-order tasks |
| `shapes_mixed.svg` | 800×600 | ~1.0 KB | Ellipse (ellipse1), hexagon path (hexagon_path), line (diagonal_line) for shape tool tasks |
| `text_styles.svg` | 800×600 | ~1.3 KB | Five text elements with varied alignment/style: text_left, text_center, text_right, text_italic, text_multiline |
| `gradient_demo.svg` | 800×600 | ~1.2 KB | grad_rect with existing linear gradient + plain_rect for radial gradient task |
| `infographic_report.svg` | 1200×800 | ~4.5 KB | 4-layer dashboard (Background, Header, Content, Footer) with cards, bar chart, donut chart, text elements |
| `icon_parts.svg` | 800×600 | ~1.2 KB | Scattered icon primitives (icon_bg, icon_triangle, icon_ring, accent_dot, icon_label) for composition tasks |

### 1.2 Key Element IDs Reference

#### simple_rect_circle.svg
- `rect1`: Blue rectangle, fill:#0000ff, stroke:#000000, width=200, height=100, x=50, y=50
- `circle1`: Red circle, fill:#ff0000, stroke:#000000, cx=400, cy=200, r=60

#### text_hello.svg
- `text_title`: "Hello World", font-size:48px, font-family:sans-serif, fill:#333333
- `text_subtitle`: "This is a sample subtitle", font-size:24px, font-family:serif, fill:#666666

#### three_layers.svg
- `layer1` (label="Background"): contains `bg_rect` (fill:#f0f0f0)
- `layer2` (label="Shapes"): contains `green_rect` (fill:#00cc00) + `orange_ellipse` (fill:#ff9900)
- `layer3` (label="Labels"): contains `label1` ("Rectangle") + `label2` ("Ellipse")

#### overlapping_circles.svg
- `circle_left`: Red, fill-opacity:0.7, cx=320, cy=300, r=120
- `circle_right`: Blue, fill-opacity:0.7, cx=480, cy=300, r=120

#### export_test.svg
- `sky`, `ground`, `sun`, `cloud1`, `cloud2`, `house`, `tree1`, `scene_title`

#### complex_path.svg
- `complex_curve`: Open bezier, `complex_shape`: Closed path, `spiral_path`, `zigzag`, `blob_shape`

#### grouped_shapes.svg
- `group1`: Parent group containing `inner_rect` (green rect) + `inner_circle` (blue circle)
- `outer_rect`: Orange rect NOT inside group1

#### multi_rects.svg
- `rect_bottom`: Green rect at y=420
- `rect_middle`: Purple rect at y=250
- `rect_top`: Orange rect at y=80

#### zorder_shapes.svg
- `large_rect`: Light-blue rect, lowest z-order (first in document)
- `medium_circle`: Pink circle, middle z-order
- `small_rect`: Light-green rect, highest z-order (last in document, renders on top)

#### shapes_mixed.svg
- `ellipse1`: Yellow ellipse, cx=400, cy=200, rx=220, ry=120
- `hexagon_path`: Purple hexagon as `<path>`
- `diagonal_line`: Red diagonal line, stroke-width=5

#### text_styles.svg
- `text_left`: 32px sans-serif, fill=#000000, left-aligned
- `text_center`: 36px serif, fill=#0055aa, center-aligned
- `text_right`: 28px monospace, fill=#aa0000, right-aligned
- `text_italic`: 30px sans-serif, fill=#006600, font-style:italic
- `text_multiline`: 24px sans-serif, fill=#555555

#### gradient_demo.svg
- `grad_rect`: rect with existing linearGradient (blue→red, id=grad_blue_red)
- `plain_rect`: Grey rect with no gradient (target for radial gradient task)

#### infographic_report.svg
- Layers: `layer_bg` (Background), `layer_header` (Header), `layer_content` (Content), `layer_footer` (Footer)
- `bg_fill`: Full-page light-grey rect
- `header_bar`: Gradient rect (id=header_gradient, #2c3e50→#3498db), `header_title`: "Annual Report 2024", `header_subtitle`: "Company Performance Overview"
- `card_left`: Rounded white card, `card_left_title`: "Revenue", `card_left_value`: "$4.2M", `card_left_delta`: "+18% vs last year"
- `card_center`: Rounded white card, `card_center_title`: "Quarterly Sales", `bar_q1`–`bar_q4`: Blue bar chart rects, `label_q1`–`label_q4`
- `card_right`: Rounded white card, `card_right_title`: "Customers", `donut_outer`(red), `donut_inner`(white), `donut_label`: "12.5K"
- `footer_bar`: Dark rect, `footer_text`: "Confidential — Internal Use Only"

#### icon_parts.svg
- `icon_bg`: Large grey circle at (200,200) r=150
- `icon_triangle`: Black triangle path at (500,100)
- `icon_ring`: Grey ring at (200,450) r=100
- `accent_dot`: Red small circle at (650,450) r=20
- `icon_label`: Text "MyApp Icon" at (400,560)

---

## 2. Evaluator Functions Overview

File: `desktop_env/evaluators/metrics/inkscape.py` (to be created)

All evaluators parse SVG files (XML format) using `xml.etree.ElementTree` with namespace handling.

**SVG Namespaces**:
```python
NS = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd',
    'xlink': 'http://www.w3.org/1999/xlink',
}
```

| Function | Description | result Type | expected Type |
|----------|-------------|-------------|---------------|
| `check_inkscape_fill_color` | Verify element fill color | `vm_file` (.svg) | `rule` |
| `check_inkscape_stroke` | Verify stroke properties | `vm_file` (.svg) | `rule` |
| `check_inkscape_element_geometry` | Verify size/position | `vm_file` (.svg) | `rule` |
| `check_inkscape_text_content` | Verify text content | `vm_file` (.svg) | `rule` |
| `check_inkscape_text_style` | Verify text font/size/weight | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_visibility` | Verify layer visibility | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_name` | Verify layer renamed | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_order` | Verify layer stacking order | `vm_file` (.svg) | `rule` |
| `check_inkscape_element_count` | Count specific elements | `vm_file` (.svg) | `rule` |
| `check_inkscape_boolean_operation` | Verify boolean op result | `vm_file` (.svg) | `rule` |
| `check_inkscape_transform` | Verify transform attribute | `vm_file` (.svg) | `rule` |
| `check_inkscape_opacity` | Verify element opacity | `vm_file` (.svg) | `rule` |
| `check_inkscape_gradient` | Verify gradient exists and type | `vm_file` (.svg) | `rule` |
| `check_inkscape_filter` | Verify filter applied | `vm_file` (.svg) | `rule` |
| `check_inkscape_clone_exists` | Verify clone exists | `vm_file` (.svg) | `rule` |
| `check_inkscape_document_properties` | Verify doc dimensions | `vm_file` (.svg) | `rule` |
| `check_inkscape_export_png` | Verify PNG export | `vm_command_line` | `rule` |
| `check_inkscape_export_pdf` | Verify PDF export | `vm_command_line` | `rule` |
| `check_inkscape_path_data` | Verify path d attribute | `vm_file` (.svg) | `rule` |
| `check_inkscape_element_deleted` | Verify element removed | `vm_file` (.svg) | `rule` |
| `check_inkscape_group_children` | Verify group contents | `vm_file` (.svg) | `rule` |
| `check_inkscape_ungroup` | Verify group has been ungrouped | `vm_file` (.svg) | `rule` |
| `check_inkscape_zorder` | Verify element z-order relative to another | `vm_file` (.svg) | `rule` |
| `check_inkscape_duplicate` | Verify element was duplicated | `vm_file` (.svg) | `rule` |
| `check_inkscape_align` | Verify elements are aligned | `vm_file` (.svg) | `rule` |
| `check_inkscape_stroke_dasharray` | Verify stroke dash style | `vm_file` (.svg) | `rule` |
| `check_inkscape_fill_rule` | Verify fill-rule (even-odd / nonzero) | `vm_file` (.svg) | `rule` |
| `check_inkscape_radial_gradient` | Verify radial gradient applied | `vm_file` (.svg) | `rule` |
| `check_inkscape_object_to_path` | Verify shape converted to path | `vm_file` (.svg) | `rule` |
| `check_inkscape_snap_to_grid` | Verify grid/guide is defined | `vm_file` (.svg) | `rule` |
| `check_inkscape_text_align` | Verify text-anchor / text-align | `vm_file` (.svg) | `rule` |
| `check_inkscape_add_layer` | Verify a new layer was added | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_lock` | Verify layer is locked/unlocked | `vm_file` (.svg) | `rule` |
| `check_inkscape_stroke_linecap` | Verify stroke-linecap property | `vm_file` (.svg) | `rule` |

---

## 3. Task Definitions

### 3.1 Level 1 — Basic Operations (Single atomic action, directly verifiable)

---

#### Task 1-1: Change Rectangle Fill Color

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Change the fill color of the blue rectangle to red (`#ff0000`), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_fill_color`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_id": "rect1", "expected_fill": "#ff0000"}`
- **Atomic feature**: Fill color editing (Object > Fill and Stroke)

---

#### Task 1-2: Change Circle Stroke Color and Width

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Change the stroke color of the red circle to green (`#00ff00`) and set the stroke width to 5 pixels, then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_stroke`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_id": "circle1", "expected_stroke": "#00ff00", "expected_stroke_width": "5"}`
- **Atomic feature**: Stroke color and width (Object > Fill and Stroke > Stroke paint / Stroke style)

---

#### Task 1-3: Resize Rectangle

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Resize the blue rectangle to width=400 and height=200 (using the W/H fields in the toolbar), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_geometry`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_id": "rect1", "expected_width": "400", "expected_height": "200", "tolerance": 5}`
- **Atomic feature**: Shape resize via toolbar W/H fields

---

#### Task 1-4: Change Text Content

- **Instruction**: Open `/home/user/Documents/text_hello.svg` in Inkscape. Change the title text from "Hello World" to "Welcome to Inkscape", then save the file.
- **Upload Resources**: `text_hello.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_text_content`
- **result**: `vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**: `rule` → `{"element_id": "text_title", "expected_text": "Welcome to Inkscape"}`
- **Atomic feature**: Text editing (Text tool, T key)

---

#### Task 1-5: Change Text Font Size

- **Instruction**: Open `/home/user/Documents/text_hello.svg` in Inkscape. Change the font size of the title text to 72 pixels, then save the file.
- **Upload Resources**: `text_hello.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_text_style`
- **result**: `vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**: `rule` → `{"element_id": "text_title", "expected_font_size": "72"}`
- **Atomic feature**: Font size (Text tool toolbar)

---

#### Task 1-6: Hide a Layer

- **Instruction**: Open `/home/user/Documents/three_layers.svg` in Inkscape. Hide the "Labels" layer so it is no longer visible, then save the file.
- **Upload Resources**: `three_layers.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_layer_visibility`
- **result**: `vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**: `rule` → `{"layer_label": "Labels", "expected_visible": false}`
- **Atomic feature**: Layer visibility toggle (Layers panel eye icon)

---

#### Task 1-7: Rename a Layer

- **Instruction**: Open `/home/user/Documents/three_layers.svg` in Inkscape. Rename the "Shapes" layer to "Geometric Objects", then save the file.
- **Upload Resources**: `three_layers.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_layer_name`
- **result**: `vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**: `rule` → `{"layer_id": "layer2", "expected_label": "Geometric Objects"}`
- **Atomic feature**: Layer rename (Layer > Layer Properties)

---

#### Task 1-8: Delete an Element

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Delete the red circle, then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_deleted`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"deleted_element_id": "circle1"}`
- **Atomic feature**: Element deletion (Select + Delete key)

---

#### Task 1-9: Move an Element to a Specific Position

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Move the blue rectangle to position x=300, y=250 (using the X/Y coordinate fields in the toolbar), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_geometry`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_id": "rect1", "expected_x": "300", "expected_y": "250", "tolerance": 5}`
- **Atomic feature**: Position by coordinates (toolbar X/Y fields)

---

#### Task 1-10: Change Document Size

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Change the document size to 1920×1080 pixels (File > Document Properties), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_document_properties`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"expected_width": "1920", "expected_height": "1080"}`
- **Atomic feature**: Document Properties canvas size

---

#### Task 1-11: Change Element Opacity

- **Instruction**: Open `/home/user/Documents/overlapping_circles.svg` in Inkscape. Change the master opacity of the left red circle to 50% (0.5), then save the file.
- **Upload Resources**: `overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_opacity`
- **result**: `vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**: `rule` → `{"element_id": "circle_left", "expected_opacity": "0.5", "tolerance": "0.05"}`
- **Atomic feature**: Master opacity (Opacity field in Fill and Stroke or bottom toolbar)

---

#### Task 1-12: Add a New Rectangle

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Draw a new rectangle anywhere on the canvas using the Rectangle tool (R key), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_count`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_tag": "rect", "min_count": 2}`
- **Atomic feature**: Rectangle drawing tool (R key)

---

#### Task 1-13: Make Text Bold

- **Instruction**: Open `/home/user/Documents/text_hello.svg` in Inkscape. Select the title text "Hello World" and make it bold, then save the file.
- **Upload Resources**: `text_hello.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_text_style`
- **result**: `vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**: `rule` → `{"element_id": "text_title", "expected_font_weight": "bold"}`
- **Atomic feature**: Font weight (Bold button in text toolbar)

---

#### Task 1-15: Change Text Color

- **Instruction**: Open `/home/user/Documents/text_hello.svg` in Inkscape. Change the fill color of the subtitle text to blue (`#0000ff`), then save the file.
- **Upload Resources**: `text_hello.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_fill_color`
- **result**: `vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**: `rule` → `{"element_id": "text_subtitle", "expected_fill": "#0000ff"}`
- **Atomic feature**: Text fill color (Object > Fill and Stroke while text selected)

---

#### Task 1-16: Change Text Alignment to Center

- **Instruction**: Open `/home/user/Documents/text_styles.svg` in Inkscape. Select the left-aligned text (id=text_left) and change its text alignment to center (`text-anchor:middle`), then save the file.
- **Upload Resources**: `text_styles.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_text_align`
- **result**: `vm_file` → `/home/user/Documents/text_styles.svg`
- **expected**: `rule` → `{"element_id": "text_left", "expected_text_anchor": "middle"}`
- **Atomic feature**: Text alignment (center button in text toolbar)

---

#### Task 1-18: Add a New Layer

- **Instruction**: Open `/home/user/Documents/three_layers.svg` in Inkscape. Add a new layer named "Annotations" above all existing layers (Layer > Add Layer...), then save the file.
- **Upload Resources**: `three_layers.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_add_layer`
- **result**: `vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**: `rule` → `{"expected_layer_label": "Annotations"}`
- **Atomic feature**: Add layer (Layer > Add Layer)

---

#### Task 1-19: Ungroup a Group

- **Instruction**: Open `/home/user/Documents/grouped_shapes.svg` in Inkscape. Select the group (id=group1) containing the inner rectangle and circle, and ungroup it (Object > Ungroup, or Ctrl+Shift+G). The inner_rect and inner_circle should become direct children of the layer, not inside a group. Save the file.
- **Upload Resources**: `grouped_shapes.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_ungroup`
- **result**: `vm_file` → `/home/user/Documents/grouped_shapes.svg`
- **expected**: `rule` → `{"ungrouped_id": "group1", "expected_free_ids": ["inner_rect", "inner_circle"]}`
- **Atomic feature**: Ungroup (Object > Ungroup)

---

#### Task 1-20: Raise an Element to Top (Z-order)

- **Instruction**: Open `/home/user/Documents/zorder_shapes.svg` in Inkscape. Select the large light-blue rectangle (id=large_rect) and raise it to the top of the z-order (Object > Raise to Top, or Home key), then save the file.
- **Upload Resources**: `zorder_shapes.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_zorder`
- **result**: `vm_file` → `/home/user/Documents/zorder_shapes.svg`
- **expected**: `rule` → `{"element_id": "large_rect", "expected_position": "top"}`
- **Atomic feature**: Raise to top (Object > Raise to Top)

---

#### Task 1-22: Change Stroke Dash Style

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Select the blue rectangle and change its stroke to a dashed line style (Object > Fill and Stroke > Stroke style > Dashes), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_stroke_dasharray`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_id": "rect1", "expect_dash": true}`
- **Atomic feature**: Stroke dash pattern (Fill and Stroke > Stroke style)

---

#### Task 1-23: Change Stroke Line Cap

- **Instruction**: Open `/home/user/Documents/shapes_mixed.svg` in Inkscape. Select the diagonal red line (id=diagonal_line) and change its stroke line cap to "round" (Object > Fill and Stroke > Stroke style > Line cap: Round), then save the file.
- **Upload Resources**: `shapes_mixed.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_stroke_linecap`
- **result**: `vm_file` → `/home/user/Documents/shapes_mixed.svg`
- **expected**: `rule` → `{"element_id": "diagonal_line", "expected_linecap": "round"}`
- **Atomic feature**: Stroke line cap (Fill and Stroke > Stroke style)

---

#### Task 1-24: Draw an Ellipse

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Draw a new ellipse anywhere on the canvas using the Ellipse tool (E key), then save the file. The document should contain at least one `<ellipse>` or `<circle>` element beyond the original circle.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_count`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_tag": "circle", "min_count": 2, "also_tag": "ellipse", "combined_min": 2}`
- **Atomic feature**: Ellipse/circle drawing tool (E key)

---

#### Task 1-25: Draw a Straight Line

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Draw a straight line from approximately (100, 500) to (700, 500) using the Bezier/Pen tool (B key) in straight-line mode (click start, double-click end), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_count`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_tag": "path", "min_count": 1}`
- **Atomic feature**: Bezier/Pen tool straight line (B key)

---

#### Task 1-26: Add Radial Gradient to Rectangle

- **Instruction**: Open `/home/user/Documents/gradient_demo.svg` in Inkscape. Apply a radial gradient fill to the grey rectangle (id=plain_rect) using the Gradient tool (G key), then save the file.
- **Upload Resources**: `gradient_demo.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_radial_gradient`
- **result**: `vm_file` → `/home/user/Documents/gradient_demo.svg`
- **expected**: `rule` → `{"element_id": "plain_rect", "gradient_type": "radialGradient"}`
- **Atomic feature**: Radial gradient (Gradient tool, Object > Fill and Stroke > Radial gradient)

---

#### Task 1-27: Rotate an Element by 90 Degrees

- **Instruction**: Open `/home/user/Documents/multi_rects.svg` in Inkscape. Select the green rectangle (id=rect_bottom) and rotate it exactly 90 degrees clockwise (Object > Transform, or use the rotation field in the toolbar), then save the file.
- **Upload Resources**: `multi_rects.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_transform`
- **result**: `vm_file` → `/home/user/Documents/multi_rects.svg`
- **expected**: `rule` → `{"element_id": "rect_bottom", "expected_transform_contains": "rotate"}`
- **Atomic feature**: Rotation (toolbar rotation field or Object > Transform)

---

#### Task 1-29: Align Elements to Canvas Center (Horizontal)

- **Instruction**: Open `/home/user/Documents/multi_rects.svg` in Inkscape. Select all three rectangles and align them to the horizontal center of the page (Object > Align and Distribute > Center on vertical axis), then save the file.
- **Upload Resources**: `multi_rects.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_align`
- **result**: `vm_file` → `/home/user/Documents/multi_rects.svg`
- **expected**: `rule` → `{"element_ids": ["rect_bottom", "rect_middle", "rect_top"], "align_axis": "horizontal_center", "page_width": 800, "tolerance": 10}`
- **Atomic feature**: Align and Distribute (Shift+Ctrl+A)

---

#### Task 1-30: Convert Shape to Path

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Select the blue rectangle (id=rect1) and convert it to a path (Path > Object to Path). After conversion the element should be a `<path>` element. Save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_object_to_path`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"original_id": "rect1", "expected_tag": "path"}`
- **Atomic feature**: Path > Object to Path (Shift+Ctrl+C)

---

#### Task 1-31: Change Fill Rule to Even-Odd

- **Instruction**: Open `/home/user/Documents/star_polygon.svg` in Inkscape. Select the five-pointed star path (id=star1) and change its fill rule to "even-odd" (Object > Fill and Stroke > Fill tab > Even-odd toggle), then save the file.
- **Upload Resources**: `star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_fill_rule`
- **result**: `vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**: `rule` → `{"element_id": "star1", "expected_fill_rule": "evenodd"}`
- **Atomic feature**: Fill rule (Fill and Stroke panel)

---

#### Task 1-32: Remove Fill (Set to None)

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Select the blue rectangle (id=rect1) and remove its fill (set fill to "None") using Object > Fill and Stroke, then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_fill_color`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_id": "rect1", "expected_fill": "none"}`
- **Atomic feature**: Set fill to None (X button in Fill and Stroke panel)

---

#### Task 1-33: Add a Text Element

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Use the Text tool (T key) to add a new text element with the content "Inkscape" anywhere on the canvas, then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_count`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"element_tag": "text", "min_count": 1}`
- **Atomic feature**: Text tool (T key)

---

#### Task 1-34: Change Font Family

- **Instruction**: Open `/home/user/Documents/text_hello.svg` in Inkscape. Select the title text (id=text_title) and change its font family to "DejaVu Sans" using the font selector in the text toolbar, then save the file.
- **Upload Resources**: `text_hello.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_text_style`
- **result**: `vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**: `rule` → `{"element_id": "text_title", "expected_font_family": "DejaVu Sans"}`
- **Atomic feature**: Font family selector (text toolbar)

---

#### Task 1-35: Scale Element Uniformly

- **Instruction**: Open `/home/user/Documents/logo_design.svg` in Inkscape. Select all objects (Ctrl+A) and scale the entire selection to 150% of its current size uniformly (use the W/H lock and enter 150% in Object > Transform > Scale tab), then save the file.
- **Upload Resources**: `logo_design.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_element_geometry`
- **result**: `vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**: `rule` → `{"element_id": "logo_outer", "expected_scale_factor": 1.5, "tolerance": 0.05}`
- **Atomic feature**: Uniform scale (Object > Transform > Scale)

---

#### Task 1-36: Add a Guide Line

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. Add a horizontal guide line at y=300 by double-clicking on the horizontal ruler and entering 300 in the guide dialog (Edit > Guides...), then save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_snap_to_grid`
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"guide_orientation": "horizontal", "guide_position": 300, "tolerance": 2}`
- **Atomic feature**: Guide lines (drag from ruler or Edit > Guides)

---

### 3.2 Level 2 — Intermediate Operations (2–3 combined actions across different feature domains)

---

#### Task 2-1: Boolean Union + Recolor Result

- **Instruction**: Open `/home/user/Documents/overlapping_circles.svg` in Inkscape. (1) Select both circles and perform a Union boolean operation (Path > Union). (2) Change the fill color of the resulting merged path to purple (`#9b59b6`). (3) Set the stroke of the merged path to white (`#ffffff`) with stroke width 3. Save the file.
- **Upload Resources**: `overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_boolean_restyle` (composite)
- **result**: `vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**: `rule` → `{"boolean_check": {"original_ids": ["circle_left", "circle_right"], "max_remaining": 1, "require_path": true}, "fill_check": {"expected_fill": "#9b59b6"}, "stroke_check": {"expected_stroke": "#ffffff", "expected_stroke_width": "3"}}`
- **Steps**: 3 — boolean union + fill recolor + stroke restyle

---

#### Task 2-2: Boolean Difference + Move Result

- **Instruction**: Open `/home/user/Documents/overlapping_circles.svg` in Inkscape. (1) Select both circles and perform a Difference boolean operation (Path > Difference). (2) Move the resulting crescent shape to the center of the canvas (approximately x=300, y=200). (3) Change its fill to yellow (`#f1c40f`). Save the file.
- **Upload Resources**: `overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_boolean_move` (composite)
- **result**: `vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**: `rule` → `{"boolean_check": {"original_ids": ["circle_left", "circle_right"], "max_remaining": 1, "require_path": true}, "fill_check": {"expected_fill": "#f1c40f"}}`
- **Steps**: 3 — boolean difference + move + recolor

---

#### Task 2-3: Blur Shape + Change Its Opacity

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. (1) Select the blue rectangle and apply a Gaussian blur filter (Filters > Blurs > Blur...) with standard deviation ≈ 5. (2) Change the rectangle's master opacity to 60% (0.6). (3) Change the rectangle's fill color to dark grey (`#555555`). Save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_blur_opacity` (composite)
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"filter_check": {"element_id": "rect1", "expected_filter_type": "feGaussianBlur"}, "opacity_check": {"element_id": "rect1", "expected_opacity": "0.6", "tolerance": "0.05"}, "fill_check": {"element_id": "rect1", "expected_fill": "#555555"}}`
- **Steps**: 3 — apply blur + change opacity + change fill

---

#### Task 2-4: Clone Element + Recolor Clones

- **Instruction**: Open `/home/user/Documents/logo_design.svg` in Inkscape. (1) Select the outer circle (id=logo_outer) and create 2 clones (Edit > Clone > Create Clone, twice). (2) Change the original outer circle's fill color to navy (`#1a1a6e`). (3) Change the document size to 600×600. Save the file.
- **Upload Resources**: `logo_design.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_clone_restyle` (composite)
- **result**: `vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**: `rule` → `{"clone_check": {"source_id": "logo_outer", "min_clones": 2}, "fill_check": {"element_id": "logo_outer", "expected_fill": "#1a1a6e"}, "doc_check": {"expected_width": "600", "expected_height": "600"}}`
- **Steps**: 3 — clone ×2 + recolor original + resize document

---

#### Task 2-5: Gradient + Drop Shadow

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. (1) Apply a linear gradient fill to the blue rectangle with at least 2 color stops. (2) Apply a drop shadow filter to the same rectangle (Filters > Shadows and Glows > Drop Shadow...). (3) Change the stroke width of the rectangle to 0 (remove the stroke by setting it to "none"). Save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_gradient_shadow` (composite)
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"gradient_check": {"element_id": "rect1", "gradient_type": "linearGradient", "min_stops": 2}, "filter_check": {"element_id": "rect1", "expected_filter_type": "feDropShadow"}, "stroke_check": {"element_id": "rect1", "expected_stroke": "none"}}`
- **Steps**: 3 — apply gradient + apply drop shadow + remove stroke

---

#### Task 2-6: Rotate + Flip + Change Color

- **Instruction**: Open `/home/user/Documents/star_polygon.svg` in Inkscape. (1) Rotate the hexagon (id=hexagon1) 45 degrees clockwise. (2) Flip the triangle (id=triangle1) horizontally (Object > Flip Horizontal). (3) Change the fill color of the star (id=star1) to gold (`#ffd700`). Save the file.
- **Upload Resources**: `star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_multi_transform` (composite)
- **result**: `vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**: `rule` → `{"transform_check_1": {"element_id": "hexagon1", "expected_transform_contains": "rotate"}, "transform_check_2": {"element_id": "triangle1", "expected_transform_contains": "scale(-1"}, "fill_check": {"element_id": "star1", "expected_fill": "#ffd700"}}`
- **Steps**: 3 — rotate one element + flip another + recolor a third (3 different elements)

---

#### Task 2-7: Restyle Text: Color + Bold + Font Change

- **Instruction**: Open `/home/user/Documents/text_hello.svg` in Inkscape. (1) Change the title text color to red (`#ff0000`). (2) Make the title text bold. (3) Change the title text font family to "DejaVu Serif". Save the file.
- **Upload Resources**: `text_hello.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_text_style`
- **result**: `vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**: `rule` → `{"element_id": "text_title", "expected_fill": "#ff0000", "expected_font_weight": "bold", "expected_font_family": "DejaVu Serif"}`
- **Steps**: 3 — change color + toggle bold + change font family (all on same element via different panels)

---

#### Task 2-8: Reorder Layers + Rename + Hide

- **Instruction**: Open `/home/user/Documents/three_layers.svg` in Inkscape. (1) Move the "Labels" layer below the "Shapes" layer so the order from bottom to top is: Background, Labels, Shapes. (2) Rename the "Shapes" layer to "Main Shapes". (3) Hide the "Background" layer. Save the file.
- **Upload Resources**: `three_layers.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_layer_ops` (composite)
- **result**: `vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**: `rule` → `{"order_check": {"expected_order": ["Background", "Labels", "Main Shapes"]}, "rename_check": {"layer_id": "layer2", "expected_label": "Main Shapes"}, "visibility_check": {"layer_label": "Background", "expected_visible": false}}`
- **Steps**: 3 — reorder layers + rename a layer + hide a layer

---

#### Task 2-9: Group Objects + Apply Transform to Group

- **Instruction**: Open `/home/user/Documents/star_polygon.svg` in Inkscape. (1) Select the hexagon (id=hexagon1) and triangle (id=triangle1) and group them together (Object > Group). (2) Rotate the entire group 30 degrees clockwise. (3) Change the fill color of the hexagon (inside the group) to teal (`#008080`). Save the file.
- **Upload Resources**: `star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_group_transform` (composite)
- **result**: `vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**: `rule` → `{"group_check": {"expected_children_ids": ["hexagon1", "triangle1"], "require_group": true}, "group_has_transform": "rotate", "fill_check": {"element_id": "hexagon1", "expected_fill": "#008080"}}`
- **Steps**: 3 — group 2 elements + rotate the group + enter group to recolor a child

---

#### Task 2-10: Convert to Path + Edit Stroke Style

- **Instruction**: Open `/home/user/Documents/simple_rect_circle.svg` in Inkscape. (1) Select the blue rectangle (id=rect1) and convert it to a path (Path > Object to Path). (2) Change the stroke of the converted path to a dashed line. (3) Change the stroke color to red (`#ff0000`) with stroke width 4. Save the file.
- **Upload Resources**: `simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_path_stroke` (composite)
- **result**: `vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**: `rule` → `{"path_check": {"original_id": "rect1", "expected_tag": "path"}, "dash_check": {"element_id": "rect1", "expect_dash": true}, "stroke_check": {"element_id": "rect1", "expected_stroke": "#ff0000", "expected_stroke_width": "4"}}`
- **Steps**: 3 — convert to path + set dash + set stroke color/width

---

#### Task 2-11: Scale All + Resize Document + Add Guide

- **Instruction**: Open `/home/user/Documents/logo_design.svg` in Inkscape. (1) Select all objects (Ctrl+A) and scale to 200% (double size). (2) Change the document size to 800×800 pixels. (3) Add a horizontal guide line at y=400 (the vertical center). Save the file.
- **Upload Resources**: `logo_design.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_scale_guide` (composite)
- **result**: `vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**: `rule` → `{"doc_check": {"expected_width": "800", "expected_height": "800"}, "guide_check": {"guide_orientation": "horizontal", "guide_position": 400, "tolerance": 5}}`
- **Steps**: 3 — scale all + resize document + add guide

---

#### Task 2-12: Drop Shadow + Z-Order + Duplicate

- **Instruction**: Open `/home/user/Documents/zorder_shapes.svg` in Inkscape. (1) Apply a drop shadow filter to the small green rectangle (id=small_rect) (Filters > Shadows and Glows > Drop Shadow...). (2) Lower the medium circle (id=medium_circle) to the bottom of the z-order. (3) Duplicate the large rectangle (id=large_rect) so there are at least 2 large rectangles. Save the file.
- **Upload Resources**: `zorder_shapes.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_l2_shadow_zorder` (composite)
- **result**: `vm_file` → `/home/user/Documents/zorder_shapes.svg`
- **expected**: `rule` → `{"filter_check": {"element_id": "small_rect", "expected_filter_type": "feDropShadow"}, "zorder_check": {"element_id": "medium_circle", "expected_position": "bottom"}, "count_check": {"element_tag": "rect", "min_count": 3}}`
- **Steps**: 3 — apply filter on element A + change z-order of element B + duplicate element C (3 different elements)

---

### 3.3 Level 3 — Advanced Operations (Multi-step workflow, 4–8 distinct actions, cross-feature coordination)

---

#### Task 3-1: Infographic Dashboard Rebranding + Export

- **Instruction**: Open `/home/user/Documents/infographic_report.svg` in Inkscape. Perform ALL of the following changes: (1) Change the header title from "Annual Report 2024" to "Annual Report 2025". (2) Change the header subtitle from "Company Performance Overview" to "Growth & Strategy Update". (3) Change the revenue value from "$4.2M" to "$5.1M". (4) Change the revenue delta text from "+18% vs last year" to "+21% vs last year". (5) Change the bar chart bar colors from blue (`#3498db`) to green (`#27ae60`) for all 4 bars (bar_q1, bar_q2, bar_q3, bar_q4). (6) Change the footer text from "Confidential — Internal Use Only" to "Public Release". (7) Save the SVG file, then export the entire document as PNG to `/home/user/Documents/report_2025.png` with a width of 2400 pixels.
- **Upload Resources**: `infographic_report.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_infographic_rebrand` (composite)
- **result**: `vm_file` → `/home/user/Documents/infographic_report.svg`
- **expected**: `rule` → `{"text_checks": [{"element_id": "header_title", "expected_text": "Annual Report 2025"}, {"element_id": "header_subtitle", "expected_text": "Growth & Strategy Update"}, {"element_id": "card_left_value", "expected_text": "$5.1M"}, {"element_id": "card_left_delta", "expected_text": "+21% vs last year"}, {"element_id": "footer_text", "expected_text": "Public Release"}], "fill_checks": [{"element_id": "bar_q1", "expected_fill": "#27ae60"}, {"element_id": "bar_q2", "expected_fill": "#27ae60"}, {"element_id": "bar_q3", "expected_fill": "#27ae60"}, {"element_id": "bar_q4", "expected_fill": "#27ae60"}], "png_export": {"expected_path": "/home/user/Documents/report_2025.png", "expected_width": 2400}}`
- **Difficulty**: 7 text/color edits across 2 layers + PNG export — requires navigating a complex multi-layer document

---

#### Task 3-2: Icon Composition from Scattered Parts

- **Instruction**: Open `/home/user/Documents/icon_parts.svg` in Inkscape. The file contains scattered shape primitives. Compose them into a centered app icon by performing these steps: (1) Move the icon_triangle to be centered inside the icon_bg circle (approximately cx=200, cy=200). (2) Move the icon_ring to be concentric with icon_bg (cx=200, cy=200). (3) Change the icon_bg fill to dark blue (`#2c3e50`). (4) Change the icon_triangle fill to white (`#ffffff`). (5) Move the accent_dot to position (310, 110) — top-right corner relative to the icon circle. (6) Change the accent_dot fill to orange (`#f39c12`). (7) Select icon_bg, icon_triangle, icon_ring, and accent_dot and group them into one group. (8) Change the icon_label text to "PlayApp". (9) Save the file.
- **Upload Resources**: `icon_parts.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_icon_composition` (composite)
- **result**: `vm_file` → `/home/user/Documents/icon_parts.svg`
- **expected**: `rule` → `{"fill_checks": [{"element_id": "icon_bg", "expected_fill": "#2c3e50"}, {"element_id": "icon_triangle", "expected_fill": "#ffffff"}, {"element_id": "accent_dot", "expected_fill": "#f39c12"}], "group_check": {"expected_children_ids": ["icon_bg", "icon_triangle", "icon_ring", "accent_dot"], "require_group": true}, "text_check": {"element_id": "icon_label", "expected_text": "PlayApp"}, "geometry_checks": [{"element_id": "accent_dot", "expected_cx": "310", "expected_cy": "110", "tolerance": 20}]}`
- **Difficulty**: 6 moves/recolors + grouping + text edit — requires spatial reasoning and precise element targeting

---

#### Task 3-3: Boolean Operations Pipeline

- **Instruction**: Open `/home/user/Documents/overlapping_circles.svg` in Inkscape. Duplicate both circles (so you have 4 circles total). Select the original two circles and perform a Union (Path > Union). Select the duplicated two circles and perform an Intersection (Path > Intersection). You should end up with exactly 2 path objects and no circle elements remaining. Save the file.
- **Upload Resources**: `overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_boolean_pipeline`
- **result**: `vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**: `rule` → `{"expected_path_count": 2, "no_circle_elements": true}`
- **Difficulty**: Requires careful selection management (select pair A, boolean, then select pair B, boolean) — order-sensitive

---

#### Task 3-4: Layer Composition Workflow with Watermark

- **Instruction**: Open `/home/user/Documents/three_layers.svg` in Inkscape. Perform ALL of the following: (1) Add a new layer named "Watermark" above all existing layers. (2) Switch to the "Watermark" layer and create a text element with content "DRAFT" in font size 72px. (3) Set the "Watermark" layer opacity to 30%. (4) Hide the "Labels" layer. (5) Rename the "Shapes" layer to "Main Content". (6) Move the "Background" layer's background rectangle fill color from `#f0f0f0` to light yellow `#fffde7`. (7) Save the file.
- **Upload Resources**: `three_layers.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_layer_workflow` (composite)
- **result**: `vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**: `rule` → `{"new_layer_label": "Watermark", "watermark_text": "DRAFT", "watermark_font_size": "72", "watermark_opacity": "0.3", "labels_hidden": true, "renamed_layer": {"layer_id": "layer2", "expected_label": "Main Content"}, "bg_fill_check": {"element_id": "bg_rect", "expected_fill": "#fffde7"}}`
- **Difficulty**: 7 distinct layer/property actions spanning 4 different layers — add, rename, hide, opacity, recolor

---

#### Task 3-5: Complex Path Editing + Style + Z-Order

- **Instruction**: Open `/home/user/Documents/complex_path.svg` in Inkscape. Perform ALL of the following: (1) Change the zigzag polyline stroke color to blue (`#0000ff`) and stroke width to 4. (2) Change the zigzag stroke to a dashed line style. (3) Apply a Gaussian blur filter to the blob_shape. (4) Delete the spiral_path element entirely. (5) Raise the complex_curve element to the top of the z-order. (6) Change the complex_shape fill to orange (`#ff8c00`). (7) Save the file.
- **Upload Resources**: `complex_path.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_complex_path_workflow` (composite)
- **result**: `vm_file` → `/home/user/Documents/complex_path.svg`
- **expected**: `rule` → `{"stroke_check": {"element_id": "zigzag", "expected_stroke": "#0000ff", "expected_stroke_width": "4"}, "dash_check": {"element_id": "zigzag", "expect_dash": true}, "filter_check": {"element_id": "blob_shape", "expected_filter_type": "feGaussianBlur"}, "deleted_id": "spiral_path", "zorder_check": {"element_id": "complex_curve", "expected_position": "top"}, "fill_check": {"element_id": "complex_shape", "expected_fill": "#ff8c00"}}`
- **Difficulty**: 7 actions across stroke/dash/filter/delete/z-order/fill — must handle 5 different elements

---

#### Task 3-6: Full Poster Design Workflow + PDF Export

- **Instruction**: Open `/home/user/Documents/poster_template.svg` in Inkscape. Perform ALL of the following steps: (1) Change the title text from "DESIGN" to "INKSCAPE". (2) Change the subtitle from "CONFERENCE 2024" to "WORKSHOP 2025". (3) Change the background color from dark (`#1a1a2e`) to navy blue (`#001f3f`). (4) Change the accent color of the top bar from `#e94560` to orange (`#ff8c00`). (5) Add a new rectangle (any size, any color) in the Content layer. (6) Change the document size to 595×842 (A4). (7) Save the SVG file. (8) Export the document as PDF to `/home/user/Documents/final_poster.pdf`.
- **Upload Resources**: `poster_template.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_full_poster_workflow` (composite)
- **result**: `vm_file` → `/home/user/Documents/poster_template.svg`
- **expected**: `rule` → `{"text_checks": [{"element_id": "poster_title", "expected_text": "INKSCAPE"}, {"element_id": "poster_subtitle", "expected_text": "WORKSHOP 2025"}], "fill_checks": [{"element_id": "poster_bg", "expected_fill": "#001f3f"}, {"element_id": "poster_topbar", "expected_fill": "#ff8c00"}], "content_layer_has_rect": true, "doc_size": {"expected_width": "595", "expected_height": "842"}, "pdf_export_path": "/home/user/Documents/final_poster.pdf"}`
- **Difficulty**: 8 actions: 2 text edits + 2 color changes + draw shape + resize doc + save + export PDF

---

#### Task 3-7: Multi-Shape Boolean + Gradient + Group + Export

- **Instruction**: Open `/home/user/Documents/star_polygon.svg` in Inkscape. Perform ALL of the following: (1) Select the hexagon (id=hexagon1) and the triangle (id=triangle1), then perform a Union boolean operation (Path > Union), producing a single merged path. (2) Apply a linear gradient fill to the merged path with at least 2 color stops. (3) Apply a drop shadow filter (Filters > Shadows and Glows > Drop Shadow) to the five-pointed star (id=star1). (4) Rotate the star 30 degrees clockwise. (5) Select both the merged path and the star, and group them together. (6) Change the document size to 600×600 (square). (7) Save the SVG. (8) Export the document as PNG to `/home/user/Documents/composed_shapes.png` with width 1200 pixels.
- **Upload Resources**: `star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_shape_composition_workflow` (composite)
- **result**: `vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**: `rule` → `{"boolean_check": {"original_ids": ["hexagon1", "triangle1"], "max_remaining": 1, "require_path": true}, "gradient_on_merged": true, "filter_check": {"element_id": "star1", "expected_filter_type": "feDropShadow"}, "transform_check": {"element_id": "star1", "expected_transform_contains": "rotate"}, "has_group_with_two_children": true, "doc_size": {"expected_width": "600", "expected_height": "600"}, "png_export": {"expected_path": "/home/user/Documents/composed_shapes.png", "expected_width": 1200}}`
- **Difficulty**: 8 actions spanning boolean ops, gradient, filter, transform, group, doc resize, export — tests nearly all L2 features in one flow

---

#### Task 3-8: Infographic Dashboard Layer Surgery + Conditional Export

- **Instruction**: Open `/home/user/Documents/infographic_report.svg` in Inkscape. Perform ALL of the following: (1) Hide the "Footer" layer. (2) Lock the "Header" layer (set it to locked so it cannot be edited). (3) In the "Content" layer, delete the entire right card (card_right, card_right_title, donut_outer, donut_inner, donut_label) — all 5 elements. (4) Resize the center card (card_center) to width=720 so it spans the center+right area (set x=420, width=720). (5) Add a new text element "Expanded View" with font-size 18px anywhere inside the center card area. (6) Change the document width from 1200 to 1000 (keep height 800). (7) Save the SVG. (8) Export the document as PNG to `/home/user/Documents/dashboard_slim.png` with width 2000 pixels.
- **Upload Resources**: `infographic_report.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_dashboard_surgery` (composite)
- **result**: `vm_file` → `/home/user/Documents/infographic_report.svg`
- **expected**: `rule` → `{"footer_hidden": true, "header_locked": true, "deleted_ids": ["card_right", "card_right_title", "donut_outer", "donut_inner", "donut_label"], "geometry_check": {"element_id": "card_center", "expected_width": "720", "tolerance": 10}, "new_text_contains": "Expanded View", "doc_size": {"expected_width": "1000", "expected_height": "800"}, "png_export": {"expected_path": "/home/user/Documents/dashboard_slim.png", "expected_width": 2000}}`
- **Difficulty**: 8 actions spanning hide layer, lock layer, delete 5 elements, resize element, add text, resize doc, export — requires navigating a 4-layer document and bulk deletion

---

#### Task 3-9: Create Tiled Pattern with Clones, Alignment, and Style

- **Instruction**: Open `/home/user/Documents/logo_design.svg` in Inkscape. Perform ALL of the following: (1) Select all objects and group them into a single group. (2) Create 3 clones of this group (Edit > Clone > Create Clone, three times). (3) Arrange the original + 3 clones in a 2×2 grid layout (move them so they tile evenly). (4) Change the document size to 800×800. (5) Add a new layer named "Overlay" above all layers. (6) In the "Overlay" layer, add a large semi-transparent white rectangle covering the entire canvas (fill `#ffffff`, opacity 20%). (7) Save the SVG. (8) Export the document as PNG to `/home/user/Documents/tiled_logo.png` with width 1600 pixels.
- **Upload Resources**: `logo_design.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_tiled_pattern_workflow` (composite)
- **result**: `vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**: `rule` → `{"min_use_elements": 3, "doc_size": {"expected_width": "800", "expected_height": "800"}, "overlay_layer": {"label": "Overlay", "has_rect": true, "rect_fill": "#ffffff", "rect_opacity_max": 0.3}, "png_export": {"expected_path": "/home/user/Documents/tiled_logo.png", "expected_width": 1600}}`
- **Difficulty**: 8 actions: group, 3× clone, arrange 2×2 grid, resize doc, add layer, semi-transparent overlay rect, export — tests spatial layout + layer management

---

#### Task 3-10: Multi-Text Poster Edit + Gradient Restyle + New Layer + Dual Export

- **Instruction**: Open `/home/user/Documents/poster_template.svg` in Inkscape. Perform ALL of the following: (1) Change the poster title to "INNOVATION". (2) Change the subtitle to "SUMMIT 2026". (3) Replace the solid background color with a radial gradient (dark center `#0d0d2b`, lighter edge `#1a1a4e`). (4) Change the accent top bar from `#e94560` to a linear gradient going from `#ff6b6b` (left) to `#ffa502` (right). (5) Add a new layer named "Badge" above all existing layers. (6) In the "Badge" layer, draw a circle (any size) with fill `#ffd700` (gold) and draw a text element "NEW" in font-size 18px. (7) Hide the Content layer (if present). (8) Save the SVG. (9) Export as PNG to `/home/user/Documents/innovation_poster.png` with width 1190. (10) Also export as PDF to `/home/user/Documents/innovation_poster.pdf`.
- **Upload Resources**: `poster_template.svg` → `/home/user/Documents/`
- **Evaluator**: `check_inkscape_dual_export_poster` (composite)
- **result**: `vm_file` → `/home/user/Documents/poster_template.svg`
- **expected**: `rule` → `{"text_checks": [{"element_id": "poster_title", "expected_text": "INNOVATION"}, {"element_id": "poster_subtitle", "expected_text": "SUMMIT 2026"}], "bg_has_radial_gradient": true, "topbar_has_linear_gradient": true, "badge_layer": {"label": "Badge", "has_circle_with_fill": "#ffd700", "has_text_containing": "NEW"}, "content_hidden_or_absent": true, "png_export": {"expected_path": "/home/user/Documents/innovation_poster.png", "expected_width": 1190}, "pdf_export": {"expected_path": "/home/user/Documents/innovation_poster.pdf", "min_size_bytes": 500}}`
- **Difficulty**: 10 actions: 2 text edits, 2 gradient replacements (radial + linear), add layer, draw circle + text in new layer, hide a layer, dual-format export — the hardest task, tests every major feature domain

---

## 4. New Evaluator Functions Specification

### 4.1 `check_inkscape_fill_color`

```python
def check_inkscape_fill_color(svg_file_path, rule):
    """
    Args:
        svg_file_path: Path to SVG file
        rule: {"element_id": "rect1", "expected_fill": "#ff0000"}
              also handles expected_fill="none"
    Returns:
        float: 1.0 if fill color matches, 0.0 otherwise
    """
    tree = ET.parse(svg_file_path)
    root = tree.getroot()
    elem = root.find(f'.//*[@id="{rule["element_id"]}"]')
    if elem is None:
        return 0.0
    style = elem.get('style', '')
    fill = extract_property(style, 'fill') or elem.get('fill', '')
    return 1.0 if normalize_color(fill) == normalize_color(rule['expected_fill']) else 0.0
```

---

### 4.2 `check_inkscape_stroke`

```python
def check_inkscape_stroke(svg_file_path, rule):
    """
    rule: {"element_id": "circle1", "expected_stroke": "#00ff00", "expected_stroke_width": "5"}
    """
```

---

### 4.3 `check_inkscape_element_geometry`

```python
def check_inkscape_element_geometry(svg_file_path, rule):
    """
    rule: {"element_id": "rect1", "expected_width": "400", "expected_height": "200", "tolerance": 5}
          or {"element_id": "rect1", "expected_x": "300", "expected_y": "250", "tolerance": 5}
          or {"element_id": "logo_outer", "expected_scale_factor": 1.5, "tolerance": 0.05}
    """
```

---

### 4.4 `check_inkscape_text_content`

```python
def check_inkscape_text_content(svg_file_path, rule):
    """
    rule: {"element_id": "text_title", "expected_text": "Welcome to Inkscape"}
    """
```

---

### 4.5 `check_inkscape_text_style`

```python
def check_inkscape_text_style(svg_file_path, rule):
    """
    rule: any combination of:
      {"element_id": "...", "expected_font_size": "72",
       "expected_fill": "#ff0000", "expected_font_weight": "bold",
       "expected_font_style": "italic", "expected_font_family": "DejaVu Sans"}
    Returns 1.0 only if ALL specified keys match.
    """
```

---

### 4.6 `check_inkscape_text_align`

```python
def check_inkscape_text_align(svg_file_path, rule):
    """
    rule: {"element_id": "text_left", "expected_text_anchor": "middle"}
    Check text-anchor style property or text-align for flowRoot.
    """
```

---

### 4.7 `check_inkscape_layer_visibility`

```python
def check_inkscape_layer_visibility(svg_file_path, rule):
    """
    rule: {"layer_label": "Labels", "expected_visible": false}
    Find <g inkscape:groupmode="layer" inkscape:label="Labels">,
    check style "display:none" (hidden) vs "display:inline" (visible).
    """
```

---

### 4.8 `check_inkscape_layer_name`

```python
def check_inkscape_layer_name(svg_file_path, rule):
    """
    rule: {"layer_id": "layer2", "expected_label": "Geometric Objects"}
    """
```

---

### 4.9 `check_inkscape_add_layer`

```python
def check_inkscape_add_layer(svg_file_path, rule):
    """
    rule: {"expected_layer_label": "Annotations"}
    Search all <g inkscape:groupmode="layer"> for matching inkscape:label.
    """
```

---

### 4.9b `check_inkscape_layer_lock`

```python
def check_inkscape_layer_lock(svg_file_path, rule):
    """
    rule: {"layer_label": "Header", "expected_locked": true}
    Find <g inkscape:groupmode="layer" inkscape:label="Header">,
    check sodipodi:insensitive="true" (locked) or absent (unlocked).
    """
```

---

### 4.10 `check_inkscape_element_count`

```python
def check_inkscape_element_count(svg_file_path, rule):
    """
    rule: {"element_tag": "rect", "min_count": 2}
         or {"element_tag": "circle", "min_count": 2, "also_tag": "ellipse", "combined_min": 2}
    Handles SVG namespace prefix automatically.
    """
```

---

### 4.11 `check_inkscape_boolean_operation`

```python
def check_inkscape_boolean_operation(svg_file_path, rule):
    """
    rule: {"original_ids": ["circle_left", "circle_right"], "max_remaining": 1, "require_path": true}
    """
```

---

### 4.12 `check_inkscape_transform`

```python
def check_inkscape_transform(svg_file_path, rule):
    """
    rule: {"element_id": "hexagon1", "expected_transform_contains": "rotate"}
          or {"element_id": "star1", "expected_transform_contains": "scale(-1"}
    """
```

---

### 4.13 `check_inkscape_opacity`

```python
def check_inkscape_opacity(svg_file_path, rule):
    """
    rule: {"element_id": "circle_left", "expected_opacity": "0.5", "tolerance": "0.05"}
    Check style "opacity" property (master opacity).
    """
```

---

### 4.14 `check_inkscape_gradient`

```python
def check_inkscape_gradient(svg_file_path, rule):
    """
    rule: {"element_id": "rect1", "gradient_type": "linearGradient", "min_stops": 2}
    Check fill is url(#id), find gradient in <defs>, verify type and stop count.
    """
```

---

### 4.15 `check_inkscape_radial_gradient`

```python
def check_inkscape_radial_gradient(svg_file_path, rule):
    """
    rule: {"element_id": "plain_rect", "gradient_type": "radialGradient"}
    Shorthand that calls check_inkscape_gradient with radialGradient type.
    """
```

---

### 4.16 `check_inkscape_filter`

```python
def check_inkscape_filter(svg_file_path, rule):
    """
    rule: {"element_id": "rect1", "expected_filter_type": "feGaussianBlur"}
          or {"element_id": "star1", "expected_filter_type": "feDropShadow"}
    Check element filter="url(#id)", find filter in <defs>, check for primitive.
    """
```

---

### 4.17 `check_inkscape_clone_exists`

```python
def check_inkscape_clone_exists(svg_file_path, rule):
    """
    rule: {"source_id": "logo_outer", "min_clones": 2}
    Find all <use xlink:href="#source_id"> elements.
    """
```

---

### 4.18 `check_inkscape_document_properties`

```python
def check_inkscape_document_properties(svg_file_path, rule):
    """
    rule: {"expected_width": "1920", "expected_height": "1080"}
    Read root <svg> width/height attributes (strip units like "px").
    """
```

---

### 4.19 `check_inkscape_export_png`

```python
def check_inkscape_export_png(command_output, rule):
    """
    command_output: "1024,768,PNG"
    rule: {"expected_path": "/home/user/output.png", "expected_width": 1024}
    """
```

---

### 4.20 `check_inkscape_export_pdf`

```python
def check_inkscape_export_pdf(command_output, rule):
    """
    command_output: "True,12345"
    rule: {"expected_path": "/home/user/output.pdf", "min_size_bytes": 500}
    """
```

---

### 4.21 `check_inkscape_element_deleted`

```python
def check_inkscape_element_deleted(svg_file_path, rule):
    """
    rule: {"deleted_element_id": "circle1"}
    Returns 1.0 if element with given id NOT found (deleted successfully).
    """
```

---

### 4.22 `check_inkscape_layer_order`

```python
def check_inkscape_layer_order(svg_file_path, rule):
    """
    rule: {"expected_order": ["Background", "Labels", "Shapes"]}
    In SVG, layers are <g> elements; lower index in document = lower in stack.
    """
```

---

### 4.23 `check_inkscape_group_children`

```python
def check_inkscape_group_children(svg_file_path, rule):
    """
    rule: {"expected_children_ids": ["hexagon1", "triangle1"], "require_group": true}
    Verify all expected children share the same immediate <g> parent.
    """
```

---

### 4.24 `check_inkscape_ungroup`

```python
def check_inkscape_ungroup(svg_file_path, rule):
    """
    rule: {"ungrouped_id": "group1", "expected_free_ids": ["inner_rect", "inner_circle"]}
    Verify group1 no longer exists OR its children are direct layer children.
    """
```

---

### 4.25 `check_inkscape_zorder`

```python
def check_inkscape_zorder(svg_file_path, rule):
    """
    rule: {"element_id": "large_rect", "expected_position": "top"}
          or {"element_id": "small_rect", "expected_position": "bottom"}
    "top" = last child of its parent in document order (renders on top).
    "bottom" = first child of its parent.
    """
```

---

### 4.26 `check_inkscape_stroke_dasharray`

```python
def check_inkscape_stroke_dasharray(svg_file_path, rule):
    """
    rule: {"element_id": "rect1", "expect_dash": true}
    Check style contains stroke-dasharray with a non-empty value (not "none").
    """
```

---

### 4.27 `check_inkscape_stroke_linecap`

```python
def check_inkscape_stroke_linecap(svg_file_path, rule):
    """
    rule: {"element_id": "diagonal_line", "expected_linecap": "round"}
    Check style stroke-linecap property.
    """
```

---

### 4.28 `check_inkscape_fill_rule`

```python
def check_inkscape_fill_rule(svg_file_path, rule):
    """
    rule: {"element_id": "star1", "expected_fill_rule": "evenodd"}
    Check style fill-rule property (evenodd or nonzero).
    """
```

---

### 4.29 `check_inkscape_object_to_path`

```python
def check_inkscape_object_to_path(svg_file_path, rule):
    """
    rule: {"original_id": "rect1", "expected_tag": "path"}
    Find element by id; verify its tag is now {svg_ns}path.
    """
```

---

### 4.30 `check_inkscape_align`

```python
def check_inkscape_align(svg_file_path, rule):
    """
    rule: {"element_ids": ["rect_bottom", "rect_middle", "rect_top"],
           "align_axis": "horizontal_center", "page_width": 800, "tolerance": 10}
    For horizontal_center: check that cx (x + width/2) ≈ page_width/2 for all elements.
    """
```

---

### 4.31 `check_inkscape_snap_to_grid`

```python
def check_inkscape_snap_to_grid(svg_file_path, rule):
    """
    rule: {"guide_orientation": "horizontal", "guide_position": 300, "tolerance": 2}
    Find <sodipodi:guide> elements in <sodipodi:namedview>.
    Check orientation and position attribute.
    """
```

---

### 4.32 `check_inkscape_duplicate`

```python
def check_inkscape_duplicate(svg_file_path, rule):
    """
    rule: {"original_id": "rect1", "min_similar_count": 2}
    Count elements with same tag and similar style/dimensions as original_id.
    """
```

---

### 4.33 Composite Evaluators (Level 2)

| Evaluator | Components | Task |
|-----------|-----------|------|
| `check_inkscape_l2_boolean_restyle` | boolean_operation + fill_color + stroke | 2-1 |
| `check_inkscape_l2_boolean_move` | boolean_operation + fill_color | 2-2 |
| `check_inkscape_l2_blur_opacity` | filter + opacity + fill_color | 2-3 |
| `check_inkscape_l2_clone_restyle` | clone_exists + fill_color + document_properties | 2-4 |
| `check_inkscape_l2_gradient_shadow` | gradient + filter + stroke | 2-5 |
| `check_inkscape_l2_multi_transform` | transform × 2 + fill_color | 2-6 |
| (reuse `check_inkscape_text_style`) | text_style (3 properties) | 2-7 |
| `check_inkscape_l2_layer_ops` | layer_order + layer_name + layer_visibility | 2-8 |
| `check_inkscape_l2_group_transform` | group_children + transform + fill_color | 2-9 |
| `check_inkscape_l2_path_stroke` | object_to_path + stroke_dasharray + stroke | 2-10 |
| `check_inkscape_l2_scale_guide` | document_properties + snap_to_grid | 2-11 |
| `check_inkscape_l2_shadow_zorder` | filter + zorder + element_count | 2-12 |

### 4.34 Composite Evaluators (Level 3)

| Evaluator | Components | Task |
|-----------|-----------|------|
| `check_inkscape_infographic_rebrand` | text_content × 5 + fill_color × 4 + export_png | 3-1 |
| `check_inkscape_icon_composition` | fill_color × 3 + group_children + text_content + element_geometry | 3-2 |
| `check_inkscape_boolean_pipeline` | element_count (path) + no circles | 3-3 |
| `check_inkscape_layer_workflow` | add_layer + text_content + text_style + opacity + layer_visibility + layer_name + fill_color | 3-4 |
| `check_inkscape_complex_path_workflow` | stroke + stroke_dasharray + filter + element_deleted + zorder + fill_color | 3-5 |
| `check_inkscape_full_poster_workflow` | text_content × 2 + fill_color × 2 + element_count + document_properties + export_pdf | 3-6 |
| `check_inkscape_shape_composition_workflow` | boolean_operation + gradient + filter + transform + group_children + document_properties + export_png | 3-7 |
| `check_inkscape_dashboard_surgery` | layer_visibility + layer_lock + element_deleted × 5 + element_geometry + text_content + document_properties + export_png | 3-8 |
| `check_inkscape_tiled_pattern_workflow` | clone_exists + document_properties + add_layer + opacity + fill_color + export_png | 3-9 |
| `check_inkscape_dual_export_poster` | text_content × 2 + radial_gradient + linear_gradient + add_layer + fill_color + text_content + layer_visibility + export_png + export_pdf | 3-10 |

---

## 5. Task Summary

```
Level 1 (Basic) — 32 Tasks
─────────────────────────────────────────────────────
Category: Fill & Color
  Task 1-1   Change Rectangle Fill Color
  Task 1-15  Change Text Color
  Task 1-32  Remove Fill (Set to None)

Category: Stroke
  Task 1-2   Change Circle Stroke Color/Width
  Task 1-22  Change Stroke Dash Style
  Task 1-23  Change Stroke Line Cap

Category: Shape Geometry & Transform
  Task 1-3   Resize Rectangle
  Task 1-9   Move Element to Coordinates
  Task 1-27  Rotate Element 90 Degrees
  Task 1-35  Scale Element Uniformly

Category: Drawing Tools
  Task 1-12  Draw a Rectangle (R key)
  Task 1-24  Draw an Ellipse (E key)
  Task 1-25  Draw a Straight Line (B key)

Category: Text
  Task 1-4   Change Text Content
  Task 1-5   Change Text Font Size
  Task 1-13  Make Text Bold
  Task 1-16  Change Text Alignment to Center
  Task 1-33  Add a Text Element
  Task 1-34  Change Font Family

Category: Object Operations
  Task 1-8   Delete an Element
  Task 1-19  Ungroup a Group
  Task 1-30  Convert Shape to Path

Category: Z-Order
  Task 1-20  Raise Element to Top

Category: Layer Operations
  Task 1-6   Hide a Layer
  Task 1-7   Rename a Layer
  Task 1-18  Add a New Layer

Category: Fill Style
  Task 1-11  Change Element Opacity
  Task 1-26  Add Radial Gradient
  Task 1-31  Change Fill Rule to Even-Odd

Category: Document & Layout
  Task 1-10  Change Document Size
  Task 1-29  Align Elements to Canvas Center
  Task 1-36  Add a Guide Line


Level 2 (Intermediate) — 12 Tasks (each combines 3 actions from different feature domains)
─────────────────────────────────────────────────────
Category: Boolean + Restyle
  Task 2-1   Boolean Union + Recolor + Stroke
  Task 2-2   Boolean Difference + Move + Recolor

Category: Filter + Property
  Task 2-3   Gaussian Blur + Opacity + Fill Change
  Task 2-5   Linear Gradient + Drop Shadow + Remove Stroke

Category: Clone + Document
  Task 2-4   Clone ×2 + Recolor Original + Resize Document

Category: Transform (multi-element)
  Task 2-6   Rotate Element A + Flip Element B + Recolor Element C

Category: Text Styling
  Task 2-7   Text Color + Bold + Font Family Change

Category: Layer Management
  Task 2-8   Reorder Layers + Rename + Hide

Category: Group + Transform
  Task 2-9   Group Objects + Rotate Group + Recolor Child Inside Group

Category: Path + Stroke
  Task 2-10  Convert to Path + Dashed Stroke + Stroke Color/Width

Category: Scale + Layout
  Task 2-11  Scale All 200% + Resize Document + Add Guide

Category: Filter + Z-Order + Duplicate
  Task 2-12  Drop Shadow on A + Lower B to Bottom + Duplicate C


Level 3 (Advanced) — 10 Tasks
─────────────────────────────────────────────────────
Category: Multi-Domain Composition (7+ steps each)
  Task 3-1   Infographic Rebranding + Export (7 edits + PNG)
  Task 3-2   Icon Composition from Scattered Parts (9 steps)
  Task 3-7   Multi-Shape Boolean + Gradient + Group + Export (8 steps)
  Task 3-9   Tiled Pattern with Clones + Overlay + Export (8 steps)

Category: Layer-Intensive Workflows
  Task 3-4   Layer Composition + Rename + Hide + Recolor (7 steps)
  Task 3-8   Dashboard Layer Surgery + Bulk Delete + Export (8 steps)

Category: Path & Style Workflows
  Task 3-3   Boolean Operations Pipeline (4 steps, order-sensitive)
  Task 3-5   Complex Path Editing + Dash + Z-Order (7 steps)

Category: Full Design + Export
  Task 3-6   Full Poster Design + Doc Resize + PDF Export (8 steps)
  Task 3-10  Multi-Text + Dual Gradient + New Layer + Dual Export (10 steps)
```

---

## 6. Evaluator Registration

After implementing evaluator functions, register them in `desktop_env/evaluators/__init__.py`:

```python
from .metrics.inkscape import (
    # Level 1 evaluators
    check_inkscape_fill_color,
    check_inkscape_stroke,
    check_inkscape_element_geometry,
    check_inkscape_text_content,
    check_inkscape_text_style,
    check_inkscape_text_align,
    check_inkscape_layer_visibility,
    check_inkscape_layer_name,
    check_inkscape_add_layer,
    check_inkscape_layer_lock,
    check_inkscape_element_deleted,
    check_inkscape_document_properties,
    check_inkscape_opacity,
    check_inkscape_element_count,
    check_inkscape_ungroup,
    check_inkscape_zorder,
    check_inkscape_stroke_dasharray,
    check_inkscape_stroke_linecap,
    check_inkscape_fill_rule,
    check_inkscape_object_to_path,
    check_inkscape_radial_gradient,
    check_inkscape_align,
    check_inkscape_snap_to_grid,
    check_inkscape_duplicate,
    # Level 2 evaluators (atomic, reused as building blocks)
    check_inkscape_boolean_operation,
    check_inkscape_filter,
    check_inkscape_clone_exists,
    check_inkscape_gradient,
    check_inkscape_transform,
    check_inkscape_layer_order,
    check_inkscape_group_children,
    # Level 2 composite evaluators
    check_inkscape_l2_boolean_restyle,
    check_inkscape_l2_boolean_move,
    check_inkscape_l2_blur_opacity,
    check_inkscape_l2_clone_restyle,
    check_inkscape_l2_gradient_shadow,
    check_inkscape_l2_multi_transform,
    check_inkscape_l2_layer_ops,
    check_inkscape_l2_group_transform,
    check_inkscape_l2_path_stroke,
    check_inkscape_l2_scale_guide,
    check_inkscape_l2_shadow_zorder,
    # Level 3 evaluators
    check_inkscape_export_png,
    check_inkscape_export_pdf,
    check_inkscape_infographic_rebrand,
    check_inkscape_icon_composition,
    check_inkscape_boolean_pipeline,
    check_inkscape_layer_workflow,
    check_inkscape_complex_path_workflow,
    check_inkscape_full_poster_workflow,
    check_inkscape_shape_composition_workflow,
    check_inkscape_dashboard_surgery,
    check_inkscape_tiled_pattern_workflow,
    check_inkscape_dual_export_poster,
)
```

Then add each to the `eval_funcs` dict in the same file.

---

## 7. Implementation Notes

1. **SVG is XML**: Use `xml.etree.ElementTree` with namespace registration:
   ```python
   ET.register_namespace('', 'http://www.w3.org/2000/svg')
   ET.register_namespace('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
   ET.register_namespace('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd')
   ```

2. **Style parsing**: Inkscape stores visual properties in the `style` attribute as CSS key-value pairs. Helper:
   ```python
   def parse_style(style_str):
       return dict(item.split(':') for item in style_str.split(';') if ':' in item)
   ```

3. **Color normalization**: Colors may appear as `#ff0000`, `#FF0000`, `#f00`, `rgb(255,0,0)`, or named colors like `red`. Expand shorthand hex and lowercase before comparison.

4. **Tolerance for geometry**: Use numeric tolerance when comparing positions/sizes as Inkscape may add decimal precision.

5. **Launch path**: Always use `/usr/bin/inkscape` as the command — never a bare `inkscape`.

6. **Config execution order**: `upload_file` → `launch` (/usr/bin/inkscape) → `sleep` (3–5 s) → (Agent performs task) → Evaluate.

7. **Export verification**: PNG: use Python PIL to check dimensions. PDF: use `os.path.getsize`. Both via `vm_command_line`.

8. **Z-order in SVG**: In SVG document order, elements listed **later** render **on top**. "Raise to Top" moves the element to be the **last** child of its parent `<g>`.

9. **Layers in SVG**: Inkscape layers are `<g>` elements with `inkscape:groupmode="layer"`. In SVG document order, the **last** `<g>` layer is the **topmost** visible layer.

---

## 8. Comparison with Kdenlive Tasks

| Aspect | Kdenlive | Inkscape |
|--------|----------|----------|
| File format | MLT XML (.kdenlive) | SVG XML (.svg) |
| Parsing method | `xml.etree.ElementTree` | `xml.etree.ElementTree` |
| Launch binary | `/usr/bin/kdenlive` | `/usr/bin/inkscape` |
| L1 focus | Import/organize clips, track mgmt | Shape props, text, layers, z-order, draw tools |
| L2 focus | Effects, transitions, trimming | Boolean ops, filters, gradients, transforms |
| L3 focus | Multi-clip editing + render | Multi-step editing + export (PNG/PDF) |
| Export verification | ffprobe (video codec/duration) | PIL (PNG dimensions) / file size (PDF) |
| Namespace complexity | MLT namespace | SVG + Inkscape + Sodipodi namespaces |
