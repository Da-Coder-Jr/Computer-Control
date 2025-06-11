import os
import sys
import json
from typing import Dict, List, Any


sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)


import pytest  # noqa: E402

from computer_control import client  # noqa: E402
from computer_control import controller  # noqa: E402


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
        {
            "function": {
                "name": "double_click",
                "arguments": json.dumps({"x": 10, "y": 10}),
            },
        },
        {
            "function": {
                "name": "drag_mouse",
                "arguments": json.dumps(
                    {"from_x": 0, "from_y": 0, "to_x": 1, "to_y": 1}
                ),
            },
        },
        {
            "function": {
                "name": "draw_path",
                "arguments": json.dumps(
                    {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}
                ),
            },
        },
        {
            "function": {
                "name": "hotkey",
                "arguments": json.dumps({"keys": ["ctrl", "c"]}),
            },
        },
        {
            "function": {
                "name": "copy_file",
                "arguments": json.dumps({"src": "a.txt", "dst": "b.txt"}),
            },
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
    monkeypatch.setattr("builtins.input", lambda *_: "n")
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
        from computer_control import controller

        controller.open_app("missing_app")


def test_open_app_linux(monkeypatch):
    from computer_control import controller

    called = {}

    monkeypatch.setattr(
        controller, "os", type("DummyOS", (), {"name": "posix"})
    )  # noqa: E501

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
    from computer_control import controller

    def bad_screenshot():
        raise OSError("scrot missing")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}),
    )

    with pytest.raises(controller.GUIUnavailable):
        controller.capture_screen()


def test_capture_screen_jpeg(monkeypatch):
    from computer_control import controller
    from PIL import Image

    def good_screenshot():
        return Image.new("RGB", (10, 10), "red")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(good_screenshot)}),
    )

    url = controller.capture_screen()
    assert url.startswith("data:image/jpeg;base64,")


def test_capture_screen_fallback(monkeypatch):
    from computer_control import controller
    from PIL import Image

    def bad_screenshot():
        raise OSError("fail")

    def grab():
        return Image.new("RGB", (5, 5), "blue")

    monkeypatch.setattr(
        controller,
        "pyautogui",
        type("Dummy", (), {"screenshot": staticmethod(bad_screenshot)}),
    )
    monkeypatch.setattr(
        controller,
        "ImageGrab",
        type("Dummy", (), {"grab": staticmethod(grab)}),
    )

    url = controller.capture_screen()
    assert url.startswith("data:image/jpeg;base64,")


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
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)  # noqa: E501
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
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)  # noqa: E501
    with pytest.raises(RuntimeError):
        client.query_pollinations(
            [{"role": "user", "content": "hi"}], retries=2
        )  # noqa: E501


def test_main_uses_blank_image(monkeypatch):
    from computer_control import main as cc_main

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
    cc_main("hello", steps=1, dry_run=True)
    assert payload.startswith("data:image/png;base64,")


def test_main_uses_blank_image_no_dry_run(monkeypatch):
    from computer_control import main as cc_main

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
    cc_main("hello", steps=1)
    assert payload.startswith("data:image/png;base64,")


def test_create_file(tmp_path):
    path = tmp_path / "sub" / "note.txt"
    controller.create_file(str(path), "hello")
    assert path.read_text() == "hello"


def test_copy_and_delete_file(tmp_path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.txt"
    src.write_text("hi")
    controller.copy_file(str(src), str(dst))
    assert dst.read_text() == "hi"
    controller.delete_file(str(src))
    assert not src.exists()


def test_analysis_functions():
    files = client.ACTION_MAP["list_python_files"]()
    assert "computer_control/main.py" in files

    text = client.ACTION_MAP["read_file"]("README.md")
    assert "Computer-Control" in text

    matches = client.ACTION_MAP["search_code"]("def main")
    assert any(m["file"].endswith("computer_control/main.py") for m in matches)

    summary = client.ACTION_MAP["summarize_codebase"]()
    assert "computer_control/main.py" in summary
    assert "main" in summary["computer_control/main.py"]["functions"]


def test_execute_tool_calls_returns_messages():
    call = {
        "id": "abc",
        "function": {
            "name": "run_shell",
            "arguments": json.dumps({"command": "echo hi"}),
        },
    }
    msgs = client.execute_tool_calls([call], dry_run=True)
    assert msgs[0]["role"] == "tool"
    assert msgs[0]["tool_call_id"] == "abc"


def test_main_unlimited(monkeypatch):
    from computer_control import main as cc_main

    responses = [
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "1",
                                "function": {
                                    "name": "run_shell",
                                    "arguments": "{}",
                                },  # noqa: E501
                            }
                        ]
                    }
                }
            ]
        },
        {"choices": [{"message": {"content": "done", "done": True}}]},
    ]
    idx = {"i": 0}

    def fake_query(_):
        res = responses[idx["i"]]
        idx["i"] += 1
        return res

    monkeypatch.setattr(client, "query_pollinations", fake_query)
    monkeypatch.setattr(
        client,
        "execute_tool_calls",
        lambda *_, **__: [
            {"role": "tool", "tool_call_id": "1", "content": "ok"}
        ],  # noqa: E501
    )
    monkeypatch.setattr(
        controller, "capture_screen", lambda: "data:image/png;base64,abc"
    )
    cc_main("hi", max_steps=0, dry_run=True)
    assert idx["i"] == 2


def test_trim_history_avoids_partial_pairs():
    from computer_control import trim_history  # noqa: E402

    # Build a message sequence with two tool call loops
    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "s1"},
        {"role": "assistant", "tool_calls": [{"id": "2"}]},
        {"role": "tool", "tool_call_id": "2", "content": "ok"},
        {"role": "user", "content": "s2"},
    ]

    trimmed = trim_history(msgs, 3)
    assert trimmed[0]["role"] == "user"
    assert trimmed[1]["role"] == "assistant"
    assert trimmed[2]["role"] == "tool"


def test_trim_history_drops_trailing_tool_call():
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "s1"},
        {"role": "assistant", "tool_calls": [{"id": "2"}]},
    ]

    trimmed = trim_history(msgs, 5)
    assert trimmed[-1]["role"] == "user"


def test_trim_history_removes_incomplete_pairs():
    from computer_control import trim_history  # noqa: E402

    msgs = [
        {"role": "system", "content": "hi"},
        {"role": "user", "content": "goal"},
        {"role": "assistant", "tool_calls": [{"id": "1"}, {"id": "2"}]},
        {"role": "tool", "tool_call_id": "1", "content": "ok"},
        {"role": "user", "content": "next"},
    ]

    trimmed = trim_history(msgs, 4)
    assert all(m.get("tool_call_id") != "1" for m in trimmed)
    assert not any("tool_calls" in m for m in trimmed)


def test_main_save_dir(monkeypatch, tmp_path):
    from computer_control import main as cc_main
    from computer_control import controller, client
    import base64

    def fake_capture():
        return "data:image/jpeg;base64," + base64.b64encode(b"abc").decode()

    def fake_query(_):
        return {"choices": [{"message": {"content": "done", "done": True}}]}

    monkeypatch.setattr(controller, "capture_screen", fake_capture)
    monkeypatch.setattr(client, "execute_tool_calls", lambda *_, **__: [])
    monkeypatch.setattr(client, "query_pollinations", fake_query)

    cc_main("goal", steps=1, dry_run=True, save_dir=str(tmp_path))
    assert (tmp_path / "0.jpg").exists()
    assert (tmp_path / "final.jpg").exists()
