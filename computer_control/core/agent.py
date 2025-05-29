import aiohttp, ssl, json, asyncio, shutil
from ..config import POLL_URL, POLL_MODEL
from .logger import warn, error

async def call_pollinations(msgs):
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{POLL_URL}/v1/chat/completions",
                          ssl=ssl.SSLContext(),
                          json={"model": POLL_MODEL,"messages":msgs}) as r:
            r.raise_for_status()
            data = await r.json()
            return data["choices"][0]["message"]["content"].strip()

async def call_local_ollama(msgs):
    if not shutil.which("ollama"): raise RuntimeError("ollama not installed")
    import subprocess, json, textwrap, tempfile, os, pathlib, sys, shlex
    prompt="\n".join(m["content"] if isinstance(m["content"],str) else str(m["content"]) for m in msgs)
    cmd=f"ollama run llama3 '{prompt}'"
    out=subprocess.check_output(cmd,shell=True,text=True)
    return out.strip()

async def chat(msgs):
    try:
        return await call_pollinations(msgs)
    except Exception as e:
        warn(f"Pollinations failed ({e}); trying local ollama.")
        return await call_local_ollama(msgs)
