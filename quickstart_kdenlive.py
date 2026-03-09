from desktop_env.desktop_env import DesktopEnv
import argparse
import json
import time
import os

with open("evaluation_examples/examples/kdenlive/test_kdenlive.json", "r") as f:
    example = json.load(f)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--provider_name", type=str, default="docker")
parser.add_argument("--path_to_vm", type=str, default="/cq_1/share_300000800/user/jackwkwang/code/OSWorld/docker_vm_data/Ubuntu.qcow2")
parser.add_argument("--os_type", type=str, default="Ubuntu")
parser.add_argument("--action_space", type=str, default="pyautogui")
parser.add_argument("--headless", type=bool, default=True)
args = parser.parse_args()

# Create output directory for screenshots
os.makedirs("kdenlive_screenshots", exist_ok=True)

def save_screenshot(obs, filename):
    """Save screenshot from observation to file."""
    filepath = os.path.join("kdenlive_screenshots", filename)
    with open(filepath, "wb") as f:
        f.write(obs["screenshot"])
    print(f"Screenshot saved to {filepath}")

# Initialize DesktopEnv
env = DesktopEnv(
    provider_name=args.provider_name,
    path_to_vm=args.path_to_vm,
    os_type=args.os_type,
    action_space=args.action_space,
    headless=args.headless
)

print("=" * 60)
print("Starting OSWorld environment...")
print("=" * 60)

# Step 0: Reset environment (launches kdenlive via config and clicks to activate)
obs = env.reset(task_config=example)
print("\n[Step 0] Environment reset complete (kdenlive launched via config). Taking initial screenshot...")
save_screenshot(obs, "step0_initial_desktop.png")

# Step 1: Wait for Kdenlive to start loading
print("\n[Step 1] Waiting 10 seconds for Kdenlive to start loading...")
time.sleep(10)
obs = env._get_obs()
save_screenshot(obs, "step1_kdenlive_loading.png")

# Step 2: Wait more and take final screenshot
print("\n[Step 2] Waiting another 10 seconds for Kdenlive to fully open...")
time.sleep(10)
obs = env._get_obs()
save_screenshot(obs, "step2_kdenlive_final.png")

print("\n" + "=" * 60)
print("All screenshots saved in kdenlive_screenshots/ directory:")
for f in sorted(os.listdir("kdenlive_screenshots")):
    print(f"  - {f}")
print("=" * 60)

# Clean up
env.close()
print("Environment closed.")
