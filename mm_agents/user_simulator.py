"""
UserSimulator: LLM-based user simulator for multi-turn interactive evaluation.

Uses an external API (GPT-4o, Claude, etc.) to simulate realistic user behavior
in multi-phase task interactions. The simulator generates natural user messages
based on the current scenario phase, agent replies, and screen state.
"""

import base64
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any

import requests

logger = logging.getLogger("desktopenv.user_simulator")

# Trigger type constants
TRIGGER_STEP_COUNT = "step_count"
TRIGGER_AGENT_DONE = "agent_done"
TRIGGER_AGENT_IDLE = "agent_idle"
TRIGGER_AGENT_ASKS = "agent_asks"
TRIGGER_LLM_JUDGE = "llm_judge"


USER_SIMULATOR_SYSTEM_PROMPT = """你是一个模拟真实用户的角色扮演者。你正在使用电脑完成一项任务，有一个 AI 助手在帮你操作屏幕。

## 当前场景
{scenario_description}

## 你的人设
- 专业水平：{expertise_level}
- 说话风格：{communication_style}
{completed_phases_section}
## 当前阶段目标（第 {current_phase_number} 阶段，共 {total_phases} 阶段）
你需要向 AI 助手提出以下要求：
{current_phase_instruction}
{next_phase_section}

## 规则
1. 像真实用户一样说话，不要使用过于精确的技术术语（除非你的人设是专业用户）
2. 根据屏幕截图判断 AI 助手是否已完成当前要求
3. 如果 AI 做错了，像普通用户一样指出错误
4. 当当前阶段完成后，如果上面提供了“下一阶段目标”，就自然地提出那个要求；不要自行编造新的需求
5. 如果当前阶段已经完成，且没有提供下一阶段目标，就表示任务都完成了，不要再新增要求
6. 保持对话自然连贯，像真人在和 AI 聊天一样

## 输出格式
你必须以 JSON 格式输出，包含以下字段：
{{
    "action": "new_instruction" 或 "feedback" 或 "clarify" 或 "wait" 或 "done",
    "message": "你要对 AI 助手说的话",
    "phase_complete": true 或 false（当前阶段的任务是否已被 AI 完成）
}}

action 含义：
- "new_instruction": 提出新的操作要求（进入下一阶段）
- "feedback": 对 AI 的操作给出反馈（如"不对"、"做得好"）
- "clarify": 回答 AI 的问题或澄清要求
- "wait": AI 还在操作中，继续等待
- "done": 所有任务都已完成，结束交互

只输出 JSON，不要输出其他内容。
"""

USER_SIMULATOR_JUDGE_PROMPT = """你正在观察一个 AI 助手操作电脑屏幕。请根据屏幕截图判断：AI 助手是否已经完成了以下操作？

要求完成的操作：{instruction}

请只回答 "yes" 或 "no"。
"""


