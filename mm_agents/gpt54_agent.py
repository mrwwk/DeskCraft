import base64
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from openai import OpenAI


logger = logging.getLogger("desktopenv.agent")

INTERACTIVE_PROMPT_SUFFIX = """

This is an interactive session.
- If the instruction is ambiguous or missing details, call `call_user` to ask a precise clarification question.
- If the user provides an update or changes the requirement later, incorporate it and continue from the current desktop state.
- Do not pretend the user already answered if they have not.
"""

CALL_USER_TOOL = {
    "type": "function",
    "name": "call_user",
    "description": "Ask the user for clarification when the instruction is ambiguous, incomplete, or updated mid-task.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "A short, specific question for the user.",
            }
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

OPERATOR_PROMPT = """

Here are some helpful tips:
- You are operating an {PLATFORM} desktop with internet access.
- My computer password is "{CLIENT_PASSWORD}" when sudo is needed.
- The current date is {CURRENT_DATE}.
- The home directory is "{HOME_DIR}".
- Stick to the website or application already opened for the task when possible.
- Prefer Chrome over Firefox/Chromium unless the task says otherwise.
- You can act without asking for confirmation.
- If content may be off-screen, scroll or zoom out before deciding it is unavailable.
- When possible, bundle multiple GUI actions into one computer-use turn.
- If the task is infeasible because of missing apps, permissions, contradictory requirements, or other hard blockers, output exactly "[INFEASIBLE]".
"""

GUI_ONLY_APP_GUARDRAILS = {
    "blender": (
        "For Blender tasks in this benchmark, use only the visible Blender GUI. "
        "Do not use Blender Python, the Scripting workspace, the Python console, terminal commands, "
        "heredocs, temporary .py files, or `--python` / `--python-expr`. "
        "If a Blender task would require scripting, do not script it; keep using GUI actions only."
    ),
    "gimp": (
        "For GIMP tasks in this benchmark, use only the visible GUI. "
        "Do not use Python-Fu, Script-Fu, plug-in consoles, terminal commands, heredocs, or temporary scripts."
    ),
    "inkscape": (
        "For Inkscape tasks in this benchmark, use only the visible GUI. "
        "Do not use command-line batch mode, extensions as a scripting shortcut, terminal commands, heredocs, or temporary scripts."
    ),
    "libreoffice_writer": (
        "For LibreOffice Writer tasks in this benchmark, use only the visible Writer GUI. "
        "Do not use macros, UNO scripting, terminal commands, heredocs, or temporary scripts."
    ),
    "vscode": (
        "For VS Code tasks in this benchmark, use only the visible VS Code GUI and direct text editing inside the editor. "
        "Do not use terminal Python scripts, shell scripts, heredocs, temporary .py files, notebook execution, or command-line automation to modify files."
    ),
}


class Action:
    """Minimal wrapper matching the existing OpenAI CUA agent contract."""

    def __init__(self, raw_action: Union[Dict[str, Any], str], action_space: str):
        self._action_space = None
        self._action = None
        self.action_space = action_space
        self.action = raw_action

    @property
    def action(self) -> Any:
        return self._action

    @property
    def action_space(self) -> str:
        return self._action_space

    @action_space.setter
    def action_space(self, value: str) -> None:
        if value != "pyautogui":
            raise ValueError("GPT54Agent only supports pyautogui actions")
        self._action_space = value

    @action.setter
    def action(self, value: Union[Dict[str, Any], str]) -> None:
        if value in (None, ""):
            raise ValueError("action cannot be empty")
        self._action = value

    def get_action(self) -> Any:
        return self._action


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.duration = time.time() - self.start


class StepError(Exception):
    pass


def encode_image(image_content: bytes) -> str:
    return base64.b64encode(image_content).decode("utf-8")


