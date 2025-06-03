import os
import sys
import json
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

import pollinations_client as client


def test_functions_spec_matches_action_map():
    names_spec = {f["function"]["name"] for f in client.FUNCTIONS_SPEC}
    names_map = set(client.ACTION_MAP)
    assert names_spec == names_map


def test_execute_tool_calls_dry_run(capsys):
    calls = [
        {
            "function": {
                "name": "run_shell",
                "arguments": json.dumps({"command": "echo hello"}),
            }
        },
        {
            "function": {
                "name": "open_app",
                "arguments": json.dumps({"name": "calculator"}),
            }
        }
    ]
    client.execute_tool_calls(calls, dry_run=True)
    captured = capsys.readouterr()
    assert "[DRY-RUN] run_shell" in captured.out
    assert "[DRY-RUN] open_app" in captured.out


def test_open_app_failure(monkeypatch):
    def fake_startfile(_):
        raise FileNotFoundError("missing")

    monkeypatch.setattr("os.startfile", fake_startfile, raising=False)
    with pytest.raises(RuntimeError):
        import controller
        controller.open_app("missing_app")



def test_capture_screen_error(monkeypatch):
    import controller

    def bad_screenshot():
        raise OSError("scrot missing")

    monkeypatch.setattr(controller, "pyautogui", type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}))

    with pytest.raises(controller.GUIUnavailable):
        controller.capture_screen()


def test_query_pollinations_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=60):
        captured["url"] = url
        captured["json"] = json

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"choices": []}

        return Response()

    monkeypatch.setattr(client.requests, "post", fake_post)
    messages: List[Dict[str, str]] = [{"role": "user", "content": "hello"}]
    client.query_pollinations(messages)

    assert captured["json"]["model"] == "openai"
    assert captured["json"]["messages"] == messages
    assert captured["json"]["tools"] == client.FUNCTIONS_SPEC
