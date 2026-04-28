from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import shutil
import signal
import sys
import time
from multiprocessing import Manager, Process, current_process
from typing import Dict, List

# Project root: <repo>/scripts/python/<this file>  →  ../..
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import lib_run_interactive
from desktop_env.desktop_env import DesktopEnv
from mm_agents.qwen3vl_agent import Qwen3VLAgent
from mm_agents.user_simulator import UserSimulator
from utils.taiji_proxy import initialize_taiji_proxy_pool


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

active_environments = []
processes = []
is_terminating = False


if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run interactive multi-env evaluation with Qwen3-VL XML toolcalls."
    )

    parser.add_argument("--path_to_vm", type=str, default=None)
    parser.add_argument("--headless", action="store_true", help="Run in headless machine")
    parser.add_argument("--action_space", type=str, default="pyautogui")
    parser.add_argument(
        "--observation_type",
        choices=["screenshot", "a11y_tree", "screenshot_a11y_tree", "som"],
        default="screenshot",
    )
    parser.add_argument("--sleep_after_execution", type=float, default=5.0)
    parser.add_argument("--max_steps", type=int, default=100)

    parser.add_argument("--test_config_base_dir", type=str, default="evaluation_examples/example_final")
    parser.add_argument("--history_n", type=int, default=4)
    parser.add_argument(
        "--coord",
        type=str,
        choices=["absolute", "relative"],
        default="relative",
        help="Coordinate system for agent outputs",
    )
    parser.add_argument("--add_thought_prefix", action="store_true")
    parser.add_argument("--platform", type=str, default="ubuntu")
    parser.add_argument(
        "--api_backend",
        type=str,
        choices=["openai", "dashscope"],
        default="openai",
    )
    parser.add_argument("--enable_thinking", action="store_true",
                        help="Enable Qwen3 thinking mode (requires vLLM --reasoning-parser qwen3)")
    parser.add_argument("--thinking_budget", type=int, default=32768,
                        help="Thinking token budget (dashscope path only)")

    parser.add_argument("--model", type=str, default="qwen3-vl")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--max_tokens", type=int, default=32768)
    parser.add_argument("--base_url", type=str, default=None,
                        help="Override OPENAI_BASE_URL for the Qwen3-VL agent's vLLM endpoint")
    parser.add_argument("--api_key", type=str, default=None,
                        help="Override OPENAI_API_KEY for the Qwen3-VL agent's vLLM endpoint")

    parser.add_argument("--user_model", type=str, default="KimiK25",
                        help="Model name for user simulator")
    parser.add_argument("--user_api_key", type=str, default="EMPTY",
                        help="API key for user simulator LLM service")
    parser.add_argument("--user_base_url", type=str,
                        default="http://28.12.129.142:8000/v1",
                        help="Base URL for user simulator API")
    parser.add_argument("--user_temperature", type=float, default=0.7,
                        help="Temperature for user simulator responses")

    parser.add_argument("--domain", type=str, default="all")
    parser.add_argument(
        "--test_all_meta_path",
        type=str,
        default="evaluation_examples/example_final_interactive_all.json",
    )

    parser.add_argument("--result_dir", type=str, default="./results")
    parser.add_argument("--simple_path", action="store_true")
    parser.add_argument("--num_envs", type=int, default=1)
    parser.add_argument(
        "--log_level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )

    parser.add_argument("--region", type=str, default="us-east-1")
    parser.add_argument(
        "--provider_name",
        type=str,
        default="docker",
        choices=["aws", "virtualbox", "vmware", "docker", "azure", "aliyun"],
    )
    parser.add_argument("--client_password", type=str, default="")
    parser.add_argument("--screen_width", type=int, default=1920)
    parser.add_argument("--screen_height", type=int, default=1080)
    parser.add_argument("--password", type=str, default="password")
    parser.add_argument("--run_name", type=str, default=None)
    parser.add_argument(
        "--no-taiji",
        action="store_false",
        dest="taiji",
        default=True,
        help="Disable taiji platform / proxy (default: taiji enabled).",
    )

    return parser.parse_args()


args = config()

root_logger = logging.getLogger()
log_level = getattr(logging, args.log_level.upper())
root_logger.setLevel(log_level)

datetime_str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler(
    os.path.join("logs", f"qwen3vl-interactive-{datetime_str}.log"), encoding="utf-8"
)
stdout_handler = logging.StreamHandler(sys.stdout)
file_handler.setLevel(logging.INFO)
stdout_handler.setLevel(log_level)
formatter = logging.Formatter(
    fmt=(
        "\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s "
        "\x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] "
        "\x1b[0m%(message)s"
    )
)
file_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)
root_logger.addHandler(stdout_handler)

