# Instruction Clarity Evaluation Pipeline

This pipeline evaluates task instructions for clarity, ambiguity, and completeness, then provides improved versions with specific suggestions.

## Overview

The pipeline analyzes task instructions by:

1. **Identifying Ambiguity**: Detects terms or phrases that could be interpreted in multiple ways
2. **Detecting Vagueness**: Finds unclear expressions like "make it better", "a bit", "some"
3. **Finding Missing Information**: Identifies critical information needed for task execution
4. **Generating Suggestions**: Provides specific, actionable improvement recommendations
5. **Rewriting Instructions**: Creates clearer, more precise versions of instructions

## Installation

No additional installation required beyond Python 3.7+ and standard libraries:
- `requests`: For LLM API calls
- `json`: For task file parsing
- Standard library modules

## Usage

### Basic Usage

Evaluate a single task:

```bash
python instruction_clarity_evaluator.py \
    --single-task evaluation_examples/examples/gimp/2a729ded-3296-423d-aec4-7dd55ed5fbb3.json \
    --output evaluation_result.json
```

Batch evaluate all GIMP tasks:

```bash
python instruction_clarity_evaluator.py \
    --task-dir evaluation_examples/examples/gimp \
    --output gimp_instruction_evaluation.json
```

### Command-Line Arguments

- `--task-dir`: Directory containing task JSON files (default: `evaluation_examples/examples/gimp`)
- `--output`: Output file for evaluation results (default: `instruction_evaluation_results.json`)
- `--llm-url`: URL of the vLLM server (default: `http://29.160.43.141:8000`)
- `--single-task`: Path to a single task JSON file to evaluate

## Output Format

### Single Task Evaluation

When evaluating a single task, the output JSON contains:

```json
{
  "task_id": "2a729ded-3296-423d-aec4-7dd55ed5fbb3",
  "original_instruction": "Could you make background of this image transparent for me?",
  "clarity_score": 0.65,
  "ambiguity_issues": [
    "What specific background area should be transparent?",
    "Should all background be removed or just part of it?"
  ],
  "vagueness_issues": [
    "\"this image\" is vague - which image?",
    "No specification of transparency level or method"
  ],
  "missing_information": [
    "Output file name or location",
    "Specific transparency method (e.g., color key, alpha channel)"
  ],
  "improvement_suggestions": [
    "Specify the exact image file to process",
    "Define the background area to remove",
    "Specify output file name and format",
    "Indicate desired transparency method"
  ],
  "improved_instruction": "Open the image '/home/user/Desktop/dog_with_background.png' in GIMP, remove the background around the dog, and save the result as '/home/user/Desktop/dog_without_background.png' with a transparent background."
}
```

### Batch Evaluation

When evaluating multiple tasks, the output is a JSON array:

```json
[
  {
    "task_id": "...",
    "original_instruction": "...",
    "clarity_score": 0.75,
    ...
  },
  {
    "task_id": "...",
    ...
  }
]
```

### Console Output

The pipeline provides detailed console output during execution:

```
============================================================
Evaluating Task: 2a729ded-3296-423d-aec4-7dd55ed5fbb3
============================================================

Original Instruction:
  Could you make background of this image transparent for me?

Step 1: Analyzing instruction for clarity and ambiguity...

Clarity Score: 0.65/1.0

Ambiguity Issues Found:
  - What specific background area should be transparent?
  - Should all background be removed or just part of it?

Vagueness Issues Found:
  - "this image" is vague - which image?
  - No specification of transparency level or method

Missing Information:
  - Output file name or location
  - Specific transparency method (e.g., color key, alpha channel)

Step 2: Generating improvement suggestions...

Improvement Suggestions:
  - Specify the exact image file to process
  - Define the background area to remove
  - Specify output file name and format
  - Indicate desired transparency method

Step 3: Generating improved instruction...

Improved Instruction:
  Open the image '/home/user/Desktop/dog_with_background.png' in GIMP, remove the background around the dog, and save the result as '/home/user/Desktop/dog_without_background.png' with a transparent background.

============================================================
```

