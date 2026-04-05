# LibreOffice Impress Task Design Document

## 0. Verification Strategy

### Core Approach

LibreOffice Impress verification downloads the user-edited `.pptx` file from the VM and performs structured comparison against a pre-built gold standard file.

1. **Presentation Structure Comparison** (`compare_pptx_files`): Uses `python-pptx` to parse `.pptx` files, supporting multi-dimensional comparison -- slide count, shape geometry, text content, indentation, fonts, colors, bullets, backgrounds, speaker notes, etc.
2. **Transition Check** (`check_transition`): Verifies whether a specified slide has the expected transition effect.
3. **Orientation Check** (`check_slide_orientation_Portrait`): Verifies whether slides use portrait layout.

**Evaluator Architecture**: Downloads edited file via `vm_file` getter; some tasks compare against gold files, others verify specific attributes (rule-based).

### Evaluator Pattern

```python
def compare_pptx_files(file1_path, file2_path, **options):
    """
    Args:
        file1_path: Path to .pptx file from VM
        file2_path: Path to gold standard .pptx file
        options: examine_shape, examine_text, examine_font boolean controls
    Returns:
        1.0 (match) or 0.0 (mismatch)
    """
```

---

## 1. Available Resources

Total: **10** initial files + corresponding gold standard files

### impress_v3 Materials (30 tasks)