logger = logging.getLogger("desktopenv.experiment")


def distribute_tasks(test_all_meta: Dict[str, List[str]]) -> List[tuple]:
    all_tasks = []
    for domain, examples in test_all_meta.items():
        for example_id in examples:
            all_tasks.append((domain, example_id))
    return all_tasks


def resolve_config_file(test_config_base_dir: str, domain: str, example_id: str) -> str:
    if not os.path.isabs(test_config_base_dir):
        test_config_base_dir = os.path.abspath(
            os.path.join(SCRIPT_DIR, "../..", test_config_base_dir)
        )

    candidate_paths = [
        os.path.join(test_config_base_dir, "examples", domain, f"{example_id}.json"),
        os.path.join(test_config_base_dir, domain, f"{example_id}.json"),
    ]
    for candidate_path in candidate_paths:
        if os.path.exists(candidate_path):
            return candidate_path

    search_roots = []
    examples_root = os.path.join(test_config_base_dir, "examples")
    if os.path.isdir(examples_root):
        search_roots.append(examples_root)
    if os.path.isdir(test_config_base_dir):
        search_roots.append(test_config_base_dir)

    target = f"{example_id}.json"
    for search_root in search_roots:
        for root, _, files in os.walk(search_root):
            if target in files:
                return os.path.join(root, target)

    raise FileNotFoundError(
        f"Cannot locate task config for domain={domain}, example_id={example_id}. "
        f"Checked: {[os.path.abspath(p) for p in candidate_paths]}"
    )


def build_example_result_dir(run_args: argparse.Namespace, domain: str, example_id: str) -> str:
    if run_args.simple_path:
        return os.path.join(run_args.result_dir, domain, example_id)
    return os.path.join(
        run_args.result_dir,
        run_args.action_space,
        run_args.observation_type,
        run_args.model,
        domain,
        example_id,
    )


def run_single_example_noninteractive(
    agent, env, example, max_steps, instruction, run_args, example_result_dir, shared_scores
):
    """Non-interactive fallback: mirrors the base qwen3vl predict/step loop."""
    runtime_logger = logging.getLogger(f"desktopenv.example.{example['id']}")
    runtime_logger.setLevel(logging.DEBUG)
    runtime_logger.addHandler(
        logging.FileHandler(os.path.join(example_result_dir, "runtime.log"))
    )

    env.reset(task_config=example)
    try:
        agent.reset(runtime_logger, vm_ip=env.vm_ip)
    except Exception:
        agent.reset(runtime_logger)

    time.sleep(60)
    obs = env._get_obs()
    done = False
    step_idx = 0

    env.controller.start_recording()

    while not done and step_idx < max_steps:
        response, actions = agent.predict(instruction, obs)

        for action in actions:
            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
            logger.info("Step %d: %s", step_idx + 1, action)
            obs, reward, done, info = env.step(action, run_args.sleep_after_execution)

            with open(
                os.path.join(example_result_dir, f"step_{step_idx + 1}_{action_timestamp}.png"),
                "wb",
            ) as _f:
                _f.write(obs["screenshot"])

            with open(os.path.join(example_result_dir, "traj.jsonl"), "a", encoding="utf-8") as _f:
                _f.write(json.dumps({
                    "step_num": step_idx + 1,
                    "action_timestamp": action_timestamp,
                    "action": action,
                    "response": response,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "screenshot_file": f"step_{step_idx + 1}_{action_timestamp}.png",
                }, ensure_ascii=False))
                _f.write("\n")

            if done:
                logger.info("The episode is done.")
                break

        step_idx += 1

    time.sleep(20)
    result = env.evaluate()
    logger.info("Result: %.2f", result)
    shared_scores.append(result)

    with open(os.path.join(example_result_dir, "result.txt"), "w", encoding="utf-8") as _f:
        _f.write(f"{result}\n")

    env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))


