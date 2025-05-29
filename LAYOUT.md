computer-control/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ setup.cfg
│
├─ computer_control/                 ← importable package
│  ├─ __init__.py
│  ├─ config.py
│  ├─ cli.py                         ← python -m computer_control ...
│  │
│  ├─ core/
│  │   ├─ agent.py                   ← LLM loop + reasoning
│  │   ├─ manager.py                 ← drives operations
│  │   └─ logger.py
│  │
│  ├─ drivers/
│  │   ├─ shell.py                   ← PowerShell / Bash
│  │   ├─ gui.py                     ← pyautogui actions
│  │   ├─ vision.py                  ← screenshots → base64
│  │   └─ voice.py                   ← Whisper-mic (optional)
│  │
│  ├─ plugins/
│  │   ├─ __init__.py
│  │   └─ sample_plugin.py           ← how to extend ops
│  │
│  └─ utils/
│      ├─ ansi.py
│      └─ paths.py
│
└─ tests/
   └─ test_smoke.py
