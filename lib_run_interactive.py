"""
Interactive execution loops for multi-turn user simulation evaluation.

Provides a generic runner plus a GPT-5.4-specific runner that mirrors the
agent-specific execution semantics used in lib_run_single.py.
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
    runtime_logger, obs, current_instruction, interaction_log = _start_interactive_run(
        agent,
        env,
        user_sim,
        example,
        example_result_dir,
    )

    done = False
    step_idx = 0
    turn_idx = 0
    while not done and step_idx < max_steps:
        response, actions = agent.predict(current_instruction, obs)
        response_text, response_meta = _normalize_response(response)
        turn_idx += 1
        for action in actions:
            if isinstance(action, str) and action.strip().upper() == "CALL_USER":
                logger.info("Step %d: CALL_USER (skipped env.step)", step_idx + 1)
                continue

            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S%f")
            logger.info("Step %d: %s", step_idx + 1, action)
            obs, reward, done, info = env.step(action, args.sleep_after_execution)
            step_idx += 1

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)

            _save_step_artifacts(
                example_result_dir,
                step_idx,
                action_timestamp,
                obs,
                {
                    "step_num": step_idx,
                    "action_timestamp": action_timestamp,
                    "action": action,
                    "response": response_text,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "phase": user_sim.current_phase_idx + 1,
                    "screenshot_file": f"step_{step_idx}_{action_timestamp}.png",
                },
            )

            if done:
                logger.info("The episode is done (agent reported DONE/FAIL).")
                break
            if step_idx >= max_steps:
                break
        
        done, should_stop = _handle_user_interaction(
            agent=agent,
            user_sim=user_sim,
            response_text=response_text,
            obs=obs,
            agent_signal=actions,
            done=done,
            turn_idx=turn_idx,
            interaction_log=interaction_log,
        )
        if should_stop:
            break

    _finalize_interactive_run(env, example, args, example_result_dir, scores, runtime_logger, interaction_log)


def run_interactive_example_gpt54(
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
    runtime_logger, obs, current_instruction, interaction_log = _start_interactive_run(
        agent,
        env,
        user_sim,
        example,
        example_result_dir,
    )
    agent.set_gui_only_constraint(example.get("related_apps", []))

    done = False
    step_idx = 0
    turn_idx = 0
    while not done and step_idx < max_steps:
        response, actions = agent.predict(current_instruction, obs)
        response_text = response.get("response", "")
        state_correct = response.get("state_correct", False)

        logger.info("Agent response: %s", response_text)
        logger.info("Agent state_correct: %s", state_correct)
        logger.info("Agent model_usage: %s", response.get("model_usage", {}))

        terminal_action = _infer_terminal_action(response, response_text, actions)
        invalid_response = not state_correct and terminal_action not in ["DONE", "FAIL"]
        done = invalid_response or (terminal_action in ["DONE", "FAIL"] and not actions)

        if invalid_response:
            logger.warning(
                "Agent returned no executable action and no terminal signal; ending episode. response=%s",
                response_text,
            )

        turn_idx += 1
        for action in actions:
            if isinstance(action, str) and action.strip().upper() == "CALL_USER":
                logger.info("Step %d: CALL_USER (skipped env.step)", step_idx + 1)
                continue

            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S%f")
            logger.info("Step %d: %s", step_idx + 1, action)
            obs, reward, done, info, step_info = agent.step(action)

            if not done and not state_correct:
                done = True

            step_idx += 1

            controller_result = info.get("controller_result", {}) if isinstance(info, dict) else {}
            if controller_result:
                logger.info("Controller returncode: %s", controller_result.get("returncode"))
                controller_error = (controller_result.get("error") or "").strip()
                controller_output = (controller_result.get("output") or "").strip()
                if controller_error:
                    logger.warning("Controller stderr: %s", controller_error)
                elif controller_output:
                    logger.info("Controller stdout: %s", controller_output)

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)

            action_record = dict(action) if isinstance(action, dict) else action
            if isinstance(action_record, dict) and action_record.get("pending_checks", None):
                del action_record["pending_checks"]

            _save_step_artifacts(
                example_result_dir,
                step_idx,
                action_timestamp,
                obs,
                {
                    "step_num": step_idx,
                    "action_timestamp": action_timestamp,
                    "action": action_record,
                    "response": response_text,
                    "state_correct": state_correct,
                    "model_usage": response.get("model_usage", {}),
                    "messages": response.get("messages", []),
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "step_info": step_info,
                    "phase": user_sim.current_phase_idx + 1,
                    "screenshot_file": f"step_{step_idx}_{action_timestamp}.png",
                },
            )

            if done:
                logger.info("The episode is done (agent reported DONE/FAIL).")
                break
            if step_idx >= max_steps:
                break

        agent_signal = actions if actions else terminal_action
        done, should_stop = _handle_user_interaction(
            agent=agent,
            user_sim=user_sim,
            response_text=response_text,
            obs=obs,
            agent_signal=agent_signal,
            done=done,
            turn_idx=turn_idx,
            interaction_log=interaction_log,
        )
        if should_stop:
            break

        if done:
            logger.info("The episode is done (invalid response or agent reported DONE/FAIL).")
            break

    _finalize_interactive_run(env, example, args, example_result_dir, scores, runtime_logger, interaction_log)


def run_interactive_example_kimi(
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
    runtime_logger, obs, current_instruction, interaction_log = _start_interactive_run(
        agent,
        env,
        user_sim,
        example,
        example_result_dir,
    )

    done = False
    step_idx = 0
    turn_idx = 0
    while not done and step_idx < max_steps:
        response, actions, info_dict = agent.predict(current_instruction, obs)
        response_text, response_meta = _normalize_response(response)
        turn_idx += 1
        for action in actions:
            if isinstance(action, str) and action.strip().upper() == "CALL_USER":
                logger.info("Step %d: CALL_USER (skipped env.step)", step_idx + 1)
                continue

            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S%f")
            logger.info("Step %d: %s", step_idx + 1, action)
            obs, reward, done, info = env.step(action, args.sleep_after_execution)
            step_idx += 1

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)

            _save_step_artifacts(
                example_result_dir,
                step_idx,
                action_timestamp,
                obs,
                {
                    "step_num": step_idx,
                    "action_timestamp": action_timestamp,
                    "action": action,
                    "response": response_text,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "phase": user_sim.current_phase_idx + 1,
                    "screenshot_file": f"step_{step_idx}_{action_timestamp}.png",
                },
            )

            if done:
                logger.info("The episode is done (agent reported DONE/FAIL).")
                break
            if step_idx >= max_steps:
                break

        done, should_stop = _handle_user_interaction(
            agent=agent,
            user_sim=user_sim,
            response_text=response_text,
            obs=obs,
            agent_signal=actions,
            done=done,
            turn_idx=turn_idx,
            interaction_log=interaction_log,
        )
        if should_stop:
            break

    _finalize_interactive_run(env, example, args, example_result_dir, scores, runtime_logger, interaction_log)


def _start_interactive_run(agent, env, user_sim, example, example_result_dir):
    runtime_logger = _setup_logger(example, example_result_dir)

    env.reset(task_config=example)
    try:
        agent.reset(runtime_logger, vm_ip=env.vm_ip)
    except Exception:
        try:
            agent.reset(runtime_logger)
        except Exception:
            agent.reset(vm_ip=env.vm_ip)

    time.sleep(60)
    obs = env._get_obs()

    user_sim.reset()
    current_instruction = user_sim.get_initial_instruction()
    interaction_log = [
        {
            "step": 0,
            "phase": 1,
            "type": "initial_instruction",
            "user_message": current_instruction,
            "timestamp": datetime.datetime.now().strftime("%Y%m%d@%H%M%S"),
        }
    ]

    has_agent_asks = any(
        phase.get("trigger", {}).get("type") == "agent_asks"
        for phase in example.get("phases", [])
    )
    if has_agent_asks and hasattr(agent, "set_interactive_prompt"):
        agent.set_interactive_prompt(True)
        logger.info("[Interactive] Enabled interactive prompt with call_user action")

    env.controller.start_recording()

    with open(os.path.join(example_result_dir, "task_instruction.jsonl"), "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "instruction": current_instruction,
                    "interactive": True,
                    "phases": len(user_sim.phases),
                },
                ensure_ascii=False,
            )
        )
        f.write("\n")

    return runtime_logger, obs, current_instruction, interaction_log


def _handle_user_interaction(
    agent,
    user_sim,
    response_text,
    obs,
    agent_signal,
    done,
    turn_idx,
    interaction_log,
):
    screenshot_b64 = None
    if obs.get("screenshot"):
        screenshot_b64 = base64.b64encode(obs["screenshot"]).decode("utf-8")

    signal_for_trigger = agent_signal if agent_signal else ""
    current_phase = user_sim.current_phase
    current_trigger_type = current_phase.get("trigger", {}).get("type", "agent_done")
    is_last_phase = user_sim.current_phase_idx >= len(user_sim.phases) - 1

    # If the final phase is a normal agent_done-style completion, stop once the
    # agent reports completion instead of generating a redundant closing user turn.
    if done and is_last_phase and current_trigger_type != "agent_asks":
        logger.info("[Interactive] Final non-agent_asks phase completed, ending without extra user response.")
        return done, True

    if not user_sim.should_intervene(turn_idx, signal_for_trigger, screenshot_b64):
        return done, False

    action_str = user_sim._normalize_action(signal_for_trigger)
    is_unexpected_call_user = action_str == "CALL_USER" and current_trigger_type != "agent_asks"
    agent_question = _extract_call_user_question(response_text)

    # For deterministic triggers (agent_done, step_count), advance the phase
    # BEFORE generating the next message so that UserSimulator sees the new
    # phase goal.  This prevents it from repeating the old phase's instruction.
    early_advance = (
        current_trigger_type in ("agent_done", "step_count")
        and not is_unexpected_call_user
    )
    if early_advance:
        logger.info(
            "[Interactive] %s trigger: advancing phase %d -> %d before generating message.",
            current_trigger_type,
            user_sim.current_phase_idx + 1,
            user_sim.current_phase_idx + 2,
        )
        user_sim.advance_phase(current_step_idx=turn_idx)

    user_response = user_sim.generate_next_message(
        agent_reply=response_text,
        screenshot_b64=screenshot_b64,
        is_unexpected_call_user=is_unexpected_call_user,
        agent_question=agent_question,
    )

    if is_unexpected_call_user:
        if user_response["phase_complete"]:
            logger.warning(
                "[Interactive] CALL_USER on non-agent_asks phase (trigger=%s). Overriding phase_complete from True to False.",
                current_trigger_type,
            )
        user_response["phase_complete"] = False

    interaction_log.append(
        {
            "step": turn_idx,
            "phase": user_sim.current_phase_idx + 1,
            "type": user_response["action"],
            "user_message": user_response["message"],
            "phase_complete": user_response["phase_complete"],
            "timestamp": datetime.datetime.now().strftime("%Y%m%d@%H%M%S"),
        }
    )

    logger.info(
        "[Interactive] Phase %d | User action: %s | Message: %s",
        user_sim.current_phase_idx + 1,
        user_response["action"],
        user_response["message"][:100],
    )

    # For non-agent_done triggers, advance only when the action type indicates
    # the phase should move forward.  agent_done phases were already advanced
    # above (early_advance).
    phase_just_completed = (
        not early_advance
        and not is_unexpected_call_user
        and (
            user_response["action"] == "new_instruction"
            or (
                current_trigger_type == "agent_asks"
                and user_response["action"] == "clarify"
            )
        )
    )
    final_phase_idx = user_sim.current_phase_idx + (1 if phase_just_completed else 0)

    if done and final_phase_idx < len(user_sim.phases):
        logger.info("[Interactive] Agent reported DONE but more phases remain. Continuing with new instruction.")
        done = False
        # Preserve conversation history (previous_response_id) so the agent
        # retains full context of what it already did.  The new phase instruction
        # will be injected via receive_user_message → predict Case 3.
        if hasattr(agent, "clear_terminal_state"):
            agent.clear_terminal_state()
        elif hasattr(agent, "clear_done_from_history"):
            agent.clear_done_from_history()

    # Always pass the user message into the agent state. The only thing that
    # blocks automatic phase advancement is an unexpected CALL_USER.
    if hasattr(agent, "receive_user_message"):
        agent.receive_user_message(user_response["message"])

    if phase_just_completed:
        user_sim.advance_phase(current_step_idx=turn_idx)

    if final_phase_idx >= len(user_sim.phases):
        logger.info("[Interactive] All phases complete, ending interaction.")
        return done, True

    return done, False


def _save_step_artifacts(example_result_dir, step_idx, action_timestamp, obs, traj_record):
    with open(
        os.path.join(example_result_dir, f"step_{step_idx}_{action_timestamp}.png"),
        "wb",
    ) as screenshot_file:
        screenshot_file.write(obs["screenshot"])

    with open(os.path.join(example_result_dir, "traj.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(traj_record, ensure_ascii=False))
        f.write("\n")


def _extract_call_user_question(response_text):
    if not response_text:
        return ""

    text = str(response_text).strip()
    prefix = "[CALL_USER]"
    if text.startswith(prefix):
        return text[len(prefix):].strip()
    return ""


def _finalize_interactive_run(env, example, args, example_result_dir, scores, runtime_logger, interaction_log):
    time.sleep(20)
    result = env.evaluate()
    logger.info("Result: %.2f", result)
    scores.append(result)

    with open(os.path.join(example_result_dir, "interaction_log.json"), "w", encoding="utf-8") as f:
        json.dump(interaction_log, f, ensure_ascii=False, indent=2)

    with open(os.path.join(example_result_dir, "result.txt"), "w", encoding="utf-8") as f:
        f.write(f"{result}\n")

    log_task_completion(example, result, example_result_dir, args)
    env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))
    _cleanup_logger(runtime_logger)


def _normalize_response(response):
    if isinstance(response, dict):
        return response.get("response", ""), response
    return response, {"response": response}


def _setup_logger(example, example_result_dir):
    runtime_logger = logging.getLogger(f"desktopenv.runtime.{example.get('id', 'unknown')}")
    for handler in runtime_logger.handlers[:]:
        runtime_logger.removeHandler(handler)
        handler.close()
    log_path = os.path.join(example_result_dir, "runtime.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt="[%(asctime)s %(levelname)s %(module)s/%(lineno)d] %(message)s")
    file_handler.setFormatter(formatter)
    runtime_logger.addHandler(file_handler)
    return runtime_logger


def _cleanup_logger(runtime_logger):
    for handler in runtime_logger.handlers[:]:
        runtime_logger.removeHandler(handler)
        handler.close()


def _infer_terminal_action(response_meta, response_text, actions):
    if actions:
        return ""

    normalized = str(response_text or "").strip().upper().rstrip(".")
    if normalized == "DONE":
        return "DONE"
    if normalized in ["FAIL", "INFEASIBLE"]:
        return "FAIL"

    lower_text = str(response_text or "").lower()
    if any(
        token in lower_text
        for token in ["[infeasible]", "unfeasible", "impossible", "cannot be done", "not feasible"]
    ):
        return "FAIL"

    for message in response_meta.get("messages", []):
        if message.get("phase") == "final_answer":
            return "DONE"

    return ""
