# Inkscape 任务设计文档（中文）

## 0. Inkscape 启动配置

Inkscape 通过其**绝对路径**启动：

```
/usr/bin/inkscape
```

在所有任务 JSON 配置块中，使用以下形式：

```json
{
  "type": "launch",
  "parameters": {
    "command": ["/usr/bin/inkscape", "/home/user/Documents/file.svg"]
  }
}
```

> **注意**：不要使用裸命令 `inkscape`，必须使用完整路径 `/usr/bin/inkscape`，以确保在测试虚拟机中正确调用。启动后请增加一个 `sleep` 步骤（3–5 秒），以便 GUI 完全初始化再由 agent 开始操作。

典型任务配置顺序：

```json
"config": [
  {"type": "upload_file",  "parameters": {"src": "assets/inkscape/file.svg", "dest": "/home/user/Documents/file.svg"}},
  {"type": "launch",       "parameters": {"command": ["/usr/bin/inkscape", "/home/user/Documents/file.svg"]}},
  {"type": "sleep",        "parameters": {"seconds": 3}}
]
```

---

## 1. 可用资源

所有资源文件位于：`assets/inkscape/`

### 1.1 SVG 文件

| 文件名 | 尺寸 | 大小 | 描述 |
|----------|-----------|------|-------------|
| `simple_rect_circle.svg` | 800×600 | ~856 B | 蓝色矩形（id=rect1）+ 红色圆形（id=circle1），用于基础属性编辑 |
| `text_hello.svg` | 800×600 | ~969 B | 标题 “Hello World”（id=text_title，48px）+ 副标题（id=text_subtitle，24px） |
| `three_layers.svg` | 800×600 | ~1.75 KB | 3 个 Inkscape 图层：Background、Shapes、Labels |
| `star_polygon.svg` | 800×600 | ~1.26 KB | 五角星（id=star1）+ 六边形（id=hexagon1）+ 三角形（id=triangle1）路径 |
| `overlapping_circles.svg` | 800×600 | ~898 B | 两个半透明重叠圆，用于布尔运算 |
| `logo_design.svg` | 400×400 | ~1.35 KB | 同心圆 logo + 字母 “A” + 装饰点 |
| `complex_drawing.svg` | 800×600 | ~2.63 KB | 渐变、模糊/阴影滤镜、克隆圆、旋转文本 |
| `poster_template.svg` | A4 (595×842) | ~3.14 KB | 深色主题会议海报（3 图层） |
| `export_test.svg` | 1024×768 | ~2.77 KB | 乡村风景导出测试场景 |
| `complex_path.svg` | 800×600 | ~1.76 KB | 贝塞尔曲线、螺旋、锯齿、团块路径，用于路径编辑 |
| `grouped_shapes.svg` | 800×600 | ~1.1 KB | 预分组图形（group1: inner_rect + inner_circle）+ 组外 `outer_rect` |
| `multi_rects.svg` | 800×600 | ~900 B | 三个不同位置矩形：rect_bottom、rect_middle、rect_top |
| `zorder_shapes.svg` | 800×600 | ~1.1 KB | 三个重叠图形（large_rect、medium_circle、small_rect），用于层级顺序任务 |
| `shapes_mixed.svg` | 800×600 | ~1.0 KB | 椭圆（ellipse1）、六边形路径（hexagon_path）、直线（diagonal_line） |
| `text_styles.svg` | 800×600 | ~1.3 KB | 五个文本元素，含不同对齐/样式：text_left、text_center、text_right、text_italic、text_multiline |
| `gradient_demo.svg` | 800×600 | ~1.2 KB | `grad_rect`（已有线性渐变）+ `plain_rect`（用于径向渐变任务） |
| `infographic_report.svg` | 1200×800 | ~4.5 KB | 4 图层仪表板（Background、Header、Content、Footer），含卡片、柱状图、环图、文本 |
| `icon_parts.svg` | 800×600 | ~1.2 KB | 分散的图标基础图元（icon_bg、icon_triangle、icon_ring、accent_dot、icon_label） |

### 1.2 关键元素 ID 参考

#### simple_rect_circle.svg
- `rect1`：蓝色矩形，fill:#0000ff，stroke:#000000，width=200，height=100，x=50，y=50
- `circle1`：红色圆形，fill:#ff0000，stroke:#000000，cx=400，cy=200，r=60

#### text_hello.svg
- `text_title`：“Hello World”，font-size:48px，font-family:sans-serif，fill:#333333
- `text_subtitle`：“This is a sample subtitle”，font-size:24px，font-family:serif，fill:#666666

#### three_layers.svg
- `layer1`（label="Background"）：包含 `bg_rect`（fill:#f0f0f0）
- `layer2`（label="Shapes"）：包含 `green_rect`（fill:#00cc00）+ `orange_ellipse`（fill:#ff9900）
- `layer3`（label="Labels"）：包含 `label1`（"Rectangle"）+ `label2`（"Ellipse"）

#### overlapping_circles.svg
- `circle_left`：红色，fill-opacity:0.7，cx=320，cy=300，r=120
- `circle_right`：蓝色，fill-opacity:0.7，cx=480，cy=300，r=120

#### export_test.svg
- `sky`、`ground`、`sun`、`cloud1`、`cloud2`、`house`、`tree1`、`scene_title`

#### complex_path.svg
- `complex_curve`：开放贝塞尔，`complex_shape`：闭合路径，`spiral_path`、`zigzag`、`blob_shape`

#### grouped_shapes.svg
- `group1`：父组，包含 `inner_rect`（绿色矩形）+ `inner_circle`（蓝色圆形）
- `outer_rect`：橙色矩形，不在 group1 内

#### multi_rects.svg
- `rect_bottom`：绿色矩形，y=420
- `rect_middle`：紫色矩形，y=250
- `rect_top`：橙色矩形，y=80

#### zorder_shapes.svg
- `large_rect`：浅蓝矩形，最低层级（文档中最先）
- `medium_circle`：粉色圆形，中间层级
- `small_rect`：浅绿色矩形，最高层级（文档中最后，显示在最上）

#### shapes_mixed.svg
- `ellipse1`：黄色椭圆，cx=400，cy=200，rx=220，ry=120
- `hexagon_path`：紫色六边形 `<path>`
- `diagonal_line`：红色斜线，stroke-width=5

#### text_styles.svg
- `text_left`：32px sans-serif，fill=#000000，左对齐
- `text_center`：36px serif，fill=#0055aa，居中对齐
- `text_right`：28px monospace，fill=#aa0000，右对齐
- `text_italic`：30px sans-serif，fill=#006600，font-style:italic
- `text_multiline`：24px sans-serif，fill=#555555

#### gradient_demo.svg
- `grad_rect`：已有 linearGradient（blue→red，id=grad_blue_red）
- `plain_rect`：无渐变的灰色矩形（径向渐变目标）

#### infographic_report.svg
- 图层：`layer_bg`（Background）、`layer_header`（Header）、`layer_content`（Content）、`layer_footer`（Footer）
- `bg_fill`：全页浅灰背景矩形
- `header_bar`：渐变矩形（id=header_gradient，#2c3e50→#3498db），`header_title`：“Annual Report 2024”，`header_subtitle`：“Company Performance Overview”
- `card_left`：圆角白色卡片，`card_left_title`：“Revenue”，`card_left_value`：“$4.2M”，`card_left_delta`：“+18% vs last year”
- `card_center`：圆角白色卡片，`card_center_title`：“Quarterly Sales”，`bar_q1`–`bar_q4`：蓝色柱状条，`label_q1`–`label_q4`
- `card_right`：圆角白色卡片，`card_right_title`：“Customers”，`donut_outer`（红），`donut_inner`（白），`donut_label`：“12.5K”
- `footer_bar`：深色矩形，`footer_text`：“Confidential — Internal Use Only”

#### icon_parts.svg
- `icon_bg`：大灰色圆，中心 (200,200)，r=150
- `icon_triangle`：黑色三角路径，约在 (500,100)
- `icon_ring`：灰色圆环，中心 (200,450)，r=100
- `accent_dot`：红色小圆，中心 (650,450)，r=20
- `icon_label`：文本 “MyApp Icon”，位置 (400,560)

---

## 2. 评估器函数概览

文件：`desktop_env/evaluators/metrics/inkscape.py`（待创建）

所有评估器都使用 `xml.etree.ElementTree`（带命名空间处理）解析 SVG（XML）文件。

**SVG 命名空间**：
```python
NS = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd',
    'xlink': 'http://www.w3.org/1999/xlink',
}
```

