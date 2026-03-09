# Quick Start Guide: Instruction Clarity Evaluation Pipeline

This guide helps you quickly get started with evaluating and improving task instructions.

## Prerequisites

1. **LLM Server Running**: Ensure your vLLM server is running at `http://29.160.43.141:8000`

2. **Python 3.7+**: Required for running the pipeline

3. **Task JSON Files**: Have access to task JSON files from `evaluation_examples/examples/gimp/`

## Quick Start (5 Minutes)

### Step 1: Test Connection (1 minute)

```bash
# Check if LLM server is accessible
curl http://29.160.43.141:8000/v1/models

# Expected output: JSON with available models
```

### Step 2: Run Test Script (2 minutes)

```bash
# Navigate to OSWorld directory
cd /apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld

# Run test script
python test_instruction_clarity.py
```

The test script will:
- Evaluate a sample instruction
- Compare multiple instructions
- Optionally evaluate a real GIMP task

### Step 3: Evaluate Single Task (1 minute)

```bash
# Evaluate a specific GIMP task
python instruction_clarity_evaluator.py \
    --single-task evaluation_examples/examples/gimp/2a729ded-3296-423d-aec4-7dd55ed5fbb3.json \
    --output single_result.json
```

### Step 4: Batch Evaluate All Tasks (1 minute)

```bash
# Evaluate all GIMP tasks
python instruction_clarity_evaluator.py \
    --task-dir evaluation_examples/examples/gimp \
    --output gimp_evaluation_results.json
```

## Understanding the Output

### Clarity Score

- **1.0**: Perfectly clear, no ambiguity
- **0.8-0.9**: Clear with minor issues
- **0.5-0.7**: Moderate clarity, some ambiguity
- **0.3-0.4**: Significant ambiguity
- **0.0-0.2**: Very unclear or ambiguous

### Issue Categories

1. **Ambiguity**: Can be interpreted in multiple ways
   - Example: "Make it better" (better in what way?)
   - Fix: Specify the exact improvement

2. **Vagueness**: Subjective or imprecise terms
   - Example: "A little bit" (how much?)
   - Fix: Use specific values

3. **Missing Information**: Critical details absent
   - Example: No output file specified
   - Fix: Add file path or name

## Common Use Cases

### Use Case 1: Improve Existing Tasks

Before deploying tasks for evaluation, improve their clarity:

```python
import json
from instruction_clarity_evaluator import InstructionEvaluator

# Load task
with open("task.json", "r") as f:
    task = json.load(f)

# Evaluate and improve
evaluator = InstructionEvaluator("http://29.160.43.141:8000")
result = evaluator.evaluate_and_improve(task)

# Update task with improved instruction
task["original_instruction"] = task["instruction"]
task["instruction"] = result["improved_instruction"]
task["clarity_score"] = result["clarity_score"]

# Save improved task
with open("task_improved.json", "w") as f:
    json.dump(task, f, indent=2)
```

### Use Case 2: Filter Tasks by Quality

Select only high-quality tasks for experiments:

```python
import json

# Load evaluation results
with open("gimp_evaluation_results.json", "r") as f:
    results = json.load(f)

# Filter by clarity score
high_quality = [r for r in results if r["clarity_score"] >= 0.8]
medium_quality = [r for r in results if 0.5 <= r["clarity_score"] < 0.8]
low_quality = [r for r in results if r["clarity_score"] < 0.5]

print(f"High Quality: {len(high_quality)}")
print(f"Medium Quality: {len(medium_quality)}")
print(f"Low Quality: {len(low_quality)}")

# Use only high-quality tasks
selected_task_ids = [r["task_id"] for r in high_quality]
```

### Use Case 3: Analyze Task Quality Trends

Track instruction quality over time:

