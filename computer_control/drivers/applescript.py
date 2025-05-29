"""
AppleScript driver  •  macOS only
Usage example in JSON from the LLM:
{
  "operation": "applescript",
  "code": "tell application \\"System Events\\" to keystroke \\"n\\" using {command down}"
}
"""

import platform, subprocess, tempfile, textwrap, os
from ..core.logger import info, err

def run(code: str) -> None:
    if platform.system() != "Darwin":
        err("applescript.run called on non-macOS system — ignored.")
        return

    script = textwrap.dedent(code).strip()
    try:
        # shortest path: pass via stdin to osascript
        subprocess.run(["osascript", "-"], input=script.encode(), check=True)
        info("[AppleScript] executed")
    except subprocess.CalledProcessError as e:
        err(f"[AppleScript] Error → {e}")
