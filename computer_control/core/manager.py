import json
from ..drivers import gui,shell,vision,voice
from .agent import chat
from .logger import info,warn
from ..config import LOOP_CAP

SYSTEM_PROMPT = """
You are an autonomous computer-control agent.
Return ONE JSON object only:
{ "thought":"…",
  "operation":"press|hotkey|write|click|move|drag|scroll|launch|shell|screenshot|done",
  …fields… }
• move:   x,y
• drag:   x1,y1,x2,y2
• scroll: amount  (positive=up)
• launch: app   OR url
"""

async def run(goal, verbose=False, plugins=None):
    msgs=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":goal}]
    loops=0
    while loops<LOOP_CAP:
        loops+=1
        raw=await chat(msgs)
        if verbose: print(raw)
        try: op=json.loads(raw)
        except: warn("bad json"); return
        act=op.get("operation","").lower()

        if act in ("press","hotkey"): gui.press(op["keys"])
        elif act=="click":            gui.click(op.get("x"),op.get("y"))
        elif act=="move":             gui.move(op["x"],op["y"])
        elif act=="drag":             gui.drag(op["x1"],op["y1"],op["x2"],op["y2"])
        elif act=="scroll":           gui.scroll(op.get("amount",-600))
        elif act=="write":            gui.write(op["content"])
        elif act=="launch":           shell.run(op["app"])
        elif act=="shell":            shell.run(op["command"])
        elif act=="screenshot":       msgs.extend(vision.attach(raw)); continue
        elif act=="done":             info(op.get("summary","Done")); return
        else: warn(f"unknown op {act}"); return

        msgs.append({"role":"assistant","content":raw})
        msgs.append({"role":"user","content":f"{act} executed"})
