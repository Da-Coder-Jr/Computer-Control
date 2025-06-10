"""Platform-independent actions executed on behalf of the AI."""

from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import shutil
import tempfile
from typing import List, Dict, Sequence
from PIL import Image, ImageGrab, UnidentifiedImageError



try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    pyautogui = None  # type: ignore


class GUIUnavailable(RuntimeError):
    """Raised when GUI actions are requested but unavailable."""


def ensure_gui_available() -> None:
    if pyautogui is None:

        raise GUIUnavailable(
            "pyautogui is not available or no GUI environment"
        )  # noqa: E501


def run_shell(command: str) -> None:
    """Run a shell command on any platform."""
    subprocess.run(command, shell=True, check=True)


def move_mouse(x: int, y: int) -> None:
    ensure_gui_available()
    pyautogui.moveTo(x, y)


def click(x: int, y: int, button: str = "left") -> None:
    ensure_gui_available()
    pyautogui.click(x=x, y=y, button=button)


def double_click(x: int, y: int, button: str = "left") -> None:
    """Double-click the mouse at x,y."""
    ensure_gui_available()
    pyautogui.doubleClick(x=x, y=y, button=button)


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


def drag_mouse(
    from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.0
) -> None:
    """Drag the mouse from one coordinate to another."""
    ensure_gui_available()
    pyautogui.moveTo(from_x, from_y)
    pyautogui.dragTo(to_x, to_y, duration=duration, button="left")


def draw_path(points: List[Dict[str, int]], duration: float = 0.0) -> None:
    """Draw by dragging the mouse through a list of x,y coordinates."""
    ensure_gui_available()
    if not points:
        return
    start = points[0]
    pyautogui.moveTo(start["x"], start["y"])
    pyautogui.mouseDown()
    for pt in points[1:]:
        pyautogui.dragTo(pt["x"], pt["y"], duration=duration, button="left")
    pyautogui.mouseUp()


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
        raise RuntimeError(
            f"Failed to open application '{name}': {exc}"
        ) from exc  # noqa: E501


def create_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def copy_file(src: str, dst: str) -> None:
    """Copy a file from ``src`` to ``dst``."""
    shutil.copy(src, dst)


def delete_file(path: str) -> None:
    """Delete a file if it exists."""
    try:
        os.remove(path)
    except FileNotFoundError:
        raise RuntimeError(f"File not found: {path}") from None


def key_down(key: str) -> None:
    """Hold down a key until released."""
    ensure_gui_available()
    pyautogui.keyDown(key)


def key_up(key: str) -> None:
    """Release a previously held key."""
    ensure_gui_available()
    pyautogui.keyUp(key)


def hotkey(keys: Sequence[str]) -> None:
    """Press a combination of keys."""
    ensure_gui_available()
    pyautogui.hotkey(*keys)


def _fallback_screenshot() -> Image | None:
    """Attempt a screenshot using platform utilities."""
    if sys.platform == "darwin":

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        try:
            tmp.close()
            subprocess.run(["screencapture", "-x", tmp.name], check=True)
            with Image.open(tmp.name) as im:
                image = im.copy()
        except Exception:
            image = None
        finally:
            os.remove(tmp.name)
        if image is not None:
            return image

    try:
        return ImageGrab.grab()
    except Exception:
        return None


def capture_screen() -> str:
    ensure_gui_available()

    try:
        image = pyautogui.screenshot()

    except Exception as exc:
        image = _fallback_screenshot()
        if image is None:
            msg = "Failed to capture screen"
            if isinstance(exc, UnidentifiedImageError):
                msg += ": cannot identify image file"
            raise GUIUnavailable(msg) from exc


    try:
        max_dim = max(image.size)
        if max_dim > 800:
            ratio = 800 / max_dim
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size)
    except Exception:
        pass
    buf = io.BytesIO()
    # Compress to JPEG to keep requests small
    image.save(buf, format="JPEG", quality=70, optimize=True)

    data = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{data}"
