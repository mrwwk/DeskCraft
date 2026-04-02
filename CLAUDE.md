# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

OSWorld is a benchmark for evaluating multimodal GUI agents on real desktop tasks. Agents are given natural language instructions and must operate a virtual desktop (via Docker/VMware/cloud VMs) to complete tasks across applications like Chrome, LibreOffice, GIMP, VLC, and VS Code. Each task is evaluated using programmatic checks on the resulting VM state.

## Installation

```bash
pip install -r requirements.txt
# Or for just the environment package:
pip install desktop-env
```

Environment variables (API keys, VM credentials) are loaded from `.env` via `python-dotenv`.

## Running Evaluations

**Quick test with Docker:**
```bash
python quickstart.py --provider_name docker --headless True
```

**Multi-environment evaluation (primary workflow):**
```bash
python run_multienv_uitars15_v2.py \
    --domain gimp_new \
    --provider_name docker \
    --headless \
    --num_envs 3 \
    --max_steps 15 \
    --model "UI-TARS-1.5-7B"
```

Each agent has its own `run_multienv_<agent>.py` script (e.g., `run_multienv_claude.py`, `run_multienv_qwen3vl.py`, `run_multienv_evocua.py`). All share the same core arguments:
- `--domain`: Filter tasks by app domain (`all`, `gimp_new`, `chrome`, etc.)
- `--num_envs`: Parallel Docker containers
- `--test_all_meta_path`: Path to task list JSON (default: `evaluation_examples/test_all.json`)
- `--result_dir`: Output directory (default: `./results`)
- `--run_name`: Custom folder name under result_dir

**Full Taiji cluster workflow** is in `taiji_task/start.sh` — starts dockerd, loads the image, launches vLLM, then runs evaluation.

**Calculate success rate after evaluation:**
```bash
python calc_success_rate.py <result_dir>
```
Results are stored per-task as `result.txt` (score 0.0 or 1.0) and `traj.jsonl` (full trajectory) under `results/<run_name>/pyautogui/screenshot/<domain>/<task_id>/`.

**Test evaluator functions without running full evaluation:**
```bash
python test_l2_evaluators.py
```

## Architecture

### Evaluation Loop (`lib_run_single.py`)
`run_single_example()` is the core loop called by all `run_multienv_*.py` scripts:
1. `env.reset(task_config)` — reverts VM snapshot, runs setup commands
2. `agent.reset(vm_ip=...)` — reinitializes agent with fresh VM IP
3. Loop up to `max_steps`: `agent.predict(instruction, obs)` → `env.step(action)`
4. Screenshots and trajectory saved to `example_result_dir/`
5. `env.evaluate()` — runs evaluator function, returns 0.0 or 1.0
6. Recording saved as `recording.mp4`

### Desktop Environment (`desktop_env/desktop_env.py`)
Implements the Gymnasium interface. Key responsibilities:
- Manages VM lifecycle via provider backends (`desktop_env/providers/`)
- Observations: screenshots, accessibility trees, or Set-of-Marks (SOM)
- Actions: dispatched as pyautogui commands to the VM
- Evaluation: calls the `evaluator.func` from the task JSON, passing results from getters

### Task Configuration (`evaluation_examples/`)
Each task is a JSON file with this structure:
```json
{
  "id": "uuid",
  "snapshot": "snapshot_name",
  "instruction": "natural language task description",
  "config": [{"type": "setup_action", ...}],
  "evaluator": {
    "func": "eval_function_name",
    "result": {"type": "getter_type", ...},
    "expected": {"type": "rule", ...}
  }
}
```
Task lists (`test_all.json`, `gimp_new.json`, `kdenlive_all.json`, `interactive_all.json`, etc.) map domain names to lists of task IDs. Tasks are classified by difficulty: L1 (single operation), L2 (composite operations), L3 (advanced workflows).

