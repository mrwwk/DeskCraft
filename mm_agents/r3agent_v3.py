import base64
import json
import logging
import os
import re
import time
from io import BytesIO
from typing import Dict, List, Tuple

from http import HTTPStatus
import dashscope
from dashscope import MultiModalConversation
import backoff
import openai
from PIL import Image
from requests.exceptions import SSLError
from google.api_core.exceptions import (
    InvalidArgument,
    ResourceExhausted,
    InternalServerError,
    BadRequest,
)
from mm_agents.utils.qwen_vl_utils import smart_resize
import httpx

logger = None

MAX_RETRY_TIMES = 5

INTERACTIVE_PROMPT_SUFFIX = """

This is an interactive session.
- If the instruction is ambiguous or missing details, call `call_user` to ask a precise clarification question.
- If the user provides an update or changes the requirement later, incorporate it and continue from the current desktop state.
- Do not pretend the user already answered if they have not.
"""

CALL_USER_TOOL_DEF = {
    "type": "function",
    "function": {
        "name_for_human": "call_user",
        "name": "call_user",
        "description": "Ask the user for clarification when the instruction is ambiguous, incomplete, or updated mid-task.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "A short, specific question for the user."
                }
            },
            "required": ["question"],
        },
        "args_format": "Format the arguments as a JSON object."
    }
}


def encode_image(image_content):
    return base64.b64encode(image_content).decode("utf-8")


def process_image(image_bytes):
    """
    Process an image for Qwen VL models (thinking variant).
    Uses a tighter resize cap consistent with the thinking DUN agent.
    """
    image = Image.open(BytesIO(image_bytes))
    width, height = image.size

    resized_height, resized_width = smart_resize(
        height=height,
        width=width,
        factor=32,
        max_pixels=16 * 16 * 4 * 12800,
    )

    image = image.resize((resized_width, resized_height))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    processed_bytes = buffer.getvalue()

    return base64.b64encode(processed_bytes).decode("utf-8")


def get_system_message_l1():
    # Tool def for computer use
    description_prompt_lines = [
        "Use a mouse and keyboard to interact with a computer, and take screenshots.",
        "* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.",
        "* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try wait and taking another screenshot.",
        "* The screen's resolution is 1000x1000.",
        "* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.",
        "* If you tried clicking on a program or link but it failed to load even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.",
        "* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.",
    ]
    description_prompt = "\n".join(description_prompt_lines)

    action_description_prompt = """* `left_click`: Click the left mouse button at the specified (x, y) coordinate.
* `right_click`: Click the right mouse button at the specified (x, y) coordinate.
* `middle_click`: Click the middle mouse button at the specified (x, y) coordinate.
* `double_click`: Double-click the left mouse button at the specified (x, y) coordinate.
* `triple_click`: Triple-click the left mouse button at a specified (x, y) coordinate.
* `drag`: Click and drag the mouse cursor from its current position to the specified (x, y) coordinate.
* `mouse_move`: Move the cursor to the specified (x, y) coordinate without clicking.
* `type`: Type a specified string of text.
* `hotkey`: Press a combination of keys (e.g., ["ctrl", "v"]).
* `press`: Press a single key or a sequence of keys, provided as an array of strings (e.g., ["backspace"], ["enter"], ["a", "b", "c"]).
* `key_down`: Press and HOLD the specified key(s) down in order (no release). Use this for stateful holds like holding Shift while clicking.
* `key_up`: Release the specified key(s) in reverse order.
* `scroll`: Scroll the mouse wheel by a specified number of pixels. Use "direction" to specify vertical (default, positive for up, negative for down) or horizontal (positive for right, negative for left) scrolling.
* `wait`: Pause execution for a specified number of seconds.
* `finished`: Terminate the task and indicate whether it was a 'success' or 'failure'."""

    tools_def = {
        "type": "function",
        "function": {
            "name_for_human": "computer_use",
            "name": "computer_use",
            "description": description_prompt,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": action_description_prompt,
                        "enum": [
                            "left_click", "right_click", "middle_click", "double_click", "triple_click",
                            "drag", "mouse_move", "type", "hotkey", "press", "key_up", "key_down",
                            "scroll", "wait", "finished"
                        ]
                    },
                    "coordinate": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "The (x, y) coordinates (0-999). Required for: clicks, mouse_move, drag."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type. Required only for `action=type`."
                    },
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of key names (e.g. ['a'], ['ctrl', 'c']). Required for: hotkey, press, key_down, key_up."
                    },
                    "pixels": {
                        "type": "integer",
                        "description": "The number of pixels to scroll. Required only for `action=scroll`."
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["vertical", "horizontal"],
                        "description": "The scroll direction. 'vertical' (default) for up/down scrolling, 'horizontal' for left/right scrolling. Required only for `action=scroll`."
                    },
                    "time": {
                        "type": "number",
                        "description": "Seconds to wait. Required only for `action=wait`."
                    },
                    "status": {
                        "type": "string",
                        "enum": ["success", "failure"],
                        "description": "The outcome of the task. Required only for `action=finished`."
                    }
                },
                "required": ["action"],
                "type": "object"
            },
            "args_format": "Format the arguments as a JSON object."
        }
    }

    system_prompt = """You are a helpful GUI agent.

# Tool
You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
""" + json.dumps(tools_def) + """
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>

# Response format

Response format for every step:
1) Action: A single <action>...</action> block containing a short imperative describing what to do in the UI.
2) A single or multiple <tool_call>...</tool_call> blocks containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

Rules:
- Output exactly in the order: <action>...</action>, <tool_call>...</tool_call>.
- Be brief: one sentence for action description.
- Do not output anything else outside those parts.
- If finishing, use action=finished in the tool call."""
    
    return system_prompt.strip()



