"""
    EvoCUA Model Evaluation Script for OSWorld

    This script is adapted from run_multienv_opencua.py for evaluating EvoCUA models.
    EvoCUA models (8B, 32B) are compatible with the OpenCUA agent framework.

    Usage:
    ```
        # For EvoCUA-8B
        python run_multienv_evocua.py \
            --headless \
            --observation_type screenshot \
            --model EvoCUA-8B \
            --model_path /path/to/EvoCUA-8B-20260105 \
            --result_dir ./results \
            --run_name EvoCUA-8B \
            --test_all_meta_path evaluation_examples/test_all.json \
            --max_steps 15 \
            --num_envs 10 \
            --coordinate_type qwen25 \
            --provider_name docker

        # For EvoCUA-32B
        python run_multienv_evocua.py \
            --headless \
            --observation_type screenshot \
            --model EvoCUA-32B \
            --model_path /path/to/EvoCUA-32B-20260105 \
            --result_dir ./results \
            --run_name EvoCUA-32B \
            --test_all_meta_path evaluation_examples/test_all.json \
            --max_steps 15 \
            --num_envs 10 \
            --coordinate_type qwen25 \
            --provider_name docker
    ```
"""

from __future__ import annotations
import argparse
import datetime
import json
import logging
import os
import sys
import signal
import time
from typing import List
from multiprocessing import Process, Manager
from multiprocessing import current_process
import lib_run_single
from desktop_env.desktop_env import DesktopEnv
from mm_agents.evocua import EvoCUAAgent

# Global variables for signal handling
active_environments = []
processes = []
is_terminating = False

# load the environment variables from .env file
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run EvoCUA model evaluation on OSWorld benchmark"
    )

    # environment config
    parser.add_argument("--path_to_vm", type=str, default=None)
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless machine"
    )
    parser.add_argument(
        "--action_space", type=str, default="pyautogui", help="Action type"
    )
    parser.add_argument(
        "--observation_type",
        choices=["screenshot", "a11y_tree", "screenshot_a11y_tree", "som"],
        default="screenshot",
        help="Observation type",
    )
    parser.add_argument("--sleep_after_execution", type=float, default=5.0)
    parser.add_argument("--max_steps", type=int, default=15)
    
    # evaluation config
    parser.add_argument(
        "--test_config_base_dir", type=str, default="evaluation_examples"
    )

    # model config
    parser.add_argument("--model", type=str, default="EvoCUA-8B", help="Model name: EvoCUA-8B or EvoCUA-32B")
    parser.add_argument("--model_path", type=str, default=None, help="Path to the local model weights")
    parser.add_argument("--api_base", type=str, default=None, help="API base URL if using remote inference")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--max_tokens", type=int, default=2048)
    parser.add_argument("--stop_token", type=str, default=None)

    # EvoCUA/OpenCUA agent config
    parser.add_argument("--cot_level", type=str, default="l2", help="CoT version: l1, l2, l3. Default is l2 includes 'thought' and 'action'")
    parser.add_argument("--history_type", type=str, default="action_history", help="Use action to represent history steps", choices=["action_history", "thought_history", "observation_history"])
    parser.add_argument("--coordinate_type", type=str, default="qwen25", help="Type of coordinate: 'relative' or 'qwen25'", choices=["relative", "qwen25"])
    parser.add_argument("--max_image_history_length", type=int, default=3, help="The max number of images in the history.")
    parser.add_argument("--use_old_sys_prompt", action="store_true", help="Use the old system prompt for smaller models")
    
    # example config
    parser.add_argument("--domain", type=str, default="all")
    parser.add_argument(
        "--test_all_meta_path", type=str, default="evaluation_examples/test_all.json"
    )

    # logging related
    parser.add_argument("--result_dir", type=str, default="./results")
    parser.add_argument("--run_name", type=str, default=None, help="Custom run name for result folder (default: auto-generated with timestamp)")
    parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to run in parallel")  
    parser.add_argument("--log_level", type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                       default='INFO', help="Set the logging level")
    
    # provider config
    parser.add_argument(
        "--region", type=str, default="us-east-1", help="AWS region for the VM"
    )
    parser.add_argument(
        "--provider_name", type=str, default="docker", choices=["aws", "virtualbox", "vmware", "docker", "azure"], help="Provider name"
    )
    parser.add_argument(
        "--client_password", type=str, default="", help="Client password"
    )
    parser.add_argument(
        "--screen_width", type=int, default=1920, help="Screen width"
    )
    parser.add_argument(
        "--screen_height", type=int, default=1080, help="Screen height"
    )
    parser.add_argument(
        "--password", type=str, default="password", help="The password for the computer if needed"
    )
    args = parser.parse_args()
    return args