### Evaluators (`desktop_env/evaluators/`)
- **`__init__.py`**: Registry mapping function name strings → Python callables (`eval_funcs` dict). Functions from `metrics/*.py` files must be explicitly imported and added to `eval_funcs` before they can be used in task JSONs. Currently registered: GIMP (`new_gimp.py`), Inkscape (`inkscape.py`), and others.
- **`metrics/`**: Evaluation logic (e.g., `new_gimp.py` for GIMP, `kdenlive.py` for video editing, `inkscape.py` for SVG editing)
- **`getters/`**: Functions that extract files/data from the VM before evaluation (e.g., `gimp.py` fetches XCF files or config files from the VM). Getter results are passed as the first argument to evaluator functions.

### Agents (`mm_agents/`)
Each agent class implements `predict(instruction, obs) -> (response, actions)` and `reset(...)`. The primary agents in use:
- `uitars15_v2.py` — UI-TARS 1.5 agent (main benchmark agent), supports Doubao and Qwen backends
- `evocua/evocua_agent.py` — EvoCua agent for interactive tasks
- `owl_agent.py`, `mano_agent.py` — other agent implementations
- `user_simulator.py` — simulates user in interactive evaluation

### Task Generation (`task_gen/`)
Pipeline for creating new benchmark tasks: candidate generation → function extraction (`complete_functions.py`) → classification (`classify_evaluator.py`) → config generation → validation (`check_task_rules.py`). Verified task candidates are in `task_gen/checked_candidates/`. The `task_gen/evaluator_func2/funcs/` directory contains 200+ reusable atomic verification functions.

## Adding a New Evaluator

1. Write the check function in `desktop_env/evaluators/metrics/` (e.g., `inkscape.py` for Inkscape, `new_gimp.py` for GIMP). Function signature: `def check_xxx(file_path, rule) -> float` returning 1.0 or 0.0.
2. Register it in **two** `__init__.py` files:
   - `desktop_env/evaluators/metrics/__init__.py` — add the import
   - `desktop_env/evaluators/__init__.py` — add both the import AND the entry in the `eval_funcs` dict
3. If the function needs to fetch files from the VM first, add a getter in `desktop_env/evaluators/getters/` and reference it in the task JSON's `evaluator.result`
4. Create task JSON files in `evaluation_examples/examples/<domain>/` (see "Creating Task JSON Files" below)
5. Create a task list JSON (e.g., `evaluation_examples/<domain>_all.json`) mapping domain name to task ID array
6. Add the task IDs to the appropriate list in `evaluation_examples/test_all.json`

## Creating Task JSON Files

### Task JSON Structure

Each task JSON must include all required fields. Use the following template:

