import os
LOOP_CAP = int(os.getenv("LOOP_CAP", 12))
POLL_URL   = os.getenv("POLL_URL", "https://text.pollinations.ai/openai")
POLL_MODEL = os.getenv("POLL_MODEL", "gpt-4o-mini")
