import aiohttp, ssl, shutil, subprocess, json, platform, textwrap
from ..config import POLL_URL,POLL_MODEL
from .logger import warn

async def _pollinations(msgs):
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{POLL_URL}/v1/chat/completions",
                          ssl=ssl.SSLContext(),
                          json={"model":POLL_MODEL,"messages":msgs}) as r:
            r.raise_for_status()
            return (await r.json())["choices"][0]["message"]["content"].strip()

async def _local_ollama(msgs):
    if not shutil.which("ollama"): raise RuntimeError("ollama not installed")
    prompt="\n".join(m["content"] if isinstance(m["content"],str) else str(m["content"]) for m in msgs)
    return subprocess.check_output(f"ollama run llama3 '{prompt}'",shell=True,text=True).strip()

async def chat(msgs):
    try: return await _pollinations(msgs)
    except Exception as e:
        warn(f"Pollinations failed ({e}), fallback to local model")
        return await _local_ollama(msgs)