def run_env_tasks(task_queue, run_args: argparse.Namespace, shared_scores: list):
    env = None
    try:
        region = run_args.region
        screen_size = (run_args.screen_width, run_args.screen_height)
        snapshot_name = "init_state"
        if run_args.provider_name == "aws":
            from desktop_env.providers.aws.manager import IMAGE_ID_MAP

            snapshot_name = IMAGE_ID_MAP[region].get(screen_size, IMAGE_ID_MAP[region][(1920, 1080)])

        env = DesktopEnv(
            path_to_vm=run_args.path_to_vm,
            action_space=run_args.action_space,
            provider_name=run_args.provider_name,
            region=region,
            snapshot_name=snapshot_name,
            screen_size=screen_size,
            headless=run_args.headless,
            os_type="Ubuntu",
            require_a11y_tree=run_args.observation_type
            in ["a11y_tree", "screenshot_a11y_tree", "som"],
            enable_proxy=run_args.taiji,
            client_password=run_args.client_password,
        )
        active_environments.append(env)

        agent = Qwen3VLAgent(
            platform=run_args.platform,
            model=run_args.model,
            max_tokens=run_args.max_tokens,
            top_p=run_args.top_p,
            temperature=run_args.temperature,
            action_space=run_args.action_space,
            observation_type=run_args.observation_type,
            history_n=run_args.history_n,
            add_thought_prefix=run_args.add_thought_prefix,
            coordinate_type=run_args.coord,
            api_backend=run_args.api_backend,
            enable_thinking=run_args.enable_thinking,
            thinking_budget=run_args.thinking_budget,
        )

        logger.info("Process %s started with Qwen3VLAgent (interactive).", current_process().name)

        while True:
            try:
                item = task_queue.get(timeout=5)
            except Exception:
                break

            domain, example_id = item
            try:
                config_file = resolve_config_file(run_args.test_config_base_dir, domain, example_id)
                with open(config_file, "r", encoding="utf-8") as f:
                    example = json.load(f)

                is_interactive = example.get("interactive", False)
                logger.info("[%s][Domain]: %s", current_process().name, domain)
                logger.info("[%s][Example ID]: %s", current_process().name, example_id)
                logger.info("[%s][Interactive]: %s", current_process().name, is_interactive)
                if is_interactive:
                    logger.info(
                        "[%s][Phases]: %s",
                        current_process().name,
                        len(example.get("phases", [])),
                    )
                else:
                    logger.info(
                        "[%s][Instruction]: %s",
                        current_process().name,
                        example.get("instruction", "N/A"),
                    )

                example_result_dir = build_example_result_dir(run_args, domain, example_id)
                os.makedirs(example_result_dir, exist_ok=True)

                try:
                    if is_interactive:
                        user_sim = UserSimulator(
                            api_key=run_args.user_api_key
                            or os.environ.get("USER_SIM_API_KEY", ""),
                            base_url=run_args.user_base_url,
                            model=run_args.user_model,
                            scenario_config=example,
                            temperature=run_args.user_temperature,
                        )
                        initial_instruction = example.get(
                            "instruction",
                            example.get("phases", [{}])[0].get("instruction", ""),
                        )
                        lib_run_interactive.run_interactive_example(
                            agent,
                            env,
                            user_sim,
                            example,
                            run_args.max_steps,
                            initial_instruction,
                            run_args,
                            example_result_dir,
                            shared_scores,
                        )
                    else:
                        run_single_example_noninteractive(
                            agent,
                            env,
                            example,
                            run_args.max_steps,
                            example["instruction"],
                            run_args,
                            example_result_dir,
                            shared_scores,
                        )
                except Exception as exc:
                    import traceback

                    logger.error(
                        "Exception in %s %s/%s: %s",
                        current_process().name,
                        domain,
                        example_id,
                        exc,
                    )
                    logger.error(traceback.format_exc())
                    try:
                        env.controller.end_recording(
                            os.path.join(example_result_dir, "recording.mp4")
                        )
                    except Exception:
                        pass
                    with open(os.path.join(example_result_dir, "traj.jsonl"), "a", encoding="utf-8") as f:
                        f.write(json.dumps({"Error": f"{domain}/{example_id} - {exc}"}, ensure_ascii=False))
                        f.write("\n")
            except Exception as exc:
                import traceback

                logger.error("Task-level error in %s: %s", current_process().name, exc)
                logger.error(traceback.format_exc())
    finally:
        logger.info("%s cleaning up environment...", current_process().name)
        try:
            if env:
                env.close()
        except Exception:
            pass


