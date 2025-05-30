import platform, subprocess, tempfile, os, textwrap
from ..core.logger import info, err

def _find_ahk() -> str | None:
    for p in (
        os.getenv("AHK_EXE"),
        r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey32.exe",
    ):
        if p and os.path.exists(p):
            return p
    return None

def run(code: str) -> None:
    if platform.system() != "Windows":
        return                                               # skip on non-Windows
    ahk = _find_ahk()
    if not ahk:
        err("AutoHotkey.exe not found; set AHK_EXE or install AHK.")
        return

    script = textwrap.dedent(code).strip()
    with tempfile.NamedTemporaryFile("w", suffix=".ahk", delete=False) as f:
        f.write(script)
        tmp = f.name
    try:
        subprocess.run([ahk, tmp], check=True)
        info("[AHK] script executed")
    except subprocess.CalledProcessError as e:
        err(f"[AHK] error → {e}")
    finally:
        os.remove(tmp)
