from __future__ import annotations
import os, platform, shlex, subprocess, sys

OS   = platform.system()
WSL  = "microsoft" in platform.release().lower() and OS == "Linux"

def _run(cmd: str) -> None:
    """best-effort execute and detach"""
    try:
        subprocess.Popen(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        subprocess.Popen(" ".join(cmd), shell=True)

def _translate_windows(tokens: list[str]) -> list[str]:
    # tokens[0] == "start"
    return ["powershell", "-NoLogo", "-Command"] + [" ".join(tokens)]

def _translate_macos(tokens: list[str]) -> list[str]:
    # Example: ['start','chrome','https://site']  →  open -a "Google Chrome" https://site
    if tokens[0] == "start":
        if len(tokens) == 1:                 # plain 'start' → open Finder
            return ["open", "."]
        app = tokens[1]
        url = tokens[2:] if len(tokens) > 2 else []
        return ["open", "-a", app.capitalize()] + url
    return tokens

def _translate_linux(tokens: list[str]) -> list[str]:
    if tokens[0] == "start":
        url = tokens[-1] if tokens[-1].startswith(("http://", "https://")) else None
        if url:
            return ["xdg-open", url]
    return tokens

def run(command: str) -> None:
    tokens = shlex.split(command)
    if OS == "Windows":
        cmd = _translate_windows(tokens)
    elif WSL:
        # pass through to Windows default browser if no xdg-open
        cmd = ["explorer.exe", tokens[-1]] if tokens[0] == "start" else tokens
    elif OS == "Darwin":
        cmd = _translate_macos(tokens)
    else:  # Linux
        cmd = _translate_linux(tokens)

    _run(cmd)
