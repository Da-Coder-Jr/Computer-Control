# Computer-Control

This project demonstrates how to let the [Pollinations AI](https://pollinations.ai)
service operate your desktop. The script repeatedly sends screenshots of your
desktop to Pollinations. The model replies with tool calls to run shell
commands, move the mouse, type text and more. After each action a new screenshot
is captured and sent back so the model can iterate just like a human.

The interaction uses Pollinations' OpenAI-compatible endpoint. The returned tool
calls are executed locally via Python using `pyautogui` for GUI operations.
These actions include launching applications, moving the mouse and typing text
so the code works across Windows, macOS and Linux provided a GUI environment is
available.

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies
- Install them with `pip install -r requirements.txt`
- Linux systems require the `scrot` package for screenshot functionality. Install
  it with your package manager, for example:
  `sudo apt-get install scrot` or `sudo yum install scrot`.

## Quick Start

1. Install the requirements:

   ```bash
   pip install -r requirements.txt
   ```

2. Run a goal in automatic mode (the script keeps looping until the AI
   signals it is done or reaches 15 steps):

   ```bash
   python computer_control.py "open calculator"
   ```

   Add `--dry-run` to preview the tool calls without actually executing
   them. Use `--secure` to confirm each step before it executes.

3. Run the automated tests (optional):

   ```bash
   pytest -q
   ```

## Usage

Set the `POLLINATIONS_API` environment variable to override the default endpoint
(`https://text.pollinations.ai/openai`). Optionally specify
`POLLINATIONS_REFERRER` to identify your app.

Run the script **from the repository root** with a goal:

```bash
python computer_control.py "open calculator"
```

The program automatically loops until the AI reports it is done (up to a
maximum of 15 steps by default). Use `--max-steps` to override that limit or
`--steps N` to force an exact number of iterations.

`computer_control.py` lives in the project root, so run it there or provide the
full path if invoking from another directory.

The AI may request functions like `open_app` to launch applications. These tool
calls are executed automatically unless `--dry-run` is used. Use `--secure` to
confirm each action before it runs.

Add `--dry-run` to print actions instead of executing them. Pollinations will
respond with JSON tool calls which are executed sequentially. Each iteration
captures a fresh screenshot so the AI can correct itself. If a GUI isn't
available (for example, on a headless server), the script falls back to a blank
image in dry‑run mode.

Supported actions include launching apps, running shell commands, moving and
clicking the mouse, scrolling, drawing with the mouse, typing text, pressing keys,
and creating files.


During execution a small popup window displays a progress bar and the current
action. If a GUI is unavailable the script falls back to simple console output.

## Testing

Run the automated test suite after installing the requirements:

```bash
pytest -q
```


**Warning:** Allowing a remote AI to issue commands on your machine can be
hazardous. Review output carefully or use the `--dry-run` option when testing.
This example is provided on a best-effort basis and may require tweaking for
your specific setup.

This project is released under the terms of the MIT License; see
the `LICENSE` file for details.
