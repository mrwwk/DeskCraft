#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 gimp_new 任务列表的脚本
自动扫描 evaluation_examples/examples/gimp_new 目录下的所有 JSON 文件
并创建 test_all.json 格式的配置文件
"""

import os
import json

def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # gimp_new 目录路径
    gimp_new_dir = os.path.join(script_dir, "evaluation_examples/examples/gimp_new")
    
    # 检查目录是否存在
    if not os.path.exists(gimp_new_dir):
        print(f"错误：目录不存在 - {gimp_new_dir}")
        return
    
    # 获取所有 JSON 文件的任务 ID
    task_ids = []
    for filename in os.listdir(gimp_new_dir):
        if filename.endswith('.json'):
            # 去掉 .json 后缀
            task_id = filename.replace('.json', '')
            task_ids.append(task_id)
    
    # 按字母顺序排序
    task_ids.sort()
    
    # 创建 test_all.json 格式
    test_all_meta = {
        "gimp_new": task_ids
    }
    
    # 写入 test_all.json 文件
    output_path = os.path.join(script_dir, "evaluation_examples/gimp_new.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_all_meta, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 成功创建 {output_path}")
    print(f"✓ 共包含 {len(task_ids)} 个任务")
    print(f"\n任务列表:")
    for task_id in task_ids:
        print(f"  - {task_id}")
    
    print(f"\n运行命令:")
    print(f"  python run_multienv_uitars15_v2.py --domain gimp_new --provider_name docker --headless --num_envs 1 --max_steps 15 --model \"UI-TARS-1.5-7B\"")

if __name__ == "__main__":
    main()