```python
import json
import matplotlib.pyplot as plt

# Load results
with open("gimp_evaluation_results.json", "r") as f:
    results = json.load(f)

# Extract clarity scores
scores = [r["clarity_score"] for r in results]
task_ids = [r["task_id"] for r in results]

# Plot distribution
plt.hist(scores, bins=10, edgecolor='black')
plt.xlabel('Clarity Score')
plt.ylabel('Number of Tasks')
plt.title('Distribution of Instruction Clarity Scores')
plt.savefig('clarity_distribution.png')

# Calculate statistics
avg_score = sum(scores) / len(scores)
print(f"Average Clarity Score: {avg_score:.2f}")
print(f"Minimum: {min(scores):.2f}")
print(f"Maximum: {max(scores):.2f}")
```

## Integration with OSWorld

### Option 1: Pre-Evaluation Pipeline

Add instruction evaluation to your experiment pipeline:

```python
# In your experiment script
from instruction_clarity_evaluator import InstructionEvaluator

def load_and_evaluate_tasks(task_dir):
    """Load tasks and evaluate instruction clarity"""
    evaluator = InstructionEvaluator("http://29.160.43.141:8000")

    tasks = []
    for task_file in glob.glob(f"{task_dir}/*.json"):
        with open(task_file, "r") as f:
            task = json.load(f)

        # Evaluate instruction
        result = evaluator.evaluate_and_improve(task)

        # Store both original and improved
        task["instruction_analysis"] = {
            "original": task["instruction"],
            "improved": result["improved_instruction"],
            "clarity_score": result["clarity_score"],
            "issues": result["ambiguity_issues"] + result["vagueness_issues"]
        }

        tasks.append(task)

    return tasks

# Use in your experiment
tasks = load_and_evaluate_tasks("evaluation_examples/examples/gimp")
```

### Option 2: Quality-Based Task Selection

Select tasks based on clarity thresholds:

```python
def select_tasks_by_quality(tasks, min_clarity=0.7):
    """Select tasks with minimum clarity score"""
    return [
        task for task in tasks
        if task.get("instruction_analysis", {}).get("clarity_score", 0) >= min_clarity
    ]

# Use only clear tasks
clear_tasks = select_tasks_by_quality(tasks, min_clarity=0.7)
print(f"Selected {len(clear_tasks)}/{len(tasks)} clear tasks")
```

## Troubleshooting

### Issue: Connection Refused

**Problem**: `requests.exceptions.ConnectionError`

**Solution**:
```bash
# Check if server is running
ps aux | grep vllm

# Start server if not running
# (Use your vLLM startup command)
```

### Issue: Timeout

**Problem**: LLM calls timeout after 60 seconds

**Solution**: Edit `instruction_clarity_evaluator.py`:
```python
# In _call_llm method, increase timeout
response = requests.post(
    self.api_endpoint,
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=120  # Increase from 60 to 120
)
```

### Issue: Poor Quality Improvements

**Problem**: Improved instructions are not better

**Solution**: Adjust prompts in `_build_analysis_prompt()` and `_build_improvement_prompt()`:
- Add more specific criteria
- Provide examples of good vs. bad instructions
- Adjust temperature parameter (lower = more conservative, higher = more creative)

## Next Steps

1. **Run Full Evaluation**: Evaluate all GIMP tasks
2. **Analyze Results**: Review clarity scores and common issues
3. **Improve Tasks**: Update task JSONs with improved instructions
4. **Validate**: Test improved instructions with actual agents
5. **Iterate**: Refine pipeline based on feedback

## Additional Resources

- [Full Documentation](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/INSTRUCTION_CLARITY_PIPELINE_README.md)
- [Task JSON Loading Pipeline](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/Task_JSON_Loading_and_Evaluation_Pipeline.md)
- [GIMP Evaluation Functions](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/GIMP评估函数文档.md)

## Support

For issues or questions:
1. Check the full documentation
2. Review test script output
3. Examine LLM responses for debugging
4. Adjust prompts as needed for your use case