def setup_logging(args):
    """Setup logging configuration"""
    logger = logging.getLogger()
    log_level = getattr(logging, args.log_level.upper())
    logger.setLevel(log_level)

    datetime_str: str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
    
    os.makedirs("logs", exist_ok=True)

    file_handler = logging.FileHandler(
        os.path.join("logs", "evocua-{:}.log".format(datetime_str)), encoding="utf-8"
    )
    debug_handler = logging.FileHandler(
        os.path.join("logs", "evocua-debug-{:}.log".format(datetime_str)), encoding="utf-8"
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

    return logging.getLogger("desktopenv.experiment")


def distribute_tasks(test_all_meta: dict) -> List[tuple]:
    all_tasks = []
    for domain, examples in test_all_meta.items():
        for example_id in examples:
            all_tasks.append((domain, example_id))
    return all_tasks


def run_env_tasks(task_queue, args: argparse.Namespace, shared_scores: list, logger):
    active_environments = []
    env = None
    try:
        REGION = args.region
        screen_size = (args.screen_width, args.screen_height)
        snapshot_name = "init_state"
        if args.provider_name == "aws":
            from desktop_env.providers.aws.manager import IMAGE_ID_MAP
            ami_id = IMAGE_ID_MAP[REGION].get(screen_size, IMAGE_ID_MAP[REGION][(1920, 1080)])
            snapshot_name = ami_id
        env = DesktopEnv(
            path_to_vm=args.path_to_vm,
            action_space=args.action_space,
            provider_name=args.provider_name,
            region=REGION,
            snapshot_name=snapshot_name,
            screen_size=screen_size,
            headless=args.headless,
            os_type="Ubuntu",
            require_a11y_tree=args.observation_type in ["a11y_tree", "screenshot_a11y_tree", "som"],
            enable_proxy=False,
            client_password=args.client_password
        )
        active_environments.append(env)
        
        logger.info(f"Process {current_process().name} started.")
        while True:
            try:
                item = task_queue.get(timeout=5)
            except Exception:
                break
            domain, example_id = item
            try:
                config_file = os.path.join(
                    args.test_config_base_dir, f"examples/{domain}/{example_id}.json"
                )
                with open(config_file, "r", encoding="utf-8") as f:
                    example = json.load(f)
                logger.info(f"[{current_process().name}][Domain]: {domain}")
                logger.info(f"[{current_process().name}][Example ID]: {example_id}")
                logger.info(f"[{current_process().name}][Instruction]: {example['instruction']}")
                example_result_dir = os.path.join(
                    args.result_dir,
                    args.action_space,
                    args.observation_type,
                    domain,
                    example_id,
                )
                os.makedirs(example_result_dir, exist_ok=True)
                
                # Create EvoCUA agent
                agent = EvoCUAAgent(
                    model=args.model,
                    max_tokens=args.max_tokens,
                    top_p=args.top_p,
                    temperature=args.temperature,
                    action_space=args.action_space,
                    observation_type=args.observation_type,
                    cot_level=args.cot_level,
                    history_type=args.history_type,
                    screen_size=(args.screen_width, args.screen_height),
                    coordinate_type=args.coordinate_type,
                    max_image_history_length=args.max_image_history_length,
                    max_steps=args.max_steps,
                    use_old_sys_prompt=args.use_old_sys_prompt,
                    password=args.password,
                    api_base=args.api_base,
                )
                try:
                    lib_run_single.run_single_example_opencua(
                        agent,
                        env,
                        example,
                        args.max_steps,
                        example["instruction"],
                        args,
                        example_result_dir,
                        shared_scores,
                    )
                except Exception as e:
                    import traceback
                    logger.error(f"Exception in {current_process().name} {domain}/{example_id}: {e}")
                    logger.error(traceback.format_exc())
                    try:
                        env.controller.end_recording(
                            os.path.join(example_result_dir, "recording.mp4")
                        )
                    except Exception as rec_e:
                        logger.error(f"Failed to end recording: {rec_e}")
                    with open(os.path.join(example_result_dir, "traj.jsonl"), "a") as f:
                        f.write(
                            json.dumps(
                                {"Error": f"{domain}/{example_id} - {e}"}
                            )
                        )
                        f.write("\n")
            except Exception as e:
                logger.error(f"Task-level error in {current_process().name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Process-level error in {current_process().name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info(f"{current_process().name} cleaning up environment...")
        try:
            if env:
                env.close()
                logger.info(f"{current_process().name} environment closed successfully")
        except Exception as e:
            logger.error(f"{current_process().name} error during environment cleanup: {e}")


def signal_handler(signum, frame):
    """Handle termination signals (SIGINT, SIGTERM) to gracefully shutdown environments."""
    global is_terminating, active_environments, processes
    
    if is_terminating:
        return
    
    is_terminating = True
    print(f"Received signal {signum}. Gracefully shutting down...")
    
    for env in active_environments:
        try:
            print(f"Closing environment...")
            env.close()
            print(f"Environment closed successfully")
        except Exception as e:
            print(f"Error closing environment: {e}")
    
    for p in processes:
        if p.is_alive():
            try:
                print(f"Sending termination signal to process {p.name}...")
                p.terminate()
            except Exception as e:
                print(f"Error sending termination signal to process: {e}")
    
    time.sleep(1)
    
    for p in processes:
        if p.is_alive():
            try:
                print(f"Forcefully terminating process {p.name}...")
                os.kill(p.pid, signal.SIGKILL)
            except Exception as e:
                print(f"Error forcefully terminating process: {e}")
    
    print("Shutdown complete. Exiting.")
    sys.exit(0)


def test(args: argparse.Namespace, test_all_meta: dict, logger) -> None:
    global processes
    logger.info("Args: %s", args)
    all_tasks = distribute_tasks(test_all_meta)
    logger.info(f"Total tasks: {len(all_tasks)}")
    with Manager() as manager:
        shared_scores = manager.list()
        task_queue = manager.Queue()
        for item in all_tasks:
            task_queue.put(item)
        num_envs = args.num_envs
        processes = []
        for i in range(num_envs):
            p = Process(
                target=run_env_tasks,
                args=(task_queue, args, shared_scores, logger),
                name=f"EnvProcess-{i+1}"
            )
            p.daemon = True
            p.start()
            processes.append(p)
            logger.info(f"Started process {p.name} with PID {p.pid}")
        try:
            while True:
                alive_count = 0
                for idx, p in enumerate(processes):
                    if not p.is_alive():
                        logger.warning(f"Process {p.name} died, restarting...")
                        new_p = Process(
                            target=run_env_tasks,
                            args=(task_queue, args, shared_scores, logger),
                            name=f"EnvProcess-Restart-{idx+1}"
                        )
                        new_p.daemon = True
                        new_p.start()
                        processes[idx] = new_p
                        logger.info(f"Restarted process {new_p.name} with PID {new_p.pid}")
                    else:
                        alive_count += 1
                if task_queue.empty():
                    logger.info("All tasks finished.")
                    break
                if alive_count == 0:
                    logger.error("All processes died, exiting.")
                    break
                time.sleep(5)
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            logger.info("Main process received KeyboardInterrupt. Initiating graceful shutdown...")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while waiting for processes: {e}", exc_info=True)
            for p in processes:
                if p.is_alive():
                    try:
                        logger.info(f"Terminating process {p.name} due to error...")
                        p.terminate()
                    except Exception as term_e:
                        logger.error(f"Error terminating process {p.name}: {term_e}")
            raise
        scores = list(shared_scores)
    logger.info(f"Average score: {sum(scores) / len(scores) if scores else 0}")


def get_unfinished(action_space, observation_type, result_dir, total_file_json):
    target_dir = os.path.join(result_dir, action_space, observation_type)

    if not os.path.exists(target_dir):
        return total_file_json

    finished = {}
    for domain in os.listdir(target_dir):
        finished[domain] = []
        domain_path = os.path.join(target_dir, domain)
        if os.path.isdir(domain_path):
            for example_id in os.listdir(domain_path):
                if example_id == "onboard":
                    continue
                example_path = os.path.join(domain_path, example_id)
                if os.path.isdir(example_path):
                    if "result.txt" not in os.listdir(example_path):
                        for file in os.listdir(example_path):
                            os.remove(os.path.join(example_path, file))
                    else:
                        finished[domain].append(example_id)

    if not finished:
        return total_file_json

    for domain, examples in finished.items():
        if domain in total_file_json:
            total_file_json[domain] = [
                x for x in total_file_json[domain] if x not in examples
            ]

    return total_file_json


def get_result(action_space, observation_type, result_dir, total_file_json):
    target_dir = os.path.join(result_dir, action_space, observation_type)
    if not os.path.exists(target_dir):
        print("New experiment, no result yet.")
        return None

    all_result = []

    for domain in os.listdir(target_dir):
        domain_path = os.path.join(target_dir, domain)
        if os.path.isdir(domain_path):
            for example_id in os.listdir(domain_path):
                example_path = os.path.join(domain_path, example_id)
                if os.path.isdir(example_path):
                    if "result.txt" in os.listdir(example_path):
                        try:
                            all_result.append(
                                float(
                                    open(
                                        os.path.join(example_path, "result.txt"), "r"
                                    ).read()
                                )
                            )
                        except:
                            all_result.append(0.0)

    if not all_result:
        print("New experiment, no result yet.")
        return None
    else:
        print("Current Success Rate:", sum(all_result) / len(all_result) * 100, "%")
        return all_result


if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Register signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        args = config()
        logger = setup_logging(args)
        
        # 设置结果目录名称
        if args.run_name:
            args.result_dir = os.path.join(args.result_dir, args.run_name)
        else:
            run_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_suffix = f"{run_date}_envs{args.num_envs}_steps{args.max_steps}"
            args.result_dir = os.path.join(args.result_dir, f"{args.model}_{run_suffix}")
        logger.info(f"Results will be saved to: {args.result_dir}")
        
        # save args to json
        path_to_args = os.path.join(
            args.result_dir,
            args.action_space,
            args.observation_type,
            "args.json",
        )
        os.makedirs(os.path.dirname(path_to_args), exist_ok=True)
        with open(path_to_args, "w", encoding="utf-8") as f:
            json.dump(vars(args), f, indent=4)

        with open(args.test_all_meta_path, "r", encoding="utf-8") as f:
            test_all_meta = json.load(f)

        if args.domain != "all":
            test_all_meta = {args.domain: test_all_meta[args.domain]}

        test_file_list = get_unfinished(
            args.action_space,
            args.observation_type,
            args.result_dir,
            test_all_meta,
        )
        left_info = ""
        for domain in test_file_list:
            left_info += f"{domain}: {len(test_file_list[domain])}\n"
        logger.info(f"Left tasks:\n{left_info}")

        get_result(
            args.action_space,
            args.observation_type,
            args.result_dir,
            test_all_meta,
        )
        test(args, test_file_list, logger)
    except KeyboardInterrupt:
        print("Main process received KeyboardInterrupt.")
    except Exception as e:
        print(f"Unexpected error in main process: {e}")
        import traceback
        traceback.print_exc()
        signal_handler(signal.SIGTERM, None)
    finally:
        print("Main process final cleanup...")
        for env in active_environments:
            if env is not None:
                try:
                    print(f"Closing environment in final cleanup...")
                    env.close()
                    print(f"Environment closed successfully in final cleanup")
                except Exception as e:
                    print(f"Error during final environment cleanup: {e}")
        
        for p in processes:
            if p is not None and p.is_alive():
                try:
                    print(f"Terminating process {p.name}...")
                    p.terminate()
                except Exception as e:
                    print(f"Error terminating process: {e}")
        
        time.sleep(1)
        
        for p in processes:
            if p is not None and p.is_alive():
                try:
                    print(f"Force killing process {p.name}...")
                    os.kill(p.pid, signal.SIGKILL)
                    print(f"Process {p.name} force killed")
                except Exception as e:
                    print(f"Error force killing process: {e}")
