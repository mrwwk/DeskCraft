# OSWorld Project Context

## Project Overview

**OSWorld** is a benchmarking framework for evaluating multimodal agents in real desktop computer environments. It provides a comprehensive infrastructure for testing AI agents' ability to perform open-ended tasks on actual operating systems (Ubuntu, Windows) through virtual machines.

### Core Purpose
- Evaluate computer-use AI agents on real desktop environments
- Benchmark multimodal models' ability to interact with GUI applications
- Provide standardized tasks across multiple domains (GIMP, LibreOffice, Chrome, VSCode, etc.)
- Support both single-environment and parallel multi-environment evaluation

### Key Components

1. **Desktop Environment (`desktop_env/`)**
   - Gymnasium-based environment interface
   - Multiple provider backends: VMware, VirtualBox, Docker, AWS, Azure
   - Screenshot and accessibility tree observations
   - pyautogui and computer_13 action spaces

2. **Multimodal Agents (`mm_agents/`)**
   - Prompt-based agent framework
   - Support for GPT-4V, Claude, Gemini, Qwen-VL, and open-source models
   - Multiple observation types: screenshot, a11y_tree, screenshot_a11y_tree, som

3. **Evaluation Examples (`evaluation_examples/`)**
   - Task definitions in JSON format
   - Pre-configured snapshots for reproducible initial states
   - Automated evaluation scripts for task success measurement

4. **Instruction Clarity Pipeline**
   - LLM-based instruction quality evaluation
   - Ambiguity and vagueness detection
   - Automatic instruction improvement suggestions

## Project Structure

```
OSWorld/
├── desktop_env/              # Core environment implementation
│   ├── providers/            # VM providers (vmware, docker, aws, etc.)
│   ├── controllers/          # VM control interfaces
│   ├── evaluators/           # Task evaluation scripts
│   └── server/               # In-VM server for interaction
├── mm_agents/                # Agent implementations
│   ├── agent.py              # Main PromptAgent class
│   ├── prompts.py            # System prompts for different configurations
│   └── accessibility_tree_wrap/  # A11y tree processing
├── evaluation_examples/      # Benchmark tasks
│   ├── examples/             # Task JSON files by domain
│   ├── settings/             # Account credentials, proxy configs
│   └── test_all.json         # Full task list
├── results/                  # Evaluation outputs (screenshots, trajectories)
├── logs/                     # Runtime logs
├── run.py                    # Single-environment evaluation
├── run_multienv.py           # Parallel multi-environment evaluation
├── run_multienv_*.py         # Model-specific evaluation scripts
├── main.py                   # Human-agent interaction demo
├── quickstart.py             # Minimal example to get started
├── config.json               # TaiJi platform configuration
├── requirements.txt          # Python dependencies
└── pyproject.toml            # UV package manager config
```

## Building and Running

### Prerequisites

1. **Python 3.10+** (3.12 recommended)
2. **Virtualization Platform** (choose one):
   - VMware Workstation Pro (Linux/Windows) or Fusion (macOS)
   - Docker with KVM support (Linux only)
   - VirtualBox (limited support)
   - AWS/Azure cloud instances

3. **Environment Variables**:
   ```bash
   export OPENAI_API_KEY='your-api-key'
   export OPENAI_BASE_URL='https://api.openai.com'  # Optional: custom endpoint
   ```

### Installation

```bash
# Clone repository
git clone https://github.com/xlang-ai/OSWorld
cd OSWorld

# Create conda environment (recommended)
conda create -n osworld python=3.10
conda activate osworld

# Install dependencies
pip install -r requirements.txt

# Alternative: install without benchmark tasks
pip install desktop-env
```

### Quick Start

```bash
# Run minimal example with default settings
python quickstart.py

# Customize provider and VM path
python quickstart.py --provider_name vmware --path_to_vm "path/to/your/vm.vmx"
```

### Running Evaluations

#### Single Environment (Deprecated but still functional)
```bash
python run.py \
    --provider_name vmware \
    --path_to_vm Ubuntu/Ubuntu.vmx \
    --headless \
    --observation_type screenshot \
    --model gpt-4o \
    --sleep_after_execution 3 \
    --max_steps 15 \
    --result_dir ./results \
    --client_password password
```

#### Parallel Multi-Environment (Recommended)
```bash
python run_multienv.py \
    --provider_name docker \
    --headless \
    --observation_type screenshot \
    --model gpt-4o \
    --sleep_after_execution 3 \
    --max_steps 15 \
    --num_envs 10 \
    --client_password password
```

#### Model-Specific Scripts
The project includes pre-configured scripts for various models:
- `run_multienv_gpt4o.py` - GPT-4o
- `run_multienv_claude.py` - Claude
- `run_multienv_qwen3vl.py` - Qwen-VL
- `run_multienv_uitars.py` - UI-TARS
- `run_multienv_mobileagent_v3.py` - MobileAgent V3
- And many more...

### Viewing Results

```bash
# Show aggregated results
python show_result.py

# Results are stored in: ./results/{action_space}/{observation_type}/{model}/{domain}/{task_id}/
# Each task directory contains:
#   - traj.jsonl      : Step-by-step trajectory
#   - recording.mp4   : Screen recording
#   - step_*.png      : Screenshots per step
#   - result.txt      : Final score
```

## Development Conventions

### Code Style
- **Type Hints**: Use Python type hints for function signatures
- **Logging**: Use structured logging with `logging.getLogger("desktopenv.<module>")`
- **Error Handling**: Wrap environment interactions in try-except blocks
- **Documentation**: Docstrings for classes and public methods

### Testing Practices
- Test new agents with `quickstart.py` first
- Use `run_multienv.py` with small `num_envs` for debugging
- Verify evaluation scripts locally before batch runs
- Check `logs/` directory for detailed runtime logs

