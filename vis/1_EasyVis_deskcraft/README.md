# EasyVis DeskCraft

Web UI for browsing DeskCraft task definitions and Kimi agent trajectories (standard + interactive tasks).

## Quick Start

```bash
cd vis_scripts/1_EasyVis_deskcraft
bash start_deskcraft_tmux.sh
# Open http://<your-ip>:8093
# tmux attach -t easyvis_deskcraft
```

Or run directly:

```bash
pip install flask requests
python3 app.py --port 8093 --host 0.0.0.0 --defaults profiles/kimi_replay_full.json
```

## Default Paths (kimi_replay_full)

| Field | Path |
|-------|------|
| Config | `DeskCraft/taiji_task/test_all_with_interactive.json` |
| Examples | `DeskCraft/evaluation_examples/examples_per_task` |
| Results | `DeskCraft/results/replay_full/kimi-replay-full/pyautogui/screenshot/Kimi-K2.6` |
| Cache | optional (leave empty for DeskCraft) |

## Task Types

- **Standard**: `L{1,2,3}_{app}_{uuid}` — single instruction, evaluator artifacts in result dir
- **Interactive**: `INTERACTIVE_{app}_interactive_{app}_{scenario}_{id}` — multi-phase with `interaction_log.json` and `phase` in trajectory

## Features

- Domain-grouped task sidebar with L1/L2/L3 and INT badges
- Trajectory player with action overlays, phase markers, model response
- Interaction log panel for interactive tasks
- Evaluator function labels + `evaluator_audit.json` from results
- Manual usable/unusable labeling (saved as `easyvis_label.json` in result dirs)

## Profiles

Create a new JSON under `profiles/` and pass `--defaults profiles/your_run.json`.

```json
{
  "title": "EasyVis DeskCraft - my_run",
  "config_path": "/abs/path/to/test_all_with_interactive.json",
  "examples_dir": "/abs/path/to/examples_per_task",
  "results_dir": "/abs/path/to/.../pyautogui/screenshot/Kimi-K2.6"
}
```
