import json
import os
from pathlib import Path

gimp_folder = Path("/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/examples/gimp")

funcs = []

for json_file in sorted(gimp_folder.glob("*.json")):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            func = data.get('evaluator', {}).get('func', 'N/A')
            if isinstance(func, list):
                funcs.extend(func)
            else:
                funcs.append(func)
    except Exception as e:
        funcs.append(f'Error: {str(e)}')

unique_funcs = sorted(list(set(funcs)))
print(unique_funcs)