| 函数 | 描述 | result 类型 | expected 类型 |
|----------|-------------|-------------|---------------|
| `check_inkscape_fill_color` | 校验元素填充色 | `vm_file` (.svg) | `rule` |
| `check_inkscape_stroke` | 校验描边属性 | `vm_file` (.svg) | `rule` |
| `check_inkscape_element_geometry` | 校验尺寸/位置 | `vm_file` (.svg) | `rule` |
| `check_inkscape_text_content` | 校验文本内容 | `vm_file` (.svg) | `rule` |
| `check_inkscape_text_style` | 校验字体/字号/字重 | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_visibility` | 校验图层可见性 | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_name` | 校验图层重命名 | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_order` | 校验图层堆叠顺序 | `vm_file` (.svg) | `rule` |
| `check_inkscape_element_count` | 统计指定元素数量 | `vm_file` (.svg) | `rule` |
| `check_inkscape_boolean_operation` | 校验布尔运算结果 | `vm_file` (.svg) | `rule` |
| `check_inkscape_transform` | 校验 transform 属性 | `vm_file` (.svg) | `rule` |
| `check_inkscape_opacity` | 校验元素透明度 | `vm_file` (.svg) | `rule` |
| `check_inkscape_gradient` | 校验渐变存在与类型 | `vm_file` (.svg) | `rule` |
| `check_inkscape_filter` | 校验滤镜是否应用 | `vm_file` (.svg) | `rule` |
| `check_inkscape_clone_exists` | 校验克隆是否存在 | `vm_file` (.svg) | `rule` |
| `check_inkscape_document_properties` | 校验文档尺寸 | `vm_file` (.svg) | `rule` |
| `check_inkscape_export_png` | 校验 PNG 导出 | `vm_command_line` | `rule` |
| `check_inkscape_export_pdf` | 校验 PDF 导出 | `vm_command_line` | `rule` |
| `check_inkscape_path_data` | 校验 path 的 d 属性 | `vm_file` (.svg) | `rule` |
| `check_inkscape_element_deleted` | 校验元素已删除 | `vm_file` (.svg) | `rule` |
| `check_inkscape_group_children` | 校验组内子元素 | `vm_file` (.svg) | `rule` |
| `check_inkscape_ungroup` | 校验已取消编组 | `vm_file` (.svg) | `rule` |
| `check_inkscape_zorder` | 校验元素相对层级 | `vm_file` (.svg) | `rule` |
| `check_inkscape_duplicate` | 校验元素已复制 | `vm_file` (.svg) | `rule` |
| `check_inkscape_align` | 校验元素对齐 | `vm_file` (.svg) | `rule` |
| `check_inkscape_stroke_dasharray` | 校验虚线样式 | `vm_file` (.svg) | `rule` |
| `check_inkscape_fill_rule` | 校验填充规则（even-odd / nonzero） | `vm_file` (.svg) | `rule` |
| `check_inkscape_radial_gradient` | 校验径向渐变应用 | `vm_file` (.svg) | `rule` |
| `check_inkscape_object_to_path` | 校验图形转路径 | `vm_file` (.svg) | `rule` |
| `check_inkscape_snap_to_grid` | 校验网格/参考线定义 | `vm_file` (.svg) | `rule` |
| `check_inkscape_text_align` | 校验 text-anchor / text-align | `vm_file` (.svg) | `rule` |
| `check_inkscape_add_layer` | 校验新增图层 | `vm_file` (.svg) | `rule` |
| `check_inkscape_layer_lock` | 校验图层锁定/解锁 | `vm_file` (.svg) | `rule` |
| `check_inkscape_stroke_linecap` | 校验 stroke-linecap 属性 | `vm_file` (.svg) | `rule` |

---

## 3. 任务定义

### 3.1 Level 1 — 基础操作（单一原子动作，可直接验证）

---

#### Task 1-1: 修改矩形填充颜色
- **Task ID**：`24925fa9-f977-4dce-a495-6094aeb1371f`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=fill+color+object+fill+and+stroke`

- **Instruction**：在 Inkscape 中打开 `/home/user/Documents/simple_rect_circle.svg`。将蓝色矩形的填充色改为红色（`#ff0000`），然后保存文件。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_fill_color`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_id": "rect1", "expected_fill": "#ff0000"}`
- **Atomic feature**：填充颜色编辑（Object > Fill and Stroke）

---

#### Task 1-2: 修改圆形描边颜色和宽度
- **Task ID**：`f0c8ae49-1707-4f19-89c5-be287d6d4a63`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=stroke+paint+stroke+style+width`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。将红色圆的描边颜色改为绿色（`#00ff00`），并将描边宽度设为 5 像素，然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_stroke`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_id": "circle1", "expected_stroke": "#00ff00", "expected_stroke_width": "5"}`
- **Atomic feature**：描边颜色与宽度（Object > Fill and Stroke > Stroke paint / Stroke style）

---

#### Task 1-3: 调整矩形大小
- **Task ID**：`a004f85d-6f1b-4e58-97ea-f6dc7dbf06a1`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=object+resize+W+H+toolbar`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。将蓝色矩形改为 width=400、height=200（使用工具栏 W/H 字段），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_geometry`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_id": "rect1", "expected_width": "400", "expected_height": "200", "tolerance": 5}`
- **Atomic feature**：通过工具栏 W/H 调整尺寸

---

#### Task 1-4: 修改文本内容
- **Task ID**：`d038a497-3399-4bfb-b4a9-82f5437ad84b`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=text+tool+edit+text+content`

- **Instruction**：打开 `/home/user/Documents/text_hello.svg`。将标题文本从 “Hello World” 改为 “Welcome to Inkscape”，然后保存。
- **Upload Resources**：`text_hello.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_text_content`
- **result**：`vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**：`rule` → `{"element_id": "text_title", "expected_text": "Welcome to Inkscape"}`
- **Atomic feature**：文本编辑（Text 工具，T 键）

---

#### Task 1-5: 修改文字字号
- **Task ID**：`7ec1d93d-3fbc-407c-bd5d-527658872de5`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=text+font+size+toolbar`

- **Instruction**：打开 `/home/user/Documents/text_hello.svg`。将标题文字字号改为 72 像素，然后保存。
- **Upload Resources**：`text_hello.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_text_style`
- **result**：`vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**：`rule` → `{"element_id": "text_title", "expected_font_size": "72"}`
- **Atomic feature**：字号设置（Text 工具栏）

---

#### Task 1-6: 隐藏图层
- **Task ID**：`cf32eb72-2c09-47e5-8b12-1661e77f664c`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=layers+dialog+hide+layer`

- **Instruction**：打开 `/home/user/Documents/three_layers.svg`。隐藏 “Labels” 图层，使其不可见，然后保存。
- **Upload Resources**：`three_layers.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_layer_visibility`
- **result**：`vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**：`rule` → `{"layer_label": "Labels", "expected_visible": false}`
- **Atomic feature**：图层可见性开关（Layers 面板眼睛图标）

---

#### Task 1-7: 重命名图层
- **Task ID**：`9fb578ef-2792-4b1e-914a-5d0c272cfd54`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=layer+properties+rename+layer`

- **Instruction**：打开 `/home/user/Documents/three_layers.svg`。将 “Shapes” 图层重命名为 “Geometric Objects”，然后保存。
- **Upload Resources**：`three_layers.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_layer_name`
- **result**：`vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**：`rule` → `{"layer_id": "layer2", "expected_label": "Geometric Objects"}`
- **Atomic feature**：图层重命名（Layer > Layer Properties）

---

#### Task 1-8: 删除元素
- **Task ID**：`7c66c2fd-9188-4f58-9259-7f375f06ad6d`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=select+object+delete`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。删除红色圆形，然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_deleted`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"deleted_element_id": "circle1"}`
- **Atomic feature**：删除元素（选择 + Delete 键）

---

#### Task 1-9: 移动元素到指定位置
- **Task ID**：`e7bdc037-abb1-4df2-a742-fd9a09c33d5f`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=object+X+Y+coordinates+toolbar`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。将蓝色矩形移动到 x=300、y=250（使用工具栏 X/Y 字段），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_geometry`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_id": "rect1", "expected_x": "300", "expected_y": "250", "tolerance": 5}`
- **Atomic feature**：坐标定位（工具栏 X/Y 字段）

---

#### Task 1-10: 修改文档尺寸
- **Task ID**：`9e490e3a-e0ef-4e99-96d3-043c3bb308b0`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=document+properties+page+size`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。将文档尺寸改为 1920×1080 像素（File > Document Properties），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_document_properties`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"expected_width": "1920", "expected_height": "1080"}`
- **Atomic feature**：文档属性画布尺寸

---

#### Task 1-11: 修改元素不透明度
- **Task ID**：`75fc04e3-f0a1-4d3e-9aba-42aa0ef16c7d`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=object+opacity+fill+and+stroke`

