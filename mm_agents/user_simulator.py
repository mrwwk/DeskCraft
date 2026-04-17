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


USER_SIMULATOR_SYSTEM_PROMPT = """You are roleplaying as a realistic computer user. You are trying to complete a task on a computer, and an AI assistant is helping operate the screen for you.

## Current Scenario
{scenario_description}

## Your Persona
- Expertise level: {expertise_level}
- Communication style: {communication_style}
{completed_phases_section}
## Current Phase Goal (Phase {current_phase_number} of {total_phases})
You need to ask the AI assistant to do the following:
{current_phase_instruction}
{next_phase_section}

## Rules
1. Speak like a real user. Do not use overly precise technical terms unless your persona is a professional user.
2. Use the screenshot to judge whether the AI assistant has completed the current requirement.
3. If a "Next Phase Goal" is provided above, naturally ask for that requirement next. Do not invent new requests on your own.
4. If the current phase is complete and there is no next phase goal, indicate that the whole task is finished and do not add any new requests.
5. Keep the conversation natural and coherent, like a real person chatting with an AI assistant.
6. Your `message` should follow the language implied by the scenario and current instruction. If the task context is in Chinese, reply in Chinese; if it is in English, reply in English.
7. In normal cases, always set `action` to `new_instruction`.
8. If the AI assistant has not completed the current phase, keep the interaction in the same phase: set `phase_complete` to false and use `message` to restate or correct the current requirement.
9. If the AI assistant has completed the current phase and there is a next phase goal, set `phase_complete` to true and use `message` to naturally express that next phase goal.
10. If the current phase expects the AI assistant to ask the user a question, answer that question directly and naturally. In that case, use `clarify` and set `phase_complete` to true.
11. If the AI assistant explicitly asks the user a question unexpectedly, you may use `clarify`, and in that case `phase_complete` must be false.

## Output Format
You must output valid JSON with the following fields:
{{
    "action": "new_instruction" or "clarify",
    "message": "What you want to say to the AI assistant",
    "phase_complete": true or false,
    "reason": "When phase_complete is false, explain why the current phase is not complete"
}}

Meaning of `action`:
- "new_instruction": The default and normal case. Use it for both correcting the current phase requirement and expressing the next phase requirement.
- "clarify": Only use this when the AI assistant explicitly asks the user a question unexpectedly. Do not use it otherwise.

Output JSON only. Do not output any extra text.
"""

USER_SIMULATOR_JUDGE_PROMPT = """You are observing an AI assistant operating a computer screen. Based on the screenshot, decide whether the AI assistant has already completed the following requirement.

Required operation: {instruction}

Answer only "yes" or "no".
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
            "scenario_description", "The user needs to complete a computer task"
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
            "content": f"[Initial instruction] {first_instruction}",
        })

        return first_instruction

    def generate_next_message(
        self,
        agent_reply: Optional[str],
        screenshot_b64: Optional[str] = None,
        is_unexpected_call_user: bool = False,
        agent_question: Optional[str] = None,
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
            agent_question: Extracted call_user question text from the GUI agent, if any.
            
        Returns:
            dict with keys:
                "action": str - "new_instruction"|"clarify"
                "message": str - The user message to send to the agent
                "phase_complete": bool - Whether the current phase is considered done
        """
        if self.all_phases_complete:
            return {
                "action": "new_instruction",
                "message": "All steps are complete. Thank you.",
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

        current_trigger_type = current_phase.get("trigger", {}).get("type", TRIGGER_AGENT_DONE)
        is_expected_call_user = current_trigger_type == TRIGGER_AGENT_ASKS and bool(agent_question)

        # When the agent asks a question in an agent_asks phase, answer that
        # question directly and treat the reply as phase completion.
        if is_expected_call_user:
            user_content.append({
                "type": "text",
                "text": (
                    "[Important] This phase expects the AI assistant to ask the user a question. "
                    "Answer the question directly and naturally. Do not introduce a new request. "
                    'Your action should be "clarify", and phase_complete should be true.'
                ),
            })
            user_content.append({
                "type": "text",
                "text": f"The AI assistant's question is: {agent_question}",
            })

        # When the agent unexpectedly asks a question on a phase that does
        # not expect CALL_USER, prepend a clear instruction to the LLM so
        # it only answers the question without advancing the phase.
        if is_unexpected_call_user:
            user_content.append({
                "type": "text",
                "text": (
                    "[Important] The AI assistant asked you a question when this phase was not expected to require user input. "
                    "You should only answer its question briefly and naturally based on the current phase goal. "
                    "Do not introduce a new request, do not say the task is finished, and do not advance to the next phase. "
                    'Your action should be "clarify", and phase_complete should be false.'
                ),
            })
            if agent_question:
                user_content.append({
                    "type": "text",
                    "text": f"The AI assistant's question is: {agent_question}",
                })

        if agent_reply:
            user_content.append({
                "type": "text",
                "text": f"The AI assistant just replied: {agent_reply}",
            })
        if screenshot_b64:
            user_content.append({
                "type": "text",
                "text": "The current screenshot is shown below:",
            })
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"},
            })
        if not user_content:
            user_content.append({
                "type": "text",
                "text": "Generate the next user message based on the current phase goal.",
            })

        messages.append({"role": "user", "content": user_content})

        # Call the external LLM API
        try:
            response = self._call_api(messages)
            result = self._parse_response(response)
        except Exception as e:
            logger.error(f"[UserSim] Error generating response: {e}")
            # Fallback: keep the response shape simple and deterministic.
            result = {
                "action": "new_instruction",
                "message": current_instruction,
                "phase_complete": False,
            }

        result = self._normalize_user_action(
            result,
            is_unexpected_call_user=is_unexpected_call_user,
            is_expected_call_user=is_expected_call_user,
        )

        # Track conversation history
        if agent_reply:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"[AI assistant reply] {agent_reply}",
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

    def _normalize_user_action(
        self,
        result: Dict[str, Any],
        is_unexpected_call_user: bool,
        is_expected_call_user: bool,
    ) -> Dict[str, Any]:
        """Normalize legacy simulator actions into the simplified protocol."""
        action = str(result.get("action", "new_instruction") or "new_instruction").strip().lower()

        if is_expected_call_user:
            result["action"] = "clarify"
            result["phase_complete"] = True
            return result

        if is_unexpected_call_user:
            result["action"] = "clarify"
            result["phase_complete"] = False
            return result

        if action != "new_instruction":
            result["action"] = "new_instruction"

        return result

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
            {"role": "system", "content": "You are an assistant that judges task completion. Reply only with yes or no."},
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

        lines = ["\n## Completed Phases (for reference, do not ask for these again)"]
        for item in self.completed_phases_summary:
            lines.append(f"- Phase {item['phase_id']}: {item['instruction']}")
        lines.append("")  # trailing newline
        return "\n".join(lines)

    def _build_next_phase_section(self) -> str:
        """Build an explicit next-phase hint so the LLM does not invent new tasks."""
        next_phase_idx = self.current_phase_idx + 1
        if next_phase_idx >= len(self.phases):
            return "\n## Next Phase Goal\nThere is no next phase."

        next_instruction = self.phases[next_phase_idx].get("instruction", "")
        return (
            "\n## Next Phase Goal\n"
            "If the current phase is complete, the next user message should naturally express the requirement below. "
            "Do not rewrite it into a different request:\n"
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
