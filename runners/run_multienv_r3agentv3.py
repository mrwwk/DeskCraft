from __future__ import annotations


import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if os.getcwd() != _PROJECT_ROOT:
    os.chdir(_PROJECT_ROOT)

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
import lib_run_interactive
from desktop_env.desktop_env import DesktopEnv
from mm_agents.r3agent_v3 import R3AgentV3
from mm_agents.user_simulator import UserSimulator
# taiji_proxy 懒加载，仅 --taiji 模式下使用

SCRIPT_DIR = _PROJECT_ROOT

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
        description="Run end-to-end evaluation on the benchmark (R3AgentV3)"
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

    # agent config
    parser.add_argument("--max_trajectory_length", type=int, default=3)
    parser.add_argument(
        "--test_config_base_dir", type=str, default="evaluation_examples"
    )

    # lm config
    parser.add_argument("--model", type=str, default="qwen3-vl")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--max_tokens", type=int, default=32768)
    parser.add_argument("--stop_token", type=str, default=None)
    parser.add_argument(
        "--coord",
        type=str,
        choices=["absolute", "relative"],
        default="relative",
        help="Coordinate system for agent outputs (absolute or relative)",
    )
    parser.add_argument(
        "--add_thought_prefix",
        action="store_true",
        help="Add thought prefix to the response",
    )
    parser.add_argument("--history_n", type=int, default=4, help="Number of history messages to include in the prompt")
    parser.add_argument(
        "--prompt_type",
        type=str,
        choices=["l1", "l2", "l3"],
        default="l1",
        help="Prompt type",
    )
    parser.add_argument("--include_observation_in_history", action="store_true", help="Include observation in history")
    parser.add_argument("--include_thinking_in_history", action="store_true", help="Include thinking in history")

    # example config
    parser.add_argument("--domain", type=str, default="all")
    parser.add_argument(
        "--test_all_meta_path", type=str, default="evaluation_examples/test_nogdrive.json"
    )

    # logging related
    parser.add_argument("--result_dir", type=str, default="./results")
    parser.add_argument("--run_name", type=str, default=None,
                        help="Custom folder name under result_dir. If set, results go to result_dir/run_name.")
    parser.add_argument(
        "--num_envs", type=int, default=1, help="Number of environments to run in parallel"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )

    # provider config
    parser.add_argument(
        "--region", type=str, default="us-east-1", help="AWS region for the VM"
    )
    parser.add_argument(
        "--provider_name",
        type=str,
        default="docker",
        choices=["aws", "virtualbox", "vmware", "docker", "azure", "aliyun"],
        help="Provider name",
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
        "--no-taiji", action="store_false", dest="taiji", default=True,
        help="Disable taiji platform / proxy (default: taiji enabled)."
    )

    # User simulator config (for interactive tasks)
    parser.add_argument("--user_model", type=str, default="gpt-4o",
                        help="Model name for user simulator")
    parser.add_argument("--user_api_key", type=str, default=None,
                        help="API key for user simulator LLM service")
    parser.add_argument("--user_base_url", type=str, default="https://api.openai.com/v1",
                        help="Base URL for user simulator API")
    parser.add_argument("--user_temperature", type=float, default=0.7,
                        help="Temperature for user simulator responses")

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
        os.path.join("logs", "r3agentv3-{:}.log".format(datetime_str)), encoding="utf-8"
    )
    debug_handler = logging.FileHandler(
        os.path.join("logs", "r3agentv3-debug-{:}.log".format(datetime_str)), encoding="utf-8"
    )
    stdout_handler = logging.StreamHandler(sys.stdout)

    file_handler.setLevel(logging.INFO)
    debug_handler.setLevel(logging.DEBUG)
    stdout_handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt=(
            "\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s "
            "\x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] "
            "\x1b[0m%(message)s"
        )
    )
    file_handler.setFormatter(formatter)
    debug_handler.setFormatter(formatter)
    stdout_handler.setFormatter(formatter)

    stdout_handler.addFilter(logging.Filter("desktopenv"))

    logger.addHandler(file_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(stdout_handler)

    return logging.getLogger("desktopenv.experiment")


def resolve_config_file(test_config_base_dir: str, domain: str, example_id: str) -> str:
    """Support both evaluation_examples/examples/<domain>/<id>.json and <base>/<domain>/<id>.json."""
    if not os.path.isabs(test_config_base_dir):
        test_config_base_dir = os.path.join(SCRIPT_DIR, test_config_base_dir)
    candidate_paths = [
        os.path.join(test_config_base_dir, "examples", domain, f"{example_id}.json"),
        os.path.join(test_config_base_dir, domain, f"{example_id}.json"),
    ]
    for candidate_path in candidate_paths:
        if os.path.exists(candidate_path):
            return candidate_path
    return candidate_paths[0]


def distribute_tasks(test_all_meta: dict) -> List[tuple]:
    all_tasks = []
    for domain, examples in test_all_meta.items():
        for example_id in examples:
            all_tasks.append((domain, example_id))
    return all_tasks


def run_env_tasks(task_queue, args: argparse.Namespace, shared_scores: list):
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
            require_a11y_tree=args.observation_type in [
                "a11y_tree",
                "screenshot_a11y_tree",
                "som",
            ],
            enable_proxy=args.taiji,
            client_password=args.client_password,
        )
        active_environments.append(env)
        agent = R3AgentV3(
            model=args.model,
            prompt_type=args.prompt_type,
            include_observation_in_history=args.include_observation_in_history,
            include_thinking_in_history=args.include_thinking_in_history,
            history_n=args.history_n,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
            temperature=args.temperature,
            action_space=args.action_space,
            coordinate_type=args.coord,
            add_thought_prefix=args.add_thought_prefix,
            api_backend="openai",
        )
        logger.info(f"Process {current_process().name} started.")
        while True:
            try:
                item = task_queue.get(timeout=5)
            except Exception:
                break
            domain, example_id = item
            try:
                config_file = resolve_config_file(
                    args.test_config_base_dir, domain, example_id
                )
                with open(config_file, "r", encoding="utf-8") as f:
                    example = json.load(f)
                logger.info(f"[{current_process().name}][Domain]: {domain}")
                logger.info(f"[{current_process().name}][Example ID]: {example_id}")

                is_interactive = example.get("interactive", False)
                logger.info(f"[{current_process().name}][Interactive]: {is_interactive}")
                if is_interactive:
                    logger.info(f"[{current_process().name}][Phases]: {len(example.get('phases', []))}")
                else:
                    logger.info(f"[{current_process().name}][Instruction]: {example.get('instruction', 'N/A')}")

                example_result_dir = os.path.join(
                    args.result_dir,
                    args.action_space,
                    args.observation_type,
                    args.model,
                    domain,
                    example_id,
                )
                os.makedirs(example_result_dir, exist_ok=True)
                try:
                    if is_interactive:
                        # Interactive task → create UserSimulator, use interactive runner
                        user_sim = UserSimulator(
                            api_key=args.user_api_key or os.environ.get("USER_SIM_API_KEY", ""),
                            base_url=args.user_base_url,
                            model=args.user_model,
                            scenario_config=example,
                            temperature=args.user_temperature,
                        )
                        initial_instruction = example.get(
                            "instruction",
                            example.get("phases", [{}])[0].get("instruction", "")
                        )
                        lib_run_interactive.run_interactive_example(
                            agent,
                            env,
                            user_sim,
                            example,
                            args.max_steps,
                            initial_instruction,
                            args,
                            example_result_dir,
                            shared_scores,
                        )
                    else:
                        # Non-interactive task → standard single-instruction runner
                        lib_run_single.run_single_example(
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
                        f.write(json.dumps({"Error": f"{domain}/{example_id} - {e}"}))
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
    global is_terminating, active_environments, processes
    if is_terminating:
        return
    is_terminating = True
    logger.info(f"Received signal {signum}. Gracefully shutting down...")
    for env in active_environments:
        try:
            logger.info(f"Closing environment...")
            env.close()
            logger.info(f"Environment closed successfully")
        except Exception as e:
            logger.error(f"Error closing environment: {e}")
    for p in processes:
        if p.is_alive():
            try:
                logger.info(f"Sending termination signal to process {p.name}...")
                p.terminate()
            except Exception as e:
                logger.error(f"Error sending termination signal to process: {e}")
    time.sleep(1)
    for p in processes:
        if p.is_alive():
            try:
                logger.info(f"Forcefully terminating process {p.name}...")
                import signal as sig
                os.kill(p.pid, sig.SIGKILL)
            except Exception as e:
                logger.error(f"Error forcefully terminating process: {e}")
    logger.info("Shutdown complete. Exiting.")
    sys.exit(0)


def test(args: argparse.Namespace, test_all_meta: dict) -> None:
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
                args=(task_queue, args, shared_scores),
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
                            args=(task_queue, args, shared_scores),
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


def get_unfinished(
    action_space, use_model, observation_type, result_dir, total_file_json
):
    target_dir = os.path.join(result_dir, action_space, observation_type, use_model)

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


def get_result(action_space, use_model, observation_type, result_dir, total_file_json):
    target_dir = os.path.join(result_dir, action_space, observation_type, use_model)
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
                            value_str = open(
                                os.path.join(example_path, "result.txt"), "r"
                            ).read()
                            all_result.append(float(value_str))
                        except Exception:
                            all_result.append(0.0)

    if not all_result:
        print("New experiment, no result yet.")
        return None
    else:
        print("Current Success Rate:", sum(all_result) / len(all_result) * 100, "%")
        return all_result


if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        args = config()
        logger = setup_logging(args)

        # 统一转换为绝对路径（与 evocua 一致）
        if not os.path.isabs(args.test_config_base_dir):
            args.test_config_base_dir = os.path.join(SCRIPT_DIR, args.test_config_base_dir)
        if not os.path.isabs(args.test_all_meta_path):
            args.test_all_meta_path = os.path.join(SCRIPT_DIR, args.test_all_meta_path)

        # run_name → result_dir 解析（与 evocua 一致）
        if args.run_name:
            args.result_dir = os.path.join(args.result_dir, args.run_name)

        logger.info(f"Results will be saved to: {args.result_dir}")

        path_to_args = os.path.join(
            args.result_dir,
            args.action_space,
            args.observation_type,
            args.model,
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
            args.model,
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
            args.model,
            args.observation_type,
            args.result_dir,
            test_all_meta,
        )
        if args.taiji:
            from utils.taiji_proxy import initialize_taiji_proxy_pool
            # 根据REGION设置对应的代理配置
            if args.region in ["wzj"]:
                # wzj地区使用star-proxy
                initialize_taiji_proxy_pool(host="star-proxy.oa.com", port=3128, protocol="http")
            elif args.region in ["gz", "zw"]:
                # gz/zw地区使用hk-mmhttpproxy
                initialize_taiji_proxy_pool(host="hk-mmhttpproxy.woa.com", port=11113, protocol="http")
            else:
                # 其他地区使用默认配置
                initialize_taiji_proxy_pool(host="star-proxy.oa.com", port=3128, protocol="http")
        else:
            logger.info("No taiji platform / proxy, skipping proxy initialization")
            
        test(args, test_file_list)
    except KeyboardInterrupt:
        logger.info("Main process received KeyboardInterrupt.")
    except Exception as e:
        logger.error(f"Unexpected error in main process: {e}", exc_info=True)
        signal_handler(signal.SIGTERM, None)
    finally:
        logger.info("Main process final cleanup...")
        for env in active_environments:
            if env is not None:
                try:
                    logger.info("Closing environment in final cleanup...")
                    env.close()
                    logger.info("Environment closed successfully in final cleanup")
                except Exception as e:
                    logger.error(f"Error during final environment cleanup: {e}")
        for p in processes:
            if p is not None and p.is_alive():
                try:
                    logger.info(f"Terminating process {p.name}...")
                    p.terminate()
                except Exception as e:
                    logger.error(f"Error terminating process: {e}")
        time.sleep(1)
        for p in processes:
            if p is not None and p.is_alive():
                try:
                    logger.info(f"Force killing process {p.name}...")
                    os.kill(p.pid, signal.SIGKILL)
                    logger.info(f"Process {p.name} force killed")
                except Exception as e:
                    logger.error(f"Error force killing process: {e}")
