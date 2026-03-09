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
Results are stored per-task as `result.txt` (score 0.0 or 1.0) under `results/<run_name>/pyautogui/screenshot/<domain>/<task_id>/`.

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
Task lists (`test_all.json`, `gimp_new.json`, etc.) map domain names to lists of task IDs.

### Evaluators (`desktop_env/evaluators/`)
- **`__init__.py`**: Registry mapping function name strings → Python callables (`eval_funcs` dict). New evaluator functions must be registered here.
- **`metrics/`**: Evaluation logic (e.g., `new_gimp.py` contains GIMP-specific check functions)
- **`getters/`**: Functions that extract files/data from the VM before evaluation (e.g., `gimp.py` fetches XCF files or config files from the VM)

### Agents (`mm_agents/`)
Each agent class implements `predict(instruction, obs) -> (response, actions)` and `reset(...)`. The primary agents in use:
- `uitars15_v2.py` — UI-TARS 1.5 agent (main benchmark agent), supports Doubao and Qwen backends
- `evocua/evocua_agent.py` — EvoCua agent for interactive tasks
- `owl_agent.py`, `mano_agent.py` — other agent implementations
- `user_simulator.py` — simulates user in interactive evaluation

### Task Generation (`task_gen/`)
Pipeline for creating new benchmark tasks: candidate generation → function extraction (`complete_functions.py`) → classification (`classify_evaluator.py`) → config generation → validation (`check_task_rules.py`). Verified task candidates are in `task_gen/checked_candidates/`. The `task_gen/evaluator_func2/funcs/` directory contains 200+ reusable atomic verification functions.

## Adding a New Evaluator

1. Write the check function in `desktop_env/evaluators/metrics/` (or `new_gimp.py` for GIMP tasks)
2. Register it in `desktop_env/evaluators/__init__.py` in the `eval_funcs` dict
3. If the function needs to fetch files from the VM first, add a getter in `desktop_env/evaluators/getters/` and reference it in the task JSON's `evaluator.result`
4. Create a task JSON in `evaluation_examples/examples/<domain>/`
5. Add the task ID to the appropriate list in `evaluation_examples/test_all.json`

## Key Environment Variables

Set in `.env` or the shell:
- `DOUBAO_API_KEY`, `DOUBAO_API_URL` — for Doubao/vLLM model access
- `AWS_REGION`, `AWS_SUBNET_ID`, `AWS_SECURITY_GROUP_ID` — required even for Docker provider (set dummy values)
- `GET_OBS_BEFORE_ACTION=1` — capture screenshot before each action step