def get_system_message_l2():
    # Tool def for computer use
    description_prompt_lines = [
        "Use a mouse and keyboard to interact with a computer, and take screenshots.",
        "* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.",
        "* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try wait and taking another screenshot.",
        "* The screen's resolution is 1000x1000.",
        "* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.",
        "* If you tried clicking on a program or link but it failed to load even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.",
        "* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.",
    ]
    description_prompt = "\n".join(description_prompt_lines)

    action_description_prompt = """* `left_click`: Click the left mouse button at the specified (x, y) coordinate.
* `right_click`: Click the right mouse button at the specified (x, y) coordinate.
* `middle_click`: Click the middle mouse button at the specified (x, y) coordinate.
* `double_click`: Double-click the left mouse button at the specified (x, y) coordinate.
* `triple_click`: Triple-click the left mouse button at a specified (x, y) coordinate.
* `drag`: Click and drag the mouse cursor from its current position to the specified (x, y) coordinate.
* `mouse_move`: Move the cursor to the specified (x, y) coordinate without clicking.
* `type`: Type a specified string of text.
* `hotkey`: Press a combination of keys (e.g., ["ctrl", "v"]).
* `press`: Press a single key or a sequence of keys, provided as an array of strings (e.g., ["backspace"], ["enter"], ["a", "b", "c"]).
* `key_down`: Press and HOLD the specified key(s) down in order (no release). Use this for stateful holds like holding Shift while clicking.
* `key_up`: Release the specified key(s) in reverse order.
* `scroll`: Scroll the mouse wheel by a specified number of pixels. Use "direction" to specify vertical (default, positive for up, negative for down) or horizontal (positive for right, negative for left) scrolling.
* `wait`: Pause execution for a specified number of seconds.
* `finished`: Terminate the task and indicate whether it was a 'success' or 'failure'."""

    tools_def = {
        "type": "function",
        "function": {
            "name_for_human": "computer_use",
            "name": "computer_use",
            "description": description_prompt,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": action_description_prompt,
                        "enum": [
                            "left_click", "right_click", "middle_click", "double_click", "triple_click",
                            "drag", "mouse_move", "type", "hotkey", "press", "key_up", "key_down",
                            "scroll", "wait", "finished"
                        ]
                    },
                    "coordinate": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "The (x, y) coordinates (0-999). Required for: clicks, mouse_move, drag."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type. Required only for `action=type`."
                    },
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of key names (e.g. ['a'], ['ctrl', 'c']). Required for: hotkey, press, key_down, key_up."
                    },
                    "pixels": {
                        "type": "integer",
                        "description": "The number of pixels to scroll. Required only for `action=scroll`."
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["vertical", "horizontal"],
                        "description": "The scroll direction. 'vertical' (default) for up/down scrolling, 'horizontal' for left/right scrolling. Required only for `action=scroll`."
                    },
                    "time": {
                        "type": "number",
                        "description": "Seconds to wait. Required only for `action=wait`."
                    },
                    "status": {
                        "type": "string",
                        "enum": ["success", "failure"],
                        "description": "The outcome of the task. Required only for `action=finished`."
                    }
                },
                "required": ["action"],
                "type": "object"
            },
            "args_format": "Format the arguments as a JSON object."
        }
    }

    system_prompt = """You are a helpful GUI agent.

# Tool
You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
""" + json.dumps(tools_def) + """
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>

# Response format

Response format for every step:
1) Thought: A single <think>...</think> block containing step by step progress assessment and next action analysis.
2) Action: A single <action>...</action> block containing a short imperative describing what to do in the UI.
3) Tool Execution: A single or multiple <tool_call>...</tool_call> blocks containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

Rules:
- Output exactly in the order: <think>...</think>, <action>...</action>, <tool_call>...</tool_call>.
- From a first-person perspective, systematically assess progress and errors, evaluate potential next steps, and precisely plan text inputs (cursor position and expected outcomes)
- Be brief for Action: one sentence for action description.
- Do not output anything else outside those parts.
- If finishing, use action=finished in the tool call."""

    return system_prompt.strip()



