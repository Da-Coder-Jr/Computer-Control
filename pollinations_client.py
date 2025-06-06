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
    }

    headers = {"Referer": POLLINATIONS_REFERRER}

    delay = 1
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                POLLINATIONS_API, json=payload, headers=headers, timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:  # network issues or HTTP errors
            if attempt == retries:
                raise RuntimeError("Failed to contact Pollinations API") from exc
            time.sleep(delay)
            delay *= 2

    # should never reach here
    raise RuntimeError("Failed to contact Pollinations API")


from rich.console import Console
from rich.panel import Panel


def execute_tool_calls(
    tool_calls: List[Dict[str, Any]],
    dry_run: bool = False,
    console: Optional[Console] = None,
) -> None:
    """Run the tool calls returned by the model."""
    console = console or Console()

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

            console.print(f"[red]Invalid arguments for {name}: {args}[/red]")
            continue
        if dry_run:
            console.print(f"[yellow][DRY-RUN][/yellow] {name}({params})")
            continue
        try:
            func(**params)
        except Exception as exc:  # pylint: disable=broad-except

            console.print(Panel(str(exc), title=f"Error executing {name}", style="red"))