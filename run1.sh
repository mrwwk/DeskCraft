cd apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang
git clone https://github.com/demouo/parameter-golf 
cd parameter-golf

# download
python data/cached_challenge_fineweb.py --variant sp1024

# start running
RUN_ID=baseline_sp1024 \
DATA_PATH=./data/datasets/fineweb10B_sp1024/ \
TOKENIZER_PATH=./data/tokenizers/fineweb_1024_bpe.model \
VOCAB_SIZE=1024 \
torchrun --standalone --nproc_per_node=1 train_gpt.py
