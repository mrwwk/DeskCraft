#!/bin/bash
# Remove proxy settings as they block huggingface.co with 403 Forbidden
unset HTTPS_PROXY
unset HTTP_PROXY
unset https_proxy
unset http_proxy

BASE_DIR="/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld"
CACHE_DIR="${BASE_DIR}/cache"

# Generate instructions via python
python3 -c "
import json
import os
import uuid

base_dir = '${BASE_DIR}'
cache_dir = '${CACHE_DIR}'
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
                        # OSWorld cache naming logic
                        url_hash = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
                        
                        if '?' in url:
                            _url = url.split('?')[0]
                        else:
                            _url = url
                        fname = os.path.basename(file_info['path'])
                        
                        task_cache_dir = os.path.join(cache_dir, task_id)
                        os.makedirs(task_cache_dir, exist_ok=True)
                        
                        dest = os.path.join(task_cache_dir, f'{url_hash}_{fname}')
                        if not os.path.exists(dest) or os.path.getsize(dest) == 0:
                            print(f'{url}|{dest}')
" > /tmp/to_download.txt

echo "Starting downloads using wget..."
while IFS='|' read -r URL DEST; do
    echo "Downloading: $URL"
    echo "To: $DEST"
    # Added -L to follow redirects (which huggingface uses)
    curl -L "$URL" -o "$DEST"
    echo "✓ Saved size: $(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST" 2>/dev/null) bytes"
done < /tmp/to_download.txt

echo "All cache files processed successfully."