- **Instruction**：打开 `/home/user/Documents/overlapping_circles.svg`。将左侧红色圆的主不透明度改为 50%（0.5），然后保存。
- **Upload Resources**：`overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_opacity`
- **result**：`vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**：`rule` → `{"element_id": "circle_left", "expected_opacity": "0.5", "tolerance": "0.05"}`
- **Atomic feature**：主不透明度（Fill and Stroke 或底部工具栏 Opacity）

---

#### Task 1-12: 新增矩形
- **Task ID**：`8ff58466-2928-4691-aa00-fb28e4240f58`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=draw+rectangle+tool`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。使用矩形工具（R 键）在画布任意位置绘制一个新矩形，然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_count`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_tag": "rect", "min_count": 2}`
- **Atomic feature**：矩形绘制工具（R 键）

---

#### Task 1-13: 文字加粗
- **Task ID**：`f333a5ec-c8bb-4cde-9659-707895e86227`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=text+bold+font+weight`

- **Instruction**：打开 `/home/user/Documents/text_hello.svg`。选中标题 “Hello World” 并设为粗体，然后保存。
- **Upload Resources**：`text_hello.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_text_style`
- **result**：`vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**：`rule` → `{"element_id": "text_title", "expected_font_weight": "bold"}`
- **Atomic feature**：字重（文本工具栏 Bold 按钮）

---

#### Task 1-15: 修改文本颜色
- **Task ID**：`eae62104-2a09-4214-b66d-26380336dd39`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=text+fill+color`

- **Instruction**：打开 `/home/user/Documents/text_hello.svg`。将副标题文本填充色改为蓝色（`#0000ff`），然后保存。
- **Upload Resources**：`text_hello.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_fill_color`
- **result**：`vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**：`rule` → `{"element_id": "text_subtitle", "expected_fill": "#0000ff"}`
- **Atomic feature**：文本填充色（选中文本后 Object > Fill and Stroke）

---

#### Task 1-16: 文本对齐改为居中
- **Task ID**：`515259fd-5e7e-43fb-bbb3-c033ae5f3693`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=text+alignment+center`

- **Instruction**：打开 `/home/user/Documents/text_styles.svg`。选中左对齐文本（id=text_left），将其文本对齐改为居中（`text-anchor:middle`），然后保存。
- **Upload Resources**：`text_styles.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_text_align`
- **result**：`vm_file` → `/home/user/Documents/text_styles.svg`
- **expected**：`rule` → `{"element_id": "text_left", "expected_text_anchor": "middle"}`
- **Atomic feature**：文本对齐（文本工具栏居中按钮）

---

#### Task 1-18: 新增图层
- **Task ID**：`2341db29-1d1f-41a0-b438-b9edc4ea9315`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=add+new+layer`

- **Instruction**：打开 `/home/user/Documents/three_layers.svg`。在所有现有图层之上新增名为 “Annotations” 的图层（Layer > Add Layer...），然后保存。
- **Upload Resources**：`three_layers.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_add_layer`
- **result**：`vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**：`rule` → `{"expected_layer_label": "Annotations"}`
- **Atomic feature**：新增图层（Layer > Add Layer）

---

#### Task 1-19: 取消编组
- **Task ID**：`2105bef2-d30b-477c-bb81-bf8492fba005`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=group+ungroup+objects`

- **Instruction**：打开 `/home/user/Documents/grouped_shapes.svg`。选中包含内矩形和内圆的分组（id=group1），执行取消编组（Object > Ungroup 或 Ctrl+Shift+G）。`inner_rect` 和 `inner_circle` 应成为图层的直接子节点，而不再位于组内。保存文件。
- **Upload Resources**：`grouped_shapes.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_ungroup`
- **result**：`vm_file` → `/home/user/Documents/grouped_shapes.svg`
- **expected**：`rule` → `{"ungrouped_id": "group1", "expected_free_ids": ["inner_rect", "inner_circle"]}`
- **Atomic feature**：取消编组（Object > Ungroup）

---

#### Task 1-20: 提升元素到最上层（Z-order）
- **Task ID**：`c90a9935-b8c3-423f-a2f7-3338e66af138`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=raise+selection+to+top+z+order`

- **Instruction**：打开 `/home/user/Documents/zorder_shapes.svg`。选中浅蓝大矩形（id=large_rect），将其提升到最上层（Object > Raise to Top 或 Home 键），然后保存。
- **Upload Resources**：`zorder_shapes.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_zorder`
- **result**：`vm_file` → `/home/user/Documents/zorder_shapes.svg`
- **expected**：`rule` → `{"element_id": "large_rect", "expected_position": "top"}`
- **Atomic feature**：置顶（Object > Raise to Top）

---

#### Task 1-22: 修改描边虚线样式
- **Task ID**：`280d6ad6-64d2-49d5-b509-9f1380d8b38d`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=stroke+dash+pattern`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。选中蓝色矩形，将描边改为虚线样式（Object > Fill and Stroke > Stroke style > Dashes），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_stroke_dasharray`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_id": "rect1", "expect_dash": true}`
- **Atomic feature**：虚线模式（Fill and Stroke > Stroke style）

---

#### Task 1-23: 修改描边端点样式
- **Task ID**：`e96ed526-89c8-44f7-8a4b-0d3139de7c8f`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=stroke+linecap+round+butt+square`

- **Instruction**：打开 `/home/user/Documents/shapes_mixed.svg`。选中红色斜线（id=diagonal_line），将描边端点改为 “round”（Object > Fill and Stroke > Stroke style > Line cap: Round），然后保存。
- **Upload Resources**：`shapes_mixed.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_stroke_linecap`
- **result**：`vm_file` → `/home/user/Documents/shapes_mixed.svg`
- **expected**：`rule` → `{"element_id": "diagonal_line", "expected_linecap": "round"}`
- **Atomic feature**：描边端点（Fill and Stroke > Stroke style）

---

#### Task 1-24: 绘制椭圆
- **Task ID**：`d9c5c781-7241-444a-8aa8-1b86fcb7dd82`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=draw+ellipse+tool`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。使用椭圆工具（E 键）在画布任意位置绘制一个新椭圆并保存。文档中应包含至少一个原始圆之外的新 `<ellipse>` 或 `<circle>` 元素。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_count`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_tag": "circle", "min_count": 2, "also_tag": "ellipse", "combined_min": 2}`
- **Atomic feature**：椭圆/圆形绘制工具（E 键）

---

#### Task 1-25: 绘制直线
- **Task ID**：`2cce379a-24e0-48b7-a0c3-b10dde56d882`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=draw+line+bezier+tool`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。使用贝塞尔/钢笔工具（B 键）直线模式绘制一条约从 (100,500) 到 (700,500) 的直线（单击起点，双击终点），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_count`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_tag": "path", "min_count": 1}`
- **Atomic feature**：贝塞尔/钢笔直线绘制（B 键）

---

#### Task 1-26: 给矩形添加径向渐变
- **Task ID**：`08c42e02-28f6-4cb9-b884-6b0eb972af39`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=radial+gradient+fill`

- **Instruction**：打开 `/home/user/Documents/gradient_demo.svg`。使用渐变工具（G 键）给灰色矩形（id=plain_rect）应用径向渐变填充，然后保存。
- **Upload Resources**：`gradient_demo.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_radial_gradient`
- **result**：`vm_file` → `/home/user/Documents/gradient_demo.svg`
- **expected**：`rule` → `{"element_id": "plain_rect", "gradient_type": "radialGradient"}`
- **Atomic feature**：径向渐变（Gradient 工具，或 Fill and Stroke > Radial gradient）

---

#### Task 1-27: 将元素旋转 90 度
- **Task ID**：`909c8dfe-3b91-43a2-9348-52973f5bf4cd`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=rotate+object+90+degrees`

- **Instruction**：打开 `/home/user/Documents/multi_rects.svg`。选中绿色矩形（id=rect_bottom），将其精确顺时针旋转 90 度（Object > Transform 或工具栏旋转字段），然后保存。
- **Upload Resources**：`multi_rects.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_transform`
- **result**：`vm_file` → `/home/user/Documents/multi_rects.svg`
- **expected**：`rule` → `{"element_id": "rect_bottom", "expected_transform_contains": "rotate"}`
- **Atomic feature**：旋转（工具栏或 Object > Transform）

---

