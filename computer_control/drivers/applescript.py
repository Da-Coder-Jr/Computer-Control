import platform, subprocess, textwrap
from ..core.logger import info, err

def run(code: str) -> None:
    if platform.system() != "Darwin":
        return                                               # silently skip on non-macOS
    script = textwrap.dedent(code).strip()
    try:
        subprocess.run(["osascript", "-"], input=script.encode(), check=True)
        info("[AppleScript] executed")
    except subprocess.CalledProcessError as e:
        err(f"[AppleScript] error → {e}")