```json
{
  "id": "<uuid4>",
  "snapshot": "<app_name>",
  "instruction": "Open ... in <App>. <Do something specific>, then save the file.",
  "source": "",
  "config": [
    {
      "type": "upload_file",
      "parameters": {
        "files": [
          {
            "local_path": "assets/<domain>/<filename>",
            "path": "/home/user/Documents/<filename>"
          }
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["/usr/bin/<app>", "/home/user/Documents/<filename>"]
      }
    },
    {
      "type": "sleep",
      "parameters": {
        "seconds": 3
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["<app_name>"],
  "evaluator": {
    "postconfig": [],
    "func": "<evaluator_function_name>",
    "result": {
      "type": "vm_file",
      "path": "/home/user/Documents/<filename>",
      "dest": "<filename>"
    },
    "expected": {
      "type": "rule",
      "rules": { ... }
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### Evaluation Call Flow

The framework resolves getters by mapping the `"type"` field to `get_{type}()` function in `desktop_env/evaluators/getters/`. The dispatch logic (`desktop_env/desktop_env.py` lines 346-376):

1. **result getter**: `evaluator.result.type` → `get_{type}(env, result_config)` → returns `result_state`
2. **expected getter**: `evaluator.expected.type` → `get_{type}(env, expected_config)` → returns `expected_state`
3. **Evaluator call**: `func(result_state, expected_state, **options)` → returns score (0.0 or 1.0)

If `expected` is absent, the call is `func(result_state, **options)`.

**Available result getter types** (by frequency in existing tasks):

| `result.type` | Getter | Returns | Usage |
|---|---|---|---|
| `vm_file` | `get_vm_file` | Local file path(s) downloaded from VM | Most common (~75%). For file-based checks (SVG, pptx, docx, etc.) |
| `vm_command_line` | `get_vm_command_line` | stdout string from running a command on VM | Shell command checks (file existence, process state, config values) |
| `active_tab_html_parse` | `get_active_tab_html_parse` | Parsed HTML content from Chrome active tab | Web content verification |
| `active_url_from_accessTree` | `get_active_url_from_accessTree` | URL string from accessibility tree | Chrome URL checks |
| `cache_file` | `get_cache_file` | Local cached file path | Pre-cached reference files |
| `googledrive_file` | `get_googledrive_file` | Downloaded file from Google Drive | Cloud document tasks |
| `vlc_config` | `get_vlc_config` | VLC config file content | VLC settings checks |
| `gimp_config_file` | `get_gimp_config_file` | GIMP config content | GIMP preference checks |
| `xcf_file` | `get_xcf_file` | Local path of downloaded XCF file | GIMP project file checks |
| `accessibility_tree` | `get_accessibility_tree` | Accessibility tree XML string | UI state verification |
| `vm_terminal_output` | `get_vm_terminal_output` | Terminal output from VM | Command output checks |
| `cloud_file` | `get_cloud_file` | Local path downloaded from URL | Remote reference files |
| `content_from_vm_file` | `get_content_from_vm_file` | File content (text/JSON) from VM | Content-based checks |
| `vm_wallpaper` | `get_vm_wallpaper` | Wallpaper file/path | Desktop customization checks |
| Others | `get_open_tabs_info`, `get_bookmarks`, `get_vscode_config`, etc. | Various | App-specific state |

**Available expected getter types**:

| `expected.type` | Getter | Returns | Usage |
|---|---|---|---|
| `rule` | `get_rule` | `config["rules"]` dict as-is | Most common (~50%). Rule-based evaluation (pass dict of expected values) |
| `cloud_file` | `get_cloud_file` | Local path downloaded from URL | File comparison (~46%). Downloads gold-standard file for diff comparison |
| `rule_relativeTime` | `get_rule_relativeTime` | Rules with resolved relative time expressions | Time-dependent tasks |
| `vm_file` | `get_vm_file` | Local file path from VM | Rare. When expected state is also on VM |

**Advanced patterns**:

- **Multi-metric**: `func`, `result`, `expected`, and `options` can all be **lists** of the same length. Each entry forms an independent evaluation. Use `"conj": "and"` (all must pass, default) or `"conj": "or"` (any can pass).
- **Options**: `evaluator.options` is an optional dict passed as `**kwargs` to the metric function. If absent, defaults to `{}`.
- **Postconfig**: `evaluator.postconfig` runs setup actions (activate window, save file, sleep) on the VM **before** evaluation, e.g., to force-save an open document.

**Example patterns**:

```jsonc
// Pattern 1: File + rule (most common for new app domains)
{"result": {"type": "vm_file", "path": "/home/user/file.svg", "dest": "file.svg"},
 "expected": {"type": "rule", "rules": {"element_id": "rect1", "expected_fill": "#ff0000"}}}

// Pattern 2: File + gold-standard comparison
{"result": {"type": "vm_file", "path": "/home/user/Desktop/doc.pptx", "dest": "doc.pptx"},
 "expected": {"type": "cloud_file", "path": "https://huggingface.co/.../gold.pptx", "dest": "gold.pptx"},
 "options": {"examine_shape": false}}

// Pattern 3: Command output + rule
{"result": {"type": "vm_command_line", "command": "cat /etc/timezone", "shell": true},
 "expected": {"type": "rule", "rules": {"expected": "UTC\n"}}}