#### Task 1-29: 元素水平居中对齐到画布
- **Task ID**：`a2739a6f-9bc0-4d21-abde-2ab8a37349d6`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=align+distribute+center+on+page`

- **Instruction**：打开 `/home/user/Documents/multi_rects.svg`。选中三个矩形并将它们对齐到页面水平中心（Object > Align and Distribute > Center on vertical axis），然后保存。
- **Upload Resources**：`multi_rects.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_align`
- **result**：`vm_file` → `/home/user/Documents/multi_rects.svg`
- **expected**：`rule` → `{"element_ids": ["rect_bottom", "rect_middle", "rect_top"], "align_axis": "horizontal_center", "page_width": 800, "tolerance": 10}`
- **Atomic feature**：对齐与分布（Shift+Ctrl+A）

---

#### Task 1-30: 图形转路径
- **Task ID**：`f6e9fe88-4e34-4005-9c79-646f8785a83f`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=object+to+path`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。选中蓝色矩形（id=rect1），执行图形转路径（Path > Object to Path）。转换后该元素应为 `<path>`。保存文件。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_object_to_path`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"original_id": "rect1", "expected_tag": "path"}`
- **Atomic feature**：Path > Object to Path（Shift+Ctrl+C）

---

#### Task 1-31: 将填充规则改为 Even-Odd
- **Task ID**：`a0d48bf4-ca01-4455-9522-4bfab9c1ce38`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=fill+rule+evenodd+nonzero`

- **Instruction**：打开 `/home/user/Documents/star_polygon.svg`。选中五角星路径（id=star1），将填充规则改为 “even-odd”（Object > Fill and Stroke > Fill 选项卡 > Even-odd），然后保存。
- **Upload Resources**：`star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_fill_rule`
- **result**：`vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**：`rule` → `{"element_id": "star1", "expected_fill_rule": "evenodd"}`
- **Atomic feature**：填充规则（Fill and Stroke 面板）

---

#### Task 1-32: 移除填充（设为 None）
- **Task ID**：`5f77d948-8abf-47cc-9cc6-853393a1d79c`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=remove+fill+set+none`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。选中蓝色矩形（id=rect1），在 Object > Fill and Stroke 中移除填充（设置为 “None”），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_fill_color`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_id": "rect1", "expected_fill": "none"}`
- **Atomic feature**：填充设为 None（Fill and Stroke 面板的 X 按钮）

---

#### Task 1-33: 新增文本元素
- **Task ID**：`f3bfc3f2-b5b6-4cca-8323-77ac045c3b82`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=create+text+object`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。使用文本工具（T 键）在画布任意位置新增文本元素，内容为 “Inkscape”，然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_count`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"element_tag": "text", "min_count": 1}`
- **Atomic feature**：文本工具（T 键）

---

#### Task 1-34: 修改字体家族
- **Task ID**：`e9fda3aa-2fbf-4d5b-87c0-6830294e6998`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=change+font+family`

- **Instruction**：打开 `/home/user/Documents/text_hello.svg`。选中标题文本（id=text_title），通过文本工具栏字体选择器将字体家族改为 “DejaVu Sans”，然后保存。
- **Upload Resources**：`text_hello.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_text_style`
- **result**：`vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**：`rule` → `{"element_id": "text_title", "expected_font_family": "DejaVu Sans"}`
- **Atomic feature**：字体家族选择器（文本工具栏）

---

#### Task 1-35: 等比缩放元素
- **Task ID**：`c9b13af7-01c1-46aa-b153-f0b752206295`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=scale+object+uniformly`

- **Instruction**：打开 `/home/user/Documents/logo_design.svg`。全选（Ctrl+A）后将整体等比缩放为当前尺寸的 150%（使用 W/H 锁定，并在 Object > Transform > Scale 中输入 150%），然后保存。
- **Upload Resources**：`logo_design.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_element_geometry`
- **result**：`vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**：`rule` → `{"element_id": "logo_outer", "expected_scale_factor": 1.5, "tolerance": 0.05}`
- **Atomic feature**：等比缩放（Object > Transform > Scale）

---

#### Task 1-36: 添加参考线
- **Task ID**：`5cf823e4-f9fa-47c0-8944-9e77fb40ab36`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=guides+create+from+ruler`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。通过双击水平标尺并在参考线对话框输入 300，新增一条 y=300 的水平参考线（Edit > Guides...），然后保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_snap_to_grid`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"guide_orientation": "horizontal", "guide_position": 300, "tolerance": 2}`
- **Atomic feature**：参考线（从标尺拖拽或 Edit > Guides）

---

### 3.2 Level 2 — 中级操作（2–3 个跨功能域组合动作）

---

#### Task 2-1: 布尔并集 + 重着色结果
- **Task ID**：`945862d5-ed15-4cc3-8c59-097f42005308`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=path+union+fill+stroke`

- **Instruction**：打开 `/home/user/Documents/overlapping_circles.svg`。 (1) 选中两个圆并执行并集（Path > Union）。(2) 将合并后路径的填充色改为紫色（`#9b59b6`）。(3) 将该路径描边改为白色（`#ffffff`），宽度设为 3。保存文件。
- **Upload Resources**：`overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_boolean_restyle`（复合）
- **result**：`vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**：`rule` → `{"boolean_check": {"original_ids": ["circle_left", "circle_right"], "max_remaining": 1, "require_path": true}, "fill_check": {"expected_fill": "#9b59b6"}, "stroke_check": {"expected_stroke": "#ffffff", "expected_stroke_width": "3"}}`
- **Steps**：3 — 并集 + 填充改色 + 描边样式调整

---

#### Task 2-2: 布尔差集 + 移动结果
- **Task ID**：`25d40034-a609-40d4-a6c2-1c1ece59c7eb`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=path+difference+move+object+fill`

- **Instruction**：打开 `/home/user/Documents/overlapping_circles.svg`。 (1) 选中两个圆执行差集（Path > Difference）。(2) 将新月形结果移动到画布中心附近（约 x=300, y=200）。(3) 将其填充改为黄色（`#f1c40f`）。保存。
- **Upload Resources**：`overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_boolean_move`（复合）
- **result**：`vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**：`rule` → `{"boolean_check": {"original_ids": ["circle_left", "circle_right"], "max_remaining": 1, "require_path": true}, "fill_check": {"expected_fill": "#f1c40f"}}`
- **Steps**：3 — 差集 + 移动 + 改色

---

#### Task 2-3: 形状模糊 + 修改透明度
- **Task ID**：`e8c44644-d755-48ab-9500-734f4c2e95cd`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=gaussian+blur+opacity+fill`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。 (1) 选中蓝色矩形并应用高斯模糊（Filters > Blurs > Blur...），标准差约 5。 (2) 将主不透明度设为 60%（0.6）。(3) 将填充色改为深灰（`#555555`）。保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_blur_opacity`（复合）
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"filter_check": {"element_id": "rect1", "expected_filter_type": "feGaussianBlur"}, "opacity_check": {"element_id": "rect1", "expected_opacity": "0.6", "tolerance": "0.05"}, "fill_check": {"element_id": "rect1", "expected_fill": "#555555"}}`
- **Steps**：3 — 加模糊 + 改透明度 + 改填充

---

#### Task 2-4: 克隆元素 + 重着色
- **Task ID**：`3b6edea0-506d-413f-a7d9-c02391728a53`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=create+clone+edit+clone+fill`

- **Instruction**：打开 `/home/user/Documents/logo_design.svg`。 (1) 选中外圈圆（id=logo_outer）并创建 2 个克隆（Edit > Clone > Create Clone，执行两次）。(2) 将原始外圈圆填充改为海军蓝（`#1a1a6e`）。(3) 将文档尺寸改为 600×600。保存。
- **Upload Resources**：`logo_design.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_clone_restyle`（复合）
- **result**：`vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**：`rule` → `{"clone_check": {"source_id": "logo_outer", "min_clones": 2}, "fill_check": {"element_id": "logo_outer", "expected_fill": "#1a1a6e"}, "doc_check": {"expected_width": "600", "expected_height": "600"}}`
- **Steps**：3 — 克隆×2 + 原件改色 + 文档尺寸调整

---

#### Task 2-5: 渐变 + 投影
- **Task ID**：`ea372358-579a-4832-a721-9a5af2d054a8`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=linear+gradient+drop+shadow`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。 (1) 给蓝色矩形应用至少 2 个色标的线性渐变。 (2) 对同一矩形应用投影滤镜（Filters > Shadows and Glows > Drop Shadow...）。 (3) 将矩形描边宽度设为 0（或描边设为 none）。保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_gradient_shadow`（复合）
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"gradient_check": {"element_id": "rect1", "gradient_type": "linearGradient", "min_stops": 2}, "filter_check": {"element_id": "rect1", "expected_filter_type": "feDropShadow"}, "stroke_check": {"element_id": "rect1", "expected_stroke": "none"}}`
- **Steps**：3 — 渐变 + 投影 + 去描边

---