def signal_handler(signum, frame):
    global is_terminating, active_environments, processes
    if is_terminating:
        return
    is_terminating = True
    logger.info("Received signal %s. Gracefully shutting down...", signum)

    for env in active_environments:
        try:
            env.close()
        except Exception:
            pass

    for process in processes:
        if process.is_alive():
            try:
                process.terminate()
            except Exception:
                pass

    time.sleep(1)
    logger.info("Shutdown complete. Exiting.")
    sys.exit(0)


def test(run_args: argparse.Namespace, test_all_meta: Dict[str, List[str]]) -> None:
    global processes

    logger.info("Args: %s", run_args)
    all_tasks = distribute_tasks(test_all_meta)
    logger.info("Total tasks: %d", len(all_tasks))

    if not all_tasks:
        logger.info("No tasks to run.")
        return

    with Manager() as manager:
        shared_scores = manager.list()
        task_queue = manager.Queue()
        for item in all_tasks:
            task_queue.put(item)

        processes = []
        for idx in range(run_args.num_envs):
            process = Process(
                target=run_env_tasks,
                args=(task_queue, run_args, shared_scores),
                name=f"EnvProcess-{idx + 1}",
            )
            process.daemon = True
            process.start()
            processes.append(process)
            logger.info("Started process %s with PID %s", process.name, process.pid)

        while True:
            alive_count = 0
            for idx, process in enumerate(processes):
                if not process.is_alive():
                    logger.warning("Process %s died, restarting...", process.name)
                    new_process = Process(
                        target=run_env_tasks,
                        args=(task_queue, run_args, shared_scores),
                        name=f"EnvProcess-Restart-{idx + 1}",
                    )
                    new_process.daemon = True
                    new_process.start()
                    processes[idx] = new_process
                    logger.info("Restarted process %s with PID %s", new_process.name, new_process.pid)
                else:
                    alive_count += 1

            if task_queue.empty():
                logger.info("All tasks finished.")
                break
            if alive_count == 0:
                logger.error("All processes died, exiting.")
                break
            time.sleep(5)

        for process in processes:
            process.join()

        scores = list(shared_scores)
        logger.info("Average score: %s", (sum(scores) / len(scores)) if scores else 0)


