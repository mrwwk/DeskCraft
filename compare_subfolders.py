#!/usr/bin/env python3
"""
直接比较两个结果目录下所有二级子文件夹的名称（task_id），
不按 domain 分组，只看名字是否相同。

结构:
  A: <root>/pyautogui/screenshot/<run_name>/<domain>/<task_id>/
  B: <root>/<domain>/<task_id>/

忽略: stats_visualizations 等辅助文件夹
"""

from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
BASE = Path("/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/results")

PATH_A = BASE / "gpt54-not_interactive—think_low"
PATH_B = BASE / "EvoCUA-32B-20260105-not_interactive/pyautogui/screenshot/EvoCUA-32B-20260105"

IGNORE = {"stats_visualizations", "args.json"}


def collect_tasks_a(root: Path):
    """
    从 A 的 pyautogui/screenshot/<run_name>/<domain>/<task_id>/ 收集所有 task_id。
    返回: { task_id -> domain }（若同名出现在多个 domain 则保留最后一个，但一般不会重复）
    """
    tasks = {}
    screenshot_dir = root / "pyautogui" / "screenshot"
    for run_dir in screenshot_dir.iterdir():
        if not run_dir.is_dir() or run_dir.name in IGNORE:
            continue
        for domain_dir in run_dir.iterdir():
            if not domain_dir.is_dir() or domain_dir.name in IGNORE:
                continue
            for task_dir in domain_dir.iterdir():
                if task_dir.is_dir() and task_dir.name not in IGNORE:
                    tasks[task_dir.name] = domain_dir.name
    return tasks


def collect_tasks_b(root: Path):
    """
    从 B 的 <domain>/<task_id>/ 收集所有 task_id。
    返回: { task_id -> domain }
    """
    tasks = {}
    for domain_dir in root.iterdir():
        if not domain_dir.is_dir() or domain_dir.name in IGNORE:
            continue
        for task_dir in domain_dir.iterdir():
            if task_dir.is_dir() and task_dir.name not in IGNORE:
                tasks[task_dir.name] = domain_dir.name
    return tasks


# ──────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────
print("=" * 70)
print(f"路径 A: {PATH_A}")
print(f"路径 B: {PATH_B}")
print("=" * 70)

tasks_a = collect_tasks_a(PATH_A)   # { task_id -> domain }
tasks_b = collect_tasks_b(PATH_B)   # { task_id -> domain }

set_a = set(tasks_a.keys())
set_b = set(tasks_b.keys())

common    = set_a & set_b
only_in_a = set_a - set_b
only_in_b = set_b - set_a

# ── 打印共同任务 ──────────────────────────────
print(f"\n{'─'*70}")
print(f"[共同存在] 共 {len(common)} 个")
print(f"{'─'*70}")
for t in sorted(common):
    print(f"  {t}  (A domain: {tasks_a[t]}, B domain: {tasks_b[t]})")

# ── 打印仅 A 有 ───────────────────────────────
print(f"\n{'─'*70}")
print(f"[仅在 A 中] 共 {len(only_in_a)} 个  (gpt54-think_low-noscripts)")
print(f"{'─'*70}")
for t in sorted(only_in_a):
    print(f"  {t}  (domain: {tasks_a[t]})")

# ── 打印仅 B 有 ───────────────────────────────
print(f"\n{'─'*70}")
print(f"[仅在 B 中] 共 {len(only_in_b)} 个  (EvoCUA-32B-20260105)")
print(f"{'─'*70}")
# 按 domain 分组输出，方便阅读
by_domain = defaultdict(list)
for t in only_in_b:
    by_domain[tasks_b[t]].append(t)
for domain in sorted(by_domain):
    print(f"  [{domain}] ({len(by_domain[domain])} 个)")
    for t in sorted(by_domain[domain]):
        print(f"    {t}")

print(f"\n{'='*70}")
print(f"汇总: A={len(set_a)}  B={len(set_b)}  共同={len(common)}  仅A={len(only_in_a)}  仅B={len(only_in_b)}")
print("=" * 70)
