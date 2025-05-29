import platform, subprocess
from ..core.logger import info, error

def run(cmd:str)->str:
    exe = ["powershell","-NoLogo","-Command",cmd] if platform.system()=="Windows" else ["bash","-c",cmd]
    p = subprocess.run(exe,capture_output=True,text=True)
    out = p.stdout.strip() or p.stderr.strip()
    info(out)
    return out or "Done"
