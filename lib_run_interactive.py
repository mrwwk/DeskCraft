"""
Interactive execution loop for multi-turn user simulation evaluation.

Replaces run_single_example() for tasks with "interactive": true,
managing multi-phase interactions between a UserSimulator and the task Agent.
"""

import base64
import datetime
import json
import logging
import os
import time

from lib_results_logger import log_task_completion

logger = logging.getLogger("desktopenv.experiment")


def run_interactive_example(
    agent,
    env,
    user_sim,
    example,
    max_steps,
    instruction,
    args,
    example_result_dir,
    scores,
):
    """
    Execute a single interactive task example with multi-turn user simulation.
    
    The flow:
      Phase 1: Initial instruction → Agent executes several steps
      ↓ (trigger condition met)
      Phase 2: User provides follow-up instruction → Agent continues
      ↓ ...
      Phase N: Final phase →Agent completes
      → Evaluate final result using existing evaluator
    
    Args:
        agent: The task agent (e.g., UITarsAgent)
        env: The DesktopEnv environment instance
        user_sim: UserSimulator instance for this task
        example: Task config dict (with "phases", "evaluator", etc.)
        max_steps: Maximum total steps across all phases
        instruction: Initial instruction (from first phase)
        args: Command line arguments
        example_result_dir: Directory to save results and logs
        scores: Shared list to append the score to
    """
    runtime_logger = _setup_logger(example, example_result_dir)

    # Reset environment
    env.reset(task_config=example)
    try:
        agent.reset(runtime_logger, vm_ip=env.vm_ip)
    except Exception:
        agent.reset(vm_ip=env.vm_ip)

    time.sleep(60)  # Wait for environment to be ready
    obs = env._get_obs()

    # Initialize interaction state
    user_sim.reset()
    current_instruction = user_sim.get_initial_instruction()
    done = False
    step_idx = 0
    interaction_log = []

    # Record the initial instruction
    interaction_log.append({
        "step": 0,
        "phase": 1,
        "type": "initial_instruction",
        "user_message": current_instruction,
        "timestamp": datetime.datetime.now().strftime("%Y%m%d@%H%M%S"),
    })

    # Check if any phase uses agent_asks trigger → enable interactive prompt
    has_agent_asks = any(
        p.get("trigger", {}).get("type") == "agent_asks"
        for p in example.get("phases", [])
    )
    if has_agent_asks and hasattr(agent, "set_interactive_prompt"):
        agent.set_interactive_prompt(True)
        logger.info("[Interactive] Enabled interactive prompt with call_user action")

    env.controller.start_recording()

    # Save task instruction
    with open(os.path.join(example_result_dir, "task_instruction.jsonl"), "a") as f:
        f.write(json.dumps({
            "instruction": current_instruction,
            "interactive": True,
            "phases": len(user_sim.phases),
        }, ensure_ascii=False))
        f.write("\n")

    while not done and step_idx < max_steps:
        # Agent predicts next action based on current instruction and observation
        response, actions = agent.predict(current_instruction, obs)

        for action in actions:
            # Skip CALL_USER action — it is a signal for user intervention,
            # not an executable action for the environment.
            if isinstance(action, str) and action.strip().upper() == "CALL_USER":
                logger.info("Step %d: CALL_USER (skipped env.step)", step_idx + 1)
                continue

            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S%f")

            logger.info("Step %d: %s", step_idx + 1, action)
            obs, reward, done, info = env.step(action, args.sleep_after_execution)
            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)

            # Save screenshot
            with open(
                os.path.join(
                    example_result_dir,
                    f"step_{step_idx + 1}_{action_timestamp}.png",
                ),
                "wb",
            ) as _f:
                _f.write(obs["screenshot"])

            # Save trajectory
            with open(os.path.join(example_result_dir, "traj.jsonl"), "a") as f:
                f.write(json.dumps({
                    "step_num": step_idx + 1,
                    "action_timestamp": action_timestamp,
                    "action": action,
                    "response": response,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "phase": user_sim.current_phase_idx + 1,
                    "screenshot_file": f"step_{step_idx + 1}_{action_timestamp}.png",
                }, ensure_ascii=False))
                f.write("\n")

            if done:
                logger.info("The episode is done (agent reported DONE/FAIL).")
                break

        step_idx += 1

        # ===== Core: Check if user should intervene =====
        screenshot_b64 = None
        if obs.get("screenshot"):
            screenshot_b64 = base64.b64encode(obs["screenshot"]).decode("utf-8")

        if user_sim.should_intervene(step_idx, actions if actions else "", screenshot_b64):
            # ── Detect unexpected CALL_USER ──
            # If the agent issued CALL_USER on a phase whose trigger is NOT
            # agent_asks, this is an unexpected call.  We still respond (to
            # avoid a dead loop), but (a) tell the user-sim LLM to only
            # answer the question, and (b) force phase_complete = False.
            current_trigger_type = (
                user_sim.current_phase
                .get("trigger", {})
                .get("type", "agent_done")
            )
            action_str = user_sim._normalize_action(actions if actions else "")
            is_unexpected_call_user = (
                action_str == "CALL_USER" and current_trigger_type != "agent_asks"
            )

            # Generate user response
            user_response = user_sim.generate_next_message(
                agent_reply=response,
                screenshot_b64=screenshot_b64,
                is_unexpected_call_user=is_unexpected_call_user,
            )

            # Guard: prevent accidental phase advancement on unexpected CALL_USER
            if is_unexpected_call_user:
                if user_response["phase_complete"]:
                    logger.warning(
                        "[Interactive] CALL_USER on non-agent_asks phase (trigger=%s). "
                        "Overriding phase_complete from True → False to prevent "
                        "unintended phase advancement.",
                        current_trigger_type,
                    )
                user_response["phase_complete"] = False

            # Log the interaction
            interaction_log.append({
                "step": step_idx,
                "phase": user_sim.current_phase_idx + 1,
                "type": user_response["action"],
                "user_message": user_response["message"],
                "phase_complete": user_response["phase_complete"],
                "timestamp": datetime.datetime.now().strftime("%Y%m%d@%H%M%S"),
            })

            logger.info(
                "[Interactive] Phase %d | User action: %s | Message: %s",
                user_sim.current_phase_idx + 1,
                user_response["action"],
                user_response["message"][:100],
            )

            # Advance phase if the user/LLM judged it complete
            if user_response["phase_complete"]:
                # Defer actual advance_phase until after done-flag handling below,
                # so that the current trigger type is still in effect for this check.
                phase_just_completed = True
            else:
                phase_just_completed = False

            # Check if all phases are done (peek ahead)
            final_phase_idx = user_sim.current_phase_idx + (1 if phase_just_completed else 0)
            if final_phase_idx >= len(user_sim.phases) or user_response["action"] == "done":
                if phase_just_completed:
                    user_sim.advance_phase(current_step_idx=step_idx)
                logger.info("[Interactive] All phases complete, ending interaction.")
                break

            # Inject the new user message into the agent
            # Keep current_instruction as the original instruction;
            # the new message is delivered via receive_user_message only,
            # and will be appended inside agent.predict() as [用户追加消息].
            new_message = user_response["message"]
            if hasattr(agent, "receive_user_message"):
                agent.receive_user_message(new_message)

            # If agent reported DONE but there are more phases, reset done flag
            if done and final_phase_idx < len(user_sim.phases):
                logger.info(
                    "[Interactive] Agent reported DONE but more phases remain. "
                    "Continuing with new instruction."
                )
                done = False
                # Clean up the DONE/terminate entry from agent's history so the
                # LLM does not think the task was already completed.
                if hasattr(agent, "clear_done_from_history"):
                    agent.clear_done_from_history()

            # Now advance phase (after done-flag handling)
            if phase_just_completed:
                user_sim.advance_phase(current_step_idx=step_idx)

    # ===== Final Evaluation =====
    time.sleep(20)  # Wait for environment to settle
    result = env.evaluate()
    logger.info("Result: %.2f", result)
    scores.append(result)

    # Save interaction log
    with open(os.path.join(example_result_dir, "interaction_log.json"), "w", encoding="utf-8") as f:
        json.dump(interaction_log, f, ensure_ascii=False, indent=2)

    # Save result
    with open(os.path.join(example_result_dir, "result.txt"), "w", encoding="utf-8") as f:
        f.write(f"{result}\n")

    # Log task completion
    log_task_completion(example, result, example_result_dir, args)

    # End recording
    env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))

    # Clean up logger handlers to avoid resource leaks
    _cleanup_logger(runtime_logger)


def _setup_logger(example, example_result_dir):
    """Set up a file logger for this specific example run."""
    runtime_logger = logging.getLogger(f"desktopenv.runtime.{example.get('id', 'unknown')}")
    # Remove any pre-existing handlers to prevent duplicate logging
    for h in runtime_logger.handlers[:]:
        runtime_logger.removeHandler(h)
        h.close()
    log_path = os.path.join(example_result_dir, "runtime.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s %(levelname)s %(module)s/%(lineno)d] %(message)s"
    )
    file_handler.setFormatter(formatter)
    runtime_logger.addHandler(file_handler)
    return runtime_logger


def _cleanup_logger(runtime_logger):
    """Remove and close all file handlers to avoid resource leaks."""
    for h in runtime_logger.handlers[:]:
        runtime_logger.removeHandler(h)
        h.close()