## Pipeline Architecture

### Components

#### 1. InstructionEvaluator Class

Main class that orchestrates the evaluation process:

- **`__init__(llm_url)`**: Initialize with LLM endpoint
- **`analyze_instruction(instruction, task_context)`**: Analyze instruction for clarity
- **`improve_instruction(instruction, analysis)`**: Generate improved instruction
- **`evaluate_and_improve(task_json)`**: Complete pipeline for a task

#### 2. InstructionAnalysis Dataclass

Stores analysis results:

```python
@dataclass
class InstructionAnalysis:
    original_instruction: str
    clarity_score: float  # 0.0 to 1.0
    ambiguity_issues: List[str]
    vagueness_issues: List[str]
    missing_information: List[str]
    improvement_suggestions: List[str]
    improved_instruction: str
```

### Evaluation Process

```
Task JSON
    ↓
Extract Instruction & Context
    ↓
Call LLM for Analysis
    ↓
Parse Analysis Response
    ↓
Generate Improvement Suggestions
    ↓
Call LLM for Improvement
    ↓
Extract Improved Instruction
    ↓
Output Results
```

### LLM Prompts

The pipeline uses carefully engineered prompts:

#### Analysis Prompt

Focuses on:
- Ambiguous terms or phrases
- Unclear objectives
- Missing parameters
- Multiple interpretations
- Incomplete information

#### Improvement Prompt

Guides LLM to:
- Be more precise and specific
- Eliminate ambiguity
- Complete missing information
- Make instruction actionable

## Common Issues Identified

### Ambiguity Examples

1. **"Make it better"**
   - Issue: What does "better" mean?
   - Fix: Specify the improvement (e.g., "increase brightness by 20%")

2. **"Adjust the settings"**
   - Issue: Which settings? To what values?
   - Fix: List specific settings and target values

3. **"Some of the items"**
   - Issue: How many? Which ones?
   - Fix: Specify exact count or selection criteria

### Vagueness Examples

1. **"A little bit"**
   - Issue: Subjective and imprecise
   - Fix: Use specific values (e.g., "5 pixels", "10%")

2. **"Make it look nice"**
   - Issue: Subjective aesthetic judgment
   - Fix: Define specific visual criteria

3. **"The right size"**
   - Issue: What is "right"?
   - Fix: Specify exact dimensions or constraints

### Missing Information Examples

1. **No output location**
   - Issue: Where should the result be saved?
   - Fix: Specify file path or location

2. **No file format**
   - Issue: What format should be used?
   - Fix: Specify format (e.g., PNG, JPEG)

3. **No parameter values**
   - Issue: What values should be used?
   - Fix: Provide specific numbers or settings

## Integration with OSWorld

This pipeline can be integrated with OSWorld's task evaluation system:

### Option 1: Pre-Evaluation

Run instruction clarity evaluation before task execution:

```python
from instruction_clarity_evaluator import InstructionEvaluator

# Load task
with open("task.json", "r") as f:
    task_json = json.load(f)

# Evaluate instruction
evaluator = InstructionEvaluator("http://29.160.43.141:8000")
result = evaluator.evaluate_and_improve(task_json)

# Use improved instruction for task
task_json["original_instruction"] = task_json["instruction"]
task_json["instruction"] = result["improved_instruction"]
task_json["clarity_analysis"] = {
    "score": result["clarity_score"],
    "issues": result["ambiguity_issues"] + result["vagueness_issues"]
}
```

### Option 2: Batch Processing

Evaluate all tasks before running experiments:

