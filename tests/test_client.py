import os
import sys
import json
import shutil
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

import pollinations_client as client
import controller


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
        },
        {
            "function": {
                "name": "scroll",
                "arguments": json.dumps({"amount": 100}),
            }
        },
    ]
    client.execute_tool_calls(calls, dry_run=True, secure=False)
    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out


def test_execute_tool_calls_secure(monkeypatch, capsys):
    calls = [
        {
            "function": {
                "name": "run_shell",
                "arguments": json.dumps({"command": "echo hello"}),
            }
        }
    ]
    monkeypatch.setattr(
        client,
        "Confirm",
        type("Dummy", (), {"ask": staticmethod(lambda *_, **__: False)}),
    )
    client.execute_tool_calls(calls, dry_run=False, secure=True)
    captured = capsys.readouterr()
    assert "Skipped run_shell" in captured.out


def test_help_runs(tmp_path):
    """computer_control.py --help should exit cleanly."""
    from subprocess import run

    result = run(
        [sys.executable, "computer_control.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_open_app_failure(monkeypatch):
    def fake_startfile(_):
        raise FileNotFoundError("missing")

    def fake_which(_):
        return None

    monkeypatch.setattr("os.startfile", fake_startfile, raising=False)
    monkeypatch.setattr("shutil.which", fake_which)
    with pytest.raises(RuntimeError):
        import controller

        controller.open_app("missing_app")


def test_open_app_linux(monkeypatch):
    import controller

    called = {}

    monkeypatch.setattr(controller, "os", type("DummyOS", (), {"name": "posix"}))

    def fake_which(name):
        called["which"] = name
        return "/usr/bin/" + name

    def fake_popen(cmd):
        called["cmd"] = cmd

        class Dummy:
            pass

        return Dummy()

    monkeypatch.setattr("shutil.which", fake_which)
    monkeypatch.setattr(controller.subprocess, "Popen", fake_popen)
    controller.open_app("vim")
    assert called["which"] == "vim"
    assert called["cmd"] == ["vim"]


def test_capture_screen_error(monkeypatch):
    import controller

    def bad_screenshot():
        raise OSError("scrot missing")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}),
    )

    with pytest.raises(controller.GUIUnavailable):
        controller.capture_screen()


def test_query_pollinations_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=60):
        captured["url"] = url
        captured["json"] = json

        class Response:
            ok = True

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


def test_query_pollinations_network_error(monkeypatch):
    def fake_post(*_, **__):
        raise client.requests.RequestException("boom")

    monkeypatch.setattr(client.requests, "post", fake_post)
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)
    messages = [{"role": "user", "content": "hi"}]
    with pytest.raises(RuntimeError):
        client.query_pollinations(messages, retries=2)


def test_query_pollinations_http_error(monkeypatch):
    class Resp:
        status_code = 400
        ok = False
        text = "bad"

        def raise_for_status(self):
            raise client.requests.HTTPError("bad request")

    def fake_post(*_, **__):
        return Resp()

    monkeypatch.setattr(client.requests, "post", fake_post)
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)
    with pytest.raises(RuntimeError):
        client.query_pollinations([{"role": "user", "content": "hi"}], retries=2)


def test_main_uses_blank_image(monkeypatch):
    import computer_control

    def fake_capture():
        raise controller.GUIUnavailable("no gui")

    def fake_query(messages: List[Dict[str, Any]]):
        nonlocal payload
        payload = messages[1]["content"][1]["image_url"]["url"]
        return {"choices": [{}]}

    payload = ""
    monkeypatch.setattr(controller, "capture_screen", fake_capture)
    monkeypatch.setattr(client, "execute_tool_calls", lambda *_, **__: None)
    monkeypatch.setattr(client, "query_pollinations", fake_query)
    computer_control.main("hello", steps=1, dry_run=True)
    assert payload.startswith("data:image/png;base64,")


def test_create_file(tmp_path):
    path = tmp_path / "sub" / "note.txt"
    controller.create_file(str(path), "hello")
    assert path.read_text() == "hello"
