from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import signal
import sys
import time
from multiprocessing import Manager, Process, current_process
from typing import List

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import lib_run_interactive
import lib_run_single
from desktop_env.desktop_env import DesktopEnv
from mm_agents.gpt54_agent import GPT54Agent
from mm_agents.user_simulator import UserSimulator


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
active_environments = []
processes = []
is_terminating = False

if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end evaluation on OSWorld with GPT-5.4 computer use and interactive support"
    )

    parser.add_argument("--path_to_vm", type=str, default=None)
    parser.add_argument("--headless", action="store_true", help="Run in headless machine")
    parser.add_argument("--action_space", type=str, default="pyautogui", help="Action type")
    parser.add_argument(
        "--observation_type",
        choices=["screenshot"],
        default="screenshot",
        help="Observation type",
    )
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)
    parser.add_argument("--max_steps", type=int, default=15)

    parser.add_argument("--max_trajectory_length", type=int, default=3)
    parser.add_argument("--test_config_base_dir", type=str, default="evaluation_examples")

    parser.add_argument("--model", type=str, default="api_azure_openai_gpt-5.4")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=None,
        help="Optional max_output_tokens override. Default is unset.",
    )
    parser.add_argument(
        "--reasoning_effort",
        type=str,
        choices=["none", "low", "medium", "high", "xhigh"],
        default="low",
    )
    parser.add_argument("--stop_token", type=str, default=None)

    parser.add_argument(
        "--user_model",
        type=str,
        default="gpt-4o",
        help="Model name for user simulator",
    )
    parser.add_argument(
        "--user_api_key",
        type=str,
        default=None,
        help="API key for user simulator LLM service",
    )
    parser.add_argument(
        "--user_base_url",
        type=str,
        default="https://api.openai.com/v1",
        help="Base URL for user simulator API",
    )
    parser.add_argument(
        "--user_temperature",
        type=float,
        default=0.7,
        help="Temperature for user simulator responses",
    )

    parser.add_argument("--domain", type=str, default="all")
    parser.add_argument(
        "--test_all_meta_path",
        type=str,
        default="evaluation_examples/interactive_all.json",
    )

    parser.add_argument("--result_dir", type=str, default="./results")
    parser.add_argument("--run_name", type=str, default=None)
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
    parser.add_argument("--region", type=str, default="us-east-1", help="AWS region for the VM")
    parser.add_argument(
        "--provider_name",
        type=str,
        default="docker",
        choices=["aws", "virtualbox", "vmware", "docker", "azure"],
        help="Provider name",
    )
    parser.add_argument("--client_password", type=str, default="", help="Client password")
    parser.add_argument("--screen_width", type=int, default=1920, help="Screen width")
    parser.add_argument("--screen_height", type=int, default=1080, help="Screen height")
    return parser.parse_args()


args = config()

logger = logging.getLogger()
log_level = getattr(logging, args.log_level.upper())
logger.setLevel(log_level)

datetime_str = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")

os.makedirs("logs", exist_ok=True)

