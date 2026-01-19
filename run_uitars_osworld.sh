# export DOUBAO_API_URL=http://localhost:8000/v1
# export DOUBAO_API_KEY=EMPTY
python run_multienv_uitars15_v1.py \
  --provider_name docker \
  --test_all_meta_path evaluation_examples/test_all.json \
  --headless \
  --max_steps 15 \
  --domain  all  \
  --num_envs 10  \
  --result_dir ./results/uitars15_osworld_s15 \
  --log_level INFO \
  --sleep_after_execution 3 \
  --model ByteDance-Seed/UI-TARS-1.5-7B \