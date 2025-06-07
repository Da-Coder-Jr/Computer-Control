"""Platform-independent actions executed on behalf of the AI."""

from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import shutil


try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    pyautogui = None  # type: ignore


class GUIUnavailable(RuntimeError):
    """Raised when GUI actions are requested but unavailable."""


def ensure_gui_available() -> None:
    if pyautogui is None:
        raise GUIUnavailable("pyautogui is not available or no GUI environment")


def run_shell(command: str) -> None:
    """Run a shell command on any platform."""
    subprocess.run(command, shell=True, check=True)


def move_mouse(x: int, y: int) -> None:
    ensure_gui_available()
    pyautogui.moveTo(x, y)


def click(x: int, y: int, button: str = "left") -> None:
    ensure_gui_available()
    pyautogui.click(x=x, y=y, button=button)


def write_text(text: str) -> None:
    ensure_gui_available()
    pyautogui.write(text)


def press_key(key: str) -> None:
    ensure_gui_available()
    pyautogui.press(key)


def scroll(amount: int) -> None:
    """Scroll the mouse wheel by the given amount."""
    ensure_gui_available()
    pyautogui.scroll(amount)


def open_app(name: str) -> None:
    """Open an application by name on the current platform."""
    try:
        if os.name == "nt":
            os.startfile(name)
        elif sys.platform == "darwin":
            subprocess.run(["open", "-a", name], check=True)
        else:
            if not shutil.which(name):  # ensure the app exists
                raise FileNotFoundError(name)
            subprocess.Popen([name])
    except Exception as exc:  # pragma: no cover - platform dependent
        raise RuntimeError(f"Failed to open application '{name}': {exc}") from exc


def create_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def capture_screen() -> str:
    ensure_gui_available()
    try:
        image = pyautogui.screenshot()
    except Exception as exc:  # pragma: no cover - GUI may be unavailable
        raise GUIUnavailable(f"Failed to capture screen: {exc}") from exc
    try:
        max_dim = max(image.size)
        if max_dim > 800:
            ratio = 800 / max_dim
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size)
    except Exception:
        pass
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{data}"