#### Task 2-6: 旋转 + 翻转 + 改色
- **Task ID**：`96b14f1d-0aba-4f66-90ae-331fc9d61892`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=rotate+flip+object+fill`

- **Instruction**：打开 `/home/user/Documents/star_polygon.svg`。 (1) 将六边形（id=hexagon1）顺时针旋转 45°。 (2) 将三角形（id=triangle1）执行水平翻转（Object > Flip Horizontal）。 (3) 将星形（id=star1）填充改为金色（`#ffd700`）。保存。
- **Upload Resources**：`star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_multi_transform`（复合）
- **result**：`vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**：`rule` → `{"transform_check_1": {"element_id": "hexagon1", "expected_transform_contains": "rotate"}, "transform_check_2": {"element_id": "triangle1", "expected_transform_contains": "scale(-1"}, "fill_check": {"element_id": "star1", "expected_fill": "#ffd700"}}`
- **Steps**：3 — 旋转 A + 翻转 B + 改色 C

---

#### Task 2-7: 文本样式重设：颜色 + 粗体 + 字体
- **Task ID**：`539ae4e0-0f75-4580-bf82-f45b1d1d69c8`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=text+color+bold+font+family`

- **Instruction**：打开 `/home/user/Documents/text_hello.svg`。 (1) 将标题文本颜色改为红色（`#ff0000`）。 (2) 将标题设为粗体。 (3) 将标题字体家族改为 “DejaVu Serif”。保存。
- **Upload Resources**：`text_hello.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_text_style`
- **result**：`vm_file` → `/home/user/Documents/text_hello.svg`
- **expected**：`rule` → `{"element_id": "text_title", "expected_fill": "#ff0000", "expected_font_weight": "bold", "expected_font_family": "DejaVu Serif"}`
- **Steps**：3 — 改颜色 + 粗体 + 字体家族

---

#### Task 2-8: 图层重排 + 重命名 + 隐藏
- **Task ID**：`f86a64e9-03a3-47b1-9ff5-17373016e26a`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=reorder+rename+hide+layers`

- **Instruction**：打开 `/home/user/Documents/three_layers.svg`。 (1) 将 “Labels” 图层移动到 “Shapes” 图层下方，使自底向上顺序为：Background、Labels、Shapes。 (2) 将 “Shapes” 重命名为 “Main Shapes”。 (3) 隐藏 “Background” 图层。保存。
- **Upload Resources**：`three_layers.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_layer_ops`（复合）
- **result**：`vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**：`rule` → `{"order_check": {"expected_order": ["Background", "Labels", "Main Shapes"]}, "rename_check": {"layer_id": "layer2", "expected_label": "Main Shapes"}, "visibility_check": {"layer_label": "Background", "expected_visible": false}}`
- **Steps**：3 — 图层重排 + 重命名 + 隐藏

---

#### Task 2-9: 编组对象 + 对组变换
- **Task ID**：`d9212d8c-eb7e-44b9-af6b-2f64558d0a91`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=group+objects+transform+group`

- **Instruction**：打开 `/home/user/Documents/star_polygon.svg`。 (1) 选中六边形（id=hexagon1）和三角形（id=triangle1）并编组（Object > Group）。 (2) 将整组顺时针旋转 30°。 (3) 将组内六边形填充改为青绿（`#008080`）。保存。
- **Upload Resources**：`star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_group_transform`（复合）
- **result**：`vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**：`rule` → `{"group_check": {"expected_children_ids": ["hexagon1", "triangle1"], "require_group": true}, "group_has_transform": "rotate", "fill_check": {"element_id": "hexagon1", "expected_fill": "#008080"}}`
- **Steps**：3 — 编组 + 组旋转 + 组内子元素改色

---

#### Task 2-10: 转路径 + 修改描边样式
- **Task ID**：`282a05d4-aa2b-4a06-9883-7f750943cd97`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=object+to+path+dash+stroke`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。 (1) 将蓝色矩形（id=rect1）执行图形转路径（Path > Object to Path）。 (2) 将转换后的路径描边改为虚线。 (3) 描边颜色改为红色（`#ff0000`），宽度设为 4。保存。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_path_stroke`（复合）
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"path_check": {"original_id": "rect1", "expected_tag": "path"}, "dash_check": {"element_id": "rect1", "expect_dash": true}, "stroke_check": {"element_id": "rect1", "expected_stroke": "#ff0000", "expected_stroke_width": "4"}}`
- **Steps**：3 — 转路径 + 设虚线 + 设描边颜色/宽度

---

#### Task 2-11: 全局缩放 + 文档改尺寸 + 加参考线
- **Task ID**：`fd01151d-b729-47eb-a515-88064c768c13`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=scale+document+size+guide`

- **Instruction**：打开 `/home/user/Documents/logo_design.svg`。 (1) 全选（Ctrl+A）并缩放到 200%（两倍）。 (2) 将文档尺寸改为 800×800 像素。 (3) 添加 y=400 的水平参考线（垂直中心）。保存。
- **Upload Resources**：`logo_design.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_scale_guide`（复合）
- **result**：`vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**：`rule` → `{"doc_check": {"expected_width": "800", "expected_height": "800"}, "guide_check": {"guide_orientation": "horizontal", "guide_position": 400, "tolerance": 5}}`
- **Steps**：3 — 全局缩放 + 文档改尺寸 + 加参考线

---

#### Task 2-12: 投影 + 层级顺序 + 复制
- **Task ID**：`2c6b4cd2-f303-4f5e-bf59-997a539eaf95`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=drop+shadow+z+order+duplicate`

- **Instruction**：打开 `/home/user/Documents/zorder_shapes.svg`。 (1) 给小绿色矩形（id=small_rect）添加投影滤镜（Filters > Shadows and Glows > Drop Shadow...）。 (2) 将中间圆（id=medium_circle）下移到底层。 (3) 复制大矩形（id=large_rect），使大矩形至少有 2 个。保存。
- **Upload Resources**：`zorder_shapes.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_shadow_zorder`（复合）
- **result**：`vm_file` → `/home/user/Documents/zorder_shapes.svg`
- **expected**：`rule` → `{"filter_check": {"element_id": "small_rect", "expected_filter_type": "feDropShadow"}, "zorder_check": {"element_id": "medium_circle", "expected_position": "bottom"}, "count_check": {"element_tag": "rect", "min_count": 3}}`
- **Steps**：3 — 元素 A 加滤镜 + 元素 B 调层级 + 元素 C 复制

---

### 3.3 Level 3 — 高级操作（多步工作流，4–8 个动作，跨功能协同）

---

#### Task 3-1: 信息图仪表板品牌改版 + 导出
- **Task ID**：`b7d10a21-5517-43c3-866b-c9a5e9c83651`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=infographic+rebrand+text+color+export+png+workflow`

- **Instruction**：打开 `/home/user/Documents/infographic_report.svg`。完成以下全部修改：
  1) 标题由 “Annual Report 2024” 改为 “Annual Report 2025”；
  2) 副标题由 “Company Performance Overview” 改为 “Growth & Strategy Update”；
  3) 营收值由 “$4.2M” 改为 “$5.1M”；
  4) 增长文本由 “+18% vs last year” 改为 “+21% vs last year”；
  5) 将柱状图 4 根柱（bar_q1~bar_q4）颜色由蓝色（`#3498db`）改为绿色（`#27ae60`）；
  6) 页脚文本由 “Confidential — Internal Use Only” 改为 “Public Release”；
  7) 保存 SVG，并将整页导出为 PNG 到 `/home/user/Documents/report_2025.png`，导出宽度 2400 像素。
- **Upload Resources**：`infographic_report.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_infographic_rebrand`（复合）
- **result**：`vm_file` → `/home/user/Documents/infographic_report.svg`
- **expected**：`rule` → `{"text_checks": [{"element_id": "header_title", "expected_text": "Annual Report 2025"}, {"element_id": "header_subtitle", "expected_text": "Growth & Strategy Update"}, {"element_id": "card_left_value", "expected_text": "$5.1M"}, {"element_id": "card_left_delta", "expected_text": "+21% vs last year"}, {"element_id": "footer_text", "expected_text": "Public Release"}], "fill_checks": [{"element_id": "bar_q1", "expected_fill": "#27ae60"}, {"element_id": "bar_q2", "expected_fill": "#27ae60"}, {"element_id": "bar_q3", "expected_fill": "#27ae60"}, {"element_id": "bar_q4", "expected_fill": "#27ae60"}], "png_export": {"expected_path": "/home/user/Documents/report_2025.png", "expected_width": 2400}}`
- **Difficulty**：跨 2 图层完成 7 项文本/颜色修改 + PNG 导出

---