// Pattern 4: Multi-metric with conjunction
{"func": ["compare_pptx_files", "compare_pptx_files"], "conj": "or",
 "result": [{"type": "vm_file", ...}, {"type": "vm_file", ...}],
 "expected": [{"type": "cloud_file", ...}, {"type": "cloud_file", ...}]}
```

### Checklist for New Task JSONs

When creating or reviewing task JSON files, verify all of the following:

1. **Instruction clarity**:
   - Instruction must clearly describe the exact operation (not ambiguous)
   - Instruction must explicitly mention **saving the file** (e.g., "then save the file")
   - Instruction should reference the full file path (e.g., `/home/user/Documents/file.svg`)
   - For element-specific tasks, include the element ID in the instruction (e.g., `(id=rect1)`)

2. **Config consistency**:
   - `upload_file.files[].path` must match `evaluator.result.path` (the file uploaded is the same file evaluated)
   - `upload_file.files[].local_path` must point to a valid asset in the `assets/` directory
   - `launch.command` should use the **full binary path** (e.g., `/usr/bin/inkscape`, not `inkscape`)
   - Include a `sleep` step (3-5 seconds) after launch for GUI initialization

3. **Evaluator function match**:
   - `evaluator.func` must be a function name registered in `desktop_env/evaluators/__init__.py`
   - `evaluator.expected.rules` keys must match the function's expected parameter names exactly
   - All required rule keys must be present; no unexpected keys should exist

4. **Result path**:
   - `evaluator.result.type` is typically `"vm_file"` for file-based checks
   - `evaluator.result.path` = full path on VM (must match what the instruction tells the user to save to)
   - `evaluator.result.dest` = just the filename (used as local cache name)

### Common Pitfalls

- **Text element fill colors**: For SVG text elements, Inkscape often stores `fill` on `<tspan>` children rather than the parent `<text>` element. Evaluator functions checking text fill must check both the element and its tspan children.
- **Style vs attribute**: SVG properties can appear either in the `style` attribute (e.g., `style="fill:#ff0000"`) or as direct XML attributes (e.g., `fill="#ff0000"`). Evaluators must check both.
- **Namespace handling**: Inkscape SVGs use multiple namespaces (`inkscape:`, `sodipodi:`, `svg:`). Use proper namespace-aware lookups (e.g., `{http://www.inkscape.org/namespaces/inkscape}label` for `inkscape:label`).
- **Color normalization**: Always normalize hex colors (#f00 → #ff0000, uppercase → lowercase) before comparison.
- **Font weight values**: `font-weight: bold` and `font-weight: 700` are equivalent; evaluators should accept both.

### Verification Script

After creating task JSONs and evaluator functions, run this validation:

```python
import json, glob

# 1. Verify all JSONs are well-formed
files = glob.glob('evaluation_examples/examples/<domain>/*.json')
for f in files:
    data = json.load(open(f))
    assert 'save' in data['instruction'].lower(), f"{f}: instruction missing 'save'"
    result_path = data['evaluator']['result']['path']
    upload_paths = [uf['path'] for uf in data['config'][0]['parameters']['files']]
    assert result_path in upload_paths, f"{f}: result path not in uploads"

# 2. Verify evaluator imports work
from desktop_env.evaluators.metrics.<module> import *

# 3. Verify registration
from desktop_env.evaluators import eval_funcs
print([k for k in eval_funcs if '<domain>' in k])
```

## Key Environment Variables

Set in `.env` or the shell:
- `DOUBAO_API_KEY`, `DOUBAO_API_URL` — for Doubao/vLLM model access
- `AWS_REGION`, `AWS_SUBNET_ID`, `AWS_SECURITY_GROUP_ID` — required even for Docker provider (set dummy values)
- `GET_OBS_BEFORE_ACTION=1` — capture screenshot before each action step
