#!/usr/bin/env python3
"""
Quick test script for instruction clarity evaluation pipeline

This script demonstrates how to use the instruction clarity evaluator
to analyze and improve GIMP task instructions.
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instruction_clarity_evaluator import InstructionEvaluator


def test_single_instruction():
    """Test with a single instruction"""
    print("\n" + "="*70)
    print("TEST 1: Single Instruction Evaluation")
    print("="*70 + "\n")

    # Create a sample task
    sample_task = {
        "id": "test-001",
        "snapshot": "gimp",
        "instruction": "Could you make background of this image transparent for me?",
        "config": [
            {
                "type": "download",
                "parameters": {
                    "files": [
                        {
                            "url": "https://example.com/image.png",
                            "path": "/home/user/Desktop/image.png"
                        }
                    ]
                }
            },
            {
                "type": "launch",
                "parameters": {
                    "command": ["gimp", "/home/user/Desktop/image.png"]
                }
            }
        ],
        "related_apps": ["gimp"],
        "evaluator": {
            "func": "check_structure_sim",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Desktop/output.png"
            },
            "expected": {
                "type": "cloud_file",
                "path": "https://example.com/expected.png"
            }
        }
    }

    # Initialize evaluator
    evaluator = InstructionEvaluator("http://29.160.43.141:8000")

    # Evaluate and improve
    result = evaluator.evaluate_and_improve(sample_task)

    # Print summary
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(f"Task ID: {result['task_id']}")
    print(f"Clarity Score: {result['clarity_score']:.2f}/1.0")
    print(f"Ambiguity Issues: {len(result['ambiguity_issues'])}")
    print(f"Vagueness Issues: {len(result['vagueness_issues'])}")
    print(f"Missing Information: {len(result['missing_information'])}")
    print(f"Improvement Suggestions: {len(result['improvement_suggestions'])}")

    return result


def test_multiple_instructions():
    """Test with multiple instructions"""
    print("\n" + "="*70)
    print("TEST 2: Multiple Instructions Comparison")
    print("="*70 + "\n")

    # Sample instructions with different clarity levels
    test_cases = [
        {
            "id": "test-002",
            "instruction": "Make the image better.",
            "description": "Very vague instruction"
        },
        {
            "id": "test-003",
            "instruction": "Increase the brightness of the photo by 30%.",
            "description": "Clear instruction with specific parameter"
        },
        {
            "id": "test-004",
            "instruction": "Could you adjust some settings in GIMP to improve the image quality?",
            "description": "Ambiguous instruction with vague terms"
        }
    ]

    evaluator = InstructionEvaluator("http://29.160.43.141:8000")

    results = []
    for test_case in test_cases:
        print(f"\n{'-'*70}")
        print(f"Testing: {test_case['description']}")
        print(f"{'-'*70}")
        print(f"Instruction: {test_case['instruction']}\n")

        # Create minimal task structure
        task = {
            "id": test_case['id'],
            "instruction": test_case['instruction'],
            "related_apps": ["gimp"],
            "config": [],
            "evaluator": {
                "func": "check_structure_sim",
                "result": {"type": "vm_file", "path": "/tmp/output.png"}
            }
        }

        # Evaluate
        result = evaluator.evaluate_and_improve(task)
        results.append(result)

    # Compare results
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print(f"{'ID':<15} {'Original':<40} {'Clarity':<10} {'Improved':<40}")
    print("-"*70)

    for result in results:
        original = result['original_instruction'][:37] + "..." if len(result['original_instruction']) > 37 else result['original_instruction']
        improved = result['improved_instruction'][:37] + "..." if len(result['improved_instruction']) > 37 else result['improved_instruction']
        print(f"{result['task_id']:<15} {original:<40} {result['clarity_score']:<10.2f} {improved:<40}")

    return results


def test_with_real_task():
    """Test with a real GIMP task from evaluation_examples"""
    print("\n" + "="*70)
    print("TEST 3: Real GIMP Task Evaluation")
    print("="*70 + "\n")

    # Path to real task file
    task_file = "evaluation_examples/examples/gimp/2a729ded-3296-423d-aec4-7dd55ed5fbb3.json"

    if not os.path.exists(task_file):
        print(f"Error: Task file not found: {task_file}")
        print("Please run this script from the OSWorld root directory.")
        return None

    # Load task
    with open(task_file, 'r', encoding='utf-8') as f:
        task_json = json.load(f)

    # Evaluate
    evaluator = InstructionEvaluator("http://29.160.43.141:8000")
    result = evaluator.evaluate_and_improve(task_json)

    # Save result
    output_file = "real_task_evaluation_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nResult saved to: {output_file}")

    return result


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("INSTRUCTION CLARITY EVALUATION PIPELINE - TEST SCRIPT")
    print("="*70)
    print("\nThis script demonstrates the instruction clarity evaluation pipeline.")
    print("It will run three tests:")
    print("  1. Single instruction evaluation")
    print("  2. Multiple instructions comparison")
    print("  3. Real GIMP task evaluation")
    print("\nNote: Make sure the LLM server is running at http://29.160.43.141:8000")

    try:
        # Test 1: Single instruction
        result1 = test_single_instruction()

        # Test 2: Multiple instructions
        results2 = test_multiple_instructions()

        # Test 3: Real task (optional)
        print("\n" + "="*70)
        print("TEST 3: Real GIMP Task Evaluation")
        print("="*70)
        print("\nDo you want to evaluate a real GIMP task? (y/n): ", end="")
        response = input().strip().lower()

        if response == 'y':
            result3 = test_with_real_task()

        print("\n" + "="*70)
        print("ALL TESTS COMPLETED")
        print("="*70)

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