```python
import glob
import json
from instruction_clarity_evaluator import batch_evaluate_gimp_tasks

# Evaluate all GIMP tasks
batch_evaluate_gimp_tasks(
    "evaluation_examples/examples/gimp",
    "gimp_instruction_analysis.json",
    "http://29.160.43.141:8000"
)

# Load analysis results
with open("gimp_instruction_analysis.json", "r") as f:
    analyses = json.load(f)

# Filter tasks by clarity score
clear_tasks = [a for a in analyses if a["clarity_score"] >= 0.8]
print(f"Clear tasks: {len(clear_tasks)}/{len(analyses)}")
```

## Example Results

### Example 1: Background Removal

**Original**: "Could you make background of this image transparent for me?"

**Issues**:
- Ambiguity: Which background area?
- Vagueness: "this image" is not specific
- Missing: Output file name

**Improved**: "Open the image '/home/user/Desktop/dog_with_background.png' in GIMP, use the Fuzzy Select tool to select the background area around the dog, press Delete to remove it, and save the result as '/home/user/Desktop/dog_without_background.png' with a transparent background."

### Example 2: Brightness Adjustment

**Original**: "Could you tone down the brightness of my photo?"

**Issues**:
- Vagueness: "tone down" is subjective
- Missing: How much to reduce?

**Improved**: "Open the image '/home/user/Desktop/woman_sitting_by_the_tree.png' in GIMP, reduce the brightness by 30% using the Brightness-Contrast tool, and save the result as '/home/user/Desktop/edited_darker.png'."

### Example 3: Saturation Enhancement

**Original**: "Could you assist me in enhancing the color vibrancy of my photo?"

**Issues**:
- Vagueness: "enhancing color vibrancy" is not specific
- Missing: Target saturation level?

**Improved**: "Open the image '/home/user/Desktop/woman_sitting_by_the_tree2.png' in GIMP, increase the saturation by 25% using the Hue-Saturation tool, and save the result as '/home/user/Desktop/edited_colorful.png'."

## Troubleshooting

### LLM Connection Issues

If you encounter connection errors:

```bash
# Check if LLM server is running
curl http://29.160.43.141:8000/v1/models

# Test connection
python -c "import requests; print(requests.get('http://29.160.43.141:8000/v1/models').status_code)"
```

### Timeout Issues

If LLM calls timeout, adjust the timeout in `_call_llm()`:

```python
response = requests.post(
    self.api_endpoint,
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=120  # Increase from 60 to 120 seconds
)
```

### Parsing Errors

If response parsing fails, check the LLM output format:

```python
# Add debug output
print(f"LLM Response:\n{response}\n")
```

## Extending the Pipeline

### Adding New Analysis Criteria

Modify `_build_analysis_prompt()` to add new analysis dimensions:

```python
def _build_analysis_prompt(self, instruction: str, context_info: str) -> str:
    return f"""Analyze the following task instruction:

Task Instruction:
"{instruction}"

Task Context:
{context_info}

Please analyze and provide:

CLARITY_SCORE: [0.0 to 1.0]

AMBIGUITY_ISSUES:
[List]

VAGUENESS_ISSUES:
[List]

MISSING_INFORMATION:
[List]

NEW_CRITERION:
[List items for new criterion]

IMPROVEMENT_SUGGESTIONS:
[List]"""
```

### Adding Custom Metrics

Extend `InstructionAnalysis` dataclass:

```python
@dataclass
class InstructionAnalysis:
    # ... existing fields ...
    new_metric: float
    new_issues: List[str]
```

## Best Practices

1. **Provide Context**: Always include task context (config, evaluator) for better analysis
2. **Use Appropriate Temperature**: Lower temperature (0.3) for analysis, higher (0.5) for generation
3. **Validate Output**: Check that improved instructions are actionable and complete
4. **Iterate**: Run multiple rounds of improvement if needed
5. **Track Metrics**: Monitor clarity scores over time to measure improvement

## References

- [Task JSON Loading and Evaluation Pipeline](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/Task_JSON_Loading_and_Evaluation_Pipeline.md)
- [GIMP Evaluation Functions Documentation](file:///apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/GIMP评估函数文档.md)
