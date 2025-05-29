import json, asyncio
from ..config import LOOP_CAP
from ..drivers import shell, gui, vision
from .agent import chat
from .logger import info, warn, error, debug

SYSTEM_PROMPT = """
You are an autonomous computer-control agent.
Return ONE JSON dict each turn:
{ "thought":"...", "operation":"press|hotkey|write|click|shell|screenshot|done", ... }
"""

async def run(goal:str, voice=False, verbose=False, plugins=None):
    msgs=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":goal}]
    if plugins: [p.on_start(goal) for p in plugins]

    loops=0
    while loops<LOOP_CAP:
        loops+=1
        raw=await chat(msgs)
        if verbose: debug(raw)
        try: op=json.loads(raw)
        except json.JSONDecodeError:
            error("Bad JSON. abort."); return
        if plugins: [p.on_thought(op) for p in plugins]

        act=op.get("operation","").lower()
        if act in ("press","hotkey"): gui.press(op["keys"])
        elif act=="click":           gui.click(op.get("x"),op.get("y"))
        elif act=="write":           gui.write(op["content"])
        elif act=="shell":           shell.run(op["command"])
        elif act=="screenshot":
            b64 = vision.snap()
            msgs+=[
              {"role":"assistant","content":raw},
              {"role":"user","content":[
                 {"type":"text","text":"Screenshot attached"},
                 {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}}]}]
            continue
        elif act=="done":
            info(op.get("summary","Done")); return
        else:
            warn(f"Unknown op {act}"); return

        msgs.append({"role":"assistant","content":raw})
        msgs.append({"role":"user","content":f"{act} executed"})
