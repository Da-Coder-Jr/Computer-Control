from __future__ import annotations
import base64, io, subprocess, platform, shutil
from pathlib import Path

try:
    import pyautogui   # GUI environment
except Exception:
    pyautogui = None

def _grab_pyautogui() -> bytes:
    img = pyautogui.screenshot()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _grab_scrot() -> bytes:
    tmp = Path("/tmp/cc-shot.png")
    subprocess.run(["scrot", str(tmp)], check=True)
    data = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    return data

def _capture() -> bytes:
    if pyautogui:
        try:
            return _grab_pyautogui()
        except Exception:   # permission / Wayland etc.
            pass
    if shutil.which("scrot"):
        return _grab_scrot()
    raise RuntimeError("No screenshot backend available")

def attach(assistant_json: str):
    data_b64 = base64.b64encode(_capture()).decode()
    return [
        {"role": "assistant", "content": assistant_json},
        {"role": "user", "content": [
            {"type": "text", "text": "Screenshot attached"},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{data_b64}"}}]}
    ]

# ------------------------------------------------------------------
# Back-compat for manager.snap()
def snap() -> str:
    """Return base-64 PNG (legacy)."""
    import base64
    return base64.b64encode(_capture()).decode()