def _normalize_base_url(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None
    base_url = base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = base_url + "/v1"
    return base_url


def _build_openai_client(model: str) -> OpenAI:
    raw_base_url = os.getenv("BASE_URL") or os.getenv("OPENAI_BASE_URL")
    base_url = _normalize_base_url(raw_base_url)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    app_id = os.getenv("APP_ID")
    app_key = os.getenv("API_KEY") or os.getenv("APP_KEY")

    client_kwargs: Dict[str, Any] = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    timeout = os.getenv("OPENAI_TIMEOUT") or os.getenv("OPENAI_AUTH_TIMEOUT")
    if timeout:
        try:
            client_kwargs["timeout"] = float(timeout)
        except ValueError:
            logger.warning("Ignoring invalid timeout value: %s", timeout)

    if openai_api_key:
        client_kwargs["api_key"] = openai_api_key
        return OpenAI(**client_kwargs)

    if app_id and app_key:
        client_kwargs["api_key"] = f"{app_id}:{app_key}"
        return OpenAI(**client_kwargs)

    raise ValueError("OPENAI_API_KEY or APP_ID/APP_KEY must be set for GPT54Agent")


def _model_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_model_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _model_dump(item) for key, item in value.items()}
    return value


def _preview_text(text: str, limit: int = 120) -> str:
    sanitized = text.replace("\n", "\\n")
    if len(sanitized) <= limit:
        return sanitized
    return sanitized[:limit] + "..."