def get_system_message_l3():
    # Tool def for computer use
    description_prompt_lines = [
        "Use a mouse and keyboard to interact with a computer, and take screenshots.",
        "* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.",
        "* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try wait and taking another screenshot.",
        "* The screen's resolution is 1000x1000.",
        "* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.",
        "* If you tried clicking on a program or link but it failed to load even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.",
        "* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.",
    ]
    description_prompt = "\n".join(description_prompt_lines)

    action_description_prompt = """* `left_click`: Click the left mouse button at the specified (x, y) coordinate.
* `right_click`: Click the right mouse button at the specified (x, y) coordinate.
* `middle_click`: Click the middle mouse button at the specified (x, y) coordinate.
* `double_click`: Double-click the left mouse button at the specified (x, y) coordinate.
* `triple_click`: Triple-click the left mouse button at a specified (x, y) coordinate.
* `drag`: Click and drag the mouse cursor from its current position to the specified (x, y) coordinate.
* `mouse_move`: Move the cursor to the specified (x, y) coordinate without clicking.
* `type`: Type a specified string of text.
* `hotkey`: Press a combination of keys (e.g., ["ctrl", "v"]).
* `press`: Press a single key or a sequence of keys, provided as an array of strings (e.g., ["backspace"], ["enter"], ["a", "b", "c"]).
* `key_down`: Press and HOLD the specified key(s) down in order (no release). Use this for stateful holds like holding Shift while clicking.
* `key_up`: Release the specified key(s) in reverse order.
* `scroll`: Scroll the mouse wheel by a specified number of pixels. Use "direction" to specify vertical (default, positive for up, negative for down) or horizontal (positive for right, negative for left) scrolling.
* `wait`: Pause execution for a specified number of seconds.
* `finished`: Terminate the task and indicate whether it was a 'success' or 'failure'."""

    tools_def = {
        "type": "function",
        "function": {
            "name_for_human": "computer_use",
            "name": "computer_use",
            "description": description_prompt,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": action_description_prompt,
                        "enum": [
                            "left_click", "right_click", "middle_click", "double_click", "triple_click",
                            "drag", "mouse_move", "type", "hotkey", "press", "key_up", "key_down",
                            "scroll", "wait", "finished"
                        ]
                    },
                    "coordinate": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "The (x, y) coordinates (0-999). Required for: clicks, mouse_move, drag."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type. Required only for `action=type`."
                    },
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "An array of key names (e.g. ['a'], ['ctrl', 'c']). Required for: hotkey, press, key_down, key_up."
                    },
                    "pixels": {
                        "type": "integer",
                        "description": "The number of pixels to scroll. Required only for `action=scroll`."
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["vertical", "horizontal"],
                        "description": "The scroll direction. 'vertical' (default) for up/down scrolling, 'horizontal' for left/right scrolling. Required only for `action=scroll`."
                    },
                    "time": {
                        "type": "number",
                        "description": "Seconds to wait. Required only for `action=wait`."
                    },
                    "status": {
                        "type": "string",
                        "enum": ["success", "failure"],
                        "description": "The outcome of the task. Required only for `action=finished`."
                    }
                },
                "required": ["action"],
                "type": "object"
            },
            "args_format": "Format the arguments as a JSON object."
        }
    }

    system_prompt = """You are a helpful GUI agent.

# Tool
You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
""" + json.dumps(tools_def) + """
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>

# Response format

Response format for every step:
1) Observation: A single <observation>...</observation> block describing the current computer state based on the full screenshot. 
2) Thought: A single <think>...</think> block containing step by step progress assessment and next action analysis.
3) Action: A single <action>...</action> block containing a short imperative describing what to do in the UI.
4) Tool Execution: A single or multiple <tool_call>...</tool_call> blocks containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

Rules:
- Output exactly in the order: <observation>...</observation>, <think>...</think>, <action>...</action>, <tool_call>...</tool_call>.
- For Observation: provide a detailed visual audit of the current state, identifying active applications, interface layouts, and all UI elements or clues relevant to the task goal.
- For Thought: from a first-person perspective, systematically assess progress and errors, evaluate potential next steps, and precisely plan text inputs (cursor position and expected outcomes)
- Be brief for Action: one sentence for action description.
- Do not output anything else outside those parts.
- If finishing, use action=finished in the tool call."""

    return system_prompt.strip()


def _inject_call_user_tool(system_prompt: str) -> str:
    """Insert the call_user tool definition into the <tools> block of the system prompt."""
    call_user_json = json.dumps(CALL_USER_TOOL_DEF)
    # Insert before the closing </tools> tag
    return system_prompt.replace("</tools>", f"\n{call_user_json}\n</tools>", 1)


