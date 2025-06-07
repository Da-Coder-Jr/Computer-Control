"""Client utilities for interacting with the Pollinations API."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

import requests

import controller

POLLINATIONS_API = os.environ.get(
    "POLLINATIONS_API", "https://text.pollinations.ai/openai"
)
POLLINATIONS_REFERRER = os.environ.get("POLLINATIONS_REFERRER", "https://example.com")

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
                "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
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
]

ACTION_MAP: Dict[str, Callable[..., None]] = {
    "run_shell": controller.run_shell,
    "move_mouse": controller.move_mouse,
    "click": controller.click,
    "write_text": controller.write_text,
    "press_key": controller.press_key,
    "scroll": controller.scroll,
    "open_app": controller.open_app,
    "create_file": controller.create_file,
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
        except requests.RequestException as exc:  # network issues
            if attempt == retries:
                raise RuntimeError("Failed to contact Pollinations API") from exc
            time.sleep(delay)
            delay *= 2
            continue

        if not response.ok:  # HTTP error
            if attempt == retries:
                raise RuntimeError(
                    f"Pollinations API returned {response.status_code}: {response.text}"
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
    console: Optional[Any] = None,
) -> None:
    """Run the tool calls returned by the model."""
    for call in tool_calls:
        name = call.get("function", {}).get("name")
        if not name:
            continue
        func = ACTION_MAP.get(name)
        if not func:
            continue
        args = call.get("function", {}).get("arguments", "{}")
        try:
            params = json.loads(args) if args else {}
        except json.JSONDecodeError:
            print(f"Invalid arguments for {name}: {args}")
            continue
        print(f"{name}({params})")
        if secure:
            resp = input(f"Execute {name}? [y/N] ")
            if resp.lower() not in ("y", "yes"):
                print(f"Skipped {name}")
                continue
        if dry_run:
            print(f"[DRY-RUN] {name}({params})")
            continue
        try:
            func(**params)
            print(f"Executed {name}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error executing {name}: {exc}")