### Task JSON Format
```json
{
  "id": "unique-task-id",
  "snapshot": "snapshot_name",
  "instruction": "Natural language task description",
  "source": "URL or reference",
  "config": [
    {"type": "download", "parameters": {...}},
    {"type": "launch", "parameters": {"command": ["app", "args"]}}
  ],
  "related_apps": ["app1", "app2"],
  "evaluator": {
    "func": "evaluation_function_name",
    "expected": {...},
    "result": {...}
  }
}
```

### Agent Interface
To implement a custom agent:

```python
from mm_agents.agent import PromptAgent

class CustomAgent(PromptAgent):
    def __init__(self, model, observation_type, **kwargs):
        super().__init__(model, observation_type, **kwargs)
    
    def reset(self, logger=None, vm_ip=None):
        # Initialize fresh state
        pass
    
    def predict(self, instruction, obs):
        """
        Args:
            instruction: Task instruction string
            obs: Dict with observation keys (e.g., 'screenshot', 'a11y_tree')
        
        Returns:
            response: Dict with model response metadata
            actions: List of action strings (pyautogui code or computer_13 actions)
        """
        # Implement prediction logic
        return response, actions
```

### Environment Interface
```python
from desktop_env.desktop_env import DesktopEnv

env = DesktopEnv(
    provider_name="vmware",      # or "docker", "aws", etc.
    path_to_vm="path/to/vm.vmx",
    action_space="pyautogui",    # or "computer_13"
    observation_type="screenshot",
    headless=True,
    os_type="Ubuntu",            # or "Windows"
)

# Reset environment with task
obs = env.reset(task_config=task_json)

# Step through environment
obs, reward, done, info = env.step(action)

# Evaluate task completion
result = env.evaluate()

# Cleanup
env.close()
```

## Configuration Guidelines

### VM Credentials
- **Ubuntu (vmware, docker, virtualbox)**: `user` / `password`
- **Cloud providers (aws, azure)**: `osworld-public-evaluation` / `osworld-public-evaluation`

### Proxy Configuration
Some tasks require proxy settings to avoid bot detection:
```bash
# See PROXY_GUIDELINE.md for detailed setup
# Or use pre-configured dataimpulse proxy
cp evaluation_examples/settings/proxy/dataimpulse.json.example \
   evaluation_examples/settings/proxy/dataimpulse.json
```

### Google Account Tasks
Tasks requiring Google services need OAuth2.0 configuration:
```bash
# See ACCOUNT_GUIDELINE.md for setup
# Place credentials in:
#   evaluation_examples/settings/google/settings.json
#   evaluation_examples/settings/googledrive/credentials.json
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `desktop_env/desktop_env.py` | Main environment class |
| `mm_agents/agent.py` | PromptAgent implementation |
| `mm_agents/prompts.py` | System prompts for different obs/action types |
| `lib_run_single.py` | Single environment execution logic |
| `run_multienv.py` | Parallel evaluation orchestrator |
| `instruction_clarity_evaluator.py` | LLM-based instruction quality evaluation |
| `evaluation_examples/test_all.json` | Complete task list by domain |

## Common Workflows

### Adding a New Agent
1. Create agent class in `mm_agents/` extending `PromptAgent`
2. Implement `reset()` and `predict()` methods
3. Create evaluation script (e.g., `run_multienv_myagent.py`)
4. Test with `quickstart.py` or small task subset

### Adding New Tasks
1. Create task JSON in `evaluation_examples/examples/{domain}/`
2. Define initial state in `config` section
3. Implement evaluator function in `desktop_env/evaluators/`
4. Add task ID to `test_all.json`

### Debugging Failed Tasks
1. Check `logs/normal-*.log` for high-level errors
2. Check `logs/debug-*.log` for detailed traces
3. Review `traj.jsonl` for action sequence
4. Watch `recording.mp4` for visual inspection
5. Check VM state directly if needed

## Troubleshooting

### Common Issues

**Connection Refused to VM**
```bash
# Check VM is running
vmrun -T ws list  # For VMware
docker ps         # For Docker

# Verify VM IP address
ping <vm_ip>
```

**Action Execution Timeout**
```python
# Increase timeout in env.step()
obs, reward, done, info = env.step(action, sleep_after_execution=5.0)
```

**Out of Memory (Parallel Runs)**
```bash
# Reduce number of parallel environments
python run_multienv.py --num_envs 5  # Instead of 10 or 20
```

**API Rate Limiting**
```python
# Add backoff/retry logic in agent.predict()
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException)
def predict(self, instruction, obs):
    ...
```

## Related Documentation

- [README.md](README.md) - Main project documentation
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - Instruction clarity pipeline quickstart
- [INSTRUCTION_CLARITY_PIPELINE_README.md](INSTRUCTION_CLARITY_PIPELINE_README.md) - Full instruction evaluation docs
- [ACCOUNT_GUIDELINE.md](ACCOUNT_GUIDELINE.md) - Google account setup
- [PROXY_GUIDELINE.md](PROXY_GUIDELINE.md) - Proxy configuration
- [PUBLIC_EVALUATION_GUIDELINE.md](PUBLIC_EVALUATION_GUIDELINE.md) - Public evaluation submission
- [GIMP 评估函数文档.md](GIMP 评估函数文档.md) - GIMP evaluation functions (Chinese)

## External Resources

- **Website**: https://os-world.github.io/
- **Paper**: https://arxiv.org/abs/2404.07972
- **HuggingFace Dataset**: https://huggingface.co/datasets/xlangai/assets
- **Discord**: https://discord.gg/4Gnw7eTEZR
- **VM Cache**: https://drive.google.com/file/d/1XlEy49otYDyBlA3O9NbR0BpPfr2TXgaD/view
