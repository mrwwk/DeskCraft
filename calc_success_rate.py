#!/usr/bin/env python3
"""计算 OSWorld 评测的 Success Rate - 直接扫描 result.txt 文件"""
import sys
import os

def calc_success_rate(result_dir):
    # 查找所有 result.txt 文件
    by_app = {}
    total = 0
    success = 0
    
    # 遍历 pyautogui/screenshot 下的所有应用目录
    screenshot_dir = os.path.join(result_dir, "pyautogui", "screenshot")
    if not os.path.exists(screenshot_dir):
        print(f"Error: {screenshot_dir} not found")
        return
    
    for app in os.listdir(screenshot_dir):
        app_dir = os.path.join(screenshot_dir, app)
        if not os.path.isdir(app_dir) or app == "args.json":
            continue
        
        if app not in by_app:
            by_app[app] = {'total': 0, 'success': 0}
        
        # 遍历每个任务目录
        for task_id in os.listdir(app_dir):
            task_dir = os.path.join(app_dir, task_id)
            if not os.path.isdir(task_dir):
                continue
            
            result_file = os.path.join(task_dir, "result.txt")
            if os.path.exists(result_file):
                by_app[app]['total'] += 1
                total += 1
                try:
                    with open(result_file, 'r') as f:
                        score = float(f.read().strip())
                        if score == 1.0:
                            by_app[app]['success'] += 1
                            success += 1
                except:
                    pass  # 解析失败算失败
    
    if total == 0:
        print("No results found")
        return
    
    print('='*50)
    print('OSWorld Evaluation Results')
    print('='*50)
    print(f'Total tasks: {total}')
    print(f'Success: {success}')
    print(f'Failed: {total - success}')
    print(f'Success Rate: {success/total*100:.2f}%')
    print()
    print('By Application:')
    for app, stats in sorted(by_app.items()):
        if stats['total'] > 0:
            rate = stats['success']/stats['total']*100
            print(f'  {app}: {stats["success"]}/{stats["total"]} ({rate:.2f}%)')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result_dir = sys.argv[1]
    else:
        # 默认使用最新的结果目录
        result_dir = "/data/workspace/OSWorld_code/results/UI-TARS-1.5-7B_20260123_120446_envs10_steps15"
    
    calc_success_rate(result_dir)
