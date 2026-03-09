#!/bin/bash

# ============================================================================
# Task Instruction Clarity Evaluator - Bash Wrapper Script
# ============================================================================
# 
# This script provides a convenient interface to call the
# instruction_clarity_evaluator.py module for evaluating and improving
# task instructions.
#
# Usage Examples:
#   1. Batch evaluate all tasks in default directory:
#      ./run_evaluation.sh
#
#   2. Evaluate a single task file:
#      ./run_evaluation.sh --single-task /path/to/task.json
#
#   3. Custom LLM server and output file:
#      ./run_evaluation.sh --llm-url "http://custom-server:8000" --output results.json
#
# ============================================================================

# Default configuration
DEFAULT_LLM_URL="http://29.160.43.141:8000"
DEFAULT_TASK_DIR="evaluation_examples/examples/gimp"
DEFAULT_OUTPUT="instruction_evaluation_results.json"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
${BLUE}Task Instruction Clarity Evaluator${NC}

This tool evaluates task instructions for clarity and ambiguity,
identifies issues, and provides improved versions.

${YELLOW}Usage:${NC}
    $0 [OPTIONS]

${YELLOW}Options:${NC}
    --task-dir DIR        Directory containing task JSON files (default: ${DEFAULT_TASK_DIR})
    --output FILE         Output file for results (default: ${DEFAULT_OUTPUT})
    --llm-url URL         URL of vLLM server (default: ${DEFAULT_LLM_URL})
    --single-task FILE    Evaluate a single task file instead of batch
    --help, -h            Show this help message

${YELLOW}Examples:${NC}
    # Batch evaluate all tasks in default directory
    $0

    # Evaluate single task file
    $0 --single-task evaluation_examples/examples/gimp/task_001.json

    # Custom output and LLM server
    $0 --output my_results.json --llm-url "http://localhost:8000"

    # Different task directory
    $0 --task-dir /path/to/tasks --output results.json

${YELLOW}Output:${NC}
    Results are saved as JSON files containing:
    - task_id: Task identifier
    - original_instruction: Original instruction text
    - clarity_score: Score from 0.0 to 1.0
    - ambiguity_issues: List of ambiguity problems found
    - vagueness_issues: List of vagueness problems found
    - missing_information: Missing critical information
    - improvement_suggestions: Suggestions for improvement
    - improved_instruction: Rewritten instruction

EOF
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python3 found: $(python3 --version)"
    else
        print_error "Python3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check if required module can be imported
    if python3 -c "import instruction_clarity_evaluator" 2> /dev/null; then
        print_success "instruction_clarity_evaluator module found"
    else
        print_warning "instruction_clarity_evaluator module not in current directory"
        print_warning "Make sure to run this script from the OSWorld directory"
    fi
    
    # Check if requests library is available
    if python3 -c "import requests" 2> /dev/null; then
        print_success "requests library found"
    else
        print_warning "requests library not found, attempting to install..."
        pip3 install requests
    fi
}

check_llm_server() {
    local llm_url=$1
    print_header "Checking LLM Server"
    
    echo "Testing connection to: ${llm_url}"
    
    if python3 -c "
import requests
import sys
try:
    response = requests.get('${llm_url}/v1/models', timeout=10)
    response.raise_for_status()
    models = response.json()
    print('Available models:')
    for model in models.get('data', []):
        print('  - ' + model.get('id', 'unknown'))
except Exception as e:
    print(f'Warning: Could not fetch model list: {e}')
    print('Server might still be usable...')
" 2>/dev/null; then
        print_success "LLM server is reachable"
    else
        print_warning "Could not connect to LLM server"
        print_warning "Please verify the server is running at: ${llm_url}"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Parse arguments
    TASK_DIR="${DEFAULT_TASK_DIR}"
    OUTPUT="${DEFAULT_OUTPUT}"
    LLM_URL="${DEFAULT_LLM_URL}"
    SINGLE_TASK=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --task-dir)
                TASK_DIR="$2"
                shift 2
                ;;
            --output)
                OUTPUT="$2"
                shift 2
                ;;
            --llm-url)
                LLM_URL="$2"
                shift 2
                ;;
            --single-task)
                SINGLE_TASK="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Print configuration
    print_header "Configuration"
    echo "LLM URL:      ${LLM_URL}"
    echo "Output File:  ${OUTPUT}"
    
    if [ -n "${SINGLE_TASK}" ]; then
        echo "Mode:         Single Task"
        echo "Task File:    ${SINGLE_TASK}"
    else
        echo "Mode:         Batch Evaluation"
        echo "Task Dir:     ${TASK_DIR}"
    fi
    
    # Check dependencies
    check_dependencies
    
    # Check LLM server (optional, doesn't fail if unavailable)
    check_llm_server "${LLM_URL}"
    
    # Execute evaluation
    print_header "Starting Evaluation"
    
    # Build command
    CMD="python3 instruction_clarity_evaluator.py"
    
    if [ -n "${SINGLE_TASK}" ]; then
        CMD="${CMD} --single-task '${SINGLE_TASK}'"
    else
        CMD="${CMD} --task-dir '${TASK_DIR}'"
    fi
    
    CMD="${CMD} --output '${OUTPUT}' --llm-url '${LLM_URL}'"
    
    echo "Executing: ${CMD}"
    echo ""
    
    # Run the command
    eval ${CMD}
    
    # Check result
    if [ $? -eq 0 ]; then
        print_header "Execution Complete"
        print_success "Results saved to: ${OUTPUT}"
        
        # Show summary if results file exists
        if [ -f "${OUTPUT}" ]; then
            echo ""
            echo "Quick Summary:"
            echo "--------------"
            python3 -c "
import json
import sys

try:
    with open('${OUTPUT}', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        print(f'Total tasks evaluated: {len(data)}')
        avg_score = sum(d.get('clarity_score', 0) for d in data) / len(data)
        print(f'Average clarity score: {avg_score:.2f}')
        
        # Show tasks with low clarity
        low_clarity = [d for d in data if d.get('clarity_score', 0) < 0.5]
        if low_clarity:
            print(f'\\nTasks needing improvement: {len(low_clarity)}')
            for task in low_clarity[:3]:  # Show first 3
                print(f'  - {task.get(\"task_id\", \"unknown\")}: {task.get(\"clarity_score\", 0):.2f}')
    else:
        print('Single task evaluated')
        print(f'Clarity score: {data.get(\"clarity_score\", \"N/A\")}')
        print(f'Ambiguity issues: {len(data.get(\"ambiguity_issues\", []))}')
        print(f'Vagueness issues: {len(data.get(\"vagueness_issues\", []))}')
        
except Exception as e:
    print(f'Could not generate summary: {e}')
    sys.exit(1)
"
        fi
    else
        print_error "Evaluation failed!"
        exit 1
    fi
}

# Run main function
main "$@"