def _build_system_prompt(prompt_type: str = "l1"):
    if prompt_type == "l1":
        return get_system_message_l1()
    elif prompt_type == "l2":
        return get_system_message_l2()
    elif prompt_type == "l3":
        return get_system_message_l3()
    else:
        raise ValueError(f"Invalid prompt type: {prompt_type}")


def _extract_action_text(response: str) -> str:
    match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).strip()


def _extract_tool_calls(response: str) -> List[str]:
    return re.findall(r"<tool_call>\s*(.*?)\s*</tool_call>", response, re.DOTALL | re.IGNORECASE)


def _compact_response_for_history(response: str, include_observation: bool = False, include_thinking: bool = False, prompt_type: str = "l1") -> str:
    if include_observation:
        assert prompt_type in ["l3"], "Observation is only supported for prompt type l3"
        match = re.search(r"<observation\b[^>]*>", response, re.IGNORECASE)
        if not match:
            return response
        return response[match.start():].strip()

    if include_thinking:
        assert prompt_type in ["l2", "l3"], "Thinking is only supported for prompt type l2 and l3"
        match = re.search(r"<think\b[^>]*>", response, re.IGNORECASE)
        if not match:
            # fallback: try from <action>
            return response
        return response[match.start():].strip()
    
    # do not include observation and thinking, only include action
    match = re.search(r"<action\b[^>]*>", response, re.IGNORECASE)
    if not match:
        return response

    return response[match.start():].strip()


def _parse_tool_call_payload(tool_call_str: str) -> dict:
    tool_call_str = tool_call_str.strip()
    try:
        return json.loads(tool_call_str)
    except json.JSONDecodeError:
        start = tool_call_str.find("{")
        end = tool_call_str.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(tool_call_str[start : end + 1])
    raise


def _scale_coordinate(x: float, y: float, original_width: int, original_height: int, coordinate_type: str) -> Tuple[int, int]:
    if coordinate_type == "absolute":
        return int(x), int(y)
    x_scale = original_width / 999.0
    y_scale = original_height / 999.0
    return int(x * x_scale), int(y * y_scale)

def _clean_keys(raw_keys):
    keys = raw_keys if isinstance(raw_keys, list) else [raw_keys]
    cleaned_keys = []
    for key in keys:
        if isinstance(key, str):
            if key.startswith("keys=["):
                key = key[6:]
            if key.endswith("]"):
                key = key[:-1]
            if key.startswith("['") or key.startswith('["'):
                key = key[2:] if len(key) > 2 else key
            if key.endswith("']") or key.endswith('"]'):
                key = key[:-2] if len(key) > 2 else key
            key = key.strip()
            cleaned_keys.append(key)
        else:
            cleaned_keys.append(key)
    return cleaned_keys