def _get_field(value: Any, field: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(field, default)
    return getattr(value, field, default)


def _sanitize_for_log(value: Any) -> Any:
    """Strip oversized payloads like base64 screenshots before logging."""
    value = _model_dump(value)
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if key == "image_url" and isinstance(item, str) and item.startswith("data:image/"):
                sanitized[key] = "<image>"
            else:
                sanitized[key] = _sanitize_for_log(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_for_log(item) for item in value]
    return value


class GPT54Agent:
    def __init__(
        self,
        env,
        platform: str = "ubuntu",
        model: str = "api_azure_openai_gpt-5.4",
        max_tokens: Optional[int] = None,
        top_p: float = 0.9,
        temperature: float = 0.5,
        action_space: str = "pyautogui",
        observation_type: str = "screenshot",
        max_trajectory_length: int = 100,
        a11y_tree_max_tokens: int = 10000,
        client_password: str = "",
        provider_name: str = "aws",
        screen_width: int = 1920,
        screen_height: int = 1080,
        sleep_after_execution: float = 0.0,
        reasoning_effort: str = "xhigh",
    ):
        if action_space != "pyautogui":
            raise ValueError("GPT54Agent only supports pyautogui action space")
        if observation_type != "screenshot":
            raise ValueError("GPT54Agent currently supports screenshot observation only")

        self.env = env
        self.platform = platform
        self.model = model
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.action_space = action_space
        self.observation_type = observation_type
        self.max_trajectory_length = max_trajectory_length
        self.a11y_tree_max_tokens = a11y_tree_max_tokens
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.sleep_after_execution = sleep_after_execution
        self.reasoning_effort = reasoning_effort
        self.client_password = client_password or (
            "osworld-public-evaluation" if provider_name == "aws" else "password"
        )

        # GPT-5.4 GA computer-use uses the plain "computer" tool shape.
        self.computer_tool = {"type": "computer"}

        self.previous_response_id: Optional[str] = None
        self.pending_input_items: List[Dict[str, Any]] = []
        self.current_batch_call_id: Optional[str] = None
        self.current_batch_expected_outputs = 0
        self.pending_user_messages: List[str] = []
        self.pending_user_call_id: Optional[str] = None
        self.is_interactive = False
        self.gui_only_instruction_suffix = ""

    def _build_tools(self) -> List[Dict[str, Any]]:
        tools = [self.computer_tool]
        if self.is_interactive:
            tools.append(CALL_USER_TOOL)
        return tools

    def _format_additional_user_messages(self, messages: List[str]) -> str:
        if not messages:
            return ""
        return "\n\n".join(
            f"[User Additional Message]:\n{message}" for message in messages if message
        )

    def receive_user_message(self, message: str) -> None:
        if not message:
            return
        self.pending_user_messages.append(message)

    def set_interactive_prompt(self, enable: bool = True) -> None:
        self.is_interactive = enable

    def set_gui_only_constraint(self, related_apps: Optional[List[str]] = None) -> None:
        related_apps = related_apps or []
        suffixes: List[str] = []
        for app in related_apps:
            text = GUI_ONLY_APP_GUARDRAILS.get(str(app).lower())
            if text and text not in suffixes:
                suffixes.append(text)
        self.gui_only_instruction_suffix = "\n".join(suffixes)

    def clear_done_from_history(self) -> None:
        """Legacy full reset – clears conversation history entirely."""
        self.previous_response_id = None
        self.pending_input_items = []
        self.pending_user_call_id = None
        self.pending_user_messages = []

    def clear_terminal_state(self) -> None:
        """Clear terminal-related state while preserving conversation history.

        After the agent reports DONE/FAIL but more phases remain, call this
        instead of clear_done_from_history so that:
        - previous_response_id is kept → next predict() walks Case 3 (unsolicited
          user message) rather than Case 1 (first request with stale instruction).
        - pending_input_items are cleared because the DONE response has no
          computer_call_output to feed back.
        - pending_user_call_id is cleared in case the DONE came from a call_user
          flow that is now stale.
        """
        self.pending_input_items = []
        self.pending_user_call_id = None

    def _create_response(self, request_input: List[Dict[str, Any]], instructions: str):
        retry_count = 0
        last_error = None
        while retry_count < 5:
            try:
                client = _build_openai_client(self.model)
                logger.info(
                    "Sending GPT-5.4 request with previous_response_id=%s and %d input item(s)",
                    self.previous_response_id,
                    len(request_input),
                )
                logger.debug("Request input items: %s", _sanitize_for_log(request_input))
                request: Dict[str, Any] = {
                    "model": self.model,
                    "instructions": instructions,
                    "input": request_input,
                    "tools": self._build_tools(),
                    "parallel_tool_calls": False,
                    "reasoning": {
                        "effort": self.reasoning_effort,
                        "summary": "concise",
                    },
                    "truncation": "auto",
                }
                if self.max_tokens is not None:
                    request["max_output_tokens"] = self.max_tokens
                if self.previous_response_id:
                    request["previous_response_id"] = self.previous_response_id
                response = client.responses.create(**request)
                response_error = _get_field(_get_field(response, "error", {}), "message")
                if response_error:
                    raise RuntimeError(response_error)
                if _get_field(response, "status") == "failed":
                    raise RuntimeError("Responses API request failed.")
                logger.info("Received GPT-5.4 computer-use response")
                logger.debug("Raw response output: %s", _sanitize_for_log(_get_field(response, "output", [])))
                return response
            except Exception as exc:
                last_error = exc
                retry_count += 1
                logger.error("OpenAI API error on GPT54Agent call: %s", exc)

                error_text = str(exc)
                # Do not resend the same interactive user message on deterministic
                # client-side request errors. Those retries only duplicate the
                # payload and cannot succeed without changing the request shape.
                if (
                    "Error code: 400" in error_text
                    or "invalid_request_error" in error_text
                    or "BadRequestError" in error_text
                ):
                    break

                time.sleep(min(5, retry_count * 2))
        raise RuntimeError(f"OpenAI API failed too many times: {last_error}")

    def _action_to_dict(self, action: Any) -> Dict[str, Any]:
        if isinstance(action, dict):
            action_type = action.get("type")
            action_args = {k: _model_dump(v) for k, v in action.items() if k != "type"}
            return {"type": action_type, "args": action_args}

        if hasattr(action, "model_dump"):
            raw = action.model_dump()
            action_type = raw.get("type")
            action_args = {k: _model_dump(v) for k, v in raw.items() if k != "type"}
            return {"type": action_type, "args": action_args}

        if hasattr(action, "to_dict"):
            raw = action.to_dict()
            action_type = raw.get("type")
            action_args = {k: _model_dump(v) for k, v in raw.items() if k != "type"}
            return {"type": action_type, "args": action_args}

        action_type = getattr(action, "type", None)
        action_args: Dict[str, Any] = {}
        for attr in dir(action):
            if attr.startswith("_") or attr == "type":
                continue
            try:
                action_args[attr] = _model_dump(getattr(action, attr))
            except Exception:
                continue
        return {"type": action_type, "args": action_args}

    def _convert_drag_path(self, args: Dict[str, Any]) -> Optional[str]:
        path = args.get("path")
        if not path and args.get("from") and args.get("to"):
            path = [args["from"], args["to"]]
        if not path or len(path) < 2:
            return None

        def point_xy(point: Any) -> Tuple[Any, Any]:
            if isinstance(point, (list, tuple)) and len(point) == 2:
                return point[0], point[1]
            if isinstance(point, dict):
                return point.get("x"), point.get("y")
            return getattr(point, "x", None), getattr(point, "y", None)

        first_x, first_y = point_xy(path[0])
        if first_x is None or first_y is None:
            return None

        commands = [f"import pyautogui\npyautogui.moveTo({first_x}, {first_y})"]
        for point in path[1:]:
            x, y = point_xy(point)
            if x is None or y is None:
                return None
            commands.append(f"pyautogui.dragTo({x}, {y}, duration=0.2, button='left')")
        return "\n".join(commands)

    def _typing_strategy(self, text: str) -> str:
        if text == "":
            return "empty"
        if not text.isascii():
            return "clipboard"
        if "\n" in text:
            return "multiline_ascii"
        if text.isascii():
            return "single_line_ascii"
        return "clipboard"

    def _summarize_type_payload(self, text: str) -> Dict[str, Any]:
        return {
            "strategy": self._typing_strategy(text),
            "chars": len(text),
            "lines": len(text.split("\n")) if text else 0,
            "ascii": text.isascii(),
            "trailing_newline": text.endswith("\n"),
            "preview": _preview_text(text),
        }

    def _build_multiline_ascii_type_command(self, text: str) -> str:
        commands = ["import pyautogui"]
        lines = text.split("\n")
        for index, line in enumerate(lines):
            if line:
                commands.append(f"pyautogui.typewrite({repr(line)}, interval=0.03)")
            if index < len(lines) - 1:
                commands.append("pyautogui.press('enter')")
        return "\n".join(commands)

    def _build_clipboard_paste_command(self, text: str, paste_keys: Tuple[str, ...] = ("ctrl", "v")) -> str:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        keys = ", ".join(repr(key) for key in paste_keys)
        return (
            "import base64, time, pyautogui, pyperclip\n"
            f"_text = base64.b64decode('{encoded}').decode('utf-8')\n"
            "pyperclip.copy(_text)\n"
            "time.sleep(0.1)\n"
            f"pyautogui.hotkey({keys})\n"
            "time.sleep(0.1)"
        )

    def _convert_action_to_pyautogui(self, action_type: str, args: Dict[str, Any]) -> Optional[str]:
        if not action_type:
            return None

        key_mapping = {
            "alt": "alt",
            "arrowdown": "down",
            "arrowleft": "left",
            "arrowright": "right",
            "arrowup": "up",
            "backspace": "backspace",
            "capslock": "capslock",
            "cmd": "command",
            "command": "command",
            "ctrl": "ctrl",
            "delete": "delete",
            "end": "end",
            "enter": "enter",
            "esc": "esc",
            "home": "home",
            "insert": "insert",
            "option": "option",
            "pagedown": "pagedown",
            "pageup": "pageup",
            "shift": "shift",
            "space": "space",
            "super": "super",
            "tab": "tab",
            "win": "win",
        }

        try:
            if action_type == "click":
                x = args.get("x")
                y = args.get("y")
                button = args.get("button", "left")
                if x is None or y is None:
                    return None
                if button not in ["left", "middle", "right"]:
                    button = "left"
                return (
                    f"import pyautogui\n"
                    f"pyautogui.moveTo({x}, {y})\n"
                    f"pyautogui.click(button='{button}')"
                )

            if action_type == "double_click":
                x = args.get("x")
                y = args.get("y")
                if x is None or y is None:
                    return None
                return (
                    f"import pyautogui\n"
                    f"pyautogui.moveTo({x}, {y})\n"
                    f"pyautogui.doubleClick()"
                )

            if action_type == "move":
                x = args.get("x")
                y = args.get("y")
                if x is None or y is None:
                    return None
                return f"import pyautogui\npyautogui.moveTo({x}, {y})"

            if action_type == "drag":
                return self._convert_drag_path(args)

            if action_type == "type":
                text = args.get("text", "")
                summary = self._summarize_type_payload(text)
                logger.info("Type action payload: %s", summary)
                if text == "":
                    return "import time\ntime.sleep(0.1)"
                strategy = summary["strategy"]
                if strategy == "multiline_ascii":
                    return self._build_multiline_ascii_type_command(text)
                if strategy == "clipboard":
                    return self._build_clipboard_paste_command(text)
                return f"import pyautogui\npyautogui.typewrite({repr(text)}, interval=0.03)"

            if action_type == "keypress":
                keys = args.get("keys")
                if not keys and args.get("key"):
                    keys = [args.get("key")]
                if not keys:
                    return None
                if not isinstance(keys, (list, tuple)):
                    keys = [keys]
                mapped_keys = []
                for key in keys:
                    normalized = key_mapping.get(str(key).lower(), str(key).lower())
                    mapped_keys.append(normalized)
                keys_str = ", ".join([repr(key) for key in mapped_keys])
                return f"import pyautogui\npyautogui.hotkey({keys_str})"

            if action_type == "scroll":
                x = args.get("x")
                y = args.get("y")
                scroll_x = int(
                    args.get("scroll_x")
                    or args.get("delta_x")
                    or args.get("deltaX")
                    or 0
                )
                scroll_y = int(
                    args.get("scroll_y")
                    or args.get("delta_y")
                    or args.get("deltaY")
                    or 0
                )
                position = f", x={x}, y={y}" if x is not None and y is not None else ""
                if scroll_y:
                    return f"import pyautogui\npyautogui.scroll({scroll_y * -1}{position})"
                if scroll_x:
                    return f"import pyautogui\npyautogui.hscroll({scroll_x * -1}{position})"
                return None

            if action_type == "wait":
                secs = max(0.1, float(args.get("ms", 1000)) / 1000.0)
                return f"import time\ntime.sleep({secs})"

            if action_type == "screenshot":
                return "import time\ntime.sleep(0.1)"
        except Exception:
            logger.exception("Failed to convert GPT-5.4 computer action: %s", action_type)
            return None

        logger.warning("Unsupported GPT-5.4 computer action: %s", action_type)
        return None

    def _message_text(self, item: Any) -> str:
        content = _get_field(item, "content", [])
        if not content:
            return ""
        if isinstance(content, list):
            parts = []
            for part in content:
                part_type = _get_field(part, "type")
                if part_type == "output_text":
                    parts.append(_get_field(part, "text", ""))
            return "\n".join([part for part in parts if part])
        return str(content)

    def _reasoning_text(self, item: Any) -> str:
        summary = _get_field(item, "summary", [])
        if not summary:
            return ""
        if isinstance(summary, list):
            parts = []
            for part in summary:
                text = _get_field(part, "text", "")
                if text:
                    parts.append(text)
            return "\n".join(parts)
        return str(summary)

    def predict(self, instruction: str, obs: Dict[str, Any]) -> List[Any]:
        home_dir = "C:\\Users\\user" if self.platform.lower().startswith("win") else "/home/user"
        instructions = OPERATOR_PROMPT.format(
            CLIENT_PASSWORD=self.client_password,
            CURRENT_DATE=datetime.now().strftime("%A, %B %d, %Y"),
            HOME_DIR=home_dir,
            PLATFORM=self.platform,
        )
        if self.gui_only_instruction_suffix:
            instructions += "\n" + self.gui_only_instruction_suffix + "\n"
        if self.is_interactive:
            instructions += INTERACTIVE_PROMPT_SUFFIX

        # Consume pending user messages once at the top
        pending_user_text = self._format_additional_user_messages(self.pending_user_messages)
        self.pending_user_messages = []

        screenshot_b64 = encode_image(obs["screenshot"])

        if not self.previous_response_id:
            # ── Case 1: First request ──
            # Append any early user messages to the task instruction text.
            task_text = instruction
            if pending_user_text:
                task_text = f"{instruction}\n\n{pending_user_text}"
            request_input = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": task_text,
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{screenshot_b64}",
                            "detail": "original",
                        },
                    ],
                }
            ]
        else:
            request_input = list(self.pending_input_items)

            if self.pending_user_call_id and pending_user_text:
                # ── Case 2: Responding to call_user ──
                # Deliver user reply ONLY as function_call_output (no duplication).
                request_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": self.pending_user_call_id,
                        "output": pending_user_text,
                    }
                )
                self.pending_user_call_id = None
                # Already consumed via function_call_output; do not inject again.
                pending_user_text = ""

            if pending_user_text or not request_input:
                # ── Case 3: Unsolicited user message (phase transition) or empty input ──
                # When previous_response_id is present, the latest screen state
                # must travel via computer_call_output only. Adding input_image
                # to the user message triggers a Responses API 400.
                continue_text = "Continue from the latest screenshot."
                if pending_user_text:
                    continue_text = f"{continue_text}\n\n[New message from user]:\n{pending_user_text}"
                request_input.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": continue_text,
                            },
                        ],
                    }
                )

        with Timer() as model_timer:
            response = self._create_response(request_input, instructions)

        self.previous_response_id = _get_field(response, "id")
        self.pending_input_items = []

        raw_output = _get_field(response, "output", []) or []
        actions: List[Any] = []
        responses: List[str] = []
        unsupported_action = False
        infeasible_message = False
        call_user_requested = False

        for item in raw_output:
            item_type = _get_field(item, "type")
            if item_type == "message":
                message_text = self._message_text(item)
                if message_text:
                    responses.append(message_text)
                    lower = message_text.lower()
                    if "[infeasible]" in lower or any(
                        token in lower
                        for token in ["infeasible", "unfeasible", "impossible", "cannot be done", "not feasible"]
                    ):
                        infeasible_message = True
            elif item_type == "reasoning":
                reasoning_text = self._reasoning_text(item)
                if reasoning_text:
                    responses.append(reasoning_text)
            elif item_type == "function_call":
                tool_name = _get_field(item, "name", "")
                if tool_name != "call_user":
                    unsupported_action = True
                    responses.append(f"Unsupported function tool from model: {tool_name}")
                    continue

                raw_arguments = _get_field(item, "arguments", {})
                if isinstance(raw_arguments, str):
                    try:
                        raw_arguments = json.loads(raw_arguments)
                    except json.JSONDecodeError:
                        raw_arguments = {"question": raw_arguments}
                elif raw_arguments is None:
                    raw_arguments = {}

                question = str(raw_arguments.get("question", "")).strip()
                self.pending_user_call_id = _get_field(item, "call_id", None)
                call_user_requested = True
                actions.append("CALL_USER")
                responses.append(f"[CALL_USER] {question}" if question else "[CALL_USER]")
            elif item_type == "computer_call":
                logger.info("Raw computer_call item: %s", _sanitize_for_log(item))
                raw_actions = _get_field(item, "actions")
                if raw_actions is None:
                    single_action = _get_field(item, "action")
                    raw_actions = [single_action] if single_action is not None else []

                call_id = _get_field(item, "call_id", "")
                pending_checks = _model_dump(_get_field(item, "pending_safety_checks", []))
                raw_actions = list(raw_actions)
                batch_size = len(raw_actions)

                for index, raw_action in enumerate(raw_actions):
                    action_info = self._action_to_dict(raw_action)
                    logger.info(
                        "Raw tool action %d/%d for call_id=%s: %s",
                        index + 1,
                        batch_size,
                        call_id,
                        _sanitize_for_log(action_info),
                    )
                    pyautogui_code = self._convert_action_to_pyautogui(
                        action_info["type"],
                        action_info["args"],
                    )
                    if not pyautogui_code:
                        unsupported_action = True
                        responses.append(
                            f"Unsupported computer action from model: {action_info['type']}"
                        )
                        continue
                    actions.append(
                        {
                            "action_space": "pyautogui",
                            "action": pyautogui_code,
                            "pending_checks": pending_checks,
                            "call_id": call_id,
                            "batch_index": index,
                            "batch_size": batch_size,
                            "batch_last": index == batch_size - 1,
                        }
                    )

        if call_user_requested:
            actions = ["CALL_USER"]

        state_correct = bool(actions) and not unsupported_action and not infeasible_message
        if unsupported_action:
            actions = []

        predict_info = {
            "model_usage": {
                "model_time": model_timer.duration,
                "prompt_tokens": _get_field(_get_field(response, "usage", {}), "input_tokens", 0),
                "completion_tokens": _get_field(_get_field(response, "usage", {}), "output_tokens", 0),
            },
            "messages": _model_dump(raw_output),
            "response": "\n".join([item for item in responses if item]),
            "state_correct": state_correct,
        }

        logger.info("Model response text: %s", predict_info["response"])
        logger.info("Model returned %d action(s)", len(actions))
        logger.debug("Model raw output messages: %s", _sanitize_for_log(predict_info["messages"]))

        return predict_info, actions

    def reset(self, _logger=None, vm_ip=None):
        global logger
        logger = _logger if _logger is not None else logging.getLogger("desktopenv.agent")
        self.previous_response_id = None
        self.pending_input_items = []
        self.current_batch_call_id = None
        self.current_batch_expected_outputs = 0
        self.pending_user_messages = []
        self.pending_user_call_id = None
        self.is_interactive = False
        self.gui_only_instruction_suffix = ""

    def step(self, action: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        try:
            if not action:
                raise StepError("Empty action received")

            with Timer() as step_timer:
                step_action = Action(action["action"], self.action_space)
                obs, reward, terminated, info = self.env.step(
                    step_action.get_action(),
                    self.sleep_after_execution,
                )

                if action.get("batch_last"):
                    screenshot_base64 = encode_image(obs["screenshot"])
                    output_item = {
                        "type": "computer_call_output",
                        "call_id": action.get("call_id", ""),
                        "output": {
                            "type": "computer_screenshot",
                            "image_url": f"data:image/png;base64,{screenshot_base64}",
                            "detail": "original",
                        },
                    }
                    pending_checks = action.get("pending_checks") or []
                    if pending_checks:
                        output_item["acknowledged_safety_checks"] = pending_checks
                    self.pending_input_items.append(output_item)

            return obs, reward, terminated, info, {
                "step_time": step_timer.duration,
                "action": action,
            }
        except Exception as exc:
            logger.exception("GPT54Agent step failed: %s", exc)
            raise StepError(f"Failed to execute step: {exc}")
