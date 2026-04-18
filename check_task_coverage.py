"""
检验 results 目录中的任务 ID 是否与 JSON 任务列表完全对应。
"""
import json
import os
from pathlib import Path

RESULT_BASE = Path(
    "/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800"
    "/user/jackwkwang/code/OSWorld/results/gpt54_interactive7/pyautogui"
    "/screenshot/api_azure_openai_gpt-5.4-2026-03-05"
)
JSON_PATH = Path(
    "/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800"
    "/user/jackwkwang/code/OSWorld/evaluation_examples"
    "/example_final_interactive_gpt54_all.json"
)

# ── 1. 从 JSON 收集所有任务 ID ──────────────────────────────────────────────
with open(JSON_PATH) as f:
    task_list = json.load(f)

json_ids: set[str] = set()
json_id_to_domain: dict[str, str] = {}
for domain, ids in task_list.items():
    for tid in ids:
        json_ids.add(tid)
        json_id_to_domain[tid] = domain

# ── 2. 从 results 目录收集所有任务 ID ─────────────────────────────────────
result_ids: set[str] = set()
result_id_to_domain: dict[str, str] = {}
for domain_dir in sorted(RESULT_BASE.iterdir()):
    if not domain_dir.is_dir():
        continue
    domain = domain_dir.name
    for task_dir in sorted(domain_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        tid = task_dir.name
        result_ids.add(tid)
        result_id_to_domain[tid] = domain

# ── 3. 对比 ────────────────────────────────────────────────────────────────
only_in_json   = json_ids   - result_ids   # JSON 有，results 没有 → 缺失
only_in_result = result_ids - json_ids     # results 有，JSON 没有 → 多余
common         = json_ids & result_ids

print("=" * 65)
print(f"  JSON  中任务总数 : {len(json_ids)}")
print(f"  结果目录任务总数 : {len(result_ids)}")
print(f"  两者共同任务数   : {len(common)}")
print("=" * 65)

if not only_in_json and not only_in_result:
    print("\n✅  完全一致！所有任务 ID 双向对应。\n")
else:
    if only_in_json:
        print(f"\n❌  仅在 JSON 中（results 缺失，共 {len(only_in_json)} 个）：")
        for tid in sorted(only_in_json):
            print(f"    [{json_id_to_domain[tid]}]  {tid}")

    if only_in_result:
        print(f"\n⚠️   仅在 results 中（JSON 未列出，共 {len(only_in_result)} 个）：")
        for tid in sorted(only_in_result):
            print(f"    [{result_id_to_domain[tid]}]  {tid}")

# ── 4. 按 domain 分组统计 ──────────────────────────────────────────────────
print("\n── 按 domain 统计（JSON 预期 vs 结果实有）──")
all_domains = sorted(set(list(task_list.keys()) +
                         [d.name for d in RESULT_BASE.iterdir() if d.is_dir()]))
for domain in all_domains:
    expected = set(task_list.get(domain, []))
    actual   = set()
    domain_dir = RESULT_BASE / domain
    if domain_dir.is_dir():
        actual = {d.name for d in domain_dir.iterdir() if d.is_dir()}
    match = "✅" if expected == actual else "❌"
    print(f"  {match}  {domain:<35}  预期={len(expected):>3}  实有={len(actual):>3}  "
          f"缺失={len(expected-actual):>2}  多余={len(actual-expected):>2}")

# ── 5. 检查 result.txt 是否存在（任务是否真正跑完）───────────────────────
print("\n── result.txt 完成情况 ──")
has_result, no_result = [], []
for tid in sorted(result_ids):
    domain = result_id_to_domain[tid]
    result_file = RESULT_BASE / domain / tid / "result.txt"
    (has_result if result_file.exists() else no_result).append((domain, tid))

print(f"  已有 result.txt : {len(has_result)}")
print(f"  缺少 result.txt : {len(no_result)}")
if no_result:
    print("  缺少的任务：")
    for domain, tid in no_result:
        print(f"    [{domain}]  {tid}")

print("\n完成。\n")
