import json
import os
import urllib.request
import uuid

base_dir = '/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld'
cache_dir = os.path.join(base_dir, 'cache')
os.makedirs(cache_dir, exist_ok=True)

interactive_jsons = [
    'evaluation_examples/examples/interactive/interactive_gimp_progressive_001.json',
    'evaluation_examples/examples/interactive/interactive_calc_requirement_change_001.json',
    'evaluation_examples/examples/interactive/interactive_impress_workflow_001.json',
    'evaluation_examples/examples/interactive/interactive_gimp_correction_001.json',
    'evaluation_examples/examples/interactive/interactive_os_ambiguous_001.json',
    'evaluation_examples/examples/interactive/interactive_writer_interruption_001.json'
]

downloads = []

for json_file in interactive_jsons:
    full_path = os.path.join(base_dir, json_file)
    if os.path.exists(full_path):
        with open(full_path, 'r') as f:
            data = json.load(f)
            task_id = data['id']
            for item in data.get('config', []):
                if item.get('type') == 'download':
                    for file_info in item['parameters'].get('files', []):
                        url = file_info['url']
                        # OSWorld cache naming logic: uuid.uuid5(uuid.NAMESPACE_URL, url)
                        url_hash = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
                        
                        path = file_info['path']
                        fname = os.path.basename(path)
                        
                        task_cache_dir = os.path.join(cache_dir, task_id)
                        os.makedirs(task_cache_dir, exist_ok=True)
                        
                        cache_path = os.path.join(task_cache_dir, f"{url_hash}_{fname}")
                        downloads.append((url, cache_path))

# Set up proxies for the Tencent network
proxy = urllib.request.ProxyHandler({'https': 'http://hk-mmhttpproxy.woa.com:11113', 'http': 'http://hk-mmhttpproxy.woa.com:11113'})
opener = urllib.request.build_opener(proxy)
urllib.request.install_opener(opener)

for url, dest in downloads:
    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        print(f'Downloading {url}\n -> {dest}')
        try:
            urllib.request.urlretrieve(url, dest)
            print(f' ✓ Done. Size: {os.path.getsize(dest)} bytes')
        except Exception as e:
            print(f' ✗ Error downloading: {e}')
    else:
        print(f' ✓ Already cached: {dest}')

print('\nAll cache files processed.')
