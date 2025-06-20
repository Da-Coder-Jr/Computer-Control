"""Client utilities for interacting with the Pollinations API."""

from __future__ import annotations


import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

import requests

from . import controller


POLLINATIONS_API = os.environ.get(
    "POLLINATIONS_API", "https://text.pollinations.ai/openai"
)

POLLINATIONS_REFERRER = os.environ.get(
    "POLLINATIONS_REFERRER", "https://example.com"
)  # noqa: E501


SYSTEM_PROMPT = (
    "You control the user's computer via function calls. "
    "Respond with tool_calls describing actions to reach the objective."
)

FUNCTIONS_SPEC: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_mouse",
            "description": "Move the mouse to x,y screen coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click the mouse at x,y",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "default": "left",
                    },
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "double_click",
            "description": "Double-click the mouse at x,y",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "default": "left",
                    },
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_text",
            "description": "Type text at the keyboard",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the mouse wheel",
            "parameters": {
                "type": "object",
                "properties": {"amount": {"type": "integer"}},
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "drag_mouse",
            "description": "Drag the mouse from one point to another",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_x": {"type": "integer"},
                    "from_y": {"type": "integer"},
                    "to_x": {"type": "integer"},
                    "to_y": {"type": "integer"},
                    "duration": {"type": "number", "default": 0.0},
                },
                "required": ["from_x", "from_y", "to_x", "to_y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_path",
            "description": "Drag the mouse along a list of coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "points": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"},
                            },
                            "required": ["x", "y"],
                        },
                        "minItems": 2,
                    },
                    "duration": {"type": "number", "default": 0.0},
                },
                "required": ["points"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application by name",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default browser",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a file with the given content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "key_down",
            "description": "Hold down a keyboard key",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "key_up",
            "description": "Release a keyboard key",
            "parameters": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press a combination of keys",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                },
                "required": ["keys"],
            },
        },
    },
]

ACTION_MAP: Dict[str, Callable[..., None]] = {
    "run_shell": controller.run_shell,
    "move_mouse": controller.move_mouse,
    "click": controller.click,
    "double_click": controller.double_click,
    "write_text": controller.write_text,
    "press_key": controller.press_key,
    "scroll": controller.scroll,
    "drag_mouse": controller.drag_mouse,
    "draw_path": controller.draw_path,
    "open_app": controller.open_app,
    "open_url": controller.open_url,
    "create_file": controller.create_file,
    "delete_file": controller.delete_file,
    "key_down": controller.key_down,
    "key_up": controller.key_up,
    "hotkey": controller.hotkey,
}


def query_pollinations(
    messages: List[Dict[str, Any]], retries: int = 3
) -> Dict[str, Any]:
    """Send ``messages`` to Pollinations and return the JSON response."""

    payload = {
        "model": "openai",
        "messages": messages,
        "tools": FUNCTIONS_SPEC,
        "tool_choice": "auto",
        "temperature": 0.2,
    }

    headers = {"Referer": POLLINATIONS_REFERRER}

    delay = 1
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                POLLINATIONS_API, json=payload, headers=headers, timeout=30
            )
        except requests.RequestException as exc:  # network issues  # noqa: E501
            if attempt == retries:
                raise RuntimeError(
                    "Failed to contact Pollinations API"
                ) from exc  # noqa: E501
            time.sleep(delay)
            delay *= 2
            continue

        if not response.ok:  # HTTP error
            if response.status_code == 413:
                raise RuntimeError(
                    "Pollinations API returned 413: request entity too large"
                )
            if attempt == retries:
                try:
                    err = response.json()
                except Exception:  # pragma: no cover - non-JSON error
                    err = {}
                details = err.get("details", {}).get("error", {})
                if details.get("code") == "content_filter":  # noqa: E501
                    raise RuntimeError(
                        "Pollinations blocked the prompt due to content filtering."  # noqa: E501
                    ) from None
                raise RuntimeError(
                    f"Pollinations API returned {response.status_code}: {response.text}"  # noqa: E501
                )
            time.sleep(delay)
            delay *= 2
            continue

        return response.json()

    # should never reach here
    raise RuntimeError("Failed to contact Pollinations API")


def execute_tool_calls(
    tool_calls: List[Dict[str, Any]],
    dry_run: bool = False,
    secure: bool = False,
    delay: float = 0.0,
    console: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Run the tool calls returned by the model and return tool messages."""

    results: List[Dict[str, Any]] = []

    for call in tool_calls:
        call_id = call.get("id", "")
        name = call.get("function", {}).get("name")
        args = call.get("function", {}).get("arguments", "{}")

        if not name:
            print(f"Unknown tool call without name: {call}")
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": "error: missing name",
                }
            )
            continue

        func = ACTION_MAP.get(name)
        if not func:
            print(f"Unknown tool {name}")
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": "error: unknown tool",
                }
            )
            continue

        try:
            params = json.loads(args) if args else {}
        except json.JSONDecodeError:
            print(f"Invalid arguments for {name}: {args}")
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": "error: bad args",
                }
            )
            continue

        print(f"{name}({params})")
        if secure:
            resp = input(f"Execute {name}? [y/N] ")
            if resp.lower() not in ("y", "yes"):
                print(f"Skipped {name}")
                results.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": "skipped",
                    }
                )
                if delay > 0:
                    time.sleep(delay)
                continue

        if dry_run:
            print(f"[DRY-RUN] {name}({params})")
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": "dry-run",
                }
            )
            if delay > 0:
                time.sleep(delay)
            continue

        try:
            result = func(**params)
            print(f"Executed {name}")
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": "" if result is None else str(result),
                }
            )
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error executing {name}: {exc}")
            results.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": f"error: {exc}",
                }
            )
        if delay > 0:
            time.sleep(delay)

    return results