| # | Initial File | Gold File | Task Summary |
|---|-------------|-----------|-------------|
| 1 | `Bitcoin_ The Digital Revolution.pptx` | `Bitcoin_L1.pptx` | Open "Bitcoin_ The Digital Revolution.pptx". On slide 1, change the co... |
| 2 | `Game Theory.pptx` | `GameTheory_L3.pptx` | Open "Game Theory.pptx" and perform all of the following: (1) On slide... |
| 3 | `The Evolution of Rock Music.pptx` | `RockMusic_L3.pptx` | Open "The Evolution of Rock Music.pptx" and perform: (1) Slide 1: back... |
| 4 | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `Ecosystem_L3.pptx` | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural For... |
| 5 | `The Golden Age of Arcade Games.pptx` | `ArcadeGames_L1.pptx` | Open "The Golden Age of Arcade Games.pptx". On slide 1, make all text ... |
| 6 | `The Evolution of Rock Music.pptx` | `RockMusic_L1.pptx` | Open "The Evolution of Rock Music.pptx". Change the title font size on... |
| 7 | `black_concise_work_report_template_english.pptx` | `BlackWorkReport_L3.pptx` | Open "black_concise_work_report_template_english.pptx" and apply: (1) ... |
| 8 | `The Golden Age of Arcade Games.pptx` | `ArcadeGames_L2.pptx` | In "The Golden Age of Arcade Games.pptx": (1) Set ALL slides backgroun... |
| 9 | `work_summary_template_english.pptx` | `WorkSummary_L3.pptx` | Open "work_summary_template_english.pptx" and apply all changes: (1) S... |
| 10 | `Game Theory.pptx` | `GameTheory_L2.pptx` | In "Game Theory.pptx": (1) On slide 4, change all body text to italic ... |
| 11 | `The Birthday Paradox.pptx` | `BirthdayParadox_L2.pptx` | In "The Birthday Paradox.pptx": (1) On slide 1, change all text to "Ti... |
| 12 | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `` | In "Tencent Holdings Limited - 2025 Interim Report.pptx", change the s... |
| 13 | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `Ecosystem_L1.pptx` | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural For... |
| 14 | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `VanGogh_L1.pptx` | Open "Vincent van Gogh_ A Life of Passion and Color.pptx". Make all ti... |
| 15 | `Game Theory.pptx` | `GameTheory_L1.pptx` | Open "Game Theory.pptx". On slide 1, set the background to dark blue (... |
| 16 | `Bitcoin_ The Digital Revolution.pptx` | `Bitcoin_L2.pptx` | In "Bitcoin_ The Digital Revolution.pptx": (1) On slide 1, set the bac... |
| 17 | `work_summary_template_english.pptx` | `WorkSummary_L1.pptx` | Open "work_summary_template_english.pptx". On slide 1, make the title ... |
| 18 | `Bitcoin_ The Digital Revolution.pptx` | `Bitcoin_L3.pptx` | Open "Bitcoin_ The Digital Revolution.pptx" and perform the following ... |
| 19 | `black_concise_work_report_template_english.pptx` | `BlackWorkReport_L1.pptx` | Open "black_concise_work_report_template_english.pptx". On slide 1, ch... |
| 20 | `The Birthday Paradox.pptx` | `` | In "The Birthday Paradox.pptx", add a "Fade" slide transition effect t... |
| 21 | `The Birthday Paradox.pptx` | `BirthdayParadox_L3.pptx` | Open "The Birthday Paradox.pptx" and perform all changes: (1) On slide... |
| 22 | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `Tencent_L3.pptx` | Open the Tencent 2025 Interim Report and perform these changes: (1) On... |
| 23 | `work_summary_template_english.pptx` | `WorkSummary_L2.pptx` | In "work_summary_template_english.pptx": (1) On slide 2, center-align ... |
| 24 | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `Ecosystem_L2.pptx` | In the Ecosystem Biodiversity presentation: (1) On slide 3, make the t... |
| 25 | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `Tencent_L2.pptx` | In "Tencent Holdings Limited - 2025 Interim Report.pptx": (1) On slide... |
| 26 | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `VanGogh_L2.pptx` | In the Van Gogh presentation: (1) Slide 5: body text dark red (#8B0000... |
| 27 | `The Evolution of Rock Music.pptx` | `RockMusic_L2.pptx` | In "The Evolution of Rock Music.pptx": (1) Right-align the title on AL... |
| 28 | `black_concise_work_report_template_english.pptx` | `BlackWorkReport_L2.pptx` | In "black_concise_work_report_template_english.pptx": (1) On ALL slide... |
| 29 | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `VanGogh_L3.pptx` | Open the Van Gogh presentation and do all of the following: (1) Slide ... |
| 30 | `The Golden Age of Arcade Games.pptx` | `ArcadeGames_L3.pptx` | Open "The Golden Age of Arcade Games.pptx" and apply: (1) ALL slides: ... |

---

## 2. Evaluation Function Design

File: `desktop_env/evaluators/metrics/slides.py`

### 2.1 Main Evaluation Functions

| Function | Description | Usage Count |
|----------|-------------|-------------|
| `compare_pptx_files` | Structured comparison of two .pptx files (slide content/shapes/text/formatting) | 28 |
| `check_transition` | Verify slide transition animation type | 1 |
| `check_slide_orientation_Portrait` | Verify slide orientation is portrait | 1 |

---

## 3. Task Definitions


### 3.1 Level 1 (L1) -- Basic Operations -- 1 tasks

> Tasks completed by agent within 10 steps with score 1.0

#### Task L1-1: The Birthday Paradox

- **ID**: `bd3f03cd-3ca8-4c8a-85d7-deb04c98a0d8`
- **Source**: `impress_v3`
- **Instruction**: In "The Birthday Paradox.pptx", add a "Fade" slide transition effect to slide 1.
- **Material File**: `The Birthday Paradox.pptx`
- **Evaluation Function**: `check_transition`
- **Gold File**: ``

#### L1 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L1-1 | Official Help | [Slide Transitions](https://help.libreoffice.org/latest/en-US/text/simpress/guide/animated_slidechange.html) | In "The Birthday Paradox.pptx", add a "Fade" slide transition effect to slide 1. |

#### L1 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | The Birthday Paradox | `The Birthday Paradox.pptx` | `check_transition`  |


### 3.2 Level 2 (L2) -- Compound Operations -- 1 tasks

> Tasks completed within 25 steps (score 1.0) or failed within 10 steps

#### Task L2-1: Tencent Holdings Limited - 2025 Interim Report

- **ID**: `5361ce1b-58bf-4218-a03f-00497a3ce6f8`
- **Source**: `impress_v3`
- **Instruction**: In "Tencent Holdings Limited - 2025 Interim Report.pptx", change the slide orientation to portrait (vertical).
- **Material File**: `Tencent Holdings Limited - 2025 Interim Report.pptx`
- **Evaluation Function**: `check_slide_orientation_Portrait`
- **Gold File**: ``

#### L2 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L2-1 | Official Help | [Slide Orientation](https://help.libreoffice.org/latest/en-US/text/simpress/guide/change_scale.html) | In "Tencent Holdings Limited - 2025 Interim Report.pptx", change the slide orien |

#### L2 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | Tencent Holdings Limited - 2025 Interim Report | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `check_slide_orientation_Portrait`  |


### 3.3 Level 3 (L3) -- Advanced Workflows -- 28 tasks

> Tasks agent cannot complete or requiring >25 steps

#### Task L3-1: Bitcoin_ The Digital Revolution

- **ID**: `03e0e85a-bfbf-4155-b706-dc5bd60fb8a0`
- **Source**: `impress_v3`
- **Instruction**: Open "Bitcoin_ The Digital Revolution.pptx". On slide 1, change the color of all text to orange (#FF7F00) and make all text bold.
- **Material File**: `Bitcoin_ The Digital Revolution.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Bitcoin_L1.pptx`

#### Task L3-2: Game Theory

- **ID**: `06706431-3011-417a-bd22-36869b25d1fe`
- **Source**: `impress_v3`
- **Instruction**: Open "Game Theory.pptx" and perform all of the following: (1) On slide 1, set background to dark blue (#00008B) and make all text white and bold. (2) On ALL slides, set title font size to 36pt. (3) On slide 4, make body text italic and dark blue (#00008B). (4) On slide 5, add this note: "Key concept: Nash Equilibrium occurs when no player can improve their payoff by unilaterally changing their strategy, given other players' strategies remain fixed." (5) On slide 6, set background to light gray (#D3D3D3). (6) On slide 9, change the table second row to: "Firm A: Lower Prices", "(4, 4)", "(9, 2)". (7) Delete the last 2 slides. Save.
- **Material File**: `Game Theory.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `GameTheory_L3.pptx`

#### Task L3-3: The Evolution of Rock Music

- **ID**: `0c7343ab-f0d9-4529-9097-5c101ac8bc74`
- **Source**: `impress_v3`
- **Instruction**: Open "The Evolution of Rock Music.pptx" and perform: (1) Slide 1: background black (#000000), all text red (#FF0000), bold, 44pt. (2) ALL slides: titles 36pt and bold. (3) ALL slides: right-align titles. (4) Slide 3: body text italic and dark gray (#404040). (5) Slide 4: add note: "Legacy: Rock music's influence extends beyond sound — it shaped fashion, politics, and social movements across multiple generations." (6) Slide 6: background dark gray (#404040), all text white. (7) Delete the last 4 slides. Save.
- **Material File**: `The Evolution of Rock Music.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `RockMusic_L3.pptx`

#### Task L3-4: Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests

- **ID**: `12776aaa-e48d-4423-856c-fd59e9f72887`
- **Source**: `impress_v3`
- **Instruction**: Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx" and perform these changes: (1) On ALL slides, make title text bold and set to 32pt. (2) On slide 1, set the background to dark green (#006400) and all text to white (#FFFFFF). (3) On slide 2, make body text italic and forest green (#228B22). (4) On slide 3, center-align the title and add this note: "Conclusion: Preserving forest ecosystems requires integrated approaches combining conservation biology, sustainable forestry, and climate change mitigation strategies." (5) On slide 5, set background to light gray (#D3D3D3). (6) On slide 6, make all body text bold and underlined. Save.
- **Material File**: `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Ecosystem_L3.pptx`

#### Task L3-5: The Golden Age of Arcade Games

- **ID**: `12fd9a81-7fdf-4f21-b6ce-7388cd2f840c`
- **Source**: `impress_v3`
- **Instruction**: Open "The Golden Age of Arcade Games.pptx". On slide 1, make all text bold, underlined, and yellow (#FFFF00).
- **Material File**: `The Golden Age of Arcade Games.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `ArcadeGames_L1.pptx`

#### Task L3-6: The Evolution of Rock Music

- **ID**: `16008ca9-7091-48b2-a22a-7a1ca1509109`
- **Source**: `impress_v3`
- **Instruction**: Open "The Evolution of Rock Music.pptx". Change the title font size on ALL slides to 36pt.
- **Material File**: `The Evolution of Rock Music.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `RockMusic_L1.pptx`

#### Task L3-7: black_concise_work_report_template_english

- **ID**: `16847518-ad96-4cdc-a639-c101bbeb6a23`
- **Source**: `impress_v3`
- **Instruction**: Open "black_concise_work_report_template_english.pptx" and apply: (1) Slide 1: Times New Roman, bold, 36pt. Background navy (#003366), text white. (2) ALL slides: titles 32pt and bold. (3) Slide 2: background dark gray (#404040). (4) Slide 3: body text italic and light gray (#D3D3D3). (5) Slide 4: add note: "Action items: Review budget allocation for Q3, prepare department performance metrics, schedule follow-up meeting with stakeholders." (6) Slide 5: center-align the title. (7) Slide 6: body text bold and underlined. Save.
- **Material File**: `black_concise_work_report_template_english.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `BlackWorkReport_L3.pptx`

#### Task L3-8: The Golden Age of Arcade Games

- **ID**: `209c3917-259e-4329-9f94-bb7a849e679c`
- **Source**: `impress_v3`
- **Instruction**: In "The Golden Age of Arcade Games.pptx": (1) Set ALL slides background to black (#000000). (2) On slide 1, make all text bold, underlined, and yellow (#FFFF00).
- **Material File**: `The Golden Age of Arcade Games.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `ArcadeGames_L2.pptx`

#### Task L3-9: work_summary_template_english

- **ID**: `2593a83c-f6b7-484e-91ad-3b0743c3058e`
- **Source**: `impress_v3`
- **Instruction**: Open "work_summary_template_english.pptx" and apply all changes: (1) Slide 1: title bold, 48pt, underlined. Background navy (#003366), text white. (2) ALL slides: background navy (#003366). (3) Slide 2: body text center-aligned and italic. (4) ALL slides: titles bold and white (#FFFFFF). (5) Slide 4: body text bold, underlined, yellow (#FFFF00). (6) Slide 5: add note: "Next steps: Finalize annual targets, distribute responsibility matrix to team leads, and set up monthly progress review cadence." (7) Slide 7: body text italic and teal (#008080). Save.
- **Material File**: `work_summary_template_english.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `WorkSummary_L3.pptx`

#### Task L3-10: Game Theory

- **ID**: `3be4747b-a8aa-4b79-8f0c-0c7326a3d169`
- **Source**: `impress_v3`
- **Instruction**: In "Game Theory.pptx": (1) On slide 4, change all body text to italic and dark blue (#00008B). (2) On slide 9, find the Pricing Game table and change the second row to: "Firm A: Lower Prices", "(4, 4)", "(9, 2)".
- **Material File**: `Game Theory.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `GameTheory_L2.pptx`

#### Task L3-11: The Birthday Paradox

- **ID**: `456c4488-c4c4-475f-b671-0556dac8696a`
- **Source**: `impress_v3`
- **Instruction**: In "The Birthday Paradox.pptx": (1) On slide 1, change all text to "Times New Roman" and italic. (2) On slide 4, make the title purple (#800080), bold, and underlined.
- **Material File**: `The Birthday Paradox.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `BirthdayParadox_L2.pptx`

#### Task L3-12: Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests

- **ID**: `59d057dc-fc2c-48b2-b7f2-b7c146be1496`
- **Source**: `impress_v3`
- **Instruction**: Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx". On slide 1, change the title font to "Georgia" and set the font size to 40pt.
- **Material File**: `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Ecosystem_L1.pptx`

#### Task L3-13: Vincent van Gogh_ A Life of Passion and Color

- **ID**: `74393e18-c452-44bb-a7df-08c2b73718cd`
- **Source**: `impress_v3`
- **Instruction**: Open "Vincent van Gogh_ A Life of Passion and Color.pptx". Make all title text bold AND italic across ALL slides.
- **Material File**: `Vincent van Gogh_ A Life of Passion and Color.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `VanGogh_L1.pptx`

#### Task L3-14: Game Theory

- **ID**: `8a9fd669-2142-46d4-bd0c-32cd6323b57f`
- **Source**: `impress_v3`
- **Instruction**: Open "Game Theory.pptx". On slide 1, set the background to dark blue (#00008B) and change all text to white (#FFFFFF).
- **Material File**: `Game Theory.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `GameTheory_L1.pptx`

#### Task L3-15: Bitcoin_ The Digital Revolution

- **ID**: `929e152a-b43a-4ad0-a9e5-b01f1a20b910`
- **Source**: `impress_v3`
- **Instruction**: In "Bitcoin_ The Digital Revolution.pptx": (1) On slide 1, set the background color to dark blue (#00008B) and change all text to white (#FFFFFF). (2) On slide 4 (THE BIRTH OF BITCOIN), add this speaker note: "Key talking point: The Genesis Block was mined on January 3rd, 2009, embedding a headline about bank bailouts as a political statement by Satoshi Nakamoto."
- **Material File**: `Bitcoin_ The Digital Revolution.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Bitcoin_L2.pptx`

#### Task L3-16: work_summary_template_english

- **ID**: `9f172a30-0f37-4155-87b3-2ab704912166`
- **Source**: `impress_v3`
- **Instruction**: Open "work_summary_template_english.pptx". On slide 1, make the title bold, 48pt, and underlined.
- **Material File**: `work_summary_template_english.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `WorkSummary_L1.pptx`

#### Task L3-17: Bitcoin_ The Digital Revolution

- **ID**: `9fadf13a-c7f5-483c-a6e4-84dbe342ec6f`
- **Source**: `impress_v3`
- **Instruction**: Open "Bitcoin_ The Digital Revolution.pptx" and perform the following changes: (1) On slide 1, set the background to navy blue (#003366) and make all text white (#FFFFFF), bold, and 36pt. (2) On slide 2, make the title text orange (#FF7F00) and bold. (3) On slide 3, make all body/content text (not the title) italic and dark blue (#00008B). (4) On slide 5, set the background color to light gray (#D3D3D3). (5) On slide 6, add this speaker note: "Summary: Bitcoin has fundamentally changed how we think about money, trust, and decentralized systems." (6) Delete the last 3 slides from the presentation. Save the file.
- **Material File**: `Bitcoin_ The Digital Revolution.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Bitcoin_L3.pptx`

#### Task L3-18: black_concise_work_report_template_english

- **ID**: `ac961eb2-aaee-41c1-941a-0277373c7831`
- **Source**: `impress_v3`
- **Instruction**: Open "black_concise_work_report_template_english.pptx". On slide 1, change all text to "Times New Roman" font.
- **Material File**: `black_concise_work_report_template_english.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `BlackWorkReport_L1.pptx`

#### Task L3-19: The Birthday Paradox

- **ID**: `bde97a2f-56de-4c6c-acd6-3aec3d25caff`
- **Source**: `impress_v3`
- **Instruction**: Open "The Birthday Paradox.pptx" and perform all changes: (1) On slide 1, set all text to Times New Roman, italic, bold. Set background to purple (#800080) and text color to white. (2) On slide 4, make title purple (#800080), bold, underlined. (3) On slide 5, make body text dark blue (#00008B) and italic. (4) On slide 6, add note: "The birthday paradox illustrates how human intuition about probability often fails when dealing with combinatorial problems." (5) On slide 7, set background to light gray (#D3D3D3). (6) On slide 8, make title bold, 36pt, maroon (#800000). Save.
- **Material File**: `The Birthday Paradox.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `BirthdayParadox_L3.pptx`

#### Task L3-20: Tencent Holdings Limited - 2025 Interim Report

- **ID**: `c425a255-7bcd-4840-a1c7-042ca352d969`
- **Source**: `impress_v3`
- **Instruction**: Open the Tencent 2025 Interim Report and perform these changes: (1) On slide 1, set background to navy (#003366), all text white, bold, 40pt. (2) On ALL slides, make titles bold and 32pt. (3) On slide 3, make body text italic. (4) On slide 4, add this note: "Board recommendation: Approve the proposed final dividend of HK$4.40 per share for the fiscal year ending June 2025." (5) On slide 6, set background to light gray (#D3D3D3) and all text to dark blue (#00008B). Save.
- **Material File**: `Tencent Holdings Limited - 2025 Interim Report.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Tencent_L3.pptx`

#### Task L3-21: work_summary_template_english

- **ID**: `c9f5b0bf-a7b9-401a-b713-304b06ab75de`
- **Source**: `impress_v3`
- **Instruction**: In "work_summary_template_english.pptx": (1) On slide 2, center-align body text and make it italic. (2) Set ALL slides background to navy blue (#003366).
- **Material File**: `work_summary_template_english.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `WorkSummary_L2.pptx`

#### Task L3-22: Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests

- **ID**: `d1a5c9cc-e8d7-45a4-9539-6d9946d645f6`
- **Source**: `impress_v3`
- **Instruction**: In the Ecosystem Biodiversity presentation: (1) On slide 3, make the title bold and dark green (#006400), and add this note: "Forests cover approximately 31% of the Earth's land surface and host over 80% of terrestrial biodiversity." (2) Set the background of ALL slides to light gray (#D3D3D3).
- **Material File**: `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Ecosystem_L2.pptx`

#### Task L3-23: Tencent Holdings Limited - 2025 Interim Report

- **ID**: `d6ba6b61-5ce3-46c0-90c0-f635d3a1a8eb`
- **Source**: `impress_v3`
- **Instruction**: In "Tencent Holdings Limited - 2025 Interim Report.pptx": (1) On slide 1, make all text bold, 44pt, and dark blue (#00008B). (2) On slide 3, add this note: "Emphasis: 15% revenue growth demonstrates continued monetization strength. WeChat MAU milestone of 1.41 billion users."
- **Material File**: `Tencent Holdings Limited - 2025 Interim Report.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `Tencent_L2.pptx`

#### Task L3-24: Vincent van Gogh_ A Life of Passion and Color

- **ID**: `d9a2dcc0-9880-4df2-9ee3-b5294f099cb8`
- **Source**: `impress_v3`
- **Instruction**: In the Van Gogh presentation: (1) Slide 5: body text dark red (#8B0000) and italic. (2) Slide 4: title bold and underlined. (3) Slide 4: add note: "Van Gogh began his artistic career at 27 and produced over 860 oil paintings in just 10 years."
- **Material File**: `Vincent van Gogh_ A Life of Passion and Color.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `VanGogh_L2.pptx`

#### Task L3-25: The Evolution of Rock Music

- **ID**: `dc7809c8-2255-4684-9ac8-d4ebcfcd35be`
- **Source**: `impress_v3`
- **Instruction**: In "The Evolution of Rock Music.pptx": (1) Right-align the title on ALL slides. (2) On slide 2, add this note: "This presentation covers five major eras of rock: 1950s origins, British Invasion, psychedelic era, heavy metal and punk, and the 90s alternative revolution."
- **Material File**: `The Evolution of Rock Music.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `RockMusic_L2.pptx`

#### Task L3-26: black_concise_work_report_template_english

- **ID**: `dde1349a-4c95-49ee-a1a5-87b1c3529864`
- **Source**: `impress_v3`
- **Instruction**: In "black_concise_work_report_template_english.pptx": (1) On ALL slides, set titles to 32pt and bold. (2) On slide 2, set background to dark gray (#404040).
- **Material File**: `black_concise_work_report_template_english.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `BlackWorkReport_L2.pptx`

#### Task L3-27: Vincent van Gogh_ A Life of Passion and Color

- **ID**: `eafdd9ea-74a1-47cb-af7d-e8b8a2463111`
- **Source**: `impress_v3`
- **Instruction**: Open the Van Gogh presentation and do all of the following: (1) Slide 1: background dark blue (#00008B), all text yellow (#FFFF00), bold, 36pt. (2) ALL slides: titles bold and italic. (3) Slide 5: body text dark red (#8B0000) and italic. (4) Slide 4: title underlined (in addition to bold+italic from step 2). (5) Slide 6: add note: "Art historians consider Starry Night, painted during Van Gogh's time at Saint-Remy asylum in June 1889, as one of the most recognized paintings in Western culture." (6) Slide 8: background light gray (#D3D3D3). (7) Slide 9: body text bold and purple (#800080). Save.
- **Material File**: `Vincent van Gogh_ A Life of Passion and Color.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `VanGogh_L3.pptx`

#### Task L3-28: The Golden Age of Arcade Games

- **ID**: `ff469fdc-409b-4ed4-a544-46cb1dfb24c2`
- **Source**: `impress_v3`
- **Instruction**: Open "The Golden Age of Arcade Games.pptx" and apply: (1) ALL slides: background black (#000000). (2) Slide 1: all text bold, underlined, yellow (#FFFF00), 40pt. (3) ALL slides: title text yellow and bold. (4) Slide 3: body text white (#FFFFFF) and italic. (5) Slide 4: add note: "The arcade industry generated over $8 billion in quarters alone during its peak year of 1982, equivalent to roughly $25 billion in today's currency." (6) Slide 6: body text teal (#008080) and bold. (7) Slide 10: background dark gray (#404040) instead of black. Save.
- **Material File**: `The Golden Age of Arcade Games.pptx`
- **Evaluation Function**: `compare_pptx_files`
- **Gold File**: `ArcadeGames_L3.pptx`

#### L3 Task Source Annotations

| Task | Source Type | Specific Source | Annotation Reason |
|------|-----------|-----------------|-------------------|
| L3-1 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Bitcoin_ The Digital Revolution.pptx". On slide 1, change the color of all |
| L3-2 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Game Theory.pptx" and perform all of the following: (1) On slide 1, set ba |
| L3-3 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Evolution of Rock Music.pptx" and perform: (1) Slide 1: background bla |
| L3-4 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx" |
| L3-5 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Golden Age of Arcade Games.pptx". On slide 1, make all text bold, unde |
| L3-6 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Evolution of Rock Music.pptx". Change the title font size on ALL slide |
| L3-7 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "black_concise_work_report_template_english.pptx" and apply: (1) Slide 1: T |
| L3-8 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Golden Age of Arcade Games.pptx": (1) Set ALL slides background to black |
| L3-9 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "work_summary_template_english.pptx" and apply all changes: (1) Slide 1: ti |
| L3-10 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "Game Theory.pptx": (1) On slide 4, change all body text to italic and dark b |
| L3-11 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Birthday Paradox.pptx": (1) On slide 1, change all text to "Times New Ro |
| L3-12 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx" |
| L3-13 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Vincent van Gogh_ A Life of Passion and Color.pptx". Make all title text b |
| L3-14 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Game Theory.pptx". On slide 1, set the background to dark blue (#00008B) a |
| L3-15 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "Bitcoin_ The Digital Revolution.pptx": (1) On slide 1, set the background co |
| L3-16 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "work_summary_template_english.pptx". On slide 1, make the title bold, 48pt |
| L3-17 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "Bitcoin_ The Digital Revolution.pptx" and perform the following changes: ( |
| L3-18 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "black_concise_work_report_template_english.pptx". On slide 1, change all t |
| L3-19 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Birthday Paradox.pptx" and perform all changes: (1) On slide 1, set al |
| L3-20 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open the Tencent 2025 Interim Report and perform these changes: (1) On slide 1,  |
| L3-21 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "work_summary_template_english.pptx": (1) On slide 2, center-align body text  |
| L3-22 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In the Ecosystem Biodiversity presentation: (1) On slide 3, make the title bold  |
| L3-23 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "Tencent Holdings Limited - 2025 Interim Report.pptx": (1) On slide 1, make a |
| L3-24 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In the Van Gogh presentation: (1) Slide 5: body text dark red (#8B0000) and ital |
| L3-25 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "The Evolution of Rock Music.pptx": (1) Right-align the title on ALL slides.  |
| L3-26 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | In "black_concise_work_report_template_english.pptx": (1) On ALL slides, set tit |
| L3-27 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open the Van Gogh presentation and do all of the following: (1) Slide 1: backgro |
| L3-28 | Official Help | [Impress Guide](https://help.libreoffice.org/latest/en-US/text/simpress/guide/main.html) | Open "The Golden Age of Arcade Games.pptx" and apply: (1) ALL slides: background |

#### L3 Task Summary Table

| # | Task Name | Material File | Evaluation Function |
|---|-----------|---------------|---------------------|
| 1 | Bitcoin_ The Digital Revolution | `Bitcoin_ The Digital Revolution.pptx` | `compare_pptx_files`  |
| 2 | Game Theory | `Game Theory.pptx` | `compare_pptx_files`  |
| 3 | The Evolution of Rock Music | `The Evolution of Rock Music.pptx` | `compare_pptx_files`  |
| 4 | Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `compare_pptx_files`  |
| 5 | The Golden Age of Arcade Games | `The Golden Age of Arcade Games.pptx` | `compare_pptx_files`  |
| 6 | The Evolution of Rock Music | `The Evolution of Rock Music.pptx` | `compare_pptx_files`  |
| 7 | black_concise_work_report_template_english | `black_concise_work_report_template_english.pptx` | `compare_pptx_files`  |
| 8 | The Golden Age of Arcade Games | `The Golden Age of Arcade Games.pptx` | `compare_pptx_files`  |
| 9 | work_summary_template_english | `work_summary_template_english.pptx` | `compare_pptx_files`  |
| 10 | Game Theory | `Game Theory.pptx` | `compare_pptx_files`  |
| 11 | The Birthday Paradox | `The Birthday Paradox.pptx` | `compare_pptx_files`  |
| 12 | Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `compare_pptx_files`  |
| 13 | Vincent van Gogh_ A Life of Passion and Color | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `compare_pptx_files`  |
| 14 | Game Theory | `Game Theory.pptx` | `compare_pptx_files`  |
| 15 | Bitcoin_ The Digital Revolution | `Bitcoin_ The Digital Revolution.pptx` | `compare_pptx_files`  |
| 16 | work_summary_template_english | `work_summary_template_english.pptx` | `compare_pptx_files`  |
| 17 | Bitcoin_ The Digital Revolution | `Bitcoin_ The Digital Revolution.pptx` | `compare_pptx_files`  |
| 18 | black_concise_work_report_template_english | `black_concise_work_report_template_english.pptx` | `compare_pptx_files`  |
| 19 | The Birthday Paradox | `The Birthday Paradox.pptx` | `compare_pptx_files`  |
| 20 | Tencent Holdings Limited - 2025 Interim Report | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `compare_pptx_files`  |
| 21 | work_summary_template_english | `work_summary_template_english.pptx` | `compare_pptx_files`  |
| 22 | Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests | `Ecosystem Mechanisms for Maintaining Biodiversity in Natural Forests.pptx` | `compare_pptx_files`  |
| 23 | Tencent Holdings Limited - 2025 Interim Report | `Tencent Holdings Limited - 2025 Interim Report.pptx` | `compare_pptx_files`  |
| 24 | Vincent van Gogh_ A Life of Passion and Color | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `compare_pptx_files`  |
| 25 | The Evolution of Rock Music | `The Evolution of Rock Music.pptx` | `compare_pptx_files`  |
| 26 | black_concise_work_report_template_english | `black_concise_work_report_template_english.pptx` | `compare_pptx_files`  |
| 27 | Vincent van Gogh_ A Life of Passion and Color | `Vincent van Gogh_ A Life of Passion and Color.pptx` | `compare_pptx_files`  |
| 28 | The Golden Age of Arcade Games | `The Golden Age of Arcade Games.pptx` | `compare_pptx_files`  |

---

### 3.4 Interactive Tasks (Impress) -- 25 tasks

> Interactive tasks use multi-phase design with `trigger` controlling phase transitions.


#### Scenario Type: `ambiguous_detail` (Ambiguous Detail) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Unclear design details
> **Evidence**: Receives "make this presentation look better" without specifying colors/fonts/layout

##### interactive_impress_003 (L3)

- **Scenario Description**: The user says to update the cover page but doesn't specify what. The agent asks, then changes the year from '2019' to '2025'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me update the cover page
  - Phase 2 (trigger: `agent_done`): Change the year '2019' on the cover to '2025', then save

##### interactive_impress_009 (L3)

- **Scenario Description**: The user says to add a conclusion but doesn't specify the content. The agent asks, then appends text to the last slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a conclusion
  - Phase 2 (trigger: `agent_done`): At the end of the last slide, add 'Game theory provides tools for strategic decision-making.', then save

##### interactive_impress_015 (L3)

- **Scenario Description**: The user says to add presenter info but doesn't specify the content. The agent asks, then adds the department name on the last slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add presenter info
  - Phase 2 (trigger: `agent_done`): On the last slide, add 'Presented by: Music History Department', then save

##### interactive_impress_017 (L3)

- **Scenario Description**: The user says to add some key information but doesn't specify what. The agent asks, then adds a summary statement on the last slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add some key info to the slides
  - Phase 2 (trigger: `agent_done`): On the last slide, add 'The arcade era transformed gaming culture forever.', then save


#### Scenario Type: `ambiguous_scope` (Ambiguous Scope) -- 3 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Uncertain edit scope
> **Evidence**: Receives "adjust the content" without specifying which pages

##### interactive_impress_007 (L2)

- **Scenario Description**: The user says to add a reference on some slide but doesn't specify which. The agent asks, then adds it only on the last slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a reference on one of the slides
  - Phase 2 (trigger: `agent_done`): Only add 'Reference: Smith et al., 2024' on the last slide, leave other slides unchanged, then save

##### interactive_impress_013 (L2)

- **Scenario Description**: The user says to add author info but doesn't specify which slide. The agent asks, then adds it only on the first slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add author info to the slides
  - Phase 2 (trigger: `agent_done`): Only add 'Author: Dr. Sarah Chen' on the first slide, leave other slides unchanged, then save

##### interactive_impress_019 (L3)

- **Scenario Description**: The user says to add copyright info but doesn't specify which slide. The agent asks, then adds it only on the last slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add copyright info to one of the slides
  - Phase 2 (trigger: `agent_done`): Only add '(c) Art History Department 2025' on the last slide, leave other slides unchanged, then save


#### Scenario Type: `ambiguous_target` (Ambiguous Target) -- 3 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Vague presentation edits
> **Evidence**: Receives "fix this PPT" without specifying which slides

##### interactive_impress_001 (L2)

- **Scenario Description**: The user says to change a title but doesn't say which one. The agent asks, then changes the first slide's 'Fashion Summary' to 'Annual Work Summary'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me change that title
  - Phase 2 (trigger: `agent_done`): Change 'Fashion Summary' on the first slide to 'Annual Work Summary', then save

##### interactive_impress_005 (L3)

- **Scenario Description**: The user says to add a note on some slide but doesn't specify which. The agent asks, then adds a disclaimer on the last slide.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me add a note on one of the slides
  - Phase 2 (trigger: `agent_done`): On the last slide, add 'This presentation is for educational purposes only.', then save

##### interactive_impress_011 (L3)

- **Scenario Description**: The user says to change the report type but doesn't specify the field. The agent asks, then changes 'Interim Report' to 'Annual Report' on the cover.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_asks`): Help me change that report type
  - Phase 2 (trigger: `agent_done`): Change 'Interim Report' on the cover to 'Annual Report', then save


#### Scenario Type: `error_correction` (Error Correction) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Presentation error correction
> **Evidence**: Title/content/layout errors found, requiring correction

##### interactive_impress_error_correction_001 (L3)

- **Scenario Description**: User asks to modify text on 'the last slide' but agent modifies the wrong one. User corrects with the specific slide number.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=5)): Add the text 'Presented by: Music History Dept.' on the last slide
  - Phase 2 (trigger: `agent_done`): Hmm, that doesn't look right. I think you added it to the wrong place. Please make sure 'Presented by: Music History Dept.' appears as a text box at t
  - Phase 3 (trigger: `agent_done`): Now also add 'Thank You!' as the main title text on that same last slide. Save the file.

##### interactive_impress_error_correction_002 (L3)

- **Scenario Description**: User asks agent to add a slide. Agent adds it but with wrong content. User provides the correct text.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=5)): Add a new slide at the end with some conclusion text
  - Phase 2 (trigger: `agent_done`): That conclusion doesn't capture what I want. Please replace it with: Title: 'Legacy of Arcade Gaming', Content: 'The arcade era established the founda
  - Phase 3 (trigger: `agent_done`): Good. Now also add 'Sources: ESA Annual Report 2024' at the bottom of that slide. Save.


#### Scenario Type: `multi_step_workflow` (Multi-step Workflow) -- 1 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Complete presentation workflow
> **Evidence**: Full pipeline: content editing, formatting, transitions/animations

##### interactive_impress_workflow_001 (L3)

- **Scenario Description**: Multi-step workflow: the user guides the agent through several coordinated actions or phases.
- **Phases**: 4
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `agent_done`): Please open MyPresentation.pptx on the desktop and change the title of the first slide to "Project Report"
  - Phase 2 (trigger: `agent_done`): Okay, now add a subtitle below the title on the first slide, writing "Q1 2025"
  - Phase 3 (trigger: `agent_done`): Then create a new slide and give it the title "Project Progress"
  - Phase 4 (trigger: `agent_done`): Finally, please save the entire presentation


#### Scenario Type: `progressive_refinement` (Progressive Refinement) -- 6 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Phased presentation creation
> **Evidence**: Start with content confirmation, then add design/animations/transitions

##### interactive_impress_002 (L2)

- **Scenario Description**: The user first asks to add a summary slide at the end, then asks to fill in specific content.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a summary slide at the end
  - Phase 2 (trigger: `agent_done`): On the new slide, add the title 'Q4 Summary' and the content 'Revenue target achieved.', then save

##### interactive_impress_008 (L3)

- **Scenario Description**: The user first asks to add a new slide at the end, then asks to fill in the title and content.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a new slide at the end
  - Phase 2 (trigger: `agent_done`): On the new slide, add the title 'Conservation Implications' and the content 'Protecting biodiversity is essential.', then save

##### interactive_impress_010 (L3)

- **Scenario Description**: The user first asks to change the first slide's title, then asks to change the subtitle.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me change the first slide's title from 'Game Theory' to 'Introduction to Game Theory'
  - Phase 2 (trigger: `agent_done`): Done. Now change the subtitle to 'A Mathematical Approach to Strategy', then save

##### interactive_impress_014 (L3)

- **Scenario Description**: The user first asks to add a summary slide at the end, then asks to fill in the key takeaway.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a summary slide at the end
  - Phase 2 (trigger: `agent_done`): On the summary slide, add 'Key Takeaway: Even unlikely events become probable over many trials.', then save

##### interactive_impress_016 (L3)

- **Scenario Description**: The user first asks to add an ending slide, then asks to fill in the closing statement.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add an ending slide at the end
  - Phase 2 (trigger: `agent_done`): On the ending slide, add 'Rock music remains a powerful force in modern culture.', then save

##### interactive_impress_020 (L3)

- **Scenario Description**: The user first asks to add a 'Legacy' slide, then asks to fill in the body text.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add a new slide at the end with the title 'Legacy'
  - Phase 2 (trigger: `agent_done`): On the Legacy slide, add the body text 'Van Gogh influenced generations of artists.', then save


#### Scenario Type: `requirement_change` (Requirement Change) -- 4 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Presentation requirement change
> **Evidence**: Mid-production request to change color scheme or add/remove slides

##### interactive_impress_004 (L2)

- **Scenario Description**: The user first asks to add 'Prepared by: Team A' on the first slide, then changes it to the more detailed 'Prepared by: Analytics Team A'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add 'Prepared by: Team A' on the first slide
  - Phase 2 (trigger: `agent_done`): Change it to 'Prepared by: Analytics Team A' instead, that's more complete, then save

##### interactive_impress_006 (L3)

- **Scenario Description**: The user first adds 'Prepared by: Research Team', then changes it to the more detailed 'Prepared by: Blockchain Research Team'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add 'Prepared by: Research Team' on the last slide
  - Phase 2 (trigger: `agent_done`): Change it to 'Prepared by: Blockchain Research Team' instead, more specific, then save

##### interactive_impress_012 (L3)

- **Scenario Description**: The user first asks to add 'For internal use only.' on the last slide, then changes it to the more professional 'For authorized personnel only.'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add 'For internal use only.' on the last slide
  - Phase 2 (trigger: `agent_done`): Make it more professional, change it to 'For authorized personnel only.', then save

##### interactive_impress_018 (L3)

- **Scenario Description**: The user first asks to add 'The End', then changes it to the more formal 'Thank You for Your Attention'.
- **Phases**: 2
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Help me add 'The End' on the last slide
  - Phase 2 (trigger: `agent_done`): Change it to 'Thank You for Your Attention' instead, more formal, then save


#### Scenario Type: `task_interruption` (Task Interruption) -- 2 tasks

> **Source Type**: Real-World Scenario | **Real-World Source**: Presentation editing interruption
> **Evidence**: During editing told to add speaker notes or modify completed sections

##### interactive_impress_interruption_001 (L3)

- **Scenario Description**: User asks agent to modify slide titles, then interrupts to check the file size, then asks to continue adding content.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Change the title on slide 1 to 'Introduction to Game Theory'
  - Phase 2 (trigger: `agent_done`): Wait - can you check the file size of this presentation? Use 'ls -lh' in a terminal to see how big the file is on Desktop
  - Phase 3 (trigger: `agent_done`): OK, now go back to the presentation and add a new slide at the end with the title 'Key Takeaways' and the text 'Game theory helps us understand strate

##### interactive_impress_interruption_002 (L3)

- **Scenario Description**: User asks agent to add speaker notes, then interrupts to organize files on Desktop, then asks to continue with slide transitions.
- **Phases**: 3
- **Evaluation Function**: `check_include_exclude`
- **Phase Design**:
  - Phase 1 (trigger: `step_count` (value=3)): Add speaker notes to slide 1: 'Welcome the audience and introduce the topic of probability.'
  - Phase 2 (trigger: `agent_done`): Actually, before continuing - can you create a folder called 'Presentations' on the Desktop and move this pptx file there?
  - Phase 3 (trigger: `agent_done`): Now open the file from its new location and add 'Author: Dr. Sarah Chen' as text on the first slide. Save.

#### Interactive Task Source Mapping

| Scenario Type | Count | Real-World Source | Evidence | Trigger Combo |
|--------------|-------|-------------------|----------|---------------|
| `ambiguous_detail` (Ambiguous Detail) | 4 | Unclear design details | Receives "make this presentation look better" without specif | agent_asks + agent_done |
| `ambiguous_scope` (Ambiguous Scope) | 3 | Uncertain edit scope | Receives "adjust the content" without specifying which pages | agent_asks + agent_done |
| `ambiguous_target` (Ambiguous Target) | 3 | Vague presentation edits | Receives "fix this PPT" without specifying which slides | agent_asks + agent_done |
| `error_correction` (Error Correction) | 2 | Presentation error correction | Title/content/layout errors found, requiring correction | agent_done + step_count |
| `multi_step_workflow` (Multi-step Workflow) | 1 | Complete presentation workflow | Full pipeline: content editing, formatting, transitions/anim | agent_done |
| `progressive_refinement` (Progressive Refinement) | 6 | Phased presentation creation | Start with content confirmation, then add design/animations/ | agent_done + step_count |
| `requirement_change` (Requirement Change) | 4 | Presentation requirement change | Mid-production request to change color scheme or add/remove  | agent_done + step_count |
| `task_interruption` (Task Interruption) | 2 | Presentation editing interruption | During editing told to add speaker notes or modify completed | agent_done + step_count |

#### Interactive Trigger Type Distribution

| Trigger Type | Count | Description |
|-------------|-------|-------------|
| `agent_done` | 32 | Automatically enters next phase when previous phase completes |
| `step_count` | 14 | Injects new instructions after reaching specified step count |
| `agent_asks` | 10 | Triggered when agent proactively asks user for clarification |

#### Interactive Task Source Mapping

| Scenario Type | Real-World Source | Evidence Package | Task JSON `source` |
|--------------|-------------------|------------------|--------------------|
| `ambiguous_target` | Vague PPT edit request | ① Original request ② Clarification ③ Execution | `impress_interactive;source_type=slide_edit;evidence=ambiguous_target` |
| `progressive_refinement` | Staged PPT creation (outline→layout→animation) | ① Phase confirmation ② Refinement ③ Final | `impress_interactive;source_type=presentation;evidence=staged_refinement` |
| `requirement_change` | Mid-task PPT requirement change | ① Initial ② Change order ③ Diff record | `impress_interactive;source_type=change;evidence=requirement_change` |
| `error_correction` | Slide format correction | ① Error description ② Correction ③ Verification | `impress_interactive;source_type=format_fix;evidence=error_correction` |

#### Source Evidence Fields

- **source_type**: `slide_edit` / `presentation` / `change` / `format_fix` / `animation` / `transition`
- **source_ref**: Source identifier (anonymized URL, ticket ID, interview record ID)
- **captured_at**: Evidence capture date (`YYYY-MM-DD`)
- **anonymized_excerpt**: Anonymized original text excerpt (1-3 sentences)
- **mapping_note**: How the original requirement maps to `phases` and `trigger`
- **reviewers**: Dual-review and adjudication record (`reviewer_a/reviewer_b/adjudicator`)

---

## 4. Evaluation Function Summary

| # | Function | Category | Usage Count |
|---|----------|----------|-------------|
| 1 | `compare_pptx_files` | Static Tasks | 28 |
| 2 | `check_transition` | Static Tasks | 1 |
| 3 | `check_slide_orientation_Portrait` | Static Tasks | 1 |
| 4 | `check_include_exclude` | Interactive Tasks | 25 |

**Total**: Covering 30 static tasks + 25 interactive tasks = **55** tasks.

---

## 5. Material Description

| Property | Value |
|----------|-------|
| File Format | `.pptx` (Office Open XML Presentation) |
| Initial Files | 10 unique `.pptx` templates (some shared across tasks) |
| Gold Files | 30 gold `.pptx` files (different difficulty variants) |
| Language | English content |
| Topics | Bitcoin, Game Theory, Rock Music, Arcade Games, Ecosystem, Work Reports |

---

## 6. Task JSON Templates

### Static Task (compare_pptx_files)

```json
{
  "evaluator": {
    "func": "compare_pptx_files",
    "expected": {"type": "cache_file", "path": "<gold>.pptx"},
    "result": {"type": "vm_file", "path": "/home/user/<file>.pptx"},
    "options": {"examine_shape": true}
  }
}
```

---

## 7. Docker Image Requirements

- **LibreOffice Impress** (7.x+), **X11**, **Python 3 + python-pptx**

---

## 8. Difficulty Distribution Summary

| Level | Count | Instruction Length | Operation Steps | Description | Examples |
|-------|-------|-------------------|----------------|-------------|---------|
| L1 | 9 | 80-129 chars | 1-2 steps | Single-step ops | Add transition, change title font size, single-slide font/color, slide orientation |
| L2 | 9 | 153-295 chars | 2-3 steps (2 sub-steps) | Multi-step ops | Body center + title setup, all-slides title + single-slide background, dual ops |
| L3 | 12 | 243-668 chars | 5-7 steps (numbered sub-steps) | Complex workflows | Multi-slide edit + background + font + color + notes + delete slides (7-step combo) |
| **Total** | **30** | | | | |

### Verifiability Guarantee

1. **`.pptx` structured comparison** via `python-pptx` -- no screenshot/OCR dependency.
2. **Attribute-level verification**: `check_transition` and `check_slide_orientation_Portrait` verify XML attributes directly.

> Difficulty tags based on kimi-k2.5 model execution under max_steps=50 (static) / max_steps=80 (interactive).

---

## 9. Common Pitfalls

- **Shape ID changes**: LibreOffice may reassign shape IDs on save; use position/content matching instead.
- **Transition names**: LibreOffice uses different internal transition names than PowerPoint.
- **Save dialog**: `.pptx` requires `Enter` after `Ctrl+S` to dismiss format confirmation.
- **Gold files**: Must exist in both `OSWorld/cache/<task_id>/` and `desktopworld/cache/<task_id>/`.
- **Shared templates**: Some tasks use the same initial `.pptx` but different gold files (e.g., `The Evolution of Rock Music.pptx` has L1/L3 variants).
