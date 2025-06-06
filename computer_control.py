"""Run a goal through Pollinations AI to control the computer."""

from __future__ import annotations

import argparse
import time
from typing import List, Dict, Any, Optional
import base64
import io
from PIL import Image
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich_argparse import RichHelpFormatter

import controller
import pollinations_client as client


def blank_image() -> str:
    """Return a tiny base64 PNG used when screenshots fail."""
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main(
    goal: str,
    steps: Optional[int] = None,
    max_steps: int = 15,
    dry_run: bool = False,
    secure: bool = False,
) -> None:
    """Send ``goal`` to Pollinations and execute returned actions."""
    console = Console()
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": client.SYSTEM_PROMPT}
    ]
    try:
        screenshot = controller.capture_screen()
    except controller.GUIUnavailable as exc:
        if dry_run:
            console.print(f"[yellow]Warning: {exc}; using blank screenshot[/yellow]")
            screenshot = blank_image()
        else:
            raise
    messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": goal},
                {"type": "image_url", "image_url": {"url": screenshot}},
            ],
        }
    )

    loop_limit = steps if steps is not None else max_steps

    with Progress(
        TextColumn("Step {task.completed}/{task.total}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("ai", total=loop_limit)
        start_time = time.perf_counter()

        for i in range(loop_limit):
            progress.update(task, advance=1)
            data = client.query_pollinations(messages)
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls")
            if tool_calls:
                client.execute_tool_calls(
                    tool_calls, dry_run=dry_run, secure=secure, console=console
                )
            if content := message.get("content"):
                console.print(content)
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content", ""),
                    **({"tool_calls": tool_calls} if tool_calls else {}),
                }
            )
            try:
                screenshot = controller.capture_screen()
            except controller.GUIUnavailable as exc:
                if dry_run:
                    console.print(
                        f"[yellow]Warning: {exc}; using blank screenshot[/yellow]"
                    )
                    screenshot = blank_image()
                else:
                    raise
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Updated screen"},
                        {"type": "image_url", "image_url": {"url": screenshot}},
                    ],
                }
            )
            status = Table(box=None)
            status.add_row("Loop", str(i + 1))
            status.add_row("Elapsed", f"{time.perf_counter() - start_time:.1f}s")
            status.add_row("Mode", "dry-run" if dry_run else "live")
            console.print(Panel(status, title="Status", style="magenta"))
            console.rule()
            if data.get("done") or message.get("done"):
                break


class Formatter(RichHelpFormatter):
    """Rich help formatter with defaults shown."""

    def __init__(
        self, *args: Any, **kwargs: Any
    ) -> None:  # pragma: no cover - simple wrapper
        super().__init__(*args, **kwargs)

    def _get_help_string(
        self, action: argparse.Action
    ) -> str:  # pragma: no cover - delegate
        return argparse.ArgumentDefaultsHelpFormatter._get_help_string(self, action)


if __name__ == "__main__":
    formatter = Formatter
    parser = argparse.ArgumentParser(
        description="Control the computer with Pollinations AI",
        formatter_class=formatter,
        epilog="Example: python computer_control.py 'Open docs.new and write a poem praising Codex.'",
    )
    parser.add_argument("goal", help="Goal to send to the AI")
    parser.add_argument(
        "--steps",
        default="auto",
        help="Number of loops or 'auto' to run until done",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=15,
        help="Maximum steps when --steps=auto",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions instead of executing"
    )
    parser.add_argument(
        "--secure",
        action="store_true",
        help="Ask for confirmation before executing each tool call",
    )
    args = parser.parse_args()
    steps = None if str(args.steps).lower() == "auto" else int(args.steps)
    main(
        args.goal,
        steps=steps,
        max_steps=args.max_steps,
        dry_run=args.dry_run,
        secure=args.secure,
    )