#### Task 3-2: 由散落部件拼装图标
- **Task ID**：`4147bf1c-e7b9-496f-84a9-9242fe8a2efb`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=icon+composition+align+group+objects+workflow`

- **Instruction**：打开 `/home/user/Documents/icon_parts.svg`。按下列步骤将散落图元组合成居中的应用图标：
  1) 移动 `icon_triangle` 到 `icon_bg` 圆内中心（约 cx=200, cy=200）；
  2) 移动 `icon_ring` 使其与 `icon_bg` 同心（cx=200, cy=200）；
  3) 将 `icon_bg` 填充改为深蓝（`#2c3e50`）；
  4) 将 `icon_triangle` 填充改为白色（`#ffffff`）；
  5) 将 `accent_dot` 移动到 (310,110)（相对圆的右上角）；
  6) 将 `accent_dot` 填充改为橙色（`#f39c12`）；
  7) 选中 `icon_bg`、`icon_triangle`、`icon_ring`、`accent_dot` 并编组；
  8) 将 `icon_label` 文本改为 “PlayApp”；
  9) 保存文件。
- **Upload Resources**：`icon_parts.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_icon_composition`（复合）
- **result**：`vm_file` → `/home/user/Documents/icon_parts.svg`
- **expected**：`rule` → `{"fill_checks": [{"element_id": "icon_bg", "expected_fill": "#2c3e50"}, {"element_id": "icon_triangle", "expected_fill": "#ffffff"}, {"element_id": "accent_dot", "expected_fill": "#f39c12"}], "group_check": {"expected_children_ids": ["icon_bg", "icon_triangle", "icon_ring", "accent_dot"], "require_group": true}, "text_check": {"element_id": "icon_label", "expected_text": "PlayApp"}, "geometry_checks": [{"element_id": "accent_dot", "expected_cx": "310", "expected_cy": "110", "tolerance": 20}]}`
- **Difficulty**：6 次移动/改色 + 编组 + 文本编辑，需空间定位

---

#### Task 3-3: 布尔运算流水线
- **Task ID**：`90716bae-b64b-4b32-8332-c48dcd4f46ca`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=boolean+operations+union+intersection+pipeline`

- **Instruction**：打开 `/home/user/Documents/overlapping_circles.svg`。复制两个圆（共 4 个圆）。对原始两个圆执行并集（Path > Union），对复制得到的两个圆执行交集（Path > Intersection）。最终应只剩 **2 个 path 对象**，且不再有 circle 元素。保存。
- **Upload Resources**：`overlapping_circles.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_boolean_pipeline`
- **result**：`vm_file` → `/home/user/Documents/overlapping_circles.svg`
- **expected**：`{"expected_path_count": 2, "no_circle_elements": true}`
- **Difficulty**：选择顺序敏感，需要精确管理选择集

---

#### Task 3-4: 图层编排工作流（含水印）
- **Task ID**：`152ebab3-5dca-4706-b4c7-e59909c6af9a`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=watermark+layer+workflow+opacity+rename+hide`

- **Instruction**：打开 `/home/user/Documents/three_layers.svg`。完成以下全部操作：
  1) 在最上方新增图层 “Watermark”；
  2) 切换到 “Watermark” 并创建文本 “DRAFT”，字号 72px；
  3) 将 “Watermark” 图层不透明度设为 30%；
  4) 隐藏 “Labels” 图层；
  5) 将 “Shapes” 图层重命名为 “Main Content”；
  6) 将 “Background” 图层背景矩形填充从 `#f0f0f0` 改为浅黄 `#fffde7`；
  7) 保存文件。
- **Upload Resources**：`three_layers.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_layer_workflow`（复合）
- **result**：`vm_file` → `/home/user/Documents/three_layers.svg`
- **expected**：`rule` → `{"new_layer_label": "Watermark", "watermark_text": "DRAFT", "watermark_font_size": "72", "watermark_opacity": "0.3", "labels_hidden": true, "renamed_layer": {"layer_id": "layer2", "expected_label": "Main Content"}, "bg_fill_check": {"element_id": "bg_rect", "expected_fill": "#fffde7"}}`
- **Difficulty**：跨 4 图层 7 个动作（新增、重命名、隐藏、透明度、改色）

---

#### Task 3-5: 复杂路径编辑 + 样式 + 层级顺序
- **Task ID**：`4c2808f3-44c1-4f41-acf1-522ddc591948`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=path+editing+stroke+dash+blur+z+order+workflow`

- **Instruction**：打开 `/home/user/Documents/complex_path.svg`，完成：
  1) 将 `zigzag` 描边改为蓝色（`#0000ff`），宽度 4；
  2) 将 `zigzag` 描边改为虚线；
  3) 对 `blob_shape` 应用高斯模糊；
  4) 删除 `spiral_path`；
  5) 将 `complex_curve` 提升到最上层；
  6) 将 `complex_shape` 填充改为橙色（`#ff8c00`）；
  7) 保存。
- **Upload Resources**：`complex_path.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_complex_path_workflow`（复合）
- **result**：`vm_file` → `/home/user/Documents/complex_path.svg`
- **expected**：`rule` → `{"stroke_check": {"element_id": "zigzag", "expected_stroke": "#0000ff", "expected_stroke_width": "4"}, "dash_check": {"element_id": "zigzag", "expect_dash": true}, "filter_check": {"element_id": "blob_shape", "expected_filter_type": "feGaussianBlur"}, "deleted_id": "spiral_path", "zorder_check": {"element_id": "complex_curve", "expected_position": "top"}, "fill_check": {"element_id": "complex_shape", "expected_fill": "#ff8c00"}}`
- **Difficulty**：7 个动作覆盖描边/虚线/滤镜/删除/层级/填充

---

#### Task 3-6: 完整海报设计工作流 + PDF 导出
- **Task ID**：`8a99d706-7fbc-48be-a26a-f3780c30416b`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=poster+design+workflow+export+pdf`

- **Instruction**：打开 `/home/user/Documents/poster_template.svg`。执行：
  1) 标题 “DESIGN” 改为 “INKSCAPE”；
  2) 副标题 “CONFERENCE 2024” 改为 “WORKSHOP 2025”；
  3) 背景色 `#1a1a2e` 改为海军蓝 `#001f3f`；
  4) 顶部强调条颜色 `#e94560` 改为橙色 `#ff8c00`；
  5) 在 Content 图层新增一个矩形（任意尺寸颜色）；
  6) 文档尺寸设为 595×842（A4）；
  7) 保存 SVG；
  8) 导出 PDF 到 `/home/user/Documents/final_poster.pdf`。
- **Upload Resources**：`poster_template.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_full_poster_workflow`（复合）
- **result**：`vm_file` → `/home/user/Documents/poster_template.svg`
- **expected**：`rule` → `{"text_checks": [{"element_id": "poster_title", "expected_text": "INKSCAPE"}, {"element_id": "poster_subtitle", "expected_text": "WORKSHOP 2025"}], "fill_checks": [{"element_id": "poster_bg", "expected_fill": "#001f3f"}, {"element_id": "poster_topbar", "expected_fill": "#ff8c00"}], "content_layer_has_rect": true, "doc_size": {"expected_width": "595", "expected_height": "842"}, "pdf_export_path": "/home/user/Documents/final_poster.pdf"}`
- **Difficulty**：8 步，涵盖文本/颜色/绘制/尺寸/导出

---

#### Task 3-7: 多图形布尔 + 渐变 + 编组 + 导出
- **Task ID**：`a6251c43-5904-401c-a5c9-57d482142e29`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=boolean+gradient+group+export+png+workflow`

- **Instruction**：打开 `/home/user/Documents/star_polygon.svg`。执行：
  1) 选中 `hexagon1` 与 `triangle1` 执行并集；
  2) 给合并路径应用线性渐变（至少 2 个色标）；
  3) 给 `star1` 应用投影滤镜；
  4) 将 `star1` 顺时针旋转 30°；
  5) 选中合并路径和星形并编组；
  6) 文档改为 600×600；
  7) 保存 SVG；
  8) 导出 PNG 到 `/home/user/Documents/composed_shapes.png`，宽度 1200。
- **Upload Resources**：`star_polygon.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_shape_composition_workflow`（复合）
- **result**：`vm_file` → `/home/user/Documents/star_polygon.svg`
- **expected**：`rule` → `{"boolean_check": {"original_ids": ["hexagon1", "triangle1"], "max_remaining": 1, "require_path": true}, "gradient_on_merged": true, "filter_check": {"element_id": "star1", "expected_filter_type": "feDropShadow"}, "transform_check": {"element_id": "star1", "expected_transform_contains": "rotate"}, "has_group_with_two_children": true, "doc_size": {"expected_width": "600", "expected_height": "600"}, "png_export": {"expected_path": "/home/user/Documents/composed_shapes.png", "expected_width": 1200}}`
- **Difficulty**：8 步，覆盖布尔、渐变、滤镜、变换、编组、导出

---

#### Task 3-8: 仪表板图层手术 + 条件导出
- **Task ID**：`ec3819a6-5a54-4e39-b721-bf0453753a97`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=dashboard+layers+lock+delete+export+workflow`