def _to_pyautogui_code(
    action: str,
    args: dict,
    original_width: int,
    original_height: int,
    coordinate_type: str,
) -> str:
    if action in ("left_click", "click", "right_click", "middle_click", "double_click", "triple_click", "drag", "mouse_move"):
        if "coordinate" in args and isinstance(args["coordinate"], (list, tuple)) and len(args["coordinate"]) >= 2:
            x, y = args["coordinate"][:2]
            adj_x, adj_y = _scale_coordinate(float(x), float(y), original_width, original_height, coordinate_type)
        else:
            adj_x, adj_y = None, None

    if action in ["left_click", "click"]:
        if adj_x is not None:
            return f"pyautogui.click({adj_x}, {adj_y})"
        return "pyautogui.click()"

    if action == "right_click":
        if adj_x is not None:
            return f"pyautogui.rightClick({adj_x}, {adj_y})"
        return "pyautogui.rightClick()"

    if action == "middle_click":
        if adj_x is not None:
            return f"pyautogui.middleClick({adj_x}, {adj_y})"
        return "pyautogui.middleClick()"

    if action == "double_click":
        if adj_x is not None:
            return f"pyautogui.doubleClick({adj_x}, {adj_y})"
        return "pyautogui.doubleClick()"
    
    if action == "triple_click":
        if adj_x is not None:
            return f"pyautogui.tripleClick({adj_x}, {adj_y})"
        return "pyautogui.tripleClick()"

    if action == "drag":
        duration = args.get("duration", 0.5)
        if adj_x is not None:
            if duration is not None:
                return f"pyautogui.dragTo({adj_x}, {adj_y}, duration={duration})"
            return f"pyautogui.dragTo({adj_x}, {adj_y})"
        return "pyautogui.dragTo(0, 0)"

    if action == "mouse_move":
        if adj_x is not None:
            return f"pyautogui.moveTo({adj_x}, {adj_y})"
        return "pyautogui.moveTo(0, 0)"

    if action == "type":
        text = args.get("text", "")
        try:
            text = text.encode('latin-1', 'backslashreplace').decode('unicode_escape')
        except Exception as e:
            logger.error(f"Failed to unescape text: {e}")

        logger.info(f"Pyautogui code[before rewrite]: {text}")

        code_str = ""
        for char in text:
            if char == '\n':
                code_str += "pyautogui.press('enter')\n"
            elif char == "'":
                code_str += 'pyautogui.press("\'")\n'
            elif char == '\\':
                code_str += "pyautogui.press('\\\\')\n"
            elif char == '"':
                code_str += "pyautogui.press('\"')\n"
            else:
                code_str += f"pyautogui.press('{char}')\n"

        logger.info(f"Pyautogui code[after rewrite]: {code_str}")
        return code_str

    if action == "hotkey":
        keys = args.get("keys", [])
        if isinstance(keys, str):
            keys = keys.split("+")
            keys = [key.strip() for key in keys]
        if isinstance(keys, list):
            cleaned_keys = []
            for key in keys:
                if isinstance(key, str):
                    if key.startswith("keys=["):
                        key = key[6:]
                    if key.endswith("]"):
                        key = key[:-1]
                    if key.startswith("['") or key.startswith('["'):
                        key = key[2:] if len(key) > 2 else key
                    if key.endswith("']") or key.endswith('"]'):
                        key = key[:-2] if len(key) > 2 else key
                    key = key.strip()
                    # Handle cases like "ctrl+alt+t" - split by + and add all parts
                    # But don't split if the key itself is just "+"
                    if "+" in key and key != "+":
                        split_keys = [k.strip() for k in key.split("+")]
                        cleaned_keys.extend(split_keys)
                    else:
                        cleaned_keys.append(key)
                else:
                    cleaned_keys.append(key)
            keys = cleaned_keys
        elif keys is not None:
            keys = [keys]
        else:
            keys = []

        keys_str = ", ".join([f"'{key}'" for key in keys])
        if len(keys) > 1:
            return f"pyautogui.hotkey({keys_str})"
        return f"pyautogui.press({keys_str})"

    if action == "press":
        keys = args.get("keys", [])
        if isinstance(keys, list):
            cleaned_keys = []
            for key in keys:
                if isinstance(key, str):
                    if key.startswith("keys=["):
                        key = key[6:]
                    if key.endswith("]"):
                        key = key[:-1]
                    if key.startswith("['") or key.startswith('["'):
                        key = key[2:] if len(key) > 2 else key
                    if key.endswith("']") or key.endswith('"]'):
                        key = key[:-2] if len(key) > 2 else key
                    key = key.strip()
                    cleaned_keys.append(key)
                else:
                    cleaned_keys.append(key)
            keys = cleaned_keys
        elif keys is not None:
            keys = [keys]
        else:
            keys = []

        if len(keys) == 1:
            return f"pyautogui.press({repr(keys[0])})"
        return f"pyautogui.press({repr(keys)})"

    if action == "key_down":
        keys = _clean_keys(args.get("keys", []))
        key_down_list = []
        for k in keys:
            key_down_list.append(f"pyautogui.keyDown('{k}')")
        return key_down_list

    if action == "key_up":
        keys = _clean_keys(args.get("keys", []))
        key_up_list = []
        for k in reversed(keys):
            key_up_list.append(f"pyautogui.keyUp('{k}')")
        return key_up_list

    if action in ["sroll", "scroll"]:
        pixels = args.get("pixels", 0)
        direction = args.get("direction", "vertical")
        if direction == "horizontal":
            return f"pyautogui.hscroll({pixels})"
        return f"pyautogui.scroll({pixels})"

    if action == "wait":
        return "WAIT"

    if action == "finished":
        status = str(args.get("status", "")).lower()
        return "DONE" if status.lower() in ["success", "successful", "yes", "ok"] else "FAIL"

    return ""