file_handler = logging.FileHandler(
    os.path.join("logs", f"gpt54-interactive-{datetime_str}.log"), encoding="utf-8"
)
debug_handler = logging.FileHandler(
    os.path.join("logs", f"gpt54-interactive-debug-{datetime_str}.log"), encoding="utf-8"
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

logger = logging.getLogger("desktopenv.experiment")


def distribute_tasks(test_all_meta: dict) -> List[tuple]:
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

    exact_filename = f"{example_id}.json"
    suffix_filename = f"{example_id}.json"

    for search_root in search_roots:
        for root, _, files in os.walk(search_root):
            if exact_filename in files:
                return os.path.join(root, exact_filename)

    for search_root in search_roots:
        for root, _, files in os.walk(search_root):
            for file_name in files:
                if file_name.endswith(suffix_filename):
                    return os.path.join(root, file_name)

    raise FileNotFoundError(
        "Unable to locate task config for "
        f"domain={domain}, example_id={example_id}. Checked exact paths: "
        + ", ".join(os.path.abspath(path) for path in candidate_paths)
        + "; searched under: "
        + ", ".join(os.path.abspath(path) for path in search_roots)
    )


def run_env_tasks(task_queue, args: argparse.Namespace, shared_scores: list):
    active_environments = []
    env = None
    try:
        screen_size = (args.screen_width, args.screen_height)
        env_kwargs = dict(
            path_to_vm=args.path_to_vm,
            action_space=args.action_space,
            provider_name=args.provider_name,
            screen_size=screen_size,
            headless=args.headless,
            os_type="Ubuntu",
            require_a11y_tree=False,
            enable_proxy=True,
            client_password=args.client_password,
        )

        if args.provider_name == "aws":
            from desktop_env.providers.aws.manager import IMAGE_ID_MAP

            region = args.region
            ami_id = IMAGE_ID_MAP[region].get(screen_size, IMAGE_ID_MAP[region][(1920, 1080)])
            env_kwargs["region"] = region
            env_kwargs["snapshot_name"] = ami_id

        env = DesktopEnv(**env_kwargs)
        active_environments.append(env)
        agent = GPT54Agent(
            env=env,
            model=args.model,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
            temperature=args.temperature,
            action_space=args.action_space,
            observation_type=args.observation_type,
            max_trajectory_length=args.max_trajectory_length,
            client_password=args.client_password,
            provider_name=args.provider_name,
            screen_width=args.screen_width,
            screen_height=args.screen_height,
            sleep_after_execution=args.sleep_after_execution,
            reasoning_effort=args.reasoning_effort,
        )
        logger.info("Process %s started.", current_process().name)

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
                        user_sim = UserSimulator(
                            api_key=args.user_api_key or os.environ.get("USER_SIM_API_KEY", ""),
                            base_url=args.user_base_url,
                            model=args.user_model,
                            scenario_config=example,
                            temperature=args.user_temperature,
                        )
                        initial_instruction = example.get(
                            "instruction",
                            example.get("phases", [{}])[0].get("instruction", ""),
                        )
                        lib_run_interactive.run_interactive_example_gpt54(
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
                        lib_run_single.run_single_example_gpt54(
                            agent,
                            env,
                            example,
                            args.max_steps,
                            example["instruction"],
                            args,
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
                        if hasattr(env, "controller") and env.controller is not None:
                            env.controller.end_recording(
                                os.path.join(example_result_dir, "recording.mp4")
                            )
                    except Exception as record_exc:
                        logger.error("Failed to end recording: %s", record_exc)
                    with open(os.path.join(example_result_dir, "traj.jsonl"), "a", encoding="utf-8") as f:
                        f.write(json.dumps({"Error": f"{domain}/{example_id} - {exc}"}))
                        f.write("\n")
            except Exception as exc:
                import traceback

                logger.error("Task-level error in %s: %s", current_process().name, exc)
                logger.error(traceback.format_exc())
    except Exception as exc:
        import traceback

        logger.error("Process-level error in %s: %s", current_process().name, exc)
        logger.error(traceback.format_exc())
    finally:
        logger.info("%s cleaning up environment...", current_process().name)
        try:
            if env:
                env.close()
                logger.info("%s environment closed successfully", current_process().name)
        except Exception as exc:
            logger.error("%s error during environment cleanup: %s", current_process().name, exc)


def signal_handler(signum, frame):
    global is_terminating, active_environments, processes

    if is_terminating:
        return

    is_terminating = True
    logger.info("Received signal %s. Gracefully shutting down...", signum)

    for env in active_environments:
        try:
            env.close()
        except Exception as exc:
            logger.error("Error closing environment: %s", exc)

    for process in processes:
        if process.is_alive():
            try:
                process.terminate()
            except Exception as exc:
                logger.error("Error sending termination signal to process: %s", exc)

    time.sleep(1)

    for process in processes:
        if process.is_alive():
            try:
                import signal as os_signal

                os.kill(process.pid, os_signal.SIGKILL)
            except Exception as exc:
                logger.error("Error forcefully terminating process: %s", exc)

    logger.info("Shutdown complete. Exiting.")
    sys.exit(0)


def test(args: argparse.Namespace, test_all_meta: dict) -> None:
    global processes

    logger.info("Args: %s", args)
    all_tasks = distribute_tasks(test_all_meta)
    logger.info("Total tasks: %d", len(all_tasks))

    with Manager() as manager:
        shared_scores = manager.list()
        task_queue = manager.Queue()
        for item in all_tasks:
            task_queue.put(item)

        processes = []
        for index in range(args.num_envs):
            process = Process(
                target=run_env_tasks,
                args=(task_queue, args, shared_scores),
                name=f"EnvProcess-{index + 1}",
            )
            process.daemon = True
            process.start()
            processes.append(process)
            logger.info("Started process %s with PID %s", process.name, process.pid)

        try:
            while True:
                alive_count = 0
                for index, process in enumerate(processes):
                    if not process.is_alive():
                        logger.warning("Process %s died, restarting...", process.name)
                        new_process = Process(
                            target=run_env_tasks,
                            args=(task_queue, args, shared_scores),
                            name=f"EnvProcess-Restart-{index + 1}",
                        )
                        new_process.daemon = True
                        new_process.start()
                        processes[index] = new_process
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
        except KeyboardInterrupt:
            logger.info("Main process received KeyboardInterrupt. Initiating graceful shutdown...")
            raise
        except Exception as exc:
            logger.error("Unexpected error while waiting for processes: %s", exc, exc_info=True)
            for process in processes:
                if process.is_alive():
                    try:
                        process.terminate()
                    except Exception as term_exc:
                        logger.error("Error terminating process %s: %s", process.name, term_exc)
            raise

        scores = list(shared_scores)

    logger.info("Average score: %s", sum(scores) / len(scores) if scores else 0)


def get_unfinished(action_space, use_model, observation_type, result_dir, total_file_json):
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
                        for file_name in os.listdir(example_path):
                            file_path = os.path.join(example_path, file_name)
                            if os.path.isdir(file_path):
                                import shutil

                                shutil.rmtree(file_path)
                            else:
                                os.remove(file_path)
                    else:
                        finished[domain].append(example_id)

    if not finished:
        return total_file_json

    for domain, examples in finished.items():
        if domain in total_file_json:
            total_file_json[domain] = [
                example_id for example_id in total_file_json[domain] if example_id not in examples
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
                if os.path.isdir(example_path) and "result.txt" in os.listdir(example_path):
                    try:
                        with open(os.path.join(example_path, "result.txt"), "r", encoding="utf-8") as f:
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

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        args = config()

        from desktop_env.providers.aws.proxy_pool import get_global_proxy_pool

        proxy_pool = get_global_proxy_pool()
        proxy_pool.add_proxy(
            host="hk-mmhttpproxy.woa.com",
            port=11113,
            protocol="http",
        )

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
        else:
            run_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_suffix = f"{run_date}_envs{args.num_envs}_steps{args.max_steps}"
            args.result_dir = os.path.join(args.result_dir, f"{args.model}_{run_suffix}")
        logger.info("Results will be saved to: %s", args.result_dir)

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
        logger.info("Left tasks:\n%s", left_info)

        get_result(
            args.action_space,
            args.model,
            args.observation_type,
            args.result_dir,
            test_all_meta,
        )
        test(args, test_file_list)
    except KeyboardInterrupt:
        logger.info("Main process received KeyboardInterrupt.")
    except Exception as exc:
        logger.error("Unexpected error in main process: %s", exc, exc_info=True)
        signal_handler(signal.SIGTERM, None)
    finally:
        logger.info("Main process final cleanup...")
        for env in active_environments:
            if env is not None:
                try:
                    env.close()
                except Exception:
                    pass
