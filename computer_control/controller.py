"""Platform-independent actions executed on behalf of the AI."""

from __future__ import annotations

import base64
import io
import os
import subprocess
import sys
import shutil
import tempfile
import webbrowser
from typing import Any, List, Dict, Sequence
from PIL import Image, ImageGrab


try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    pyautogui = None  # type: ignore


class GUIUnavailable(RuntimeError):
    """Raised when GUI actions are requested but unavailable."""


def _get_pyautogui() -> Any:
    """Return the ``pyautogui`` module or raise ``GUIUnavailable``."""
    if pyautogui is None:
        raise GUIUnavailable("pyautogui is not available or no GUI environment")
    return pyautogui


def ensure_gui_available() -> None:
    """Raise ``GUIUnavailable`` if GUI operations are not possible."""
    _get_pyautogui()


def run_shell(command: str) -> None:
    """Run a shell command on any platform."""
    subprocess.run(command, shell=True, check=True)


def move_mouse(x: int, y: int) -> None:
    pg = _get_pyautogui()
    pg.moveTo(x, y)


def click(x: int, y: int, button: str = "left") -> None:
    pg = _get_pyautogui()
    pg.click(x=x, y=y, button=button)


def double_click(x: int, y: int, button: str = "left") -> None:
    """Double-click the mouse at x,y."""
    pg = _get_pyautogui()
    pg.doubleClick(x=x, y=y, button=button)


def write_text(text: str) -> None:
    pg = _get_pyautogui()
    pg.write(text)


def press_key(key: str) -> None:
    pg = _get_pyautogui()
    pg.press(key)


def scroll(amount: int) -> None:
    """Scroll the mouse wheel by the given amount."""
    pg = _get_pyautogui()
    pg.scroll(amount)


def drag_mouse(
    from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.0
) -> None:
    """Drag the mouse from one coordinate to another."""
    pg = _get_pyautogui()
    pg.moveTo(from_x, from_y)
    pg.dragTo(to_x, to_y, duration=duration, button="left")


def draw_path(points: List[Dict[str, int]], duration: float = 0.0) -> None:
    """Draw by dragging the mouse through a list of x,y coordinates."""
    pg = _get_pyautogui()
    if not points:
        return
    start = points[0]
    pg.moveTo(start["x"], start["y"])
    pg.mouseDown()
    for pt in points[1:]:
        pg.dragTo(pt["x"], pt["y"], duration=duration, button="left")
    pg.mouseUp()


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


def move_file(src: str, dst: str) -> None:
    """Move a file from ``src`` to ``dst``."""
    shutil.move(src, dst)


def open_url(url: str) -> None:
    """Open ``url`` in the default web browser."""
    webbrowser.open(url)


def delete_file(path: str) -> None:
    """Delete a file if it exists."""
    try:
        os.remove(path)
    except FileNotFoundError:
        raise RuntimeError(f"File not found: {path}") from None


def key_down(key: str) -> None:
    """Hold down a key until released."""
    pg = _get_pyautogui()
    pg.keyDown(key)


def key_up(key: str) -> None:
    """Release a previously held key."""
    pg = _get_pyautogui()
    pg.keyUp(key)


def hotkey(keys: Sequence[str]) -> None:
    """Press a combination of keys."""
    pg = _get_pyautogui()
    pg.hotkey(*keys)


def _fallback_screenshot() -> Image.Image | None:
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


def _blank_data_url() -> str:
    """Return a 1x1 white PNG data URL."""
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def capture_screen() -> str:
    pg = _get_pyautogui()

    try:
        image = pg.screenshot()

    except Exception:
        image = _fallback_screenshot()
        if image is None:
            return _blank_data_url()

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


def save_image(data_url: str, path: str) -> None:
    """Save a base64 ``data_url`` to ``path``."""
    if not data_url.startswith("data:image"):
        raise ValueError("invalid data url")
    _, b64 = data_url.split(",", 1)
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
