#!/usr/bin/env python3
"""
Check if all cloud_file in evaluator configs can be loaded from cache.
"""

import json
import os
from pathlib import Path

cache_dir = "cache"
input_dir = "evaluation_examples/examples/gimp_new"

print("=" * 80)
print("检查所有 evaluator 中的 cloud_file 是否能从缓存加载")
print("=" * 80)

input_path = Path(input_dir)
json_files = list(input_path.glob('*.json'))

total = 0
success = 0
failed = 0
no_cloud_file = 0

results = []

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        task_data = json.load(f)
    
    task_id = task_data.get('id', 'unknown')
    evaluator = task_data.get('evaluator', {})
    expected = evaluator.get('expected', [])
    
    if isinstance(expected, dict):
        expected = [expected]
    
    if not expected:
        no_cloud_file += 1
        continue
    
    for exp in expected:
        if not exp or exp.get('type') != 'cloud_file':
            continue
        
        total += 1
        url = exp.get('path')
        dest = exp.get('dest')
        
        if not url or not dest:
            failed += 1
            results.append({
                'task_id': task_id,
                'status': 'FAILED',
                'reason': 'Missing url or dest',
                'url': url,
                'dest': dest,
                'cache_path': None
            })
            continue
        
        # cloud_file 的缓存路径是 cache/{task_id}/{dest}
        cache_path = os.path.join(cache_dir, task_id, dest)
        
        if os.path.exists(cache_path):
            file_size = os.path.getsize(cache_path)
            success += 1
            results.append({
                'task_id': task_id,
                'status': 'SUCCESS',
                'reason': None,
                'url': url,
                'dest': dest,
                'cache_path': cache_path,
                'file_size': file_size
            })
        else:
            failed += 1
            results.append({
                'task_id': task_id,
                'status': 'FAILED',
                'reason': 'Cache file not found',
                'url': url,
                'dest': dest,
                'cache_path': cache_path
            })

print(f"\n总任务数：{len(json_files)}")
print(f"无 cloud_file 的任务：{no_cloud_file}")
print(f"有 cloud_file 的总数：{total}")
print(f"✅ 成功：{success}")
print(f"❌ 失败：{failed}")

print("\n" + "=" * 80)
print("详细信息:")
print("=" * 80)

for r in results:
    status_icon = "✅" if r['status'] == 'SUCCESS' else "❌"
    print(f"\n{status_icon} 任务：{r['task_id']}")
    print(f"   状态：{r['status']}")
    if r['reason']:
        print(f"   原因：{r['reason']}")
    print(f"   URL: {r['url']}")
    print(f"   目标文件：{r['dest']}")
    if r['cache_path']:
        print(f"   缓存路径：{r['cache_path']}")
    if r.get('file_size'):
        print(f"   文件大小：{r['file_size'] / 1024:.2f} KB")

if failed > 0:
    print("\n" + "=" * 80)
    print("失败的任务列表:")
    print("=" * 80)
    for r in results:
        if r['status'] == 'FAILED':
            print(f"  - {r['task_id']}: {r['dest']} ({r['reason']})")
