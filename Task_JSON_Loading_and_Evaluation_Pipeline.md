# Task JSON Loading and Evaluation Pipeline Documentation

This document explains how task JSON files from `evaluation_examples` are loaded and evaluated in the OSWorld system, focusing on the `config` field loading, evaluator loading, and evaluation logic.

## Table of Contents

1. [Overview](#overview)
2. [Task JSON Structure](#task-json-structure)
3. [Loading Pipeline](#loading-pipeline)
4. [Config Field Loading](#config-field-loading)
5. [Evaluator Loading](#evaluator-loading)
6. [Evaluation Logic](#evaluation-logic)
7. [Example Walkthrough](#example-walkthrough)
8. [Key Components](#key-components)

---

## Overview

The OSWorld evaluation system follows a structured pipeline to load task configurations and evaluate task completion:

1. **Task Loading**: Load task JSON file containing task definition
2. **Environment Setup**: Execute `config` to prepare the environment
3. **Evaluator Initialization**: Parse `evaluator` field to set up metrics and getters
4. **Task Execution**: Agent performs actions to complete the task
5. **Evaluation**: Execute evaluator to determine task success

The main logic is implemented in [desktop_env.py](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/desktop_env.py).

---

## Task JSON Structure

A typical task JSON file has the following structure:

```json
{
  "id": "2a729ded-3296-423d-aec4-7dd55ed5fbb3",
  "snapshot": "gimp",
  "instruction": "Could you make background of this image transparent for me?",
  "source": "https://www.youtube.com/watch?v=lOzSiOIipSM",
  "config": [
    {
      "type": "download",
      "parameters": {
        "files": [...]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": [...]
      }
    }
  ],
  "trajectory": "trajectories/",
  "related_apps": ["gimp"],
  "evaluator": {
    "postconfig": [...],
    "func": "check_structure_sim",
    "expected": {
      "type": "cloud_file",
      "path": "https://...",
      "dest": "dog_cutout_gold.png"
    },
    "result": {
      "type": "vm_file",
      "path": "/home/user/Desktop/dog_without_background.png",
      "dest": "dog_without_background.png"
    }
  },
  "proxy": false,
  "fixed_ip": false,
  "possibility_of_env_change": "low"
}
```

### Key Fields

- **`id`**: Unique task identifier
- **`snapshot`**: VM snapshot name to revert to
- **`instruction`**: Natural language task description
- **`config`**: List of setup operations to prepare the environment
- **`evaluator`**: Evaluation configuration (detailed below)
- **`proxy`**: Whether proxy is required for this task

---

## Loading Pipeline

The loading pipeline is triggered when `DesktopEnv.reset(task_config)` is called:

```python
# In desktop_env.py
def reset(self, task_config: Optional[Dict[str, Any]] = None, seed=None, options=None):
    # 1. Reset counters
    self._traj_no += 1
    self._step_no = 0
    self.action_history.clear()

    # 2. Revert to snapshot if environment was used
    if self.is_environment_used:
        self._revert_to_snapshot()
        self._start_emulator()
        self.is_environment_used = False

    # 3. Set task information
    if task_config is not None:
        self._set_task_info(task_config)
        self.setup_controller.reset_cache_dir(self.cache_dir)

        # 4. Setup environment using config
        success = self.setup_controller.setup(self.config, self.enable_proxy)
        if success:
            self.is_environment_used = True
```

### Step-by-Step Process

1. **Initialize Episode**: Reset trajectory and step counters
2. **Revert Snapshot**: Restore VM to clean state (if previously used)
3. **Set Task Info**: Parse task configuration
4. **Setup Environment**: Execute `config` operations
5. **Ready for Execution**: Environment is ready for agent interaction

---

## Config Field Loading

The `config` field contains a list of setup operations that prepare the environment for the task.

### Config Structure

```json
"config": [
  {
    "type": "download",
    "parameters": {
      "files": [
        {
          "url": "https://...",
          "path": "/home/user/Desktop/file.png"
        }
      ]
    }
  },
  {
    "type": "launch",
    "parameters": {
      "command": ["gimp", "/home/user/Desktop/file.png"]
    }
  }
]
```

### Config Types

Common config types include:

- **`download`**: Download files from cloud storage
- **`launch`**: Launch applications with specific parameters
- **`execute`**: Execute shell commands
- **`sleep`**: Wait for specified duration
- **`copy`**: Copy files within the VM

### Config Execution

The `SetupController.setup()` method in [setup.py](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/controllers/setup.py) handles config execution:

```python
def setup(self, config: List[Dict[str, Any]], use_proxy: bool = False) -> bool:
    for i, cfg in enumerate(config):
        config_type: str = cfg["type"]
        parameters: Dict[str, Any] = cfg["parameters"]

        # Dynamically call setup method based on type
        setup_function: str = "_{:}_setup".format(config_type)
        getattr(self, setup_function)(**parameters)
```

Each config type has a corresponding method:
- `_download_setup()`: Downloads files to VM
- `_launch_setup()`: Launches applications
- `_execute_setup()`: Executes commands
- `_sleep_setup()`: Pauses execution

---

## Evaluator Loading

The `evaluator` field is parsed in the `_set_evaluator_info()` method, which performs the following steps:

### Evaluator Loading Steps

1. **Load Metric Function(s)**: Dynamically import metric function(s) from the `metrics` module based on the `func` field. Supports both single metric (string) and multiple metrics (list of strings).

2. **Load Conjunction**: Get the conjunction type for combining multiple metrics, defaulting to "and" if not specified.

3. **Load Result Getter(s)**: Dynamically import result getter function(s) from the `getters` module based on the `result` field. The getter function name follows the pattern `get_{type}` (e.g., `get_vm_file`, `get_cloud_file`). Supports both single and multiple result configurations.

4. **Load Expected Getter(s)**: Dynamically import expected value getter function(s) from the `getters` module based on the `expected` field (if present). Used to fetch ground truth for comparison. Supports both single and multiple expected configurations.

5. **Load Metric Options**: Extract additional parameters for metric functions from the `options` field. If not specified, defaults to empty dictionary for single metric or list of empty dictionaries for multiple metrics.

The method ensures that when multiple metrics are specified, all corresponding lists (`func`, `result`, `expected`, `options`) have the same length. If a particular metric doesn't need a specific field (e.g., no expected value), `null` is used in that position.

### Evaluator Fields

- **`func`**: Metric function name(s) from [metrics](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/evaluators/metrics/__init__.py)
- **`result`**: Result getter configuration(s) from [getters](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/evaluators/getters/__init__.py)
- **`expected`**: Expected value getter configuration(s)
- **`options`**: Additional parameters for metric functions
- **`postconfig`**: Setup operations to execute before evaluation
- **`conj`**: Conjunction for multiple metrics ("and" or "or")

### Support for Multiple Metrics

The system supports evaluating multiple metrics:

```json
{
  "evaluator": {
    "func": ["check_structure_sim", "check_file_exists"],
    "result": [
      {"type": "vm_file", "path": "/path/to/result.png"},
      {"type": "vm_file", "path": "/path/to/result.txt"}
    ],
    "expected": [
      {"type": "cloud_file", "path": "https://...", "dest": "expected.png"},
      null
    ],
    "options": [
      {"threshold": 0.9},
      {}
    ],
    "conj": "and"
  }
}
```

When multiple metrics are specified:
- All lists (`func`, `result`, `expected`, `options`) must have the same length
- Use `null` for fields not needed by a specific metric
- `conj` determines how results are combined ("and" = all must pass, "or" = any must pass)

---

## Evaluation Logic

The evaluation is triggered by calling `DesktopEnv.evaluate()`. The method performs the following steps:

### Evaluation Steps

1. **Execute Postconfig**: Run any setup operations needed before evaluation (e.g., keyboard shortcuts to save files)

2. **Check Infeasible Tasks**: Handle tasks that are designed to be impossible to complete. If the task is marked as "infeasible", return 1.0 if the agent correctly identifies it as impossible (by sending a FAIL action), otherwise return 0.0.

3. **Check Explicit Failure**: If the agent explicitly sent a FAIL action, immediately return 0.0 (task failed).

4. **Get Results**: Use result getters to fetch actual outputs from the VM or cache. Each getter is called with its corresponding configuration.

5. **Get Expected Values**: Use expected getters to fetch ground truth from cloud storage or other sources (if specified in the evaluator).

6. **Compute Metrics**: Call metric functions with the actual results and expected values. Each metric function returns a float between 0.0 and 1.0.

7. **Combine Results**: For multiple metrics, apply conjunction logic:
   - **"and" conjunction**: All metrics must pass (return 1.0). If any metric returns 0.0, the overall result is 0.0. Otherwise, return the average of all metric scores.
   - **"or" conjunction**: At least one metric must pass (return 1.0). If any metric returns 1.0, the overall result is 1.0. Otherwise, return the maximum of all metric scores.

### Return Values

- **`1.0`**: Task successfully completed
- **`0.0`**: Task failed
- **`0.0 - 1.0`**: Partial success (for multiple metrics with "and" conjunction, indicating average score)

---

## Example Walkthrough

Let's walk through a complete example using the GIMP task:

### Task JSON

```json
{
  "id": "2a729ded-3296-423d-aec4-7dd55ed5fbb3",
  "snapshot": "gimp",
  "instruction": "Could you make background of this image transparent for me?",
  "config": [
    {
      "type": "download",
      "parameters": {
        "files": [
          {
            "url": "https://huggingface.co/.../dog_with_background.png",
            "path": "/home/user/Desktop/dog_with_background.png"
          }
        ]
      }
    },
    {
      "type": "launch",
      "parameters": {
        "command": ["gimp", "/home/user/Desktop/dog_with_background.png"]
      }
    }
  ],
  "evaluator": {
    "postconfig": [
      {
        "type": "execute",
        "parameters": {
          "command": ["python3", "-c", "import pyautogui; pyautogui.hotkey(['shift', 'ctrl', 'e']);"]
        }
      },
      {
        "type": "sleep",
        "parameters": {"seconds": 0.5}
      },
      {
        "type": "execute",
        "parameters": {
          "command": ["python3", "-c", "import pyautogui; pyautogui.write('dog_without_background');"]
        }
      }
    ],
    "func": "check_structure_sim",
    "expected": {
      "type": "cloud_file",
      "path": "https://huggingface.co/.../dog_cutout_gold.png",
      "dest": "dog_cutout_gold.png"
    },
    "result": {
      "type": "vm_file",
      "path": "/home/user/Desktop/dog_without_background.png",
      "dest": "dog_without_background.png"
    }
  }
}
```

### Execution Flow

1. **Load Task**:
   ```python
   env.reset(task_config)
   ```

2. **Set Task Info**:
   - `task_id = "2a729ded-3296-423d-aec4-7dd55ed5fbb3"`
   - `cache_dir = "cache/2a729ded-3296-423d-aec4-7dd55ed5fbb3"`
   - `config = [...]` (list of setup operations)

3. **Set Evaluator Info**:
   - `metric = metrics.check_structure_sim`
   - `result_getter = getters.get_vm_file`
   - `expected_getter = getters.get_cloud_file`

4. **Setup Environment**:
   - Download `dog_with_background.png` to VM
   - Launch GIMP with the image

5. **Agent Executes**:
   - Agent performs actions to remove background
   - Saves result as `dog_without_background.png`

6. **Evaluate**:
   ```python
   env.evaluate()
   ```

7. **Postconfig Execution**:
   - Press Ctrl+Shift+E to export
   - Type filename
   - Press Enter

8. **Get Results**:
   ```python
   result_state = result_getter(env, {
       "type": "vm_file",
       "path": "/home/user/Desktop/dog_without_background.png",
       "dest": "dog_without_background.png"
   })
   # Returns: "/path/to/cache/dog_without_background.png"
   ```

9. **Get Expected**:
   ```python
   expected_state = expected_getter(env, {
       "type": "cloud_file",
       "path": "https://huggingface.co/.../dog_cutout_gold.png",
       "dest": "dog_cutout_gold.png"
   })
   # Returns: "/path/to/cache/dog_cutout_gold.png"
   ```

10. **Compute Metric**:
    ```python
    metric_result = metric(result_state, expected_state)
    # Calls: check_structure_sim(result_state, expected_state)
    # Returns: 1.0 (if similar) or 0.0 (if not similar)
    ```

11. **Return Result**:
    - `1.0` = Task completed successfully
    - `0.0` = Task failed

---

## Key Components

### Metrics

Metrics are evaluation functions defined in [desktop_env/evaluators/metrics/](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/evaluators/metrics/):

- **`check_structure_sim`**: Compare image structure similarity
- **`check_file_exists_and_structure_sim`**: Check file existence and structure
- **`check_brightness_decrease_and_structure_sim`**: Check brightness and structure
- **`check_contrast_increase_and_structure_sim`**: Check contrast and structure
- **`check_saturation_increase_and_structure_sim`**: Check saturation and structure
- **`check_image_size`**: Check image dimensions
- **`check_image_mirror`**: Check if image is mirrored
- **`check_palette_and_structure_sim`**: Check palette mode and structure
- **`check_textbox_on_leftside`**: Check textbox position
- **`check_triangle_position`**: Check triangle position
- **`check_green_background`**: Check background color
- **`check_config_status`**: Check configuration status
- And many more...

### Getters

Getters retrieve data from the VM or cloud storage, defined in [desktop_env/evaluators/getters/](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/evaluators/getters/):

- **`get_vm_file`**: Copy file from VM to cache
- **`get_cloud_file`**: Download file from cloud storage
- **`get_cache_file`**: Get file from cache directory
- **`get_content_from_vm_file`**: Get file content from VM
- **`get_gimp_config_file`**: Get GIMP configuration
- **`get_accessibility_tree`**: Get accessibility tree
- **And many more...**

### Setup Controller

The [SetupController](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/controllers/setup.py) handles environment setup:

- Downloads files from cloud storage
- Launches applications
- Executes shell commands
- Manages proxy configuration
- Handles file operations

### Desktop Environment

The [DesktopEnv](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/desktop_env.py) class provides:

- Task loading and initialization
- Environment setup and reset
- Action execution
- Evaluation orchestration
- Observation retrieval

---

## Summary

The OSWorld evaluation pipeline provides a flexible and extensible framework for:

1. **Defining Tasks**: JSON-based task definitions with clear structure
2. **Setting Up Environments**: Automated environment preparation
3. **Evaluating Results**: Pluggable metrics and getters
4. **Supporting Multiple Applications**: Generic framework for various desktop apps
5. **Handling Complex Scenarios**: Support for multiple metrics, postconfig, and conjunctions

The separation of concerns (config, metrics, getters) makes it easy to:
- Add new evaluation metrics
- Support new applications
- Define complex evaluation scenarios
- Maintain and extend the system

