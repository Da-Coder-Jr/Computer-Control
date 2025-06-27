"""Run a goal through Pollinations AI to control the computer."""

from __future__ import annotations
import argparse
import os
from typing import List, Dict, Any, Optional
import base64
import io
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox
from computer_control import controller
from computer_control import client


class PopupUI:
    """Simple Tkinter-based progress popup."""

    def __init__(self, total_steps: Optional[int]) -> None:
        self.total_steps = total_steps
        self.root: Optional[tk.Tk]
        try:
            self.root = tk.Tk()
            self.root.title("Computer Control")

            mode = (
                "determinate" if total_steps is not None else "indeterminate"
            )  # noqa: E501

            self.progress = ttk.Progressbar(
                self.root,
                maximum=(total_steps or 100),
                length=300,
                mode=mode,
            )
            self.progress.pack(padx=10, pady=10)
            self.label = ttk.Label(self.root, text="Starting...")
            self.label.pack(padx=10, pady=10)
            if mode == "indeterminate":
                self.progress.start(10)
            self.update = self._update_gui
            self.done = self._done_gui
            assert self.root is not None
            self.root.update()
        except Exception:
            self.root = None
            self.update = self._update_console
            self.done = self._done_console
            print("GUI unavailable; falling back to console output")

    def _update_gui(self, step: int, text: str) -> None:
        if self.total_steps is not None:
            self.progress["value"] = step
        self.label.config(text=text)
        assert self.root is not None
        self.root.update()

    def _done_gui(self) -> None:
        if self.total_steps is None:
            self.progress.stop()
        self.label.config(text="Done")
        assert self.root is not None
        self.root.update()
        try:
            messagebox.showinfo("Done", "Goal complete")
        finally:
            assert self.root is not None
            self.root.destroy()

    def _update_console(self, step: int, text: str) -> None:
        if self.total_steps is not None:
            print(f"Step {step}/{self.total_steps}: {text}")
        else:
            print(f"Step {step}: {text}")

    def _done_console(self) -> None:
        print("Goal complete")


def blank_image() -> str:
    """Return a tiny base64 PNG used when screenshots fail."""
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def trim_history(
    msgs: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    """Return at most ``limit`` recent messages starting from a user or system
    message.

    The helper ensures no assistant message with ``tool_calls`` is included
    without the corresponding tool responses which would otherwise trigger API
    errors.
    """

    if limit <= 0:
        return []

    start = max(0, len(msgs) - limit)
    while start < len(msgs) and msgs[start]["role"] not in ("system", "user"):
        start += 1
    trimmed = msgs[start:]

    def clean(seq: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        """Return ``seq`` with incomplete assistant/tool pairs removed."""

        # drop trailing assistant messages that contain tool_calls
        while seq and seq[-1].get("tool_calls"):
            seq.pop()

        # drop leading tool messages without a preceding assistant
        while seq and seq[0]["role"] == "tool":
            seq.pop(0)

        # remove any assistant message whose tool_calls lack responses
        while True:
            pending: List[str] = []
            first_incomplete: Optional[int] = None
            for i, msg in enumerate(seq):
                if msg.get("tool_calls"):
                    ids = [c.get("id", "") for c in msg["tool_calls"]]
                    pending.extend(ids)
                    if first_incomplete is None:
                        first_incomplete = i
                else:
                    call_id = msg.get("tool_call_id")
                    if call_id and call_id in pending:
                        pending.remove(call_id)
                        if not pending:
                            first_incomplete = None

            if not pending:
                break

            assert first_incomplete is not None
            seq = seq[first_incomplete + 1 :]  # noqa: E203
            while seq and seq[0]["role"] == "tool":
                seq.pop(0)

        # ensure sequence starts with system or user
        while seq and seq[0]["role"] not in ("system", "user"):
            seq.pop(0)


        return seq

    trimmed = clean(trimmed)

    if len(trimmed) > limit:
        trimmed = trimmed[-limit:]
        trimmed = clean(trimmed)


    return trimmed


def main(
    goal: str,
    steps: Optional[int] = None,
    max_steps: int = 0,
    dry_run: bool = False,
    secure: bool = True,
    history: int = 8,
    save_dir: Optional[str] = None,
    delay: float = 0.0,
) -> None:
    """Send ``goal`` to Pollinations and execute returned actions.


    ``history`` controls how many of the most recent messages are sent
    to the API each loop. Limiting the history prevents request payloads
    from growing too large and triggering HTTP 413 errors.

    """
    ui = PopupUI(steps)
    counter = 0
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    print("AI is taking control. Do not touch your computer.")
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": client.SYSTEM_PROMPT}
    ]

    try:
        screenshot = controller.capture_screen()
    except controller.GUIUnavailable as exc:
        print(f"Warning: {exc}; using blank screenshot")
        screenshot = blank_image()
    if save_dir:
        path = os.path.join(save_dir, f"{counter}.jpg")
        controller.save_image(screenshot, path)
        counter += 1

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
    unlimited = steps is None and loop_limit <= 0
    i = 0

    while True:

        try:
            data = client.query_pollinations(trim_history(messages, history))
        except RuntimeError as exc:
            if "413" in str(exc) and history > 1:
                history = max(1, history // 2)
                print(
                    "Warning: payload too large;",
                    f"retrying with history={history}",
                )
                continue
            print(f"Error: {exc}")
            break

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls")
        tool_messages: List[Dict[str, Any]] = []
        if tool_calls:
            tool_messages = client.execute_tool_calls(
                tool_calls, dry_run=dry_run, secure=secure, delay=delay
            )  # noqa: E501
            ui.update(
                i + 1, f"{tool_calls[0].get('function', {}).get('name')}"
            )  # noqa: E501
        if content := message.get("content"):
            print(content)
        messages.append(
            {
                "role": "assistant",
                "content": message.get("content", ""),
                **({"tool_calls": tool_calls} if tool_calls else {}),
            }
        )
        if tool_calls:
            messages.extend(tool_messages)
        try:
            screenshot = controller.capture_screen()
        except controller.GUIUnavailable as exc:
            print(f"Warning: {exc}; using blank screenshot")
            screenshot = blank_image()
        if save_dir:
            path = os.path.join(save_dir, f"{counter}.jpg")
            controller.save_image(screenshot, path)
            counter += 1
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
        i += 1
        if not unlimited and i >= loop_limit:
            break
    if save_dir:
        try:
            final_img = controller.capture_screen()
            path = os.path.join(save_dir, "final.jpg")
            controller.save_image(final_img, path)
        except controller.GUIUnavailable:
            pass
    ui.done()


def cli_entry() -> None:
    parser = argparse.ArgumentParser(
        description="Control the computer with Pollinations AI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Example: python computer_control.py "
            "'Open docs.new and write a poem praising Codex.'"
        ),
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
        default=0,
        help="Maximum steps when --steps=auto (0 for unlimited)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions instead of executing",
    )
    parser.add_argument(
        "--history",
        type=int,
        default=8,
        help="Number of recent messages to send to the API",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait after each action",
    )
    args = parser.parse_args()
    steps = None if str(args.steps).lower() == "auto" else int(args.steps)
    main(
        args.goal,
        steps=steps,
        max_steps=args.max_steps,
        dry_run=args.dry_run,
        secure=True,
        history=args.history,
        delay=args.delay,
    )


if __name__ == "__main__":
    cli_entry()
