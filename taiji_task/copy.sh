DATA_PATH="/apdcephfs/jp_fsgm_cephfs3/apdcephfs_fsgm/share_304220499/chenxuwu"
CODE_PATH="/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang"

cd ${CODE_PATH}/code/OSWorld

# 1. 处理 cache
if [ ! -d "cache" ]; then
    echo ">>> Start copying osworld_cache.zip..."
    # 使用 rsync -avP 替代 cp -r
    # -a: 归档模式，保留权限等
    # -v: 详细输出
    # -P: 显示进度条 (Progress) 并支持断点续传
    rsync -avP ${DATA_PATH}/data/osworld_cache.zip ./osworld_cache.zip
    
    echo ">>> Start unzipping osworld_cache.zip..."
    # 去掉 -q 参数，显示解压文件列表以观察进度
    unzip osworld_cache.zip && mv osworld_cache cache && rm -rf osworld_cache.zip
fi

# 2. 处理 image
echo ">>> Start copying osworld_image.tar..."
rsync -avP ${DATA_PATH}/data/osworld_image.tar ./osworld_image.tar

mkdir -p docker_vm_data

# 3. 处理 Ubuntu 镜像
if [ ! -f "docker_vm_data/Ubuntu.qcow2" ]; then
    echo ">>> Start copying Ubuntu.qcow2.zip..."
    rsync -avP ${DATA_PATH}/data/Ubuntu.qcow2.zip ./docker_vm_data/
    
    cd docker_vm_data
    echo ">>> Start unzipping Ubuntu.qcow2.zip..."
    unzip Ubuntu.qcow2.zip && rm -f Ubuntu.qcow2.zip && cd ..
fi