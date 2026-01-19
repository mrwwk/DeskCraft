from desktop_env.desktop_env import DesktopEnv
import argparse
import logging
import os
import sys
import datetime
import json


with open("evaluation_examples/examples/vs_code/4e60007a-f5be-4bfc-9723-c39affa0a6d3.json", "r") as f:
    example = json.load(f)
# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--provider_name", type=str, default="docker")
parser.add_argument("--path_to_vm", type=str, default=None)
parser.add_argument("--os_type", type=str, default="Ubuntu")
parser.add_argument("--action_space", type=str, default="pyautogui")
parser.add_argument("--log_level", type=str, default="DEBUG")
parser.add_argument("--headless", type=bool, default=False) # Set to True if you want to run without GUI
args = parser.parse_args()


logger = logging.getLogger()
log_level = getattr(logging, args.log_level.upper())
logger.setLevel(log_level)

datetime_str: str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")

file_handler = logging.FileHandler(
    os.path.join("logs", "normal-{:}.log".format(datetime_str)), encoding="utf-8"
)
debug_handler = logging.FileHandler(
    os.path.join("logs", "debug-{:}.log".format(datetime_str)), encoding="utf-8"
)
stdout_handler = logging.StreamHandler(sys.stdout)

file_handler.setLevel(logging.INFO)
debug_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(log_level)

formatter = logging.Formatter(
    fmt="\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s \x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] \x1b[0m%(message)s"
)
file_handler.setFormatter(formatter)
debug_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)

stdout_handler.addFilter(logging.Filter("desktopenv"))

logger.addHandler(file_handler)
logger.addHandler(debug_handler)
logger.addHandler(stdout_handler)
#  }}} Logger Configs #

logger = logging.getLogger("desktopenv.experiment")

# Initialize DesktopEnv
env = DesktopEnv(
    provider_name=args.provider_name,
    path_to_vm=args.path_to_vm,
    os_type=args.os_type,
    action_space=args.action_space,
    headless=args.headless
)

logger.info("Starting OSWorld environment...")
obs = env.reset(task_config=example)
logger.info("Environment reset complete!")

# logger.info("Executing action: pyautogui.rightClick()")
# obs, reward, done, info = env.step("pyautogui.rightClick()")
# logger.info("Action executed successfully!")


import time

# # Step-by-step execution of actions from traj.jsonl
# with open('results/pyautogui/screenshot/ByteDance-Seed/UI-TARS-1.5-7B/vs_code/4e60007a-f5be-4bfc-9723-c39affa0a6d3/traj.jsonl', 'r') as file:
#     import json
#     for line in file:
#         action_data = json.loads(line)
#         action_code = action_data.get('action', '')
#         if action_code:
#             logger.info("Executing action: %s", action_code)
#             env.step(action_code)
#             time.sleep(1)  # Adding delay between actions for stability
# time.sleep(2)  # Wait before evaluation

# result = env.evaluate()
# logger.info("Result: %.2f", result)
# time.sleep(1)
# # Clean up
# env.close()
# logger.info("Environment closed.")