def parse_response(response: str, original_width: int, original_height: int, coordinate_type: str) -> Tuple[str, List[str]]:
    low_level_instruction = _extract_action_text(response)
    if not low_level_instruction:
        return "<Error>: no <action> block found in response", ["FAIL"]

    tool_calls = _extract_tool_calls(response)
    if not tool_calls:
        return "<Error>: no <tool_call> blocks found in response", ["FAIL"]

    pyautogui_codes = []
    for tool_call in tool_calls:
        try:
            tool_obj = _parse_tool_call_payload(tool_call)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse tool call JSON: {exc}")
            pyautogui_codes.append("FAIL")
            continue

        # Handle call_user tool (interactive mode)
        if tool_obj.get("name") == "call_user":
            args = tool_obj.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"question": args}
            question = str(args.get("question", "")).strip()
            return f"[CALL_USER] {question}" if question else "[CALL_USER]", ["CALL_USER"]

        if tool_obj.get("name") != "computer_use":
            logger.warning(f"Unsupported tool name: {tool_obj.get('name')}")
            continue

        args = tool_obj.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)

        action = args.get("action")
        if not action:
            logger.error("Tool call missing action field")
            pyautogui_codes.append("FAIL")
            continue

        code = _to_pyautogui_code(action, args, original_width, original_height, coordinate_type)
        if not code:
            logger.error(f"Unsupported action: {action}")
            pyautogui_codes.append("FAIL")
            continue

        if isinstance(code, list):
            pyautogui_codes.extend(code)
        else:
            pyautogui_codes.append(code)

    if not pyautogui_codes:
        return "<Error>: no pyautogui code generated", ["FAIL"]

    # merge multiple pyautogui codes, but skip merging if ctrl/shift keyDown/keyUp present
    # force join if enter/backspace/tab/space appear in any code
    if len(pyautogui_codes) > 1:
        has_modifier = any("'ctrl'" in c or "'shift'" in c for c in pyautogui_codes
                           if "keyDown" in c or "keyUp" in c)
        force_join = any(k in c for c in pyautogui_codes
                         for k in ("'enter'", "'backspace'", "'tab'", "'space'"))
        if not has_modifier or force_join:
            return low_level_instruction, ["\n".join(pyautogui_codes)]

    return low_level_instruction, pyautogui_codes