- **Instruction**：打开 `/home/user/Documents/infographic_report.svg`，执行：
  1) 隐藏 “Footer” 图层；
  2) 锁定 “Header” 图层（不可编辑）；
  3) 在 “Content” 图层删除右侧卡片全部元素（`card_right`、`card_right_title`、`donut_outer`、`donut_inner`、`donut_label`）；
  4) 将中心卡片 `card_center` 调整为 width=720、x=420；
  5) 在中心卡片区域新增文本 “Expanded View”，字号 18px；
  6) 文档宽由 1200 改为 1000（高度保持 800）；
  7) 保存 SVG；
  8) 导出 PNG 到 `/home/user/Documents/dashboard_slim.png`，宽度 2000。
- **Upload Resources**：`infographic_report.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_dashboard_surgery`（复合）
- **result**：`vm_file` → `/home/user/Documents/infographic_report.svg`
- **expected**：`rule` → `{"footer_hidden": true, "header_locked": true, "deleted_ids": ["card_right", "card_right_title", "donut_outer", "donut_inner", "donut_label"], "geometry_check": {"element_id": "card_center", "expected_width": "720", "tolerance": 10}, "new_text_contains": "Expanded View", "doc_size": {"expected_width": "1000", "expected_height": "800"}, "png_export": {"expected_path": "/home/user/Documents/dashboard_slim.png", "expected_width": 2000}}`
- **Difficulty**：8 步，含图层控制、批量删除、几何修改、文本新增与导出

---

#### Task 3-9: 克隆拼贴图案 + 对齐 + 样式
- **Task ID**：`9f5bdba8-6c96-4e9a-9ec4-575ea9656142`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=clone+tiling+pattern+alignment+workflow`

- **Instruction**：打开 `/home/user/Documents/logo_design.svg`，执行：
  1) 全选并编为一个组；
  2) 为该组创建 3 个克隆；
  3) 将原组 + 3 个克隆排成 2×2 网格；
  4) 文档尺寸改为 800×800；
  5) 在最上方新增图层 “Overlay”；
  6) 在 “Overlay” 图层添加覆盖整页的大白色半透明矩形（fill `#ffffff`，opacity 20%）；
  7) 保存 SVG；
  8) 导出 PNG 到 `/home/user/Documents/tiled_logo.png`，宽度 1600。
- **Upload Resources**：`logo_design.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_tiled_pattern_workflow`（复合）
- **result**：`vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**：`rule` → `{"min_use_elements": 3, "doc_size": {"expected_width": "800", "expected_height": "800"}, "overlay_layer": {"label": "Overlay", "has_rect": true, "rect_fill": "#ffffff", "rect_opacity_max": 0.3}, "png_export": {"expected_path": "/home/user/Documents/tiled_logo.png", "expected_width": 1600}}`
- **Difficulty**：8 步，覆盖编组、克隆、排布、图层、透明覆盖、导出

---

#### Task 3-10: 多文本海报编辑 + 渐变重塑 + 新图层 + 双导出
- **Task ID**：`4300db79-4191-4a16-bf6d-c12e6070b3e7`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=poster+text+gradient+layer+export+png+pdf`

- **Instruction**：打开 `/home/user/Documents/poster_template.svg`，执行：
  1) 标题改为 “INNOVATION”；
  2) 副标题改为 “SUMMIT 2026”；
  3) 将纯色背景替换为径向渐变（中心 `#0d0d2b`，边缘 `#1a1a4e`）；
  4) 将顶部强调条 `#e94560` 改为线性渐变（左 `#ff6b6b` → 右 `#ffa502`）；
  5) 在最上方新增图层 “Badge”；
  6) 在 “Badge” 图层绘制一个金色圆（fill `#ffd700`）并添加文本 “NEW”（18px）；
  7) 隐藏 Content 图层（若存在）；
  8) 保存 SVG；
  9) 导出 PNG 到 `/home/user/Documents/innovation_poster.png`，宽度 1190；
  10) 再导出 PDF 到 `/home/user/Documents/innovation_poster.pdf`。
- **Upload Resources**：`poster_template.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_dual_export_poster`（复合）
- **result**：`vm_file` → `/home/user/Documents/poster_template.svg`
- **expected**：`rule` → `{"text_checks": [{"element_id": "poster_title", "expected_text": "INNOVATION"}, {"element_id": "poster_subtitle", "expected_text": "SUMMIT 2026"}], "bg_has_radial_gradient": true, "topbar_has_linear_gradient": true, "badge_layer": {"label": "Badge", "has_circle_with_fill": "#ffd700", "has_text_containing": "NEW"}, "content_hidden_or_absent": true, "png_export": {"expected_path": "/home/user/Documents/innovation_poster.png", "expected_width": 1190}, "pdf_export": {"expected_path": "/home/user/Documents/innovation_poster.pdf", "min_size_bytes": 500}}`
- **Difficulty**：10 步（文本、双渐变、新图层绘制、隐藏图层、双格式导出）

---

### 3.4 Interactive 任务规划（多轮交互草案）

> 本节先给出 Inkscape interactive 任务的规划设计（非最终 JSON）。后续落地时建议命名为 `interactive_inkscape_<scenario>_<nnn>.json`，并放入 `evaluation_examples/examples/interactive/`（或 `interactive_xt/`）统一管理。

#### 3.4.1 构建流程与触发方式（与现有 interactive 样例对齐）

- **任务结构**：顶层设置 `"interactive": true`，用 `phases` 描述多轮用户输入。
- **phase 基本字段**：每轮包含 `phase_id`、`instruction`、`trigger`。
- **用户触发方式映射**（对应你提到的 step / ask / Agent done）：
  - **step** → `{"type": "step_count", "value": N}`（Agent 执行到第 N 步时，用户中途插话）
  - **ask** → `{"type": "agent_asks"}`（Agent 主动提问后，用户补充澄清信息）
  - **Agent done** → `{"type": "agent_done"}`（Agent 表示完成后，用户追加下一轮需求）
- **设计原则**：
  1) 第 1 轮尽量口语化、模糊化，贴近真实甲方表达；
  2) 第 2/3 轮逐步补参数（颜色、尺寸、导出规格）；
  3) 评估尽量对准最终产物（SVG 内容 + 导出文件），减少过程依赖。

#### 3.4.2 候选任务清单（贴近真实创作场景）

| 规划编号 | 建议 Task ID | 场景类型 | 触发链路 | 核心素材 | 真实场景关键词 |
|---|---|---|---|---|---|
| IP-4 | `interactive_inkscape_correction_001` | `correction` | Agent done → Agent done → Agent done | `complex_path.svg` | 用户发现改错对象后纠偏 |
| IP-6 | `interactive_inkscape_workflow_001` | `multi_step_workflow` | Agent done → Agent done → Agent done → Agent done | `three_layers.svg` | 团队交接收尾流程 |

---

#### Interactive Plan IP-1：模糊品牌改版需求（先澄清再执行）
- **建议 Task ID**：`interactive_inkscape_social_cover_ambiguous_001`
- **scenario_type**：`ambiguous_instruction`
- **触发链路**：`ask(agent_asks)` → `Agent done(agent_done)` → `Agent done(agent_done)`
- **素材**：`/home/user/Documents/infographic_report.svg`
- **Phase 1（模糊需求）**：
  - instruction：`帮我把这份年报图改得更有科技感，今天下午就要给老板看。`
  - trigger：`{"type": "agent_asks"}`
- **Phase 2（澄清后执行）**：
  - instruction：`标题改成 Annual Report 2025，副标题改成 Growth & Strategy Update，四根柱子统一换成 #27ae60，页脚改成 Public Release。`
  - trigger：`{"type": "agent_done"}`
- **Phase 3（交付）**：
  - instruction：`导出整页 PNG 到 /home/user/Documents/report_2025.png，宽度 2400。`
  - trigger：`{"type": "agent_done"}`
- **建议评估器组合**：`check_inkscape_infographic_rebrand` + `check_inkscape_export_png`
- **真实创作映射**：典型“甲方口头模糊需求 → 设计师主动澄清 → 一次性交付”流程。

---

#### Interactive Plan IP-2：海报制作中途插单（执行中被打断）
- **建议 Task ID**：`interactive_inkscape_interruption_001`
- **scenario_type**：`interruption`
- **触发链路**：`step(step_count=3)` → `Agent done(agent_done)` → `Agent done(agent_done)`
- **素材**：`/home/user/Documents/poster_template.svg`
- **Phase 1（先做首版）**：
  - instruction：`先把标题改成 INKSCAPE WORKSHOP，副标题改成 2026 SPRING，并把背景改深蓝风格。`
  - trigger：`{"type": "step_count", "value": 3}`
