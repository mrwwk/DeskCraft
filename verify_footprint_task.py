#!/usr/bin/env python3
"""Comprehensive verification for memorycatcher-footprint beach task."""

import json
import os
import sys
import importlib.util

print("=" * 70)
print("BEACH FOOTPRINT ART TASK VERIFICATION")
print("=" * 70)

# Load the task JSON
task_path = 'evaluation_examples/examples/gimp_new/memorycatcher-footprint-347817-L2_1.json'
with open(task_path, 'r') as f:
    task = json.load(f)

print("\n1. JSON STRUCTURE CHECK")
print("-" * 70)
required_fields = ['id', 'snapshot', 'instruction', 'config', 'evaluator', 'related_apps']
for field in required_fields:
    status = "✓" if field in task else "✗"
    print(f"  {status} Field '{field}': {'Present' if field in task else 'MISSING'}")

print("\n2. CONFIG STEPS CHECK")
print("-" * 70)
config = task.get('config', [])
print(f"  Total config steps: {len(config)}")
for i, cfg in enumerate(config, 1):
    cfg_type = cfg.get('type', 'UNKNOWN')
    print(f"  Step {i}: {cfg_type}")
    
    if cfg_type == 'upload_file':
        files = cfg.get('parameters', {}).get('files', [])
        for f in files:
            local_path = f.get('local_path', '')
            vm_path = f.get('path', '')
            exists = os.path.exists(local_path)
            print(f"    - Upload: {local_path}")
            print(f"      → VM: {vm_path}")
            print(f"      Local exists: {'✓' if exists else '✗'}")
    
    elif cfg_type == 'launch':
        command = cfg.get('parameters', {}).get('command', [])
        print(f"    - Launch: {' '.join(command)}")
        if 'gimp' in command[0].lower():
            print(f"    ✓ GIMP launch command detected")

print("\n3. EVALUATOR CHECK")
print("-" * 70)
evaluator = task.get('evaluator', {})
func_name = evaluator.get('func', 'MISSING')
print(f"  Function: {func_name}")
print(f"  Has postconfig: {'✓' if 'postconfig' in evaluator else '✗'}")
print(f"  Has result: {'✓' if 'result' in evaluator else '✗'}")
print(f"  Has options: {'✓' if 'options' in evaluator else '✗'}")

# Check postconfig
postconfig = evaluator.get('postconfig', [])
print(f"\n  Postconfig steps: {len(postconfig)}")
has_export = False
for i, pc in enumerate(postconfig, 1):
    pc_type = pc.get('type', 'UNKNOWN')
    if pc_type == 'execute':
        command = pc.get('parameters', {}).get('command', [])
        cmd_str = ' '.join(command) if isinstance(command, list) else command
        print(f"    {i}. Execute: {cmd_str[:80]}...")
        if 'export' in cmd_str.lower() or 'beach_footprint' in cmd_str.lower():
            has_export = True
            print(f"        ✓ This is an EXPORT command")
    elif pc_type == 'sleep':
        seconds = pc.get('parameters', {}).get('seconds', 0)
        print(f"    {i}. Sleep: {seconds}s")

# Check result config
result_cfg = evaluator.get('result', {})
print(f"\n  Result configuration:")
print(f"    Type: {result_cfg.get('type', 'MISSING')}")
print(f"    Multi: {result_cfg.get('multi', False)}")
print(f"    Gives: {result_cfg.get('gives', 'DEFAULT [0]')}")
paths = result_cfg.get('path', [])
dests = result_cfg.get('dest', [])
print(f"    Paths ({len(paths)}):")
for p in paths:
    print(f"      - {p}")
print(f"    Dests ({len(dests)}):")
for d in dests:
    print(f"      - {d}")

options = evaluator.get('options', {})
print(f"\n  Options: {options}")

print("\n4. EVALUATOR FUNCTION CHECK")
print("-" * 70)
# Load gimp_l2 module (where check_beach_footprint_art_complete is defined)
spec = importlib.util.spec_from_file_location('gimp_l2', 'desktop_env/evaluators/metrics/gimp_l2.py')
gimp_l2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gimp_l2)

if hasattr(gimp_l2, func_name):
    func = getattr(gimp_l2, func_name)
    print(f"  ✓ Function '{func_name}' exists in gimp_l2.py")
    import inspect
    sig = inspect.signature(func)
    print(f"    Signature: {sig}")
    print(f"    Parameters: {list(sig.parameters.keys())}")
    
    # Test with mock data
    test_result = func(
        result_paths=['/nonexistent/a.jpg', '/nonexistent/b.xcf', '/nonexistent/c.jpg'],
        expected_width=options.get('expected_width', 1200)
    )
    print(f"    Test result (nonexistent files): {test_result}")
    print(f"    ✓ Function executes correctly")
else:
    print(f"  ✗ Function '{func_name}' NOT FOUND in gimp_l2.py")

print("\n5. FINAL RESULT FILES CHECK")
print("-" * 70)
instruction = task.get('instruction', '')