class R3AgentV3:

    def __init__(
        self,
        platform: str = "ubuntu",
        model: str = "qwen3-vl",
        prompt_type: str = "l1",
        max_tokens: int = 32768,
        top_p: float = 0.9,
        temperature: float = 0.0,
        action_space: str = "pyautogui",
        observation_type: str = "screenshot",
        history_n: int = 3,
        add_thought_prefix: bool = False,
        include_observation_in_history: bool = False,
        include_thinking_in_history: bool = False,
        coordinate_type: str = "relative",
        api_backend: str = "openai",  # "openai" or "dashscope"
        enable_thinking: bool = False,  # Enable thinking mode for DashScope
        thinking_budget: int = 32768,  # Token budget for reasoning
        **kwargs,  # Accept extra kwargs from registry (name, max_steps, screen_size, etc.)
    ):
        self.platform = platform
        self.model = model
        self.prompt_type = prompt_type
        self.include_observation_in_history = include_observation_in_history
        self.include_thinking_in_history = include_thinking_in_history

        print(f"🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 Model: {self.model}🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")
        print(f"🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 Prompt type: {self.prompt_type}🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")
        print(f"🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀 🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")

        self.max_tokens = max_tokens
        self.top_p = top_p
        self.temperature = temperature
        self.action_space = action_space
        self.observation_type = observation_type
        self.history_n = history_n
        self.add_thought_prefix = add_thought_prefix
        self.coordinate_type = coordinate_type
        self.api_backend = api_backend
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

        assert action_space in ["pyautogui"], "Invalid action space"
        assert observation_type in ["screenshot"], "Invalid observation type"
        assert api_backend in ["openai", "dashscope"], "Invalid API backend, must be 'openai' or 'dashscope'"

        self.thoughts = []
        self.actions = []
        self.observations = []
        self.responses = []
        self.screenshots = []

        # Interactive mode state
        self.is_interactive = False
        self.pending_user_messages: List[str] = []

    def predict(self, instruction: str, obs: Dict) -> List:
        """
        Predict the next action(s) based on the current observation.
        Returns (response, pyautogui_code).
        """
        # Consume pending user messages (from interactive phase transitions or call_user replies)
        pending_user_text = ""
        if self.pending_user_messages:
            pending_user_text = "\n\n".join(
                f"[User Additional Message]:\n{m}" for m in self.pending_user_messages
            )
            self.pending_user_messages = []

        screenshot_bytes = obs["screenshot"]

        image = Image.open(BytesIO(screenshot_bytes))
        width, height = image.size
        print(f"Original screen resolution: {width}x{height}")

        processed_image = process_image(screenshot_bytes)
        processed_img = Image.open(
            BytesIO(base64.b64decode(processed_image))
        )
        processed_width, processed_height = processed_img.size
        print(
            "Processed image resolution: "
            f"{processed_width}x{processed_height}"
        )

        self.screenshots.append(processed_image)

        current_step = len(self.actions)
        history_start_idx = max(0, current_step - self.history_n)

        previous_actions = []
        for i in range(history_start_idx):
            if i < len(self.actions):
                previous_actions.append(f"Step {i+1}: {self.actions[i]}")
        previous_actions_str = (
            "\n".join(previous_actions) if previous_actions else "None"
        )

        system_prompt = _build_system_prompt(self.prompt_type)
        if self.is_interactive:
            system_prompt = _inject_call_user_tool(system_prompt)
            system_prompt += INTERACTIVE_PROMPT_SUFFIX

        instruction_prompt = f"""
Please generate the next move according to the UI screenshot, instruction and previous actions.

Instruction: {instruction}
"""
        if pending_user_text:
            instruction_prompt += f"\n{pending_user_text}\n"

        instruction_prompt += f"""
Previous actions:
{previous_actions_str}"""

        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_prompt},
                ],
            }
        ]

        history_len = min(self.history_n, len(self.responses))
        if history_len > 0:
            history_responses = [
                _compact_response_for_history(resp, include_observation=self.include_observation_in_history, include_thinking=self.include_thinking_in_history, prompt_type=self.prompt_type)
                for resp in self.responses[-history_len:]
            ]
            history_screenshots = self.screenshots[-history_len - 1:-1]

            for idx in range(history_len):
                if idx < len(history_screenshots):
                    screenshot_b64 = history_screenshots[idx]
                    if idx == 0:
                        img_url = f"data:image/png;base64,{screenshot_b64}"
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": img_url},
                                    },
                                    {"type": "text", "text": instruction_prompt},
                                ],
                            }
                        )
                    else:
                        img_url = f"data:image/png;base64,{screenshot_b64}"
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": img_url},
                                    }
                                ],
                            }
                        )

                messages.append(
                    {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": f"{history_responses[idx]}"},
                        ],
                    }
                )

            curr_img_url = f"data:image/png;base64,{processed_image}"
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": curr_img_url},
                        }
                    ],
                }
            )
        else:
            curr_img_url = f"data:image/png;base64,{processed_image}"
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": curr_img_url},
                        },
                        {"type": "text", "text": instruction_prompt},
                    ],
                }
            )

        # Debug: save messages before sending to model
        try:
            draft_dir = "./draft/message_cache"
            os.makedirs(draft_dir, exist_ok=True)
            message_file_path = os.path.join(
                draft_dir, f"messages_step_{current_step}.json"
            )
            with open(message_file_path, "w") as f:
                json.dump(messages, f)
        except Exception as _e:  # do not fail prediction due to debug IO
            pass

        response = self.call_llm(
            {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "temperature": self.temperature,
            },
            self.model,
        )

        logger.info(f"R3AgentV3 Output: {response}")

        self.responses.append(response)

        low_level_instruction, pyautogui_code = parse_response(
            response,
            width,
            height,
            self.coordinate_type,
        )

        logger.info(f"Low level instruction: {low_level_instruction}")
        logger.info(f"Pyautogui code: {pyautogui_code}")

        self.actions.append(low_level_instruction)

        return response, pyautogui_code

    @staticmethod
    def _to_dashscope_messages(messages):
        """
        Convert messages built for OpenAI compat into DashScope MultiModalConversation format.
        - "text" part  -> {"text": "..."}
        - "image_url"  -> {"image": "<url-or-data-uri>"}
        - "video_url"  -> {"video": "<url-or-data-uri>"}
        """
        ds_msgs = []
        for m in messages:
            role = m.get("role", "")
            parts = m.get("content", [])
            ds_content = []
            for p in parts:
                ptype = p.get("type")
                if ptype == "text":
                    ds_content.append({"text": p.get("text", "")})
                elif ptype == "image_url":
                    url = (p.get("image_url") or {}).get("url", "")
                    # DashScope accepts http(s), file://, or data:image/*; keep as-is
                    ds_content.append({"image": url})
                elif ptype == "video_url":
                    url = (p.get("video_url") or {}).get("url", "")
                    ds_content.append({"video": url})
                else:
                    # If you ever pass raw assistant strings (no parts), tolerate it
                    if isinstance(p, str):
                        ds_content.append({"text": p})
            # Also tolerate plain-string content (rare)
            if not ds_content and isinstance(m.get("content"), str):
                ds_content = [{"text": m["content"]}]
            ds_msgs.append({"role": role, "content": ds_content})
        return ds_msgs

    @staticmethod
    def _extract_text_from_dashscope_response(resp):
        """Join all 'text' parts from the first choice, including reasoning if present."""
        if hasattr(resp, "output"):
            out = resp.output
        else:
            out = resp.get("output") if isinstance(resp, dict) else None
        if not out:
            return None
        choices = getattr(out, "choices", None) if not isinstance(out, dict) else out.get("choices")
        if not choices:
            return None
        msg = getattr(choices[0], "message", None) if not isinstance(choices[0], dict) else choices[0].get("message")
        if not msg:
            return None
        content = getattr(msg, "content", None) if not isinstance(msg, dict) else msg.get("content", [])
        if not content:
            return None

        # Extract reasoning content if present (for thinking models)
        reasoning_content = getattr(msg, "reasoning_content", None) if not isinstance(msg, dict) else msg.get("reasoning_content", None)

        content_text = "".join(part.get("text", "") for part in content if isinstance(part, dict) and "text" in part)

        # Format with thinking tags if reasoning exists
        if reasoning_content is not None:
            return f"<think>\n{reasoning_content}\n</think>\n\n{content_text}"
        else:
            return content_text

    @backoff.on_exception(
        backoff.constant,
        (
            SSLError,
            openai.RateLimitError,
            openai.BadRequestError,
            openai.InternalServerError,
            InvalidArgument,
            ResourceExhausted,
            InternalServerError,
            BadRequest,
        ),
        interval=30,
        max_tries=5,
    )
    def call_llm(self, payload, model):
        messages = payload["messages"]

        if self.api_backend == "openai":
            return self._call_llm_openai(messages, model)
        elif self.api_backend == "dashscope":
            return self._call_llm_dashscope(messages, model)
        else:
            raise ValueError(f"Unknown API backend: {self.api_backend}")

    def _call_llm_openai(self, messages, model):
        """Call LLM using OpenAI SDK (compatible with OpenAI-compatible endpoints)."""
        base_url = os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        api_key = os.environ.get("OPENAI_API_KEY", "sk-123")
        cookies = os.environ.get("OPENAI_COOKIES", "")
        if cookies:
            http_client = httpx.Client(
                headers={"Cookie": cookies},
                timeout=3600,
            )
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=http_client,
            )
        else:
            client = openai.OpenAI(base_url=base_url, api_key=api_key)

        for attempt in range(1, MAX_RETRY_TIMES + 1):
            logger.info(f"[OpenAI] Generating content with model: {model} (attempt {attempt}/{MAX_RETRY_TIMES})")
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"[OpenAI] Error calling model: {e}")
                if attempt < MAX_RETRY_TIMES:
                    time.sleep(5)
                    continue
                break
        return ""

    def _call_llm_dashscope(self, messages, model):
        """Call LLM using DashScope SDK."""
        dashscope.base_http_api_url = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY", "sk-123")

        # Convert message schema
        ds_messages = self._to_dashscope_messages(messages)

        # Retry loop
        last_err = None
        for attempt in range(1, MAX_RETRY_TIMES + 1):
            thinking_status = f" (thinking={self.enable_thinking})" if self.enable_thinking else ""
            logger.info(f"[DashScope] Generating content with model: {model}, thinking_status: {thinking_status} (attempt {attempt}/{MAX_RETRY_TIMES})")
            try:
                # Build API call parameters
                call_params = {
                    "model": model,
                    "messages": ds_messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "vl_high_resolution_images": True,
                }

                # Add thinking parameters if enabled
                if self.enable_thinking:
                    call_params["enable_thinking"] = True
                    call_params["thinking_budget"] = self.thinking_budget

                resp = MultiModalConversation.call(**call_params)

                if getattr(resp, "status_code", None) not in (None, HTTPStatus.OK):
                    code = getattr(resp, "code", "")
                    msg = getattr(resp, "message", "")
                    reqid = getattr(resp, "request_id", "")
                    logger.warning(f"[DashScope] non-OK response (id={reqid}): {code} {msg}")
                    last_err = RuntimeError(f"DashScope status {resp.status_code}: {code} {msg}")
                    time.sleep(1.5 * attempt)
                    continue

                text = self._extract_text_from_dashscope_response(resp)
                if not text:
                    raise ValueError("DashScope response has no text content")
                return text

            except Exception as e:
                last_err = e
                logger.error(f"[DashScope] call failed: {e}")
                if attempt < MAX_RETRY_TIMES:
                    time.sleep(1.5 * attempt)
                    continue
                break

        if last_err:
            raise last_err
        return ""

    def set_interactive_prompt(self, enable: bool = True) -> None:
        """Enable or disable interactive mode (adds call_user tool and prompt suffix)."""
        self.is_interactive = enable

    def receive_user_message(self, message: str) -> None:
        """Queue a user message to be injected at the next predict() call."""
        if not message:
            return
        self.pending_user_messages.append(message)

    def clear_terminal_state(self) -> None:
        """Called when agent reports DONE/FAIL but more phases remain.
        Preserves conversation history so agent retains full context of prior work.
        Only clears pending_user_messages to avoid re-injecting stale data."""
        self.pending_user_messages = []

    def clear_done_from_history(self) -> None:
        """Full reset - clears all conversation history (fallback)."""
        self.thoughts = []
        self.actions = []
        self.observations = []
        self.responses = []
        self.screenshots = []
        self.pending_user_messages = []

    def reset(self, _logger=None, *args, **kwargs):
        global logger
        logger = (
            _logger if _logger is not None
            else logging.getLogger("desktopenv.r3agent_v3")
        )

        self.thoughts = []
        self.action_descriptions = (
            [] if hasattr(self, "action_descriptions") else []
        )
        self.actions = []
        self.observations = []
        self.responses = []
        self.screenshots = []
        self.is_interactive = False
        self.pending_user_messages = []
