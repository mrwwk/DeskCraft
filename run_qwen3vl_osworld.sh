# Usage: change url ip before running, also change result_dir and model as needed
# max steps is set to 15, {50, 100} may also be used for more thorough evaluation
#!/bin/bash

export OPENAI_BASE_URL=http://28.33.19.134:8080/v1
export GET_OBS_BEFORE_ACTION=1
python run_multienv_qwen3vl.py \
  --provider_name docker \
  --test_all_meta_path evaluation_examples/test_all.json \
  --headless \
  --max_steps 15 \
  --domain  all  \
  --num_envs 5  \
  --result_dir ./results/qwen3vl_8b_s15_instruct \
  --log_level INFO \
  --sleep_after_execution 3 \
  --model Qwen/Qwen3-VL-8B-Instruct \