class UserSimulator:
    """
    LLM-based user simulator for multi-turn interactive evaluation.
    
    Uses an external API (separate from the task agent's vLLM service) to
    simulate realistic user behavior across multiple interaction phases.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        scenario_config: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """
        Initialize UserSimulator.
        
        Args:
            api_key: API key for the external LLM service
            base_url: Base URL for the API (e.g., https://api.openai.com/v1)  
            model: Model name (e.g., "gpt-4o", "claude-3.5-sonnet")
            scenario_config: Task scenario configuration dict with "phases" etc.
            temperature: Sampling temperature for user responses
            max_tokens: Max tokens for user response generation
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Scenario config
        self.scenario = scenario_config
        self.phases: List[Dict] = scenario_config.get("phases", [])
        self.scenario_description = scenario_config.get(
            "scenario_description", "用户需要完成一项电脑操作任务"
        )

        # User persona
        persona = scenario_config.get("user_persona", {})
        self.expertise_level = persona.get("expertise_level", "beginner")
        self.communication_style = persona.get("communication_style", "casual_chinese")

        # State
        self.current_phase_idx: int = 0
        self.conversation_history: List[Dict] = []
        self.recent_agent_actions: List[str] = []
        self._wait_count: int = 0  # Count consecutive WAITs for idle detection
        self._phase_start_step: int = 0  # Step index when current phase started
        self.completed_phases_summary: List[Dict] = []  # Track completed phase history

    def get_initial_instruction(self) -> str:
        """
        Return the first phase's instruction as the initial user message.
        
        If there are no phases (shouldn't happen for interactive tasks),
        falls back to the scenario description.
        """
        if not self.phases:
            logger.warning("No phases defined, using scenario_description as instruction")
            return self.scenario_description

        first_instruction = self.phases[0].get("instruction", "")
        logger.info(f"[UserSim] Initial instruction (Phase 1): {first_instruction}")

        # Record the initial instruction in conversation history so later
        # phases can see what the user originally asked for.
        self.conversation_history.append({
            "role": "user",
            "content": f"[初始指令] {first_instruction}",
        })

        return first_instruction

    def generate_next_message(
        self,
        agent_reply: Optional[str],
        screenshot_b64: Optional[str] = None,
        is_unexpected_call_user: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate the next user message based on the current phase, agent's reply,
        and (optionally) the current screenshot.
        
        Args:
            agent_reply: The agent's latest response text
            screenshot_b64: Base64-encoded screenshot of the current screen state
            is_unexpected_call_user: If True, the agent issued CALL_USER on a phase
                whose trigger type is NOT agent_asks.  The LLM will be instructed
                to only answer the agent's question without advancing the phase.
            
        Returns:
            dict with keys:
                "action": str - "new_instruction"|"feedback"|"clarify"|"wait"|"done"
                "message": str - The user message to send to the agent
                "phase_complete": bool - Whether the current phase is considered done
        """
        if self.all_phases_complete:
            return {
                "action": "done",
                "message": "好的，所有操作都完成了，谢谢！",
                "phase_complete": True,
            }

        current_phase = self.current_phase
        current_instruction = current_phase.get("instruction", "")

        # Build completed phases section for system prompt
        completed_phases_section = self._build_completed_phases_section()

        # Build the system prompt with current context
        system_prompt = USER_SIMULATOR_SYSTEM_PROMPT.format(
            scenario_description=self.scenario_description,
            expertise_level=self.expertise_level,
            communication_style=self.communication_style,
            completed_phases_section=completed_phases_section,
            current_phase_number=self.current_phase_idx + 1,
            total_phases=len(self.phases),
            current_phase_instruction=current_instruction,
            next_phase_section=self._build_next_phase_section(),
        )

        # Build messages for the LLM
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last few turns for context).
        # Keep the initial instruction entry (index 0) plus the most recent turns
        # to ensure the LLM always sees the original user request.
        history = self.conversation_history
        if len(history) > 8:
            # Always include the first entry (initial instruction) + last 8 turns
            messages.append(history[0])
            for entry in history[-8:]:
                messages.append(entry)
        else:
            for entry in history:
                messages.append(entry)

        # Add current turn context
        user_content = []

        # When the agent unexpectedly asks a question on a phase that does
        # not expect CALL_USER, prepend a clear instruction to the LLM so
        # it only answers the question without advancing the phase.
        if is_unexpected_call_user:
            user_content.append({
                "type": "text",
                "text": (
                    "【重要提示】AI 助手在你没有期望它提问的情况下向你提了一个问题。"
                    "你只需要根据当前阶段目标，简单、自然地回答它的问题即可。"
                    "不要提出新的要求，不要说任务已完成，不要推进到下一阶段。"
                    '你的 action 应该是 "clarify"，phase_complete 应该是 false。'
                ),
            })

        if agent_reply:
            user_content.append({
                "type": "text",
                "text": f"AI 助手刚才的回复：{agent_reply}",
            })
        if screenshot_b64:
            user_content.append({
                "type": "text",
                "text": "当前屏幕截图如下：",
            })
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"},
            })
        if not user_content:
            user_content.append({
                "type": "text",
                "text": "请根据当前阶段目标生成用户消息。",
            })

        messages.append({"role": "user", "content": user_content})

        # Call the external LLM API
        try:
            response = self._call_api(messages)
            result = self._parse_response(response)
        except Exception as e:
            logger.error(f"[UserSim] Error generating response: {e}")
            # Fallback: just provide the next phase instruction directly
            result = {
                "action": "new_instruction",
                "message": current_instruction,
                "phase_complete": False,
            }

        # Track conversation history
        if agent_reply:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"[AI助手回复] {agent_reply}",
            })
        self.conversation_history.append({
            "role": "user",
            "content": result["message"],
        })

        logger.info(
            f"[UserSim] Phase {self.current_phase_idx + 1}/{len(self.phases)} | "
            f"Action: {result['action']} | Phase complete: {result['phase_complete']} | "
            f"Message: {result['message'][:100]}..."
        )

        return result

    def should_intervene(
        self,
        step_idx: int,
        agent_action: Any,
        screenshot_b64: Optional[str] = None,
    ) -> bool:
        """
        Check whether the user should intervene at this point based on
        the current phase's trigger condition.
        
        Args:
            step_idx: Current step index in the execution loop
            agent_action: The agent's last action (str or list)
            screenshot_b64: Base64-encoded screenshot (for LLM-based triggers)
            
        Returns:
            True if the user should send a new message
        """
        if self.all_phases_complete:
            return False

        trigger = self.current_phase.get("trigger", {"type": TRIGGER_AGENT_DONE})
        trigger_type = trigger.get("type", TRIGGER_AGENT_DONE)

        # Normalize agent_action to string
        action_str = self._normalize_action(agent_action)

        # ── Universal override: CALL_USER always triggers intervention ──
        # The agent explicitly asked the user for help / clarification.
        # This takes priority regardless of the configured trigger type,
        # so that tasks without an "agent_asks" trigger still respond
        # correctly when the model decides to call_user.
        if action_str == "CALL_USER":
            logger.info(
                "[UserSim] CALL_USER detected (trigger=%s) — forcing intervention",
                trigger_type,
            )
            return True

        if trigger_type == TRIGGER_STEP_COUNT:
            threshold = trigger.get("value", 5)
            # Use relative step count within the current phase,
            # not the global step_idx, to avoid immediate re-trigger
            # after advancing to a new phase.
            steps_in_phase = step_idx - self._phase_start_step
            return steps_in_phase >= threshold

        elif trigger_type == TRIGGER_AGENT_DONE:
            return action_str in ["DONE", "FAIL"]

        elif trigger_type == TRIGGER_AGENT_IDLE:
            if action_str == "WAIT":
                self._wait_count += 1
            else:
                self._wait_count = 0
            threshold = trigger.get("value", 3)
            return self._wait_count >= threshold

        elif trigger_type == TRIGGER_AGENT_ASKS:
            # CALL_USER is already handled above; this branch now only
            # exists for completeness / future trigger subtypes.
            return False

        elif trigger_type == TRIGGER_LLM_JUDGE:
            return self._llm_judge_ready(screenshot_b64)

        else:
            logger.warning(f"[UserSim] Unknown trigger type: {trigger_type}")
            return False

    def advance_phase(self, current_step_idx: int = 0):
        """Move to the next interaction phase, recording the completed one.
        
        Args:
            current_step_idx: The global step index at the time of phase advance,
                              used to anchor relative step counting for the next phase.
        """
        # Record completed phase summary before advancing
        if self.current_phase_idx < len(self.phases):
            completed = self.phases[self.current_phase_idx]
            self.completed_phases_summary.append({
                "phase_id": completed.get("phase_id", self.current_phase_idx + 1),
                "instruction": completed.get("instruction", ""),
            })

        self.current_phase_idx += 1
        self._wait_count = 0
        self._phase_start_step = current_step_idx  # Reset step offset for next phase
        if self.current_phase_idx < len(self.phases):
            logger.info(
                f"[UserSim] Advanced to Phase {self.current_phase_idx + 1}: "
                f"{self.current_phase.get('instruction', '')[:80]}"
            )
        else:
            logger.info("[UserSim] All phases complete.")

    @property
    def all_phases_complete(self) -> bool:
        """Check if all interaction phases have been completed."""
        return self.current_phase_idx >= len(self.phases)

    @property
    def current_phase(self) -> Dict[str, Any]:
        """Get the current phase config."""
        if self.current_phase_idx < len(self.phases):
            return self.phases[self.current_phase_idx]
        return {}

    def _call_api(self, messages: List[Dict]) -> str:
        """
        Call the external LLM API (OpenAI-compatible format).
        
        Args:
            messages: List of message dicts for the chat API
            
        Returns:
            The response content string
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        response = requests.post(url, headers=headers, json=data, timeout=120)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(
                f"API request failed ({response.status_code}): {response.text}"
            )

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response into the expected dict format.
        Handles cases where the response might not be valid JSON.
        """
        # Try to extract JSON from the response
        text = response_text.strip()

        # Remove explicit reasoning blocks if the model emitted them.
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.strip() == "```" and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        candidates = []
        embedded_json = self._extract_json_object(text)
        if embedded_json:
            candidates.append(embedded_json)
        candidates.append(text)

        for candidate in candidates:
            try:
                result = json.loads(candidate)
                # Validate required fields
                if "action" not in result:
                    result["action"] = "new_instruction"
                if "message" not in result:
                    result["message"] = candidate
                if "phase_complete" not in result:
                    result["phase_complete"] = False
                return result
            except json.JSONDecodeError:
                continue

            logger.warning(f"[UserSim] Failed to parse JSON, using raw text as message")
            return {
                "action": "new_instruction",
                "message": text,
                "phase_complete": False,
            }

    def _extract_json_object(self, text: str) -> Optional[str]:
        """Extract the last balanced JSON object from a mixed-text response."""
        last_candidate = None

        for start_idx, char in enumerate(text):
            if char != "{":
                continue

            depth = 0
            in_string = False
            escaped = False

            for end_idx in range(start_idx, len(text)):
                current = text[end_idx]

                if escaped:
                    escaped = False
                    continue

                if current == "\\":
                    escaped = True
                    continue

                if current == '"':
                    in_string = not in_string
                    continue

                if in_string:
                    continue

                if current == "{":
                    depth += 1
                elif current == "}":
                    depth -= 1
                    if depth == 0:
                        last_candidate = text[start_idx:end_idx + 1]
                        break

        return last_candidate

    def _normalize_action(self, agent_action: Any) -> str:
        """Normalize agent action to a canonical uppercase string for trigger comparison.
        
        Handles various formats returned by different agents:
        - str: "CALL_USER", "call_user", "DONE", "FAIL", "WAIT"
        - list: ["CALL_USER"], ["click(...)", "DONE"]
        - dict: {"action_type": "CALL_USER", ...}
        """
        if isinstance(agent_action, str):
            normalized = agent_action.strip().upper()
            # Map known action keywords to canonical forms
            if normalized in ("CALL_USER", "DONE", "FAIL", "WAIT"):
                return normalized
            return agent_action
        elif isinstance(agent_action, list):
            if len(agent_action) > 0:
                return self._normalize_action(agent_action[-1])
            return ""
        elif isinstance(agent_action, dict):
            return agent_action.get("action_type", "")
        return str(agent_action)

    def _llm_judge_ready(self, screenshot_b64: Optional[str]) -> bool:
        """
        Use the LLM to judge whether the current phase is ready for
        user intervention based on the screenshot.
        """
        if not screenshot_b64:
            return False

        current_instruction = self.current_phase.get("instruction", "")
        prompt = USER_SIMULATOR_JUDGE_PROMPT.format(instruction=current_instruction)

        messages = [
            {"role": "system", "content": "你是一个判断任务是否完成的助手。只回答 yes 或 no。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"},
                    },
                ],
            },
        ]

        try:
            response = self._call_api(messages)
            return "yes" in response.lower()
        except Exception as e:
            logger.error(f"[UserSim] LLM judge error: {e}")
            return False

    def _build_completed_phases_section(self) -> str:
        """
        Build a summary section of completed phases for the system prompt.
        This ensures the LLM knows what the user previously asked for
        and what the AI assistant has already done.
        """
        if not self.completed_phases_summary:
            return ""

        lines = ["\n## 已完成的阶段（供参考，不要重复提出这些要求）"]
        for item in self.completed_phases_summary:
            lines.append(f"- 第 {item['phase_id']} 阶段：{item['instruction']}")
        lines.append("")  # trailing newline
        return "\n".join(lines)

    def _build_next_phase_section(self) -> str:
        """Build an explicit next-phase hint so the LLM does not invent new tasks."""
        next_phase_idx = self.current_phase_idx + 1
        if next_phase_idx >= len(self.phases):
            return "\n## 下一阶段目标\n没有下一阶段了。"

        next_instruction = self.phases[next_phase_idx].get("instruction", "")
        return (
            "\n## 下一阶段目标\n"
            "如果当前阶段已经完成，下一条用户消息应该自然地表达下面这个要求，"
            "不要改写成别的需求：\n"
            f"{next_instruction}"
        )

    def reset(self):
        """Reset the simulator state for a new task."""
        self.current_phase_idx = 0
        self.conversation_history.clear()
        self.recent_agent_actions.clear()
        self.completed_phases_summary.clear()
        self._wait_count = 0
        self._phase_start_step = 0
