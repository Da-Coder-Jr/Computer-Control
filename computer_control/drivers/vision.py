import base64, pyautogui
from pathlib import Path
SS=Path("screenshot.png")
def snap()->str:
    pyautogui.screenshot(str(SS))
    return base64.b64encode(SS.read_bytes()).decode()
