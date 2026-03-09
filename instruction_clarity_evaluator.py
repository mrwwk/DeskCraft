"""
Task Instruction Clarity Evaluation Pipeline

This module provides functionality to evaluate and improve task instructions
by identifying ambiguous expressions and providing clearer alternatives.
"""

import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class InstructionAnalysis:
    """Result of instruction analysis"""
    original_instruction: str
    clarity_score: float  # 0.0 to 1.0, higher is better
    ambiguity_issues: List[str]
    vagueness_issues: List[str]
    missing_information: List[str]
    improvement_suggestions: List[str]
    improved_instruction: str


class InstructionEvaluator:
    """Evaluates and improves task instructions using LLM"""

    def __init__(self, llm_url: str = "http://29.160.43.141:8000"):
        """
        Initialize the evaluator with LLM endpoint

        Args:
            llm_url: URL of the vLLM server
        """
        self.llm_url = llm_url
        self.api_endpoint = f"{llm_url}/v1/chat/completions"

    def _call_vllm_server(self, messages, model_name, max_tokens=50000, temperature=1.0):
        """
        调用远程 vLLM 服务器进行推理
        使用 /v1/chat/completions 接口
        """
        # 移除 host 中的 http:// 或 https:// 前缀
        #clean_host = host.replace("http://", "").replace("https://", "")
        url = self.api_endpoint
        
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.95,
            "chat_template_kwargs": {
                "thinking": True
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=1200)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                print(f"[Warning] Unexpected response format: {result}")
                return ""
        except requests.exceptions.RequestException as e:
            print(f"[Error] Request failed: {e}")
            return ""
        except json.JSONDecodeError as e:
            print(f"[Error] Failed to parse response: {e}")
            return ""

    def analyze_instruction(self, instruction: str, task_context: Optional[Dict] = None) -> InstructionAnalysis:
        """
        Analyze a task instruction for clarity and ambiguity

        Args:
            instruction: The task instruction to analyze
            task_context: Optional task context (config, evaluator, etc.)

        Returns:
            InstructionAnalysis object with analysis results
        """
        # Build context information
        context_info = self._build_context_info(task_context)

        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(instruction, context_info)

        # Call LLM for analysis
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": analysis_prompt}
        ]
        print("messages", messages)
        response = self._call_vllm_server(messages, model_name="KimiK25", max_tokens=2000, temperature=1.0)

        # Parse LLM response
        analysis = self._parse_analysis_response(response, instruction)

        return analysis

    def improve_instruction(self, instruction: str, analysis: InstructionAnalysis) -> str:
        """
        Generate an improved version of the instruction

        Args:
            instruction: Original instruction
            analysis: Analysis result from analyze_instruction

        Returns:
            Improved instruction string
        """
        # Build improvement prompt
        improvement_prompt = self._build_improvement_prompt(instruction, analysis)

        # Call LLM for improvement
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": improvement_prompt}
        ]

        response = self._call_vllm_server(messages, model_name="default", max_tokens=2000, temperature=0.5)

        # Extract improved instruction
        improved = self._extract_improved_instruction(response)

        return improved

    def evaluate_and_improve(self, task_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete pipeline: analyze and improve a task instruction

        Args:
            task_json: Complete task JSON object

        Returns:
            Dictionary with original instruction, analysis, and improved instruction
        """
        instruction = task_json.get("instruction", "")
        task_id = task_json.get("id", "unknown")

        print(f"\n{'='*60}")
        print(f"Evaluating Task: {task_id}")
        print(f"{'='*60}\n")

        print(f"Original Instruction:")
        print(f"  {instruction}\n")

        # Step 1: Analyze the instruction
        print("Step 1: Analyzing instruction for clarity and ambiguity...")
        analysis = self.analyze_instruction(instruction, task_json)

        print(f"\nClarity Score: {analysis.clarity_score:.2f}/1.0")
        if analysis.ambiguity_issues:
            print(f"\nAmbiguity Issues Found:")
            for issue in analysis.ambiguity_issues:
                print(f"  - {issue}")

        if analysis.vagueness_issues:
            print(f"\nVagueness Issues Found:")
            for issue in analysis.vagueness_issues:
                print(f"  - {issue}")

        if analysis.missing_information:
            print(f"\nMissing Information:")
            for info in analysis.missing_information:
                print(f"  - {info}")

        # Step 2: Generate improvement suggestions
        print("\nStep 2: Generating improvement suggestions...")
        if analysis.improvement_suggestions:
            print("\nImprovement Suggestions:")
            for suggestion in analysis.improvement_suggestions:
                print(f"  - {suggestion}")

        # Step 3: Generate improved instruction
        print("\nStep 3: Generating improved instruction...")
        improved_instruction = self.improve_instruction(instruction, analysis)

        print(f"\nImproved Instruction:")
        print(f"  {improved_instruction}\n")

        # Return complete result
        return {
            "task_id": task_id,
            "original_instruction": instruction,
            "clarity_score": analysis.clarity_score,
            "ambiguity_issues": analysis.ambiguity_issues,
            "vagueness_issues": analysis.vagueness_issues,
            "missing_information": analysis.missing_information,
            "improvement_suggestions": analysis.improvement_suggestions,
            "improved_instruction": improved_instruction
        }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM"""
        return """You are an expert task instruction analyst and writer. Your role is to:

1. Analyze task instructions for clarity, precision, and ambiguity
2. Identify vague expressions, ambiguous descriptions, and unclear objectives
3. Provide specific, actionable suggestions for improvement
4. Rewrite instructions to be more precise, unambiguous, and actionable

Focus on:
- Clear task objectives
- Specific parameters (if applicable: values, thresholds, file names, etc.)
- Unambiguous terminology
- Complete information for task execution
- Actionable and measurable goals

Output format: Always provide structured responses that can be easily parsed."""

    def _build_context_info(self, task_context: Optional[Dict]) -> str:
        """Build context information from task JSON"""
        if not task_context:
            return "No additional context provided."

        context_parts = []

        # Add related apps
        if "related_apps" in task_context:
            context_parts.append(f"Related Applications: {', '.join(task_context['related_apps'])}")

        # Add evaluator info
        if "evaluator" in task_context:
            evaluator = task_context["evaluator"]
            if "func" in evaluator:
                func = evaluator["func"]
                if isinstance(func, list):
                    func = ', '.join(func)
                context_parts.append(f"Evaluation Metric: {func}")

        # Add config info
        if "config" in task_context:
            config_types = [cfg.get("type", "") for cfg in task_context["config"]]
            context_parts.append(f"Setup Operations: {', '.join(config_types)}")

        return "\n".join(context_parts) if context_parts else "No additional context provided."

    def _build_analysis_prompt(self, instruction: str, context_info: str) -> str:
        """Build the prompt for instruction analysis"""
        return f"""Analyze the following task instruction for clarity and ambiguity:

Task Instruction:
"{instruction}"

Task Context:
{context_info}

Please analyze this instruction and provide a structured response in the following format:

CLARITY_SCORE: [0.0 to 1.0, where 1.0 is perfectly clear]

AMBIGUITY_ISSUES:
[List each ambiguity issue found, one per line]

VAGUENESS_ISSUES:
[List each vague expression found, one per line]

MISSING_INFORMATION:
[List any critical information missing for task execution, one per line]

IMPROVEMENT_SUGGESTIONS:
[List specific suggestions to improve the instruction, one per line]

Focus on identifying:
1. Ambiguous terms or phrases (e.g., "a bit", "some", "make it better")
2. Unclear objectives (what exactly should be achieved?)
3. Missing parameters (specific values, file names, thresholds)
4. Multiple interpretations (could the instruction be understood in different ways?)
5. Incomplete information (what else is needed to complete the task?)"""

    def _build_improvement_prompt(self, instruction: str, analysis: InstructionAnalysis) -> str:
        """Build the prompt for instruction improvement"""
        prompt = f"""Original Instruction:
"{instruction}"

Analysis Results:
- Clarity Score: {analysis.clarity_score:.2f}/1.0
"""

        if analysis.ambiguity_issues:
            prompt += f"\nAmbiguity Issues:\n" + "\n".join([f"- {issue}" for issue in analysis.ambiguity_issues])

        if analysis.vagueness_issues:
            prompt += f"\nVagueness Issues:\n" + "\n".join([f"- {issue}" for issue in analysis.vagueness_issues])

        if analysis.missing_information:
            prompt += f"\nMissing Information:\n" + "\n".join([f"- {info}" for info in analysis.missing_information])

        prompt += f"""

Based on the analysis above, rewrite the instruction to be:
1. More precise and specific
2. Unambiguous with clear objectives
3. Complete with all necessary information
4. Actionable and measurable

Please provide ONLY the improved instruction, without any additional explanation or commentary.

IMPROVED_INSTRUCTION:"""

        return prompt

    def _parse_analysis_response(self, response: str, original_instruction: str) -> InstructionAnalysis:
        """Parse the LLM analysis response"""
        # Initialize with defaults
        analysis = InstructionAnalysis(
            original_instruction=original_instruction,
            clarity_score=0.5,
            ambiguity_issues=[],
            vagueness_issues=[],
            missing_information=[],
            improvement_suggestions=[],
            improved_instruction=""
        )

        # Parse the structured response
        lines = response.strip().split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("CLARITY_SCORE:"):
                try:
                    score_str = line.split(":", 1)[1].strip()
                    analysis.clarity_score = float(score_str)
                except:
                    pass

            elif line.startswith("AMBIGUITY_ISSUES:"):
                current_section = "ambiguity"
            elif line.startswith("VAGUENESS_ISSUES:"):
                current_section = "vagueness"
            elif line.startswith("MISSING_INFORMATION:"):
                current_section = "missing"
            elif line.startswith("IMPROVEMENT_SUGGESTIONS:"):
                current_section = "suggestions"
            elif line.startswith("-") and current_section:
                item = line[1:].strip()
                if item:
                    if current_section == "ambiguity":
                        analysis.ambiguity_issues.append(item)
                    elif current_section == "vagueness":
                        analysis.vagueness_issues.append(item)
                    elif current_section == "missing":
                        analysis.missing_information.append(item)
                    elif current_section == "suggestions":
                        analysis.improvement_suggestions.append(item)

        return analysis

    def _extract_improved_instruction(self, response: str) -> str:
        """Extract the improved instruction from LLM response"""
        # Look for IMPROVED_INSTRUCTION: marker
        if "IMPROVED_INSTRUCTION:" in response:
            instruction = response.split("IMPROVED_INSTRUCTION:", 1)[1].strip()
            # Remove quotes if present
            if instruction.startswith('"') and instruction.endswith('"'):
                instruction = instruction[1:-1]
            return instruction

        # If no marker, take the last non-empty line
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            return lines[-1]

        return ""


def batch_evaluate_gimp_tasks(task_dir: str, output_file: str, llm_url: str = "http://29.160.43.141:8000"):
    """
    Batch evaluate all GIMP task instructions

    Args:
        task_dir: Directory containing task JSON files
        output_file: Path to save evaluation results
        llm_url: URL of the vLLM server
    """
    import os
    import glob

    evaluator = InstructionEvaluator(llm_url)

    # Find all task JSON files
    task_files = glob.glob(os.path.join(task_dir, "*.json"))

    print(f"Found {len(task_files)} task files to evaluate\n")

    # Evaluate each task
    results = []
    for task_file in sorted(task_files):
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task_json = json.load(f)

            result = evaluator.evaluate_and_improve(task_json)
            results.append(result)

        except Exception as e:
            print(f"Error processing {task_file}: {e}")
            continue

    # Save results to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Evaluation complete! Results saved to: {output_file}")
    print(f"{'='*60}\n")

    # Print summary statistics
    if results:
        avg_clarity = sum(r["clarity_score"] for r in results) / len(results)
        total_ambiguities = sum(len(r["ambiguity_issues"]) for r in results)
        total_vagueness = sum(len(r["vagueness_issues"]) for r in results)
        total_missing = sum(len(r["missing_information"]) for r in results)

        print(f"Summary Statistics:")
        print(f"  Total Tasks Evaluated: {len(results)}")
        print(f"  Average Clarity Score: {avg_clarity:.2f}/1.0")
        print(f"  Total Ambiguity Issues: {total_ambiguities}")
        print(f"  Total Vagueness Issues: {total_vagueness}")
        print(f"  Total Missing Information: {total_missing}")


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate and improve task instructions for clarity"
    )
    parser.add_argument(
        "--task-dir",
        type=str,
        default="evaluation_examples/examples/gimp",
        help="Directory containing task JSON files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="instruction_evaluation_results.json",
        help="Output file for evaluation results"
    )
    parser.add_argument(
        "--llm-url",
        type=str,
        default="http://29.160.43.141:8000",
        help="URL of the vLLM server"
    )
    parser.add_argument(
        "--single-task",
        type=str,
        default="/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/examples/gimp/2a729ded-3296-423d-aec4-7dd55ed5fbb3.json",
        help="Evaluate a single task JSON file"
    )

    args = parser.parse_args()

    evaluator = InstructionEvaluator(args.llm_url)

    if args.single_task:
        # Evaluate single task
        with open(args.single_task, 'r', encoding='utf-8') as f:
            task_json = json.load(f)

        result = evaluator.evaluate_and_improve(task_json)

        # Save single result
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\nResult saved to: {args.output}")
    else:
        # Batch evaluate all tasks
        batch_evaluate_gimp_tasks(args.task_dir, args.output, args.llm_url)


if __name__ == "__main__":
    main()
