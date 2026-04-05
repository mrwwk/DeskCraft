# Inkscape 任务设计文档（中文）移除任务备份

- **来源文件**：`evaluation_examples/examples/inkscape/inkscape_task_design_zh.md`
- **备份日期**：`2026-04-03`
- **说明**：本备份收录从主文档中移除的 15 个任务定义。筛选原则是优先移除重复度较高、测试能力可由其他保留任务覆盖的条目，同时保持 Level 1 / Level 2 / Level 3 的难度分布基本均衡。

## Level 1 移除任务（9 个）

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

#### Task 1-30: 图形转路径
- **Task ID**：`f6e9fe88-4e34-4005-9c79-646f8785a83f`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=object+to+path`

- **Instruction**：打开 `/home/user/Documents/simple_rect_circle.svg`。选中蓝色矩形（id=rect1），执行图形转路径（Path > Object to Path）。转换后该元素应为 `<path>`。保存文件。
- **Upload Resources**：`simple_rect_circle.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_object_to_path`
- **result**：`vm_file` → `/home/user/Documents/simple_rect_circle.svg`
- **expected**：`rule` → `{"original_id": "rect1", "expected_tag": "path"}`
- **Atomic feature**：Path > Object to Path（Shift+Ctrl+C）

## Level 2 移除任务（4 个）

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

#### Task 2-11: 全局缩放 + 文档改尺寸 + 加参考线
- **Task ID**：`fd01151d-b729-47eb-a515-88064c768c13`
- **来源**：Inkscape Manual 任务对应检索页：`https://inkscape-manuals.readthedocs.io/en/latest/search.html?q=scale+document+size+guide`

- **Instruction**：打开 `/home/user/Documents/logo_design.svg`。 (1) 全选（Ctrl+A）并缩放到 200%（两倍）。 (2) 将文档尺寸改为 800×800 像素。 (3) 添加 y=400 的水平参考线（垂直中心）。保存。
- **Upload Resources**：`logo_design.svg` → `/home/user/Documents/`
- **Evaluator**：`check_inkscape_l2_scale_guide`（复合）
- **result**：`vm_file` → `/home/user/Documents/logo_design.svg`
- **expected**：`rule` → `{"doc_check": {"expected_width": "800", "expected_height": "800"}, "guide_check": {"guide_orientation": "horizontal", "guide_position": 400, "tolerance": 5}}`
- **Steps**：3 — 全局缩放 + 文档改尺寸 + 加参考线

## Level 3 移除任务（2 个）

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
