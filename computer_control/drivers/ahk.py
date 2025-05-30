"""
AutoHotkey driver  •  Windows only
Usage example in JSON:
{
  "operation": "ahk",
  "code": "Send, ^s"
}
"""

import platform, subprocess, tempfile, os, shutil, textwrap
from ..core.logger import info, err

def _find_ahk_exe() -> str | None:
    # 1) environment override
    if (p := os.getenv("AHK_EXE")): return p
    # 2) common install locations
    candidates = [
        r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey32.exe",
    ]
    return next((p for p in candidates if os.path.exists(p)), None)

def run(code: str) -> None:
    if platform.system() != "Windows":
        err("ahk.run called on non-Windows system — ignored.")
        return

    ahk = _find_ahk_exe()
    if not ahk:
        err("AutoHotkey executable not found; install AHK or set AHK_EXE env.")
        return

    script = textwrap.dedent(code).strip()
    with tempfile.NamedTemporaryFile("w", suffix=".ahk", delete=False) as f:
        f.write(script)
        tmp_path = f.name

    try:
        subprocess.run([ahk, tmp_path], check=True)
        info("[AHK] script ran")
    except subprocess.CalledProcessError as e:
        err(f"[AHK] Error → {e}")
    finally:
        try: os.remove(tmp_path)
        except OSError: pass
