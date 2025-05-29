from ..core.logger import info
def on_start(goal): info(f"[plugin] starting objective: {goal}")
def on_thought(op): info(f"[plugin] LLM decided: {op.get('operation')}")
