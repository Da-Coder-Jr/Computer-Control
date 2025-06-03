"""Run a goal through Pollinations AI to control the computer."""
from __future__ import annotations

import argparse
from typing import List, Dict, Any

import controller
import pollinations_client as client


def main(goal: str, steps: int = 5, dry_run: bool = False) -> None:
    """Send ``goal`` to Pollinations and execute returned actions."""
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": client.SYSTEM_PROMPT}
    ]
    screenshot = controller.capture_screen()
    messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": goal},
                {"type": "image_url", "image_url": {"url": screenshot}},
            ],
        }
    )

    for _ in range(steps):
        data = client.query_pollinations(messages)
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls")
        if tool_calls:
            client.execute_tool_calls(tool_calls, dry_run=dry_run)
        if content := message.get("content"):
            print(content)
        messages.append(
            {
                "role": "assistant",
                "content": message.get("content", ""),
                **({"tool_calls": tool_calls} if tool_calls else {}),
            }
        )
        screenshot = controller.capture_screen()
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Updated screen"},
                    {"type": "image_url", "image_url": {"url": screenshot}},
                ],
            }
        )
        if not tool_calls:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control the computer with Pollinations AI")
    parser.add_argument("goal", help="Goal to send to the AI")
    parser.add_argument("--steps", type=int, default=5, help="Maximum interaction loops")
    parser.add_argument("--dry-run", action="store_true", help="Print actions instead of executing")
    args = parser.parse_args()
    main(args.goal, steps=args.steps, dry_run=args.dry_run)