def get_unfinished(
    action_space: str,
    use_model: str,
    observation_type: str,
    result_dir: str,
    total_file_json: Dict[str, List[str]],
    simple_path: bool = False,
) -> Dict[str, List[str]]:
    target_dir = result_dir if simple_path else os.path.join(
        result_dir, action_space, observation_type, use_model
    )

    if not os.path.exists(target_dir):
        return total_file_json

    finished: Dict[str, List[str]] = {}
    for domain in os.listdir(target_dir):
        domain_path = os.path.join(target_dir, domain)
        if not os.path.isdir(domain_path):
            continue

        finished[domain] = []
        for example_id in os.listdir(domain_path):
            example_path = os.path.join(domain_path, example_id)
            if not os.path.isdir(example_path):
                continue
            if os.path.exists(os.path.join(example_path, "result.txt")):
                finished[domain].append(example_id)
                continue

            for item in os.listdir(example_path):
                item_path = os.path.join(example_path, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception:
                    pass

    if not finished:
        return total_file_json

    remaining = {}
    for domain, examples in total_file_json.items():
        done_ids = set(finished.get(domain, []))
        left = [example_id for example_id in examples if example_id not in done_ids]
        if left:
            remaining[domain] = left
    return remaining


def get_result(
    action_space: str,
    use_model: str,
    observation_type: str,
    result_dir: str,
    simple_path: bool = False,
):
    target_dir = result_dir if simple_path else os.path.join(
        result_dir, action_space, observation_type, use_model
    )

    if not os.path.exists(target_dir):
        print("New experiment, no result yet.")
        return None

    all_result = []
    for domain in os.listdir(target_dir):
        domain_path = os.path.join(target_dir, domain)
        if not os.path.isdir(domain_path):
            continue
        for example_id in os.listdir(domain_path):
            example_path = os.path.join(domain_path, example_id)
            if not os.path.isdir(example_path):
                continue
            result_file = os.path.join(example_path, "result.txt")
            if not os.path.exists(result_file):
                continue
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    all_result.append(float(f.read()))
            except Exception:
                all_result.append(0.0)

    if not all_result:
        print("New experiment, no result yet.")
        return None

    print("Current Success Rate:", sum(all_result) / len(all_result) * 100, "%")
    return all_result


if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.taiji:
        initialize_taiji_proxy_pool(host="hk-mmhttpproxy.woa.com", port=11113, protocol="http")
    else:
        logger.info("No taiji platform / proxy, skipping proxy initialization")

    if not os.path.isabs(args.test_config_base_dir):
        args.test_config_base_dir = os.path.abspath(
            os.path.join(SCRIPT_DIR, "../..", args.test_config_base_dir)
        )
    if not os.path.isabs(args.test_all_meta_path):
        args.test_all_meta_path = os.path.abspath(
            os.path.join(SCRIPT_DIR, "../..", args.test_all_meta_path)
        )

    if args.run_name:
        args.result_dir = os.path.join(args.result_dir, args.run_name)

    if args.simple_path:
        path_to_args = os.path.join(args.result_dir, "args.json")
    else:
        path_to_args = os.path.join(
            args.result_dir, args.action_space, args.observation_type, args.model, "args.json"
        )

    os.makedirs(os.path.dirname(path_to_args), exist_ok=True)
    with open(path_to_args, "w", encoding="utf-8") as file_obj:
        json.dump(vars(args), file_obj, indent=2, ensure_ascii=False)

    with open(args.test_all_meta_path, "r", encoding="utf-8") as file_obj:
        test_all_meta = json.load(file_obj)

    if args.domain != "all":
        test_all_meta = {args.domain: test_all_meta[args.domain]}

    test_file_list = get_unfinished(
        args.action_space,
        args.model,
        args.observation_type,
        args.result_dir,
        test_all_meta,
        simple_path=args.simple_path,
    )

    left_info = ""
    for domain, examples in test_file_list.items():
        left_info += f"{domain}: {len(examples)}\n"
    logger.info("Left tasks:\n%s", left_info)
    get_result(args.action_space, args.model, args.observation_type, args.result_dir,
               simple_path=args.simple_path)

    test(args, test_file_list)