- **Phase 2（中途插单）**：
  - instruction：`先别导出，客户临时改需求：画布改成 1080x1080，右下角加“扫码报名”文案。`
  - trigger：`{"type": "agent_done"}`
- **Phase 3（最终交付）**：
  - instruction：`现在导出 PNG 到 /home/user/Documents/workshop_square.png，宽度 1080。`
  - trigger：`{"type": "agent_done"}`
- **建议评估器组合**：`check_inkscape_document_properties` + `check_inkscape_text_content` + `check_inkscape_export_png`
- **真实创作映射**：制作进行中被运营/客户临时插单是高频真实情境。

---

#### Interactive Plan IP-3：先交初稿，再按反馈渐进细化
- **建议 Task ID**：`interactive_inkscape_progressive_001`
- **scenario_type**：`progressive_refinement`
- **触发链路**：`Agent done(agent_done)` → `Agent done(agent_done)` → `Agent done(agent_done)`
- **素材**：`/home/user/Documents/icon_parts.svg`
- **Phase 1（初稿）**：
  - instruction：`先把这些散落图元拼成一个居中图标，文字先保留默认。`
  - trigger：`{"type": "agent_done"}`
- **Phase 2（反馈 1）**：
  - instruction：`图标底色改成 #2c3e50，三角形改白色，点缀圆改 #f39c12。`
  - trigger：`{"type": "agent_done"}`
- **Phase 3（反馈 2 + 交付）**：
  - instruction：`把文字改成 PlayApp，并导出 /home/user/Documents/playapp_icon.png（宽度 1024）。`
  - trigger：`{"type": "agent_done"}`
- **建议评估器组合**：`check_inkscape_icon_composition` + `check_inkscape_export_png`
- **真实创作映射**：先看结构稿，再逐轮细化颜色与文案，是设计评审常见节奏。

---

#### Interactive Plan IP-4：用户纠错（改错对象后返工）
- **建议 Task ID**：`interactive_inkscape_correction_001`
- **scenario_type**：`correction`
- **触发链路**：`Agent done(agent_done)` → `Agent done(agent_done)` → `Agent done(agent_done)`
- **素材**：`/home/user/Documents/complex_path.svg`
- **Phase 1（首次要求）**：
  - instruction：`把 zigzag 改成蓝色虚线，线宽 4。`
  - trigger：`{"type": "agent_done"}`
- **Phase 2（用户纠错）**：
  - instruction：`我说错了，不是改 zigzag；请把 blob_shape 填充改成 #ff8c00，并删除 spiral_path。`
  - trigger：`{"type": "agent_done"}`
- **Phase 3（收口）**：
  - instruction：`再把 complex_curve 提到最上层，然后保存。`
  - trigger：`{"type": "agent_done"}`
- **建议评估器组合**：`check_inkscape_complex_path_workflow`
- **真实创作映射**：需求方“说错对象再纠正”是非常常见的人机协作噪声。

---

#### Interactive Plan IP-5：需求变更（内部稿改公开稿）
- **建议 Task ID**：`interactive_inkscape_requirement_change_001`
- **scenario_type**：`requirement_change`
- **触发链路**：`Agent done(agent_done)` → `Agent done(agent_done)` → `Agent done(agent_done)`
- **素材**：`/home/user/Documents/infographic_report.svg`
- **Phase 1（内部稿）**：
  - instruction：`先按内部评审稿处理，保留页脚“Confidential — Internal Use Only”。`
  - trigger：`{"type": "agent_done"}`
- **Phase 2（临时改口）**：
  - instruction：`现在改成对外公开版：页脚改 Public Release，并删除右侧客户数环图那一组元素。`
  - trigger：`{"type": "agent_done"}`
- **Phase 3（导出）**：
  - instruction：`导出 PNG 到 /home/user/Documents/report_public.png，宽度 2000。`
  - trigger：`{"type": "agent_done"}`
- **建议评估器组合**：`check_inkscape_dashboard_surgery` + `check_inkscape_export_png`
- **真实创作映射**：同一份视觉物料在“内外版本”切换非常常见。

---

#### Interactive Plan IP-6：团队交接收尾（分阶段验收）
- **建议 Task ID**：`interactive_inkscape_workflow_001`
- **scenario_type**：`multi_step_workflow`
- **触发链路**：`Agent done(agent_done)` → `Agent done(agent_done)` → `Agent done(agent_done)` → `Agent done(agent_done)`
- **素材**：`/home/user/Documents/three_layers.svg`
- **Phase 1（结构整理）**：
  - instruction：`把图层顺序整理成 Background、Labels、Shapes。`
  - trigger：`{"type": "agent_done"}`
- **Phase 2（命名规范）**：
  - instruction：`把 Shapes 重命名成 Main Content。`
  - trigger：`{"type": "agent_done"}`
- **Phase 3（可见性规范）**：
  - instruction：`隐藏 Labels 图层，并把 Background 填充改成 #fffde7。`
  - trigger：`{"type": "agent_done"}`
- **Phase 4（交付）**：
  - instruction：`保存后导出 /home/user/Documents/layer_handoff.png（宽度 1600）。`
  - trigger：`{"type": "agent_done"}`
- **建议评估器组合**：`check_inkscape_l2_layer_ops` + `check_inkscape_fill_color` + `check_inkscape_export_png`
- **真实创作映射**：设计团队交接时常按“结构→命名→可见性→导出”逐步验收。

---

## 4. 新评估器函数规范

> 以下函数签名与代码块保持与原文一致，仅补充中文说明。

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

### 4.33 复合评估器（Level 2）

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

### 4.34 复合评估器（Level 3）

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

## 5. 任务汇总

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

## 6. 评估器注册

实现评估器后，在 `desktop_env/evaluators/__init__.py` 中注册（代码与原文一致）：

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

然后在同文件 `eval_funcs` 字典中加入对应映射。

---

## 7. 实现说明

1. **SVG 是 XML**：使用带命名空间注册的 `xml.etree.ElementTree`：
   ```python
   ET.register_namespace('', 'http://www.w3.org/2000/svg')
   ET.register_namespace('inkscape', 'http://www.inkscape.org/namespaces/inkscape')
   ET.register_namespace('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd')
   ```

2. **style 解析**：Inkscape 常将样式存于 `style` 字段（CSS 键值）；可用辅助函数解析：
   ```python
   def parse_style(style_str):
       return dict(item.split(':') for item in style_str.split(';') if ':' in item)
   ```

3. **颜色归一化**：颜色可能是 `#ff0000`、`#FF0000`、`#f00`、`rgb(255,0,0)` 或命名色（如 `red`）。比较前先展开短十六进制并转小写。

4. **几何容差**：比较位置/尺寸时应使用数值容差，Inkscape 常会引入小数精度。

5. **启动路径**：始终使用 `/usr/bin/inkscape`，不要用裸 `inkscape`。

6. **配置顺序**：`upload_file` → `launch`（/usr/bin/inkscape）→ `sleep`（3–5 秒）→（Agent 执行任务）→ 评估。

7. **导出校验**：PNG 使用 Python PIL 检查尺寸；PDF 用 `os.path.getsize` 校验，二者通过 `vm_command_line`。

8. **SVG 层级（Z-order）**：文档中**后出现**的元素渲染在**上层**。“Raise to Top” 即移动为父节点的**最后一个**子元素。

9. **图层本质**：Inkscape 图层是 `<g inkscape:groupmode="layer">`。在 SVG 文档顺序中，**最后一个 `<g>` 图层**是视觉上最上层。

---

## 8. 与 Kdenlive 任务对比

| 维度 | Kdenlive | Inkscape |
|--------|----------|----------|
| 文件格式 | MLT XML（.kdenlive） | SVG XML（.svg） |
| 解析方式 | `xml.etree.ElementTree` | `xml.etree.ElementTree` |
| 启动二进制 | `/usr/bin/kdenlive` | `/usr/bin/inkscape` |
| L1 重点 | 片段导入/组织、轨道管理 | 图形属性、文本、图层、层级、绘图工具 |
| L2 重点 | 特效、转场、修剪 | 布尔运算、滤镜、渐变、变换 |
| L3 重点 | 多片段编辑 + 渲染 | 多步骤编辑 + 导出（PNG/PDF） |
| 导出校验 | ffprobe（视频编码/时长） | PIL（PNG 尺寸）/ 文件大小（PDF） |
| 命名空间复杂度 | MLT namespace | SVG + Inkscape + Sodipodi 命名空间 |

... EOF ...