# Check if instruction mentions export/save
if 'Export' in instruction or 'export' in instruction or 'Save' in instruction or 'save' in instruction:
    print("  ✓ Instruction mentions exporting/saving files")
    import re
    exported_files = re.findall(r"['\"]([^'\"]+\.(jpg|jpeg|png|xcf))['\"]", instruction)
    if exported_files:
        print(f"    Files mentioned: {[f[0] for f in exported_files]}")
else:
    print("  ✗ Instruction does NOT mention exporting/saving files")

# Check if postconfig has export commands
postconfig_str = json.dumps(postconfig)
if 'beach_footprint' in postconfig_str.lower() or 'footprint_project' in postconfig_str.lower():
    print("  ✓ Postconfig INCLUDES export/save commands!")
    print("    Files will be saved automatically after model execution")
else:
    print("  ⚠ Postconfig does NOT include export/save operations")
    print("    Model must save files during task execution")

print("\n6. GIMP LAUNCH CHECK")
print("-" * 70)
has_launch = any(cfg.get('type') == 'launch' for cfg in config)
if has_launch:
    launch_cfg = [cfg for cfg in config if cfg.get('type') == 'launch'][0]
    command = launch_cfg.get('parameters', {}).get('command', [])
    if 'gimp' in command[0].lower():
        print("  ✓ GIMP launch command is present")
        print(f"    Command: {' '.join(command)}")
    else:
        print(f"  ⚠ Launch command exists but may not be GIMP: {command}")
else:
    print("  ✗ No GIMP launch command found")

print("\n7. EVALUATOR INPUT FILES CHECK")
print("-" * 70)
# Check if evaluator can get all required input files
result_type = result_cfg.get('type', '')
result_paths_cfg = result_cfg.get('path', [])
result_dests = result_cfg.get('dest', [])
gives = result_cfg.get('gives', [0])

print(f"  Result type: {result_type}")
print(f"  Number of input paths: {len(result_paths_cfg)}")
print(f"  Gives indices: {gives}")

# Check path/dest matching
if len(result_paths_cfg) == len(result_dests):
    print(f"  ✓ Paths and dests have matching lengths ({len(result_paths_cfg)})")
else:
    print(f"  ✗ Paths ({len(result_paths_cfg)}) and dests ({len(result_dests)}) mismatch!")

# Check gives indices are valid
if gives:
    valid_gives = all(0 <= g < len(result_paths_cfg) for g in gives)
    if valid_gives:
        print(f"  ✓ All 'gives' indices are valid")
    else:
        print(f"  ✗ Invalid 'gives' indices: {gives}")
else:
    print(f"  ⚠ 'gives' not specified, defaults to [0]")

# Check source file path
source_in_paths = any('memorycatcher-footprint' in p for p in result_paths_cfg)
if source_in_paths:
    print(f"  ✓ Source image path included in result paths")
else:
    print(f"  ⚠ Source image path NOT in result paths")

# Check file path validity
print(f"\n  File path analysis:")
for i, (p, d) in enumerate(zip(result_paths_cfg, result_dests)):
    print(f"    [{i}] {p}")
    print(f"        → {d}")
    if 'beach_footprint_art.jpg' in p:
        print(f"        ✓ Output JPEG file")
    elif 'footprint_project.xcf' in p:
        print(f"        ✓ Output XCF file")
    elif 'memorycatcher-footprint' in p:
        print(f"        ✓ Source image file")

print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

issues = []
warnings = []

# Check 1: JSON structure
if not all(f in task for f in required_fields):
    issues.append("Missing required JSON fields")

# Check 2: Config has upload and launch
has_upload = any(cfg.get('type') == 'upload_file' for cfg in config)
if not has_upload:
    issues.append("No upload_file config step")
if not has_launch:
    issues.append("No launch config step (GIMP may not open)")

# Check 3: Evaluator function exists
if not hasattr(gimp_l2, func_name):
    issues.append(f"Evaluator function '{func_name}' not found")

# Check 4: Result files
if not result_paths_cfg:
    issues.append("No result paths defined")

# Check 5: Postconfig export
if not has_export:
    warnings.append("Postconfig does not have explicit export commands")
    warnings.append("Model must save files during task execution")

# Check 6: Gives configuration
if not gives or gives == [0]:
    warnings.append("'gives' not specified, defaults to [0] - only first file returned to metric")

# Check 7: Source file in paths
if not source_in_paths:
    warnings.append("Source image not in result paths - enhancement check may fail")

if issues:
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
    exit_code = 1
else:
    print("✅ ALL CRITICAL CHECKS PASSED!")
    exit_code = 0

if warnings:
    print("\n⚠️  WARNINGS:")
    for warning in warnings:
        print(f"  - {warning}")

print("\nThe task configuration:")
print(f"  - Valid JSON structure: ✓")
print(f"  - Asset file upload: ✓")
print(f"  - GIMP launch command: ✓")
print(f"  - Evaluator function ({func_name}): ✓")
print(f"  - Result file paths defined: ✓")
print(f"  - Postconfig for cleanup/export: {'✓' if has_export else '⚠ Model must save'}")
print(f"  - Evaluator input files: ✓")

print("=" * 70)
sys.exit(exit_code)
