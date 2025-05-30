import json, asyncio
from ..config import LOOP_CAP
from ..drivers import gui, shell, vision, applescript, ahk      #  ← NEW
from ..core.agent import chat
from ..core.logger import info, warn

SYSTEM_PROMPT = """
You are an autonomous computer-control agent.
Return ONE JSON object per turn — no extra text.

Fields:
{ "thought": "why this step",
  "operation":
    "press" | "hotkey" | "write" |
    "click" | "move" | "drag" | "scroll" |
    "launch" | "shell" |
    "screenshot" |
    "applescript" | "ahk" |          #  NEW
    "done",
  … additional fields …

✦ press/hotkey      →  "keys": ["ctrl","s"]  or "keys": "enter"
✦ move              →  "x": 100, "y": 200
✦ drag              →  "x1": 100, "y1":200, "x2":300, "y2":400
✦ scroll            →  "amount": -800
✦ launch            →  "app": "chrome"  (or url)
✦ shell             →  "command": "ls -la"
✦ applescript (mac) →  "code": "<AppleScript>"
✦ ahk        (win)  →  "code": "<AutoHotkey>"
"""

async def run(goal: str, verbose=False, plugins=None):
    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": goal}
    ]
    loops = 0
    while loops < LOOP_CAP:
        loops += 1
        raw = await chat(msgs)
        if verbose:
            print("LLM>", raw)

        try:
            op = json.loads(raw)
        except json.JSONDecodeError:
            warn("⚠️  LLM returned non-JSON, stopping."); return

        act = op.get("operation", "").lower()

        # ─── dispatch table ────────────────────────────────────────────
        if   act in ("press", "hotkey"): gui.press(op["keys"])
        elif act == "click":            gui.click(op.get("x"), op.get("y"))
        elif act == "move":             gui.move(op["x"], op["y"])
        elif act == "drag":             gui.drag(op["x1"], op["y1"], op["x2"], op["y2"])
        elif act == "scroll":           gui.scroll(op.get("amount", -600))
        elif act == "write":            gui.write(op["content"])
        elif act == "launch":           shell.run(op["app"])
        elif act == "shell":            shell.run(op["command"])
        elif act == "applescript":      applescript.run(op["code"])      # NEW
        elif act == "ahk":              ahk.run(op["code"])              # NEW
        elif act == "screenshot":       msgs.extend(vision.attach(raw)); continue
        elif act == "done":             info(op.get("summary", "✅ Done")); return
        else:                           warn(f"⚠️  unknown op '{act}'");  return
        # ───────────────────────────────────────────────────────────────

        # feedback for next LLM turn
        msgs.append({"role": "assistant", "content": raw})
        msgs.append({"role": "user",      "content": f"{act} executed"})
