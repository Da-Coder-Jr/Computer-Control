"""Run a goal through Pollinations AI to control the computer."""

from __future__ import annotations

import argparse
import time
from typing import List, Dict, Any, Optional
import base64
import io
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox

import controller
import pollinations_client as client


class PopupUI:
    """Simple Tkinter-based progress popup."""

    def __init__(self, max_steps: int) -> None:
        self.max_steps = max_steps
        try:
            self.root = tk.Tk()
            self.root.title("Computer Control")
            self.progress = ttk.Progressbar(
                self.root, maximum=max_steps, length=300
            )
            self.progress.pack(padx=10, pady=10)
            self.label = ttk.Label(self.root, text="Starting...")
            self.label.pack(padx=10, pady=10)
            self.update = self._update_gui
            self.done = self._done_gui
            self.root.update()
        except Exception:
            self.root = None
            self.update = self._update_console
            self.done = self._done_console
            print("GUI unavailable; falling back to console output")

    def _update_gui(self, step: int, text: str) -> None:
        self.progress["value"] = step
        self.label.config(text=text)
        self.root.update()

    def _done_gui(self) -> None:
        self.label.config(text="Done")
        self.root.update()
        try:
            messagebox.showinfo("Done", "Goal complete")
        finally:
            self.root.destroy()

    def _update_console(self, step: int, text: str) -> None:
        print(f"Step {step}/{self.max_steps}: {text}")

    def _done_console(self) -> None:
        print("Goal complete")


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
    ui = PopupUI(max_steps if steps is None else steps)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": client.SYSTEM_PROMPT}
    ]
    try:
        screenshot = controller.capture_screen()
    except controller.GUIUnavailable as exc:
        if dry_run:
            print(f"Warning: {exc}; using blank screenshot")
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

    start_time = time.perf_counter()

    for i in range(loop_limit):
        data = client.query_pollinations(messages)
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls")
        if tool_calls:
            client.execute_tool_calls(
                tool_calls, dry_run=dry_run, secure=secure
            )
            ui.update(i + 1, f"{tool_calls[0].get('function',{}).get('name')}")
        if content := message.get("content"):
            print(content)
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
                print(f"Warning: {exc}; using blank screenshot")
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
        ui.update(i + 1, f"step {i + 1}")
        if data.get("done") or message.get("done"):
            break
    ui.done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Control the computer with Pollinations AI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        "--dry-run",
        action="store_true",
        help="Print actions instead of executing",
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
