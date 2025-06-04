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

2. Run a simple goal with three interaction steps:

   ```bash
   python computer_control.py "open calculator" --steps 3
   ```

3. Use `--dry-run` to print planned actions without executing them.

- Linux users may also need the `scrot` package for screenshots


## Usage

Set the `POLLINATIONS_API` environment variable to override the default endpoint
(`https://text.pollinations.ai/openai`). Optionally specify
`POLLINATIONS_REFERRER` to identify your app.


Run the script from the repository root with a goal and the number of
interaction loops:

Run a goal with up to a number of interaction loops:


```bash
python computer_control.py "open calculator" --steps 3
```


`computer_control.py` lives in the project root, so reference it directly
or with the full path if running from another directory.

=======

The AI may request functions like `open_app` to launch applications. These tool
calls are executed automatically unless `--dry-run` is used.

Add `--dry-run` to print actions instead of executing them. Pollinations will
respond with JSON tool calls which are executed sequentially. Each iteration

captures a fresh screenshot so the AI can correct itself. If a GUI isn't
available (for example, on a headless server), the script falls back to a blank
image in dry‑run mode.

## Testing

Run the automated test suite after installing the requirements:

```bash
pytest -q
```


captures a fresh screenshot so the AI can correct itself.


**Warning:** Allowing a remote AI to issue commands on your machine can be
hazardous. Review output carefully or use the `--dry-run` option when testing.
This example is provided on a best-effort basis and may require tweaking for
your specific setup.


This project is released under the terms of the MIT License; see
the `LICENSE` file for details.
=======

