from desktop_env.desktop_env import DesktopEnv
import argparse
import json
import time
import os

with open("evaluation_examples/examples/blender/test_blender.json", "r") as f:
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
os.makedirs("blender_screenshots", exist_ok=True)

def save_screenshot(obs, filename):
    """Save screenshot from observation to file."""
    filepath = os.path.join("blender_screenshots", filename)
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

# Step 0: Reset environment (only click to clear screen overlay)
obs = env.reset(task_config=example)
print("\n[Step 0] Environment reset complete. Taking initial screenshot...")
save_screenshot(obs, "step0_initial_desktop.png")

# Step 1: Open terminal using Ctrl+Alt+T keyboard shortcut
print("\n[Step 1] Opening terminal with Ctrl+Alt+T...")
obs, _, _, _ = env.step('import pyautogui; pyautogui.hotkey("ctrl", "alt", "t")', pause=3)
save_screenshot(obs, "step1_open_terminal.png")

# Step 2: Wait for terminal to fully appear
print("\n[Step 2] Waiting for terminal to fully load...")
time.sleep(3)
obs = env._get_obs()
save_screenshot(obs, "step2_terminal_ready.png")

# Step 3: Type 'blender' in the terminal
print("\n[Step 3] Typing 'blender' in terminal...")
obs, _, _, _ = env.step('import pyautogui; pyautogui.typewrite("blender", interval=0.05)', pause=2)
save_screenshot(obs, "step3_typed_blender.png")

# Step 4: Press Enter to execute the command
print("\n[Step 4] Pressing Enter to run blender...")
obs, _, _, _ = env.step('import pyautogui; pyautogui.press("enter")', pause=3)
save_screenshot(obs, "step4_pressed_enter.png")

# Step 5: Wait for Blender to start loading
print("\n[Step 5] Waiting 10 seconds for Blender to start loading...")
time.sleep(10)
obs = env._get_obs()
save_screenshot(obs, "step5_blender_loading.png")

# Step 6: Wait more and take final screenshot
print("\n[Step 6] Waiting another 10 seconds for Blender to fully open...")
time.sleep(10)
obs = env._get_obs()
save_screenshot(obs, "step6_blender_final.png")

print("\n" + "=" * 60)
print("All screenshots saved in blender_screenshots/ directory:")
for f in sorted(os.listdir("blender_screenshots")):
    print(f"  - {f}")
print("=" * 60)

# Clean up
env.close()
print("Environment closed.")
