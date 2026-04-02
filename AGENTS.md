# Repository Guidelines

## Project Structure & Module Organization
Core runtime code lives in `desktop_env/` (environment control, providers, evaluators) and `mm_agents/` (agent implementations and model adapters). Benchmark/task data is under `evaluation_examples/` and helper task tooling is in `task_gen/` and `optimized_gimp_commands/`. Top-level runner scripts (`run.py`, `run_multienv.py`, `run_multienv_*.py`, `quickstart*.py`) are the main entry points. Generated outputs belong in `results/` and `logs/`; monitoring UI assets are in `monitor/`.

## Build, Test, and Development Commands
Install dependencies first:

```bash
pip install -r requirements.txt
```

Run a sanity check environment launch:

```bash
python quickstart.py
```

Run benchmark jobs (single process or parallel):

```bash
python run.py --provider_name vmware --model gpt-4o
python run_multienv.py --provider_name docker --num_envs 4 --model gpt-4o
```

Summarize results:

```bash
python show_result.py
```

Targeted regression scripts currently in repo:

```bash
python test_instruction_clarity.py
python test_l2_evaluators.py
```

## Coding Style & Naming Conventions
Use Python with 4-space indentation and PEP 8-friendly naming: `snake_case` for functions/files, `PascalCase` for classes, uppercase constants. Keep new run entry points in the existing pattern (`run_<feature>.py` or `run_multienv_<agent>.py`). Place provider-specific logic under `desktop_env/providers/<provider>/` and evaluator logic under `desktop_env/evaluators/metrics/`. If formatting is needed, use `black` before submitting.

## Testing Guidelines
This repo uses script-style tests and task-level checks instead of a single enforced test harness. Add or update `test_*.py` scripts for changed behavior, keep assertions deterministic, and clean temporary files/resources in tests. For evaluator or task changes, validate against representative JSON tasks from `evaluation_examples/examples/<domain>/`.

## Commit & Pull Request Guidelines
Recent history mixes plain messages with Conventional Commit prefixes; prefer clear, imperative commits such as `feat: add aws evaluator retry` or `fix: handle missing vm snapshot`. Keep each commit focused on one change area. In PRs, include: objective, exact run/test commands, impacted domains/providers, and sample output paths (or screenshots when UI/task behavior changes). Link related issues or task IDs when available.

## Security & Configuration Tips
Do not commit secrets (`OPENAI_API_KEY`, cloud credentials, proxy tokens, `.env` values). Keep machine-specific VM paths and large artifacts (`logs/`, `results/`, tar files) out of commits unless explicitly required.
