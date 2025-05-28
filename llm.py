import os, aiohttp, ssl
from dotenv import load_dotenv
load_dotenv()                                      # optional .env

URL   = os.getenv("POLL_URL", "https://text.pollinations.ai/openai")
MODEL = os.getenv("POLL_MODEL", "gpt-4o-mini")     # pick any from /models

async def chat(messages: list[str|dict]) -> str:
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"{URL}/v1/chat/completions",
            ssl=ssl.SSLContext(),
            json={"model": MODEL, "messages": messages},
            timeout=120
        ) as r:
            r.raise_for_status()
            data = await r.json()
            return data["choices"][0]["message"]["content"].strip()
