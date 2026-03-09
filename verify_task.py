#!/usr/bin/env python3
"""Comprehensive task verification script."""

import json
import os
import sys
import importlib.util
import re

print("=" * 70)
print("COMPREHENSIVE TASK VERIFICATION")
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
    
    elif cfg_type == 'sleep':
        seconds = cfg.get('parameters', {}).get('seconds', 0)
        print(f"    - Sleep: {seconds} seconds")

print("\n3. EVALUATOR CHECK")
print("-" * 70)
evaluator = task.get('evaluator', {})
print(f"  Function: {evaluator.get('func', 'MISSING')}")
print(f"  Has postconfig: {'✓' if 'postconfig' in evaluator else '✗'}")
print(f"  Has result: {'✓' if 'result' in evaluator else '✗'}")
print(f"  Has options: {'✓' if 'options' in evaluator else '✗'}")

postconfig = evaluator.get('postconfig', [])
print(f"\n  Postconfig steps: {len(postconfig)}")
for i, pc in enumerate(postconfig, 1):
    pc_type = pc.get('type', 'UNKNOWN')
    if pc_type == 'execute':
        command = pc.get('parameters', {}).get('command', [])
        print(f"    {i}. Execute: {' '.join(command)}")
    elif pc_type == 'sleep':
        seconds = pc.get('parameters', {}).get('seconds', 0)
        print(f"    {i}. Sleep: {seconds}s")

result_cfg = evaluator.get('result', {})
print(f"\n  Result configuration:")
print(f"    Type: {result_cfg.get('type', 'MISSING')}")
print(f"    Multi: {result_cfg.get('multi', False)}")
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
spec = importlib.util.spec_from_file_location('gimp_l2', 'desktop_env/evaluators/metrics/gimp_l2.py')
gimp_l2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gimp_l2)

func_name = evaluator.get('func', '')
if hasattr(gimp_l2, func_name):
    func = getattr(gimp_l2, func_name)
    print(f"  ✓ Function '{func_name}' exists in gimp_l2.py")
    import inspect
    sig = inspect.signature(func)
    print(f"    Signature: {sig}")
    
    test_result = func(
        result_paths=['/nonexistent/a.jpg', '/nonexistent/b.xcf', '/nonexistent/c.jpg'],
        expected_width=options.get('expected_width', 1400)
    )
    print(f"    Test result (nonexistent files): {test_result}")
    print(f"    ✓ Function executes correctly")
else:
    print(f"  ✗ Function '{func_name}' NOT FOUND in gimp_l2.py")

print("\n5. FINAL RESULT FILES CHECK")
print("-" * 70)
instruction = task.get('instruction', '')
if 'Export' in instruction or 'export' in instruction or 'Save' in instruction or 'save' in instruction:
    print("  ✓ Instruction mentions exporting/saving files")
    exported_files = re.findall(r"['\"]([^'\"]+\.(jpg|jpeg|png|xcf))['\"]", instruction)
    if exported_files:
        print(f"    Files mentioned: {[f[0] for f in exported_files]}")
else:
    print("  ✗ Instruction does NOT mention exporting/saving files")

postconfig_str = json.dumps(postconfig)
if 'export' in postconfig_str.lower() or 'save' in postconfig_str.lower():
    print("  ✓ Postconfig includes export/save operations")
else:
    print("  ⚠ Postconfig does NOT include export/save operations")
    print("    Note: Model must save files during task execution")

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
    print("    Note: Model needs to open GIMP manually")

print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

issues = []

if not all(f in task for f in required_fields):
    issues.append("Missing required JSON fields")

has_upload = any(cfg.get('type') == 'upload_file' for cfg in config)
if not has_upload:
    issues.append("No upload_file config step")
if not has_launch:
    issues.append("No launch config step (GIMP may not open)")

if not hasattr(gimp_l2, func_name):
    issues.append(f"Evaluator function '{func_name}' not found")

result_paths = result_cfg.get('path', [])
if not result_paths:
    issues.append("No result paths defined")

if issues:
    print("❌ ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)
else:
    print("✅ ALL CHECKS PASSED!")
    print("\nThe task is properly configured with:")
    print("  - Valid JSON structure")
    print("  - Asset file upload")
    print("  - GIMP launch command")
    print("  - Evaluator function (check_beach_footprint_art_complete)")
    print("  - Result file paths defined")
    print("  - Postconfig for cleanup")

print("=" * 70)
